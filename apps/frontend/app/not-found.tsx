import Link from "next/link";

export default function NotFound() {
  return <div className="shell section empty-state"><h1>Nie znaleziono programu</h1><p>Program nie istnieje albo nie został jeszcze opublikowany.</p><Link className="button" href="/dotacje">Wróć do listy</Link></div>;
}
