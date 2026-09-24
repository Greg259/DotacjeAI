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
          <p className="eyebrow">Oficjalne źródła · jasne kryteria</p>
          <h1>Znajdź dotację dla swojego domu lub mieszkania</h1>
          <p className="lead">Monitorujemy nabory i dokumenty, a każdą informację publikujemy dopiero po weryfikacji.</p>
          <div className="actions"><Link className="button" href="/dotacje">Przeglądaj dotacje</Link><Link className="secondary-link" href="/gmina/nadarzyn">Programy w Nadarzynie</Link></div>
        </div>
        <aside className="trust-card"><strong>Co znajdziesz przy programie?</strong><ul><li>aktualny status i termin,</li><li>kwotę oraz poziom wsparcia,</li><li>oficjalne dokumenty,</li><li>datę ostatniej weryfikacji.</li></ul></aside>
      </div></section>
      <section className="shell section"><div className="section-heading"><div><p className="eyebrow">Najnowsze</p><h2>Zweryfikowane programy</h2></div><Link className="text-link" href="/dotacje">Zobacz wszystkie →</Link></div><ProgramList items={programs.items} /></section>
      <section className="category-band"><div className="shell"><p className="eyebrow">Popularne cele</p><div className="category-links"><Link href="/kategoria/fotowoltaika">Fotowoltaika</Link><Link href="/kategoria/magazyny-energii">Magazyny energii</Link><Link href="/kategoria/pompy-ciepla">Pompy ciepła</Link></div></div></section>
    </>
  );
}
