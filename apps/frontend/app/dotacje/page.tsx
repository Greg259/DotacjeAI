import type { Metadata } from "next";

import { Filters } from "@/components/filters";
import { ProgramList } from "@/components/program-list";
import { Pagination } from "@/components/pagination";
import { getPrograms } from "@/lib/api";

export const dynamic = "force-dynamic";
export const metadata: Metadata = { title: "Dotacje" };

type SearchParams = Promise<Record<string, string | string[] | undefined>>;

export default async function ProgramsPage({ searchParams }: { searchParams: SearchParams }) {
  const values = await searchParams;
  const programs = await getPrograms(values);
  return <div className="shell section"><p className="eyebrow">Zweryfikowana baza programów</p><h1>Dotacje dla osób prywatnych i firm</h1><p className="lead compact">Znaleziono {programs.total} programów. Użyj filtrów, aby zobaczyć wsparcie odpowiadające Twojej lokalizacji i inwestycji.</p><Filters values={values} /><ProgramList items={programs.items} /><Pagination total={programs.total} limit={programs.limit} offset={programs.offset} values={values} /></div>;
}
