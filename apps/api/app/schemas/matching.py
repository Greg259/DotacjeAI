import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel

from app.models.enums import MatchOutcome, MatchRuleStatus, ProfileKind, ProgramStatus


class MatchRuleResult(BaseModel):
    code: str
    label: str
    status: MatchRuleStatus
    explanation: str
    source_url: str | None = None
    source_reference: str | None = None
    evidence_quote: str | None = None
    blocking: bool = True


class ProgramMatchResult(BaseModel):
    program_id: uuid.UUID
    slug: str
    title: str
    organizer: str
    program_status: ProgramStatus
    application_end: date | None
    max_amount: Decimal | None
    currency: str
    outcome: MatchOutcome
    score: int
    rank: int
    missing_data: list[str]
    rules: list[MatchRuleResult]


class ProfileMatchesResponse(BaseModel):
    profile_id: uuid.UUID
    profile_name: str
    profile_kind: ProfileKind
    generated_at: datetime
    results: list[ProgramMatchResult]
    disclaimer: str
