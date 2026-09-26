# ruff: noqa: E501

import html
import json
import uuid
from collections import Counter
from datetime import UTC, datetime
from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import get_settings
from app.db.session import get_session
from app.models.domain import (
    AuditLog,
    ExtractionJob,
    LlmRun,
    Program,
    ProgramDocument,
    ReviewTask,
    Source,
    SourceSnapshot,
)
from app.models.enums import ExtractionStatus, ReviewReason, ReviewStatus
from app.services.completeness import program_completeness
from app.services.crawler import CrawlError, build_diff, crawl_source
from app.services.extraction import retry_extraction_job
from app.services.review import (
    ReviewOperationError,
    approve_review,
    publish_program,
    reject_review,
    replace_review_candidate,
)

router = APIRouter(prefix="/admin", tags=["admin"], include_in_schema=False)
SessionDep = Annotated[AsyncSession, Depends(get_session)]


def _page(title: str, body: str) -> HTMLResponse:
    return HTMLResponse(
        "<!doctype html><html lang='pl'><head><meta charset='utf-8'>"
        "<meta name='viewport' content='width=device-width,initial-scale=1'>"
        f"<title>{html.escape(title)} | DotacjeAI Admin</title>"
        "<style>body{font:15px Arial;margin:0;background:#f6f8f6;color:#15251d}"
        "header{background:#123d29;color:white;padding:16px 4vw}main{max-width:1200px;margin:auto;padding:28px 4vw}"
        "a{color:#12663d}table{width:100%;border-collapse:collapse;background:white;margin:18px 0}"
        "th,td{padding:10px;border:1px solid #dce4dd;text-align:left;vertical-align:top}"
        "th{background:#edf4ef}.grid{display:grid;grid-template-columns:repeat(4,1fr);gap:12px}"
        ".metric,.panel{background:white;border:1px solid #dce4dd;border-radius:8px;padding:16px}"
        "textarea{width:100%;min-height:440px;font:12px monospace;padding:10px;box-sizing:border-box}"
        "button{padding:9px 13px;border:0;border-radius:6px;background:#12663d;color:white;font-weight:bold;cursor:pointer}"
        "button.danger{background:#9b3028}.actions{display:flex;gap:8px;flex-wrap:wrap;margin:12px 0}"
        "pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#f1f4f1;padding:12px}"
        ".bad{color:#9b3028;font-weight:bold}.ok{color:#12663d;font-weight:bold}"
        "@media(max-width:800px){.grid{grid-template-columns:1fr}table{font-size:12px}}"
        "</style></head><body><header><strong>DotacjeAI — panel administratora</strong> · "
        "<a style='color:white' href='/admin'>pulpit</a></header>"
        f"<main><h1>{html.escape(title)}</h1>{body}</main></body></html>",
        headers={"Cache-Control": "no-store"},
    )


def _validate_origin(request: Request) -> None:
    origin = request.headers.get("origin")
    if origin and origin.rstrip("/") != "https://dotacjeai.eu":
        raise HTTPException(status_code=403, detail="Invalid origin")


@router.get("", response_class=HTMLResponse)
async def dashboard(request: Request, session: SessionDep) -> HTMLResponse:
    sources = list((await session.scalars(select(Source).order_by(Source.name))).all())
    all_reviews = list(
        (
            await session.scalars(
                select(ReviewTask).order_by(ReviewTask.created_at.desc()).limit(200)
            )
        ).all()
    )
    status_filter = request.query_params.get("status", "")
    program_filter = request.query_params.get("program", "").strip().casefold()
    created_from = request.query_params.get("created_from", "")
    reviews = all_reviews
    if status_filter:
        reviews = [item for item in reviews if item.status.value == status_filter]
    if program_filter:
        reviews = [
            item
            for item in reviews
            if program_filter
            in str(item.payload.get("source_slug", "")).casefold()
        ]
    if created_from:
        try:
            minimum = datetime.fromisoformat(created_from).replace(tzinfo=UTC)
            reviews = [item for item in reviews if item.created_at >= minimum]
        except ValueError:
            pass
    unavailable = list(
        (
            await session.scalars(
                select(ProgramDocument).where(ProgramDocument.is_available.is_(False))
            )
        ).all()
    )
    month_start = datetime.now(UTC).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    monthly_cost = await session.scalar(
        select(func.coalesce(func.sum(LlmRun.cost_usd), Decimal("0"))).where(
            LlmRun.created_at >= month_start
        )
    )
    pending_count = sum(item.status == ReviewStatus.PENDING for item in all_reviews)
    published_count = await session.scalar(
        select(func.count()).select_from(Program).where(Program.is_published.is_(True))
    )
    published_programs = list(
        (
            await session.scalars(
                select(Program)
                .where(Program.is_published.is_(True))
                .options(
                    selectinload(Program.locations),
                    selectinload(Program.beneficiary_types),
                    selectinload(Program.investment_categories),
                )
                .order_by(Program.title)
            )
        ).all()
    )
    completeness = [
        (program, await program_completeness(session, program))
        for program in published_programs
    ]
    metrics = (
        "<div class='grid'>"
        f"<div class='metric'><strong>{published_count or 0}</strong><br>programów publicznych</div>"
        f"<div class='metric'><strong>{pending_count}</strong><br>zadań REVIEW</div>"
        f"<div class='metric'><strong>{len(unavailable)}</strong><br>niedostępnych dokumentów</div>"
        f"<div class='metric'><strong>{monthly_cost or 0} USD</strong><br>koszt LLM w miesiącu</div>"
        "</div>"
    )
    source_rows = "".join(
        "<tr>"
        f"<td>{html.escape(source.name)}</td><td>{html.escape(source.slug)}</td>"
        f"<td>{html.escape(str(source.last_checked_at or 'nigdy'))}</td>"
        f"<td class='{'bad' if source.last_error_message else 'ok'}'>{html.escape(source.last_error_message or 'OK')}</td>"
        f"<td><button onclick=\"actionPost('/admin/sources/{source.id}/crawl')\">Sprawdź teraz</button></td>"
        "</tr>"
        for source in sources
    )
    review_ids = [item.id for item in all_reviews]
    jobs = list(
        (
            await session.scalars(
                select(ExtractionJob).where(ExtractionJob.review_task_id.in_(review_ids))
            )
        ).all()
    ) if review_ids else []
    jobs_by_review = {item.review_task_id: item for item in jobs}
    llm_ids = [item.last_llm_run_id for item in jobs if item.last_llm_run_id]
    llm_runs = list(
        (await session.scalars(select(LlmRun).where(LlmRun.id.in_(llm_ids)))).all()
    ) if llm_ids else []
    costs = {item.id: item.cost_usd for item in llm_runs}
    source_counts = Counter(
        str(item.payload.get("source_slug", "brak źródła")) for item in reviews
    )
    review_rows = "".join(
        "<tr>"
        f"<td><a href='/admin/reviews/{review.id}'>{review.id}</a></td>"
        f"<td>{html.escape(str(review.payload.get('source_slug', '—')))}</td>"
        f"<td>{review.reason.value}</td><td>{review.status.value}</td>"
        f"<td>{costs.get(jobs_by_review.get(review.id).last_llm_run_id, 0) if jobs_by_review.get(review.id) else 0} USD</td>"
        f"<td>{html.escape(str(review.created_at))}</td>"
        "</tr>"
        for review in reviews
    )
    grouped_rows = "".join(
        f"<li><strong>{html.escape(slug)}</strong>: {count}</li>"
        for slug, count in source_counts.most_common()
    ) or "<li>Brak wyników dla filtrów.</li>"
    audit_items = list(
        (
            await session.scalars(
                select(AuditLog).order_by(AuditLog.created_at.desc()).limit(50)
            )
        ).all()
    )
    audit_rows = "".join(
        "<tr>"
        f"<td>{html.escape(str(item.created_at))}</td>"
        f"<td>{html.escape(item.actor)}</td><td>{html.escape(item.action)}</td>"
        f"<td>{html.escape(item.entity_type)}</td><td>{html.escape(str(item.entity_id or '—'))}</td>"
        "</tr>"
        for item in audit_items
    )
    unavailable_rows = "".join(
        f"<li class='bad'>{html.escape(item.title)} — {html.escape(item.url)} — {html.escape(item.last_error_message or 'brak odpowiedzi')}</li>"
        for item in unavailable
    ) or "<li class='ok'>Wszystkie sprawdzone dokumenty są dostępne.</li>"
    completeness_rows = "".join(
        "<tr>"
        f"<td>{html.escape(program.title)}</td>"
        f"<td class='{'ok' if result.score >= 80 else 'bad'}'>{result.score}% ({result.completed}/{result.total})</td>"
        f"<td>{html.escape(', '.join(result.missing) or 'brak')}</td>"
        "</tr>"
        for program, result in completeness
    )
    return _page(
        "Pulpit",
        metrics
        + "<h2>Źródła</h2><table><tr><th>Nazwa</th><th>Slug</th><th>Ostatnia kontrola</th><th>Stan</th><th>Akcja</th></tr>"
        + source_rows
        + "</table><h2>Kolejka REVIEW</h2>"
        + "<form method='get' class='panel actions'><label>Status <select name='status'><option value=''>wszystkie</option>"
        + "".join(f"<option value='{value}' {'selected' if status_filter == value else ''}>{value}</option>" for value in ('pending','approved','rejected'))
        + "</select></label><label>Źródło <input name='program' value='"
        + html.escape(request.query_params.get("program", ""))
        + "'></label><label>Od <input type='date' name='created_from' value='"
        + html.escape(created_from)
        + "'></label><button type='submit'>Filtruj</button><a href='/admin'>Wyczyść</a></form>"
        + "<h3>Grupowanie wyników</h3><ul>" + grouped_rows + "</ul>"
        + "<table><tr><th>ID</th><th>Źródło</th><th>Powód</th><th>Status</th><th>Koszt</th><th>Utworzono</th></tr>"
        + review_rows
        + "</table><h2>Kompletność programów</h2><table><tr><th>Program</th><th>Wynik</th><th>Braki</th></tr>"
        + completeness_rows
        + "</table><h2>Kontrola dokumentów</h2><ul>"
        + unavailable_rows
        + "</ul><h2>Historia operacji</h2><table><tr><th>Data</th><th>Operator</th><th>Akcja</th><th>Typ</th><th>ID</th></tr>"
        + audit_rows
        + "</table><script>async function actionPost(url){const response=await fetch(url,{method:'POST'});if(!response.ok)alert(await response.text());else location.reload();}</script>",
    )


@router.get("/reviews/{review_id}", response_class=HTMLResponse)
async def review_page(review_id: uuid.UUID, session: SessionDep) -> HTMLResponse:
    review = await session.get(ReviewTask, review_id)
    if review is None:
        raise HTTPException(status_code=404, detail="Review not found")
    job = await session.scalar(select(ExtractionJob).where(ExtractionJob.review_task_id == review.id))
    snapshot = await session.get(SourceSnapshot, job.source_snapshot_id) if job else None
    previous = await session.get(SourceSnapshot, snapshot.previous_snapshot_id) if snapshot and snapshot.previous_snapshot_id else None
    diff = build_diff(previous.normalized_text or "", snapshot.normalized_text or "") if previous and snapshot else "Brak poprzedniego snapshotu."
    candidate = json.dumps(job.candidate_data if job else None, ensure_ascii=False, indent=2)
    program = await session.get(Program, review.program_id) if review.program_id else None
    latest_snapshot = None
    if snapshot is not None:
        latest_snapshot = await session.scalar(
            select(SourceSnapshot)
            .where(SourceSnapshot.source_id == snapshot.source_id)
            .order_by(SourceSnapshot.fetched_at.desc(), SourceSnapshot.id.desc())
            .limit(1)
        )
    stale_warning = ""
    if latest_snapshot is not None and snapshot is not None and latest_snapshot.id != snapshot.id:
        stale_warning = "<p class='bad'>Uwaga: istnieje nowszy snapshot tego źródła. Porównaj go przed zatwierdzeniem lub publikacją.</p>"
    actions = ""
    if review.status == ReviewStatus.PENDING and (
        job is not None
        or review.payload.get("kind") == "date_status"
        or review.reason == ReviewReason.DOCUMENT_CHANGED
    ):
        actions = (
            f"<div class='actions'><button onclick=\"actionPost('/admin/reviews/{review.id}/approve')\">Zatwierdź</button>"
            f"<button class='danger' onclick=\"rejectReview('/admin/reviews/{review.id}/reject')\">Odrzuć</button></div>"
        )
    if program is not None and not program.is_published:
        actions += f"<button onclick=\"actionPost('/admin/programs/{program.id}/publish')\">Opublikuj program</button>"
    if job is not None and job.status in {
        ExtractionStatus.FAILED,
        ExtractionStatus.AWAITING_API_KEY,
        ExtractionStatus.BLOCKED_BY_BUDGET,
    }:
        actions += f"<button onclick=\"actionPost('/admin/extractions/{job.id}/retry')\">Ponów ekstrakcję</button>"
    script = f"""
    <script>
    async function actionPost(url, body) {{
      const response = await fetch(url, {{method:'POST',headers: body ? {{'Content-Type':'application/json'}} : {{}},body: body ? JSON.stringify(body) : undefined}});
      if (!response.ok) alert(await response.text()); else location.reload();
    }}
    function saveCandidate() {{
      try {{ actionPost('/admin/reviews/{review.id}/candidate', JSON.parse(document.getElementById('candidate').value)); }}
      catch (error) {{ alert('Niepoprawny JSON: ' + error); }}
    }}
    function rejectReview(url) {{ const note=prompt('Podaj przyczynę odrzucenia:'); if(note) actionPost(url, {{note}}); }}
    </script>"""
    body = (
        f"<p>Status: <strong>{review.status.value}</strong> · powód: {review.reason.value}</p>{stale_warning}{actions}"
        f"<h2>Dane kandydata</h2><textarea id='candidate'>{html.escape(candidate)}</textarea>"
        + ("<button onclick='saveCandidate()'>Zapisz poprawiony JSON</button>" if review.status == ReviewStatus.PENDING and job else "")
        + f"<h2>Ostrzeżenia</h2><pre>{html.escape(json.dumps(job.warnings if job else [], ensure_ascii=False, indent=2))}</pre>"
        f"<h2>Diff źródła</h2><pre>{html.escape(diff[:100000])}</pre>"
        f"<h2>Treść snapshotu</h2><pre>{html.escape((snapshot.normalized_text if snapshot else '')[:100000])}</pre>"
        + script
    )
    return _page(f"REVIEW {review.id}", body)


@router.post("/reviews/{review_id}/candidate")
async def update_candidate(review_id: uuid.UUID, request: Request, session: SessionDep):
    _validate_origin(request)
    try:
        await replace_review_candidate(session, review_id, await request.json(), actor="admin-web")
        await session.commit()
    except (ReviewOperationError, json.JSONDecodeError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"status": "updated"}


@router.post("/reviews/{review_id}/approve")
async def approve(review_id: uuid.UUID, request: Request, session: SessionDep):
    _validate_origin(request)
    try:
        program = await approve_review(session, review_id, actor="admin-web")
        await session.commit()
    except ReviewOperationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"status": "approved", "program_id": str(program.id)}


@router.post("/reviews/{review_id}/reject")
async def reject(review_id: uuid.UUID, request: Request, session: SessionDep):
    _validate_origin(request)
    payload = await request.json()
    try:
        await reject_review(session, review_id, actor="admin-web", note=str(payload.get("note", "")))
        await session.commit()
    except ReviewOperationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"status": "rejected"}


@router.post("/programs/{program_id}/publish")
async def publish(program_id: uuid.UUID, request: Request, session: SessionDep):
    _validate_origin(request)
    try:
        await publish_program(session, program_id, actor="admin-web")
        await session.commit()
    except ReviewOperationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return RedirectResponse("/admin", status_code=303)


@router.post("/sources/{source_id}/crawl")
async def crawl_now(source_id: uuid.UUID, request: Request, session: SessionDep):
    _validate_origin(request)
    source = await session.get(Source, source_id)
    if source is None:
        raise HTTPException(status_code=404, detail="Source not found")
    try:
        result = await crawl_source(session, source, get_settings())
        session.add(
            AuditLog(
                actor="admin-web",
                action="source.crawl",
                entity_type="source",
                entity_id=source.id,
                details=result.to_dict(),
            )
        )
        await session.commit()
    except (CrawlError, OSError) as exc:
        await session.rollback()
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return result.to_dict()


@router.post("/extractions/{job_id}/retry")
async def retry_extraction(job_id: uuid.UUID, request: Request, session: SessionDep):
    _validate_origin(request)
    job = await session.get(ExtractionJob, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Extraction not found")
    try:
        await retry_extraction_job(session, job, get_settings())
        session.add(
            AuditLog(
                actor="admin-web",
                action="extraction.retry",
                entity_type="extraction_job",
                entity_id=job.id,
                details={"retry_count": job.retry_count, "status": job.status.value},
            )
        )
        await session.commit()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"status": job.status.value, "retry_count": job.retry_count}
