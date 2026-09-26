import json
from datetime import UTC, date, datetime

import httpx
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.config import Settings
from app.db.base import Base
from app.models.domain import ExtractionJob, LlmRun, ReviewTask, Source, SourceSnapshot
from app.models.enums import (
    ExtractionStatus,
    LlmRunStatus,
    ProgramStatus,
    ReviewReason,
    ReviewStatus,
    SourceType,
)
from app.schemas.extraction import ExtractionCandidate
from app.services.extraction import (
    _finalize_candidate,
    process_pending_extractions,
    retry_extraction_job,
)


async def seed_pending_review(
    session,
    *,
    slug: str = "zrodlo-testowe",
    text: str = "Informacja bez terminu i statusu.",
) -> None:
    source = Source(
        name="Źródło testowe",
        slug=slug,
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
        normalized_text=text,
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


async def test_manual_retry_increments_attempt_without_replacing_job() -> None:
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
        jobs = await process_pending_extractions(session, settings, today=date(2026, 9, 24))
        await session.commit()
        original_id = jobs[0].id

        retried = await retry_extraction_job(
            session,
            jobs[0],
            settings,
            today=date(2026, 9, 24),
        )
        await session.commit()

        assert retried.id == original_id
        assert retried.retry_count == 1
        assert retried.status == ExtractionStatus.AWAITING_API_KEY
        assert await session.scalar(select(func.count()).select_from(ExtractionJob)) == 1

    await engine.dispose()


def test_finalize_candidate_anchors_url_and_infers_closed_status() -> None:
    source = Source(
        name="Gmina Nadarzyn",
        slug="nadarzyn-wymiana-zrodla-ciepla-2026",
        url="https://example.org/regulamin.pdf",
        source_type=SourceType.PDF,
    )
    base_data = {
        "slug": source.slug,
        "title": "Dofinansowanie do wymiany źródła ciepła",
        "organizer": "Gmina Nadarzyn",
        "status": "unknown",
        "application_end": "2026-07-31",
        "max_amount": 6000,
        "support_percent": 100,
        "official_url": source.url,
        "evidence": [
            {
                "field": "application_end",
                "quote": "Wnioski będą przyjmowane do 31 lipca 2026 r.",
                "locator": "§ 6 ust. 1",
                "method": "llm",
                "confidence": 0.99,
            }
        ],
        "warnings": [
            {
                "code": "status_unknown",
                "message": "Status wymaga wyliczenia.",
                "fields": ["status"],
            }
        ],
    }
    candidate = ExtractionCandidate.model_validate(base_data)
    deterministic = ExtractionCandidate.model_validate(
        {
            **base_data,
            "evidence": [
                {
                    "field": "official_url",
                    "quote": source.url,
                    "locator": "rekord źródła",
                    "method": "rule",
                    "confidence": 1,
                }
            ],
        }
    )

    finalized = _finalize_candidate(
        candidate,
        deterministic,
        source,
        today=date(2026, 9, 24),
    )

    assert finalized.status == ProgramStatus.CLOSED
    assert {item.field for item in finalized.evidence} >= {
        "application_end",
        "official_url",
        "status",
    }
    assert all(warning.code != "status_unknown" for warning in finalized.warnings)


async def test_complex_wfos_page_never_bypasses_llm_with_rules_only() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    text = (
        "Nabór zakończony 21 stycznia 2019 r. Maksymalna kwota 1 650 zł. "
        "Najwyższy poziom dofinansowania 100% kosztów kwalifikowanych."
    )
    async with factory() as session:
        await seed_pending_review(
            session,
            slug="wfosigw-warszawa-czyste-powietrze",
            text=text,
        )
        settings = Settings(
            DATABASE_URL="sqlite+aiosqlite:///:memory:",
            OPENROUTER_API_KEY="",
        )
        jobs = await process_pending_extractions(session, settings, today=date(2026, 9, 24))
        await session.commit()

        assert jobs[0].status == ExtractionStatus.AWAITING_API_KEY
        assert jobs[0].candidate_data is None
        assert jobs[0].error_message == "missing_api_key"

        # Regresja produkcyjna: wynik oznaczony wcześniej jako gotowy wyłącznie
        # przez reguły musi zostać cofnięty do kolejki oczekującej na LLM.
        jobs[0].status = ExtractionStatus.READY_FOR_REVIEW
        jobs[0].candidate_data = jobs[0].deterministic_data
        await session.commit()
        retried = await process_pending_extractions(session, settings, today=date(2026, 9, 24))
        await session.commit()
        assert retried[0].status == ExtractionStatus.AWAITING_API_KEY
        assert retried[0].candidate_data is None

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
        runs = list((await session.scalars(select(LlmRun).order_by(LlmRun.created_at))).all())
        assert [run.status for run in runs] == [
            LlmRunStatus.REJECTED_BY_VALIDATION,
            LlmRunStatus.SUCCEEDED,
        ]
        assert runs[0].cost_usd is not None
        assert runs[0].input_tokens == 10

    await client.aclose()
    await engine.dispose()


async def test_missing_critical_evidence_uses_strong_model_repair() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        evidence = (
            []
            if calls == 1
            else [
                {
                    "field": "status",
                    "quote": "Nabór trwa",
                    "locator": "strona 1",
                    "method": "llm",
                    "confidence": 0.9,
                }
            ]
        )
        content = json.dumps(
            {
                "schema_version": "extraction-v2",
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
                "details": {},
                "evidence": evidence,
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
            session, settings, today=date(2026, 9, 24), client=client
        )
        await session.commit()

        assert calls == 2
        assert jobs[0].status == ExtractionStatus.READY_FOR_REVIEW
        runs = list((await session.scalars(select(LlmRun).order_by(LlmRun.created_at))).all())
        assert [run.status for run in runs] == [
            LlmRunStatus.REJECTED_BY_VALIDATION,
            LlmRunStatus.SUCCEEDED,
        ]

    await client.aclose()
    await engine.dispose()
