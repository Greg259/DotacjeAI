import type { Metadata } from "next";

export const metadata: Metadata = { title: "Regulamin wersji testowej" };

export default function TermsPage() {
  return <article className="shell narrow-section legal-copy"><p className="eyebrow">Wersja testowa · 26.09.2026</p><h1>Regulamin korzystania z DotacjeAI</h1><p>DotacjeAI jest narzędziem informacyjnym pomagającym przeglądać oficjalne programy dotacyjne i przygotowywać profile nieruchomości. Utworzenie konta jest dobrowolne.</p><h2>Charakter informacji</h2><p>Wyniki i opisy nie są decyzją instytucji przyznającej dotację ani poradą prawną. Przed złożeniem wniosku użytkownik powinien sprawdzić aktualny regulamin i dokumenty wskazane na karcie programu.</p><h2>Konto użytkownika</h2><p>Użytkownik odpowiada za poufność hasła oraz prawdziwość zapisanych danych. Nie należy używać hasła stosowanego w innym serwisie. Konto i profile można w dowolnym momencie usunąć.</p><h2>Wersja testowa</h2><p>Funkcje mogą być rozwijane, a dostęp czasowo ograniczony podczas prac technicznych. Przed publiczną betą regulamin zostanie uzupełniony o pełne dane usługodawcy i wymagane postanowienia prawne.</p></article>;
}
