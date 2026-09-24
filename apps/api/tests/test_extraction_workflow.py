import json
from datetime import UTC, date, datetime

import httpx
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.config import Settings
from app.db.base import Base
from app.models.domain import ExtractionJob, LlmRun, ReviewTask, Source, SourceSnapshot
from app.models.enums import ExtractionStatus, LlmRunStatus, ReviewReason, ReviewStatus, SourceType
from app.services.extraction import process_pending_extractions


async def seed_pending_review(session) -> None:
    source = Source(
        name="Źródło testowe",
        slug="zrodlo-testowe",
        url="https://example.org/source",
        source_type=SourceType.HTML,
    )
    session.add(source)
    await session.flush()
    snapshot = SourceSnapshot(
        source_id=source.id,
        fetched_at=datetime.now(UTC),
        final_url=source.url,
        http_status=200,
        sha256="a" * 64,
        normalized_sha256="b" * 64,
        size_bytes=20,
        storage_path="test/source.html",
        normalized_text="Informacja bez terminu i statusu.",
        is_changed=True,
    )
    session.add(snapshot)
    await session.flush()
    session.add(
        ReviewTask(
            reason=ReviewReason.NEW_PROGRAM,
            status=ReviewStatus.PENDING,
            payload={"snapshot_id": str(snapshot.id)},
        )
    )
    await session.commit()


async def test_pending_extraction_is_idempotent_and_waits_for_key() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    async with factory() as session:
        await seed_pending_review(session)

        settings = Settings(
            DATABASE_URL="sqlite+aiosqlite:///:memory:",
            OPENROUTER_API_KEY="",
        )
        first = await process_pending_extractions(session, settings, today=date(2026, 9, 24))
        await session.commit()
        second = await process_pending_extractions(session, settings, today=date(2026, 9, 24))
        await session.commit()

        assert first[0].status == ExtractionStatus.AWAITING_API_KEY
        assert first[0].error_message == "missing_api_key"
        assert second[0].id == first[0].id
        assert await session.scalar(select(func.count()).select_from(ExtractionJob)) == 1

    await engine.dispose()


async def test_invalid_fast_model_response_uses_one_strong_model_repair() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        if calls == 1:
            content = "not-json"
        else:
            content = json.dumps(
                {
                    "schema_version": "extraction-v1",
                    "slug": "program-testowy",
                    "title": "Program testowy",
                    "organizer": "Organizator",
                    "summary": None,
                    "status": "open",
                    "application_start": None,
                    "application_end": None,
                    "max_amount": None,
                    "support_percent": None,
                    "currency": "PLN",
                    "location_slugs": [],
                    "beneficiary_types": [],
                    "property_types": [],
                    "investment_categories": [],
                    "official_url": "https://example.org/source",
                    "document_urls": [],
                    "evidence": [
                        {
                            "field": "status",
                            "quote": "Nabór trwa",
                            "locator": "strona 1",
                            "method": "llm",
                            "confidence": 0.9,
                        },
                        {
                            "field": "official_url",
                            "quote": "https://example.org/source",
                            "locator": "rekord źródła",
                            "method": "rule",
                            "confidence": 1,
                        },
                    ],
                    "warnings": [],
                }
            )
        return httpx.Response(
            200,
            json={
                "id": f"gen-{calls}",
                "model": f"test/model-{calls}",
                "choices": [{"message": {"content": content}}],
                "usage": {"prompt_tokens": 10, "completion_tokens": 10, "cost": 0.001},
            },
            request=request,
        )

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    async with factory() as session:
        await seed_pending_review(session)
        settings = Settings(
            DATABASE_URL="sqlite+aiosqlite:///:memory:",
            OPENROUTER_API_KEY="test-key",
            LLM_MODEL_FAST="test/fast",
            LLM_MODEL_STRONG="test/strong",
        )
        jobs = await process_pending_extractions(
            session,
            settings,
            today=date(2026, 9, 24),
            client=client,
        )
        await session.commit()

        assert calls == 2
        assert jobs[0].status == ExtractionStatus.READY_FOR_REVIEW
        statuses = list(await session.scalars(select(ExtractionJob.status)))
        assert statuses == [ExtractionStatus.READY_FOR_REVIEW]
        runs = list(
            (await session.scalars(select(LlmRun).order_by(LlmRun.created_at))).all()
        )
        assert [run.status for run in runs] == [
            LlmRunStatus.REJECTED_BY_VALIDATION,
            LlmRunStatus.SUCCEEDED,
        ]
        assert runs[0].cost_usd is not None
        assert runs[0].input_tokens == 10

    await client.aclose()
    await engine.dispose()
