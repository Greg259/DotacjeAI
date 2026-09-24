import { ProgramList } from "@/components/program-list";
import { getPrograms } from "@/lib/api";

const categories: Record<string, { api: string; label: string }> = {
  fotowoltaika: { api: "photovoltaics", label: "Fotowoltaika" },
  "magazyny-energii": { api: "energy_storage", label: "Magazyny energii" },
  "pompy-ciepla": { api: "heat_pump", label: "Pompy ciepła" },
};

export const dynamic = "force-dynamic";
export default async function CategoryPage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  const category = categories[slug] ?? { api: slug, label: slug };
  const programs = await getPrograms({ category: category.api });
  return <div className="shell section"><p className="eyebrow">Cel inwestycji</p><h1>Dotacje: {category.label}</h1><p className="lead compact">Zweryfikowane programy wspierające tę inwestycję.</p><ProgramList items={programs.items} /></div>;
}
