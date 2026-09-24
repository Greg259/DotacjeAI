"use client";

export default function ErrorPage({ reset }: { reset: () => void }) {
  return <div className="shell section empty-state"><h1>Nie udało się pobrać danych</h1><p>Spróbuj ponownie za chwilę.</p><button className="button" onClick={() => reset()}>Ponów</button></div>;
}
