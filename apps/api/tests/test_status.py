from datetime import date

import pytest

from app.models.enums import ProgramStatus
from app.services.status import infer_program_status


@pytest.mark.parametrize(
    ("today", "start", "end", "declared", "expected"),
    [
        (
            date(2026, 9, 23),
            None,
            date(2026, 7, 31),
            None,
            ProgramStatus.CLOSED,
        ),
        (
            date(2026, 9, 23),
            date(2026, 10, 1),
            date(2026, 12, 31),
            None,
            ProgramStatus.PLANNED,
        ),
        (
            date(2026, 9, 23),
            date(2026, 9, 1),
            date(2027, 2, 26),
            None,
            ProgramStatus.OPEN,
        ),
        (
            date(2026, 9, 23),
            date(2026, 1, 1),
            date(2027, 1, 1),
            ProgramStatus.SUSPENDED,
            ProgramStatus.SUSPENDED,
        ),
        (date(2026, 9, 23), None, None, None, ProgramStatus.UNKNOWN),
    ],
)
def test_infer_program_status(today, start, end, declared, expected) -> None:
    assert (
        infer_program_status(
            today=today,
            application_start=start,
            application_end=end,
            declared_status=declared,
        )
        == expected
    )
