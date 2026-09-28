import type { Metadata } from "next";

import { MatchReport } from "@/components/match-report";

export const metadata: Metadata = { title: "Raport dopasowania" };

export default async function MatchReportPage({ params }: { params: Promise<{ id: string; slug: string }> }) {
  const { id, slug } = await params;
  return <section className="shell section"><MatchReport profileId={id} slug={slug} /></section>;
}
