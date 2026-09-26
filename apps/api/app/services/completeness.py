from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.domain import Program, ProgramDocument, ProgramVersion
from app.models.enums import DocumentState
from app.schemas.content import ProgramDetails


@dataclass(frozen=True)
class CompletenessResult:
    score: int
    completed: int
    total: int
    missing: list[str]


async def program_completeness(session: AsyncSession, program: Program) -> CompletenessResult:
    latest = await session.scalar(
        select(ProgramVersion)
        .where(
            ProgramVersion.program_id == program.id,
            ProgramVersion.approved_at.is_not(None),
        )
        .order_by(ProgramVersion.version_number.desc())
    )
    details = ProgramDetails.model_validate(
        latest.extracted_data.get("details", {}) if latest else {}
    )
    current_documents = await session.scalar(
        select(func.count(ProgramDocument.id)).where(
            ProgramDocument.program_id == program.id,
            ProgramDocument.state == DocumentState.CURRENT,
            ProgramDocument.is_available.is_(True),
        )
    )
    checks = {
        "opis": bool(program.summary),
        "status": program.status.value != "unknown",
        "lokalizacja": bool(program.locations),
        "beneficjenci strukturalni": bool(program.beneficiary_types),
        "kategorie inwestycji": bool(program.investment_categories),
        "najważniejsze informacje": bool(details.key_takeaways),
        "dla kogo": bool(details.eligible_applicants),
        "warunki": bool(details.eligibility_conditions),
        "kwoty lub poziomy wsparcia": bool(details.funding_options),
        "ograniczenia": bool(details.important_information),
        "kroki złożenia wniosku": bool(details.application_steps),
        "wymagane dokumenty": bool(details.required_documents),
        "formularze lub oficjalne zasoby": bool(details.application_resources),
        "aktualny dokument": bool(current_documents),
    }
    completed = sum(checks.values())
    total = len(checks)
    return CompletenessResult(
        score=round(completed * 100 / total),
        completed=completed,
        total=total,
        missing=[label for label, value in checks.items() if not value],
    )
