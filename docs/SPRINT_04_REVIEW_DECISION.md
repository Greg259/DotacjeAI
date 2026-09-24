# Sprint 04 — decyzje REVIEW przed pierwszą publikacją

Stan: wykonane 2026-09-24

Wynik: 2 zadania `approved`, 1 zadanie `rejected`, 2 programy opublikowane

Właściciel jawnie zatwierdził rekomendację. Operacje `approve`, `reject` i późniejsze, osobne operacje `publish` zostały wykonane oraz zweryfikowane.

## 1. Gmina Nadarzyn

Review ID: `b14946a7-1d07-466b-88b3-c9dbd23516f6`  
Decyzja: **approved** i **published**.

Program ID: `00af1be1-e50d-49fb-a77c-8be877478173`

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
Decyzja: **approved** i **published**.

Program ID: `4b672da8-5e6c-4b1d-90ef-ab8f208b318b`

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
Decyzja: **rejected** jako słabszy duplikat.

Proponowane uzasadnienie odrzucenia:

> Duplikat wyniku bazowego. Wariant ustawia 100% jako jedną wartość wsparcia mimo kilku poziomów programu i nie zachowuje listy dokumentów. Do publikacji wybrano pełniejszy wynik `7605513b-f481-4860-adee-34f6d367d67b`.

## 4. Weryfikacja po publikacji

1. Przed publikacją oba programy zwracały publicznie `404`, a lista miała `total: 0`.
2. Po publikacji lista ma `total: 2`.
3. Filtr Nadarzyn + `closed` zwraca jeden program.
4. Filtr Mazowieckie + `open` + `heat_pump` zwraca jeden program.
5. Nadarzyn ma jedną zatwierdzoną wersję i jeden dokument.
6. Czyste Powietrze ma jedną zatwierdzoną wersję i trzy dokumenty.
7. Landing, lista, strony regionu/gminy i obie karty zwracają HTTP 200 oraz treść programów.
8. Backup po publikacji: `bdb9f3f2`; Restic, SHA-256 i pełny import do tymczasowej bazy zakończyły się poprawnie.
9. Rotacja ujawnionego klucza OpenRouter pozostaje ostatnią czynnością Sprintu 04.
