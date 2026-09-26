import re
import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.models.enums import (
    BeneficiaryType,
    BuildingState,
    BusinessLegalForm,
    BusinessSize,
    HeatSource,
    InvestmentCategory,
    ProfileKind,
    PropertyType,
    UserRole,
)

USERNAME_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{2,39}$")
PROFILE_PROPERTY_TYPES = {
    PropertyType.SINGLE_FAMILY_HOUSE,
    PropertyType.APARTMENT,
    PropertyType.HOUSING_COMMUNITY,
}


class Credentials(BaseModel):
    username: str
    password: str = Field(min_length=12, max_length=128)

    @field_validator("username")
    @classmethod
    def normalize_username(cls, value: str) -> str:
        normalized = value.strip().lower()
        if not USERNAME_RE.fullmatch(normalized):
            raise ValueError("Nazwa musi mieć 3–40 znaków: a-z, 0-9, kropka, _ lub -.")
        return normalized


class RegistrationRequest(Credentials):
    accept_terms: bool
    accept_privacy: bool


class DeleteAccountRequest(BaseModel):
    password: str = Field(min_length=1, max_length=128)


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    username: str
    role: UserRole
    terms_version: str
    accepted_terms_at: datetime
    accepted_privacy_at: datetime
    created_at: datetime


class AuthResponse(BaseModel):
    user: UserResponse


class LocationOption(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    location_type: str


class ProfilePayload(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    profile_kind: ProfileKind = ProfileKind.PROPERTY
    location_id: uuid.UUID | None = None
    beneficiary_type: BeneficiaryType
    property_type: PropertyType | None = None
    building_state: BuildingState | None = None
    current_heat_source: HeatSource | None = None
    year_built: int | None = Field(default=None, ge=1800, le=2100)
    heated_area_m2: Decimal | None = Field(default=None, gt=0, le=100000)
    annual_household_income_pln: Decimal | None = Field(default=None, ge=0, le=10**15)
    household_members: int | None = Field(default=None, ge=1, le=100)
    business_name: str | None = Field(default=None, max_length=255)
    business_size: BusinessSize | None = None
    legal_form: BusinessLegalForm | None = None
    established_year: int | None = Field(default=None, ge=1800, le=2100)
    employee_count: int | None = Field(default=None, ge=0, le=10_000_000)
    annual_turnover_pln: Decimal | None = Field(default=None, ge=0, le=10**15)
    project_budget_pln: Decimal | None = Field(default=None, ge=0, le=10**15)
    own_contribution_pln: Decimal | None = Field(default=None, ge=0, le=10**15)
    de_minimis_aid_eur: Decimal | None = Field(default=None, ge=0, le=10**12)
    is_startup: bool | None = None
    has_vc_investor: bool | None = None
    consortium_planned: bool | None = None
    industry_codes: list[str] = Field(default_factory=list, max_length=20)
    investment_categories: list[InvestmentCategory] = Field(min_length=1, max_length=16)

    @field_validator("name")
    @classmethod
    def strip_name(cls, value: str) -> str:
        return value.strip()

    @field_validator("property_type")
    @classmethod
    def validate_property_type(cls, value: PropertyType | None) -> PropertyType | None:
        if value is not None and value not in PROFILE_PROPERTY_TYPES:
            raise ValueError("Nieobsługiwany typ profilu nieruchomości.")
        return value

    @field_validator("business_name")
    @classmethod
    def strip_business_name(cls, value: str | None) -> str | None:
        return value.strip() if value else None

    @field_validator("industry_codes")
    @classmethod
    def normalize_industry_codes(cls, value: list[str]) -> list[str]:
        normalized = [item.strip().upper() for item in value if item.strip()]
        if any(len(item) > 20 for item in normalized):
            raise ValueError("Kod branży może mieć maksymalnie 20 znaków.")
        return list(dict.fromkeys(normalized))

    @field_validator("investment_categories")
    @classmethod
    def unique_categories(cls, value: list[InvestmentCategory]) -> list[InvestmentCategory]:
        return list(dict.fromkeys(value))

    @model_validator(mode="after")
    def validate_profile_kind(self):
        if (
            self.project_budget_pln is not None
            and self.own_contribution_pln is not None
            and self.own_contribution_pln > self.project_budget_pln
        ):
            raise ValueError("Wkład własny nie może przekraczać budżetu projektu.")
        if self.profile_kind == ProfileKind.PROPERTY:
            if not self.property_type or not self.building_state or not self.current_heat_source:
                raise ValueError("Profil nieruchomości wymaga typu, stanu i źródła ciepła.")
            if self.beneficiary_type in {
                BeneficiaryType.ENTERPRISE,
                BeneficiaryType.SME,
                BeneficiaryType.RESEARCH_ORGANIZATION,
                BeneficiaryType.CONSORTIUM,
            }:
                raise ValueError("Nieprawidłowy beneficjent profilu nieruchomości.")
        else:
            if not self.business_name or not self.business_size or not self.legal_form:
                raise ValueError("Profil przedsiębiorstwa wymaga nazwy, wielkości i formy prawnej.")
            if self.beneficiary_type not in {
                BeneficiaryType.ENTERPRISE,
                BeneficiaryType.SME,
                BeneficiaryType.RESEARCH_ORGANIZATION,
                BeneficiaryType.CONSORTIUM,
            }:
                raise ValueError("Nieprawidłowy beneficjent profilu przedsiębiorstwa.")
        return self


class PropertyProfileResponse(BaseModel):
    id: uuid.UUID
    name: str
    profile_kind: ProfileKind
    location: LocationOption | None
    beneficiary_type: BeneficiaryType
    property_type: PropertyType | None
    building_state: BuildingState | None
    current_heat_source: HeatSource | None
    year_built: int | None
    heated_area_m2: Decimal | None
    annual_household_income_pln: Decimal | None
    household_members: int | None
    business_name: str | None
    business_size: BusinessSize | None
    legal_form: BusinessLegalForm | None
    established_year: int | None
    employee_count: int | None
    annual_turnover_pln: Decimal | None
    project_budget_pln: Decimal | None
    own_contribution_pln: Decimal | None
    de_minimis_aid_eur: Decimal | None
    is_startup: bool | None
    has_vc_investor: bool | None
    consortium_planned: bool | None
    industry_codes: list[str]
    investment_categories: list[InvestmentCategory]
    created_at: datetime
    updated_at: datetime


class ProfileOptionsResponse(BaseModel):
    locations: list[LocationOption]
    beneficiary_types: list[BeneficiaryType]
    property_types: list[PropertyType]
    building_states: list[BuildingState]
    heat_sources: list[HeatSource]
    investment_categories: list[InvestmentCategory]
    profile_kinds: list[ProfileKind]
    business_sizes: list[BusinessSize]
    legal_forms: list[BusinessLegalForm]
