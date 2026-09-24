from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.models.domain import LlmRun


@dataclass(frozen=True)
class BudgetState:
    daily_spend: Decimal
    monthly_spend: Decimal
    allowed: bool
    reason: str | None


async def get_budget_state(
    session: AsyncSession,
    settings: Settings,
    *,
    now: datetime | None = None,
) -> BudgetState:
    now = now or datetime.now(UTC)
    day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    month_start = day_start.replace(day=1)
    daily = await session.scalar(
        select(func.coalesce(func.sum(LlmRun.cost_usd), 0)).where(
            LlmRun.created_at >= day_start,
            LlmRun.cost_usd.is_not(None),
        )
    )
    monthly = await session.scalar(
        select(func.coalesce(func.sum(LlmRun.cost_usd), 0)).where(
            LlmRun.created_at >= month_start,
            LlmRun.cost_usd.is_not(None),
        )
    )
    daily_spend = Decimal(str(daily))
    monthly_spend = Decimal(str(monthly))
    reason = None
    if daily_spend >= settings.llm_daily_budget_usd:
        reason = "daily_budget_exhausted"
    elif monthly_spend >= settings.llm_monthly_budget_usd:
        reason = "monthly_budget_exhausted"
    return BudgetState(daily_spend, monthly_spend, reason is None, reason)
