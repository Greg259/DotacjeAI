import Link from "next/link";

import { categoryLabels, formatDate, formatMoney, statusLabels } from "@/lib/format";
import type { ProgramItem } from "@/lib/types";

export function ProgramCard({ program }: { program: ProgramItem }) {
  return (
    <article className="program-card">
      <div className="card-topline">
        <span className={`status status-${program.status}`}>{statusLabels[program.status]}</span>
        <span className="verified">Sprawdzono: {formatDate(program.last_verified_at)}</span>
      </div>
      <h2><Link href={`/dotacje/${program.slug}`}>{program.title}</Link></h2>
      <p className="organizer">{program.organizer}</p>
      <p>{program.summary ?? "Opis programu jest przygotowywany."}</p>
      <div className="facts">
        <span><strong>Do:</strong> {formatDate(program.application_end)}</span>
        <span><strong>Maksymalnie:</strong> {formatMoney(program.max_amount, program.currency)}</span>
      </div>
      <div className="tags">
        {program.investment_categories.map((category) => (
          <span key={category}>{categoryLabels[category] ?? category}</span>
        ))}
        {program.locations.map((location) => <span key={location.slug}>{location.name}</span>)}
      </div>
      <Link className="text-link" href={`/dotacje/${program.slug}`}>Zobacz szczegóły →</Link>
    </article>
  );
}
