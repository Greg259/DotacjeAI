import uuid
from datetime import UTC, datetime

from pydantic import ValidationError
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.domain import (
    AuditLog,
    ExtractionJob,
    Location,
    Program,
    ProgramBeneficiaryType,
    ProgramDocument,
    ProgramInvestmentCategory,
    ProgramLocation,
    ProgramPropertyType,
    ProgramVersion,
    ReviewTask,
    SourceSnapshot,
)
from app.models.enums import DocumentType, ExtractionStatus, ReviewStatus
from app.schemas.content import ApplicationResource
from app.schemas.extraction import ExtractionCandidate


class ReviewOperationError(RuntimeError):
    pass


def _document_type(resource: ApplicationResource) -> DocumentType:
    return {
        "application_form": DocumentType.APPLICATION_FORM,
        "instructions": DocumentType.GUIDELINES,
        "regulations": DocumentType.REGULATIONS,
    }.get(resource.resource_type, DocumentType.OTHER)


async def get_review_details(session: AsyncSession, review_id: uuid.UUID) -> dict:
    review = await session.get(ReviewTask, review_id)
    if review is None:
        raise ReviewOperationError("review_not_found")
    job = await session.scalar(
        select(ExtractionJob).where(ExtractionJob.review_task_id == review.id)
    )
    return {
        "review_id": str(review.id),
        "status": review.status.value,
        "reason": review.reason.value,
        "resolution_note": review.resolution_note,
        "program_id": str(review.program_id) if review.program_id else None,
        "program_version_id": (
            str(review.program_version_id) if review.program_version_id else None
        ),
        "extraction": None
        if job is None
        else {
            "job_id": str(job.id),
            "status": job.status.value,
            "candidate": job.candidate_data,
            "warnings": job.warnings,
            "error": job.error_message,
        },
    }


async def list_reviews(session: AsyncSession) -> list[dict]:
    reviews = list(
        (await session.scalars(select(ReviewTask).order_by(ReviewTask.created_at))).all()
    )
    return [await get_review_details(session, review.id) for review in reviews]


async def approve_review(
    session: AsyncSession,
    review_id: uuid.UUID,
    *,
    actor: str,
) -> Program:
    review = await session.get(ReviewTask, review_id)
    if review is None:
        raise ReviewOperationError("review_not_found")
    if review.status == ReviewStatus.APPROVED and review.program_id:
        program = await session.get(Program, review.program_id)
        if program is None:
            raise ReviewOperationError("approved_program_missing")
        return program
    if review.status != ReviewStatus.PENDING:
        raise ReviewOperationError("review_not_pending")

    job = await session.scalar(
        select(ExtractionJob).where(ExtractionJob.review_task_id == review.id)
    )
    if job is None or job.status != ExtractionStatus.READY_FOR_REVIEW:
        raise ReviewOperationError("extraction_not_ready")
    candidate = ExtractionCandidate.model_validate(job.candidate_data)
    missing = candidate.missing_critical_evidence()
    if missing:
        raise ReviewOperationError("missing_critical_evidence:" + ",".join(missing))

    snapshot = await session.get(SourceSnapshot, job.source_snapshot_id)
    if snapshot is None:
        raise ReviewOperationError("snapshot_missing")
    program = await session.scalar(select(Program).where(Program.slug == candidate.slug))
    if program is None:
        program = Program(
            primary_source_id=snapshot.source_id,
            slug=candidate.slug,
            title=candidate.title,
            organizer=candidate.organizer,
        )
        session.add(program)
        await session.flush()

    program.primary_source_id = snapshot.source_id
    program.title = candidate.title
    program.organizer = candidate.organizer
    program.summary = candidate.summary
    program.status = candidate.status
    program.application_start = candidate.application_start
    program.application_end = candidate.application_end
    program.max_amount = candidate.max_amount
    program.support_percent = candidate.support_percent
    program.currency = candidate.currency
    program.last_verified_at = snapshot.fetched_at

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
        raise ReviewOperationError("unknown_locations:" + ",".join(missing_locations))
    session.add_all(
        [ProgramLocation(program_id=program.id, location_id=location.id) for location in locations]
    )
    session.add_all(
        [
            ProgramPropertyType(program_id=program.id, property_type=value)
            for value in candidate.property_types
        ]
    )
    session.add_all(
        [
            ProgramBeneficiaryType(program_id=program.id, beneficiary_type=value)
            for value in candidate.beneficiary_types
        ]
    )
    session.add_all(
        [
            ProgramInvestmentCategory(program_id=program.id, investment_category=value)
            for value in candidate.investment_categories
        ]
    )

    version_number = (
        await session.scalar(
            select(func.coalesce(func.max(ProgramVersion.version_number), 0)).where(
                ProgramVersion.program_id == program.id
            )
        )
    ) + 1
    approved_at = datetime.now(UTC)
    version = ProgramVersion(
        program_id=program.id,
        source_snapshot_id=snapshot.id,
        version_number=version_number,
        extracted_data=candidate.model_dump(mode="json", exclude={"evidence"}),
        evidence={"fields": [item.model_dump(mode="json") for item in candidate.evidence]},
        change_summary="Zatwierdzenie wyniku ekstrakcji",
        approved_at=approved_at,
    )
    session.add(version)
    for url in candidate.document_urls:
        value = str(url)
        existing_document = await session.scalar(
            select(ProgramDocument).where(
                ProgramDocument.program_id == program.id,
                ProgramDocument.url == value,
            )
        )
        if existing_document is None:
            session.add(
                ProgramDocument(
                    program_id=program.id,
                    title="Dokument źródłowy",
                    url=value,
                    document_type=DocumentType.OTHER,
                )
            )
    for resource in candidate.details.application_resources:
        value = str(resource.url)
        existing_document = await session.scalar(
            select(ProgramDocument).where(
                ProgramDocument.program_id == program.id,
                ProgramDocument.url == value,
            )
        )
        if existing_document is None:
            session.add(
                ProgramDocument(
                    program_id=program.id,
                    title=resource.title,
                    url=value,
                    document_type=_document_type(resource),
                )
            )
        else:
            existing_document.title = resource.title
            existing_document.document_type = _document_type(resource)
    await session.flush()

    review.status = ReviewStatus.APPROVED
    review.program_id = program.id
    review.program_version_id = version.id
    review.resolved_at = approved_at
    review.resolution_note = "Zatwierdzono przez operatora CLI"
    session.add(
        AuditLog(
            actor=actor,
            action="review.approve",
            entity_type="program_version",
            entity_id=version.id,
            details={
                "review_id": str(review.id),
                "program_id": str(program.id),
                "snapshot_id": str(snapshot.id),
            },
        )
    )
    return program


async def reject_review(
    session: AsyncSession,
    review_id: uuid.UUID,
    *,
    actor: str,
    note: str,
) -> None:
    if not note.strip():
        raise ReviewOperationError("rejection_note_required")
    review = await session.get(ReviewTask, review_id)
    if review is None:
        raise ReviewOperationError("review_not_found")
    if review.status == ReviewStatus.REJECTED:
        return
    if review.status != ReviewStatus.PENDING:
        raise ReviewOperationError("review_not_pending")
    review.status = ReviewStatus.REJECTED
    review.resolution_note = note.strip()[:4000]
    review.resolved_at = datetime.now(UTC)
    session.add(
        AuditLog(
            actor=actor,
            action="review.reject",
            entity_type="review_task",
            entity_id=review.id,
            details={"note": review.resolution_note},
        )
    )


async def replace_review_candidate(
    session: AsyncSession,
    review_id: uuid.UUID,
    candidate_payload: dict,
    *,
    actor: str,
) -> None:
    review = await session.get(ReviewTask, review_id)
    if review is None:
        raise ReviewOperationError("review_not_found")
    if review.status != ReviewStatus.PENDING:
        raise ReviewOperationError("review_not_pending")
    job = await session.scalar(
        select(ExtractionJob).where(ExtractionJob.review_task_id == review.id)
    )
    if job is None:
        raise ReviewOperationError("extraction_job_not_found")
    try:
        candidate = ExtractionCandidate.model_validate(candidate_payload)
    except ValidationError as exc:
        raise ReviewOperationError("invalid_candidate_json") from exc
    missing = candidate.missing_critical_evidence()
    if missing:
        raise ReviewOperationError("missing_critical_evidence:" + ",".join(missing))
    job.candidate_data = candidate.model_dump(mode="json")
    job.evidence = [item.model_dump(mode="json") for item in candidate.evidence]
    job.warnings = [item.model_dump(mode="json") for item in candidate.warnings]
    job.status = ExtractionStatus.READY_FOR_REVIEW
    job.error_message = None
    session.add(
        AuditLog(
            actor=actor,
            action="review.candidate_replace",
            entity_type="extraction_job",
            entity_id=job.id,
            details={"review_id": str(review.id)},
        )
    )


async def publish_program(
    session: AsyncSession,
    program_id: uuid.UUID,
    *,
    actor: str,
) -> Program:
    program = await session.get(Program, program_id)
    if program is None:
        raise ReviewOperationError("program_not_found")
    approved_review = await session.scalar(
        select(ReviewTask).where(
            ReviewTask.program_id == program.id,
            ReviewTask.status == ReviewStatus.APPROVED,
        )
    )
    if approved_review is None:
        raise ReviewOperationError("program_has_no_approved_review")
    if program.is_published:
        return program
    program.is_published = True
    program.published_at = datetime.now(UTC)
    session.add(
        AuditLog(
            actor=actor,
            action="program.publish",
            entity_type="program",
            entity_id=program.id,
            details={"review_id": str(approved_review.id)},
        )
    )
    return program
