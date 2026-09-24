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
from app.models.enums import DocumentType, SourceType
from app.schemas.content import ProgramDetails
from app.services.program_content import update_program_content


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
        document_urls = set(
            (await session.scalars(select(ProgramDocument.url))).all()
        )
        assert document_urls == {"https://example.org/dokumenty"}

    await engine.dispose()
