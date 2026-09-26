from datetime import UTC, datetime

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.domain import (
    AuditLog,
    Location,
    Program,
    ProgramBeneficiaryType,
    ProgramBusinessSize,
    ProgramDocument,
    ProgramInvestmentCategory,
    ProgramLocation,
    ProgramPropertyType,
    ProgramVersion,
)
from app.models.enums import DocumentState, DocumentType
from app.schemas.content import ApplicationResource, ProgramDetails
from app.schemas.extraction import ExtractionCandidate


class ProgramContentError(RuntimeError):
    pass


async def _latest_approved_version(session: AsyncSession, program_id) -> ProgramVersion | None:
    return await session.scalar(
        select(ProgramVersion)
        .where(
            ProgramVersion.program_id == program_id,
            ProgramVersion.approved_at.is_not(None),
        )
        .order_by(ProgramVersion.version_number.desc())
    )


async def update_program_core(
    session: AsyncSession,
    slug: str,
    candidate: ExtractionCandidate,
    *,
    actor: str,
) -> ProgramVersion:
    """Apply a manually reviewed core correction and keep it in version history."""
    if candidate.slug != slug:
        raise ProgramContentError("slug_mismatch")
    if candidate.missing_critical_evidence():
        raise ProgramContentError("missing_critical_evidence")
    program = await session.scalar(select(Program).where(Program.slug == slug))
    if program is None:
        raise ProgramContentError("program_not_found")
    latest = await _latest_approved_version(session, program.id)
    if latest is None:
        raise ProgramContentError("approved_version_not_found")

    locations = list(
        (
            await session.scalars(
                select(Location).where(Location.slug.in_(candidate.location_slugs))
            )
        ).all()
    )
    found_locations = {location.slug for location in locations}
    missing_locations = sorted(set(candidate.location_slugs) - found_locations)
    if missing_locations:
        raise ProgramContentError("unknown_locations:" + ",".join(missing_locations))

    program.title = candidate.title
    program.organizer = candidate.organizer
    program.summary = candidate.summary
    program.status = candidate.status
    program.application_start = candidate.application_start
    program.application_end = candidate.application_end
    program.max_amount = candidate.max_amount
    program.support_percent = candidate.support_percent
    program.currency = candidate.currency
    program.eligibility_rules = [
        item.model_dump(mode="json") for item in candidate.eligibility_rules
    ]

    await session.execute(delete(ProgramLocation).where(ProgramLocation.program_id == program.id))
    await session.execute(
        delete(ProgramPropertyType).where(ProgramPropertyType.program_id == program.id)
    )
    await session.execute(
        delete(ProgramBeneficiaryType).where(ProgramBeneficiaryType.program_id == program.id)
    )
    await session.execute(
        delete(ProgramInvestmentCategory).where(ProgramInvestmentCategory.program_id == program.id)
    )
    await session.execute(
        delete(ProgramBusinessSize).where(ProgramBusinessSize.program_id == program.id)
    )
    session.add_all(
        [ProgramLocation(program_id=program.id, location_id=item.id) for item in locations]
    )
    session.add_all(
        [
            ProgramPropertyType(program_id=program.id, property_type=item)
            for item in candidate.property_types
        ]
    )
    session.add_all(
        [
            ProgramBeneficiaryType(program_id=program.id, beneficiary_type=item)
            for item in candidate.beneficiary_types
        ]
    )
    session.add_all(
        [
            ProgramInvestmentCategory(program_id=program.id, investment_category=item)
            for item in candidate.investment_categories
        ]
    )
    session.add_all(
        [
            ProgramBusinessSize(program_id=program.id, business_size=item)
            for item in candidate.business_sizes
        ]
    )

    version_number = (
        await session.scalar(
            select(func.coalesce(func.max(ProgramVersion.version_number), 0)).where(
                ProgramVersion.program_id == program.id
            )
        )
    ) + 1
    extracted_data = dict(latest.extracted_data)
    extracted_data.update(candidate.model_dump(mode="json", exclude={"details", "evidence"}))
    now = datetime.now(UTC)
    version = ProgramVersion(
        program_id=program.id,
        source_snapshot_id=latest.source_snapshot_id,
        version_number=version_number,
        extracted_data=extracted_data,
        evidence={
            "core_review": "manual_review_of_official_sources",
            "previous_version_id": str(latest.id),
            "fields": [item.model_dump(mode="json") for item in candidate.evidence],
        },
        change_summary="Korekta danych głównych i filtrów po kontroli wizualnej",
        approved_at=now,
    )
    session.add(version)
    await session.flush()
    session.add(
        AuditLog(
            actor=actor,
            action="program.core_update",
            entity_type="program_version",
            entity_id=version.id,
            details={
                "program_id": str(program.id),
                "previous_version_id": str(latest.id),
            },
        )
    )
    await session.flush()
    return version


def _document_type(resource: ApplicationResource) -> DocumentType:
    return {
        "application_form": DocumentType.APPLICATION_FORM,
        "instructions": DocumentType.GUIDELINES,
        "regulations": DocumentType.REGULATIONS,
    }.get(resource.resource_type, DocumentType.OTHER)


async def update_program_content(
    session: AsyncSession,
    slug: str,
    details: ProgramDetails,
    *,
    actor: str,
) -> ProgramVersion:
    program = await session.scalar(select(Program).where(Program.slug == slug))
    if program is None:
        raise ProgramContentError("program_not_found")
    latest = await _latest_approved_version(session, program.id)
    if latest is None:
        raise ProgramContentError("approved_version_not_found")

    version_number = (
        await session.scalar(
            select(func.coalesce(func.max(ProgramVersion.version_number), 0)).where(
                ProgramVersion.program_id == program.id
            )
        )
    ) + 1
    extracted_data = dict(latest.extracted_data)
    previous_details = ProgramDetails.model_validate(extracted_data.get("details", {}))
    previous_resource_urls = {str(item.url) for item in previous_details.application_resources}
    current_resource_urls = {str(item.url) for item in details.application_resources}
    removed_resource_urls = previous_resource_urls - current_resource_urls
    if removed_resource_urls:
        obsolete_documents = list(
            (
                await session.scalars(
                    select(ProgramDocument).where(
                        ProgramDocument.program_id == program.id,
                        ProgramDocument.url.in_(removed_resource_urls),
                    )
                )
            ).all()
        )
        for document in obsolete_documents:
            document.state = DocumentState.SUPERSEDED
            document.state_reason = "Usunięto z aktualnej, zatwierdzonej listy materiałów programu."
            document.state_changed_at = datetime.now(UTC)

    extracted_data["schema_version"] = "extraction-v2"
    extracted_data["details"] = details.model_dump(mode="json")
    now = datetime.now(UTC)
    version = ProgramVersion(
        program_id=program.id,
        source_snapshot_id=latest.source_snapshot_id,
        version_number=version_number,
        extracted_data=extracted_data,
        evidence={
            "content_review": "manual_review_of_official_sources",
            "previous_version_id": str(latest.id),
        },
        change_summary=("Rozszerzenie karty o warunki, kwoty, dokumenty i sposób złożenia wniosku"),
        approved_at=now,
    )
    session.add(version)

    for resource in details.application_resources:
        value = str(resource.url)
        document = await session.scalar(
            select(ProgramDocument).where(
                ProgramDocument.program_id == program.id,
                ProgramDocument.url == value,
            )
        )
        if document is None:
            session.add(
                ProgramDocument(
                    program_id=program.id,
                    title=resource.title,
                    url=value,
                    document_type=_document_type(resource),
                    state=DocumentState.CURRENT,
                )
            )
        else:
            document.title = resource.title
            document.document_type = _document_type(resource)
            document.state = DocumentState.CURRENT
            document.state_reason = None
            document.state_changed_at = now

    session.add(
        AuditLog(
            actor=actor,
            action="program.content_update",
            entity_type="program_version",
            entity_id=version.id,
            details={
                "program_id": str(program.id),
                "previous_version_id": str(latest.id),
                "resource_count": len(details.application_resources),
                "removed_resource_count": len(removed_resource_urls),
            },
        )
    )
    await session.flush()
    return version
