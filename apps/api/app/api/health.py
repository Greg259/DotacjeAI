from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.db.session import get_session

router = APIRouter(tags=["system"])
SettingsDep = Annotated[Settings, Depends(get_settings)]
SessionDep = Annotated[AsyncSession, Depends(get_session)]


@router.get("/health")
async def health(settings: SettingsDep) -> dict[str, str]:
    return {"status": "ok", "service": "api", "version": settings.app_version}


@router.get("/ready")
async def readiness(session: SessionDep) -> dict[str, str]:
    await session.execute(text("SELECT 1"))
    return {"status": "ok", "database": "ready"}
