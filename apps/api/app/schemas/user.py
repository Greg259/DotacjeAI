import re
import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.enums import (
    BeneficiaryType,
    BuildingState,
    HeatSource,
    InvestmentCategory,
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
    location_id: uuid.UUID | None = None
    beneficiary_type: BeneficiaryType
    property_type: PropertyType
    building_state: BuildingState
    current_heat_source: HeatSource
    year_built: int | None = Field(default=None, ge=1800, le=2100)
    heated_area_m2: Decimal | None = Field(default=None, gt=0, le=100000)
    investment_categories: list[InvestmentCategory] = Field(min_length=1, max_length=8)

    @field_validator("name")
    @classmethod
    def strip_name(cls, value: str) -> str:
        return value.strip()

    @field_validator("property_type")
    @classmethod
    def validate_property_type(cls, value: PropertyType) -> PropertyType:
        if value not in PROFILE_PROPERTY_TYPES:
            raise ValueError("Nieobsługiwany typ profilu nieruchomości.")
        return value

    @field_validator("investment_categories")
    @classmethod
    def unique_categories(
        cls, value: list[InvestmentCategory]
    ) -> list[InvestmentCategory]:
        return list(dict.fromkeys(value))


class PropertyProfileResponse(BaseModel):
    id: uuid.UUID
    name: str
    location: LocationOption | None
    beneficiary_type: BeneficiaryType
    property_type: PropertyType
    building_state: BuildingState
    current_heat_source: HeatSource
    year_built: int | None
    heated_area_m2: Decimal | None
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
