import hashlib
from pathlib import Path

import httpx
import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.config import Settings
from app.db.base import Base
from app.models.domain import ReviewTask, Source, SourceSnapshot
from app.models.enums import SourceType
from app.services.crawler import build_diff, crawl_source, normalize_html


def test_normalize_html_removes_scripts_and_keeps_absolute_links() -> None:
    raw = b"""
        <html><body><h1>Program</h1><script>secret()</script>
        <p>Kwota   6000 zl</p><a href="/regulamin.pdf">Regulamin</a></body></html>
    """

    normalized = normalize_html(raw, "https://example.org/dotacje/")

    assert "secret" not in normalized
    assert "Kwota 6000 zl" in normalized
    assert "LINK: Regulamin -> https://example.org/regulamin.pdf" in normalized


def test_normalize_html_removes_volatile_visit_counter() -> None:
    first = normalize_html(
        b"<main><h1>Program</h1><p>Liczba odwiedzin:</p><p>194</p><p>Termin: 2027</p></main>",
        "https://example.org/program",
    )
    second = normalize_html(
        b"<main><h1>Program</h1><p>Liczba odwiedzin:</p><p>210</p><p>Termin: 2027</p></main>",
        "https://example.org/program",
    )

    assert first == second
    assert "Liczba odwiedzin" not in first
    assert "194" not in first
    assert "Termin: 2027" in first


def test_build_diff_reports_changed_lines() -> None:
    diff = build_diff("Status: otwarty\n", "Status: zakończony\n")

    assert "-Status: otwarty" in diff
    assert "+Status: zakończony" in diff


async def test_crawler_versions_changed_content_and_creates_review(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    settings = Settings(
        DATABASE_URL="sqlite+aiosqlite:///:memory:",
        SOURCE_STORAGE_ROOT=Path("/snapshots"),
    )
    writes: dict[str, bytes] = {}

    def fake_write(path: Path, data: bytes) -> None:
        writes[path.as_posix()] = data

    monkeypatch.setattr("app.services.crawler._write_atomic", fake_write)
    bodies = [
        b"<html><body><h1>Nabor</h1><p>Status: otwarty</p></body></html>",
        b"<html><body><h1>Nabor</h1><p>Status: otwarty</p></body></html>",
        b"<html><body><h1>Nabor</h1><p>Status: zakonczony</p></body></html>",
    ]

    def handler(request: httpx.Request) -> httpx.Response:
        body = bodies.pop(0)
        return httpx.Response(
            200,
            content=body,
            headers={"content-type": "text/html", "etag": f'"{len(bodies)}"'},
            request=request,
        )

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler), follow_redirects=True)
    async with factory() as session:
        source = Source(
            name="Test",
            slug="test-source",
            url="https://example.org/source",
            source_type=SourceType.HTML,
        )
        session.add(source)
        await session.commit()

        first = await crawl_source(session, source, settings, client=client)
        await session.commit()
        second = await crawl_source(session, source, settings, client=client)
        await session.commit()
        third = await crawl_source(session, source, settings, client=client)
        await session.commit()

        assert first.outcome == "changed"
        assert first.review_created is True
        assert second.outcome == "unchanged"
        assert second.review_created is False
        assert third.outcome == "changed"
        assert third.review_created is True

        snapshots = list(
            (
                await session.scalars(select(SourceSnapshot).order_by(SourceSnapshot.fetched_at))
            ).all()
        )
        assert len(snapshots) == 3
        assert (
            snapshots[0].sha256
            == hashlib.sha256(
                b"<html><body><h1>Nabor</h1><p>Status: otwarty</p></body></html>"
            ).hexdigest()
        )
        assert snapshots[1].storage_path == snapshots[0].storage_path
        assert snapshots[2].diff_path is not None
        assert f"/snapshots/{snapshots[2].diff_path}" in writes
        assert await session.scalar(select(func.count()).select_from(ReviewTask)) == 2

    await client.aclose()
    await engine.dispose()


async def test_crawler_records_conditional_304_without_review(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    settings = Settings(
        DATABASE_URL="sqlite+aiosqlite:///:memory:",
        SOURCE_STORAGE_ROOT=Path("/snapshots"),
    )
    monkeypatch.setattr("app.services.crawler._write_atomic", lambda path, data: None)
    requests = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal requests
        requests += 1
        if requests == 1:
            return httpx.Response(
                200,
                content=b"<h1>Program</h1>",
                headers={"content-type": "text/html", "etag": '"version-1"'},
                request=request,
            )
        assert request.headers["if-none-match"] == '"version-1"'
        return httpx.Response(304, request=request)

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler), follow_redirects=True)
    async with factory() as session:
        source = Source(
            name="Test 304",
            slug="test-304",
            url="https://example.org/source",
            source_type=SourceType.HTML,
        )
        session.add(source)
        await session.commit()
        await crawl_source(session, source, settings, client=client)
        await session.commit()
        result = await crawl_source(session, source, settings, client=client)
        await session.commit()

        assert result.outcome == "not_modified"
        assert result.http_status == 304
        assert result.review_created is False
        assert await session.scalar(select(func.count()).select_from(SourceSnapshot)) == 2
        assert await session.scalar(select(func.count()).select_from(ReviewTask)) == 1

    await client.aclose()
    await engine.dispose()


async def test_crawler_ignores_visit_counter_change_from_legacy_snapshot(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    settings = Settings(
        DATABASE_URL="sqlite+aiosqlite:///:memory:",
        SOURCE_STORAGE_ROOT=Path("/snapshots"),
    )
    monkeypatch.setattr("app.services.crawler._write_atomic", lambda path, data: None)
    client = httpx.AsyncClient(
        transport=httpx.MockTransport(
            lambda request: httpx.Response(
                200,
                content=b"<h1>Program</h1><p>Liczba odwiedzin:</p><p>210</p>",
                headers={"content-type": "text/html"},
                request=request,
            )
        )
    )

    async with factory() as session:
        source = Source(
            name="Licznik CMS",
            slug="cms-counter",
            url="https://example.org/program",
            source_type=SourceType.HTML,
        )
        session.add(source)
        await session.flush()
        legacy_text = "Program\nLiczba odwiedzin:\n194"
        session.add(
            SourceSnapshot(
                source_id=source.id,
                fetched_at=source.created_at,
                final_url=source.url,
                http_status=200,
                content_type="text/html",
                sha256="a" * 64,
                normalized_sha256=hashlib.sha256(legacy_text.encode()).hexdigest(),
                size_bytes=1,
                storage_path="legacy.html",
                normalized_text=legacy_text,
                is_changed=True,
            )
        )
        await session.commit()

        result = await crawl_source(session, source, settings, client=client)
        await session.commit()

        assert result.outcome == "unchanged"
        assert result.review_created is False
        assert await session.scalar(select(func.count()).select_from(ReviewTask)) == 0

    await client.aclose()
    await engine.dispose()
