import uuid
from datetime import UTC, date, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import selectinload

from app.core.security import hash_password
from app.db.base import Base
from app.models.domain import (
    Location,
    ProfileInvestmentCategory,
    Program,
    ProgramBeneficiaryType,
    ProgramBusinessSize,
    ProgramInvestmentCategory,
    ProgramLocation,
    ProgramPropertyType,
    PropertyProfile,
    User,
)
from app.models.enums import (
    BeneficiaryType,
    BuildingState,
    BusinessLegalForm,
    BusinessSize,
    HeatSource,
    InvestmentCategory,
    LocationType,
    MatchOutcome,
    MatchRuleStatus,
    ProfileKind,
    ProgramStatus,
    PropertyType,
    UserRole,
)
from app.services.matching import match_profile


async def test_matching_is_deterministic_for_property_and_business_profiles() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    now = datetime(2026, 9, 26, tzinfo=UTC)
    async with session_factory() as session:
        poland = Location(
            id=uuid.uuid4(), name="Polska", slug="polska", location_type=LocationType.COUNTRY
        )
        mazovia = Location(
            id=uuid.uuid4(),
            name="Mazowieckie",
            slug="mazowieckie",
            location_type=LocationType.REGION,
            parent_id=poland.id,
        )
        nadarzyn = Location(
            id=uuid.uuid4(),
            name="Nadarzyn",
            slug="nadarzyn",
            location_type=LocationType.MUNICIPALITY,
            parent_id=mazovia.id,
        )
        user = User(
            username="user1",
            password_hash=hash_password("bezpieczne-haslo-123"),
            role=UserRole.USER,
            terms_version="2026-09-26",
            accepted_terms_at=now,
            accepted_privacy_at=now,
        )
        home = PropertyProfile(
            user=user,
            name="Dom",
            profile_kind=ProfileKind.PROPERTY,
            location=nadarzyn,
            beneficiary_type=BeneficiaryType.OWNER,
            property_type=PropertyType.SINGLE_FAMILY_HOUSE,
            building_state=BuildingState.EXISTING,
            current_heat_source=HeatSource.COAL,
            industry_codes=[],
            investment_categories=[
                ProfileInvestmentCategory(investment_category=InvestmentCategory.HEAT_PUMP)
            ],
        )
        company = PropertyProfile(
            user=user,
            name="Firma innowacyjna",
            profile_kind=ProfileKind.BUSINESS,
            location=mazovia,
            beneficiary_type=BeneficiaryType.ENTERPRISE,
            business_name="Przykład sp. z o.o.",
            business_size=BusinessSize.SMALL,
            legal_form=BusinessLegalForm.COMPANY,
            annual_turnover_pln="1450000",
            project_budget_pln="1000000",
            own_contribution_pln="300000",
            has_vc_investor=True,
            industry_codes=["62.01.Z"],
            investment_categories=[
                ProfileInvestmentCategory(
                    investment_category=InvestmentCategory.RESEARCH_AND_DEVELOPMENT
                )
            ],
        )
        home_program = Program(
            slug="pompa-dla-domu",
            title="Pompa dla domu",
            organizer="Fundusz",
            status=ProgramStatus.OPEN,
            application_end=date(2027, 1, 1),
            is_published=True,
            locations=[ProgramLocation(location=mazovia)],
            beneficiary_types=[
                ProgramBeneficiaryType(beneficiary_type=BeneficiaryType.NATURAL_PERSON)
            ],
            property_types=[
                ProgramPropertyType(property_type=PropertyType.SINGLE_FAMILY_HOUSE),
                ProgramPropertyType(property_type=PropertyType.EXISTING_BUILDING),
            ],
            investment_categories=[
                ProgramInvestmentCategory(investment_category=InvestmentCategory.HEAT_PUMP)
            ],
        )
        business_program = Program(
            slug="badania-dla-msp",
            title="Badania dla MŚP",
            organizer="NCBR",
            status=ProgramStatus.OPEN,
            application_end=date(2027, 2, 1),
            is_published=True,
            locations=[ProgramLocation(location=poland)],
            beneficiary_types=[ProgramBeneficiaryType(beneficiary_type=BeneficiaryType.SME)],
            business_sizes=[
                ProgramBusinessSize(business_size=BusinessSize.MICRO),
                ProgramBusinessSize(business_size=BusinessSize.SMALL),
                ProgramBusinessSize(business_size=BusinessSize.MEDIUM),
            ],
            investment_categories=[
                ProgramInvestmentCategory(
                    investment_category=InvestmentCategory.RESEARCH_AND_DEVELOPMENT
                )
            ],
            eligibility_rules=[
                {
                    "code": "turnover_limit",
                    "label": "Maksymalny roczny obrót",
                    "profile_field": "annual_turnover_pln",
                    "operator": "lte",
                    "expected": ["2000000"],
                    "unit": "PLN",
                    "blocking": True,
                    "source_url": "https://example.gov.pl/regulamin",
                    "source_reference": "§ 4 ust. 2",
                    "evidence_quote": "Roczny obrót nie przekracza 2 mln PLN.",
                },
                {
                    "code": "own_contribution",
                    "label": "Minimalny wkład własny",
                    "profile_field": "own_contribution_percent",
                    "operator": "gte",
                    "expected": ["20"],
                    "unit": "%",
                    "blocking": True,
                    "source_url": "https://example.gov.pl/regulamin",
                    "source_reference": "§ 7",
                    "evidence_quote": "Wkład własny wynosi co najmniej 20%.",
                },
                {
                    "code": "vc_investor",
                    "label": "Inwestor VC",
                    "profile_field": "has_vc_investor",
                    "operator": "is_true",
                    "expected": [],
                    "unit": None,
                    "blocking": False,
                    "source_url": "https://example.gov.pl/regulamin",
                    "source_reference": "§ 9",
                    "evidence_quote": "Udział inwestora VC jest dodatkowo punktowany.",
                },
            ],
        )
        session.add_all([home, company, home_program, business_program])
        await session.commit()
        home_id, company_id = home.id, company.id

    async with session_factory() as session:
        profiles = list(
            (
                await session.scalars(
                    select(PropertyProfile)
                    .where(PropertyProfile.id.in_([home_id, company_id]))
                    .options(
                        selectinload(PropertyProfile.location),
                        selectinload(PropertyProfile.investment_categories),
                    )
                )
            ).all()
        )
        by_kind = {item.profile_kind: item for item in profiles}
        home_matches = await match_profile(
            session, by_kind[ProfileKind.PROPERTY], today=date(2026, 9, 26)
        )
        company_profile = by_kind[ProfileKind.BUSINESS]
        company_matches = await match_profile(session, company_profile, today=date(2026, 9, 26))
        company_profile.annual_turnover_pln = "3000000"
        over_limit_matches = await match_profile(session, company_profile, today=date(2026, 9, 26))
        company_profile.annual_turnover_pln = None
        missing_data_matches = await match_profile(
            session, company_profile, today=date(2026, 9, 26)
        )

    assert home_matches.results[0].slug == "pompa-dla-domu"
    assert home_matches.results[0].outcome == MatchOutcome.ELIGIBLE
    assert home_matches.results[0].score == 100
    assert company_matches.results[0].slug == "badania-dla-msp"
    assert company_matches.results[0].outcome == MatchOutcome.ELIGIBLE
    assert company_matches.results[0].score == 100
    assert len(company_matches.results[0].rules) == 8
    detailed = company_matches.results[0].rules[-1]
    assert detailed.source_url == "https://example.gov.pl/regulamin"
    assert detailed.evidence_quote
    over_limit = next(item for item in over_limit_matches.results if item.slug == "badania-dla-msp")
    assert over_limit.outcome == MatchOutcome.NOT_ELIGIBLE
    missing_data = next(
        item for item in missing_data_matches.results if item.slug == "badania-dla-msp"
    )
    assert missing_data.outcome == MatchOutcome.POSSIBLE
    rejected = next(item for item in company_matches.results if item.slug == "pompa-dla-domu")
    assert rejected.outcome == MatchOutcome.NOT_ELIGIBLE
    assert any(rule.status == MatchRuleStatus.NOT_FULFILLED for rule in rejected.rules)
    await engine.dispose()
