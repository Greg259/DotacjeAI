import type { Metadata } from "next";

import { MatchResults } from "@/components/match-results";

export const metadata: Metadata = { title: "Dopasowane dotacje" };

export default async function MatchesPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return <section className="shell section"><MatchResults profileId={id} /></section>;
}
