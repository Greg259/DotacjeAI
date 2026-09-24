import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";

import { beneficiaryLabels, categoryLabels, formatDate, formatMoney, propertyLabels, statusLabels } from "@/lib/format";
import { getProgram } from "@/lib/api";

export const dynamic = "force-dynamic";
type Params = Promise<{ slug: string }>;

export async function generateMetadata({ params }: { params: Params }): Promise<Metadata> {
  const { slug } = await params;
  const program = await getProgram(slug);
  return program ? { title: program.title, description: program.summary } : { title: "Nie znaleziono programu" };
}

export default async function ProgramPage({ params }: { params: Params }) {
  const { slug } = await params;
  const program = await getProgram(slug);
  if (!program) notFound();
  return <div className="shell section detail-layout"><article>
    <Link className="back-link" href="/dotacje">← Wszystkie dotacje</Link>
    <div className="card-topline"><span className={`status status-${program.status}`}>{statusLabels[program.status]}</span><span className="verified">Sprawdzono: {formatDate(program.last_verified_at)}</span></div>
    <h1>{program.title}</h1><p className="organizer">{program.organizer}</p><p className="lead compact">{program.summary}</p>
    <section className="detail-section"><h2>Najważniejsze informacje</h2><dl className="details"><div><dt>Termin naboru</dt><dd>{formatDate(program.application_start)} – {formatDate(program.application_end)}</dd></div><div><dt>Maksymalna kwota</dt><dd>{formatMoney(program.max_amount, program.currency)}</dd></div><div><dt>Poziom wsparcia</dt><dd>{program.support_percent ? `${Number(program.support_percent)}%` : "Nie podano"}</dd></div><div><dt>Lokalizacja</dt><dd>{program.locations.map((item) => item.name).join(", ") || "Nie podano"}</dd></div></dl></section>
    <section className="detail-section"><h2>Dla kogo i na co</h2><div className="tags large">{program.property_types.map((item) => <span key={item}>{propertyLabels[item] ?? item}</span>)}{program.beneficiary_types.map((item) => <span key={item}>{beneficiaryLabels[item] ?? item}</span>)}{program.investment_categories.map((item) => <span key={item}>{categoryLabels[item] ?? item}</span>)}</div></section>
    <section className="detail-section"><h2>Dokumenty i źródła</h2>{program.documents.length ? <ul className="source-list">{program.documents.map((doc) => <li key={doc.url}><a href={doc.url} target="_blank" rel="noreferrer">{doc.title} ↗</a></li>)}</ul> : <p>Oficjalny dokument jest przygotowywany.</p>}{program.official_url && <a className="button small" href={program.official_url} target="_blank" rel="noreferrer">Otwórz oficjalną stronę</a>}</section>
    {program.versions.length > 0 && <section className="detail-section"><h2>Historia zmian</h2><ol className="history">{program.versions.map((version) => <li key={version.version_number}><strong>Wersja {version.version_number}</strong><span>{formatDate(version.approved_at)}</span><p>{version.change_summary ?? "Zatwierdzona aktualizacja danych."}</p></li>)}</ol></section>}
  </article><aside className="notice"><strong>Ważne</strong><p>Portal pomaga znaleźć program. Przed złożeniem wniosku potwierdź warunki w oficjalnym regulaminie.</p></aside></div>;
}
