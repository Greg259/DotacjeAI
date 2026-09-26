"use client";

import { useRouter } from "next/navigation";
import { FormEvent, useEffect, useState } from "react";

import { apiRequest, errorMessage } from "@/lib/account";

type Option = { id?: string; name?: string; value?: string; slug?: string; location_type?: string };
type Options = {
  locations: Option[]; beneficiary_types: string[]; property_types: string[];
  building_states: string[]; heat_sources: string[]; investment_categories: string[];
};
type Profile = {
  name: string; location: { id: string } | null; beneficiary_type: string; property_type: string;
  building_state: string; current_heat_source: string; year_built: number | null;
  heated_area_m2: string | null; investment_categories: string[];
};

const labels: Record<string, string> = {
  natural_person: "osoba fizyczna", owner: "właściciel", co_owner: "współwłaściciel",
  tenant: "najemca", housing_community: "wspólnota mieszkaniowa",
  single_family_house: "dom jednorodzinny", apartment: "mieszkanie", new: "nowy budynek",
  existing: "istniejący budynek", coal: "węgiel", biomass: "biomasa", gas: "gaz",
  electric: "energia elektryczna", district_heating: "sieć ciepłownicza", heat_pump: "pompa ciepła",
  other: "inne", none: "brak", photovoltaics: "fotowoltaika", energy_storage: "magazyn energii",
  heat_storage: "magazyn ciepła", domestic_hot_water: "CWU", micro_wind: "mikrowiatrak",
  thermal_modernization: "termomodernizacja", heat_source_replacement: "wymiana źródła ciepła",
};

export function ProfileForm({ profileId }: { profileId?: string }) {
  const router = useRouter();
  const [options, setOptions] = useState<Options | null>(null);
  const [profile, setProfile] = useState<Profile | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    const requests = [fetch("/api/profiles/options")];
    if (profileId) requests.push(fetch(`/api/profiles/${profileId}`));
    Promise.all(requests).then(async (responses) => {
      if (responses[0].status === 401) return router.replace("/konto/logowanie");
      if (responses.some((response) => !response.ok)) return setError("Nie udało się pobrać formularza.");
      setOptions(await responses[0].json());
      if (responses[1]) setProfile(await responses[1].json());
    });
  }, [profileId, router]);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true); setError("");
    const form = new FormData(event.currentTarget);
    const payload = {
      name: form.get("name"), location_id: form.get("location_id") || null,
      beneficiary_type: form.get("beneficiary_type"), property_type: form.get("property_type"),
      building_state: form.get("building_state"), current_heat_source: form.get("current_heat_source"),
      year_built: form.get("year_built") ? Number(form.get("year_built")) : null,
      heated_area_m2: form.get("heated_area_m2") || null,
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
  return <form className="profile-form" onSubmit={submit}>
    <label>Nazwa profilu<input name="name" defaultValue={profile?.name ?? ""} placeholder="np. Dom w Nadarzynie" required /></label>
    <label>Lokalizacja<select name="location_id" defaultValue={profile?.location?.id ?? ""}><option value="">Wybierz lokalizację</option>{options.locations.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}</select></label>
    <label>Kim jesteś?<select name="beneficiary_type" defaultValue={profile?.beneficiary_type ?? "owner"}>{options.beneficiary_types.map((item) => <option key={item} value={item}>{labels[item] ?? item}</option>)}</select></label>
    <label>Typ nieruchomości<select name="property_type" defaultValue={profile?.property_type ?? "single_family_house"}>{options.property_types.map((item) => <option key={item} value={item}>{labels[item] ?? item}</option>)}</select></label>
    <label>Stan budynku<select name="building_state" defaultValue={profile?.building_state ?? "existing"}>{options.building_states.map((item) => <option key={item} value={item}>{labels[item] ?? item}</option>)}</select></label>
    <label>Obecne źródło ciepła<select name="current_heat_source" defaultValue={profile?.current_heat_source ?? "other"}>{options.heat_sources.map((item) => <option key={item} value={item}>{labels[item] ?? item}</option>)}</select></label>
    <label>Rok budowy<input name="year_built" type="number" min="1800" max="2100" defaultValue={profile?.year_built ?? ""} /></label>
    <label>Powierzchnia ogrzewana (m²)<input name="heated_area_m2" type="number" min="1" max="100000" step="0.01" defaultValue={profile?.heated_area_m2 ?? ""} /></label>
    <fieldset><legend>Planowane inwestycje</legend><div className="check-grid">{options.investment_categories.map((item) => <label className="check-row" key={item}><input name="investment_categories" type="checkbox" value={item} defaultChecked={selected.has(item)} />{labels[item] ?? item}</label>)}</div></fieldset>
    {error && <p className="form-error" role="alert">{error}</p>}
    <div className="actions"><button className="button" disabled={busy} type="submit">{busy ? "Zapisywanie…" : "Zapisz profil"}</button><button className="secondary-button" type="button" onClick={() => router.push("/konto")}>Anuluj</button></div>
  </form>;
}
