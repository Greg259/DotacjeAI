import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict

from app.models.enums import (
    BeneficiaryType,
    DocumentType,
    InvestmentCategory,
    ProgramStatus,
    PropertyType,
)
from app.schemas.content import ProgramDetails


class LocationItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str
    slug: str
    location_type: str


class ProgramItem(BaseModel):
    id: uuid.UUID
    slug: str
    title: str
    organizer: str
    summary: str | None
    status: ProgramStatus
    application_start: date | None
    application_end: date | None
    max_amount: Decimal | None
    support_percent: Decimal | None
    currency: str
    last_verified_at: datetime | None
    official_url: str | None
    locations: list[LocationItem]
    property_types: list[PropertyType]
    beneficiary_types: list[BeneficiaryType]
    investment_categories: list[InvestmentCategory]


class ProgramListResponse(BaseModel):
    items: list[ProgramItem]
    total: int
    limit: int
    offset: int


class ProgramDocumentItem(BaseModel):
    title: str
    url: str
    document_type: DocumentType
    is_available: bool
    last_checked_at: datetime | None


class ProgramVersionItem(BaseModel):
    version_number: int
    change_summary: str | None
    approved_at: datetime


class ProgramDetail(ProgramItem):
    documents: list[ProgramDocumentItem]
    versions: list[ProgramVersionItem]
    details: ProgramDetails
