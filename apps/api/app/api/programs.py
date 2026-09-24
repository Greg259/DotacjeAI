from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.session import get_session
from app.models.domain import (
    Location,
    Program,
    ProgramBeneficiaryType,
    ProgramDocument,
    ProgramInvestmentCategory,
    ProgramLocation,
    ProgramPropertyType,
    ProgramVersion,
)
from app.models.enums import (
    BeneficiaryType,
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
        investment_categories=[
            item.investment_category for item in program.investment_categories
        ],
    )


@router.get("", response_model=ProgramListResponse)
async def list_programs(
    session: SessionDep,
    status: ProgramStatus | None = None,
    location: str | None = None,
    category: InvestmentCategory | None = None,
    property_type: PropertyType | None = None,
    beneficiary_type: BeneficiaryType | None = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> ProgramListResponse:
    filters = [Program.is_published.is_(True)]
    if status:
        filters.append(Program.status == status)
    if location:
        filters.append(
            Program.locations.any(
                ProgramLocation.location.has(Location.slug == location.lower())
            )
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

    total = await session.scalar(select(func.count(Program.id)).where(*filters))
    result = await session.scalars(
        select(Program)
        .where(*filters)
        .options(*_options())
        .order_by(Program.application_end.asc().nullslast(), Program.title.asc())
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
