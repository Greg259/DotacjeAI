"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

type Rule = { code: string; label: string; status: string; explanation: string };
type Match = {
  program_id: string; slug: string; title: string; organizer: string; program_status: string;
  application_end: string | null; max_amount: string | null; currency: string;
  outcome: "eligible" | "possible" | "not_eligible"; score: number; rank: number;
  missing_data: string[]; rules: Rule[];
};
type MatchResponse = {
  profile_name: string; profile_kind: string; generated_at: string;
  results: Match[]; disclaimer: string;
};

const outcomeLabels = { eligible: "Pasuje", possible: "Możliwe dopasowanie", not_eligible: "Nie pasuje" };
const ruleLabels: Record<string, string> = {
  fulfilled: "spełnione", not_fulfilled: "niespełnione", missing_data: "brak danych",
};

export function MatchResults({ profileId }: { profileId: string }) {
  const router = useRouter();
  const [data, setData] = useState<MatchResponse | null>(null);
  const [error, setError] = useState("");
  useEffect(() => {
    fetch(`/api/profiles/${profileId}/matches`).then(async (response) => {
      if (response.status === 401) return router.replace("/konto/logowanie");
      if (!response.ok) return setError("Nie udało się obliczyć dopasowań.");
      setData(await response.json());
    });
  }, [profileId, router]);
  if (error) return <p className="form-error">{error}</p>;
  if (!data) return <p>Obliczanie dopasowań…</p>;
  return <>
    <div className="section-heading"><div><p className="eyebrow">Profil</p><h1>{data.profile_name}</h1></div><Link className="secondary-button" href="/konto">Wróć do konta</Link></div>
    <p className="notice">{data.disclaimer}</p>
    <div className="match-list">{data.results.map((item) => <article className={`match-card match-${item.outcome}`} key={item.program_id}>
      <div className="match-heading"><div><span className={`match-outcome ${item.outcome}`}>{outcomeLabels[item.outcome]}</span><h2>#{item.rank} · <Link href={`/dotacje/${item.slug}`}>{item.title}</Link></h2><p>{item.organizer}</p></div><strong className="match-score">{item.score}%<small>reguł spełnionych</small></strong></div>
      {item.missing_data.length > 0 && <p className="missing-summary"><strong>Wymaga uzupełnienia:</strong> {item.missing_data.join(", ")}.</p>}
      <ul className="match-rules">{item.rules.map((rule) => <li key={rule.code}><span className={`rule-status ${rule.status}`}>{ruleLabels[rule.status]}</span><div><strong>{rule.label}</strong><p>{rule.explanation}</p></div></li>)}</ul>
    </article>)}</div>
  </>;
}
