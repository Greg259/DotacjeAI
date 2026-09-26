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
    ProgramDocument,
    ProgramInvestmentCategory,
    ProgramLocation,
    ProgramPropertyType,
    ProgramVersion,
    Source,
    SourceSnapshot,
)
from app.models.enums import (
    BeneficiaryType,
    DocumentType,
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
        await session.flush()
        snapshot = SourceSnapshot(
            source_id=source.id,
            final_url=source.url,
            http_status=200,
            content_type="application/pdf",
            sha256="a" * 64,
            normalized_sha256="b" * 64,
            size_bytes=1024,
            storage_path="sources/nadarzyn.pdf",
            normalized_text="Regulamin programu",
            is_changed=True,
        )
        session.add(snapshot)
        await session.flush()
        session.add_all(
            [
                ProgramDocument(
                    program_id=program.id,
                    title="Regulamin naboru",
                    url=source.url,
                    document_type=DocumentType.REGULATIONS,
                ),
                ProgramVersion(
                    program_id=program.id,
                    source_snapshot_id=snapshot.id,
                    version_number=1,
                    extracted_data={
                        "title": program.title,
                        "details": {
                            "key_takeaways": [
                                {
                                    "title": "Nabór zakończony",
                                    "description": "Termin minął 31 lipca 2026 r.",
                                    "source_reference": "Regulamin, § 8",
                                    "source_url": source.url,
                                }
                            ],
                            "funding_options": [
                                {
                                    "name": "Zakup źródła ciepła",
                                    "description": "Do 100% kosztów zakupu.",
                                    "support_percent": 100,
                                    "max_amount": 6000,
                                    "currency": "PLN",
                                    "source_reference": "Regulamin, § 6",
                                    "source_url": source.url,
                                }
                            ],
                        },
                    },
                    evidence={},
                    change_summary="Pierwsza zatwierdzona wersja programu.",
                    approved_at=datetime(2026, 9, 23, tzinfo=UTC),
                ),
                ProgramVersion(
                    program_id=program.id,
                    source_snapshot_id=snapshot.id,
                    version_number=2,
                    extracted_data={"title": program.title},
                    evidence={},
                    change_summary="Wersja robocza nie może być publiczna.",
                ),
                Program(
                    slug="program-roboczy",
                    title="Program roboczy",
                    organizer="Test",
                    status=ProgramStatus.OPEN,
                    is_published=False,
                ),
            ]
        )
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
                    "beneficiary_type": "natural_person",
                    "application_end_to": "2026-08-01",
                    "min_amount": "5000",
                    "min_support_percent": "70",
                    "sort": "amount_desc",
                },
            )
            missing = await client.get("/api/programs", params={"location": "warszawa"})
            detail = await client.get(
                "/api/programs/wymiana-zrodla-ciepla-nadarzyn-2026"
            )
            unpublished = await client.get("/api/programs/program-roboczy")
            admin = await client.get("/admin", params={"status": "pending"})
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
    assert detail.status_code == 200
    detail_payload = detail.json()
    assert detail_payload["documents"] == [
        {
            "title": "Regulamin naboru",
            "url": "https://example.invalid/nadarzyn.pdf",
            "document_type": "regulations",
            "is_available": True,
            "last_checked_at": None,
        }
    ]
    assert [item["version_number"] for item in detail_payload["versions"]] == [1]
    assert detail_payload["details"]["key_takeaways"][0]["title"] == "Nabór zakończony"
    assert Decimal(detail_payload["details"]["funding_options"][0]["max_amount"]) == Decimal(
        "6000.00"
    )
    assert unpublished.status_code == 404
    assert admin.status_code == 200
    assert "Historia operacji" in admin.text
    assert "Sprawdź teraz" in admin.text
