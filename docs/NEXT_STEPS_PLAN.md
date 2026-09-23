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
4. [x] Dodać klucz SSH do konta `deploy` i przetestować osobną sesję.
5. [x] Wyłączyć logowanie roota oraz logowanie hasłem po teście klucza.
6. [x] Zmienić ujawnione hasło roota.
7. [ ] Wybrać zewnętrzny storage backupów.
8. [ ] Wdrożyć codzienny `pg_dump`, backup dokumentów, szyfrowanie, retencję i test odtworzenia.
9. [ ] Dodać monitoring dostępności, dysku i błędów kontenerów.

Definition of Done:

- HTTPS działa,
- logowanie kluczem działa,
- backup można odtworzyć,
- alarm testowy dociera do administratora.

## Etap 2 - fundament aplikacji

1. [x] Utworzyć repozytorium GitHub i skonfigurować dostęp przez SSH.
2. [x] Wysłać kod infrastruktury i dokumentację bez sekretów na `main`.
3. [ ] Włączyć ochronę `main`, pracę przez pull request i podstawowe reguły przeglądu.
4. [ ] Zastąpić placeholder frontendu minimalnym Next.js.
5. [ ] Rozbudować FastAPI o konfigurację, logowanie JSON i obsługę błędów.
6. [ ] Dodać SQLAlchemy oraz Alembic.
7. [ ] Utworzyć pierwsze migracje: `users`, `sources`, `source_snapshots`, `programs`, `program_versions`, `program_documents`, `document_versions`, `llm_runs`, `audit_log`.
8. [ ] Dodać worker i scheduler korzystające z Redis.
9. [ ] Dodać testy, lint i kontrolę migracji w GitHub Actions.

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

1. [x] Domena projektu: `dotacjeai.eu`.
2. [x] Repozytorium i dostęp: `Greg259/DotacjeAI`, SSH.
3. [ ] Pierwsze 3-5 oficjalnych źródeł dotacji.
4. [ ] Dostawca poczty transakcyjnej.
5. [ ] Dostawca zewnętrznego backupu.
6. [ ] Miesięczny limit OpenRouter.
7. [ ] Czy prywatne dokumenty użytkowników wchodzą do pierwszej bety, czy do etapu po uruchomieniu portalu.

## Najbliższy sprint - rekomendowana kolejność

### P0 - bieżąca konserwacja po zabezpieczeniu SSH

1. [x] Ustanowić `D:\Codex\DotacjeAI` jedynym aktywnym repozytorium i zachować odzyskiwalne archiwum starej kopii.
2. [ ] Wykonać zaszyfrowaną kopię odzyskiwania kluczy właściciela oraz zapisać nowe hasła w menedżerze haseł.
3. [x] Zainstalować oczekujące pakiety jądra `6.8.0-142`.
4. [x] Wykonać kontrolowany restart VPS.
5. [x] Potwierdzić nowe jądro, SSH, fail2ban, HTTPS i pięć zdrowych kontenerów; reguły ekspozycji portów zweryfikowano zewnętrznie.
6. [ ] Dokończyć instalację narzędzia `restic`.

Rezultat: serwer jest aktualny, a utrata obecnego komputera nie powoduje utraty dostępu.

### P0 - bezpieczeństwo dostępu

1. [x] Dodać publiczny klucz RSA 4096 do `/home/deploy/.ssh/authorized_keys`.
2. [x] Otworzyć nową sesję jako `deploy` i potwierdzić działanie `sudo` oraz Dockera.
3. [x] Potwierdzić dostęp przez Emergency Console i zachować sesje awaryjne do końca testu.
4. [x] Zmienić hasło `root`, następnie wyłączyć `PermitRootLogin` i `PasswordAuthentication`.
5. [x] Sprawdzić ponownie SSH, fail2ban oraz dostępność aplikacji; UFW pozostał aktywny z portami 22, 80 i 443.

Rezultat: administracja VPS jest możliwa wyłącznie kluczem przez konto `deploy`.

### P0 - backup i odtwarzanie

1. [x] Wybrać Cloudflare R2 jako zewnętrzny magazyn zgodny z S3.
2. [x] Przygotować skrypt codziennego `pg_dump` i backupu dokumentów bez kopiowania aktywnych sekretów w postaci jawnej.
3. [x] Przygotować szyfrowanie po stronie Restic przed wysłaniem poza VPS.
4. Ustawić retencję dzienną, tygodniową i miesięczną oraz alarm błędu zadania.
5. Wykonać próbne odtworzenie do osobnej bazy i zapisać procedurę disaster recovery.

Rezultat: istnieje sprawdzona kopia poza VPS, a nie tylko repozytorium GitHub.

### P1 - kontrola działania

1. Dodać zewnętrzny test `https://dotacjeai.eu/health`.
2. Alarmować o niedostępności, małej ilości miejsca, błędach backupu i niezdrowych kontenerach.
3. Ustawić rotację logów Dockera i prosty raport dzienny.

Rezultat: administrator dowiaduje się o awarii bez ręcznego logowania na serwer.

### P1 - fundament MVP

1. Ustawić ochronę gałęzi `main` i GitHub Actions dla testów.
2. Zbudować Next.js, FastAPI, SQLAlchemy/Alembic oraz pierwsze migracje.
3. Dodać worker i scheduler oparte na Redis.
4. Przygotować test uruchomienia od pustej bazy.

Rezultat: zmiany aplikacji można bezpiecznie testować i wdrażać.

### P1 - pierwszy pionowy przepływ

1. Wskazać 3-5 źródeł, ale najpierw wdrożyć jedno źródło end-to-end.
2. Pobrać stronę lub PDF, zapisać URL, datę, nagłówki i SHA-256.
3. Wykrywać zmianę bez LLM, zapisywać snapshot i generować diff.
4. Dopiero na wykrytej zmianie uruchomić ekstrakcję OpenRouter do walidowanego JSON.
5. Zatwierdzić wynik w prostym panelu REVIEW i opublikować program.

Rezultat: jeden audytowalny program przechodzi cały proces od źródła do publikacji.

### P2 - użytkownicy i beta

Po ustabilizowaniu przepływu należy dodać konta, matching, subskrypcje, e-mail, wymagania RODO i dopiero potem prywatne dokumenty użytkowników.
