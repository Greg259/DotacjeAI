from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.config import Settings
from app.db.base import Base
from app.models.domain import LlmRun
from app.models.enums import LlmRunStatus
from app.services.llm_budget import get_budget_state


async def test_daily_budget_blocks_new_calls_at_limit() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    now = datetime(2026, 9, 24, 10, tzinfo=UTC)
    async with factory() as session:
        session.add(
            LlmRun(
                provider="openrouter",
                model="test/model",
                prompt_version="extraction-v1",
                status=LlmRunStatus.SUCCEEDED,
                cost_usd=Decimal("1.00"),
                created_at=now,
            )
        )
        await session.commit()
        state = await get_budget_state(
            session,
            Settings(LLM_DAILY_BUDGET_USD="1", LLM_MONTHLY_BUDGET_USD="10"),
            now=now,
        )

        assert state.allowed is False
        assert state.reason == "daily_budget_exhausted"
        assert state.daily_spend == Decimal("1.00")
    await engine.dispose()
