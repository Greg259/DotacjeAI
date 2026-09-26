"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { apiRequest, errorMessage } from "@/lib/account";

type User = { username: string; role: string; created_at: string };
type Profile = {
  id: string;
  name: string;
  profile_kind: "property" | "business";
  location: { name: string } | null;
  property_type: string | null;
  building_state: string | null;
  current_heat_source: string | null;
  business_name: string | null;
  business_size: string | null;
  investment_categories: string[];
};
type SourceSuggestion = {
  id: string;
  title: string | null;
  url: string;
  note: string | null;
  status: "pending" | "approved" | "rejected";
  reviewer_note: string | null;
  created_at: string;
};

const labels: Record<string, string> = {
  single_family_house: "dom jednorodzinny", apartment: "mieszkanie",
  housing_community: "wspólnota mieszkaniowa", new: "nowy", existing: "istniejący",
  coal: "węgiel", biomass: "biomasa", gas: "gaz", electric: "energia elektryczna",
  district_heating: "sieć ciepłownicza", heat_pump: "pompa ciepła", other: "inne", none: "brak",
  photovoltaics: "fotowoltaika", energy_storage: "magazyn energii", heat_storage: "magazyn ciepła",
  domestic_hot_water: "CWU", micro_wind: "mikrowiatrak", thermal_modernization: "termomodernizacja",
  heat_source_replacement: "wymiana źródła ciepła",
  research_and_development: "badania i rozwój", innovation: "innowacje", digitalization: "cyfryzacja",
  energy_efficiency: "efektywność energetyczna", internationalization: "internacjonalizacja",
  micro: "mikroprzedsiębiorstwo", small: "małe przedsiębiorstwo",
  medium: "średnie przedsiębiorstwo", large: "duże przedsiębiorstwo",
};

export function AccountDashboard() {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [profiles, setProfiles] = useState<Profile[]>([]);
  const [suggestions, setSuggestions] = useState<SourceSuggestion[]>([]);
  const [sourceTitle, setSourceTitle] = useState("");
  const [sourceUrl, setSourceUrl] = useState("");
  const [sourceNote, setSourceNote] = useState("");
  const [submittingSource, setSubmittingSource] = useState(false);
  const [error, setError] = useState("");
  const [deletePassword, setDeletePassword] = useState("");

  useEffect(() => {
    Promise.all([
      fetch("/api/auth/me"),
      fetch("/api/profiles"),
      fetch("/api/source-suggestions"),
    ]).then(async ([me, list, sourceList]) => {
      if (me.status === 401) return router.replace("/konto/logowanie");
      if (!me.ok || !list.ok || !sourceList.ok) return setError("Nie udało się pobrać danych konta.");
      setUser(await me.json());
      setProfiles(await list.json());
      setSuggestions(await sourceList.json());
    });
  }, [router]);

  async function submitSource(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setSubmittingSource(true);
    const response = await apiRequest("/api/source-suggestions", {
      method: "POST",
      body: JSON.stringify({
        title: sourceTitle || null,
        url: sourceUrl,
        note: sourceNote || null,
      }),
    });
    setSubmittingSource(false);
    if (!response.ok) return setError(await errorMessage(response));
    const item: SourceSuggestion = await response.json();
    setSuggestions((items) => [item, ...items]);
    setSourceTitle("");
    setSourceUrl("");
    setSourceNote("");
  }

  async function logout() {
    await apiRequest("/api/auth/logout", { method: "POST" });
    router.push("/");
    router.refresh();
  }

  async function removeProfile(id: string) {
    if (!window.confirm("Usunąć ten profil dotacyjny?")) return;
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
          <div><h2>Profile dotacyjne</h2><p>Każdy profil jest niezależnie dopasowywany do programów.</p></div>
          <Link className="button" href="/konto/profil/nowy">Dodaj profil</Link>
        </div>
        {profiles.length === 0 ? (
          <div className="empty-state"><h2>Nie masz jeszcze profilu</h2><p>Dodaj nieruchomość albo przedsiębiorstwo.</p></div>
        ) : <div className="profile-grid">{profiles.map((profile) => (
          <article className="profile-card" key={profile.id}>
            <h3>{profile.name}</h3>
            {profile.profile_kind === "property" ? <>
              <p>{labels[profile.property_type ?? ""]} · {labels[profile.building_state ?? ""]}</p>
              <p>{profile.location?.name ?? "Lokalizacja nieustalona"} · ogrzewanie: {labels[profile.current_heat_source ?? ""]}</p>
            </> : <>
              <p>{profile.business_name} · {labels[profile.business_size ?? ""]}</p>
              <p>{profile.location?.name ?? "Lokalizacja nieustalona"}</p>
            </>}
            <div className="tags">{profile.investment_categories.map((item) => <span key={item}>{labels[item] ?? item}</span>)}</div>
            <div className="profile-actions"><Link className="text-link" href={`/konto/profil/${profile.id}/dopasowania`}>Dopasowania</Link><Link className="text-link" href={`/konto/profil/${profile.id}`}>Edytuj</Link><button onClick={() => removeProfile(profile.id)}>Usuń</button></div>
          </article>
        ))}</div>}

        <section className="source-suggestions">
          <div className="section-heading profile-heading">
            <div>
              <h2>Zaproponuj stronę do skanowania</h2>
              <p>Podaj publiczną stronę HTTPS z dotacjami lub wsparciem. Skanowanie rozpocznie się dopiero po akceptacji administratora.</p>
            </div>
          </div>
          <form className="source-suggestion-form" onSubmit={submitSource}>
            <label>Tytuł lub instytucja (opcjonalnie)<input maxLength={255} value={sourceTitle} onChange={(event) => setSourceTitle(event.target.value)} /></label>
            <label>Adres strony<input required type="url" pattern="https://.*" placeholder="https://instytucja.pl/dotacje" value={sourceUrl} onChange={(event) => setSourceUrl(event.target.value)} /></label>
            <label>Co warto znaleźć? (opcjonalnie)<textarea maxLength={1000} rows={3} value={sourceNote} onChange={(event) => setSourceNote(event.target.value)} /></label>
            <button className="button" disabled={submittingSource}>{submittingSource ? "Wysyłanie…" : "Wyślij do akceptacji"}</button>
          </form>
          {suggestions.length > 0 && <div className="suggestion-list">
            {suggestions.map((item) => <article className="suggestion-card" key={item.id}>
              <div><strong>{item.title || item.url}</strong><a href={item.url} target="_blank" rel="noreferrer">{item.url}</a></div>
              <span className={`suggestion-status ${item.status}`}>{item.status === "pending" ? "oczekuje" : item.status === "approved" ? "zaakceptowana" : "odrzucona"}</span>
              {item.reviewer_note && <p>{item.reviewer_note}</p>}
            </article>)}
          </div>}
        </section>
      </section>
      <aside className="account-sidebar">
        <h2>Twoje dane</h2>
        <a className="button secondary-button" href="/api/auth/export">Pobierz dane JSON</a>
        <div className="danger-zone"><h3>Usuń konto</h3><p>Usuniemy konto, sesje i wszystkie profile.</p><input type="password" value={deletePassword} onChange={(event) => setDeletePassword(event.target.value)} placeholder="Potwierdź hasłem" /><button className="danger-button" disabled={!deletePassword} onClick={removeAccount}>Usuń konto</button></div>
      </aside>
    </div>
  );
}
