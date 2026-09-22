# Status przygotowania serwera DotacjeAI

Weryfikacja: 2026-09-22 po kontrolowanym restarcie.

## Stan końcowy

- System zaktualizowany; brak oczekujących aktualizacji.
- Strefa czasowa `Europe/Warsaw`; NTP aktywne.
- Swap 2 GB aktywny także po restarcie.
- Docker i Docker Compose v2 aktywne.
- Fail2ban aktywny z jail `sshd`.
- UFW aktywny; publicznie dozwolone tylko 22, 80 i 443.
- Konto `deploy` należy do grup `sudo` i `docker`.
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

1. Dodać klucz SSH użytkownika `deploy`, a następnie wyłączyć hasło i logowanie `root`.
2. Zmienić ujawnione podczas konfiguracji hasło `root`.
3. Wybrać zewnętrzny storage i uruchomić szyfrowany backup z testem odtworzenia.
4. Dodać monitoring dostępności, miejsca na dysku i stanu kontenerów.
5. Skonfigurować zasady pracy z repozytorium: ochrona `main`, pull requesty i CI.
6. Zastąpić techniczny frontend docelową aplikacją Next.js oraz dodać migracje bazy.
7. Wybrać 3-5 oficjalnych źródeł pilotażowych.
8. Ustawić `OPENROUTER_API_KEY` dopiero przed wdrożeniem i testami integracji LLM.

## Repozytorium i dokumentacja

- Repozytorium GitHub: `Greg259/DotacjeAI`.
- Kod infrastruktury i dokumentacja znajdują się na gałęzi `main`.
- Sekrety i pliki `.env` nie są wersjonowane.
- Kopia robocza repozytorium znajduje się w `D:\Codex\DotacjeAI`.
- Dokumentacja jest również synchronizowana do `/home/deploy/Codex/ProjektDotacje` na VPS.
