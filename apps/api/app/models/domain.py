import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import (
    JSON,
    Boolean,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import (
    BeneficiaryType,
    DocumentType,
    ExtractionStatus,
    InvestmentCategory,
    LlmRunStatus,
    LocationType,
    ProgramStatus,
    PropertyType,
    ReviewReason,
    ReviewStatus,
    SourceType,
)

json_type = JSON().with_variant(JSONB(), "postgresql")


def enum_values(enum_class):
    return [item.value for item in enum_class]


def enum_column(enum_class, length: int):
    return Enum(
        enum_class,
        values_callable=enum_values,
        native_enum=False,
        length=length,
    )


class UuidPrimaryKeyMixin:
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )


class Source(UuidPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "sources"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(160), nullable=False, unique=True)
    url: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    source_type: Mapped[SourceType] = mapped_column(enum_column(SourceType, 20), nullable=False)
    active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="true"
    )
    crawl_interval_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=360)
    last_checked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_success_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_error_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_error_message: Mapped[str | None] = mapped_column(Text)

    snapshots: Mapped[list["SourceSnapshot"]] = relationship(back_populates="source")


class SourceSnapshot(UuidPrimaryKeyMixin, Base):
    __tablename__ = "source_snapshots"
    __table_args__ = (
        Index("ix_source_snapshots_source_fetched", "source_id", "fetched_at"),
        Index("ix_source_snapshots_source_sha256", "source_id", "sha256"),
    )

    source_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("sources.id", ondelete="CASCADE"), nullable=False
    )
    previous_snapshot_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("source_snapshots.id", ondelete="SET NULL")
    )
    fetched_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    final_url: Mapped[str] = mapped_column(Text, nullable=False)
    http_status: Mapped[int] = mapped_column(Integer, nullable=False)
    content_type: Mapped[str | None] = mapped_column(String(255))
    etag: Mapped[str | None] = mapped_column(Text)
    last_modified: Mapped[str | None] = mapped_column(Text)
    sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    normalized_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    storage_path: Mapped[str] = mapped_column(Text, nullable=False)
    diff_path: Mapped[str | None] = mapped_column(Text)
    normalized_text: Mapped[str | None] = mapped_column(Text)
    is_changed: Mapped[bool] = mapped_column(Boolean, nullable=False)

    source: Mapped[Source] = relationship(back_populates="snapshots")


class Location(UuidPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "locations"
    __table_args__ = (UniqueConstraint("parent_id", "location_type", "slug"),)

    parent_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("locations.id", ondelete="CASCADE")
    )
    location_type: Mapped[LocationType] = mapped_column(
        enum_column(LocationType, 20), nullable=False
    )
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    slug: Mapped[str] = mapped_column(String(160), nullable=False)


class Program(UuidPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "programs"
    __table_args__ = (
        Index("ix_programs_public_status", "is_published", "status"),
        Index("ix_programs_dates", "application_start", "application_end"),
    )

    primary_source_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("sources.id", ondelete="SET NULL")
    )
    slug: Mapped[str] = mapped_column(String(200), nullable=False, unique=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    organizer: Mapped[str] = mapped_column(String(255), nullable=False)
    summary: Mapped[str | None] = mapped_column(Text)
    status: Mapped[ProgramStatus] = mapped_column(
        enum_column(ProgramStatus, 20),
        nullable=False,
        default=ProgramStatus.UNKNOWN,
    )
    application_start: Mapped[date | None] = mapped_column(Date)
    application_end: Mapped[date | None] = mapped_column(Date)
    max_amount: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))
    support_percent: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="PLN")
    last_verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    is_published: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )

    primary_source: Mapped[Source | None] = relationship()
    locations: Mapped[list["ProgramLocation"]] = relationship(
        back_populates="program", cascade="all, delete-orphan"
    )
    property_types: Mapped[list["ProgramPropertyType"]] = relationship(
        back_populates="program", cascade="all, delete-orphan"
    )
    beneficiary_types: Mapped[list["ProgramBeneficiaryType"]] = relationship(
        back_populates="program", cascade="all, delete-orphan"
    )
    investment_categories: Mapped[list["ProgramInvestmentCategory"]] = relationship(
        back_populates="program", cascade="all, delete-orphan"
    )


class ProgramLocation(Base):
    __tablename__ = "program_locations"

    program_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("programs.id", ondelete="CASCADE"), primary_key=True
    )
    location_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("locations.id", ondelete="CASCADE"), primary_key=True
    )

    program: Mapped[Program] = relationship(back_populates="locations")
    location: Mapped[Location] = relationship()


class ProgramPropertyType(Base):
    __tablename__ = "program_property_types"

    program_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("programs.id", ondelete="CASCADE"), primary_key=True
    )
    property_type: Mapped[PropertyType] = mapped_column(
        enum_column(PropertyType, 40), primary_key=True
    )

    program: Mapped[Program] = relationship(back_populates="property_types")


class ProgramBeneficiaryType(Base):
    __tablename__ = "program_beneficiary_types"

    program_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("programs.id", ondelete="CASCADE"), primary_key=True
    )
    beneficiary_type: Mapped[BeneficiaryType] = mapped_column(
        enum_column(BeneficiaryType, 40), primary_key=True
    )

    program: Mapped[Program] = relationship(back_populates="beneficiary_types")


class ProgramInvestmentCategory(Base):
    __tablename__ = "program_investment_categories"

    program_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("programs.id", ondelete="CASCADE"), primary_key=True
    )
    investment_category: Mapped[InvestmentCategory] = mapped_column(
        enum_column(InvestmentCategory, 40), primary_key=True
    )

    program: Mapped[Program] = relationship(back_populates="investment_categories")


class ProgramVersion(UuidPrimaryKeyMixin, Base):
    __tablename__ = "program_versions"
    __table_args__ = (UniqueConstraint("program_id", "version_number"),)

    program_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("programs.id", ondelete="CASCADE"), nullable=False
    )
    source_snapshot_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("source_snapshots.id", ondelete="RESTRICT"), nullable=False
    )
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    extracted_data: Mapped[dict[str, Any]] = mapped_column(json_type, nullable=False)
    evidence: Mapped[dict[str, Any]] = mapped_column(json_type, nullable=False)
    change_summary: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class ProgramDocument(UuidPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "program_documents"
    __table_args__ = (UniqueConstraint("program_id", "url"),)

    program_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("programs.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    document_type: Mapped[DocumentType] = mapped_column(
        enum_column(DocumentType, 30), nullable=False
    )
    last_checked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_http_status: Mapped[int | None] = mapped_column(Integer)
    last_error_message: Mapped[str | None] = mapped_column(Text)
    is_available: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="true"
    )


class DocumentVersion(UuidPrimaryKeyMixin, Base):
    __tablename__ = "document_versions"
    __table_args__ = (
        UniqueConstraint("document_id", "sha256"),
        Index("ix_document_versions_document_fetched", "document_id", "fetched_at"),
    )

    document_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("program_documents.id", ondelete="CASCADE"), nullable=False
    )
    fetched_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    content_type: Mapped[str | None] = mapped_column(String(255))
    storage_path: Mapped[str] = mapped_column(Text, nullable=False)
    extracted_text_path: Mapped[str | None] = mapped_column(Text)


class LlmRun(UuidPrimaryKeyMixin, Base):
    __tablename__ = "llm_runs"
    __table_args__ = (Index("ix_llm_runs_created_status", "created_at", "status"),)

    source_snapshot_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("source_snapshots.id", ondelete="SET NULL")
    )
    idempotency_key: Mapped[str | None] = mapped_column(String(64), unique=True)
    request_sha256: Mapped[str | None] = mapped_column(String(64))
    external_id: Mapped[str | None] = mapped_column(String(255))
    provider: Mapped[str] = mapped_column(String(80), nullable=False)
    model: Mapped[str] = mapped_column(String(200), nullable=False)
    prompt_version: Mapped[str] = mapped_column(String(80), nullable=False)
    status: Mapped[LlmRunStatus] = mapped_column(
        enum_column(LlmRunStatus, 30), nullable=False
    )
    input_tokens: Mapped[int | None] = mapped_column(Integer)
    output_tokens: Mapped[int | None] = mapped_column(Integer)
    cost_usd: Mapped[Decimal | None] = mapped_column(Numeric(12, 6))
    latency_ms: Mapped[int | None] = mapped_column(Integer)
    response_data: Mapped[dict[str, Any] | None] = mapped_column(json_type)
    validation_errors: Mapped[list[Any] | None] = mapped_column(json_type)
    error_message: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class ExtractionJob(UuidPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "extraction_jobs"
    __table_args__ = (
        UniqueConstraint("source_snapshot_id", "prompt_version"),
        Index("ix_extraction_jobs_status_created", "status", "created_at"),
    )

    source_snapshot_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("source_snapshots.id", ondelete="CASCADE"), nullable=False
    )
    review_task_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("review_tasks.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    last_llm_run_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("llm_runs.id", ondelete="SET NULL")
    )
    prompt_version: Mapped[str] = mapped_column(String(80), nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    status: Mapped[ExtractionStatus] = mapped_column(
        enum_column(ExtractionStatus, 30), nullable=False, default=ExtractionStatus.PENDING
    )
    deterministic_data: Mapped[dict[str, Any]] = mapped_column(json_type, nullable=False)
    candidate_data: Mapped[dict[str, Any] | None] = mapped_column(json_type)
    evidence: Mapped[list[Any] | None] = mapped_column(json_type)
    warnings: Mapped[list[Any] | None] = mapped_column(json_type)
    error_message: Mapped[str | None] = mapped_column(Text)


class ReviewTask(UuidPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "review_tasks"
    __table_args__ = (Index("ix_review_tasks_status_created", "status", "created_at"),)

    program_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("programs.id", ondelete="CASCADE")
    )
    program_version_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("program_versions.id", ondelete="CASCADE")
    )
    reason: Mapped[ReviewReason] = mapped_column(enum_column(ReviewReason, 40), nullable=False)
    status: Mapped[ReviewStatus] = mapped_column(
        enum_column(ReviewStatus, 20),
        nullable=False,
        default=ReviewStatus.PENDING,
    )
    payload: Mapped[dict[str, Any]] = mapped_column(json_type, nullable=False)
    resolution_note: Mapped[str | None] = mapped_column(Text)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class AuditLog(UuidPrimaryKeyMixin, Base):
    __tablename__ = "audit_log"
    __table_args__ = (
        Index("ix_audit_log_entity_created", "entity_type", "entity_id", "created_at"),
    )

    actor: Mapped[str] = mapped_column(String(160), nullable=False)
    action: Mapped[str] = mapped_column(String(120), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(120), nullable=False)
    entity_id: Mapped[uuid.UUID | None]
    details: Mapped[dict[str, Any]] = mapped_column(json_type, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
