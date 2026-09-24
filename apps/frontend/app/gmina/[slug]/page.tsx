import { ProgramList } from "@/components/program-list";
import { getPrograms } from "@/lib/api";

export const dynamic = "force-dynamic";
export default async function MunicipalityPage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  const programs = await getPrograms({ location: slug });
  const name = slug === "nadarzyn" ? "Nadarzyn" : slug;
  return <div className="shell section"><p className="eyebrow">Programy lokalne</p><h1>Dotacje: Gmina {name}</h1><p className="lead compact">Nabory gminne oraz programy obejmujące tę lokalizację.</p><ProgramList items={programs.items} /></div>;
}
