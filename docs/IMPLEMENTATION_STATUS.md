# Status przygotowania serwera DotacjeAI

Ostatnia weryfikacja: 2026-09-23.

## Stan końcowy

- System działa stabilnie; dostępna jest aktualizacja jądra z `6.8.0-139` do `6.8.0-142`, wymagająca instalacji i późniejszego restartu.
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

1. Zainstalować pakiety jądra `6.8.0-142`, wykonać kontrolowany restart i ponownie sprawdzić usługi.
2. Wybrać zewnętrzny storage i uruchomić szyfrowany backup z testem odtworzenia; katalog backupów jest obecnie pusty.
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
- Dokumentacja jest również synchronizowana do `/home/deploy/Codex/ProjektDotacje` na VPS.
