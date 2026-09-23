from datetime import UTC, date, datetime
from decimal import Decimal

from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.db.base import Base
from app.db.session import get_session
from app.main import app
from app.models.domain import (
    Location,
    Program,
    ProgramBeneficiaryType,
    ProgramInvestmentCategory,
    ProgramLocation,
    ProgramPropertyType,
    Source,
)
from app.models.enums import (
    BeneficiaryType,
    InvestmentCategory,
    LocationType,
    ProgramStatus,
    PropertyType,
    SourceType,
)


async def test_public_program_list_supports_mvp_filters() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    async with session_factory() as session:
        source = Source(
            name="Gmina Nadarzyn — regulamin 2026",
            slug="nadarzyn-regulamin-2026",
            url="https://example.invalid/nadarzyn.pdf",
            source_type=SourceType.PDF,
        )
        location = Location(
            name="Nadarzyn",
            slug="nadarzyn",
            location_type=LocationType.MUNICIPALITY,
        )
        program = Program(
            slug="wymiana-zrodla-ciepla-nadarzyn-2026",
            title="Wymiana źródła ciepła w Gminie Nadarzyn",
            organizer="Gmina Nadarzyn",
            summary="Dotacja na zakup nowego źródła ciepła.",
            status=ProgramStatus.CLOSED,
            application_end=date(2026, 7, 31),
            max_amount=Decimal("6000"),
            support_percent=Decimal("100"),
            last_verified_at=datetime(2026, 9, 23, tzinfo=UTC),
            is_published=True,
            primary_source=source,
            locations=[ProgramLocation(location=location)],
            property_types=[
                ProgramPropertyType(property_type=PropertyType.SINGLE_FAMILY_HOUSE)
            ],
            beneficiary_types=[
                ProgramBeneficiaryType(beneficiary_type=BeneficiaryType.NATURAL_PERSON)
            ],
            investment_categories=[
                ProgramInvestmentCategory(
                    investment_category=InvestmentCategory.HEAT_SOURCE_REPLACEMENT
                )
            ],
        )
        session.add(program)
        await session.commit()

    async def override_session():
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_session] = override_session
    try:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get(
                "/api/programs",
                params={
                    "location": "nadarzyn",
                    "category": "heat_source_replacement",
                    "status": "closed",
                },
            )
            missing = await client.get("/api/programs", params={"location": "warszawa"})
    finally:
        app.dependency_overrides.clear()
        await engine.dispose()

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 1
    assert payload["items"][0]["max_amount"] == "6000.00"
    assert payload["items"][0]["support_percent"] == "100.00"
    assert payload["items"][0]["official_url"].endswith("nadarzyn.pdf")
    assert missing.status_code == 200
    assert missing.json()["total"] == 0
