from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.db.base import Base
from app.models.domain import (
    AuditLog,
    Program,
    ProgramDocument,
    ProgramVersion,
    Source,
    SourceSnapshot,
)
from app.models.enums import DocumentState, DocumentType, ProgramStatus, SourceType
from app.schemas.content import ProgramDetails
from app.schemas.extraction import ExtractionCandidate
from app.services.program_content import update_program_content, update_program_core


async def test_update_program_content_versions_details_and_syncs_resources() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    async with factory() as session:
        source = Source(
            name="Oficjalne źródło",
            slug="official-source",
            url="https://example.org/program",
            source_type=SourceType.HTML,
        )
        program = Program(
            slug="program-testowy",
            title="Program testowy",
            organizer="Instytucja",
            primary_source=source,
            is_published=True,
        )
        session.add(program)
        await session.flush()
        snapshot = SourceSnapshot(
            source_id=source.id,
            final_url=source.url,
            http_status=200,
            sha256="a" * 64,
            normalized_sha256="b" * 64,
            size_bytes=100,
            storage_path="sources/program.html",
            normalized_text="Treść programu",
            is_changed=True,
        )
        session.add(snapshot)
        await session.flush()
        session.add(
            ProgramVersion(
                program_id=program.id,
                source_snapshot_id=snapshot.id,
                version_number=1,
                extracted_data={"schema_version": "extraction-v1", "title": program.title},
                evidence={},
                approved_at=datetime.now(UTC),
            )
        )
        await session.commit()

        details = ProgramDetails.model_validate(
            {
                "key_takeaways": [
                    {
                        "title": "Najważniejszy wniosek",
                        "description": "Opis zweryfikowany w regulaminie.",
                        "source_reference": "Regulamin, § 1",
                        "source_url": "https://example.org/regulamin.pdf",
                    }
                ],
                "application_resources": [
                    {
                        "title": "Formularz wniosku",
                        "url": "https://example.org/wniosek.pdf",
                        "resource_type": "application_form",
                        "description": "Oficjalny formularz.",
                    }
                ],
            }
        )
        version = await update_program_content(
            session, program.slug, details, actor="test"
        )
        await session.commit()

        document = await session.scalar(select(ProgramDocument))
        assert version.version_number == 2
        assert version.extracted_data["schema_version"] == "extraction-v2"
        assert version.extracted_data["details"]["key_takeaways"][0]["title"] == (
            "Najważniejszy wniosek"
        )
        assert document is not None
        assert document.title == "Formularz wniosku"
        assert document.document_type == DocumentType.APPLICATION_FORM
        assert await session.scalar(select(func.count()).select_from(AuditLog)) == 1

        replacement = ProgramDetails(
            application_resources=[
                {
                    "title": "Aktualna strona dokumentów",
                    "url": "https://example.org/dokumenty",
                    "resource_type": "official_page",
                }
            ]
        )
        await update_program_content(session, program.slug, replacement, actor="test")
        await session.commit()
        documents = list((await session.scalars(select(ProgramDocument))).all())
        states = {item.url: item.state for item in documents}
        assert states == {
            "https://example.org/wniosek.pdf": DocumentState.SUPERSEDED,
            "https://example.org/dokumenty": DocumentState.CURRENT,
        }

    await engine.dispose()


async def test_update_program_core_preserves_details_and_creates_audit_version() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    async with factory() as session:
        source = Source(
            name="Źródło",
            slug="source",
            url="https://example.org/program",
            source_type=SourceType.HTML,
        )
        program = Program(
            slug="program-testowy",
            title="Uszkodzony tytu??",
            organizer="Instytucja",
            primary_source=source,
            is_published=True,
        )
        session.add(program)
        await session.flush()
        snapshot = SourceSnapshot(
            source_id=source.id,
            final_url=source.url,
            http_status=200,
            sha256="c" * 64,
            normalized_sha256="d" * 64,
            size_bytes=100,
            storage_path="sources/program.html",
            normalized_text="Treść programu",
            is_changed=True,
        )
        session.add(snapshot)
        await session.flush()
        session.add(
            ProgramVersion(
                program_id=program.id,
                source_snapshot_id=snapshot.id,
                version_number=1,
                extracted_data={
                    "schema_version": "extraction-v2",
                    "details": {"key_takeaways": [{"title": "Zachowane", "description": "Tak"}]},
                },
                evidence={},
                approved_at=datetime.now(UTC),
            )
        )
        await session.commit()

        candidate = ExtractionCandidate.model_validate(
            {
                "slug": program.slug,
                "title": "Poprawny polski tytuł",
                "organizer": "Właściwa instytucja",
                "summary": "Poprawiony opis.",
                "status": "closed",
                "official_url": source.url,
                "evidence": [
                    {
                        "field": "status",
                        "quote": "zamknięty",
                        "locator": "strona",
                        "method": "rule",
                        "confidence": 1,
                    },
                    {
                        "field": "official_url",
                        "quote": "program",
                        "locator": "rekord",
                        "method": "rule",
                        "confidence": 1,
                    },
                ],
            }
        )
        version = await update_program_core(
            session, program.slug, candidate, actor="test"
        )
        await session.commit()

        assert program.title == "Poprawny polski tytuł"
        assert program.status == ProgramStatus.CLOSED
        assert version.version_number == 2
        assert version.extracted_data["details"]["key_takeaways"][0]["title"] == "Zachowane"
        assert await session.scalar(select(func.count()).select_from(AuditLog)) == 1

    await engine.dispose()
