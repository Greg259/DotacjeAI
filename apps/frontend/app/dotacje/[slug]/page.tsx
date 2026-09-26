import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";

import { getProgram } from "@/lib/api";
import {
  beneficiaryLabels,
  categoryLabels,
  formatDate,
  formatDateTime,
  formatMoney,
  propertyLabels,
  statusLabels,
} from "@/lib/format";
import type { ProgramContentItem } from "@/lib/types";

export const dynamic = "force-dynamic";
type Params = Promise<{ slug: string }>;

const resourceLabels: Record<string, string> = {
  application_form: "Formularz wniosku",
  statement: "Oświadczenie",
  instructions: "Instrukcja",
  regulations: "Regulamin",
  application_portal: "Portal do składania wniosków",
  official_page: "Strona oficjalna",
  other: "Dokument",
};

function SourceNote({ item }: { item: ProgramContentItem }) {
  if (!item.source_reference && !item.source_url) return null;
  return (
    <p className="source-note">
      Źródło: {item.source_url ? (
        <a href={item.source_url} target="_blank" rel="noreferrer">
          {item.source_reference ?? "oficjalna strona"} ↗
        </a>
      ) : item.source_reference}
    </p>
  );
}

function ContentList({ items }: { items: ProgramContentItem[] }) {
  if (!items.length) return <p>Informacje są uzupełniane na podstawie oficjalnych dokumentów.</p>;
  return (
    <div className="content-list">
      {items.map((item, index) => (
        <div className="content-item" key={`${item.title}-${index}`}>
          <h3>{item.title}</h3>
          <p>{item.description}</p>
          <SourceNote item={item} />
        </div>
      ))}
    </div>
  );
}

export async function generateMetadata({ params }: { params: Params }): Promise<Metadata> {
  const { slug } = await params;
  const program = await getProgram(slug);
  return program ? { title: program.title, description: program.summary, alternates: { canonical: `/dotacje/${slug}` } } : { title: "Nie znaleziono programu" };
}

export default async function ProgramPage({ params }: { params: Params }) {
  const { slug } = await params;
  const program = await getProgram(slug);
  if (!program) notFound();
  const details = program.details;
  const structuredData = {
    "@context": "https://schema.org",
    "@type": "GovernmentService",
    name: program.title,
    description: program.summary,
    provider: { "@type": "GovernmentOrganization", name: program.organizer },
    areaServed: program.locations.map((item) => item.name),
    url: `https://dotacjeai.eu/dotacje/${program.slug}`,
    serviceUrl: program.official_url,
  };

  return (
    <div className="shell section detail-layout">
      <article>
        <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(structuredData).replace(/</g, "\\u003c") }} />
        <Link className="back-link" href="/dotacje">← Wszystkie dotacje</Link>
        <div className="card-topline">
          <span className={`status status-${program.status}`}>{statusLabels[program.status]}</span>
          <span className="verified">Sprawdzono: {formatDate(program.last_verified_at)}</span>
        </div>
        <h1>{program.title}</h1>
        <p className="organizer">{program.organizer}</p>
        <p className="lead compact">{program.summary}</p>
        {program.status !== "open" && (
          <div className={`status-notice status-notice-${program.status}`}>
            <strong>{statusLabels[program.status]}</strong>
            <span>{program.status === "closed" ? "Nabór jest zakończony — karta pozostaje dostępna informacyjnie." : program.status === "planned" ? "Nabór jest zapowiedziany, ale formularz może nie być jeszcze dostępny." : "Status lub dostępność naboru trzeba potwierdzić w oficjalnym źródle albo właściwej gminie."}</span>
          </div>
        )}

        {details.key_takeaways.length > 0 && (
          <section className="detail-section takeaways">
            <h2>Najważniejsze wnioski</h2>
            <ContentList items={details.key_takeaways} />
          </section>
        )}

        <section className="detail-section">
          <h2>Najważniejsze informacje</h2>
          <dl className="details">
            <div><dt>Termin naboru</dt><dd>{formatDate(program.application_start)} – {formatDate(program.application_end)}</dd></div>
            <div><dt>Maksymalna kwota</dt><dd>{formatMoney(program.max_amount, program.currency)}</dd></div>
            <div><dt>Poziom wsparcia</dt><dd>{program.support_percent ? `${Number(program.support_percent)}%` : "Zależy od wariantu"}</dd></div>
            <div><dt>Lokalizacja</dt><dd>{program.locations.map((item) => item.name).join(", ") || "Nie podano"}</dd></div>
          </dl>
        </section>

        <section className="detail-section">
          <h2>Dla kogo i na co</h2>
          <div className="tags large">
            {program.property_types.map((item) => <span key={item}>{propertyLabels[item] ?? item}</span>)}
            {program.beneficiary_types.map((item) => <span key={item}>{beneficiaryLabels[item] ?? item}</span>)}
            {program.investment_categories.map((item) => <span key={item}>{categoryLabels[item] ?? item}</span>)}
          </div>
          <ContentList items={details.eligible_applicants} />
        </section>

        <section className="detail-section">
          <h2>Warunki przyznania dotacji</h2>
          <ContentList items={details.eligibility_conditions} />
        </section>

        <section className="detail-section">
          <h2>Kwoty i poziomy wsparcia</h2>
          {details.funding_options.length ? (
            <div className="funding-grid">
              {details.funding_options.map((option) => (
                <div className="funding-card" key={option.name}>
                  <h3>{option.name}</h3>
                  <div className="funding-numbers">
                    {option.support_percent && <strong>do {Number(option.support_percent)}%</strong>}
                    {option.max_amount && <strong>do {formatMoney(option.max_amount, option.currency)}</strong>}
                  </div>
                  <p>{option.description}</p>
                  {(option.source_reference || option.source_url) && (
                    <p className="source-note">Źródło: {option.source_url ? <a href={option.source_url} target="_blank" rel="noreferrer">{option.source_reference ?? "oficjalna strona"} ↗</a> : option.source_reference}</p>
                  )}
                </div>
              ))}
            </div>
          ) : <p>Szczegółowe kwoty są uzupełniane na podstawie oficjalnych dokumentów.</p>}
        </section>

        <section className="detail-section important-section">
          <h2>Ważne informacje i ograniczenia</h2>
          <ContentList items={details.important_information} />
        </section>

        <section className="detail-section">
          <h2>Jak złożyć wniosek</h2>
          {details.application_steps.length ? (
            <ol className="steps">
              {details.application_steps.map((item, index) => (
                <li key={`${item.title}-${index}`}>
                  <h3>{item.title}</h3>
                  <p>{item.description}</p>
                  <SourceNote item={item} />
                </li>
              ))}
            </ol>
          ) : <p>Instrukcja składania wniosku jest uzupełniana.</p>}
        </section>

        <section className="detail-section">
          <h2>Co przygotować</h2>
          <ContentList items={details.required_documents} />
        </section>

        <section className="detail-section">
          <h2>Wnioski, formularze i oficjalne dokumenty</h2>
          {details.application_resources.length ? (
            <div className="resource-list">
              {details.application_resources.map((resource) => (
                <a className={`resource-card ${program.documents.find((item) => item.url === resource.url)?.is_available === false ? "resource-unavailable" : ""}`} href={resource.url} target="_blank" rel="noreferrer" key={resource.url}>
                  <span className="resource-type">{resourceLabels[resource.resource_type] ?? "Dokument"}</span>
                  <strong>{resource.title} ↗</strong>
                  {resource.description && <span>{resource.description}</span>}
                  <span>Ostatnia kontrola linku: {formatDateTime(program.documents.find((item) => item.url === resource.url)?.last_checked_at ?? null)}</span>
                  {program.documents.find((item) => item.url === resource.url)?.state !== "current" && <span className="resource-warning">Dokument wymaga ponownej weryfikacji</span>}
                </a>
              ))}
            </div>
          ) : <p>Oficjalne formularze są uzupełniane.</p>}
        </section>

        <section className="detail-section">
          <h2>Wszystkie źródła</h2>
          {program.documents.length ? (
            <ul className="source-list">
              {program.documents.map((doc) => <li key={doc.url}><a href={doc.url} target="_blank" rel="noreferrer">{doc.title} ↗</a><span className="document-checked">sprawdzono link: {formatDateTime(doc.last_checked_at)}</span>{doc.state !== "current" && <span className="resource-warning"> — {doc.state_reason ?? "dokument wymaga weryfikacji"}</span>}</li>)}
            </ul>
          ) : <p>Oficjalny dokument jest przygotowywany.</p>}
          {program.official_url && <a className="button small" href={program.official_url} target="_blank" rel="noreferrer">Otwórz oficjalną stronę</a>}
        </section>

        {program.versions.length > 0 && (
          <section className="detail-section">
            <h2>Historia zmian</h2>
            <ol className="history">
              {program.versions.map((version) => (
                <li key={version.version_number}>
                  <strong>Wersja {version.version_number}</strong>
                  <span>{formatDate(version.approved_at)}</span>
                  <p>{version.change_summary ?? "Zatwierdzona aktualizacja danych."}</p>
                </li>
              ))}
            </ol>
          </section>
        )}
      </article>
      <aside className="notice">
        <strong>Ważne</strong>
        <p>Podsumowanie pomaga przygotować się do złożenia wniosku. Ostatecznie obowiązuje regulamin i dokumenty instytucji prowadzącej nabór.</p>
      </aside>
    </div>
  );
}
