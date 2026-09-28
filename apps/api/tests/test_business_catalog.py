from datetime import date
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.db.base import Base
from app.models.domain import Program, PropertyProfile
from app.models.enums import (
    BeneficiaryType,
    BusinessLegalForm,
    BusinessSize,
    MatchRuleStatus,
    ProfileKind,
)
from app.services.business_catalog import import_business_catalog, load_business_catalog
from app.services.matching import _eligibility_rule

CATALOG_PATH = Path(__file__).parents[3] / "content" / "business-programs-2026-09.json"
TODAY = date(2026, 9, 27)


def _profile(field: str, value) -> PropertyProfile:
    profile = PropertyProfile(
        name="Test firmy",
        profile_kind=ProfileKind.BUSINESS,
        beneficiary_type=BeneficiaryType.ENTERPRISE,
        industry_codes=[],
    )
    if field == "business_age_years":
        profile.established_year = TODAY.year - value if value is not None else None
    elif field == "business_size":
        profile.business_size = BusinessSize(value) if value is not None else None
    elif field == "legal_form":
        profile.legal_form = BusinessLegalForm(value) if value is not None else None
    else:
        setattr(profile, field, value)
    return profile


def test_catalog_has_40_verified_programs_and_required_operators() -> None:
    catalog, _ = load_business_catalog(CATALOG_PATH)

    assert len(catalog.programs) == 40
    assert sum(item.status.value in {"open", "planned"} for item in catalog.programs) >= 25
    organizers = " ".join(item.organizer for item in catalog.programs)
    assert "Polska Agencja Rozwoju Przedsiębiorczości" in organizers
    assert "Narodowe Centrum Badań i Rozwoju" in organizers
    assert "Bank Gospodarstwa Krajowego" in organizers
    assert any(
        "tmp_regionalne.xlsx" == item.catalog_evidence["source_file"] for item in catalog.programs
    )
    assert all(item.details.business_requirements for item in catalog.programs)


def test_each_program_has_positive_negative_and_missing_data_scenario() -> None:
    catalog, _ = load_business_catalog(CATALOG_PATH)

    for item in catalog.programs:
        rule = item.eligibility_rules[0].model_dump(mode="json")
        program = Program(slug=item.slug, title=item.title, organizer=item.organizer)
        positive = _eligibility_rule(
            program,
            _profile(item.matching_tests.profile_field, item.matching_tests.positive),
            rule,
            TODAY,
        )
        negative = _eligibility_rule(
            program,
            _profile(item.matching_tests.profile_field, item.matching_tests.negative),
            rule,
            TODAY,
        )
        missing = _eligibility_rule(
            program,
            _profile(item.matching_tests.profile_field, item.matching_tests.missing),
            rule,
            TODAY,
        )
        assert positive.status == MatchRuleStatus.FULFILLED, item.slug
        assert negative.status == MatchRuleStatus.NOT_FULFILLED, item.slug
        assert missing.status == MatchRuleStatus.MISSING_DATA, item.slug


async def test_catalog_import_is_idempotent() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    async with session_factory() as session:
        first = await import_business_catalog(session, CATALOG_PATH, actor="test")
        await session.commit()
    async with session_factory() as session:
        second = await import_business_catalog(session, CATALOG_PATH, actor="test")
        await session.commit()
    async with session_factory() as session:
        session.add(
            Program(
                slug="firma-usuniety-z-manifestu",
                title="Stary program",
                organizer="Test",
                is_published=True,
            )
        )
        await session.commit()
        third = await import_business_catalog(session, CATALOG_PATH, actor="test")
        await session.commit()
        stale = await session.scalar(
            select(Program).where(Program.slug == "firma-usuniety-z-manifestu")
        )

    assert first == {
        "created": 40,
        "updated": 0,
        "unchanged": 0,
        "retired": 0,
        "total": 40,
    }
    assert second == {
        "created": 0,
        "updated": 0,
        "unchanged": 40,
        "retired": 0,
        "total": 40,
    }
    assert third == {
        "created": 0,
        "updated": 0,
        "unchanged": 40,
        "retired": 1,
        "total": 40,
    }
    assert stale is not None and stale.is_published is False
    await engine.dispose()
