import { ProgramList } from "@/components/program-list";
import { getPrograms } from "@/lib/api";

export const dynamic = "force-dynamic";
export default async function RegionPage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  const programs = await getPrograms({ location: slug });
  return <div className="shell section"><p className="eyebrow">Region</p><h1>Dotacje: województwo mazowieckie</h1><p className="lead compact">Zweryfikowane programy dostępne na Mazowszu.</p><ProgramList items={programs.items} /></div>;
}
