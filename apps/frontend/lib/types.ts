export type ProgramStatus = "open" | "planned" | "suspended" | "closed" | "unknown";

export interface LocationItem {
  name: string;
  slug: string;
  location_type: string;
}

export interface ProgramItem {
  id: string;
  slug: string;
  title: string;
  organizer: string;
  summary: string | null;
  status: ProgramStatus;
  application_start: string | null;
  application_end: string | null;
  max_amount: string | null;
  support_percent: string | null;
  currency: string;
  last_verified_at: string | null;
  official_url: string | null;
  locations: LocationItem[];
  property_types: string[];
  beneficiary_types: string[];
  investment_categories: string[];
  business_sizes: string[];
}

export interface ProgramDocument {
  title: string;
  url: string;
  document_type: string;
  is_available: boolean;
  state: "current" | "needs_review" | "superseded" | "unavailable";
  state_reason: string | null;
  last_checked_at: string | null;
}

export interface ProgramVersion {
  version_number: number;
  change_summary: string | null;
  approved_at: string;
}

export interface ProgramContentItem {
  title: string;
  description: string;
  source_reference: string | null;
  source_url: string | null;
}

export interface FundingOption {
  name: string;
  description: string;
  support_percent: string | null;
  max_amount: string | null;
  currency: "PLN";
  source_reference: string | null;
  source_url: string | null;
}

export interface ApplicationResource {
  title: string;
  url: string;
  resource_type:
    | "application_form"
    | "statement"
    | "instructions"
    | "regulations"
    | "application_portal"
    | "official_page"
    | "other";
  description: string | null;
}

export interface ProgramDetails {
  key_takeaways: ProgramContentItem[];
  eligible_applicants: ProgramContentItem[];
  eligibility_conditions: ProgramContentItem[];
  funding_options: FundingOption[];
  important_information: ProgramContentItem[];
  application_steps: ProgramContentItem[];
  required_documents: ProgramContentItem[];
  application_resources: ApplicationResource[];
}

export interface ProgramDetail extends ProgramItem {
  documents: ProgramDocument[];
  versions: ProgramVersion[];
  details: ProgramDetails;
}

export interface ProgramListResponse {
  items: ProgramItem[];
  total: number;
  limit: number;
  offset: number;
}
