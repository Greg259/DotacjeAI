import hashlib
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlparse

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.models.domain import AuditLog, DocumentVersion, Program, ProgramDocument
from app.services.crawler import _build_ssl_context


@dataclass(frozen=True)
class DocumentSyncResult:
    document_id: str
    url: str
    outcome: str
    http_status: int | None
    sha256: str | None

    def to_dict(self) -> dict:
        return asdict(self)


def _extension(url: str, content_type: str | None) -> str:
    mime = (content_type or "").lower()
    if "pdf" in mime:
        return ".pdf"
    suffix = Path(urlparse(url).path).suffix.lower()
    return suffix if suffix in {".pdf", ".doc", ".docx", ".xls", ".xlsx", ".zip"} else ".html"


def _write_atomic(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_bytes(data)
    temporary.replace(path)


async def sync_program_documents(
    session: AsyncSession,
    settings: Settings,
    *,
    client: httpx.AsyncClient | None = None,
) -> list[DocumentSyncResult]:
    rows = (
        await session.execute(
            select(ProgramDocument, Program)
            .join(Program, Program.id == ProgramDocument.program_id)
            .where(Program.is_published.is_(True))
            .order_by(ProgramDocument.created_at)
        )
    ).all()
    owns_client = client is None
    if client is None:
        client = httpx.AsyncClient(
            follow_redirects=True,
            timeout=settings.crawler_timeout_seconds,
            verify=_build_ssl_context(settings),
            headers={"User-Agent": settings.crawler_user_agent},
        )
    results = []
    try:
        for document, program in rows:
            checked_at = datetime.now(UTC)
            try:
                response = await client.get(document.url)
                status = response.status_code
                document.last_checked_at = checked_at
                document.last_http_status = status
                if status != 200:
                    document.is_available = False
                    document.last_error_message = f"HTTP {status}"
                    results.append(
                        DocumentSyncResult(
                            str(document.id), document.url, "unavailable", status, None
                        )
                    )
                    continue
                raw = response.content
                if len(raw) > settings.crawler_max_response_bytes:
                    raise ValueError("document exceeds configured size limit")
                digest = hashlib.sha256(raw).hexdigest()
                document.is_available = True
                document.last_error_message = None
                existing = await session.scalar(
                    select(DocumentVersion).where(
                        DocumentVersion.document_id == document.id,
                        DocumentVersion.sha256 == digest,
                    )
                )
                if existing is not None:
                    results.append(
                        DocumentSyncResult(
                            str(document.id), document.url, "unchanged", status, digest
                        )
                    )
                    continue
                extension = _extension(document.url, response.headers.get("content-type"))
                relative = (
                    Path("documents")
                    / str(program.id)
                    / str(document.id)
                    / f"{digest}{extension}"
                )
                _write_atomic(settings.source_storage_root / relative, raw)
                session.add(
                    DocumentVersion(
                        document_id=document.id,
                        sha256=digest,
                        content_type=response.headers.get("content-type"),
                        storage_path=relative.as_posix(),
                    )
                )
                session.add(
                    AuditLog(
                        actor="document-monitor",
                        action="document.version_created",
                        entity_type="program_document",
                        entity_id=document.id,
                        details={"program_id": str(program.id), "sha256": digest},
                    )
                )
                results.append(
                    DocumentSyncResult(str(document.id), document.url, "versioned", status, digest)
                )
            except (httpx.HTTPError, OSError, ValueError) as exc:
                document.last_checked_at = checked_at
                document.last_http_status = None
                previous_version = await session.scalar(
                    select(DocumentVersion.id)
                    .where(DocumentVersion.document_id == document.id)
                    .limit(1)
                )
                document.is_available = previous_version is not None
                document.last_error_message = (str(exc) or type(exc).__name__)[:1000]
                results.append(
                    DocumentSyncResult(str(document.id), document.url, "failed", None, None)
                )
    finally:
        if owns_client:
            await client.aclose()
    return results
