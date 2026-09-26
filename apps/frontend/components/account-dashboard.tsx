"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { apiRequest, errorMessage } from "@/lib/account";

type User = { username: string; role: string; created_at: string };
type Profile = {
  id: string;
  name: string;
  location: { name: string } | null;
  property_type: string;
  building_state: string;
  current_heat_source: string;
  investment_categories: string[];
};

const labels: Record<string, string> = {
  single_family_house: "dom jednorodzinny", apartment: "mieszkanie",
  housing_community: "wspólnota mieszkaniowa", new: "nowy", existing: "istniejący",
  coal: "węgiel", biomass: "biomasa", gas: "gaz", electric: "energia elektryczna",
  district_heating: "sieć ciepłownicza", heat_pump: "pompa ciepła", other: "inne", none: "brak",
  photovoltaics: "fotowoltaika", energy_storage: "magazyn energii", heat_storage: "magazyn ciepła",
  domestic_hot_water: "CWU", micro_wind: "mikrowiatrak", thermal_modernization: "termomodernizacja",
  heat_source_replacement: "wymiana źródła ciepła",
};

export function AccountDashboard() {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [profiles, setProfiles] = useState<Profile[]>([]);
  const [error, setError] = useState("");
  const [deletePassword, setDeletePassword] = useState("");

  useEffect(() => {
    Promise.all([fetch("/api/auth/me"), fetch("/api/profiles")]).then(async ([me, list]) => {
      if (me.status === 401) return router.replace("/konto/logowanie");
      if (!me.ok || !list.ok) return setError("Nie udało się pobrać danych konta.");
      setUser(await me.json());
      setProfiles(await list.json());
    });
  }, [router]);

  async function logout() {
    await apiRequest("/api/auth/logout", { method: "POST" });
    router.push("/");
    router.refresh();
  }

  async function removeProfile(id: string) {
    if (!window.confirm("Usunąć ten profil nieruchomości?")) return;
    const response = await apiRequest(`/api/profiles/${id}`, { method: "DELETE" });
    if (response.ok) setProfiles((items) => items.filter((item) => item.id !== id));
    else setError(await errorMessage(response));
  }

  async function removeAccount() {
    if (!window.confirm("Usunąć konto i wszystkie profile bez możliwości cofnięcia?")) return;
    const response = await apiRequest("/api/auth/me", {
      method: "DELETE",
      body: JSON.stringify({ password: deletePassword }),
    });
    if (!response.ok) return setError(await errorMessage(response));
    router.push("/");
    router.refresh();
  }

  if (!user && !error) return <p>Wczytywanie konta…</p>;
  return (
    <div className="account-layout">
      <section>
        <div className="section-heading">
          <div><p className="eyebrow">Twoje konto</p><h1>{user?.username}</h1></div>
          <button className="secondary-button" onClick={logout}>Wyloguj się</button>
        </div>
        {error && <p className="form-error" role="alert">{error}</p>}
        <div className="section-heading profile-heading">
          <div><h2>Profile nieruchomości</h2><p>Profile posłużą później do dopasowania dotacji.</p></div>
          <Link className="button" href="/konto/profil/nowy">Dodaj profil</Link>
        </div>
        {profiles.length === 0 ? (
          <div className="empty-state"><h2>Nie masz jeszcze profilu</h2><p>Dodaj dom, mieszkanie albo wspólnotę.</p></div>
        ) : <div className="profile-grid">{profiles.map((profile) => (
          <article className="profile-card" key={profile.id}>
            <h3>{profile.name}</h3>
            <p>{labels[profile.property_type]} · {labels[profile.building_state]}</p>
            <p>{profile.location?.name ?? "Lokalizacja nieustalona"} · ogrzewanie: {labels[profile.current_heat_source]}</p>
            <div className="tags">{profile.investment_categories.map((item) => <span key={item}>{labels[item] ?? item}</span>)}</div>
            <div className="profile-actions"><Link className="text-link" href={`/konto/profil/${profile.id}`}>Edytuj</Link><button onClick={() => removeProfile(profile.id)}>Usuń</button></div>
          </article>
        ))}</div>}
      </section>
      <aside className="account-sidebar">
        <h2>Twoje dane</h2>
        <a className="button secondary-button" href="/api/auth/export">Pobierz dane JSON</a>
        <div className="danger-zone"><h3>Usuń konto</h3><p>Usuniemy konto, sesje i wszystkie profile.</p><input type="password" value={deletePassword} onChange={(event) => setDeletePassword(event.target.value)} placeholder="Potwierdź hasłem" /><button className="danger-button" disabled={!deletePassword} onClick={removeAccount}>Usuń konto</button></div>
      </aside>
    </div>
  );
}
