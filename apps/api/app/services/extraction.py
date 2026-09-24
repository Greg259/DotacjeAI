import hashlib
import uuid
from datetime import UTC, date, datetime

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.models.domain import ExtractionJob, LlmRun, ReviewTask, Source, SourceSnapshot
from app.models.enums import ExtractionStatus, LlmRunStatus, ReviewStatus
from app.schemas.extraction import ExtractionCandidate
from app.services.deterministic_extraction import RULES_ONLY_SOURCE_SLUGS, extract_deterministic
from app.services.llm_budget import get_budget_state
from app.services.openrouter import (
    InvalidStructuredResponseError,
    MissingApiKeyError,
    OpenRouterError,
    extract_with_openrouter,
)

PROMPT_VERSION = "extraction-v1"
LLM_REQUEST_VERSION = "6"


def _job_key(snapshot: SourceSnapshot) -> str:
    value = f"{snapshot.id}:{snapshot.normalized_sha256}:{PROMPT_VERSION}"
    return hashlib.sha256(value.encode()).hexdigest()


def _llm_key(job: ExtractionJob, model: str, attempt: int) -> str:
    value = f"{job.idempotency_key}:{LLM_REQUEST_VERSION}:{model}:{attempt}"
    return hashlib.sha256(value.encode()).hexdigest()


async def _snapshot_from_review(session: AsyncSession, review: ReviewTask) -> SourceSnapshot | None:
    snapshot_id = review.payload.get("snapshot_id")
    if not snapshot_id:
        return None
    try:
        parsed_id = uuid.UUID(str(snapshot_id))
    except ValueError:
        return None
    return await session.get(SourceSnapshot, parsed_id)


async def ensure_extraction_job(
    session: AsyncSession,
    review: ReviewTask,
    *,
    today: date,
) -> ExtractionJob | None:
    snapshot = await _snapshot_from_review(session, review)
    if snapshot is None:
        return None
    existing = await session.scalar(
        select(ExtractionJob).where(
            ExtractionJob.source_snapshot_id == snapshot.id,
            ExtractionJob.prompt_version == PROMPT_VERSION,
        )
    )
    if existing is not None:
        return existing
    source = await session.get(Source, snapshot.source_id)
    if source is None:
        return None
    deterministic = extract_deterministic(source, snapshot, today=today)
    payload = deterministic.model_dump(mode="json")
    job = ExtractionJob(
        source_snapshot_id=snapshot.id,
        review_task_id=review.id,
        prompt_version=PROMPT_VERSION,
        idempotency_key=_job_key(snapshot),
        status=ExtractionStatus.RULES_READY,
        deterministic_data=payload,
        evidence=[item.model_dump(mode="json") for item in deterministic.evidence],
        warnings=[item.model_dump(mode="json") for item in deterministic.warnings],
    )
    session.add(job)
    await session.flush()
    return job


async def process_extraction_job(
    session: AsyncSession,
    job: ExtractionJob,
    settings: Settings,
    *,
    client: httpx.AsyncClient | None = None,
) -> ExtractionJob:
    snapshot = await session.get(SourceSnapshot, job.source_snapshot_id)
    review = await session.get(ReviewTask, job.review_task_id)
    if snapshot is None or review is None:
        job.status = ExtractionStatus.FAILED
        job.error_message = "snapshot_or_review_missing"
        return job
    source = await session.get(Source, snapshot.source_id)
    if source is None:
        job.status = ExtractionStatus.FAILED
        job.error_message = "source_missing"
        return job

    rules_only = source.slug in RULES_ONLY_SOURCE_SLUGS
    if job.status == ExtractionStatus.READY_FOR_REVIEW and (
        rules_only or job.last_llm_run_id is not None
    ):
        return job
    if not rules_only and job.last_llm_run_id is None:
        # Czyści wynik utworzony przez starszą, zbyt liberalną bramkę regułową.
        # Dane deterministyczne pozostają zachowane jako wejście dla LLM.
        job.candidate_data = None

    deterministic = ExtractionCandidate.model_validate(job.deterministic_data)
    missing = deterministic.missing_critical_evidence()
    if rules_only and not missing and not deterministic.warnings:
        job.candidate_data = deterministic.model_dump(mode="json")
        job.evidence = [item.model_dump(mode="json") for item in deterministic.evidence]
        job.warnings = []
        job.status = ExtractionStatus.READY_FOR_REVIEW
        review.payload = {**review.payload, "extraction_job_id": str(job.id)}
        return job

    if not settings.openrouter_api_key.get_secret_value():
        job.status = ExtractionStatus.AWAITING_API_KEY
        job.error_message = "missing_api_key"
        return job

    budget = await get_budget_state(session, settings)
    if not budget.allowed:
        job.status = ExtractionStatus.BLOCKED_BY_BUDGET
        job.error_message = budget.reason
        return job

    candidate: ExtractionCandidate | None = None
    models = list(dict.fromkeys((settings.llm_model_fast, settings.llm_model_strong)))
    for attempt, model in enumerate(models[:2], start=1):
        idempotency_key = _llm_key(job, model, attempt)
        previous_run = await session.scalar(
            select(LlmRun).where(LlmRun.idempotency_key == idempotency_key)
        )
        if previous_run and previous_run.status == LlmRunStatus.SUCCEEDED:
            candidate = ExtractionCandidate.model_validate(previous_run.response_data)
            job.last_llm_run_id = previous_run.id
            break
        if previous_run is not None:
            continue
        run = LlmRun(
            source_snapshot_id=snapshot.id,
            idempotency_key=idempotency_key,
            provider="openrouter",
            model=model,
            prompt_version=PROMPT_VERSION,
            status=LlmRunStatus.FAILED,
        )
        session.add(run)
        await session.flush()
        try:
            result = await extract_with_openrouter(
                settings,
                model=model,
                deterministic_data=job.deterministic_data,
                source_text=snapshot.normalized_text or "",
                client=client,
            )
            candidate = result.candidate
            run.status = LlmRunStatus.SUCCEEDED
            run.request_sha256 = result.request_sha256
            run.external_id = result.external_id
            run.model = result.model
            run.input_tokens = result.input_tokens
            run.output_tokens = result.output_tokens
            run.cost_usd = result.cost_usd
            run.latency_ms = result.latency_ms
            run.response_data = candidate.model_dump(mode="json")
        except MissingApiKeyError:
            job.status = ExtractionStatus.AWAITING_API_KEY
            job.error_message = "missing_api_key"
            return job
        except InvalidStructuredResponseError as exc:
            run.status = LlmRunStatus.REJECTED_BY_VALIDATION
            run.error_message = str(exc)[:4000]
            run.validation_errors = [{"message": str(exc)[:1000]}]
            run.request_sha256 = exc.request_sha256
            run.external_id = exc.external_id
            run.model = exc.model
            run.input_tokens = exc.input_tokens
            run.output_tokens = exc.output_tokens
            run.cost_usd = exc.cost_usd
            run.latency_ms = exc.latency_ms
            job.last_llm_run_id = run.id
            if attempt < len(models[:2]):
                continue
            job.status = ExtractionStatus.FAILED
            job.error_message = str(exc)[:4000]
            return job
        except OpenRouterError as exc:
            run.error_message = str(exc)[:4000]
            job.status = ExtractionStatus.FAILED
            job.error_message = str(exc)[:4000]
            job.last_llm_run_id = run.id
            return job
        job.last_llm_run_id = run.id
        break

    if candidate is None:
        job.status = ExtractionStatus.FAILED
        job.error_message = "no_valid_llm_result"
        return job

    missing_evidence = candidate.missing_critical_evidence()
    if missing_evidence:
        job.status = ExtractionStatus.FAILED
        job.error_message = "missing_critical_evidence:" + ",".join(missing_evidence)
        return job

    job.candidate_data = candidate.model_dump(mode="json")
    job.evidence = [item.model_dump(mode="json") for item in candidate.evidence]
    job.warnings = [item.model_dump(mode="json") for item in candidate.warnings]
    job.status = ExtractionStatus.READY_FOR_REVIEW
    job.error_message = None
    review.payload = {**review.payload, "extraction_job_id": str(job.id)}
    return job


async def process_pending_extractions(
    session: AsyncSession,
    settings: Settings,
    *,
    today: date | None = None,
    client: httpx.AsyncClient | None = None,
) -> list[ExtractionJob]:
    today = today or datetime.now(UTC).date()
    reviews = list(
        (
            await session.scalars(
                select(ReviewTask)
                .where(ReviewTask.status == ReviewStatus.PENDING)
                .order_by(ReviewTask.created_at)
            )
        ).all()
    )
    jobs = []
    for review in reviews:
        job = await ensure_extraction_job(session, review, today=today)
        if job is None:
            continue
        await process_extraction_job(session, job, settings, client=client)
        jobs.append(job)
    return jobs
