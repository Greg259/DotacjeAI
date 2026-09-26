from __future__ import annotations

import asyncio
import difflib
import hashlib
import io
import re
import ssl
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup
from pypdf import PdfReader
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.models.domain import ReviewTask, Source, SourceSnapshot
from app.models.enums import ReviewReason, ReviewStatus, SourceType
from app.services.change_detection import classify_source_change


class CrawlError(RuntimeError):
    pass


@dataclass(frozen=True)
class CrawlResult:
    source_slug: str
    outcome: str
    http_status: int
    snapshot_id: str | None
    sha256: str | None
    normalized_sha256: str | None
    size_bytes: int
    review_created: bool
    change_kinds: list[str]

    def to_dict(self) -> dict[str, str | int | bool | None]:
        return asdict(self)


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _validate_web_url(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise CrawlError(f"Unsupported source URL: {url}")


_VOLATILE_VALUE_LABELS = {
    "liczba odwiedzin:",
}


def strip_volatile_content(text: str) -> str:
    """Remove CMS counters that change without changing the grant content."""
    stable_lines: list[str] = []
    skip_next_value = False
    for line in text.splitlines():
        if skip_next_value:
            skip_next_value = False
            continue
        if line.strip().casefold() in _VOLATILE_VALUE_LABELS:
            skip_next_value = True
            continue
        stable_lines.append(line)
    return "\n".join(stable_lines).strip()


def _build_ssl_context(settings: Settings) -> ssl.SSLContext:
    context = ssl.create_default_context()
    extra_ca_path = settings.crawler_extra_ca_path
    if extra_ca_path is not None:
        if not extra_ca_path.is_file():
            raise CrawlError(f"Configured extra CA file does not exist: {extra_ca_path}")
        context.load_verify_locations(cafile=extra_ca_path)
    return context


def normalize_html(raw: bytes, base_url: str) -> str:
    soup = BeautifulSoup(raw, "html.parser")
    for element in soup(["script", "style", "noscript", "template", "svg"]):
        element.decompose()

    lines = []
    for value in soup.get_text("\n").splitlines():
        line = re.sub(r"\s+", " ", value).strip()
        if line and (not lines or line != lines[-1]):
            lines.append(line)

    links = []
    seen_links: set[tuple[str, str]] = set()
    for anchor in soup.find_all("a", href=True):
        href = urljoin(base_url, anchor["href"].strip())
        if urlparse(href).scheme not in {"http", "https"}:
            continue
        label = re.sub(r"\s+", " ", anchor.get_text(" ")).strip() or "[bez nazwy]"
        item = (label, href)
        if item not in seen_links:
            seen_links.add(item)
            links.append(f"LINK: {label} -> {href}")

    sections = ["\n".join(lines)]
    if links:
        sections.append("\n".join(links))
    return strip_volatile_content("\n\n".join(section for section in sections if section).strip())


def normalize_pdf(raw: bytes) -> str:
    try:
        reader = PdfReader(io.BytesIO(raw))
        pages = []
        for page in reader.pages:
            text = page.extract_text() or ""
            normalized = "\n".join(
                line for value in text.splitlines() if (line := re.sub(r"\s+", " ", value).strip())
            )
            if normalized:
                pages.append(normalized)
        return "\n\n".join(pages).strip()
    except Exception as exc:
        raise CrawlError(f"PDF text extraction failed: {exc}") from exc


def build_diff(previous: str, current: str) -> str:
    return "".join(
        difflib.unified_diff(
            previous.splitlines(keepends=True),
            current.splitlines(keepends=True),
            fromfile="previous",
            tofile="current",
            lineterm="\n",
        )
    )


def _extension(source: Source, content_type: str | None) -> str:
    mime = (content_type or "").lower()
    if source.source_type == SourceType.PDF or "application/pdf" in mime:
        return ".pdf"
    return ".html"


def _write_atomic(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_bytes(data)
    temporary.replace(path)


async def _latest_snapshot(session: AsyncSession, source_id) -> SourceSnapshot | None:
    return await session.scalar(
        select(SourceSnapshot)
        .where(SourceSnapshot.source_id == source_id)
        .order_by(SourceSnapshot.fetched_at.desc(), SourceSnapshot.id.desc())
        .limit(1)
    )


async def crawl_source(
    session: AsyncSession,
    source: Source,
    settings: Settings,
    *,
    client: httpx.AsyncClient | None = None,
) -> CrawlResult:
    _validate_web_url(source.url)
    previous = await _latest_snapshot(session, source.id)
    headers = {"User-Agent": settings.crawler_user_agent, "Accept": "text/html,application/pdf"}
    if previous and previous.etag:
        headers["If-None-Match"] = previous.etag
    if previous and previous.last_modified:
        headers["If-Modified-Since"] = previous.last_modified

    owns_client = client is None
    if client is None:
        client = httpx.AsyncClient(
            follow_redirects=True,
            timeout=settings.crawler_timeout_seconds,
            max_redirects=10,
            verify=_build_ssl_context(settings),
        )

    checked_at = datetime.now(UTC)
    response: httpx.Response | None = None
    last_http_error: httpx.HTTPError | None = None
    try:
        for attempt in range(settings.crawler_retries):
            try:
                candidate = await client.get(source.url, headers=headers)
                response = candidate
                if candidate.status_code not in {429, 500, 502, 503, 504}:
                    break
            except httpx.HTTPError as exc:
                last_http_error = exc
            if attempt + 1 < settings.crawler_retries:
                await asyncio.sleep(0.25 * (2**attempt))
    finally:
        if owns_client:
            await client.aclose()

    if response is None:
        raise CrawlError(f"HTTP request failed for {source.slug}: {last_http_error}")

    _validate_web_url(str(response.url))
    source.last_checked_at = checked_at
    source.last_success_at = checked_at
    source.last_error_at = None
    source.last_error_message = None

    if response.status_code == 304:
        if previous is None:
            raise CrawlError("Server returned 304 without an earlier snapshot")
        snapshot = SourceSnapshot(
            source_id=source.id,
            previous_snapshot_id=previous.id,
            fetched_at=checked_at,
            final_url=str(response.url),
            http_status=304,
            content_type=previous.content_type,
            etag=response.headers.get("etag") or previous.etag,
            last_modified=response.headers.get("last-modified") or previous.last_modified,
            sha256=previous.sha256,
            normalized_sha256=previous.normalized_sha256,
            size_bytes=previous.size_bytes,
            storage_path=previous.storage_path,
            diff_path=None,
            normalized_text=previous.normalized_text,
            is_changed=False,
        )
        session.add(snapshot)
        await session.flush()
        return CrawlResult(
            source_slug=source.slug,
            outcome="not_modified",
            http_status=304,
            snapshot_id=str(snapshot.id),
            sha256=snapshot.sha256,
            normalized_sha256=snapshot.normalized_sha256,
            size_bytes=snapshot.size_bytes,
            review_created=False,
            change_kinds=[],
        )

    if response.status_code != 200:
        raise CrawlError(f"Unexpected HTTP {response.status_code} for {source.slug}")

    raw = response.content
    if b"/_Incapsula_Resource" in raw and len(raw) < 10_000:
        raise CrawlError(f"Anti-bot challenge returned instead of content for {source.slug}")
    declared_size = response.headers.get("content-length")
    try:
        response_too_large = (
            declared_size is not None and int(declared_size) > settings.crawler_max_response_bytes
        )
    except ValueError:
        response_too_large = False
    if response_too_large:
        raise CrawlError(f"Response exceeds size limit for {source.slug}")
    if len(raw) > settings.crawler_max_response_bytes:
        raise CrawlError(f"Response exceeds size limit for {source.slug}")

    content_type = response.headers.get("content-type")
    if source.source_type == SourceType.PDF or "application/pdf" in (content_type or "").lower():
        normalized_text = normalize_pdf(raw)
    else:
        normalized_text = normalize_html(raw, str(response.url))

    raw_hash = _sha256(raw)
    normalized_hash = _sha256(normalized_text.encode("utf-8")) if normalized_text else raw_hash
    previous_normalized_text = (
        strip_volatile_content(previous.normalized_text or "") if previous else ""
    )
    previous_comparable_hash = (
        _sha256(previous_normalized_text.encode("utf-8"))
        if previous_normalized_text
        else previous.normalized_sha256
        if previous
        else None
    )
    changed = previous is None or previous_comparable_hash != normalized_hash
    timestamp = checked_at.strftime("%Y/%m/%d/%H%M%S")
    extension = _extension(source, content_type)
    relative_path = Path(source.slug) / f"{timestamp}-{raw_hash[:16]}{extension}"
    absolute_path = settings.source_storage_root / relative_path

    if previous is not None and previous.sha256 == raw_hash:
        storage_path = previous.storage_path
    else:
        _write_atomic(absolute_path, raw)
        storage_path = relative_path.as_posix()

    diff_path: str | None = None
    diff_text = ""
    if changed and previous is not None:
        diff_text = build_diff(previous_normalized_text, normalized_text)
        diff_relative = relative_path.with_suffix(relative_path.suffix + ".diff")
        _write_atomic(settings.source_storage_root / diff_relative, diff_text.encode("utf-8"))
        diff_path = diff_relative.as_posix()

    snapshot = SourceSnapshot(
        source_id=source.id,
        previous_snapshot_id=previous.id if previous else None,
        fetched_at=checked_at,
        final_url=str(response.url),
        http_status=200,
        content_type=content_type,
        etag=response.headers.get("etag"),
        last_modified=response.headers.get("last-modified"),
        sha256=raw_hash,
        normalized_sha256=normalized_hash,
        size_bytes=len(raw),
        storage_path=storage_path,
        diff_path=diff_path,
        normalized_text=normalized_text,
        is_changed=changed,
    )
    session.add(snapshot)
    await session.flush()

    review_created = False
    change = classify_source_change(previous_normalized_text, normalized_text) if previous else None
    if changed and source.source_type != SourceType.INDEX:
        reason = ReviewReason.NEW_PROGRAM if previous is None else ReviewReason.SOURCE_CHANGED
        session.add(
            ReviewTask(
                reason=reason,
                status=ReviewStatus.PENDING,
                payload={
                    "source_id": str(source.id),
                    "source_slug": source.slug,
                    "snapshot_id": str(snapshot.id),
                    "source_url": source.url,
                    "final_url": snapshot.final_url,
                    "sha256": raw_hash,
                    "normalized_sha256": normalized_hash,
                    "diff_path": diff_path,
                    "diff_characters": len(diff_text),
                    "change_kinds": change.kinds if change else ["new_program"],
                    "added_links": change.added_links if change else [],
                    "removed_links": change.removed_links if change else [],
                },
            )
        )
        review_created = True

    return CrawlResult(
        source.slug,
        "changed" if changed else "unchanged",
        200,
        str(snapshot.id),
        raw_hash,
        normalized_hash,
        len(raw),
        review_created,
        change.kinds if change else (["new_program"] if changed else []),
    )
