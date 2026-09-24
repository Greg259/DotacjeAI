import type { Metadata } from "next";

import { ProgramList } from "@/components/program-list";
import { getPrograms } from "@/lib/api";

export const dynamic = "force-dynamic";

export async function generateMetadata({ params }: { params: Promise<{ slug: string }> }): Promise<Metadata> {
  const { slug } = await params;
  const label = slug === "pruszkowski" ? "pruszkowski" : slug;
  return { title: `Dotacje — powiat ${label}`, alternates: { canonical: `/powiat/${slug}` } };
}

export default async function CountyPage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  const programs = await getPrograms({ location: slug });
  const name = slug === "pruszkowski" ? "pruszkowski" : slug;
  return <div className="shell section"><p className="eyebrow">Programy powiatowe</p><h1>Dotacje: powiat {name}</h1><p className="lead compact">Zweryfikowane nabory obejmujące ten powiat.</p><ProgramList items={programs.items} /></div>;
}
