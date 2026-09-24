# Ekstrakcja i REVIEW — instrukcja operatorska

## Stan wdrożenia

Moduł ekstrakcji może działać bez klucza OpenRouter. Najpierw wykonuje reguły deterministyczne, zapisuje `ExtractionJob`, a jeżeli potrzebuje LLM i klucz nie jest ustawiony, kończy zadanie stanem `awaiting_api_key`. Nie wykonuje połączenia zewnętrznego i nie generuje kosztu.

## Uruchomienie ekstrakcji

```bash
ssh deploy@185.69.52.106
cd /opt/dotacje-ai/app
./server/run_extraction.sh
```

Możliwe stany:

- `ready_for_review` — kandydat jest gotowy do kontroli,
- `awaiting_api_key` — potrzebne jest uzupełnienie przez OpenRouter,
- `blocked_by_budget` — osiągnięto limit kosztów,
- `failed` — walidacja lub połączenie zakończyło się błędem,
- `rules_ready` — wykonano reguły, ale zadanie nie przeszło jeszcze całego procesu.

Ponowne uruchomienie jest idempotentne: nie tworzy drugiego zadania dla tego samego snapshotu i wersji promptu.

## Kolejka REVIEW

Lista:

```bash
./server/review_cli.sh list
```

Szczegóły:

```bash
./server/review_cli.sh show REVIEW_ID
```

Zatwierdzenie tworzy wersję programu, ale jej nie publikuje:

```bash
./server/review_cli.sh approve REVIEW_ID
```

Odrzucenie zawsze wymaga uzasadnienia:

```bash
./server/review_cli.sh reject REVIEW_ID --note "Powód odrzucenia"
```

Korekta kandydata jest przekazywana przez standardowe wejście i ponownie walidowana:

```bash
./server/review_cli.sh replace REVIEW_ID < poprawiony-kandydat.json
```

Publikacja jest osobną, jawną operacją:

```bash
./server/review_cli.sh publish PROGRAM_ID
```

## Zasady bezpieczeństwa

- nie uruchamiać `approve` bez sprawdzenia cytatów i oficjalnego źródła,
- nie uruchamiać `publish` tylko dlatego, że ekstrakcja zakończyła się technicznie poprawnie,
- nie wklejać klucza OpenRouter do polecenia, pliku JSON ani rozmowy,
- klucz wpisuje właściciel wyłącznie do `/opt/dotacje-ai/secrets/app.env`,
- CLI działa wewnątrz sieci backendowej i nie jest udostępnione przez HTTPS,
- wszystkie approve, reject, replace i publish zapisują `audit_log`,
- pełne prompty i klucz API nie są zapisywane w logach.

## Limity kosztów

- limit dzienny: 1 USD,
- ostrzeżenie miesięczne: 5 USD,
- poziom krytyczny: 8 USD,
- twardy limit miesięczny: 10 USD,
- pierwszy benchmark produkcyjny: maksymalnie 0,50 USD.

Przed każdym wywołaniem system sumuje zapisane koszty z bieżącego dnia i miesiąca. Poprawna oraz odrzucona przez walidację odpowiedź zapisuje tokeny i koszt zwrócony przez OpenRouter.

## Publikacja

Publiczne API pokazuje wyłącznie rekordy z `is_published=true`. Zatwierdzenie ustawia dane programu i tworzy `ProgramVersion`; publikacja ustawia `published_at` dopiero po osobnym poleceniu. Dzięki temu wynik LLM nigdy nie trafia automatycznie do portalu.

## Stan produkcyjny 2026-09-24

- 3 zadania ekstrakcji: `ready_for_review`,
- 3 zadania REVIEW: `pending`,
- koszt dotychczasowego benchmarku: 0,026836 USD,
- publiczne programy: 0,
- domyślny model: `openai/gpt-6-luna`,
- model naprawczy: `openai/gpt-6-luna-pro`.

Klucz użyty w pierwszym benchmarku został ujawniony w rozmowie. Jest tymczasowo aktywny wyłącznie w chronionym pliku serwera, ale należy go unieważnić i podmienić przed dalszymi wywołaniami. Nowego klucza nie wolno przesyłać w rozmowie ani umieszczać w poleceniu zapisującym się w historii powłoki.
