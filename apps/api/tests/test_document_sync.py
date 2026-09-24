from pathlib import Path

import httpx
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.config import Settings
from app.db.base import Base
from app.models.domain import DocumentVersion, Program, ProgramDocument
from app.models.enums import DocumentType
from app.services.document_sync import sync_program_documents


async def test_document_sync_versions_content_and_marks_broken_link(tmp_path: Path) -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    async with factory() as session:
        program = Program(
            slug="test",
            title="Test",
            organizer="Test",
            is_published=True,
        )
        session.add(program)
        await session.flush()
        document = ProgramDocument(
            program_id=program.id,
            title="Formularz",
            url="https://example.org/form.pdf",
            document_type=DocumentType.APPLICATION_FORM,
        )
        session.add(document)
        await session.commit()

        def ok_handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(
                200,
                content=b"%PDF-1.4 official form",
                headers={"content-type": "application/pdf"},
                request=request,
            )

        settings = Settings(SOURCE_STORAGE_ROOT=tmp_path)
        client = httpx.AsyncClient(transport=httpx.MockTransport(ok_handler))
        first = await sync_program_documents(session, settings, client=client)
        second = await sync_program_documents(session, settings, client=client)
        await client.aclose()
        await session.commit()

        assert first[0].outcome == "versioned"
        assert second[0].outcome == "unchanged"
        assert await session.scalar(select(func.count()).select_from(DocumentVersion)) == 1
        version = await session.scalar(select(DocumentVersion))
        assert version is not None
        assert (tmp_path / version.storage_path).is_file()

        def missing_handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(404, request=request)

        client = httpx.AsyncClient(transport=httpx.MockTransport(missing_handler))
        result = await sync_program_documents(session, settings, client=client)
        await client.aclose()
        await session.commit()
        await session.refresh(document)
        assert result[0].outcome == "unavailable"
        assert document.is_available is False
        assert document.last_http_status == 404

    await engine.dispose()
