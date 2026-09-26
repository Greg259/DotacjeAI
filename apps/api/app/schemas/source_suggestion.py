import ipaddress
import uuid
from datetime import datetime

from pydantic import BaseModel, Field, HttpUrl, field_validator


class SourceSuggestionPayload(BaseModel):
    title: str | None = Field(default=None, max_length=255)
    url: HttpUrl
    note: str | None = Field(default=None, max_length=1000)

    @field_validator("url")
    @classmethod
    def public_https_url(cls, value: HttpUrl) -> HttpUrl:
        if value.scheme != "https":
            raise ValueError("Dozwolone są wyłącznie adresy HTTPS.")
        hostname = (value.host or "").rstrip(".").lower()
        if hostname in {"localhost", "localhost.localdomain"} or hostname.endswith(".local"):
            raise ValueError("Adres lokalny nie jest dozwolony.")
        try:
            address = ipaddress.ip_address(hostname)
        except ValueError:
            address = None
        if address is not None and not address.is_global:
            raise ValueError("Prywatny lub lokalny adres IP nie jest dozwolony.")
        return value

    @field_validator("title", "note")
    @classmethod
    def strip_optional(cls, value: str | None) -> str | None:
        return (value.strip() or None) if value else None


class SourceSuggestionResponse(BaseModel):
    id: uuid.UUID
    title: str | None
    url: str
    note: str | None
    status: str
    reviewer_note: str | None
    created_at: datetime
    reviewed_at: datetime | None
