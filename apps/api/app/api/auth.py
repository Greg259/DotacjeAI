from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, HTTPException, Request, Response
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from sqlalchemy import delete, select
from sqlalchemy.orm import selectinload

from app.api.dependencies import (
    CSRF_COOKIE,
    SESSION_COOKIE,
    CsrfIdentityDep,
    IdentityDep,
    SessionDep,
)
from app.core.config import get_settings
from app.core.security import hash_password, new_token, token_hash, verify_password
from app.models.domain import (
    ProfileInvestmentCategory,
    PropertyProfile,
    SourceSuggestion,
    User,
    UserSession,
)
from app.models.enums import UserRole
from app.schemas.user import (
    AuthResponse,
    Credentials,
    DeleteAccountRequest,
    RegistrationRequest,
    UserResponse,
)

router = APIRouter(prefix="/auth", tags=["accounts"])
settings = get_settings()
DUMMY_PASSWORD_HASH = hash_password("not-a-real-user-password")


def _client_ip(request: Request) -> str | None:
    forwarded = request.headers.get("x-forwarded-for", "")
    return forwarded.split(",", 1)[0].strip() or (request.client.host if request.client else None)


def _set_auth_cookies(response: Response, session_token: str, csrf_token: str) -> None:
    max_age = settings.session_days * 24 * 60 * 60
    response.set_cookie(
        SESSION_COOKIE,
        session_token,
        max_age=max_age,
        httponly=True,
        secure=settings.session_cookie_secure,
        samesite="lax",
        path="/",
    )
    response.set_cookie(
        CSRF_COOKIE,
        csrf_token,
        max_age=max_age,
        httponly=False,
        secure=settings.session_cookie_secure,
        samesite="lax",
        path="/",
    )


def _clear_auth_cookies(response: Response) -> None:
    response.delete_cookie(SESSION_COOKIE, path="/")
    response.delete_cookie(CSRF_COOKIE, path="/")


async def _start_session(request: Request, session: SessionDep, user: User) -> tuple[str, str]:
    session_token = new_token()
    csrf_token = new_token()
    now = datetime.now(UTC)
    session.add(
        UserSession(
            user_id=user.id,
            token_hash=token_hash(session_token),
            csrf_token_hash=token_hash(csrf_token),
            expires_at=now + timedelta(days=settings.session_days),
            user_agent=request.headers.get("user-agent", "")[:500] or None,
            ip_address=_client_ip(request),
        )
    )
    user.last_login_at = now
    await session.commit()
    return session_token, csrf_token


@router.post("/register", response_model=AuthResponse, status_code=201)
async def register(payload: RegistrationRequest, request: Request, session: SessionDep):
    if not payload.accept_terms or not payload.accept_privacy:
        raise HTTPException(
            status_code=422,
            detail="Zaakceptowanie regulaminu i polityki prywatności jest wymagane.",
        )
    if await session.scalar(select(User.id).where(User.username == payload.username)):
        raise HTTPException(status_code=409, detail="Ta nazwa użytkownika jest zajęta.")
    now = datetime.now(UTC)
    user = User(
        username=payload.username,
        password_hash=hash_password(payload.password),
        role=UserRole.USER,
        terms_version=settings.terms_version,
        accepted_terms_at=now,
        accepted_privacy_at=now,
    )
    session.add(user)
    await session.flush()
    session_token, csrf_token = await _start_session(request, session, user)
    response = JSONResponse(
        status_code=201,
        content=jsonable_encoder(AuthResponse(user=UserResponse.model_validate(user))),
    )
    _set_auth_cookies(response, session_token, csrf_token)
    return response


@router.post("/login", response_model=AuthResponse)
async def login(payload: Credentials, request: Request, session: SessionDep):
    user = await session.scalar(select(User).where(User.username == payload.username))
    encoded_hash = user.password_hash if user else DUMMY_PASSWORD_HASH
    password_matches = verify_password(payload.password, encoded_hash)
    if not user or not password_matches or not user.is_active:
        raise HTTPException(status_code=401, detail="Nieprawidłowa nazwa lub hasło.")
    session_token, csrf_token = await _start_session(request, session, user)
    response = JSONResponse(
        content=jsonable_encoder(AuthResponse(user=UserResponse.model_validate(user)))
    )
    _set_auth_cookies(response, session_token, csrf_token)
    return response


@router.get("/me", response_model=UserResponse)
async def current_user(identity: IdentityDep):
    return UserResponse.model_validate(identity.user)


@router.post("/logout", status_code=204)
async def logout(identity: CsrfIdentityDep, session: SessionDep):
    await session.delete(identity.login_session)
    await session.commit()
    response = Response(status_code=204)
    _clear_auth_cookies(response)
    return response


@router.get("/export")
async def export_account(identity: IdentityDep, session: SessionDep):
    profiles = list(
        (
            await session.scalars(
                select(PropertyProfile)
                .where(PropertyProfile.user_id == identity.user.id)
                .options(
                    selectinload(PropertyProfile.location),
                    selectinload(PropertyProfile.investment_categories),
                )
                .order_by(PropertyProfile.created_at)
            )
        ).all()
    )
    source_suggestions = list(
        (
            await session.scalars(
                select(SourceSuggestion)
                .where(SourceSuggestion.user_id == identity.user.id)
                .order_by(SourceSuggestion.created_at)
            )
        ).all()
    )
    payload = {
        "exported_at": datetime.now(UTC),
        "account": UserResponse.model_validate(identity.user),
        "profiles": [
            {
                "id": profile.id,
                "name": profile.name,
                "profile_kind": profile.profile_kind,
                "location": (
                    {
                        "id": profile.location.id,
                        "name": profile.location.name,
                        "slug": profile.location.slug,
                        "type": profile.location.location_type,
                    }
                    if profile.location
                    else None
                ),
                "beneficiary_type": profile.beneficiary_type,
                "property_type": profile.property_type,
                "building_state": profile.building_state,
                "current_heat_source": profile.current_heat_source,
                "year_built": profile.year_built,
                "heated_area_m2": profile.heated_area_m2,
                "annual_household_income_pln": profile.annual_household_income_pln,
                "household_members": profile.household_members,
                "business_name": profile.business_name,
                "business_size": profile.business_size,
                "legal_form": profile.legal_form,
                "established_year": profile.established_year,
                "employee_count": profile.employee_count,
                "annual_turnover_pln": profile.annual_turnover_pln,
                "project_budget_pln": profile.project_budget_pln,
                "own_contribution_pln": profile.own_contribution_pln,
                "de_minimis_aid_eur": profile.de_minimis_aid_eur,
                "is_startup": profile.is_startup,
                "has_vc_investor": profile.has_vc_investor,
                "consortium_planned": profile.consortium_planned,
                "industry_codes": profile.industry_codes,
                "investment_categories": [
                    item.investment_category for item in profile.investment_categories
                ],
                "created_at": profile.created_at,
                "updated_at": profile.updated_at,
            }
            for profile in profiles
        ],
        "source_suggestions": [
            {
                "id": item.id,
                "title": item.title,
                "url": item.url,
                "note": item.note,
                "status": item.status,
                "reviewer_note": item.reviewer_note,
                "created_at": item.created_at,
                "reviewed_at": item.reviewed_at,
            }
            for item in source_suggestions
        ],
    }
    return JSONResponse(
        content=jsonable_encoder(payload),
        headers={"Content-Disposition": 'attachment; filename="dotacjeai-dane.json"'},
    )


@router.delete("/me", status_code=204)
async def delete_account(
    payload: DeleteAccountRequest, identity: CsrfIdentityDep, session: SessionDep
):
    if not verify_password(payload.password, identity.user.password_hash):
        raise HTTPException(status_code=401, detail="Nieprawidłowe hasło.")
    profile_ids = select(PropertyProfile.id).where(PropertyProfile.user_id == identity.user.id)
    await session.execute(
        delete(ProfileInvestmentCategory).where(
            ProfileInvestmentCategory.profile_id.in_(profile_ids)
        )
    )
    await session.execute(
        delete(PropertyProfile).where(PropertyProfile.user_id == identity.user.id)
    )
    await session.execute(
        delete(SourceSuggestion).where(SourceSuggestion.user_id == identity.user.id)
    )
    await session.execute(delete(UserSession).where(UserSession.user_id == identity.user.id))
    await session.execute(delete(User).where(User.id == identity.user.id))
    await session.commit()
    response = Response(status_code=204)
    _clear_auth_cookies(response)
    return response
