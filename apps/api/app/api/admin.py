# ruff: noqa: E501

import html
import json
import uuid
from datetime import UTC, datetime
from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.models.domain import (
    ExtractionJob,
    LlmRun,
    Program,
    ProgramDocument,
    ReviewTask,
    Source,
    SourceSnapshot,
)
from app.models.enums import ReviewStatus
from app.services.crawler import build_diff
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
        f"<main><h1>{html.escape(title)}</h1>{body}</main></body></html>"
    )


def _validate_origin(request: Request) -> None:
    origin = request.headers.get("origin")
    if origin and origin.rstrip("/") != "https://dotacjeai.eu":
        raise HTTPException(status_code=403, detail="Invalid origin")


@router.get("", response_class=HTMLResponse)
async def dashboard(session: SessionDep) -> HTMLResponse:
    sources = list((await session.scalars(select(Source).order_by(Source.name))).all())
    reviews = list(
        (
            await session.scalars(
                select(ReviewTask).order_by(ReviewTask.created_at.desc()).limit(50)
            )
        ).all()
    )
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
    pending_count = sum(item.status == ReviewStatus.PENDING for item in reviews)
    published_count = await session.scalar(
        select(func.count()).select_from(Program).where(Program.is_published.is_(True))
    )
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
        "</tr>"
        for source in sources
    )
    review_rows = "".join(
        "<tr>"
        f"<td><a href='/admin/reviews/{review.id}'>{review.id}</a></td>"
        f"<td>{review.reason.value}</td><td>{review.status.value}</td>"
        f"<td>{html.escape(str(review.created_at))}</td>"
        "</tr>"
        for review in reviews
    )
    unavailable_rows = "".join(
        f"<li class='bad'>{html.escape(item.title)} — {html.escape(item.url)} — {html.escape(item.last_error_message or 'brak odpowiedzi')}</li>"
        for item in unavailable
    ) or "<li class='ok'>Wszystkie sprawdzone dokumenty są dostępne.</li>"
    return _page(
        "Pulpit",
        metrics
        + "<h2>Źródła</h2><table><tr><th>Nazwa</th><th>Slug</th><th>Ostatnia kontrola</th><th>Stan</th></tr>"
        + source_rows
        + "</table><h2>Kolejka REVIEW</h2><table><tr><th>ID</th><th>Powód</th><th>Status</th><th>Utworzono</th></tr>"
        + review_rows
        + "</table><h2>Kontrola dokumentów</h2><ul>"
        + unavailable_rows
        + "</ul>",
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
    actions = ""
    if review.status == ReviewStatus.PENDING and (
        job is not None or review.payload.get("kind") == "date_status"
    ):
        actions = (
            f"<div class='actions'><button onclick=\"actionPost('/admin/reviews/{review.id}/approve')\">Zatwierdź</button>"
            f"<button class='danger' onclick=\"rejectReview('/admin/reviews/{review.id}/reject')\">Odrzuć</button></div>"
        )
    if program is not None and not program.is_published:
        actions += f"<button onclick=\"actionPost('/admin/programs/{program.id}/publish')\">Opublikuj program</button>"
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
        f"<p>Status: <strong>{review.status.value}</strong> · powód: {review.reason.value}</p>{actions}"
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
