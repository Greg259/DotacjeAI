# DotacjeAI - infrastruktura MVP

Ten katalog zawiera minimalny, produkcyjnie ukierunkowany szkielet środowiska DotacjeAI.

## Uruchomione komponenty

- Caddy - jedyny publiczny punkt wejścia HTTP/HTTPS.
- Frontend - tymczasowy serwer aplikacji, do zastąpienia docelowym Next.js.
- API - minimalne FastAPI z endpointem zdrowia.
- PostgreSQL - główna baza danych, bez portu publicznego.
- Redis - kolejka/cache, bez portu publicznego.

## Endpointy

- `/health` - healthcheck reverse proxy.
- `/api/health` - healthcheck API.
- `/` - strona techniczna frontendu.

## Lokalizacja produkcyjna

- aplikacja: `/opt/dotacje-ai/app`
- dane aplikacyjne: `/opt/dotacje-ai/data`
- sekrety: `/opt/dotacje-ai/secrets/app.env`
- backupy: `/opt/dotacje-ai/backups`
- dokumentacja: `/home/deploy/Codex/ProjektDotacje`

## Repozytorium robocze

Jedynym aktywnym repozytorium na komputerze administratora jest:

`D:\Codex\DotacjeAI`

Historyczna ścieżka `D:\Codex\ProjektDotacje` jest junctionem prowadzącym do tego repozytorium. Archiwum stanu sprzed konsolidacji znajduje się w `D:\Codex\archive\ProjektDotacje-pre-git-20260923` i nie służy do dalszej pracy.

Prawdziwy plik `app.env` nigdy nie może trafić do repozytorium ani dokumentacji.

## Dokumentacja

- `docs/TECHNICAL_SERVER_DOCUMENTATION.md` - aktualny stan techniczny VPS.
- `docs/CONVERSATION_LOG.md` - zapis rozmowy, decyzji i wykonanych działań bez sekretów.
- `docs/IMPLEMENTATION_STATUS.md` - raport z przygotowania środowiska.
- `docs/OPENROUTER_COST_OPTIMIZATION.md` - warianty modeli i optymalizacja kosztów.
- `docs/OPENROUTER_MODELS.md` - pierwotna rekomendacja modeli.
- `docs/NEXT_STEPS_PLAN.md` - kolejność dalszej implementacji.
- `docs/SERVER_SETUP.md` - operacyjna instrukcja środowiska.
- `docs/SSH_HARDENING_RUNBOOK.md` - wykonana procedura utwardzenia SSH.
- `docs/ACCESS_ONBOARDING.md` - dostęp z kolejnego komputera i onboarding operatorów.
- `docs/BACKUP_AND_MONITORING.md` - szyfrowany backup poza VPS, test odtworzenia i monitoring.
