# DotacjeAI - plan kolejnych kroków

Aktualizacja: 2026-09-22.

## Cel najbliższego etapu

Najpierw należy uruchomić jeden kompletny i audytowalny przepływ:

```text
oficjalne źródło
-> pobranie i hash
-> wykrycie zmiany
-> zapis wersji i dokumentu
-> ekstrakcja AI
-> REVIEW administratora
-> publikacja programu
-> alert e-mail
```

## Etap 1 - domknięcie infrastruktury

Priorytet: natychmiast po podjęciu decyzji o domenie i dostępie.

1. [x] Skierować domenę `dotacjeai.eu` na VPS.
2. [x] Uruchomić automatyczny certyfikat HTTPS dla domeny głównej.
3. [x] Potwierdzić propagację i certyfikat dla `www.dotacjeai.eu`.
4. [ ] Dodać klucz SSH do konta `deploy` i przetestować osobną sesję.
5. [ ] Wyłączyć logowanie roota oraz logowanie hasłem dopiero po teście klucza.
6. [ ] Zmienić obecne hasło roota.
7. [ ] Wybrać zewnętrzny storage backupów.
8. [ ] Wdrożyć codzienny `pg_dump`, backup dokumentów, szyfrowanie, retencję i test odtworzenia.
9. [ ] Dodać monitoring dostępności, dysku i błędów kontenerów.

Definition of Done:

- HTTPS działa,
- logowanie kluczem działa,
- backup można odtworzyć,
- alarm testowy dociera do administratora.

## Etap 2 - fundament aplikacji

1. Utworzyć repozytorium Git i zasady branch/PR.
2. Zastąpić placeholder frontendu minimalnym Next.js.
3. Rozbudować FastAPI o konfigurację, logowanie JSON i obsługę błędów.
4. Dodać SQLAlchemy oraz Alembic.
5. Utworzyć pierwsze migracje: `users`, `sources`, `source_snapshots`, `programs`, `program_versions`, `program_documents`, `document_versions`, `llm_runs`, `audit_log`.
6. Dodać worker i scheduler korzystające z Redis.
7. Dodać testy, lint i kontrolę migracji w CI.

Definition of Done:

- czysta baza przechodzi wszystkie migracje,
- API i worker mają healthchecki,
- testy i lint przechodzą,
- README pozwala uruchomić środowisko od zera.

## Etap 3 - monitoring bez AI

1. Wybrać 3-5 oficjalnych źródeł pilotażowych.
2. Zbudować adapter HTTP z limitami, timeoutami, retry i identyfikacją aplikacji.
3. Obsłużyć ETag, Last-Modified, status HTTP i SHA-256.
4. Normalizować HTML przed hashowaniem.
5. Zapisywać niezmienne snapshoty i wersje PDF.
6. Generować diff tekstowy i listę nowych linków.
7. Wprowadzić idempotency key dla każdego zadania.

Definition of Done:

- brak zmiany kończy zadanie bez LLM,
- zmiana tworzy nową wersję i diff,
- ponowienie zadania nie tworzy duplikatu,
- PDF można powiązać z URL, datą i SHA-256.

## Etap 4 - OpenRouter i test modeli

1. Utworzyć klucz OpenRouter z limitem wydatków.
2. Zapisać klucz wyłącznie w `/opt/dotacje-ai/secrets/app.env`.
3. Zaimplementować `LLMProvider` dla OpenRouter.
4. Wymusić JSON Schema i walidację Pydantic.
5. Wprowadzić routing: tani model -> walidator -> mocny model.
6. Zapisywać model, provider, prompt version, tokeny, koszt, latency i status.
7. Przygotować zestaw 20-30 regulaminów z ręcznie sprawdzonym wynikiem.
8. Porównać DeepSeek V4 Flash, GPT-5 Nano i GPT-5.6 Luna Pro.
9. Ustawić dzienny i miesięczny limit kosztów oraz circuit breaker.

Definition of Done:

- każde wywołanie jest rozliczalne,
- niepoprawny JSON nie jest publikowany,
- model tani ma zmierzoną jakość,
- niska pewność zawsze tworzy zadanie REVIEW.

## Etap 5 - panel administratora

1. Lista źródeł i stan ostatniego pobrania.
2. Podgląd wersji i diff.
3. Kolejka wyników AI do zatwierdzenia.
4. Akcje approve, reject i edit.
5. Widoczność źródła każdego pola.
6. Podgląd kosztów LLM i błędów workerów.

## Etap 6 - portal publiczny

1. Landing i lista dotacji.
2. Filtry po regionie, beneficjencie, kategorii i statusie.
3. Karta programu ze źródłami i datą weryfikacji.
4. Historia zmian i dokumentów.
5. Sitemap, canonical, robots.txt i podstawowe SEO.

## Etap 7 - użytkownicy i matching

1. Rejestracja, weryfikacja e-mail i reset hasła.
2. Role `user`, `editor`, `admin`.
3. Strukturalne profile beneficjenta i inwestycji.
4. Silnik wyników: spełnione, niespełnione, nieustalone.
5. Subskrypcje programów.
6. Izolacja danych użytkowników i testy autoryzacji.

## Etap 8 - alerty i beta

1. Dostawca e-maili transakcyjnych.
2. Deduplikacja alertów.
3. Test end-to-end: zmiana -> AI -> review -> publikacja -> matching -> e-mail.
4. Rate limiting, testy bezpieczeństwa i polityki retencji.
5. Regulamin, polityka prywatności i analiza RODO.
6. Stabilizacja monitoringu przez kilka dni przed zaproszeniem użytkowników.

## Decyzje potrzebne od właściciela

1. Domena projektu.
2. Repozytorium Git i sposób dostępu.
3. Pierwsze 3-5 źródeł dotacji.
4. Dostawca poczty transakcyjnej.
5. Dostawca zewnętrznego backupu.
6. Miesięczny limit OpenRouter.
7. Czy prywatne dokumenty użytkowników wchodzą do pierwszej bety, czy do etapu po uruchomieniu portalu.

## Rekomendowana najbliższa kolejność

1. Klucz SSH i zamknięcie logowania hasłem.
2. Backup poza VPS.
3. Repozytorium i migracje bazy.
4. Trzy realne źródła i monitoring deterministyczny.
5. Dopiero potem klucz OpenRouter i porównanie modeli.
