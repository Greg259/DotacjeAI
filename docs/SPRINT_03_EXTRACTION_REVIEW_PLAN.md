# Sprint 03 — ekstrakcja AI, REVIEW i pierwsza publikacja

Data planu: 2026-09-23  
Stan wejściowy: API 0.3.0, crawler produkcyjny, dwa oczekujące zadania REVIEW  
Cel: przeprowadzić co najmniej jeden program od oficjalnego snapshotu do ręcznie zatwierdzonej publikacji

## 1. Rezultat sprintu

Po zakończeniu sprintu system powinien:

1. pobrać najnowszy zmieniony snapshot źródła,
2. wydobyć dane deterministyczne bez LLM tam, gdzie jest to możliwe,
3. wysłać pozostałą treść do OpenRouter wyłącznie w granicach budżetu,
4. otrzymać i zwalidować strukturalny JSON wraz z dowodami źródłowymi,
5. zapisać koszt, tokeny, model, czas i wynik wywołania,
6. przedstawić wynik administratorowi przez bezpieczne CLI dostępne przez SSH,
7. po jawnym zatwierdzeniu utworzyć wersję programu,
8. opublikować program dopiero osobnym poleceniem administratora,
9. pokazać zatwierdzony program w publicznym API `/api/programs`.

Pierwszym testem biznesowym będzie Nadarzyn, który musi zostać rozpoznany jako program zakończony. Drugim będzie WFOŚiGW Warszawa / Czyste Powietrze.

## 2. Zakres sprintu

### W zakresie

- wersjonowany schemat danych ekstrakcji,
- dowód źródłowy dla każdego istotnego pola,
- deterministyczna ekstrakcja dat, kwot, procentów i linków,
- klient OpenRouter z timeoutem, retry i walidacją odpowiedzi,
- kontrola budżetu dziennego i miesięcznego,
- routing model tani → walidator → model mocniejszy tylko przy potrzebie,
- pełne logowanie techniczne wywołań bez sekretów i pełnych promptów,
- idempotencja ekstrakcji,
- kolejka REVIEW obsługiwana przez CLI na VPS,
- approve, reject, korekta danych i osobna publikacja,
- historia wersji oraz audit log,
- testy jednostkowe, integracyjne i migracyjne,
- wdrożenie produkcyjne dla dwóch istniejących snapshotów.

### Poza zakresem

- publiczny panel administratora bez uwierzytelnienia,
- konta użytkowników i role webowe,
- matching profilu nieruchomości,
- alerty e-mail,
- OCR skanowanych PDF-ów,
- automatyczna publikacja wyniku LLM,
- uruchomienie wszystkich siedmiu źródeł,
- prywatne dokumenty użytkowników.

Panel webowy będzie osobnym sprintem po ustaleniu bezpiecznego uwierzytelnienia administratora. W tym sprincie operacje REVIEW będą możliwe wyłącznie przez konto `deploy` i SSH.

## 3. Docelowy model danych ekstrakcji

Wynik `ExtractionCandidate` powinien zawierać co najmniej:

- tytuł programu,
- organizatora,
- opis skrócony,
- status: `open`, `planned`, `suspended`, `closed` albo `unknown`,
- datę rozpoczęcia i zakończenia naboru,
- maksymalną kwotę,
- procent wsparcia,
- walutę,
- lokalizacje,
- typy beneficjentów,
- typy nieruchomości,
- kategorie inwestycji,
- oficjalny URL,
- dokumenty źródłowe,
- datę ostatniej weryfikacji,
- ostrzeżenia i pola nieustalone.

Każde pole istotne biznesowo musi mieć `evidence`:

- identyfikator snapshotu,
- krótki fragment źródła,
- numer strony PDF albo URL sekcji,
- metodę pozyskania: reguła albo LLM,
- poziom pewności,
- opcjonalną informację o konflikcie.

Brak dowodu dla daty, kwoty, statusu lub poziomu wsparcia blokuje publikację.

## 4. Kolejność implementacji

### Etap A — kontrakt i migracja

1. Utworzyć modele Pydantic `ExtractionCandidate`, `FieldEvidence` i `ExtractionWarning`.
2. Dodać wersję schematu i promptu, np. `extraction-v1`.
3. Rozszerzyć bazę o stan przetwarzania snapshotu i idempotency key.
4. Ustalić unikalność: snapshot + wersja promptu + rodzaj zadania.
5. Dodać migrację Alembic oraz test upgrade/downgrade na PostgreSQL 16.

### Etap B — ekstrakcja bez LLM

1. Wydobywać linki i tytuły dokumentów z HTML.
2. Rozpoznawać polskie formaty dat i zakresy naboru.
3. Rozpoznawać kwoty PLN, procent wsparcia i podstawowe statusy.
4. Zachować dokładny fragment tekstu jako dowód.
5. Oznaczać konflikty zamiast arbitralnie wybierać wartość.

Reguły deterministyczne mają pierwszeństwo dla prostych, jednoznacznych danych. LLM otrzyma wynik reguł i powinien uzupełniać braki, a nie bezwarunkowo przeliczać całość.

### Etap C — OpenRouter i budżet

1. Sprawdzić aktualne modele i ceny OpenRouter w dniu implementacji.
2. Wybrać 2–3 tanie modele do krótkiego benchmarku na tych samych fixture’ach.
3. Ustawić modele wyłącznie przez zmienne środowiskowe.
4. Wymusić odpowiedź zgodną ze schematem JSON.
5. Walidować JSON przez Pydantic i odrzucać dodatkowe, nieznane pola.
6. Zapisywać model, tokeny wejścia/wyjścia, koszt, czas, status i błąd w `llm_runs`.
7. Ustawić limity:
   - dzienny: 1 USD,
   - ostrzeżenie miesięczne: 5 USD,
   - alarm krytyczny: 8 USD,
   - twardy limit miesięczny: 10 USD.
8. Ograniczyć pierwszy benchmark produkcyjny do maksymalnie 0,50 USD.
9. Po błędzie JSON wykonać najwyżej jedną próbę naprawczą.
10. Użyć mocniejszego modelu tylko po błędzie walidacji, konflikcie lub niskiej pewności.

Klucz `OPENROUTER_API_KEY` zostanie wpisany ręcznie bezpośrednio do `/opt/dotacje-ai/secrets/app.env`. Nie może znaleźć się w rozmowie, Git, dokumentacji, logach ani historii powłoki.

### Etap D — bezpieczne REVIEW przez CLI

Przygotować polecenia operatorskie:

```bash
./server/run_extraction.sh --pending
./server/review_cli.sh list
./server/review_cli.sh show <review-id>
./server/review_cli.sh approve <review-id>
./server/review_cli.sh reject <review-id> --note "powód"
./server/review_cli.sh publish <program-id>
```

Wymagania:

- `approve` nie publikuje automatycznie,
- `publish` działa tylko na zatwierdzonej i poprawnej wersji,
- każda operacja zapisuje audit log z aktorem `deploy`,
- odrzucenie wymaga notatki,
- ponowne wykonanie tej samej operacji jest bezpieczne,
- CLI nie pokazuje klucza API ani sekretów bazy.

### Etap E — utworzenie programu i publikacja

1. Zatwierdzenie tworzy lub aktualizuje `Program` i `ProgramVersion`.
2. Wersja programu wskazuje dokładny `SourceSnapshot`.
3. Program pozostaje `is_published=false` do osobnego polecenia.
4. Publikacja ustawia `published_at`, `last_verified_at` i zapisuje audit log.
5. Nadarzyn musi otrzymać status `closed` oraz termin 31.07.2026, jeżeli potwierdzi to zatwierdzony dowód.
6. Publiczne API pokazuje wyłącznie zatwierdzone i opublikowane rekordy.
7. Odpowiedź API zawiera oficjalny URL i datę ostatniej weryfikacji.

## 5. Bezpieczeństwo

- treść strony i PDF jest traktowana jako niezaufane dane, nie jako instrukcja dla modelu,
- prompt systemowy zabrania wykonywania poleceń znalezionych w dokumencie,
- LLM nie otrzymuje sekretów, konfiguracji serwera ani danych użytkowników,
- pełna treść promptu i odpowiedzi nie trafia do zwykłych logów aplikacji,
- publikacja zawsze wymaga człowieka,
- panel administracyjny nie jest wystawiany publicznie,
- limity kosztów są sprawdzane przed każdym wywołaniem,
- timeout i retry nie mogą spowodować wielokrotnego rozliczenia tego samego zadania bez zapisu stanu,
- tekst dowodowy jest ograniczony długością, ale zachowuje możliwość audytu.

## 6. Testy wymagane przed wdrożeniem

1. Poprawny strukturalny JSON z modelu mockowanego.
2. Błędny JSON i jedna próba naprawcza.
3. Odpowiedź z nieznanym polem.
4. Brak dowodu dla statusu lub terminu.
5. Timeout, HTTP 429 i błąd 5xx OpenRouter.
6. Przekroczenie limitu dziennego i miesięcznego.
7. Ponowienie tego samego snapshotu bez duplikatu kosztu i wersji.
8. Konflikt kwoty 5000/6000 zł w źródłach Nadarzyna.
9. Rozpoznanie Nadarzyna jako `closed` po 31.07.2026.
10. Próba publikacji przed zatwierdzeniem — musi zostać odrzucona.
11. Approve, reject i publish zapisują audit log.
12. Publiczne API nie pokazuje wersji roboczej.
13. Migracja od aktualnej bazy produkcyjnej oraz start od pustej bazy.
14. Test, że klucz OpenRouter nie pojawia się w logach ani wyjątkach.

Minimalny próg jakości benchmarku:

- 100% poprawności statusu i terminu dla dwóch źródeł pilotażowych,
- 100% obecności oficjalnego URL i identyfikatora snapshotu,
- brak publikacji bez dowodów,
- zero duplikatów po ponowieniu zadania,
- koszt całego testu poniżej 0,50 USD.

## 7. Wdrożenie produkcyjne

1. Wykonać backup przed migracją.
2. Uruchomić GitHub Actions i test migracji PostgreSQL 16.
3. Wdrożyć kod bez klucza i potwierdzić, że ekstrakcja kończy się kontrolowanym statusem `missing_api_key`.
4. Właściciel wpisuje klucz OpenRouter bezpośrednio na VPS.
5. Uruchomić ograniczony benchmark modeli na fixture’ach.
6. Wybrać domyślny model tani i model awaryjny na podstawie jakości oraz kosztu.
7. Przetworzyć Nadarzyn, sprawdzić dowody i ręcznie zatwierdzić.
8. Przetworzyć WFOŚiGW, sprawdzić dowody i ręcznie zatwierdzić.
9. Osobno podjąć decyzję o publikacji każdego programu.
10. Sprawdzić `/api/programs`, monitoring, koszty i logi.
11. Wykonać backup po publikacji i pełny test odtworzenia.
12. Zaktualizować dokumentację i historię rozmowy w obu lokalizacjach na VPS.

## 8. Definition of Done

Sprint jest zakończony, gdy:

- schemat ekstrakcji jest wersjonowany i walidowany,
- każde kluczowe pole ma dowód albo jawny status `unknown`,
- budżety 1/5/8/10 USD są egzekwowane,
- każde wywołanie LLM jest rozliczalne,
- retry nie tworzy podwójnego kosztu ani wersji,
- dwa obecne snapshoty można obsłużyć przez CLI REVIEW,
- co najmniej Nadarzyn ma zatwierdzoną wersję ze statusem `closed`,
- publikacja wymaga osobnej jawnej komendy,
- co najmniej jeden zatwierdzony program jest widoczny w publicznym API,
- testy, lint, migracje i GitHub Actions przechodzą,
- backup przed i po migracji został sprawdzony przez pełne odtworzenie,
- dokumentacja jest identyczna lokalnie, w GitHubie i na VPS.

## 9. Dane potrzebne od właściciela

Nie są potrzebne na początku implementacji. Przed produkcyjnym benchmarkiem wymagane będą:

1. klucz OpenRouter wpisany samodzielnie na VPS,
2. potwierdzenie maksymalnego kosztu benchmarku 0,50 USD w ramach limitu 10 USD,
3. ręczna decyzja approve/reject dla wyników Nadarzyna i WFOŚiGW,
4. osobna decyzja, które zatwierdzone programy opublikować.

Klucza ani jego fragmentu nie należy przesyłać w rozmowie.

## 10. Następny sprint po tym etapie

Po udanej publikacji należy zbudować docelowy frontend publiczny i bezpieczny panel administratora z uwierzytelnieniem. Następnie można rozszerzyć crawler o harmonogram NFOŚiGW, kolejne programy oraz OCR.
