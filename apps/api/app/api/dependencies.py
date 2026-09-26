from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Annotated

from fastapi import Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import token_hash
from app.db.session import get_session
from app.models.domain import User, UserSession

SESSION_COOKIE = "dotacjeai_session"
CSRF_COOKIE = "dotacjeai_csrf"

SessionDep = Annotated[AsyncSession, Depends(get_session)]


@dataclass
class Identity:
    user: User
    login_session: UserSession


def _as_utc(value: datetime) -> datetime:
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)


async def get_current_identity(request: Request, session: SessionDep) -> Identity:
    raw_token = request.cookies.get(SESSION_COOKIE)
    if not raw_token:
        raise HTTPException(status_code=401, detail="Wymagane jest zalogowanie.")
    login_session = await session.scalar(
        select(UserSession).where(UserSession.token_hash == token_hash(raw_token))
    )
    now = datetime.now(UTC)
    if not login_session or _as_utc(login_session.expires_at) <= now:
        raise HTTPException(status_code=401, detail="Sesja wygasła.")
    user = await session.get(User, login_session.user_id)
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="Konto jest nieaktywne.")
    return Identity(user=user, login_session=login_session)


IdentityDep = Annotated[Identity, Depends(get_current_identity)]


async def require_csrf(request: Request, identity: IdentityDep) -> Identity:
    header_token = request.headers.get("x-csrf-token", "")
    cookie_token = request.cookies.get(CSRF_COOKIE, "")
    if not header_token or header_token != cookie_token:
        raise HTTPException(status_code=403, detail="Nieprawidłowy token CSRF.")
    if token_hash(header_token) != identity.login_session.csrf_token_hash:
        raise HTTPException(status_code=403, detail="Nieprawidłowy token CSRF.")
    return identity


CsrfIdentityDep = Annotated[Identity, Depends(require_csrf)]
