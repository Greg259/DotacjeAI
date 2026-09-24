from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.domain import Program, ReviewTask
from app.models.enums import ProgramStatus, ReviewReason, ReviewStatus
from app.services.status import infer_program_status


async def propose_date_status_changes(session: AsyncSession) -> list[ReviewTask]:
    today = datetime.now(UTC).date()
    programs = list(
        (
            await session.scalars(
                select(Program).where(
                    Program.is_published.is_(True),
                    Program.status.not_in((ProgramStatus.CLOSED, ProgramStatus.SUSPENDED)),
                )
            )
        ).all()
    )
    created = []
    for program in programs:
        proposed = infer_program_status(
            today=today,
            application_start=program.application_start,
            application_end=program.application_end,
        )
        if proposed == program.status or proposed == ProgramStatus.UNKNOWN:
            continue
        pending = await session.scalar(
            select(ReviewTask).where(
                ReviewTask.program_id == program.id,
                ReviewTask.reason == ReviewReason.STATUS_CHANGED,
                ReviewTask.status == ReviewStatus.PENDING,
            )
        )
        if pending is not None:
            continue
        review = ReviewTask(
            program_id=program.id,
            reason=ReviewReason.STATUS_CHANGED,
            status=ReviewStatus.PENDING,
            payload={
                "kind": "date_status",
                "current_status": program.status.value,
                "proposed_status": proposed.value,
                "application_start": (
                    program.application_start.isoformat() if program.application_start else None
                ),
                "application_end": (
                    program.application_end.isoformat() if program.application_end else None
                ),
                "evaluated_on": today.isoformat(),
            },
        )
        session.add(review)
        created.append(review)
    await session.flush()
    return created
