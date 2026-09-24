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
}

export interface ProgramDocument {
  title: string;
  url: string;
  document_type: string;
}

export interface ProgramVersion {
  version_number: number;
  change_summary: string | null;
  approved_at: string;
}

export interface ProgramDetail extends ProgramItem {
  documents: ProgramDocument[];
  versions: ProgramVersion[];
}

export interface ProgramListResponse {
  items: ProgramItem[];
  total: number;
  limit: number;
  offset: number;
}
