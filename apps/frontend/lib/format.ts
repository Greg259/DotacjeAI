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
};

export const propertyLabels: Record<string, string> = {
  single_family_house: "Dom jednorodzinny",
  apartment: "Mieszkanie",
  housing_community: "Wspólnota mieszkaniowa",
  new_house: "Nowy dom",
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

export function formatMoney(value: string | null, currency: string): string {
  if (!value) return "Nie podano";
  return new Intl.NumberFormat("pl-PL", {
    style: "currency",
    currency,
    maximumFractionDigits: 0,
  }).format(Number(value));
}
