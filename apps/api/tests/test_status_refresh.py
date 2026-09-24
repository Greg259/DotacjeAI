from datetime import UTC, date, datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.db.base import Base
from app.models.domain import Program, ProgramVersion, Source, SourceSnapshot
from app.models.enums import ProgramStatus, SourceType
from app.services.review import approve_review
from app.services.status_refresh import propose_date_status_changes


async def test_expired_program_creates_review_and_requires_approval() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    async with factory() as session:
        source = Source(
            name="Source",
            slug="source",
            url="https://example.org/source",
            source_type=SourceType.HTML,
        )
        program = Program(
            slug="program",
            title="Program",
            organizer="Test",
            status=ProgramStatus.OPEN,
            application_end=date(2020, 1, 1),
            is_published=True,
            primary_source=source,
        )
        session.add(program)
        await session.flush()
        snapshot = SourceSnapshot(
            source_id=source.id,
            final_url=source.url,
            http_status=200,
            sha256="a" * 64,
            normalized_sha256="b" * 64,
            size_bytes=1,
            storage_path="source.html",
            normalized_text="Nabór",
            is_changed=True,
        )
        session.add(snapshot)
        await session.flush()
        session.add(
            ProgramVersion(
                program_id=program.id,
                source_snapshot_id=snapshot.id,
                version_number=1,
                extracted_data={"status": "open"},
                evidence={},
                approved_at=datetime.now(UTC),
            )
        )
        await session.commit()

        reviews = await propose_date_status_changes(session)
        await session.commit()
        assert len(reviews) == 1
        assert program.status == ProgramStatus.OPEN

        await approve_review(session, reviews[0].id, actor="test")
        await session.commit()
        await session.refresh(program)
        assert program.status == ProgramStatus.CLOSED
        assert (
            await session.scalar(
                select(func.count()).select_from(ProgramVersion).where(
                    ProgramVersion.program_id == program.id
                )
            )
            == 2
        )

    await engine.dispose()
