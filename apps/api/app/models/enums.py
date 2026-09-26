from enum import StrEnum


class SourceType(StrEnum):
    HTML = "html"
    PDF = "pdf"
    INDEX = "index"


class ProgramStatus(StrEnum):
    OPEN = "open"
    PLANNED = "planned"
    SUSPENDED = "suspended"
    CLOSED = "closed"
    UNKNOWN = "unknown"


class LocationType(StrEnum):
    COUNTRY = "country"
    REGION = "region"
    COUNTY = "county"
    MUNICIPALITY = "municipality"


class PropertyType(StrEnum):
    SINGLE_FAMILY_HOUSE = "single_family_house"
    APARTMENT = "apartment"
    HOUSING_COMMUNITY = "housing_community"
    NEW_HOUSE = "new_house"
    EXISTING_BUILDING = "existing_building"


class BeneficiaryType(StrEnum):
    NATURAL_PERSON = "natural_person"
    OWNER = "owner"
    CO_OWNER = "co_owner"
    TENANT = "tenant"
    HOUSING_COMMUNITY = "housing_community"


class InvestmentCategory(StrEnum):
    PHOTOVOLTAICS = "photovoltaics"
    ENERGY_STORAGE = "energy_storage"
    HEAT_STORAGE = "heat_storage"
    HEAT_PUMP = "heat_pump"
    DOMESTIC_HOT_WATER = "domestic_hot_water"
    MICRO_WIND = "micro_wind"
    THERMAL_MODERNIZATION = "thermal_modernization"
    HEAT_SOURCE_REPLACEMENT = "heat_source_replacement"


class ReviewStatus(StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class ReviewReason(StrEnum):
    NEW_PROGRAM = "new_program"
    SOURCE_CHANGED = "source_changed"
    CONFLICTING_SOURCES = "conflicting_sources"
    LOW_CONFIDENCE = "low_confidence"
    INVALID_EXTRACTION = "invalid_extraction"
    STATUS_CHANGED = "status_changed"
    DOCUMENT_CHANGED = "document_changed"


class LlmRunStatus(StrEnum):
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    REJECTED_BY_VALIDATION = "rejected_by_validation"
    BLOCKED_BY_BUDGET = "blocked_by_budget"


class ExtractionStatus(StrEnum):
    PENDING = "pending"
    RULES_READY = "rules_ready"
    AWAITING_API_KEY = "awaiting_api_key"
    BLOCKED_BY_BUDGET = "blocked_by_budget"
    READY_FOR_REVIEW = "ready_for_review"
    FAILED = "failed"


class DocumentType(StrEnum):
    REGULATIONS = "regulations"
    APPLICATION_FORM = "application_form"
    ANNOUNCEMENT = "announcement"
    GUIDELINES = "guidelines"
    OTHER = "other"


class DocumentState(StrEnum):
    CURRENT = "current"
    NEEDS_REVIEW = "needs_review"
    SUPERSEDED = "superseded"
    UNAVAILABLE = "unavailable"
