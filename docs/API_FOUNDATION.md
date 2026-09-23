# DotacjeAI — fundament API MVP-0

Aktualizacja: 2026-09-23.

## Zakres sprintu

Pierwszy sprint aplikacyjny dostarcza asynchroniczne FastAPI, SQLAlchemy 2, Alembic, strukturalny model domeny, publiczne endpointy odczytowe, mechanizm wyliczania statusu oraz GitHub Actions. Nie uruchamia jeszcze crawlera ani OpenRouter.

Stan produkcyjny: wdrożono 2026-09-23, API `0.2.0`, migracja `4167552a1c92`.

## Struktura

- aplikacja: `apps/api/app/`,
- konfiguracja: `app/core/config.py`,
- sesja asynchroniczna: `app/db/session.py`,
- modele: `app/models/domain.py`,
- kontrolowane wartości enum: `app/models/enums.py`,
- endpointy: `app/api/`,
- migracje: `apps/api/alembic/`,
- seed oficjalnych źródeł: `python -m app.cli.seed_sources`,
- testy: `apps/api/tests/`,
- CI: `.github/workflows/api-ci.yml`.

## Model domeny

Pierwsza migracja tworzy:

- `sources`,
- `source_snapshots`,
- `locations`,
- `programs`,
- `program_locations`,
- `program_property_types`,
- `program_beneficiary_types`,
- `program_investment_categories`,
- `program_versions`,
- `program_documents`,
- `document_versions`,
- `llm_runs`,
- `review_tasks`,
- `audit_log`.

Lokalizacja, typ nieruchomości, beneficjent, kategoria inwestycji, status oraz przyczyna REVIEW są danymi strukturalnymi. Brak informacji jest reprezentowany jawnie, a nie tekstem wymyślonym przez model.

## Publiczne endpointy

- `GET /api/health` — proces API i wersja,
- `GET /api/ready` — połączenie z PostgreSQL,
- `GET /api/programs` — opublikowane programy z paginacją,
- `GET /api/programs/{slug}` — publiczna karta programu.

Lista obsługuje filtry `status`, `location`, `category`, `property_type` oraz `beneficiary_type`. Nieopublikowane rekordy nigdy nie są zwracane przez publiczne endpointy.

## Status naboru

Funkcja domenowa rozpoznaje `open`, `planned`, `suspended`, `closed` i `unknown`. Oficjalne zamknięcie lub wstrzymanie ma pierwszeństwo, a przekroczona data końcowa proponuje `closed`. Wynik nadal podlega REVIEW przed pierwszą publikacją.

Test referencyjny Nadarzyna sprawdza termin 31.07.2026, status `closed`, maksymalną kwotę 6000 zł i poziom wsparcia 100%.

## Migracje i uruchomienie

Compose zawiera jednorazową usługę `migrate`. API uruchamia się dopiero po poprawnym `alembic upgrade head` oraz zdrowym Redisie. Migrację można wykonać ręcznie:

```bash
docker compose --env-file /opt/dotacje-ai/secrets/app.env -f infra/docker-compose.yml run --rm migrate
```

Seed źródeł jest idempotentny:

```bash
docker compose --env-file /opt/dotacje-ai/secrets/app.env -f infra/docker-compose.yml run --rm --no-deps api python -m app.cli.seed_sources
```

## Kontrola jakości

GitHub Actions wykonuje:

1. instalację zależności,
2. `ruff check`,
3. siedem testów pytest,
4. migrację czystej bazy PostgreSQL 16,
5. seed siedmiu oficjalnych źródeł,
6. `alembic check` wykrywający rozbieżność modeli i migracji.

Lokalnie sprawdzono również pełny cykl `upgrade -> downgrade -> upgrade` na SQLite oraz na izolowanym PostgreSQL 16 w Dockerze na VPS. Produkcyjna baza nie była używana podczas walidacji.

Pierwszy workflow GitHub Actions dla commita `b78e4ff` zakończył się statusem `success`. Po wdrożeniu produkcyjnym potwierdzono zdrowe kontenery, gotowość bazy, siedem zasianych źródeł, backup oraz pełne odtworzenie dumpa.

## Sekrety i budżet

Hasła bazy i klucz OpenRouter są typu `SecretStr`, więc ich reprezentacja jest maskowana. Klucz nie jest jeszcze ustawiany. Konfiguracja przewiduje miesięczny limit 10 USD oraz progi ostrzegawcze 5 i 8 USD.

## Następny sprint

1. Dodać crawler HTTP/PDF, trwałe pliki snapshotów i normalizację treści.
2. Zaimplementować hash, ETag, Last-Modified i diff.
3. Uruchomić WFOŚiGW Warszawa jako pierwsze źródło.
4. Dodać Nadarzyn jako test PDF, daty końcowej i konfliktu wersji.
5. Dopiero później podłączyć OpenRouter oraz panel REVIEW.
