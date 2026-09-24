from datetime import date
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator

from app.models.enums import (
    BeneficiaryType,
    InvestmentCategory,
    ProgramStatus,
    PropertyType,
)
from app.schemas.content import ProgramDetails


class StrictSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")


class FieldEvidence(StrictSchema):
    field: str = Field(min_length=1, max_length=100)
    quote: str = Field(min_length=1, max_length=1000)
    locator: str = Field(min_length=1, max_length=500)
    method: Literal["rule", "llm"]
    confidence: float = Field(ge=0, le=1)


class ExtractionWarning(StrictSchema):
    code: str = Field(min_length=1, max_length=100)
    message: str = Field(min_length=1, max_length=1000)
    fields: list[str] = Field(default_factory=list)


class ExtractionCandidate(StrictSchema):
    schema_version: Literal["extraction-v1", "extraction-v2"] = "extraction-v2"
    slug: str = Field(pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$", max_length=200)
    title: str = Field(min_length=3, max_length=500)
    organizer: str = Field(min_length=2, max_length=255)
    summary: str | None = Field(default=None, max_length=4000)
    status: ProgramStatus = ProgramStatus.UNKNOWN
    application_start: date | None = None
    application_end: date | None = None
    max_amount: Decimal | None = Field(default=None, ge=0, max_digits=14, decimal_places=2)
    support_percent: Decimal | None = Field(
        default=None, ge=0, le=100, max_digits=5, decimal_places=2
    )
    currency: Literal["PLN"] = "PLN"
    location_slugs: list[str] = Field(default_factory=list)
    beneficiary_types: list[BeneficiaryType] = Field(default_factory=list)
    property_types: list[PropertyType] = Field(default_factory=list)
    investment_categories: list[InvestmentCategory] = Field(default_factory=list)
    official_url: HttpUrl
    document_urls: list[HttpUrl] = Field(default_factory=list)
    details: ProgramDetails = Field(default_factory=ProgramDetails)
    evidence: list[FieldEvidence] = Field(default_factory=list)
    warnings: list[ExtractionWarning] = Field(default_factory=list)

    @field_validator(
        "location_slugs",
        "beneficiary_types",
        "property_types",
        "investment_categories",
        "document_urls",
    )
    @classmethod
    def unique_items(cls, value: list):
        return list(dict.fromkeys(value))

    def missing_critical_evidence(self) -> list[str]:
        evidenced = {item.field for item in self.evidence}
        required = {"status", "official_url"}
        if self.application_end is not None:
            required.add("application_end")
        if self.max_amount is not None:
            required.add("max_amount")
        if self.support_percent is not None:
            required.add("support_percent")
        return sorted(required - evidenced)
