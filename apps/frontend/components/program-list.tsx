import { ProgramCard } from "./program-card";
import type { ProgramItem } from "@/lib/types";

export function ProgramList({ items }: { items: ProgramItem[] }) {
  if (items.length === 0) {
    return (
      <div className="empty-state">
        <h2>Brak opublikowanych dotacji dla tych filtrów</h2>
        <p>Źródła są monitorowane. Program pojawi się po weryfikacji i zatwierdzeniu danych.</p>
      </div>
    );
  }
  return <div className="program-grid">{items.map((item) => <ProgramCard key={item.id} program={item} />)}</div>;
}
