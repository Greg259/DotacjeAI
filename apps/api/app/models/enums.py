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
    ENTERPRISE = "enterprise"
    SME = "sme"
    RESEARCH_ORGANIZATION = "research_organization"
    CONSORTIUM = "consortium"


class InvestmentCategory(StrEnum):
    PHOTOVOLTAICS = "photovoltaics"
    ENERGY_STORAGE = "energy_storage"
    HEAT_STORAGE = "heat_storage"
    HEAT_PUMP = "heat_pump"
    DOMESTIC_HOT_WATER = "domestic_hot_water"
    MICRO_WIND = "micro_wind"
    THERMAL_MODERNIZATION = "thermal_modernization"
    HEAT_SOURCE_REPLACEMENT = "heat_source_replacement"
    RESEARCH_AND_DEVELOPMENT = "research_and_development"
    INNOVATION = "innovation"
    DIGITALIZATION = "digitalization"
    ENERGY_EFFICIENCY = "energy_efficiency"
    INTERNATIONALIZATION = "internationalization"


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


class UserRole(StrEnum):
    USER = "user"
    EDITOR = "editor"
    ADMIN = "admin"


class BuildingState(StrEnum):
    NEW = "new"
    EXISTING = "existing"


class HeatSource(StrEnum):
    COAL = "coal"
    BIOMASS = "biomass"
    GAS = "gas"
    ELECTRIC = "electric"
    DISTRICT_HEATING = "district_heating"
    HEAT_PUMP = "heat_pump"
    OTHER = "other"
    NONE = "none"


class ProfileKind(StrEnum):
    PROPERTY = "property"
    BUSINESS = "business"


class BusinessSize(StrEnum):
    MICRO = "micro"
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"


class BusinessLegalForm(StrEnum):
    SOLE_PROPRIETORSHIP = "sole_proprietorship"
    COMPANY = "company"
    COOPERATIVE = "cooperative"
    NGO = "ngo"
    RESEARCH_ORGANIZATION = "research_organization"
    OTHER = "other"


class MatchRuleStatus(StrEnum):
    FULFILLED = "fulfilled"
    NOT_FULFILLED = "not_fulfilled"
    MISSING_DATA = "missing_data"


class MatchOutcome(StrEnum):
    ELIGIBLE = "eligible"
    POSSIBLE = "possible"
    NOT_ELIGIBLE = "not_eligible"


class EligibilityOperator(StrEnum):
    EQUALS = "equals"
    NOT_EQUALS = "not_equals"
    IN = "in"
    NOT_IN = "not_in"
    GTE = "gte"
    LTE = "lte"
    BETWEEN = "between"
    CONTAINS_ANY = "contains_any"
    CONTAINS_NONE = "contains_none"
    IS_TRUE = "is_true"
    IS_FALSE = "is_false"


class EligibilityProfileField(StrEnum):
    BENEFICIARY_TYPE = "beneficiary_type"
    PROPERTY_TYPE = "property_type"
    BUILDING_STATE = "building_state"
    CURRENT_HEAT_SOURCE = "current_heat_source"
    YEAR_BUILT = "year_built"
    ANNUAL_HOUSEHOLD_INCOME_PLN = "annual_household_income_pln"
    MONTHLY_INCOME_PER_PERSON_PLN = "monthly_income_per_person_pln"
    BUSINESS_SIZE = "business_size"
    LEGAL_FORM = "legal_form"
    BUSINESS_AGE_YEARS = "business_age_years"
    EMPLOYEE_COUNT = "employee_count"
    ANNUAL_TURNOVER_PLN = "annual_turnover_pln"
    INDUSTRY_CODES = "industry_codes"
    PROJECT_BUDGET_PLN = "project_budget_pln"
    OWN_CONTRIBUTION_PERCENT = "own_contribution_percent"
    DE_MINIMIS_AID_EUR = "de_minimis_aid_eur"
    IS_STARTUP = "is_startup"
    HAS_VC_INVESTOR = "has_vc_investor"
    CONSORTIUM_PLANNED = "consortium_planned"


class DiscoveryStatus(StrEnum):
    NEW = "new"
    TRACKED = "tracked"
    IGNORED = "ignored"


class SuggestionStatus(StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
