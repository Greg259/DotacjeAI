from datetime import UTC, date, datetime
from decimal import Decimal, InvalidOperation

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.domain import Location, Program, ProgramLocation, PropertyProfile
from app.models.enums import (
    BeneficiaryType,
    BuildingState,
    BusinessSize,
    EligibilityOperator,
    EligibilityProfileField,
    MatchOutcome,
    MatchRuleStatus,
    ProfileKind,
    ProgramStatus,
    PropertyType,
)
from app.schemas.extraction import EligibilityRuleCandidate
from app.schemas.matching import MatchRuleResult, ProfileMatchesResponse, ProgramMatchResult

RULE_LABELS = {
    "status": "Status i termin naboru",
    "beneficiary": "Typ beneficjenta",
    "location": "Lokalizacja",
    "subject": "Typ nieruchomości lub wielkość firmy",
    "category": "Cel inwestycji",
}


def _rule(
    code: str,
    status: MatchRuleStatus,
    explanation: str,
    *,
    program: Program | None = None,
    label: str | None = None,
    source_url: str | None = None,
    source_reference: str | None = None,
    evidence_quote: str | None = None,
    blocking: bool = True,
) -> MatchRuleResult:
    if program and program.primary_source:
        source_url = source_url or program.primary_source.url
        source_reference = source_reference or "Zatwierdzona klasyfikacja programu"
    return MatchRuleResult(
        code=code,
        label=label or RULE_LABELS[code],
        status=status,
        explanation=explanation,
        source_url=source_url,
        source_reference=source_reference,
        evidence_quote=evidence_quote,
        blocking=blocking,
    )


def _status_rule(program: Program, today: date) -> MatchRuleResult:
    if program.status in {ProgramStatus.CLOSED, ProgramStatus.SUSPENDED}:
        return _rule(
            "status", MatchRuleStatus.NOT_FULFILLED, "Nabór nie jest otwarty.", program=program
        )
    if program.application_end and program.application_end < today:
        return _rule(
            "status", MatchRuleStatus.NOT_FULFILLED, "Termin naboru już minął.", program=program
        )
    if program.application_start and program.application_start > today:
        return _rule(
            "status",
            MatchRuleStatus.MISSING_DATA,
            "Nabór jeszcze się nie rozpoczął.",
            program=program,
        )
    if program.status == ProgramStatus.OPEN:
        return _rule(
            "status",
            MatchRuleStatus.FULFILLED,
            "Nabór jest oznaczony jako otwarty.",
            program=program,
        )
    return _rule(
        "status",
        MatchRuleStatus.MISSING_DATA,
        "Status nie pozwala jeszcze potwierdzić dostępności naboru.",
        program=program,
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
        if profile.business_size in {BusinessSize.MICRO, BusinessSize.SMALL, BusinessSize.MEDIUM}:
            aliases.add(BeneficiaryType.SME)
    return aliases


def _beneficiary_rule(program: Program, profile: PropertyProfile) -> MatchRuleResult:
    allowed = {item.beneficiary_type for item in program.beneficiary_types}
    if not allowed:
        return _rule(
            "beneficiary",
            MatchRuleStatus.MISSING_DATA,
            "Program nie ma pełnej klasyfikacji beneficjentów.",
            program=program,
        )
    if allowed & _beneficiary_aliases(profile):
        return _rule(
            "beneficiary",
            MatchRuleStatus.FULFILLED,
            "Typ profilu występuje na liście beneficjentów.",
            program=program,
        )
    return _rule(
        "beneficiary",
        MatchRuleStatus.NOT_FULFILLED,
        "Typ profilu nie pasuje do beneficjentów programu.",
        program=program,
    )


def _location_rule(
    program: Program, profile: PropertyProfile, parent_by_id: dict
) -> MatchRuleResult:
    if not program.locations:
        return _rule(
            "location",
            MatchRuleStatus.MISSING_DATA,
            "Program nie ma pełnej klasyfikacji terytorialnej.",
            program=program,
        )
    if not profile.location_id:
        return _rule(
            "location",
            MatchRuleStatus.MISSING_DATA,
            "Profil nie ma wybranej lokalizacji.",
            program=program,
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
            program=program,
        )
    return _rule(
        "location",
        MatchRuleStatus.NOT_FULFILLED,
        "Program nie obejmuje lokalizacji zapisanej w profilu.",
        program=program,
    )


def _subject_rule(program: Program, profile: PropertyProfile) -> MatchRuleResult:
    if profile.profile_kind == ProfileKind.BUSINESS:
        sizes = {item.business_size for item in program.business_sizes}
        if sizes:
            status = (
                MatchRuleStatus.FULFILLED
                if profile.business_size in sizes
                else MatchRuleStatus.NOT_FULFILLED
            )
            explanation = (
                "Wielkość przedsiębiorstwa jest dopuszczona."
                if status == MatchRuleStatus.FULFILLED
                else "Wielkość przedsiębiorstwa nie jest dopuszczona."
            )
            return _rule("subject", status, explanation, program=program)
        if program.property_types:
            return _rule(
                "subject",
                MatchRuleStatus.NOT_FULFILLED,
                "Program jest skierowany do nieruchomości mieszkalnych.",
                program=program,
            )
        return _rule(
            "subject",
            MatchRuleStatus.MISSING_DATA,
            "Brakuje klasyfikacji wielkości przedsiębiorstwa.",
            program=program,
        )

    allowed = {item.property_type for item in program.property_types}
    if not allowed:
        return _rule(
            "subject",
            MatchRuleStatus.MISSING_DATA,
            "Program nie ma pełnej klasyfikacji nieruchomości.",
            program=program,
        )
    accepted: set[PropertyType | None] = {profile.property_type}
    if profile.building_state == BuildingState.NEW:
        accepted.add(PropertyType.NEW_HOUSE)
    elif profile.building_state == BuildingState.EXISTING:
        accepted.add(PropertyType.EXISTING_BUILDING)
    status = MatchRuleStatus.FULFILLED if allowed & accepted else MatchRuleStatus.NOT_FULFILLED
    explanation = (
        "Typ i stan nieruchomości pasują do programu."
        if status == MatchRuleStatus.FULFILLED
        else "Typ lub stan nieruchomości nie pasuje do programu."
    )
    return _rule("subject", status, explanation, program=program)


def _category_rule(program: Program, profile: PropertyProfile) -> MatchRuleResult:
    program_categories = {item.investment_category for item in program.investment_categories}
    profile_categories = {item.investment_category for item in profile.investment_categories}
    if not program_categories:
        return _rule(
            "category",
            MatchRuleStatus.MISSING_DATA,
            "Program nie ma pełnej klasyfikacji celu inwestycji.",
            program=program,
        )
    if program_categories & profile_categories:
        return _rule(
            "category",
            MatchRuleStatus.FULFILLED,
            "Program obejmuje co najmniej jeden wybrany cel.",
            program=program,
        )
    return _rule(
        "category",
        MatchRuleStatus.NOT_FULFILLED,
        "Program nie obejmuje wybranych celów profilu.",
        program=program,
    )


def _profile_value(profile: PropertyProfile, field: EligibilityProfileField, today: date):
    direct = {
        EligibilityProfileField.BENEFICIARY_TYPE: profile.beneficiary_type,
        EligibilityProfileField.PROPERTY_TYPE: profile.property_type,
        EligibilityProfileField.BUILDING_STATE: profile.building_state,
        EligibilityProfileField.CURRENT_HEAT_SOURCE: profile.current_heat_source,
        EligibilityProfileField.YEAR_BUILT: profile.year_built,
        EligibilityProfileField.ANNUAL_HOUSEHOLD_INCOME_PLN: profile.annual_household_income_pln,
        EligibilityProfileField.BUSINESS_SIZE: profile.business_size,
        EligibilityProfileField.LEGAL_FORM: profile.legal_form,
        EligibilityProfileField.EMPLOYEE_COUNT: profile.employee_count,
        EligibilityProfileField.ANNUAL_TURNOVER_PLN: profile.annual_turnover_pln,
        EligibilityProfileField.INDUSTRY_CODES: profile.industry_codes,
        EligibilityProfileField.PROJECT_BUDGET_PLN: profile.project_budget_pln,
        EligibilityProfileField.DE_MINIMIS_AID_EUR: profile.de_minimis_aid_eur,
        EligibilityProfileField.IS_STARTUP: profile.is_startup,
        EligibilityProfileField.HAS_VC_INVESTOR: profile.has_vc_investor,
        EligibilityProfileField.CONSORTIUM_PLANNED: profile.consortium_planned,
    }
    if field in direct:
        value = direct[field]
        return value.value if hasattr(value, "value") else value
    if field == EligibilityProfileField.BUSINESS_AGE_YEARS:
        return today.year - profile.established_year if profile.established_year else None
    if field == EligibilityProfileField.MONTHLY_INCOME_PER_PERSON_PLN:
        if profile.annual_household_income_pln is None or not profile.household_members:
            return None
        return profile.annual_household_income_pln / Decimal(12 * profile.household_members)
    if field == EligibilityProfileField.OWN_CONTRIBUTION_PERCENT:
        if not profile.project_budget_pln or profile.own_contribution_pln is None:
            return None
        return profile.own_contribution_pln / profile.project_budget_pln * Decimal(100)
    return None


def _decimal(value: object) -> Decimal:
    return Decimal(str(value).replace(",", "."))


def _evaluate_operator(value, rule: EligibilityRuleCandidate) -> bool:
    expected = rule.expected
    operator = rule.operator
    normalized = value.value if hasattr(value, "value") else value
    if operator == EligibilityOperator.IS_TRUE:
        return normalized is True
    if operator == EligibilityOperator.IS_FALSE:
        return normalized is False
    if operator in {EligibilityOperator.GTE, EligibilityOperator.LTE, EligibilityOperator.BETWEEN}:
        numeric = _decimal(normalized)
        limits = [_decimal(item) for item in expected]
        if operator == EligibilityOperator.GTE:
            return bool(limits) and numeric >= limits[0]
        if operator == EligibilityOperator.LTE:
            return bool(limits) and numeric <= limits[0]
        return len(limits) >= 2 and limits[0] <= numeric <= limits[1]
    if isinstance(normalized, list):
        actual = {str(item).strip().upper() for item in normalized}
        wanted = {item.strip().upper() for item in expected}
        if operator == EligibilityOperator.CONTAINS_ANY:
            return bool(actual & wanted)
        if operator == EligibilityOperator.CONTAINS_NONE:
            return not bool(actual & wanted)
    text = str(normalized).strip().casefold()
    wanted_text = {item.strip().casefold() for item in expected}
    if operator in {EligibilityOperator.EQUALS, EligibilityOperator.IN}:
        return text in wanted_text
    if operator in {EligibilityOperator.NOT_EQUALS, EligibilityOperator.NOT_IN}:
        return text not in wanted_text
    return False


def _eligibility_rule(
    program: Program, profile: PropertyProfile, raw_rule: dict, today: date
) -> MatchRuleResult:
    try:
        candidate = EligibilityRuleCandidate.model_validate(raw_rule)
    except (ValueError, TypeError):
        return _rule(
            "eligibility:invalid",
            MatchRuleStatus.MISSING_DATA,
            "Zatwierdzona reguła wymaga korekty przez administratora.",
            program=program,
            label="Warunek szczegółowy",
        )
    value = _profile_value(profile, candidate.profile_field, today)
    common = {
        "program": program,
        "label": candidate.label,
        "source_url": str(candidate.source_url),
        "source_reference": candidate.source_reference,
        "evidence_quote": candidate.evidence_quote,
        "blocking": candidate.blocking,
    }
    if value is None or value == []:
        return _rule(
            f"eligibility:{candidate.code}",
            MatchRuleStatus.MISSING_DATA,
            f"Uzupełnij w profilu pole: {candidate.profile_field.value}.",
            **common,
        )
    try:
        passed = _evaluate_operator(value, candidate)
    except (InvalidOperation, ValueError, TypeError):
        return _rule(
            f"eligibility:{candidate.code}",
            MatchRuleStatus.MISSING_DATA,
            "Reguła ma nieprawidłową wartość liczbową i wymaga korekty administratora.",
            **common,
        )
    expected = ", ".join(candidate.expected) or candidate.operator.value
    unit_suffix = f" {candidate.unit}" if candidate.unit else ""
    return _rule(
        f"eligibility:{candidate.code}",
        MatchRuleStatus.FULFILLED if passed else MatchRuleStatus.NOT_FULFILLED,
        (f"Wartość profilu: {value}. Warunek: {candidate.operator.value} {expected}{unit_suffix}."),
        **common,
    )


def _outcome(rules: list[MatchRuleResult]) -> MatchOutcome:
    if any(item.blocking and item.status == MatchRuleStatus.NOT_FULFILLED for item in rules):
        return MatchOutcome.NOT_ELIGIBLE
    if any(item.blocking and item.status == MatchRuleStatus.MISSING_DATA for item in rules):
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
                    selectinload(Program.primary_source),
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
        rules.extend(
            _eligibility_rule(program, profile, raw_rule, current_day)
            for raw_rule in (program.eligibility_rules or [])
        )
        blocking = [item for item in rules if item.blocking]
        fulfilled = sum(item.status == MatchRuleStatus.FULFILLED for item in blocking)
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
                score=round(fulfilled / len(blocking) * 100) if blocking else 0,
                rank=0,
                missing_data=[
                    item.label
                    for item in rules
                    if item.blocking and item.status == MatchRuleStatus.MISSING_DATA
                ],
                rules=rules,
            )
        )
    order = {MatchOutcome.ELIGIBLE: 0, MatchOutcome.POSSIBLE: 1, MatchOutcome.NOT_ELIGIBLE: 2}
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
            "Wynik jest technicznym porównaniem zatwierdzonych danych i nie stanowi "
            "decyzji instytucji udzielającej wsparcia. Zawsze sprawdź aktualny regulamin."
        ),
    )
