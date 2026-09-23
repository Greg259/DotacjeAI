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
5. [x] Rozbudować FastAPI o konfigurację, logowanie JSON i obsługę błędów.
6. [x] Dodać SQLAlchemy oraz Alembic.
7. [x] Utworzyć pierwszą migrację MVP-0: źródła, snapshoty, lokalizacje, programy, wersje, dokumenty, LLM, REVIEW i audit log; tabelę użytkowników przesunąć do MVP-1.
8. [ ] Dodać worker i scheduler korzystające z Redis.
9. [x] Dodać testy, lint i kontrolę migracji w GitHub Actions.

Definition of Done:

- czysta baza przechodzi wszystkie migracje,
- API i worker mają healthchecki,
- testy i lint przechodzą,
- README pozwala uruchomić środowisko od zera.

## Etap 3 - monitoring bez AI

1. [ ] Rozszerzyć pilotaż z dwóch wdrożonych źródeł do 3-5 oficjalnych źródeł.
2. [x] Zbudować adapter HTTP z limitami, timeoutami, retry i identyfikacją aplikacji.
3. [x] Obsłużyć ETag, Last-Modified, status HTTP i SHA-256.
4. [x] Normalizować HTML przed hashowaniem.
5. [x] Zapisywać niezmienne snapshoty i wersje PDF.
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
3. [x] Pierwsze źródła: WFOŚiGW Warszawa / Czyste Powietrze i Gmina Nadarzyn; następnie harmonogram NFOŚiGW, Moje Ciepło, magazyny energii, Moja Elektrownia Wiatrowa i Ciepłe Mieszkanie.
4. [x] Dostawcę poczty transakcyjnej odłożyć do MVP-1.
5. [x] Zewnętrzny backup odłożyć na etap obowiązkowy przed betą; podczas budowy używać lokalnego Restic i GitHuba dla kodu oraz dokumentacji.
6. [x] Miesięczny limit OpenRouter: 10 USD; ostrzeżenia przy 5 i 8 USD, twarde zatrzymanie przy 10 USD.
7. [x] Konta i prywatne dokumenty użytkowników pominąć w MVP-0 i rozważyć w MVP-1.

## Najbliższy sprint - rekomendowana kolejność

### P0 - bieżąca konserwacja po zabezpieczeniu SSH

1. [x] Ustanowić `D:\Codex\DotacjeAI` jedynym aktywnym repozytorium i zachować odzyskiwalne archiwum starej kopii.
2. [ ] Wykonać zaszyfrowaną kopię odzyskiwania kluczy właściciela oraz zapisać nowe hasła w menedżerze haseł.
3. [x] Zainstalować oczekujące pakiety jądra `6.8.0-142`.
4. [x] Wykonać kontrolowany restart VPS.
5. [x] Potwierdzić nowe jądro, SSH, fail2ban, HTTPS i pięć zdrowych kontenerów; reguły ekspozycji portów zweryfikowano zewnętrznie.
6. [x] Dokończyć instalację narzędzia `restic` i potwierdzić zapis do katalogu backupów.

Rezultat: serwer jest aktualny, a utrata obecnego komputera nie powoduje utraty dostępu.

### P0 - bezpieczeństwo dostępu

1. [x] Dodać publiczny klucz RSA 4096 do `/home/deploy/.ssh/authorized_keys`.
2. [x] Otworzyć nową sesję jako `deploy` i potwierdzić działanie `sudo` oraz Dockera.
3. [x] Potwierdzić dostęp przez Emergency Console i zachować sesje awaryjne do końca testu.
4. [x] Zmienić hasło `root`, następnie wyłączyć `PermitRootLogin` i `PasswordAuthentication`.
5. [x] Sprawdzić ponownie SSH, fail2ban oraz dostępność aplikacji; UFW pozostał aktywny z portami 22, 80 i 443.

Rezultat: administracja VPS jest możliwa wyłącznie kluczem przez konto `deploy`.

### P0 - backup i odtwarzanie

1. [x] Przyjąć lokalne, szyfrowane repozytorium Restic na VPS jako rozwiązanie dla etapu budowy MVP; zewnętrzny storage przesunąć przed betę.
2. [x] Przygotować skrypt codziennego `pg_dump` i backupu dokumentów bez kopiowania aktywnych sekretów w postaci jawnej.
3. [x] Włączyć szyfrowanie repozytorium po stronie Restic.
4. [x] Ustawić retencję 7 kopii dziennych, 5 tygodniowych i 12 miesięcznych oraz lokalną kontrolę błędu zadania.
5. [x] Wykonać próbne odtworzenie plików i pełny import dumpa do osobnej bazy.

Rezultat MVP: istnieje sprawdzona, szyfrowana kopia bazy i danych na VPS oraz osobna kopia kodu i dokumentacji na GitHubie. Przed betą wynik musi zostać rozszerzony o kopię poza VPS.

### P1 - kontrola działania

1. [x] Dodać lokalny test `https://dotacjeai.eu/health` i `/api/health` co 5 minut.
2. [x] Kontrolować lokalnie niedostępność, miejsce, świeżość backupu i zdrowie kontenerów.
3. [x] Ustawić rotację logów Dockera.
4. [ ] Przed betą podłączyć zewnętrzne alarmy, aby awaria całego VPS była widoczna poza serwerem.

Rezultat: administrator dowiaduje się o awarii bez ręcznego logowania na serwer.

### P1 - fundament MVP

1. Ustawić ochronę gałęzi `main` i GitHub Actions dla testów.
2. Zbudować Next.js, FastAPI, SQLAlchemy/Alembic oraz pierwsze migracje.
3. Dodać worker i scheduler oparte na Redis.
4. [x] Przygotować test uruchomienia od pustej bazy w GitHub Actions.

Rezultat: zmiany aplikacji można bezpiecznie testować i wdrażać.

### P1 - pierwszy pionowy przepływ

1. Wdrożyć WFOŚiGW Warszawa / Czyste Powietrze jako pierwsze źródło end-to-end, a Gminę Nadarzyn jako drugi test PDF i zakończonego terminu.
2. [x] Pobrać stronę lub PDF, zapisać URL, datę, nagłówki i SHA-256.
3. [x] Wykrywać zmianę bez LLM, zapisywać snapshot i generować diff.
4. Dopiero na wykrytej zmianie uruchomić ekstrakcję OpenRouter do walidowanego JSON.
5. Zatwierdzić wynik w prostym panelu REVIEW i opublikować program.

Rezultat: jeden audytowalny program przechodzi cały proces od źródła do publikacji.

### P2 - użytkownicy i beta

Po ustabilizowaniu przepływu należy dodać konta, matching, subskrypcje, e-mail, wymagania RODO i dopiero potem prywatne dokumenty użytkowników.

## Najbliższe kroki po wdrożeniu crawlera

1. Dodać jawny idempotency key i osobną listę nowych/usuniętych linków.
2. Rozszerzyć pilotaż o harmonogram NFOŚiGW jako trzecie źródło.
3. Przygotować walidowany schemat ekstrakcji programu wraz z dowodami dla każdego pola.
4. Zaimplementować budżetowany provider OpenRouter bez ustawiania klucza w Git.
5. Zbudować prosty panel administratora dla dwóch oczekujących zadań REVIEW.
6. Dopiero po ręcznym zatwierdzeniu utworzyć pierwsze rekordy `programs` i opublikować je w portalu.
