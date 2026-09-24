from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.domain import AuditLog, Program, ProgramDocument, ProgramVersion
from app.models.enums import DocumentType
from app.schemas.content import ApplicationResource, ProgramDetails


class ProgramContentError(RuntimeError):
    pass


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
    latest = await session.scalar(
        select(ProgramVersion)
        .where(
            ProgramVersion.program_id == program.id,
            ProgramVersion.approved_at.is_not(None),
        )
        .order_by(ProgramVersion.version_number.desc())
    )
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
            await session.delete(document)

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
        change_summary=(
            "Rozszerzenie karty o warunki, kwoty, dokumenty i sposób złożenia wniosku"
        ),
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
                )
            )
        else:
            document.title = resource.title
            document.document_type = _document_type(resource)

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
