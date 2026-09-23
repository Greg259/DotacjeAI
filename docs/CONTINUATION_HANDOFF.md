# DotacjeAI — przekazanie kontekstu do kolejnej sesji

Aktualizacja: 2026-09-23.

## Punkt startowy

Infrastruktura do rozpoczęcia właściwego MVP jest gotowa. Serwer działa na jądrze `6.8.0-142-generic`, dostęp administracyjny odbywa się kluczem SSH przez użytkownika `deploy`, a logowanie hasłem i bezpośrednie logowanie `root` są wyłączone.

Produkcja działa pod `https://dotacjeai.eu`. Kontenery `caddy`, `frontend`, `api`, `postgres` i `redis` są zdrowe. PostgreSQL oraz Redis nie mają publicznych portów.

## Repozytorium i dokumentacja

- główne repozytorium: `git@github.com:Greg259/DotacjeAI.git`,
- lokalne źródło prawdy: `D:\Codex\DotacjeAI`,
- `D:\Codex\ProjektDotacje` jest junctionem do głównego repozytorium,
- aplikacja na VPS: `/opt/dotacje-ai/app`,
- dokumentacja na VPS: `/home/deploy/Codex/ProjektDotacje`,
- bazowy commit kompletnego backupu i monitoringu: `d6790f0`.

Nie wolno commitować plików `.env`, haseł, kluczy SSH, klucza OpenRouter ani hasła Restic.

## Backup i monitoring

- Restic `0.16.4`,
- zaszyfrowane repozytorium: `/opt/dotacje-ai/backups/restic-repository`,
- backup PostgreSQL i katalogów danych: codziennie o 02:30,
- monitoring HTTPS, API, pięciu kontenerów, dysku i świeżości backupu: co 5 minut,
- pełny test odtworzenia do tymczasowej bazy: zakończony poprawnie,
- retencja: 7 dziennych, 5 tygodniowych i 12 miesięcznych,
- logi: `/opt/dotacje-ai/backups/logs/`.

Backup znajduje się na tym samym VPS. Zewnętrzną kopię i zewnętrzne alarmy świadomie odłożono, ale są wymagane przed uruchomieniem bety.

## Najbliższa kolejność prac

1. Dodać GitHub Actions dla testów i kontroli jakości.
2. Ustalić ochronę gałęzi `main` i pracę przez pull requesty.
3. Zastąpić techniczny frontend właściwą aplikacją.
4. Rozbudować FastAPI o konfigurację, logowanie i obsługę błędów.
5. Dodać SQLAlchemy i Alembic.
6. Utworzyć pierwsze migracje domeny DotacjeAI.
7. Dodać worker i scheduler wykorzystujące Redis.
8. Zbudować pierwszy przepływ: pobranie oficjalnego źródła, hash, wersja, diff, ekstrakcja AI, review i publikacja.

Fundament API, modele SQLAlchemy, pierwsza migracja Alembic, publiczne endpointy oraz CI zostały przygotowane i zweryfikowane. Szczegóły znajdują się w `API_FOUNDATION.md`. Najbliższy kodowy krok to crawler HTTP/PDF i trwałe snapshoty, nie ponowne tworzenie modeli.

## Decyzje produktu MVP-0

- portal publiczny działa bez logowania,
- konta użytkowników i prywatne dokumenty przechodzą do MVP-1,
- pierwszy crawler: WFOŚiGW Warszawa / Czyste Powietrze,
- drugi crawler: Gmina Nadarzyn / wymiana źródła ciepła,
- miesięczny limit OpenRouter: 10 USD, alerty przy 5 i 8 USD,
- zatwierdzone wymagania: `MVP0_PRODUCT_REQUIREMENTS.md`,
- zweryfikowane adresy startowe: `SOURCE_CATALOG.md`.

Pełny status znajduje się w `IMPLEMENTATION_STATUS.md`, kolejność etapów w `NEXT_STEPS_PLAN.md`, a historia decyzji w `CONVERSATION_LOG.md`.
