# Status przygotowania serwera DotacjeAI

Ostatnia weryfikacja: 2026-09-23.

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
- Klucz OpenRouter pozostaje pusty i gotowy do późniejszego ustawienia.

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

Fundament został wdrożony produkcyjnie. Aktywna migracja to `4167552a1c92`, API ma wersję `0.2.0`, w tabeli `sources` znajduje się siedem oficjalnych źródeł, a publiczna lista pozostaje pusta do czasu zatwierdzenia pierwszego programu. OpenRouter i crawler nie są jeszcze uruchomione.

Po migracji wykonano snapshot Restic `0e57cdc7`. Kontrola repozytorium, SHA-256 i pełny import do tymczasowej bazy zakończyły się poprawnie. Monitoring po wdrożeniu zwrócił `OK`.

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
