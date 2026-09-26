import uuid

from fastapi import APIRouter, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.api.dependencies import CsrfIdentityDep, IdentityDep, SessionDep
from app.models.domain import (
    Location,
    ProfileInvestmentCategory,
    PropertyProfile,
)
from app.models.enums import (
    BeneficiaryType,
    BuildingState,
    BusinessLegalForm,
    BusinessSize,
    HeatSource,
    InvestmentCategory,
    ProfileKind,
    PropertyType,
)
from app.schemas.matching import ProfileMatchesResponse
from app.schemas.user import (
    LocationOption,
    ProfileOptionsResponse,
    ProfilePayload,
    PropertyProfileResponse,
)
from app.services.matching import match_profile

router = APIRouter(prefix="/profiles", tags=["property-profiles"])


def _serialize(profile: PropertyProfile) -> PropertyProfileResponse:
    location = None
    if profile.location:
        location = LocationOption(
            id=profile.location.id,
            name=profile.location.name,
            slug=profile.location.slug,
            location_type=profile.location.location_type.value,
        )
    return PropertyProfileResponse(
        id=profile.id,
        name=profile.name,
        profile_kind=profile.profile_kind,
        location=location,
        beneficiary_type=profile.beneficiary_type,
        property_type=profile.property_type,
        building_state=profile.building_state,
        current_heat_source=profile.current_heat_source,
        year_built=profile.year_built,
        heated_area_m2=profile.heated_area_m2,
        annual_household_income_pln=profile.annual_household_income_pln,
        household_members=profile.household_members,
        business_name=profile.business_name,
        business_size=profile.business_size,
        legal_form=profile.legal_form,
        established_year=profile.established_year,
        employee_count=profile.employee_count,
        annual_turnover_pln=profile.annual_turnover_pln,
        project_budget_pln=profile.project_budget_pln,
        own_contribution_pln=profile.own_contribution_pln,
        de_minimis_aid_eur=profile.de_minimis_aid_eur,
        is_startup=profile.is_startup,
        has_vc_investor=profile.has_vc_investor,
        consortium_planned=profile.consortium_planned,
        industry_codes=profile.industry_codes,
        investment_categories=[item.investment_category for item in profile.investment_categories],
        created_at=profile.created_at,
        updated_at=profile.updated_at,
    )


async def _owned_profile(
    profile_id: uuid.UUID, user_id: uuid.UUID, session: SessionDep
) -> PropertyProfile:
    profile = await session.scalar(
        select(PropertyProfile)
        .where(PropertyProfile.id == profile_id, PropertyProfile.user_id == user_id)
        .options(
            selectinload(PropertyProfile.location),
            selectinload(PropertyProfile.investment_categories),
        )
    )
    if not profile:
        raise HTTPException(status_code=404, detail="Nie znaleziono profilu.")
    return profile


async def _validate_location(location_id: uuid.UUID | None, session: SessionDep) -> None:
    if location_id and not await session.get(Location, location_id):
        raise HTTPException(status_code=422, detail="Nieprawidłowa lokalizacja.")


async def _ensure_unique_name(
    name: str,
    user_id: uuid.UUID,
    session: SessionDep,
    excluding: uuid.UUID | None = None,
) -> None:
    statement = select(PropertyProfile.id).where(
        PropertyProfile.user_id == user_id, PropertyProfile.name == name
    )
    if excluding:
        statement = statement.where(PropertyProfile.id != excluding)
    if await session.scalar(statement):
        raise HTTPException(status_code=409, detail="Profil o tej nazwie już istnieje.")


@router.get("/options", response_model=ProfileOptionsResponse)
async def profile_options(identity: IdentityDep, session: SessionDep):
    del identity
    locations = list(
        (
            await session.scalars(select(Location).order_by(Location.location_type, Location.name))
        ).all()
    )
    return ProfileOptionsResponse(
        locations=[
            LocationOption(
                id=item.id,
                name=item.name,
                slug=item.slug,
                location_type=item.location_type.value,
            )
            for item in locations
        ],
        beneficiary_types=list(BeneficiaryType),
        property_types=[
            PropertyType.SINGLE_FAMILY_HOUSE,
            PropertyType.APARTMENT,
            PropertyType.HOUSING_COMMUNITY,
        ],
        building_states=list(BuildingState),
        heat_sources=list(HeatSource),
        investment_categories=list(InvestmentCategory),
        profile_kinds=list(ProfileKind),
        business_sizes=list(BusinessSize),
        legal_forms=list(BusinessLegalForm),
    )


@router.get("", response_model=list[PropertyProfileResponse])
async def list_profiles(identity: IdentityDep, session: SessionDep):
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
    return [_serialize(item) for item in profiles]


@router.get("/{profile_id}", response_model=PropertyProfileResponse)
async def get_profile(profile_id: uuid.UUID, identity: IdentityDep, session: SessionDep):
    return _serialize(await _owned_profile(profile_id, identity.user.id, session))


@router.get("/{profile_id}/matches", response_model=ProfileMatchesResponse)
async def profile_matches(profile_id: uuid.UUID, identity: IdentityDep, session: SessionDep):
    profile = await _owned_profile(profile_id, identity.user.id, session)
    return await match_profile(session, profile)


@router.post("", response_model=PropertyProfileResponse, status_code=201)
async def create_profile(payload: ProfilePayload, identity: CsrfIdentityDep, session: SessionDep):
    await _validate_location(payload.location_id, session)
    await _ensure_unique_name(payload.name, identity.user.id, session)
    profile = PropertyProfile(
        user_id=identity.user.id,
        location_id=payload.location_id,
        name=payload.name,
        profile_kind=payload.profile_kind,
        beneficiary_type=payload.beneficiary_type,
        property_type=payload.property_type
        if payload.profile_kind == ProfileKind.PROPERTY
        else None,
        building_state=payload.building_state
        if payload.profile_kind == ProfileKind.PROPERTY
        else None,
        current_heat_source=(
            payload.current_heat_source if payload.profile_kind == ProfileKind.PROPERTY else None
        ),
        year_built=payload.year_built if payload.profile_kind == ProfileKind.PROPERTY else None,
        heated_area_m2=(
            payload.heated_area_m2 if payload.profile_kind == ProfileKind.PROPERTY else None
        ),
        annual_household_income_pln=(
            payload.annual_household_income_pln
            if payload.profile_kind == ProfileKind.PROPERTY
            else None
        ),
        household_members=(
            payload.household_members if payload.profile_kind == ProfileKind.PROPERTY else None
        ),
        business_name=payload.business_name
        if payload.profile_kind == ProfileKind.BUSINESS
        else None,
        business_size=payload.business_size
        if payload.profile_kind == ProfileKind.BUSINESS
        else None,
        legal_form=payload.legal_form if payload.profile_kind == ProfileKind.BUSINESS else None,
        established_year=(
            payload.established_year if payload.profile_kind == ProfileKind.BUSINESS else None
        ),
        employee_count=(
            payload.employee_count if payload.profile_kind == ProfileKind.BUSINESS else None
        ),
        annual_turnover_pln=(
            payload.annual_turnover_pln if payload.profile_kind == ProfileKind.BUSINESS else None
        ),
        project_budget_pln=payload.project_budget_pln,
        own_contribution_pln=payload.own_contribution_pln,
        de_minimis_aid_eur=(
            payload.de_minimis_aid_eur if payload.profile_kind == ProfileKind.BUSINESS else None
        ),
        is_startup=payload.is_startup if payload.profile_kind == ProfileKind.BUSINESS else None,
        has_vc_investor=(
            payload.has_vc_investor if payload.profile_kind == ProfileKind.BUSINESS else None
        ),
        consortium_planned=(
            payload.consortium_planned if payload.profile_kind == ProfileKind.BUSINESS else None
        ),
        industry_codes=payload.industry_codes
        if payload.profile_kind == ProfileKind.BUSINESS
        else [],
        investment_categories=[
            ProfileInvestmentCategory(investment_category=item)
            for item in payload.investment_categories
        ],
    )
    session.add(profile)
    await session.commit()
    return _serialize(await _owned_profile(profile.id, identity.user.id, session))


@router.put("/{profile_id}", response_model=PropertyProfileResponse)
async def update_profile(
    profile_id: uuid.UUID,
    payload: ProfilePayload,
    identity: CsrfIdentityDep,
    session: SessionDep,
):
    profile = await _owned_profile(profile_id, identity.user.id, session)
    await _validate_location(payload.location_id, session)
    await _ensure_unique_name(payload.name, identity.user.id, session, profile.id)
    profile.name = payload.name
    profile.location_id = payload.location_id
    profile.profile_kind = payload.profile_kind
    profile.beneficiary_type = payload.beneficiary_type
    is_property = payload.profile_kind == ProfileKind.PROPERTY
    profile.property_type = payload.property_type if is_property else None
    profile.building_state = payload.building_state if is_property else None
    profile.current_heat_source = payload.current_heat_source if is_property else None
    profile.year_built = payload.year_built if is_property else None
    profile.heated_area_m2 = payload.heated_area_m2 if is_property else None
    profile.annual_household_income_pln = (
        payload.annual_household_income_pln if is_property else None
    )
    profile.household_members = payload.household_members if is_property else None
    profile.business_name = payload.business_name if not is_property else None
    profile.business_size = payload.business_size if not is_property else None
    profile.legal_form = payload.legal_form if not is_property else None
    profile.established_year = payload.established_year if not is_property else None
    profile.employee_count = payload.employee_count if not is_property else None
    profile.annual_turnover_pln = payload.annual_turnover_pln if not is_property else None
    profile.project_budget_pln = payload.project_budget_pln
    profile.own_contribution_pln = payload.own_contribution_pln
    profile.de_minimis_aid_eur = payload.de_minimis_aid_eur if not is_property else None
    profile.is_startup = payload.is_startup if not is_property else None
    profile.has_vc_investor = payload.has_vc_investor if not is_property else None
    profile.consortium_planned = payload.consortium_planned if not is_property else None
    profile.industry_codes = payload.industry_codes if not is_property else []
    profile.investment_categories = [
        ProfileInvestmentCategory(investment_category=item)
        for item in payload.investment_categories
    ]
    await session.commit()
    return _serialize(await _owned_profile(profile.id, identity.user.id, session))


@router.delete("/{profile_id}", status_code=204)
async def delete_profile(profile_id: uuid.UUID, identity: CsrfIdentityDep, session: SessionDep):
    profile = await _owned_profile(profile_id, identity.user.id, session)
    await session.delete(profile)
    await session.commit()
