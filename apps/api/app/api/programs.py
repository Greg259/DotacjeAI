from datetime import date
from decimal import Decimal
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.session import get_session
from app.models.domain import (
    Location,
    Program,
    ProgramBeneficiaryType,
    ProgramBusinessSize,
    ProgramDocument,
    ProgramInvestmentCategory,
    ProgramLocation,
    ProgramPropertyType,
    ProgramVersion,
)
from app.models.enums import (
    BeneficiaryType,
    BusinessSize,
    InvestmentCategory,
    ProgramStatus,
    PropertyType,
)
from app.schemas.content import ProgramDetails
from app.schemas.program import (
    LocationItem,
    ProgramDetail,
    ProgramDocumentItem,
    ProgramItem,
    ProgramListResponse,
    ProgramVersionItem,
)

router = APIRouter(prefix="/programs", tags=["programs"])
SessionDep = Annotated[AsyncSession, Depends(get_session)]


def _options():
    return (
        selectinload(Program.primary_source),
        selectinload(Program.locations).selectinload(ProgramLocation.location),
        selectinload(Program.property_types),
        selectinload(Program.beneficiary_types),
        selectinload(Program.investment_categories),
        selectinload(Program.business_sizes),
    )


def _serialize(program: Program) -> ProgramItem:
    return ProgramItem(
        id=program.id,
        slug=program.slug,
        title=program.title,
        organizer=program.organizer,
        summary=program.summary,
        status=program.status,
        application_start=program.application_start,
        application_end=program.application_end,
        max_amount=program.max_amount,
        support_percent=program.support_percent,
        currency=program.currency,
        last_verified_at=program.last_verified_at,
        official_url=program.primary_source.url if program.primary_source else None,
        locations=[LocationItem.model_validate(item.location) for item in program.locations],
        property_types=[item.property_type for item in program.property_types],
        beneficiary_types=[item.beneficiary_type for item in program.beneficiary_types],
        investment_categories=[item.investment_category for item in program.investment_categories],
        business_sizes=[item.business_size for item in program.business_sizes],
    )


@router.get("", response_model=ProgramListResponse)
async def list_programs(
    session: SessionDep,
    status: ProgramStatus | None = None,
    location: str | None = None,
    category: InvestmentCategory | None = None,
    property_type: PropertyType | None = None,
    beneficiary_type: BeneficiaryType | None = None,
    business_size: BusinessSize | None = None,
    application_end_from: date | None = None,
    application_end_to: date | None = None,
    min_amount: Annotated[Decimal | None, Query(ge=0)] = None,
    max_amount: Annotated[Decimal | None, Query(ge=0)] = None,
    min_support_percent: Annotated[Decimal | None, Query(ge=0, le=100)] = None,
    verified_since: date | None = None,
    sort: Literal["ending_soon", "newest", "amount_desc", "title"] = "ending_soon",
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> ProgramListResponse:
    filters = [Program.is_published.is_(True)]
    if status:
        filters.append(Program.status == status)
    if location:
        locations = list((await session.scalars(select(Location))).all())
        target = next((item for item in locations if item.slug == location.lower()), None)
        related_ids = set()
        if target is not None:
            related_ids.add(target.id)
            parent_id = target.parent_id
            while parent_id is not None:
                related_ids.add(parent_id)
                parent = next((item for item in locations if item.id == parent_id), None)
                parent_id = parent.parent_id if parent is not None else None
            pending = [target.id]
            while pending:
                current = pending.pop()
                children = [item.id for item in locations if item.parent_id == current]
                related_ids.update(children)
                pending.extend(children)
        filters.append(
            Program.locations.any(ProgramLocation.location_id.in_(related_ids))
            if related_ids
            else Program.id.is_(None)
        )
    if category:
        filters.append(
            Program.investment_categories.any(
                ProgramInvestmentCategory.investment_category == category
            )
        )
    if property_type:
        filters.append(
            Program.property_types.any(ProgramPropertyType.property_type == property_type)
        )
    if beneficiary_type:
        filters.append(
            Program.beneficiary_types.any(
                ProgramBeneficiaryType.beneficiary_type == beneficiary_type
            )
        )
    if business_size:
        filters.append(
            Program.business_sizes.any(ProgramBusinessSize.business_size == business_size)
        )
    if application_end_from:
        filters.append(Program.application_end >= application_end_from)
    if application_end_to:
        filters.append(Program.application_end <= application_end_to)
    if min_amount is not None:
        filters.append(Program.max_amount >= min_amount)
    if max_amount is not None:
        filters.append(Program.max_amount <= max_amount)
    if min_support_percent is not None:
        filters.append(Program.support_percent >= min_support_percent)
    if verified_since:
        filters.append(Program.last_verified_at >= verified_since)

    ordering = {
        "ending_soon": (Program.application_end.asc().nullslast(), Program.title.asc()),
        "newest": (Program.last_verified_at.desc().nullslast(), Program.title.asc()),
        "amount_desc": (Program.max_amount.desc().nullslast(), Program.title.asc()),
        "title": (Program.title.asc(),),
    }[sort]

    total = await session.scalar(select(func.count(Program.id)).where(*filters))
    result = await session.scalars(
        select(Program)
        .where(*filters)
        .options(*_options())
        .order_by(*ordering)
        .limit(limit)
        .offset(offset)
    )
    items = [_serialize(program) for program in result.unique().all()]
    return ProgramListResponse(items=items, total=total or 0, limit=limit, offset=offset)


@router.get("/{slug}", response_model=ProgramDetail)
async def get_program(slug: str, session: SessionDep) -> ProgramDetail:
    program = await session.scalar(
        select(Program)
        .where(Program.slug == slug, Program.is_published.is_(True))
        .options(*_options())
    )
    if program is None:
        raise HTTPException(status_code=404, detail="Program not found")

    documents = (
        await session.scalars(
            select(ProgramDocument)
            .where(ProgramDocument.program_id == program.id)
            .order_by(ProgramDocument.title.asc())
        )
    ).all()
    versions = (
        await session.scalars(
            select(ProgramVersion)
            .where(
                ProgramVersion.program_id == program.id,
                ProgramVersion.approved_at.is_not(None),
            )
            .order_by(ProgramVersion.version_number.desc())
        )
    ).all()

    return ProgramDetail(
        **_serialize(program).model_dump(),
        documents=[
            ProgramDocumentItem(
                title=document.title,
                url=document.url,
                document_type=document.document_type,
                is_available=document.is_available,
                state=document.state,
                state_reason=document.state_reason,
                last_checked_at=document.last_checked_at,
            )
            for document in documents
        ],
        versions=[
            ProgramVersionItem(
                version_number=version.version_number,
                change_summary=version.change_summary,
                approved_at=version.approved_at,
            )
            for version in versions
            if version.approved_at is not None
        ],
        details=ProgramDetails.model_validate(
            versions[0].extracted_data.get("details", {}) if versions else {}
        ),
    )
