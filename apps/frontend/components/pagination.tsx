import Link from "next/link";

type Values = Record<string, string | string[] | undefined>;

function pageHref(values: Values, offset: number, limit: number): string {
  const query = new URLSearchParams();
  for (const [key, rawValue] of Object.entries(values)) {
    if (key === "offset") continue;
    const value = Array.isArray(rawValue) ? rawValue[0] : rawValue;
    if (value) query.set(key, value);
  }
  query.set("limit", String(limit));
  query.set("offset", String(Math.max(0, offset)));
  return `/dotacje?${query.toString()}`;
}

export function Pagination({ total, limit, offset, values }: { total: number; limit: number; offset: number; values: Values }) {
  if (total <= limit) return null;
  const current = Math.floor(offset / limit) + 1;
  const pages = Math.ceil(total / limit);
  return (
    <nav className="pagination" aria-label="Stronicowanie wyników">
      {offset > 0 && <Link href={pageHref(values, offset - limit, limit)}>← Poprzednia</Link>}
      <span>Strona {current} z {pages}</span>
      {offset + limit < total && <Link href={pageHref(values, offset + limit, limit)}>Następna →</Link>}
    </nav>
  );
}
