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

1. Dokończyć instalację `restic` (aktualizacja systemu i jądra została wykonana, lecz pakiet Restic nie został zainstalowany przez poprzedni łańcuch poleceń).
2. Utworzyć prywatny bucket Cloudflare R2, wprowadzić dane dostępowe bezpośrednio na VPS i uruchomić szyfrowany backup z testem odtworzenia.
3. Dodać monitoring dostępności, miejsca na dysku i stanu kontenerów.
4. Skonfigurować zasady pracy z repozytorium: ochrona `main`, pull requesty i CI.
5. Zastąpić techniczny frontend docelową aplikacją Next.js oraz dodać migracje bazy.
6. Wybrać 3-5 oficjalnych źródeł pilotażowych.
7. Ustawić `OPENROUTER_API_KEY` dopiero przed wdrożeniem i testami integracji LLM.

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
- `restic`: nadal wymaga instalacji.
