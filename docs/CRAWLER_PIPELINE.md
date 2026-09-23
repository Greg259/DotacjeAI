# Crawler źródeł DotacjeAI

## Cel sprintu

Crawler pobiera oficjalne strony HTML i dokumenty PDF bez użycia LLM. Każde pobranie zapisuje metadane techniczne, a zmiana treści tworzy zadanie w kolejce `REVIEW`. Publikacja programu nadal wymaga późniejszej ekstrakcji i zatwierdzenia.

## Przepływ

1. Odczyt aktywnego źródła z tabeli `sources`.
2. Wysłanie warunkowego żądania HTTP z `If-None-Match` i `If-Modified-Since`, jeżeli poprzedni snapshot zawiera ETag lub Last-Modified.
3. Maksymalnie trzy próby dla błędów transportu, HTTP 429 i przejściowych błędów 5xx.
4. Kontrola limitu odpowiedzi 25 MiB.
5. Zapis niezmienionego surowego HTML/PDF w `/opt/dotacje-ai/data/documents/sources`.
6. Normalizacja widocznego tekstu HTML wraz z linkami albo ekstrakcja tekstu z PDF.
7. Obliczenie SHA-256 surowego pliku i SHA-256 tekstu znormalizowanego.
8. Porównanie hasha tekstu z poprzednim snapshotem.
9. Zapis unified diff dla rzeczywistej zmiany treści.
10. Utworzenie zadania `NEW_PROGRAM` dla pierwszego pobrania albo `SOURCE_CHANGED` dla kolejnej zmiany.

WFOŚiGW nie wysyła obecnie kompletnego łańcucha TLS. W repozytorium znajduje się wyłącznie publiczny certyfikat pośredni `home pl OV TLS G2 R35 CA`, pobrany z adresu AIA wskazanego przez certyfikat serwera. Crawler dodaje go do standardowego magazynu CA, ale nadal rygorystycznie sprawdza nazwę hosta, podpis, terminy ważności i zaufany root. Weryfikacja TLS nie jest wyłączana.

Odpowiedź `304 Not Modified` również jest zapisywana jako sprawdzenie, ale nie tworzy nowego zadania REVIEW ani kopii pliku.

## Dane audytowe

Tabela `source_snapshots` przechowuje:

- źródło i poprzedni snapshot,
- czas pobrania, końcowy URL i kod HTTP,
- Content-Type, ETag i Last-Modified,
- SHA-256 surowego pliku oraz tekstu znormalizowanego,
- rozmiar odpowiedzi,
- względną ścieżkę surowego pliku i opcjonalnego diffu,
- znormalizowany tekst i flagę zmiany.

Tabela `sources` przechowuje ostatnie sprawdzenie, ostatni sukces oraz czas i treść ostatniego błędu. Komunikat błędu jest ograniczony do 4000 znaków i nie zawiera sekretów.

## Uruchomienie na VPS

Domyślnie uruchamiane są dwa priorytetowe źródła: WFOŚiGW Warszawa oraz regulamin Gminy Nadarzyn.

```bash
/opt/dotacje-ai/app/server/run_crawler.sh
```

Jedno wskazane źródło:

```bash
/opt/dotacje-ai/app/server/run_crawler.sh --slug wfosigw-warszawa-czyste-powietrze
```

Wszystkie aktywne źródła:

```bash
/opt/dotacje-ai/app/server/run_crawler.sh --all
```

Kod zakończenia `0` oznacza sukces wszystkich źródeł, `1` co najmniej jeden błąd pobierania, a `2` nieznany slug. Wynik każdego źródła jest pojedynczym obiektem JSON, bez sekretów.

## Harmonogram i backup

Cron użytkownika `deploy` uruchamia priorytetowy crawler co sześć godzin, 15 minut po pełnej godzinie. Log trafia do `/opt/dotacje-ai/backups/logs/crawler.log`.

Snapshoty są częścią istniejącego drzewa `/opt/dotacje-ai/data/documents`, dlatego obejmuje je codzienny backup Restic. Baza przechowująca metadane i kolejkę REVIEW jest objęta istniejącym `pg_dump`.

## Ograniczenia bieżącego sprintu

- skanowane PDF-y bez warstwy tekstowej nie mają jeszcze OCR,
- crawler nie uruchamia OpenRouter,
- kolejka REVIEW nie ma jeszcze panelu administracyjnego,
- wykryta zmiana nie jest automatycznie publikowana,
- przed betą nadal wymagany jest backup poza VPS i zewnętrzny alert awarii.
