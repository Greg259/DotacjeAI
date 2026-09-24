from datetime import UTC, date, datetime

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.db.base import Base
from app.models.domain import (
    AuditLog,
    ExtractionJob,
    Location,
    Program,
    ReviewTask,
    Source,
    SourceSnapshot,
)
from app.models.enums import (
    ExtractionStatus,
    LocationType,
    ReviewReason,
    ReviewStatus,
    SourceType,
)
from app.services.review import ReviewOperationError, approve_review, publish_program


def ready_candidate() -> dict:
    return {
        "schema_version": "extraction-v1",
        "slug": "nadarzyn-wymiana-zrodla-ciepla-2026",
        "title": "Dofinansowanie do wymiany źródła ciepła",
        "organizer": "Gmina Nadarzyn",
        "summary": "Program lokalny",
        "status": "closed",
        "application_start": None,
        "application_end": "2026-07-31",
        "max_amount": "6000.00",
        "support_percent": "100.00",
        "currency": "PLN",
        "location_slugs": ["nadarzyn"],
        "beneficiary_types": ["natural_person", "owner"],
        "property_types": ["single_family_house", "existing_building"],
        "investment_categories": ["heat_source_replacement"],
        "official_url": "https://example.org/regulamin.pdf",
        "document_urls": [],
        "evidence": [
            {
                "field": "official_url",
                "quote": "https://example.org/regulamin.pdf",
                "locator": "rekord źródła",
                "method": "rule",
                "confidence": 1,
            },
            {
                "field": "application_end",
                "quote": "do 31 lipca 2026",
                "locator": "strona 1",
                "method": "rule",
                "confidence": 0.98,
            },
            {
                "field": "status",
                "quote": "do 31 lipca 2026",
                "locator": "strona 1",
                "method": "rule",
                "confidence": 0.98,
            },
            {
                "field": "max_amount",
                "quote": "maksymalnie 6000 zł",
                "locator": "strona 1",
                "method": "rule",
                "confidence": 0.95,
            },
            {
                "field": "support_percent",
                "quote": "do 100% kosztów",
                "locator": "strona 1",
                "method": "rule",
                "confidence": 0.95,
            },
        ],
        "warnings": [],
    }


async def test_approval_creates_draft_and_publish_is_separate() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    async with factory() as session:
        source = Source(
            name="Nadarzyn",
            slug="nadarzyn-wymiana-zrodla-ciepla-2026",
            url="https://example.org/regulamin.pdf",
            source_type=SourceType.PDF,
        )
        location = Location(
            name="Nadarzyn",
            slug="nadarzyn",
            location_type=LocationType.MUNICIPALITY,
        )
        session.add_all([source, location])
        await session.flush()
        snapshot = SourceSnapshot(
            source_id=source.id,
            fetched_at=datetime.now(UTC),
            final_url=source.url,
            http_status=200,
            sha256="a" * 64,
            normalized_sha256="b" * 64,
            size_bytes=100,
            storage_path="nadarzyn/source.pdf",
            normalized_text="do 31 lipca 2026, 6000 zł, 100%",
            is_changed=True,
        )
        session.add(snapshot)
        await session.flush()
        review = ReviewTask(
            reason=ReviewReason.NEW_PROGRAM,
            status=ReviewStatus.PENDING,
            payload={"snapshot_id": str(snapshot.id)},
        )
        session.add(review)
        await session.flush()
        session.add(
            ExtractionJob(
                source_snapshot_id=snapshot.id,
                review_task_id=review.id,
                prompt_version="extraction-v1",
                idempotency_key="c" * 64,
                status=ExtractionStatus.READY_FOR_REVIEW,
                deterministic_data=ready_candidate(),
                candidate_data=ready_candidate(),
                evidence=ready_candidate()["evidence"],
                warnings=[],
            )
        )
        await session.commit()

        program = await approve_review(session, review.id, actor="deploy")
        await session.commit()
        assert program.status.value == "closed"
        assert program.application_end == date(2026, 7, 31)
        assert program.is_published is False

        await publish_program(session, program.id, actor="deploy")
        await session.commit()
        stored = await session.get(Program, program.id)
        assert stored is not None and stored.is_published is True
        assert await session.scalar(select(func.count()).select_from(AuditLog)) == 2

    await engine.dispose()


async def test_publish_without_approved_review_is_blocked() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    async with factory() as session:
        program = Program(slug="draft", title="Draft", organizer="Test")
        session.add(program)
        await session.commit()
        with pytest.raises(ReviewOperationError, match="program_has_no_approved_review"):
            await publish_program(session, program.id, actor="deploy")
    await engine.dispose()
