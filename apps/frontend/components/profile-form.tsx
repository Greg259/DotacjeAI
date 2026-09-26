"use client";

import { useRouter } from "next/navigation";
import { FormEvent, useEffect, useState } from "react";

import { apiRequest, errorMessage } from "@/lib/account";

type Option = { id: string; name: string };
type Options = {
  locations: Option[]; beneficiary_types: string[]; property_types: string[];
  building_states: string[]; heat_sources: string[]; investment_categories: string[];
  profile_kinds: string[]; business_sizes: string[]; legal_forms: string[];
};
type Profile = {
  name: string; profile_kind: "property" | "business"; location: { id: string } | null;
  beneficiary_type: string; property_type: string | null; building_state: string | null;
  current_heat_source: string | null; year_built: number | null; heated_area_m2: string | null;
  business_name: string | null; business_size: string | null; legal_form: string | null;
  established_year: number | null; employee_count: number | null; annual_turnover_pln: string | null;
  industry_codes: string[]; investment_categories: string[];
};

const labels: Record<string, string> = {
  natural_person: "osoba fizyczna", owner: "właściciel", co_owner: "współwłaściciel",
  tenant: "najemca", housing_community: "wspólnota mieszkaniowa", enterprise: "przedsiębiorstwo",
  sme: "MŚP", research_organization: "organizacja badawcza", consortium: "konsorcjum",
  single_family_house: "dom jednorodzinny", apartment: "mieszkanie", new: "nowy budynek",
  existing: "istniejący budynek", coal: "węgiel", biomass: "biomasa", gas: "gaz",
  electric: "energia elektryczna", district_heating: "sieć ciepłownicza", heat_pump: "pompa ciepła",
  other: "inne", none: "brak", micro: "mikro", small: "małe", medium: "średnie", large: "duże",
  sole_proprietorship: "jednoosobowa działalność", company: "spółka", cooperative: "spółdzielnia",
  ngo: "organizacja pozarządowa", photovoltaics: "fotowoltaika", energy_storage: "magazyn energii",
  heat_storage: "magazyn ciepła", domestic_hot_water: "CWU", micro_wind: "mikrowiatrak",
  thermal_modernization: "termomodernizacja", heat_source_replacement: "wymiana źródła ciepła",
  research_and_development: "badania i rozwój", innovation: "innowacje", digitalization: "cyfryzacja",
  energy_efficiency: "efektywność energetyczna", internationalization: "internacjonalizacja",
};
const businessBeneficiaries = new Set(["enterprise", "sme", "research_organization", "consortium"]);
const propertyCategories = new Set([
  "photovoltaics", "energy_storage", "heat_storage", "heat_pump", "domestic_hot_water",
  "micro_wind", "thermal_modernization", "heat_source_replacement", "energy_efficiency",
]);

export function ProfileForm({ profileId }: { profileId?: string }) {
  const router = useRouter();
  const [options, setOptions] = useState<Options | null>(null);
  const [profile, setProfile] = useState<Profile | null>(null);
  const [kind, setKind] = useState<"property" | "business">("property");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    const requests = [fetch("/api/profiles/options")];
    if (profileId) requests.push(fetch(`/api/profiles/${profileId}`));
    Promise.all(requests).then(async (responses) => {
      if (responses[0].status === 401) return router.replace("/konto/logowanie");
      if (responses.some((response) => !response.ok)) return setError("Nie udało się pobrać formularza.");
      const loaded: Profile | null = responses[1] ? await responses[1].json() : null;
      if (loaded) { setProfile(loaded); setKind(loaded.profile_kind); }
      setOptions(await responses[0].json());
    });
  }, [profileId, router]);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setBusy(true); setError("");
    const form = new FormData(event.currentTarget);
    const value = (name: string) => form.get(name) || null;
    const payload = {
      name: form.get("name"), profile_kind: kind, location_id: value("location_id"),
      beneficiary_type: form.get("beneficiary_type"), property_type: value("property_type"),
      building_state: value("building_state"), current_heat_source: value("current_heat_source"),
      year_built: value("year_built") ? Number(value("year_built")) : null,
      heated_area_m2: value("heated_area_m2"), business_name: value("business_name"),
      business_size: value("business_size"), legal_form: value("legal_form"),
      established_year: value("established_year") ? Number(value("established_year")) : null,
      employee_count: value("employee_count") ? Number(value("employee_count")) : null,
      annual_turnover_pln: value("annual_turnover_pln"),
      industry_codes: String(form.get("industry_codes") ?? "").split(","),
      investment_categories: form.getAll("investment_categories"),
    };
    const response = await apiRequest(profileId ? `/api/profiles/${profileId}` : "/api/profiles", {
      method: profileId ? "PUT" : "POST", body: JSON.stringify(payload),
    });
    if (!response.ok) { setError(await errorMessage(response)); setBusy(false); return; }
    router.push("/konto"); router.refresh();
  }

  if (!options) return <p>{error || "Wczytywanie formularza…"}</p>;
  const selected = new Set(profile?.investment_categories ?? []);
  const beneficiaries = options.beneficiary_types.filter((item) =>
    kind === "business" ? businessBeneficiaries.has(item) : !businessBeneficiaries.has(item));
  const categories = options.investment_categories.filter((item) =>
    kind === "property" ? propertyCategories.has(item) : !propertyCategories.has(item) || item === "energy_efficiency");
  return <form className="profile-form" onSubmit={submit}>
    <label>Rodzaj profilu<select name="profile_kind" value={kind} onChange={(event) => setKind(event.target.value as "property" | "business")}><option value="property">Nieruchomość prywatna</option><option value="business">Przedsiębiorstwo lub organizacja</option></select></label>
    <label>Nazwa profilu<input name="name" defaultValue={profile?.name ?? ""} placeholder={kind === "property" ? "np. Dom w Nadarzynie" : "np. Moja firma — projekty B+R"} required /></label>
    <label>Lokalizacja<select name="location_id" defaultValue={profile?.location?.id ?? ""}><option value="">Wybierz lokalizację</option>{options.locations.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}</select></label>
    <label>Typ beneficjenta<select name="beneficiary_type" key={`beneficiary-${kind}`} defaultValue={kind === "business" ? profile?.beneficiary_type ?? "enterprise" : profile?.beneficiary_type ?? "owner"}>{beneficiaries.map((item) => <option key={item} value={item}>{labels[item] ?? item}</option>)}</select></label>
    {kind === "property" ? <>
      <label>Typ nieruchomości<select name="property_type" defaultValue={profile?.property_type ?? "single_family_house"}>{options.property_types.map((item) => <option key={item} value={item}>{labels[item] ?? item}</option>)}</select></label>
      <label>Stan budynku<select name="building_state" defaultValue={profile?.building_state ?? "existing"}>{options.building_states.map((item) => <option key={item} value={item}>{labels[item] ?? item}</option>)}</select></label>
      <label>Obecne źródło ciepła<select name="current_heat_source" defaultValue={profile?.current_heat_source ?? "other"}>{options.heat_sources.map((item) => <option key={item} value={item}>{labels[item] ?? item}</option>)}</select></label>
      <label>Rok budowy<input name="year_built" type="number" min="1800" max="2100" defaultValue={profile?.year_built ?? ""} /></label>
      <label>Powierzchnia ogrzewana (m²)<input name="heated_area_m2" type="number" min="1" max="100000" step="0.01" defaultValue={profile?.heated_area_m2 ?? ""} /></label>
    </> : <>
      <label>Nazwa przedsiębiorstwa lub organizacji<input name="business_name" defaultValue={profile?.business_name ?? ""} required /></label>
      <label>Wielkość<select name="business_size" defaultValue={profile?.business_size ?? "micro"}>{options.business_sizes.map((item) => <option key={item} value={item}>{labels[item] ?? item}</option>)}</select></label>
      <label>Forma prawna<select name="legal_form" defaultValue={profile?.legal_form ?? "company"}>{options.legal_forms.map((item) => <option key={item} value={item}>{labels[item] ?? item}</option>)}</select></label>
      <label>Rok rozpoczęcia działalności<input name="established_year" type="number" min="1800" max="2100" defaultValue={profile?.established_year ?? ""} /></label>
      <label>Liczba pracowników<input name="employee_count" type="number" min="0" defaultValue={profile?.employee_count ?? ""} /></label>
      <label>Roczny obrót w PLN<input name="annual_turnover_pln" type="number" min="0" step="0.01" defaultValue={profile?.annual_turnover_pln ?? ""} /></label>
      <label>Kody PKD lub branżowe, oddzielone przecinkami<input name="industry_codes" defaultValue={profile?.industry_codes.join(", ") ?? ""} placeholder="np. 62.01.Z, 72.19.Z" /></label>
    </>}
    <fieldset><legend>Planowane inwestycje</legend><div className="check-grid">{categories.map((item) => <label className="check-row" key={item}><input name="investment_categories" type="checkbox" value={item} defaultChecked={selected.has(item)} />{labels[item] ?? item}</label>)}</div></fieldset>
    {error && <p className="form-error" role="alert">{error}</p>}
    <div className="actions"><button className="button" disabled={busy} type="submit">{busy ? "Zapisywanie…" : "Zapisz profil"}</button><button className="secondary-button" type="button" onClick={() => router.push("/konto")}>Anuluj</button></div>
  </form>;
}
