# DotacjeAI - plan kolejnych kroków

Aktualizacja: 2026-09-26.

## Rozpoczęcie MVP-1 — Sprint 09A

- [x] Dodano lokalne konta oparte na nazwie użytkownika i haśle, bez wymagania e-maila.
- [x] Dodano role `user`, `editor` i `admin`, sesje serwerowe oraz ochronę CSRF.
- [x] Dodano tworzenie, edycję i usuwanie profili nieruchomości.
- [x] Dodano eksport danych i trwałe usunięcie konta.
- [x] Dodano wersjonowane zgody, informację o prywatności i regulamin wersji testowej.
- [ ] Dodać e-mail, weryfikację adresu i reset hasła w późniejszym sprincie.
- [ ] Sprint 10: wykorzystać profile w deterministycznym silniku dopasowania.

Szczegóły: `SPRINT_09_ACCOUNTS_PROFILES.md`.

## Sprint 10 — deterministyczne dopasowanie

- [x] Jeden użytkownik może mieć wiele niezależnych profili.
- [x] Profile obejmują nieruchomości oraz przedsiębiorstwa/organizacje.
- [x] Dodano dane MŚP, formę prawną, zatrudnienie, obrót, branże i cele B+R.
- [x] Dodano reguły statusu, beneficjenta, lokalizacji, rodzaju profilu i celu inwestycji.
- [x] Dodano wyniki `spełnione`, `niespełnione`, `brak danych` oraz ranking programów.
- [x] Każda decyzja ma jawne uzasadnienie; AI nie decyduje o kwalifikacji.
- [ ] Rozszerzyć produkcyjny katalog o zweryfikowane programy NCBR, PARP i Funduszy Europejskich.

Szczegóły: `SPRINT_10_DETERMINISTIC_MATCHING.md`.

## Sprint 10B — reguły szczegółowe i programy firmowe

- [x] Dodano wersjonowane reguły kwalifikacji z oficjalnym dowodem.
- [x] Dodano kryteria dochodowe, budżet i wkład własny dla profili prywatnych.
- [x] Dodano pomoc de minimis, startup, VC i konsorcjum dla profili firmowych.
- [x] Dodano deterministyczne operatory liczbowe, listowe i logiczne.
- [x] Dodano wykrywanie programów z indeksów PARP, NCBR i Funduszy Europejskich.
- [x] Dodano diagnostykę dopasowania profilu w panelu administratora.
- [ ] Po wdrożeniu wykonać REVIEW pierwszych wyników PARP i opublikować wyłącznie zweryfikowane programy.

Szczegóły: `SPRINT_10B_ADVANCED_MATCHING_BUSINESS_DISCOVERY.md`.

## Stan po Sprincie 07

- [x] Rozszerzono katalog do 12 oficjalnych źródeł i 11 programów publicznych.
- [x] Dodano gminy powiatu pruszkowskiego: Pruszków, Brwinów, Michałowice, Piastów i Raszyn obok Nadarzyna.
- [x] Dodano klasyfikację zmian regulaminu, terminu, kwoty, formularza i zamknięcia naboru.
- [x] Dodano stany dokumentów i REVIEW nowych wersji.
- [x] Przygotowano 20-przypadkowy zestaw jakości AI i porównano cztery modele.
- [x] Dodano ocenę kompletności programu w panelu administratora.

Następny rekomendowany etap: Sprint 06 w zakresie infrastruktury przed betą (backup poza VPS, alarm zewnętrzny i końcowa rotacja klucza), a następnie Sprint 08 — konta oraz profile użytkowników.

## Stan po odbiorze MVP-0

MVP-0 zostało zakończone i wdrożone. Aktualny protokół oraz granica zakresu znajdują się w `MVP0_COMPLETION.md`. Poniższe historyczne etapy pozostają jako zapis realizacji; aktualna kolejność dalszych prac to:

1. P0 właściciela: obrócić ujawniony klucz OpenRouter bez przekazywania nowej wartości przez rozmowę lub Git.
2. P0 przed betą: wysłać zaszyfrowany backup poza VPS i dodać zewnętrzny alarm dostępności.
3. P1: obserwować crawler, ekstrakcję, REVIEW, dokumenty i automatyczne statusy przez kilka dni.
4. [x] P1: rozszerzyć katalog do sześciu oficjalnych programów; wykonano w Sprincie 05.
5. P2 / MVP-1: konta, profile nieruchomości, matching, obserwowanie programów i e-mail.

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
7. [ ] Wybrać zewnętrzny storage backupów przed betą; lokalny etap MVP działa.
8. [x] Wdrożyć codzienny `pg_dump`, backup dokumentów, szyfrowanie, retencję i test odtworzenia.
9. [x] Dodać monitoring dostępności, dysku i błędów kontenerów.

Definition of Done:

- HTTPS działa,
- logowanie kluczem działa,
- backup można odtworzyć,
- alarm testowy dociera do administratora.

## Etap 2 - fundament aplikacji

1. [x] Utworzyć repozytorium GitHub i skonfigurować dostęp przez SSH.
2. [x] Wysłać kod infrastruktury i dokumentację bez sekretów na `main`.
3. [ ] Włączyć ochronę `main`, pracę przez pull request i podstawowe reguły przeglądu.
4. [x] Zastąpić placeholder frontendu aplikacją Next.js.
5. [x] Rozbudować FastAPI o konfigurację, logowanie JSON i obsługę błędów.
6. [x] Dodać SQLAlchemy oraz Alembic.
7. [x] Utworzyć pierwszą migrację MVP-0: źródła, snapshoty, lokalizacje, programy, wersje, dokumenty, LLM, REVIEW i audit log; tabelę użytkowników przesunąć do MVP-1.
8. [x] Dodać harmonogram zadań crawlera, ekstrakcji, dokumentów i statusów; stały worker odłożono do skali po MVP-0.
9. [x] Dodać testy, lint i kontrolę migracji w GitHub Actions.

Definition of Done:

- czysta baza przechodzi wszystkie migracje,
- API i worker mają healthchecki,
- testy i lint przechodzą,
- README pozwala uruchomić środowisko od zera.

## Etap 3 - monitoring bez AI

1. [x] Rozszerzyć pilotaż do trzech opublikowanych oficjalnych programów.
2. [x] Zbudować adapter HTTP z limitami, timeoutami, retry i identyfikacją aplikacji.
3. [x] Obsłużyć ETag, Last-Modified, status HTTP i SHA-256.
4. [x] Normalizować HTML przed hashowaniem.
5. [x] Zapisywać niezmienne snapshoty i wersje PDF.
6. [x] Generować diff tekstowy i monitorować linki dokumentów.
7. [x] Wprowadzić idempotency key dla każdego zadania.

Definition of Done:

- brak zmiany kończy zadanie bez LLM,
- zmiana tworzy nową wersję i diff,
- ponowienie zadania nie tworzy duplikatu,
- PDF można powiązać z URL, datą i SHA-256.

## Etap 4 - OpenRouter i test modeli

Stan MVP-0: punkty 2–6 i 9 wykonano produkcyjnie; szerszy benchmark 20–30 regulaminów oraz porównanie wielu modeli pozostają optymalizacją po MVP-0. Rotacja tymczasowego klucza wymaga właściciela.

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

Stan MVP-0: wykonane w chronionym panelu `/admin`.

1. Lista źródeł i stan ostatniego pobrania.
2. Podgląd wersji i diff.
3. Kolejka wyników AI do zatwierdzenia.
4. Akcje approve, reject i edit.
5. Widoczność źródła każdego pola.
6. Podgląd kosztów LLM i błędów workerów.

## Etap 6 - portal publiczny

Stan MVP-0: wykonane produkcyjnie.

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

Szczegółowy zakres wykonawczy znajduje się w `SPRINT_03_EXTRACTION_REVIEW_PLAN.md`.

1. Dodać jawny idempotency key i osobną listę nowych/usuniętych linków.
2. Rozszerzyć pilotaż o harmonogram NFOŚiGW jako trzecie źródło.
3. Przygotować walidowany schemat ekstrakcji programu wraz z dowodami dla każdego pola.
4. Zaimplementować budżetowany provider OpenRouter bez ustawiania klucza w Git.
5. Zbudować prosty panel administratora dla dwóch oczekujących zadań REVIEW.
6. Dopiero po ręcznym zatwierdzeniu utworzyć pierwsze rekordy `programs` i opublikować je w portalu.

## Aktualny krok po ekstrakcji produkcyjnej — 2026-09-24

1. [ ] P0: unieważnić ujawniony klucz OpenRouter i wprowadzić nowy bezpośrednio na VPS.
2. [ ] Sprawdzić przez `review_cli.sh show` Nadarzyn oraz dwa wyniki WFOŚiGW.
3. [ ] Zatwierdzić Nadarzyn albo skorygować ostrzeżenie dotyczące typu nieruchomości.
4. [ ] Dla WFOŚiGW wybrać właściwy wynik bazowy i odrzucić zbędne zadanie zmiany z uzasadnieniem.
5. [ ] Osobnym poleceniem opublikować wyłącznie ręcznie zatwierdzone programy.
6. [ ] Sprawdzić publiczne filtry i karty programów po pierwszej publikacji.
7. [ ] Rozpocząć Sprint 04: docelowy frontend publiczny i bezpieczne uwierzytelnienie administratora.

Stan techniczny: 3/3 ekstrakcje są `ready_for_review`, 0 programów publicznych, koszt 0,026836 USD, backup `8fc846f5` zweryfikowany pełnym odtworzeniem.

Szczegółowy następny etap opisuje `SPRINT_04_PUBLIC_PORTAL_PLAN.md`. Na decyzję właściciela rotację ujawnionego klucza OpenRouter przeniesiono na sam koniec Sprintu 04. Do tego czasu nowe wywołania LLM pozostają zamrożone.

## Realizacja Sprintu 04 — następna kolejność

1. [x] Rozszerzyć publiczne API o dokumenty i zatwierdzoną historię zmian.
2. [x] Zablokować publiczny dostęp do szkiców testem regresji.
3. [x] Zastąpić placeholder frontendem Next.js i przygotować wymagane trasy MVP-0.
4. [x] Dodać frontend do GitHub Actions i lokalnie sprawdzić typecheck/build.
5. [x] Wysłać commit, potwierdzić zielone CI i wykonać backup przed wdrożeniem.
6. [x] Zbudować obrazy na VPS, wdrożyć dokładny commit i sprawdzić HTTPS oraz healthchecki.
7. [x] Otrzymać od właściciela decyzje REVIEW dla Nadarzyna i dwóch wyników WFOŚiGW.
8. [x] Wykonać jawne `approve`, a potem osobne `publish` tylko dla zatwierdzonych danych.
9. [x] Przejść kontrolę listy, filtrów i karty oraz sprawdzić mobile; audyt produkcji 390 × 844 px zakończono w punkcie 4 Sprintu 05.
10. [x] Wykonać backup po publikacji i pełny test odtworzenia.
11. [ ] Na samym końcu obrócić ujawniony klucz OpenRouter bez wpisywania nowego klucza do rozmowy lub Git.

Stan wdrożenia: commit `99f22c7`, CI run 22 `success`, backup przed wdrożeniem `570de219`, API `0.5.0`, pięć zdrowych kontenerów i HTTP 200 dla wszystkich tras MVP. Następna czynność wymaga jawnej decyzji opisanej w `SPRINT_04_REVIEW_DECISION.md`.

Stan po decyzji REVIEW: dwa programy publiczne, dwa zadania zatwierdzone, jeden duplikat odrzucony, filtry i karty działają. Zweryfikowany backup po publikacji: `bdb9f3f2`. Pozostały kontrola wizualna oraz końcowa rotacja ujawnionego klucza.

## Stan po rozszerzeniu kart — 2026-09-24

1. [x] Rozszerzyć model ekstrakcji o warunki, beneficjentów, warianty finansowania, ograniczenia, kroki, załączniki i formularze.
2. [x] Pokazać te informacje na publicznej karcie programu wraz ze wskazaniem źródła.
3. [x] Dodać tylko oficjalne formularze i portale dla Nadarzyna oraz Czystego Powietrza.
4. [x] Zachować ręczny REVIEW i wersjonowanie; zablokować automatyczną publikację wyniku AI.
5. [x] Wdrożyć commit `12833a7`, sprawdzić API, HTML, kontenery i logi.
6. [x] Wykonać oraz w pełni zweryfikować backup `0049f91e`.
7. [x] Wykonać kontrolę wizualną na telefonie i komputerze; wykryty błąd UTF-8 naprawiono i zweryfikowano ponownie.
8. [ ] Dodać trzeci program i sprawdzić pełny automatyczny przepływ `crawler → extraction-v2 → REVIEW → publish`.
9. [ ] Dodać walidator linków dokumentów oraz oznaczanie formularza jako nieaktualnego po zmianie źródła.
10. [ ] Na końcu prac obrócić ujawniony klucz OpenRouter bez wpisywania nowej wartości do rozmowy lub Git.
