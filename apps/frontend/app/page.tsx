import Link from "next/link";

import { ProgramList } from "@/components/program-list";
import { getPrograms } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function HomePage() {
  const programs = await getPrograms({ limit: "3" });
  return (
    <>
      <section className="hero"><div className="shell hero-grid">
        <div>
          <p className="eyebrow">Oficjalne źródła · przejrzyste kryteria</p>
          <h1>Znajdź właściwe wsparcie dla domu lub firmy</h1>
          <p className="lead">Porównujemy Twój profil z aktualnymi programami, pokazujemy warunki i zawsze wskazujemy oficjalne źródło.</p>
          <div className="actions"><Link className="button" href="/konto">Sprawdź dopasowania</Link><Link className="secondary-link" href="/dotacje">Przeglądaj katalog →</Link></div>
        </div>
        <aside className="trust-card"><span className="trust-icon" aria-hidden="true">✓</span><strong>Decyzje oparte na danych</strong><ul><li>osobne wyniki dla nieruchomości i firm,</li><li>warunki oraz kwoty wsparcia,</li><li>oficjalne dokumenty i formularze,</li><li>historia zmian i data weryfikacji.</li></ul></aside>
      </div></section>
      <section className="shell section"><div className="section-heading"><div><p className="eyebrow">Najnowsze</p><h2>Zweryfikowane programy</h2></div><Link className="text-link" href="/dotacje">Zobacz wszystkie →</Link></div><ProgramList items={programs.items} /></section>
      <section className="category-band"><div className="shell"><p className="eyebrow">Popularne cele</p><h2>Wsparcie dopasowane do planu inwestycji</h2><div className="category-links"><Link href="/kategoria/fotowoltaika">Fotowoltaika</Link><Link href="/kategoria/magazyny-energii">Magazyny energii</Link><Link href="/kategoria/pompy-ciepla">Pompy ciepła</Link><Link href="/dotacje?beneficiary_type=enterprise">Programy dla firm</Link></div></div></section>
    </>
  );
}
