from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.db.base import Base
from app.models.domain import (
    Program,
    ProgramBeneficiaryType,
    ProgramDocument,
    ProgramInvestmentCategory,
    ProgramVersion,
    Source,
    SourceSnapshot,
)
from app.models.enums import (
    BeneficiaryType,
    DocumentType,
    InvestmentCategory,
    ProgramStatus,
    SourceType,
)
from app.services.completeness import program_completeness


async def test_completeness_reports_score_and_missing_sections() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    async with factory() as session:
        source = Source(
            name="Źródło",
            slug="source",
            url="https://example.org/source",
            source_type=SourceType.HTML,
        )
        session.add(source)
        await session.flush()
        program = Program(
            primary_source_id=source.id,
            slug="program",
            title="Program",
            organizer="Organizator",
            summary="Opis",
            status=ProgramStatus.OPEN,
            is_published=True,
        )
        session.add(program)
        await session.flush()
        session.add_all(
            [
                ProgramBeneficiaryType(
                    program_id=program.id,
                    beneficiary_type=BeneficiaryType.OWNER,
                ),
                ProgramInvestmentCategory(
                    program_id=program.id,
                    investment_category=InvestmentCategory.HEAT_PUMP,
                ),
                ProgramDocument(
                    program_id=program.id,
                    title="Regulamin",
                    url="https://example.org/regulamin.pdf",
                    document_type=DocumentType.REGULATIONS,
                ),
            ]
        )
        snapshot = SourceSnapshot(
            source_id=source.id,
            final_url=source.url,
            http_status=200,
            sha256="a" * 64,
            normalized_sha256="b" * 64,
            size_bytes=10,
            storage_path="source.html",
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
                    "details": {
                        "key_takeaways": [{"title": "Ważne", "description": "Opis informacji"}]
                    }
                },
                evidence={},
                approved_at=datetime.now(UTC),
            )
        )
        await session.commit()
        await session.refresh(program, ["locations", "beneficiary_types", "investment_categories"])

        result = await program_completeness(session, program)

        assert result.score > 0
        assert result.score < 100
        assert "lokalizacja" in result.missing
        assert "najważniejsze informacje" not in result.missing

    await engine.dispose()
