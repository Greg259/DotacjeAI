from fastapi import APIRouter, HTTPException
from sqlalchemy import func, select

from app.api.dependencies import CsrfIdentityDep, IdentityDep, SessionDep
from app.models.domain import SourceSuggestion
from app.models.enums import SuggestionStatus
from app.schemas.source_suggestion import SourceSuggestionPayload, SourceSuggestionResponse

router = APIRouter(prefix="/source-suggestions", tags=["source-suggestions"])


def _serialize(item: SourceSuggestion) -> SourceSuggestionResponse:
    return SourceSuggestionResponse(
        id=item.id,
        title=item.title,
        url=item.url,
        note=item.note,
        status=item.status,
        reviewer_note=item.reviewer_note,
        created_at=item.created_at,
        reviewed_at=item.reviewed_at,
    )


@router.get("", response_model=list[SourceSuggestionResponse])
async def list_suggestions(identity: IdentityDep, session: SessionDep):
    items = list(
        (
            await session.scalars(
                select(SourceSuggestion)
                .where(SourceSuggestion.user_id == identity.user.id)
                .order_by(SourceSuggestion.created_at.desc())
            )
        ).all()
    )
    return [_serialize(item) for item in items]


@router.post("", response_model=SourceSuggestionResponse, status_code=201)
async def create_suggestion(
    payload: SourceSuggestionPayload, identity: CsrfIdentityDep, session: SessionDep
):
    url = str(payload.url)
    existing = await session.scalar(
        select(SourceSuggestion).where(
            SourceSuggestion.user_id == identity.user.id,
            SourceSuggestion.url == url,
        )
    )
    if existing:
        raise HTTPException(status_code=409, detail="Ten adres został już zgłoszony.")
    pending = await session.scalar(
        select(func.count(SourceSuggestion.id)).where(
            SourceSuggestion.user_id == identity.user.id,
            SourceSuggestion.status == SuggestionStatus.PENDING,
        )
    )
    if (pending or 0) >= 5:
        raise HTTPException(
            status_code=429, detail="Możesz mieć maksymalnie 5 oczekujących zgłoszeń."
        )
    item = SourceSuggestion(
        user_id=identity.user.id,
        title=payload.title,
        url=url,
        note=payload.note,
        status=SuggestionStatus.PENDING,
    )
    session.add(item)
    await session.commit()
    await session.refresh(item)
    return _serialize(item)
