# Sprint 04 — decyzje REVIEW przed pierwszą publikacją

Stan: 2026-09-24  
Kolejka: 3 zadania `pending`, 3 ekstrakcje `ready_for_review`, 0 programów publicznych

Dokument nie wykonuje `approve`, `reject` ani `publish`. Zawiera rekomendację techniczną do jawnej decyzji właściciela.

## 1. Gmina Nadarzyn

Review ID: `b14946a7-1d07-466b-88b3-c9dbd23516f6`  
Rekomendacja: **approve**, a następnie osobne **publish**.

Najważniejsze dane potwierdzone w oficjalnym regulaminie:

- status dla naboru 2026: `closed`,
- termin: do 31 lipca 2026 r.,
- poziom wsparcia: 100% udokumentowanych kosztów zakupu,
- maksymalna kwota: 6000 PLN,
- lokalizacja: Gmina Nadarzyn,
- cel: wymiana nieefektywnego źródła ciepła na paliwo stałe,
- beneficjenci obejmują m.in. osoby fizyczne i wspólnoty mieszkaniowe posiadające tytuł prawny do nieruchomości.

Ostrzeżenie `property_type_inferred` należy pozostawić w audycie. Oznaczenie `existing_building` jest logiczne, ponieważ program wymaga posiadania i wymiany już eksploatowanego źródła ciepła, ale regulamin nie podaje wprost typu budynku.

Oficjalny dokument: `https://www.nadarzyn.pl/plik,23325,regulamin-zalacznik-nr-1-do-uchwaly-nr-xxv-564-2026-pdf.pdf`

## 2. Czyste Powietrze — wynik bazowy

Review ID: `7605513b-f481-4860-adee-34f6d367d67b`  
Powód: `new_program`  
Rekomendacja: **approve**, a następnie osobne **publish**.

Dlaczego ten wariant:

- zachowuje trzy oficjalne adresy dokumentów i obsługi wniosku,
- nie wpisuje jednej mylącej wartości procentowej dla programu mającego kilka poziomów wsparcia,
- pozostawia `max_amount` jako brak jednej kwoty dla całego programu,
- jawnie zapisuje brak daty końca naboru,
- obejmuje wymianę źródła ciepła, termomodernizację i pompy ciepła,
- ogranicza nieruchomości do istniejących budynków jednorodzinnych.

Oficjalne źródło: `https://wfosigw.pl/czyste-powietrze/ogloszenie-o-naborze/`

## 3. Czyste Powietrze — wynik duplikujący

Review ID: `4777f3b0-fe97-4fbe-a5d6-3aae786a00b2`  
Powód: `source_changed`  
Rekomendacja: **reject** jako słabszy duplikat.

Proponowane uzasadnienie odrzucenia:

> Duplikat wyniku bazowego. Wariant ustawia 100% jako jedną wartość wsparcia mimo kilku poziomów programu i nie zachowuje listy dokumentów. Do publikacji wybrano pełniejszy wynik `7605513b-f481-4860-adee-34f6d367d67b`.

## 4. Kolejność po decyzji właściciela

1. Wykonać `approve` dla zatwierdzonych review ID.
2. Sprawdzić utworzone rekordy, wersje, dokumenty i audit log.
3. Niezwłocznie sprawdzić karty w API przed publikacją — nadal powinny zwracać `404`.
4. Wykonać osobne `publish` dla każdego zaakceptowanego programu.
5. Przetestować listę, filtry, kartę, dokumenty i oficjalne źródło przez HTTPS.
6. Wykonać backup oraz pełny test odtworzenia.
7. Rotację ujawnionego klucza OpenRouter wykonać dopiero jako ostatnią czynność Sprintu 04.
