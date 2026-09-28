"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useMemo, useState } from "react";

import { apiRequest } from "@/lib/account";
import {
  beneficiaryLabels,
  categoryLabels,
  formatDate,
  formatDateTime,
  formatMoney,
  propertyLabels,
  statusLabels,
} from "@/lib/format";
import type { ProgramContentItem, ProgramDetail } from "@/lib/types";

type Profile = {
  id: string;
  name: string;
  profile_kind: "property" | "business";
  location: { name: string; location_type: string } | null;
  beneficiary_type: string;
  property_type: string | null;
  building_state: string | null;
  current_heat_source: string | null;
  year_built: number | null;
  heated_area_m2: string | null;
  annual_household_income_pln: string | null;
  household_members: number | null;
  business_name: string | null;
  business_size: string | null;
  legal_form: string | null;
  established_year: number | null;
  employee_count: number | null;
  annual_turnover_pln: string | null;
  project_budget_pln: string | null;
  own_contribution_pln: string | null;
  de_minimis_aid_eur: string | null;
  is_startup: boolean | null;
  has_vc_investor: boolean | null;
  consortium_planned: boolean | null;
  industry_codes: string[];
  investment_categories: string[];
  updated_at: string;
};

type MatchRule = {
  code: string;
  label: string;
  status: "fulfilled" | "not_fulfilled" | "missing_data";
  explanation: string;
  source_url: string | null;
  source_reference: string | null;
  evidence_quote: string | null;
  blocking: boolean;
};

type Match = {
  program_id: string;
  slug: string;
  title: string;
  organizer: string;
  outcome: "eligible" | "possible" | "not_eligible";
  score: number;
  rank: number;
  missing_data: string[];
  rules: MatchRule[];
};

type MatchResponse = {
  profile_name: string;
  profile_kind: string;
  generated_at: string;
  results: Match[];
  disclaimer: string;
};

const outcomeLabels = {
  eligible: "Spełnia warunki wstępne",
  possible: "Jest szansa — potrzebne są dodatkowe dane",
  not_eligible: "Nie spełnia co najmniej jednego warunku",
};

const ruleLabels = {
  fulfilled: "Spełnione",
  not_fulfilled: "Niespełnione",
  missing_data: "Brak danych",
};

const valueLabels: Record<string, string> = {
  property: "Nieruchomość",
  business: "Przedsiębiorstwo",
  new: "Nowy budynek",
  existing: "Istniejący budynek",
  coal: "Węgiel",
  gas: "Gaz",
  biomass: "Biomasa",
  electricity: "Energia elektryczna",
  district_heating: "Sieć ciepłownicza",
  heat_pump: "Pompa ciepła",
  none: "Brak",
  micro: "Mikroprzedsiębiorstwo",
  small: "Małe przedsiębiorstwo",
  medium: "Średnie przedsiębiorstwo",
  large: "Duże przedsiębiorstwo",
  sole_proprietorship: "Jednoosobowa działalność gospodarcza",
  civil_partnership: "Spółka cywilna",
  limited_liability_company: "Spółka z o.o.",
  joint_stock_company: "Spółka akcyjna",
  foundation: "Fundacja",
  association: "Stowarzyszenie",
  cooperative: "Spółdzielnia",
  other: "Inna",
  enterprise: "Przedsiębiorstwo",
  sme: "MŚP",
  research_organization: "Organizacja badawcza",
  consortium: "Konsorcjum",
  yes: "Tak",
  no: "Nie",
  unknown: "Nie ustalono",
  required: "Wymagane",
  allowed: "Dozwolone",
  not_allowed: "Niedozwolone",
};

function label(value: string | null): string {
  if (!value) return "Nie podano";
  return beneficiaryLabels[value] ?? propertyLabels[value] ?? valueLabels[value] ?? value;
}

function yesNo(value: boolean | null): string {
  if (value === null) return "Nie podano";
  return value ? "Tak" : "Nie";
}

function pln(value: string | null): string {
  return value ? formatMoney(value, "PLN") : "Nie podano";
}

function eur(value: string | null): string {
  return value ? formatMoney(value, "EUR") : "Nie podano";
}

function SourceNote({ item }: { item: ProgramContentItem }) {
  if (!item.source_reference && !item.source_url) return null;
  return <p className="source-note"><strong>Źródło w programie:</strong> {item.source_url ? <a href={item.source_url} rel="noreferrer" target="_blank">{item.source_reference ?? "oficjalny dokument"}</a> : item.source_reference}</p>;
}

function ContentSection({ title, items }: { title: string; items: ProgramContentItem[] }) {
  if (items.length === 0) return null;
  return <section className="report-section"><h2>{title}</h2><div className="content-list">{items.map((item, index) => <article className="content-item" key={`${item.title}-${index}`}><h3>{item.title}</h3><p>{item.description}</p><SourceNote item={item} /></article>)}</div></section>;
}

export function MatchReport({ profileId, slug }: { profileId: string; slug: string }) {
  const router = useRouter();
  const [profile, setProfile] = useState<Profile | null>(null);
  const [matches, setMatches] = useState<MatchResponse | null>(null);
  const [program, setProgram] = useState<ProgramDetail | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;
    Promise.all([
      apiRequest(`/api/profiles/${profileId}`),
      apiRequest(`/api/profiles/${profileId}/matches`),
      apiRequest(`/api/programs/${encodeURIComponent(slug)}`),
    ]).then(async ([profileResponse, matchesResponse, programResponse]) => {
      if (profileResponse.status === 401 || matchesResponse.status === 401) {
        router.replace("/konto/logowanie");
        return;
      }
      if (!profileResponse.ok || !matchesResponse.ok || !programResponse.ok) {
        if (active) setError("Nie udało się przygotować raportu. Odśwież stronę lub wróć do listy dopasowań.");
        return;
      }
      const [profileData, matchesData, programData] = await Promise.all([
        profileResponse.json(), matchesResponse.json(), programResponse.json(),
      ]);
      if (active) {
        setProfile(profileData);
        setMatches(matchesData);
        setProgram(programData);
      }
    }).catch(() => active && setError("Nie udało się połączyć z serwerem raportów."));
    return () => { active = false; };
  }, [profileId, router, slug]);

  const match = useMemo(() => matches?.results.find((item) => item.slug === slug) ?? null, [matches, slug]);

  if (error) return <div className="empty-state"><h1>Raport jest niedostępny</h1><p>{error}</p><Link className="secondary-button" href={`/konto/profil/${profileId}/dopasowania`}>Wróć do dopasowań</Link></div>;
  if (!profile || !matches || !program) return <p className="report-loading">Przygotowywanie pełnego raportu…</p>;
  if (!match) return <div className="empty-state"><h1>Brak tego dopasowania</h1><p>Program nie należy już do puli właściwej dla tego profilu albo został usunięty.</p><Link className="secondary-button" href={`/konto/profil/${profileId}/dopasowania`}>Wróć do dopasowań</Link></div>;

  const profileRows: Array<[string, string]> = [
    ["Rodzaj profilu", label(profile.profile_kind)],
    ["Nazwa profilu", profile.name],
    ["Lokalizacja", profile.location?.name ?? "Nie podano"],
    ["Typ beneficjenta", label(profile.beneficiary_type)],
    ["Planowane inwestycje", profile.investment_categories.map((item) => categoryLabels[item] ?? item).join(", ") || "Nie podano"],
    ["Budżet projektu", pln(profile.project_budget_pln)],
    ["Wkład własny", pln(profile.own_contribution_pln)],
  ];
  if (profile.profile_kind === "property") profileRows.push(
    ["Typ nieruchomości", label(profile.property_type)],
    ["Stan budynku", label(profile.building_state)],
    ["Obecne źródło ciepła", label(profile.current_heat_source)],
    ["Rok budowy", profile.year_built?.toString() ?? "Nie podano"],
    ["Powierzchnia ogrzewana", profile.heated_area_m2 ? `${profile.heated_area_m2} m²` : "Nie podano"],
    ["Roczny dochód gospodarstwa", pln(profile.annual_household_income_pln)],
    ["Liczba osób w gospodarstwie", profile.household_members?.toString() ?? "Nie podano"],
  );
  else profileRows.push(
    ["Nazwa przedsiębiorstwa", profile.business_name ?? "Nie podano"],
    ["Wielkość przedsiębiorstwa", label(profile.business_size)],
    ["Forma prawna", label(profile.legal_form)],
    ["Rok rozpoczęcia działalności", profile.established_year?.toString() ?? "Nie podano"],
    ["Liczba pracowników", profile.employee_count?.toString() ?? "Nie podano"],
    ["Roczny obrót", pln(profile.annual_turnover_pln)],
    ["Wykorzystana pomoc de minimis", eur(profile.de_minimis_aid_eur)],
    ["Startup", yesNo(profile.is_startup)],
    ["Inwestor VC", yesNo(profile.has_vc_investor)],
    ["Planowane konsorcjum", yesNo(profile.consortium_planned)],
    ["PKD / branże", profile.industry_codes.join(", ") || "Nie podano"],
  );

  const business = program.details.business_requirements;
  const resources = [...program.details.application_resources];
  const resourceUrls = new Set(resources.map((item) => item.url));
  for (const document of program.documents) if (!resourceUrls.has(document.url)) resources.push({
    title: document.title,
    url: document.url,
    resource_type: document.document_type === "regulations" ? "regulations" : "other",
    description: document.is_available ? null : "Dokument oznaczony jako niedostępny — sprawdź stronę oficjalną.",
  });

  return <article className="report-page">
    <div className="report-toolbar no-print"><Link className="back-link" href={`/konto/profil/${profileId}/dopasowania`}>← Wróć do dopasowań</Link><button className="button" onClick={() => window.print()} type="button">Drukuj / zapisz PDF</button></div>

    <header className="report-hero">
      <p className="eyebrow">Raport dopasowania · #{match.rank}</p>
      <h1>{program.title}</h1>
      <p className="lead compact">Profil: <strong>{profile.name}</strong> · Organizator: {program.organizer}</p>
      <div className="report-result"><span className={`match-outcome ${match.outcome}`}>{outcomeLabels[match.outcome]}</span><strong>{match.score}%<small> reguł spełnionych</small></strong></div>
      <dl className="report-meta">
        <div><dt>Status programu</dt><dd>{statusLabels[program.status]}</dd></div>
        <div><dt>Termin naboru</dt><dd>{formatDate(program.application_start)} – {formatDate(program.application_end)}</dd></div>
        <div><dt>Maksymalna kwota</dt><dd>{formatMoney(program.max_amount, program.currency)}</dd></div>
        <div><dt>Ostatnia weryfikacja</dt><dd>{formatDateTime(program.last_verified_at)}</dd></div>
      </dl>
      <p className="report-generated">Raport obliczono: {formatDateTime(matches.generated_at)} · profil zaktualizowano: {formatDateTime(profile.updated_at)}</p>
    </header>

    {program.summary && <section className="report-section"><p className="eyebrow">Opis programu</p><h2>Najważniejszy kontekst</h2><p>{program.summary}</p></section>}
    <ContentSection title="Najważniejsze wnioski" items={program.details.key_takeaways} />

    <section className="report-section"><p className="eyebrow">Źródło: profil użytkownika</p><h2>Dane przyjęte do porównania</h2><p className="report-intro">Poniższe wartości pochodzą z profilu użytkownika. „Nie podano” oznacza, że silnik nie mógł użyć tej informacji.</p><dl className="report-profile-grid">{profileRows.map(([name, value]) => <div key={name}><dt>{name}</dt><dd>{value}</dd></div>)}</dl></section>

    <section className="report-section"><p className="eyebrow">Wynik silnika reguł</p><h2>Dlaczego powstał taki wynik</h2>{match.missing_data.length > 0 && <p className="missing-summary"><strong>Dane wymagające uzupełnienia:</strong> {match.missing_data.join(", ")}.</p>}<ul className="report-rules">{match.rules.map((rule) => <li key={rule.code}><span className={`rule-status ${rule.status}`}>{ruleLabels[rule.status]}</span><div><h3>{rule.label}</h3><p>{rule.explanation}</p><p className="report-origin"><strong>Porównano:</strong> dane profilu z warunkiem programu.</p>{(rule.source_url || rule.source_reference || rule.evidence_quote) && <div className="report-evidence"><strong>Dowód z regulaminu / źródła programu</strong>{rule.source_reference && <span>{rule.source_reference}</span>}{rule.evidence_quote && <blockquote>„{rule.evidence_quote}”</blockquote>}{rule.source_url && <a href={rule.source_url} rel="noreferrer" target="_blank">Otwórz oficjalne źródło</a>}</div>}{!rule.blocking && <small>Warunek informacyjny — nie blokuje wyniku.</small>}</div></li>)}</ul></section>

    <ContentSection title="Dla kogo jest program" items={program.details.eligible_applicants} />
    <ContentSection title="Warunki przyznania wsparcia" items={program.details.eligibility_conditions} />

    {program.details.funding_options.length > 0 && <section className="report-section"><h2>Kwoty i poziomy wsparcia</h2><div className="funding-grid">{program.details.funding_options.map((item, index) => <article className="funding-card" key={`${item.name}-${index}`}><h3>{item.name}</h3><div className="funding-numbers">{item.support_percent && <strong>{item.support_percent}%</strong>}{item.max_amount && <strong>do {formatMoney(item.max_amount, item.currency)}</strong>}</div><p>{item.description}</p>{(item.source_reference || item.source_url) && <p className="source-note"><strong>Źródło w programie:</strong> {item.source_url ? <a href={item.source_url} rel="noreferrer" target="_blank">{item.source_reference ?? "oficjalny dokument"}</a> : item.source_reference}</p>}</article>)}</div></section>}

    {business && <section className="report-section"><h2>Wymagania dla przedsiębiorstw</h2><dl className="report-profile-grid"><div><dt>PKD</dt><dd>{business.pkd_codes.join(", ") || business.pkd_description || "Nie wskazano"}</dd></div><div><dt>Pomoc de minimis</dt><dd>{label(business.de_minimis)}{business.de_minimis_description ? ` — ${business.de_minimis_description}` : ""}</dd></div><div><dt>Koszty kwalifikowane</dt><dd>{business.eligible_costs.join(", ") || "Nie wskazano"}</dd></div><div><dt>Wkład własny</dt><dd>{business.own_contribution_percent ? `${business.own_contribution_percent}%` : "Nie wskazano"}{business.own_contribution_description ? ` — ${business.own_contribution_description}` : ""}</dd></div><div><dt>Konsorcjum</dt><dd>{label(business.consortium)}{business.consortium_description ? ` — ${business.consortium_description}` : ""}</dd></div></dl>{(business.source_reference || business.source_url) && <p className="source-note"><strong>Źródło:</strong> {business.source_url ? <a href={business.source_url} rel="noreferrer" target="_blank">{business.source_reference ?? "oficjalny dokument"}</a> : business.source_reference}</p>}</section>}

    <ContentSection title="Ważne informacje i ograniczenia" items={program.details.important_information} />
    <ContentSection title="Wymagane dokumenty" items={program.details.required_documents} />

    <section className="report-section report-application"><p className="eyebrow">Następne kroki</p><h2>Jak i gdzie złożyć wniosek</h2>{program.details.application_steps.length > 0 ? <ol className="steps">{program.details.application_steps.map((item, index) => <li key={`${item.title}-${index}`}><h3>{item.title}</h3><p>{item.description}</p><SourceNote item={item} /></li>)}</ol> : <p>Źródło nie zawiera jeszcze kompletnej instrukcji. Skorzystaj z oficjalnej strony programu i aktualnego regulaminu.</p>}</section>

    <section className="report-section"><h2>Wnioski, formularze, instrukcje i regulaminy</h2>{resources.length > 0 ? <div className="resource-list">{resources.map((resource, index) => <a className="resource-card" href={resource.url} key={`${resource.url}-${index}`} rel="noreferrer" target="_blank"><span className="resource-type">{resource.resource_type.replaceAll("_", " ")}</span><strong>{resource.title}</strong>{resource.description && <span>{resource.description}</span>}</a>)}</div> : <p>Nie zapisano osobnych formularzy. Przejdź do oficjalnej strony programu.</p>}<div className="report-official no-print">{program.official_url && <a className="button" href={program.official_url} rel="noreferrer" target="_blank">Otwórz oficjalną stronę programu</a>}</div></section>

    <aside className="notice report-disclaimer"><strong>Ważne:</strong> {matches.disclaimer} Raport wspiera wstępną ocenę i nie zastępuje decyzji instytucji przyznającej dofinansowanie. Przed złożeniem wniosku sprawdź aktualny regulamin i formularze w oficjalnym źródle.</aside>
  </article>;
}
