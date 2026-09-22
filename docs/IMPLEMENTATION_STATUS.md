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
2. Ustawić `OPENROUTER_API_KEY` w `/opt/dotacje-ai/secrets/app.env`.
3. Wybrać dostawcę e-maili oraz zewnętrznego backupu.
4. Zastąpić techniczny frontend docelową aplikacją Next.js.
