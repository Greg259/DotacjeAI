# Raporty dopasowania

Data wdrożenia: 2026-09-28.

## Cel

Każdy wynik na stronie dopasowań ma przycisk **Pełny raport dopasowania**. Raport jest dostępny wyłącznie w chronionej strefie konta i łączy trzy warstwy informacji:

1. dane zapisane przez użytkownika w wybranym profilu,
2. deterministyczny wynik dopasowania i wyjaśnienie każdej reguły,
3. dane programu, regulaminów, formularzy i oficjalnych źródeł.

## Zakres raportu

- wynik, pozycja rankingu i procent spełnionych reguł,
- status programu, termin, maksymalna kwota i data weryfikacji,
- komplet użytych danych profilu oraz jawne oznaczenie braków,
- każda reguła jako spełniona, niespełniona albo wymagająca danych,
- wskazanie, że silnik porównał dane profilu z warunkiem programu,
- cytat, paragraf lub odnośnik do oficjalnego źródła, jeśli jest zapisany,
- beneficjenci, warunki, kwoty, ograniczenia i wymagane dokumenty,
- wymagania firmowe: PKD, de minimis, koszty, wkład własny i konsorcjum,
- instrukcja ubiegania się o wsparcie,
- wnioski, formularze, instrukcje, regulaminy i strona oficjalna.

Brak dowodu źródłowego nie jest ukrywany. Raport prezentuje tylko informacje zapisane i zatwierdzone dla programu, a na końcu przypomina o konieczności sprawdzenia aktualnego regulaminu.

## Drukowanie

Przycisk **Drukuj / zapisz PDF** wywołuje systemowe okno drukowania przeglądarki. Osobny styl A4:

- ukrywa nawigację, stopkę i przyciski,
- wymusza jasne, kontrastowe kolory także po użyciu dark mode,
- ogranicza dzielenie kart, reguł i formularzy między stronami,
- pozwala zapisać raport jako PDF bez osobnego generatora po stronie serwera.

## Bezpieczeństwo i ograniczenia

- Profil i wynik są pobierane z endpointów wymagających aktywnej sesji.
- Brak sesji powoduje przekierowanie do logowania.
- Raport nie wykonuje kwalifikacji przez LLM; pokazuje wynik deterministycznego silnika.
- Raport nie stanowi decyzji o przyznaniu wsparcia.

## Weryfikacja

- TypeScript `tsc --noEmit`: sukces.
- Produkcyjny build Next.js: sukces; trasa raportu występuje w manifeście routingu.
- GitHub Actions run 62 dla commita `63c2dbe`: sukces.
- Wdrożenie na VPS: commit `63c2dbe01f079e26b24f49f8395a7478a8a30603`.
- Backup przed wdrożeniem: snapshot Restic `e0b2271e`; repozytorium, 474 pliki i katalogi, SHA-256 dumpa oraz pełny import PostgreSQL zostały poprawnie zweryfikowane.
- Odbiór: 51 programów, 34 zadania REVIEW, 1 niedostępny dokument, poprawne zabezpieczenia API i pięć zdrowych kontenerów.
