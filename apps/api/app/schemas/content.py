from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class StrictContentSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ProgramContentItem(StrictContentSchema):
    title: str = Field(min_length=2, max_length=240)
    description: str = Field(min_length=2, max_length=2000)
    source_reference: str | None = Field(default=None, max_length=500)
    source_url: HttpUrl | None = None


class FundingOption(StrictContentSchema):
    name: str = Field(min_length=2, max_length=240)
    description: str = Field(min_length=2, max_length=2000)
    support_percent: Decimal | None = Field(
        default=None, ge=0, le=100, max_digits=5, decimal_places=2
    )
    max_amount: Decimal | None = Field(
        default=None, ge=0, max_digits=14, decimal_places=2
    )
    currency: Literal["PLN"] = "PLN"
    source_reference: str | None = Field(default=None, max_length=500)
    source_url: HttpUrl | None = None


class ApplicationResource(StrictContentSchema):
    title: str = Field(min_length=2, max_length=500)
    url: HttpUrl
    resource_type: Literal[
        "application_form",
        "statement",
        "instructions",
        "regulations",
        "application_portal",
        "official_page",
        "other",
    ]
    description: str | None = Field(default=None, max_length=1000)


class ProgramDetails(StrictContentSchema):
    key_takeaways: list[ProgramContentItem] = Field(default_factory=list, max_length=20)
    eligible_applicants: list[ProgramContentItem] = Field(default_factory=list, max_length=20)
    eligibility_conditions: list[ProgramContentItem] = Field(default_factory=list, max_length=30)
    funding_options: list[FundingOption] = Field(default_factory=list, max_length=20)
    important_information: list[ProgramContentItem] = Field(default_factory=list, max_length=30)
    application_steps: list[ProgramContentItem] = Field(default_factory=list, max_length=20)
    required_documents: list[ProgramContentItem] = Field(default_factory=list, max_length=30)
    application_resources: list[ApplicationResource] = Field(default_factory=list, max_length=30)
