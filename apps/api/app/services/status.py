from datetime import date

from app.models.enums import ProgramStatus


def infer_program_status(
    *,
    today: date,
    application_start: date | None,
    application_end: date | None,
    declared_status: ProgramStatus | None = None,
) -> ProgramStatus:
    """Infer a candidate status; an official explicit closure always wins."""
    if declared_status in {ProgramStatus.CLOSED, ProgramStatus.SUSPENDED}:
        return declared_status
    if application_end and today > application_end:
        return ProgramStatus.CLOSED
    if application_start and today < application_start:
        return ProgramStatus.PLANNED
    if application_start and application_start <= today:
        return ProgramStatus.OPEN
    if declared_status is not None:
        return declared_status
    return ProgramStatus.UNKNOWN
