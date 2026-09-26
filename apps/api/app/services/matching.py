from datetime import UTC, date, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.domain import (
    Location,
    Program,
    ProgramLocation,
    PropertyProfile,
)
from app.models.enums import (
    BeneficiaryType,
    BuildingState,
    BusinessSize,
    MatchOutcome,
    MatchRuleStatus,
    ProfileKind,
    ProgramStatus,
    PropertyType,
)
from app.schemas.matching import (
    MatchRuleResult,
    ProfileMatchesResponse,
    ProgramMatchResult,
)

RULE_LABELS = {
    "status": "Status i termin naboru",
    "beneficiary": "Typ beneficjenta",
    "location": "Lokalizacja",
    "subject": "Typ nieruchomości lub wielkość firmy",
    "category": "Cel inwestycji",
}


def _rule(code: str, status: MatchRuleStatus, explanation: str) -> MatchRuleResult:
    return MatchRuleResult(
        code=code, label=RULE_LABELS[code], status=status, explanation=explanation
    )


def _status_rule(program: Program, today: date) -> MatchRuleResult:
    if program.status in {ProgramStatus.CLOSED, ProgramStatus.SUSPENDED}:
        return _rule("status", MatchRuleStatus.NOT_FULFILLED, "Nabór nie jest otwarty.")
    if program.application_end and program.application_end < today:
        return _rule("status", MatchRuleStatus.NOT_FULFILLED, "Termin naboru już minął.")
    if program.application_start and program.application_start > today:
        return _rule("status", MatchRuleStatus.MISSING_DATA, "Nabór jeszcze się nie rozpoczął.")
    if program.status == ProgramStatus.OPEN:
        return _rule("status", MatchRuleStatus.FULFILLED, "Nabór jest oznaczony jako otwarty.")
    return _rule(
        "status",
        MatchRuleStatus.MISSING_DATA,
        "Status nie pozwala jeszcze potwierdzić dostępności naboru.",
    )


def _beneficiary_aliases(profile: PropertyProfile) -> set[BeneficiaryType]:
    aliases = {profile.beneficiary_type}
    if profile.profile_kind == ProfileKind.PROPERTY:
        if profile.beneficiary_type in {
            BeneficiaryType.OWNER,
            BeneficiaryType.CO_OWNER,
            BeneficiaryType.TENANT,
        }:
            aliases.add(BeneficiaryType.NATURAL_PERSON)
    else:
        aliases.add(BeneficiaryType.ENTERPRISE)
        if profile.business_size in {
            BusinessSize.MICRO,
            BusinessSize.SMALL,
            BusinessSize.MEDIUM,
        }:
            aliases.add(BeneficiaryType.SME)
    return aliases


def _beneficiary_rule(program: Program, profile: PropertyProfile) -> MatchRuleResult:
    allowed = {item.beneficiary_type for item in program.beneficiary_types}
    if not allowed:
        return _rule(
            "beneficiary",
            MatchRuleStatus.MISSING_DATA,
            "Program nie ma pełnej klasyfikacji beneficjentów.",
        )
    if allowed & _beneficiary_aliases(profile):
        return _rule(
            "beneficiary",
            MatchRuleStatus.FULFILLED,
            "Typ profilu występuje na liście beneficjentów.",
        )
    return _rule(
        "beneficiary",
        MatchRuleStatus.NOT_FULFILLED,
        "Typ profilu nie pasuje do beneficjentów programu.",
    )


def _location_rule(
    program: Program, profile: PropertyProfile, parent_by_id: dict
) -> MatchRuleResult:
    if not program.locations:
        return _rule(
            "location",
            MatchRuleStatus.MISSING_DATA,
            "Program nie ma pełnej klasyfikacji terytorialnej.",
        )
    if not profile.location_id:
        return _rule(
            "location", MatchRuleStatus.MISSING_DATA, "Profil nie ma wybranej lokalizacji."
        )
    ancestors = {profile.location_id}
    parent_id = parent_by_id.get(profile.location_id)
    while parent_id:
        ancestors.add(parent_id)
        parent_id = parent_by_id.get(parent_id)
    if any(item.location_id in ancestors for item in program.locations):
        return _rule(
            "location",
            MatchRuleStatus.FULFILLED,
            "Lokalizacja profilu znajduje się na obszarze programu.",
        )
    return _rule(
        "location",
        MatchRuleStatus.NOT_FULFILLED,
        "Program nie obejmuje lokalizacji zapisanej w profilu.",
    )


def _subject_rule(program: Program, profile: PropertyProfile) -> MatchRuleResult:
    if profile.profile_kind == ProfileKind.BUSINESS:
        sizes = {item.business_size for item in program.business_sizes}
        if sizes:
            if profile.business_size in sizes:
                return _rule(
                    "subject",
                    MatchRuleStatus.FULFILLED,
                    "Wielkość przedsiębiorstwa jest dopuszczona.",
                )
            return _rule(
                "subject",
                MatchRuleStatus.NOT_FULFILLED,
                "Wielkość przedsiębiorstwa nie jest dopuszczona.",
            )
        if program.property_types:
            return _rule(
                "subject",
                MatchRuleStatus.NOT_FULFILLED,
                "Program jest skierowany do nieruchomości mieszkalnych.",
            )
        return _rule(
            "subject",
            MatchRuleStatus.MISSING_DATA,
            "Brakuje klasyfikacji wielkości przedsiębiorstwa.",
        )

    allowed = {item.property_type for item in program.property_types}
    if not allowed:
        return _rule(
            "subject",
            MatchRuleStatus.MISSING_DATA,
            "Program nie ma pełnej klasyfikacji nieruchomości.",
        )
    accepted: set[PropertyType | None] = {profile.property_type}
    if profile.building_state == BuildingState.NEW:
        accepted.add(PropertyType.NEW_HOUSE)
    elif profile.building_state == BuildingState.EXISTING:
        accepted.add(PropertyType.EXISTING_BUILDING)
    if allowed & accepted:
        return _rule(
            "subject", MatchRuleStatus.FULFILLED, "Typ i stan nieruchomości pasują do programu."
        )
    return _rule(
        "subject",
        MatchRuleStatus.NOT_FULFILLED,
        "Typ lub stan nieruchomości nie pasuje do programu.",
    )


def _category_rule(program: Program, profile: PropertyProfile) -> MatchRuleResult:
    program_categories = {item.investment_category for item in program.investment_categories}
    profile_categories = {item.investment_category for item in profile.investment_categories}
    if not program_categories:
        return _rule(
            "category",
            MatchRuleStatus.MISSING_DATA,
            "Program nie ma pełnej klasyfikacji celu inwestycji.",
        )
    if program_categories & profile_categories:
        return _rule(
            "category", MatchRuleStatus.FULFILLED, "Program obejmuje co najmniej jeden wybrany cel."
        )
    return _rule(
        "category", MatchRuleStatus.NOT_FULFILLED, "Program nie obejmuje wybranych celów profilu."
    )


def _outcome(rules: list[MatchRuleResult]) -> MatchOutcome:
    statuses = {item.status for item in rules}
    if MatchRuleStatus.NOT_FULFILLED in statuses:
        return MatchOutcome.NOT_ELIGIBLE
    if MatchRuleStatus.MISSING_DATA in statuses:
        return MatchOutcome.POSSIBLE
    return MatchOutcome.ELIGIBLE


async def match_profile(
    session: AsyncSession, profile: PropertyProfile, *, today: date | None = None
) -> ProfileMatchesResponse:
    current_day = today or date.today()
    locations = list((await session.scalars(select(Location))).all())
    parent_by_id = {item.id: item.parent_id for item in locations}
    programs = list(
        (
            await session.scalars(
                select(Program)
                .where(Program.is_published.is_(True))
                .options(
                    selectinload(Program.locations).selectinload(ProgramLocation.location),
                    selectinload(Program.property_types),
                    selectinload(Program.beneficiary_types),
                    selectinload(Program.investment_categories),
                    selectinload(Program.business_sizes),
                )
            )
        )
        .unique()
        .all()
    )
    results = []
    for program in programs:
        rules = [
            _status_rule(program, current_day),
            _beneficiary_rule(program, profile),
            _location_rule(program, profile, parent_by_id),
            _subject_rule(program, profile),
            _category_rule(program, profile),
        ]
        fulfilled = sum(item.status == MatchRuleStatus.FULFILLED for item in rules)
        results.append(
            ProgramMatchResult(
                program_id=program.id,
                slug=program.slug,
                title=program.title,
                organizer=program.organizer,
                program_status=program.status,
                application_end=program.application_end,
                max_amount=program.max_amount,
                currency=program.currency,
                outcome=_outcome(rules),
                score=round(fulfilled / len(rules) * 100),
                rank=0,
                missing_data=[
                    item.label for item in rules if item.status == MatchRuleStatus.MISSING_DATA
                ],
                rules=rules,
            )
        )
    order = {
        MatchOutcome.ELIGIBLE: 0,
        MatchOutcome.POSSIBLE: 1,
        MatchOutcome.NOT_ELIGIBLE: 2,
    }
    results.sort(key=lambda item: (order[item.outcome], -item.score, item.title.lower()))
    for rank, item in enumerate(results, start=1):
        item.rank = rank
    return ProfileMatchesResponse(
        profile_id=profile.id,
        profile_name=profile.name,
        profile_kind=profile.profile_kind,
        generated_at=datetime.now(UTC),
        results=results,
        disclaimer=(
            "Wynik jest technicznym porównaniem zatwierdzonych danych i nie stanowi decyzji "
            "instytucji udzielającej wsparcia. Zawsze sprawdź aktualny regulamin."
        ),
    )
