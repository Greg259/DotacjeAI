import type { ProgramStatus } from "./types";

export const statusLabels: Record<ProgramStatus, string> = {
  open: "Otwarta",
  planned: "Planowana",
  suspended: "Wstrzymana",
  closed: "Zakończona",
  unknown: "Do weryfikacji",
};

export const categoryLabels: Record<string, string> = {
  photovoltaics: "Fotowoltaika",
  energy_storage: "Magazyn energii",
  heat_storage: "Magazyn ciepła",
  heat_pump: "Pompa ciepła",
  domestic_hot_water: "Ciepła woda użytkowa",
  micro_wind: "Mikrowiatrak",
  heat_source_replacement: "Wymiana źródła ciepła",
  thermal_modernization: "Termomodernizacja",
  research_and_development: "Badania i rozwój",
  innovation: "Innowacje",
  digitalization: "Cyfryzacja",
  energy_efficiency: "Efektywność energetyczna",
  internationalization: "Internacjonalizacja",
};

export const propertyLabels: Record<string, string> = {
  single_family_house: "Dom jednorodzinny",
  apartment: "Mieszkanie",
  housing_community: "Wspólnota mieszkaniowa",
  enterprise: "Przedsiębiorstwo",
  sme: "MŚP",
  research_organization: "Organizacja badawcza",
  consortium: "Konsorcjum",
  new_house: "Nowy dom",
  existing_building: "Istniejący budynek",
};

export const beneficiaryLabels: Record<string, string> = {
  natural_person: "Osoba fizyczna",
  owner: "Właściciel",
  co_owner: "Współwłaściciel",
  tenant: "Najemca",
  housing_community: "Wspólnota mieszkaniowa",
};

export function formatDate(value: string | null): string {
  if (!value) return "Brak daty";
  return new Intl.DateTimeFormat("pl-PL", { dateStyle: "long" }).format(new Date(value));
}

export function formatDateTime(value: string | null): string {
  if (!value) return "jeszcze nie sprawdzono";
  return new Intl.DateTimeFormat("pl-PL", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

export function formatMoney(value: string | null, currency: string): string {
  if (!value) return "Nie podano";
  return new Intl.NumberFormat("pl-PL", {
    style: "currency",
    currency,
    maximumFractionDigits: 0,
  }).format(Number(value));
}
