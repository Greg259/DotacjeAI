# Status przygotowania serwera DotacjeAI

Ostatnia weryfikacja: 2026-09-24.

## Stan końcowy

- System działa stabilnie na jądrze `6.8.0-142-generic`; kontrolowany restart zakończył się poprawnie 2026-09-23.
- Strefa czasowa `Europe/Warsaw`; NTP aktywne.
- Swap 2 GB aktywny także po restarcie.
- Docker i Docker Compose v2 aktywne.
- Fail2ban aktywny z jail `sshd`.
- UFW aktywny; publicznie dozwolone tylko 22, 80 i 443.
- Konto `deploy` należy do grup `sudo` i `docker`.
- Logowanie `deploy` działa przy użyciu osobnego klucza RSA 4096 chronionego passphrase.
- Logowanie SSH hasłem oraz bezpośrednie logowanie `root` są wyłączone.
- Hasła `deploy` i `root` zostały ustawione poza dokumentacją; ujawnione wcześniej hasło `root` jest nieaktualne.
- Sekrety mają uprawnienia 700 dla katalogu i 600 dla pliku.
- Klucz OpenRouter jest tymczasowo skonfigurowany na VPS, ale został ujawniony w rozmowie i musi zostać niezwłocznie obrócony. Wartość nie znajduje się w Git ani dokumentacji.

## Kontenery po restarcie

- `caddy` - healthy
- `frontend` - healthy
- `api` - healthy
- `postgres` - healthy
- `redis` - healthy

PostgreSQL i Redis nie publikują portów na hoście. Z Internetu dostępne są wyłącznie Caddy oraz SSH.

## Testy

- `GET /health` zwraca `200 ok`.
- `GET /api/health` zwraca poprawny JSON API.
- Kontenery uruchamiają się automatycznie po restarcie VPS.
- Docker, fail2ban, unattended-upgrades i AppArmor są aktywne.
- Brak nieudanych jednostek systemd.

## Domena i HTTPS

- Domena produkcyjna: `dotacjeai.eu`.
- Rekord A domeny głównej wskazuje na VPS.
- Caddy skonfigurowano do automatycznego HTTPS.
- `https://www.dotacjeai.eu` ma własny certyfikat i przekierowuje na `https://dotacjeai.eu`.

## Otwarte zadania

1. Dodać zewnętrzny backup i alarmy przed rozpoczęciem bety.
2. Skonfigurować zasady pracy z repozytorium: ochrona `main`, pull requesty i CI.
3. Zastąpić techniczny frontend docelową aplikacją Next.js oraz dodać migracje bazy.
4. Zaimplementować pierwsze źródła opisane w `SOURCE_CATALOG.md`.
5. Ustawić `OPENROUTER_API_KEY` dopiero przed wdrożeniem i testami integracji LLM; limit miesięczny wynosi 10 USD.

## Fundament API przygotowany 2026-09-23

- FastAPI z konfiguracją środowiskową i logami JSON,
- SQLAlchemy 2 z sesją asynchroniczną,
- pierwsza migracja Alembic dla domeny MVP-0,
- strukturalne filtry lokalizacji, nieruchomości, beneficjentów i inwestycji,
- tabele wersji, dokumentów, wywołań LLM, REVIEW i audytu,
- publiczne endpointy zdrowia, gotowości, listy i szczegółów programu,
- idempotentny seed siedmiu oficjalnych źródeł i lokalizacji pilotażowych,
- GitHub Actions dla lint, testów, migracji i seeda,
- 7 testów lokalnych zakończonych poprawnie,
- pełny cykl migracji zweryfikowany na odseparowanym PostgreSQL 16 na VPS.

Fundament został wdrożony produkcyjnie. Po sprincie crawlera aktywna migracja wynosiła `a8d2f6c4b901`, a API miało wersję `0.3.0`. Aktualny stan po Sprincie 03 opisano poniżej.

Po migracji wykonano snapshot Restic `0e57cdc7`. Kontrola repozytorium, SHA-256 i pełny import do tymczasowej bazy zakończyły się poprawnie. Monitoring po wdrożeniu zwrócił `OK`.

## Crawler produkcyjny wdrożony 2026-09-23

- crawler HTML/PDF działa jako jednorazowe zadanie Docker bez uprawnień root,
- obsługuje timeout, trzy próby, limit 25 MiB, redirecty, ETag i Last-Modified,
- zapisuje surowy plik, dwa hashe SHA-256, tekst znormalizowany i opcjonalny diff,
- pierwsza zmiana tworzy zadanie `NEW_PROGRAM`, kolejna `SOURCE_CHANGED`,
- błędy są zapisywane przy źródle i nie wyłączają weryfikacji TLS,
- cron użytkownika `deploy` uruchamia dwa priorytetowe źródła co sześć godzin,
- Nadarzyn: PDF 360899 B, kolejne sprawdzenie zwróciło HTTP 304,
- WFOŚiGW: HTML 231516 B, powtórne sprawdzenie miało identyczne hashe,
- baza zawiera cztery sprawdzenia, dwa snapshoty oznaczone jako zmiana i dwa oczekujące zadania REVIEW,
- oba źródła mają wyczyszczony stan ostatniego błędu,
- 11 testów lokalnych oraz GitHub Actions zakończyły się sukcesem.

Serwer WFOŚiGW nie wysyła kompletnego łańcucha TLS. Dodano publiczny certyfikat pośredni wskazany w AIA certyfikatu serwera. Nadal sprawdzane są hostname, podpis, ważność i zaufany root; weryfikacja TLS nie została wyłączona.

Backup po wdrożeniu ma identyfikator `81688635`. Restic nie wykrył błędów, odtworzył 23 pliki i katalogi, zweryfikował SHA-256 dumpa oraz wykonał pełny import do bazy tymczasowej.

## Zatwierdzony zakres MVP-0

- portal publiczny bez logowania,
- pierwszy obszar: Mazowieckie, ze szczególnym uwzględnieniem Nadarzyna,
- pierwsze źródło: WFOŚiGW Warszawa / Czyste Powietrze,
- drugi test: Gmina Nadarzyn / wymiana źródła ciepła,
- crawler stron i PDF, wersjonowanie, diff, AI, REVIEW i publikacja,
- filtry lokalizacji, nieruchomości, beneficjenta, inwestycji, statusu, terminu i poziomu wsparcia,
- bez kont użytkowników, matchingu, poczty i prywatnych dokumentów do czasu MVP-1.

## Repozytorium i dokumentacja

- Repozytorium GitHub: `Greg259/DotacjeAI`.
- Kod infrastruktury i dokumentacja znajdują się na gałęzi `main`.
- Sekrety i pliki `.env` nie są wersjonowane.
- Kopia robocza repozytorium znajduje się w `D:\Codex\DotacjeAI`.
- `D:\Codex\DotacjeAI` jest jedynym aktywnym lokalnym źródłem prawdy.
- Dawny `D:\Codex\ProjektDotacje` jest junctionem do aktywnego repozytorium; jego stan sprzed konsolidacji zachowano w `D:\Codex\archive\ProjektDotacje-pre-git-20260923`.
- Dokumentacja jest również synchronizowana do `/home/deploy/Codex/ProjektDotacje` na VPS.

## Weryfikacja po aktualizacji z 2026-09-23

- aktywne jądro: `6.8.0-142-generic`,
- ponowny restart: niewymagany,
- usługi `ssh`, `docker` i `fail2ban`: aktywne i włączone przy starcie,
- kontenery `caddy`, `frontend`, `api`, `postgres` i `redis`: `healthy`,
- `https://dotacjeai.eu/health`: `ok`,
- `https://dotacjeai.eu/api/health`: poprawna odpowiedź JSON,
- dysk: 23% zajęte, około 73 GB dostępne,
- pamięć: około 7,1 GiB dostępne, swap 2 GiB,
- `restic`: wersja `0.16.4`; lokalne zaszyfrowane repozytorium działa.
- `/opt/dotacje-ai/backups`: właściciel `deploy:deploy`, tryb `0700`, zapis potwierdzony.

## Backup i monitoring lokalny z 2026-09-23

- pierwszy poprawnie zweryfikowany snapshot: `858176df`,
- dump PostgreSQL przechodzi kontrolę formatu i SHA-256,
- pełny import do tymczasowej bazy zakończył się poprawnie,
- kontrola Restic nie wykryła błędów,
- retencja grupuje snapshoty po hoście i tagu: 7 dziennych, 5 tygodniowych, 12 miesięcznych,
- backup uruchamia się codziennie o 02:30,
- monitoring uruchamia się co 5 minut,
- ręczny test monitoringu: `OK` dla HTTPS, API, pięciu kontenerów, dysku i świeżości backupu.

## Sprint 03 — ekstrakcja i prywatny REVIEW (2026-09-24)

- wdrożona migracja `c4e7b9a210f3` oraz API `0.4.0`,
- dodano wersjonowany `ExtractionCandidate`, dowody pól, ostrzeżenia i `ExtractionJob`,
- klient OpenRouter wymusza ścisły JSON Schema, walidację Pydantic i `require_parameters=true`,
- modele produkcyjne: `openai/gpt-6-luna` oraz awaryjny `openai/gpt-6-luna-pro`,
- limity kosztów pozostają ustawione na 1 USD dziennie oraz 5/8/10 USD miesięcznie,
- trzy zadania mają status `ready_for_review`, a trzy zadania REVIEW nadal są `pending`,
- Nadarzyn: `closed`, termin 31.07.2026, maksymalnie 6000 PLN, wsparcie 100%,
- dwa snapshoty WFOŚiGW: `open`; wymagają ręcznego porównania jako `new_program` i `source_changed`,
- 8 rozliczonych odpowiedzi wykorzystało 255521 tokenów wejścia i 22984 wyjścia; łączny koszt wyniósł 0,026836 USD,
- powtórne uruchomienie potwierdziło idempotencję i nie zwiększyło kosztu,
- 23 testy lokalne, lint oraz GitHub Actions dla commita `d2ba81e` zakończyły się sukcesem,
- publiczne `/api/programs` pozostaje puste; nic nie zostało zatwierdzone ani opublikowane,
- backup po wdrożeniu: `8fc846f5`; Restic, SHA-256 i pełny import do tymczasowej bazy zakończyły się poprawnie.

Najbliższa obowiązkowa czynność bezpieczeństwa: unieważnić ujawniony klucz OpenRouter, utworzyć nowy i podmienić go bezpośrednio w `/opt/dotacje-ai/secrets/app.env`, bez przesyłania przez rozmowę.

## Sprint 04 — portal publiczny rozpoczęty 2026-09-24

- API 0.5.0 rozszerza kartę programu o oficjalne dokumenty i historię zatwierdzonych wersji,
- endpoint szczegółów nie ujawnia wersji roboczych ani nieopublikowanych programów,
- techniczny placeholder frontendu zastąpiono Next.js 16.3.6 z App Routerem i TypeScript,
- wdrożono strony `/`, `/dotacje`, `/dotacje/[slug]`, `/region/[slug]`, `/gmina/[slug]` i `/kategoria/[slug]`,
- filtry działają przez parametry URL i są renderowane po stronie serwera,
- dodano pusty wynik, błąd API, 404, responsywny interfejs, healthcheck, robots i sitemap,
- obraz produkcyjny wykorzystuje Next.js `standalone`, Node.js 22 i konto bez uprawnień root,
- workflow CI obejmuje teraz API oraz typecheck i produkcyjny build frontendu,
- lokalna walidacja: Ruff bez błędów, 23/23 testów API, typecheck i build Next.js zakończone sukcesem,
- lokalny Docker Desktop nie był uruchomiony; właściwy build obrazu i test Compose zostaną wykonane na VPS,
- niczego nie zatwierdzono ani nie opublikowano; wymagana jest osobna decyzja właściciela,
- na życzenie właściciela rotacja ujawnionego klucza pozostaje ostatnim krokiem; do tego czasu nie wykonujemy nowych wywołań LLM.
