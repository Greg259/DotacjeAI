# DotacjeAI - zapis rozmowy i decyzji projektowych

Data rozpoczęcia: 2026-09-22
Użytkownik: właściciel projektu
Asystent: Codex

> Dokument jest uporządkowanym zapisem rozmowy, decyzji i wykonanych działań. Hasła oraz sekrety zostały usunięte. Szczegółowe komunikaty narzędziowe, logi instalatora i powtarzające się dane techniczne zostały skrócone.

## 1. Weryfikacja dostępu do VPS

### Użytkownik

Poprosił o sprawdzenie dostępu do serwera Time4VPS i przekazał:

- użytkownika `root`,
- hasło: `[USUNIĘTO]`,
- adres IP `185.69.52.106`.

### Codex

Sprawdzono dostępność portu SSH 22 oraz wykonano testowe logowanie bez modyfikacji serwera.

Wynik:

- SSH odpowiada,
- uwierzytelnienie użytkownika `root` działa,
- system Linux x86-64,
- używany kernel w czasie pierwszej kontroli: `6.8.0-139-generic`.

Zalecono zmianę przekazanego hasła oraz docelowe przejście na klucz SSH.

## 2. Klucz SSH

### Użytkownik

Zapytał, gdzie znajduje się klucz SSH.

### Codex

Sprawdzono lokalny katalog użytkownika Windows. Znaleziono istniejącą parę:

- klucz prywatny: `C:\Users\grzeg\.ssh\id_ed25519`,
- klucz publiczny: `C:\Users\grzeg\.ssh\id_ed25519.pub`.

Wyjaśniono, że klucza prywatnego nie wolno udostępniać, a klucz publiczny można dodać na serwerze do `authorized_keys`.

### Użytkownik

Zdecydował, aby na tym etapie nie instalować klucza.

### Decyzja

Logowanie roota hasłem pozostało aktywne, aby nie utracić dostępu. Wyłączenie hasła i logowania roota zostało przesunięte do czasu przetestowania logowania kluczem na koncie `deploy`.

## 3. Analiza planu MVP z PDF

### Użytkownik

Poprosił o przejrzenie dokumentu:

`C:\Users\grzeg\Downloads\DotacjeAI_MVP_plan_wdrozenia_Time4VPS.pdf`

oraz przygotowanie planu implementacji z wykorzystaniem istniejącego VPS.

### Codex

Przeanalizowano pełny, 18-stronicowy dokument wraz z kontrolą wizualną stron. Potwierdzono, że VPS wystarczy do MVP obejmującego:

- portal publiczny,
- FastAPI i frontend,
- PostgreSQL oraz Redis,
- monitoring oficjalnych źródeł,
- wersjonowanie stron i dokumentów,
- ekstrakcję oraz klasyfikację LLM,
- panel administratora,
- konta użytkowników,
- matching programów,
- powiadomienia.

Zalecono:

- jeden VPS dla całego MVP,
- Docker Compose zamiast Kubernetes,
- zewnętrzne API LLM zamiast lokalnego modelu,
- publiczne wystawienie wyłącznie Caddy,
- pozostawienie PostgreSQL i Redis w sieci wewnętrznej,
- budowę najpierw pionowego przepływu `źródło -> zmiana -> AI -> review -> publikacja -> alert`.

Oszacowano pełne MVP na około 7-9 tygodni pracy jednego doświadczonego programisty.

## 4. Audyt VPS przed wdrożeniem

Przed zmianami wykonano diagnostykę tylko do odczytu.

Stan początkowy:

- Ubuntu 24.04.4 LTS,
- 3 vCPU,
- 7,8 GiB RAM,
- około 77 GiB wolnego miejsca,
- Docker aktywny,
- brak Docker Compose,
- UFW aktywny z portami 22, 80 i 443,
- brak uruchomionych kontenerów,
- brak swapu,
- strefa czasowa `Europe/Vilnius`,
- fail2ban nieaktywny,
- 48 oczekujących aktualizacji,
- bezpośrednie logowanie `root` hasłem aktywne,
- około 7 GB starych obrazów Docker.

## 5. Przygotowanie serwera

### Użytkownik

Polecił:

1. zaktualizować system i zaplanować restart,
2. ustawić `Europe/Warsaw`,
3. dodać swap,
4. zainstalować Docker Compose,
5. uruchomić fail2ban,
6. utworzyć użytkownika `deploy`,
7. utworzyć `/opt/dotacje-ai`,
8. przygotować dane, sekrety i backupy,
9. uruchomić minimalny Compose z Caddy, API, frontendem, PostgreSQL i Redisem,
10. przechowywać Markdown lokalnie i na serwerze,
11. przygotować system pod OpenRouter.

### Codex - wykonane działania

- Zaktualizowano wszystkie pakiety systemowe.
- System po aktualizacji zgłasza Ubuntu 24.04.5 LTS.
- Wykonano kontrolowany restart.
- Ustawiono strefę `Europe/Warsaw` i potwierdzono NTP.
- Utworzono swap 2 GiB i ustawiono `vm.swappiness=10`.
- Zainstalowano Docker Compose 2.40.3.
- Zainstalowano i skonfigurowano fail2ban dla SSH.
- Utworzono konto `deploy` w grupach `sudo` i `docker`.
- Utworzono strukturę `/opt/dotacje-ai`.
- Wygenerowano losowe hasła PostgreSQL i Redis.
- Sekrety zapisano poza repozytorium z prawami 600.
- Uruchomiono pięć kontenerów z healthcheckami i limitami zasobów.
- Przetestowano automatyczny powrót kontenerów po restarcie VPS.

Kontenery:

- `caddy`,
- `frontend`,
- `api`,
- `postgres`,
- `redis`.

Endpointy testowe:

- `/`,
- `/health`,
- `/api/health`.

Wszystkie kontenery uzyskały status `healthy`.

### Świadomie niewykonane

- Nie wyłączono logowania roota ani logowania hasłem, ponieważ użytkownik nie chciał jeszcze instalować klucza SSH.
- Nie skonfigurowano HTTPS, ponieważ nie wskazano domeny.
- Nie usunięto starych obrazów Docker bez dodatkowej zgody i weryfikacji.
- Nie skonfigurowano produkcyjnego backupu zewnętrznego.

## 6. Organizacja dokumentacji

### Lokalnie

`D:\Codex\ProjektDotacje`

### Na serwerze

`/home/deploy/Codex/ProjektDotacje`

Dokumenty są synchronizowane do obu lokalizacji i przechowywane bez sekretów.

## 7. Pierwsza rekomendacja modeli OpenRouter

Początkowo zaproponowano:

- `openai/gpt-5.6-luna` jako model szybki,
- `openai/gpt-5.6-luna-pro` jako model dokładny,
- `google/gemini-3.8-flash` jako model walidacyjny/multimodalny.

Klucz OpenRouter pozostawiono pusty w:

`/opt/dotacje-ai/secrets/app.env`

Nie zapisano żadnego klucza API w repozytorium ani dokumentacji.

## 8. Analiza tańszych modeli OpenRouter

### Użytkownik

Poprosił o sprawdzenie, czy można użyć tańszych modeli.

### Codex

Porównano aktualne ceny i funkcje modeli w katalogu OpenRouter. Zaproponowano routing wielopoziomowy:

```dotenv
LLM_MODEL_CLASSIFY=deepseek/deepseek-v4-flash-0731
LLM_MODEL_EXTRACT=deepseek/deepseek-v4-flash-0731
LLM_MODEL_VALIDATE=openai/gpt-5-nano
LLM_MODEL_STRONG=openai/gpt-5.6-luna-pro
LLM_MODEL_MULTIMODAL=google/gemini-3.1-flash-lite
```

Wnioski:

- deterministyczny monitoring powinien eliminować większość wywołań LLM,
- DeepSeek V4 Flash nadaje się do taniej analizy publicznego tekstu,
- GPT-5 Nano może pełnić rolę taniego walidatora,
- GPT-5.6 Luna Pro powinien obsługiwać wyłącznie trudne przypadki,
- Gemini 3.1 Flash Lite powinien być używany tylko dla skanów, obrazów i trudnych PDF,
- danych o niskiej pewności nie wolno publikować bez REVIEW,
- model należy wybrać po teście na 20-30 ręcznie sprawdzonych regulaminach.

Dla przykładu 50 000 tokenów wejścia i 2 000 wyjścia oszacowano:

- DeepSeek V4 Flash: około 0,00282 USD,
- GPT-5 Nano: około 0,00330 USD,
- GPT-5.6 Luna: około 0,01240 USD.

Aktywnej konfiguracji modeli nie zmieniono przed wykonaniem testów jakościowych.

## 9. Utworzona dokumentacja

W katalogu projektu znajdują się:

- `README.md`,
- `SERVER_SETUP.md`,
- `IMPLEMENTATION_STATUS.md`,
- `TECHNICAL_SERVER_DOCUMENTATION.md`,
- `OPENROUTER_MODELS.md`,
- `OPENROUTER_COST_OPTIMIZATION.md`,
- `NEXT_STEPS_PLAN.md`,
- `CONVERSATION_LOG.md` - niniejszy dokument.

## 10. Ustalony plan dalszych działań

Rekomendowana kolejność:

1. domena i HTTPS,
2. klucz SSH dla `deploy`, test logowania i zamknięcie dostępu hasłem,
3. zmiana ujawnionego hasła roota,
4. zewnętrzny backup i test odtworzenia,
5. repozytorium Git, FastAPI, Next.js i migracje PostgreSQL,
6. wybór 3-5 oficjalnych źródeł pilotażowych,
7. monitoring deterministyczny i wersjonowanie dokumentów,
8. integracja OpenRouter i test porównawczy modeli,
9. panel REVIEW,
10. portal publiczny, konta, matching i alerty.

## 11. Aktualny stan końcowy

- VPS działa po restarcie.
- Wszystkie pięć kontenerów ma status `healthy`.
- Oczekujące aktualizacje: 0.
- UFW, fail2ban, Docker, AppArmor i unattended-upgrades są aktywne.
- PostgreSQL i Redis nie mają publicznych portów.
- HTTPS czeka na domenę.
- Backup aplikacyjny czeka na zewnętrzny storage i harmonogram.
- OpenRouter czeka na klucz API oraz test modeli.
- Logowanie roota hasłem pozostaje tymczasowo aktywne.

## 12. Domena produkcyjna

Użytkownik wskazał świeżo zakupioną domenę `dotacjeai.eu` utrzymywaną w home.pl.

Ustalono rekordy:

- A dla domeny głównej -> `185.69.52.106`,
- CNAME `www` -> `dotacjeai.eu`.

Rekord TXT weryfikacyjny pozostawiono bez zmian. Po pojawieniu się rekordu A skonfigurowano automatyczne HTTPS w Caddy.

Wynik:

- `http://dotacjeai.eu` przekierowuje do HTTPS,
- `https://dotacjeai.eu` działa,
- `https://dotacjeai.eu/api/health` odpowiada poprawnie,
- certyfikat został wystawiony przez Let's Encrypt,
- wszystkie kontenery pozostały zdrowe,
- rekord `www.dotacjeai.eu` pojawił się w DNS home.pl,
- Caddy wystawił osobny certyfikat Let's Encrypt dla `www.dotacjeai.eu`,
- `https://www.dotacjeai.eu` przekierowuje kodem 301 na `https://dotacjeai.eu`.

## 13. Repozytorium GitHub

Użytkownik utworzył repozytorium:

`git@github.com:Greg259/DotacjeAI.git`

oraz dodał publiczny klucz SSH komputera do swojego konta GitHub.

Wykonane działania:

- potwierdzono uwierzytelnienie konta `Greg259`,
- sklonowano istniejącą gałąź `main`,
- zachowano pierwotny commit repozytorium,
- dodano kod infrastruktury, aplikacje techniczne i dokumentację,
- dodano `.gitignore` oraz `.gitattributes`,
- przeskanowano staged diff pod kątem sekretów,
- nie wykryto prawdziwych haseł ani kluczy API,
- wykonano commit `832abd6` o opisie `Add DotacjeAI MVP infrastructure and documentation`,
- wysłano commit do `origin/main`.

GitHub przechowuje kod i dokumentację. Nie służy jako backup PostgreSQL, uploadów użytkowników, dokumentów prywatnych ani pliku `/opt/dotacje-ai/secrets/app.env`. Te dane wymagają osobnego, szyfrowanego backupu poza VPS.

## 14. Aktualizacja planu realizacji

Na prośbę użytkownika zaktualizowano status i plan kolejnych prac. Jako wykonane oznaczono domenę, HTTPS, repozytorium GitHub, dostęp do GitHuba przez SSH oraz pierwszy backup kodu i dokumentacji.

Najbliższe działania uporządkowano według priorytetów:

1. P0: klucz SSH dla `deploy`, test dostępu, zmiana hasła `root` i wyłączenie logowania hasłem oraz bezpośredniego logowania `root`.
2. P0: szyfrowany backup poza VPS wraz z testem odtworzenia.
3. P1: monitoring dostępności, zasobów, kontenerów i backupów.
4. P1: ochrona gałęzi `main`, CI, Next.js, FastAPI, migracje i worker.
5. P1: pierwszy kompletny przepływ od oficjalnego źródła do zatwierdzonej publikacji.
6. P2: użytkownicy, matching, alerty e-mail, RODO i beta.

Szczegóły oraz kryteria rezultatów zapisano w `NEXT_STEPS_PLAN.md`, a bieżące otwarte zadania w `IMPLEMENTATION_STATUS.md`.

## 15. Procedura zabezpieczenia SSH

Użytkownik poprosił o opis wykonania zadania P0 dotyczącego SSH. Przygotowano instrukcję `SSH_HARDENING_RUNBOOK.md`.

Ustalono bezpieczną kolejność: dostęp do konsoli awaryjnej, instalacja klucza publicznego dla `deploy`, ustawienie lokalnych haseł poza rozmową, test `sudo` i Dockera, walidacja konfiguracji przez `sshd -t`, przeładowanie usługi oraz testy pozytywne i negatywne w nowych sesjach.

Zmian bezpieczeństwa nie wykonano jeszcze na VPS. Nie wolno wyłączać dostępu hasłem ani konta `root`, zanim logowanie kluczem i `sudo` użytkownika `deploy` nie zostaną potwierdzone.

Użytkownik wskazał opcję SSH Key Management w Time4VPS. Zalecono zapisanie w panelu istniejącego klucza publicznego `id_ed25519.pub`, bez tworzenia zbędnej drugiej pary i bez udostępniania klucza prywatnego. Dokumentacja Time4VPS opisuje użycie klucza podczas instalacji lub reinstalacji systemu, dlatego dla działającego VPS klucz zostanie dodatkowo zainstalowany bezpośrednio na koncie `deploy`.

Panel odrzucił klucz ED25519, ale zaakceptował osobną parę RSA 4096 przeznaczoną dla VPS. Ustalono rozdzielenie: ED25519 dla GitHuba, RSA dla VPS. Konfiguracja działającego serwera pozostaje bez zmian do czasu potwierdzenia dostępu do konsoli awaryjnej.

## 16. Zakończenie zabezpieczania SSH

Potwierdzono działanie Emergency Console Time4VPS oraz logowanie lokalne jako `root`. Publiczny klucz RSA 4096 dodano do `/home/deploy/.ssh/authorized_keys` z uprawnieniami `0700` dla `.ssh` i `0600` dla pliku kluczy.

W nowych sesjach potwierdzono logowanie jako `deploy`, grupy `sudo` i `docker`, działanie `sudo`, dostęp do Dockera, pięć zdrowych kontenerów oraz odpowiedź `ok` aplikacji. Wdrożono i zweryfikowano konfigurację `/etc/ssh/sshd_config.d/00-dotacje-ai-hardening.conf`. Logowanie hasłem, keyboard-interactive i bezpośrednie logowanie `root` zostały wyłączone. Usługę SSH włączono przy starcie systemu.

Użytkownik ustawił nowe, nieujawnione hasła `deploy` i `root`, a testy niedozwolonych metod zakończyły się oczekiwaną odmową dostępu. Etap P0 zabezpieczenia SSH uznano za wykonany.

Po uruchomieniu lokalnego `ssh-agent` potwierdzono bezinterakcyjne uwierzytelnienie konta `deploy` właściwym kluczem. Zewnętrzny test portów wykazał dostępność 22, 80 i 443 oraz brak publicznego dostępu do 3000, 5432, 6379 i 8000. Zaktualizowane dokumenty zsynchronizowano przez `deploy`, a ich lokalne i serwerowe sumy SHA-256 są identyczne.

## 17. Dostęp dla kolejnej osoby i komputera

Użytkownik zapytał o przekazanie dostępu do projektu osobie pracującej z innego komputera i Codexa. Odrzucono pomysł paczki zawierającej produkcyjny `.env` i prywatne klucze.

Przyjęto model osobnych kluczy dla każdej osoby i każdego urządzenia, kont imiennych na VPS, indywidualnych kont GitHub oraz sekretów przekazywanych przez kontrolowany menedżer haseł. Codex korzysta z lokalnego `ssh-agent` i nie otrzymuje kopii klucza prywatnego ani passphrase.

Pełną procedurę onboardingu, offboardingu, dostępu do GitHuba oraz bezpiecznego zakresu paczki startowej zapisano w `ACCESS_ONBOARDING.md`.

Użytkownik doprecyzował, że chodzi o jego własny drugi komputer. Ustalono zachowanie tych samych kont OpenAI, GitHub `Greg259` i VPS `deploy`, ale z nowym kluczem przypisanym do drugiego urządzenia. Kod oraz trwały kontekst będą odtwarzane z repozytorium i dokumentacji, bez kopiowania produkcyjnego `.env`, folderu `.ssh` ani całego profilu `.codex`.

## 18. Kolejność dalszych prac na obecnym komputerze

Kontrola odczytowa wykazała 74 GB wolnego miejsca, około 7,1 GB dostępnej pamięci, nieużywany swap i pięć zdrowych kontenerów. Katalog `/opt/dotacje-ai/backups` nie zawiera backupów. Dostępna jest aktualizacja jądra z `6.8.0-139` do `6.8.0-142`; przed jej instalacją system nie wymaga jeszcze restartu.

Jako kolejne działania wskazano: zaszyfrowaną kopię odzyskiwania kluczy i haseł, instalację aktualizacji z kontrolowanym restartem, zewnętrzny szyfrowany backup z testem odtworzenia, monitoring, a następnie fundament aplikacji MVP.

Na polecenie użytkownika rozpoczęto realizację całej kolejki. Porównano `D:\Codex\DotacjeAI` i `D:\Codex\ProjektDotacje`; zestaw oraz treść plików były zgodne, a różnice binarne wynikały z końców linii Git. Dawną kopię przeniesiono do `D:\Codex\archive\ProjektDotacje-pre-git-20260923`, a ścieżkę `D:\Codex\ProjektDotacje` zastąpiono junctionem do `D:\Codex\DotacjeAI`. Od tego momentu istnieje jedno aktywne repozytorium robocze.

Do zewnętrznego backupu zarekomendowano `restic` z magazynem Cloudflare R2, a do monitoringu zewnętrznego Better Stack lub HetrixTools. Aktywacja tych usług wymaga kont i sekretów wprowadzonych poza repozytorium oraz rozmową.

## 19. Aktualizacja jądra i przygotowanie automatyzacji

Użytkownik uruchomił aktualizację systemu i kontrolowany restart. Po ponownym uruchomieniu zweryfikowano jądro `6.8.0-142-generic`, brak potrzeby kolejnego restartu, aktywne i włączone usługi SSH, Docker oraz fail2ban, pięć zdrowych kontenerów, poprawne endpointy HTTPS i API, 23% zajętego dysku oraz 2 GiB aktywnego swapu.

Polecenie aktualizacji nie zainstalowało pakietu `restic`, dlatego jego instalacja pozostała osobnym krótkim krokiem administracyjnym. W repozytorium przygotowano skrypt szyfrowanego backupu PostgreSQL i danych do Cloudflare R2, kontrolę integralności i odtworzenia oraz lokalny monitoring HTTPS, API, kontenerów, dysku i świeżości kopii. Sekrety R2 i heartbeat mają być wprowadzone bezpośrednio na serwerze i nie mogą trafić do rozmowy ani Git.

Pakiet `restic 0.16.4` został następnie zainstalowany. Po skorygowaniu przełamanej podczas wklejania ścieżki potwierdzono, że `/opt/dotacje-ai/backups` należy do `deploy:deploy`, ma tryb `0700` i jest zapisywalny dla procesu backupu. Ponowna walidacja składni wszystkich trzech skryptów na Ubuntu zakończyła się poprawnie.

## 20. Lokalny backup na czas budowy MVP

Użytkownik zdecydował, że na etapie budowy MVP nie będzie zakładał Cloudflare R2. Przyjęto szyfrowane repozytorium Restic na tym samym VPS oraz GitHub jako kopię kodu i dokumentacji. Baza danych, uploady oraz sekrety nie będą umieszczane w Git.

Zewnętrzny backup pozostaje obowiązkowym zadaniem przed betą, ponieważ kopia na tym samym VPS nie chroni przed utratą całej maszyny. Przygotowano automatyczną konfigurację lokalnego repozytorium, codzienny backup, retencję, pełny test importu dumpa do tymczasowej bazy i harmonogram lokalnego monitoringu.

Utworzono zaszyfrowane lokalne repozytorium Restic, a hasło zapisano wyłącznie w chronionym pliku z trybem `0600`. Pierwszy test wykrył absolutną ścieżkę w pliku sum kontrolnych; poprawiono ją na względną i powtórzono cały proces. Snapshot `858176df` przeszedł kontrolę repozytorium, odtworzenie plików, weryfikację SHA-256 oraz pełny import do tymczasowej bazy PostgreSQL. Poprawiono także grupowanie retencji po hoście i tagu.

Crontab użytkownika `deploy` uruchamia backup codziennie o 02:30 oraz monitoring co 5 minut. Końcowy test monitoringu potwierdził HTTPS, API, stan pięciu kontenerów, poziom zajętości dysku oraz świeżość backupu.

## 21. Decyzja o pominięciu Cloudflare na etapie MVP

Użytkownik zapytał, czy Cloudflare jest konieczny do uruchomienia MVP. Ustalono, że Cloudflare R2 nie jest zależnością aplikacji i można go odłożyć. Na czas budowy przyjęto lokalne, szyfrowane backupy Restic na VPS oraz GitHub jako osobną kopię kodu i dokumentacji.

Po instalacji Restic skorygowano uprawnienia katalogów `/opt/dotacje-ai` i `/opt/dotacje-ai/backups`. Potwierdzono wersję `restic 0.16.4`, możliwość zapisu przez użytkownika `deploy` oraz prawidłowe tryby chronionych plików. Następnie wykonano rzeczywisty backup, test integralności, odtworzenie plików i pełny import dumpa do tymczasowej bazy.

Automatyzacja została zakończona: backup działa codziennie o 02:30, monitoring co 5 minut, a ostatni automatyczny wpis miał status `OK`. Kod, skrypty i dokumentację zapisano na GitHubie w commicie `d6790f0` oraz zsynchronizowano do `/home/deploy/Codex/ProjektDotacje`.

Kolejna sesja powinna rozpocząć właściwy fundament MVP: GitHub Actions i zasady pracy z `main`, docelowy frontend, rozbudowę FastAPI, SQLAlchemy/Alembic, pierwsze migracje oraz worker oparty na Redis. Zewnętrzny backup i zewnętrzne alarmy pozostają obowiązkowe przed betą.

## 22. Zatwierdzenie zakresu produktu MVP-0

Użytkownik zatwierdził publiczny portal bez logowania oraz przesunięcie kont, profili nieruchomości, subskrypcji, matchingu, poczty i prywatnych dokumentów do MVP-1. Pierwszym obszarem jest województwo mazowieckie, ze szczególnym uwzględnieniem Gminy Nadarzyn.

Jako pierwsze źródło produkcyjne wybrano WFOŚiGW w Warszawie i program Czyste Powietrze. Drugim źródłem jest regulamin Gminy Nadarzyn dotyczący wymiany źródła ciepła, który ma sprawdzać rozpoznawanie zakończonego naboru. Do kolejki P1 dodano harmonogram NFOŚiGW, Moje Ciepło, przydomowe magazyny energii, Moją Elektrownię Wiatrową oraz Ciepłe Mieszkanie.

Ustalono miesięczny limit OpenRouter 10 USD, ostrzeżenia przy 5 i 8 USD oraz twarde zatrzymanie niekrytycznych wywołań po osiągnięciu limitu. Klucz będzie wpisany później wyłącznie jako `OPENROUTER_API_KEY` na VPS.

Zweryfikowano oficjalne źródła i zapisano wymagania w `MVP0_PRODUCT_REQUIREMENTS.md`, a adresy, statusy początkowe i reguły wiarygodności w `SOURCE_CATALOG.md`.

W oficjalnych materiałach Nadarzyna wykryto konflikt wersji: starsza podstrona nadal podaje 60% i maksymalnie 5000 zł na podstawie uchwały z 2021 r., natomiast regulamin z 2026 r. podaje 100% i maksymalnie 6000 zł. Przypadek zapisano jako obowiązkowy test wersjonowania, pierwszeństwa nowszego aktu i kolejki REVIEW.

## 23. Pierwszy sprint aplikacyjny MVP-0

Na polecenie użytkownika rozpoczęto implementację właściwego MVP. Przygotowano asynchroniczne FastAPI, konfigurację maskującą sekrety, logowanie JSON, SQLAlchemy 2, Alembic oraz strukturalny model źródeł, snapshotów, lokalizacji, programów, dokumentów, wywołań LLM, zadań REVIEW i audytu.

Dodano publiczne endpointy zdrowia, gotowości, listy oraz szczegółów programu. Lista obsługuje podstawowe filtry MVP-0. Mechanizm statusu otrzymał test Nadarzyna potwierdzający `closed` po 31.07.2026. Łącznie siedem testów oraz lint przechodzą lokalnie.

Pierwszą migrację sprawdzono na SQLite, a następnie w odseparowanym projekcie Docker na VPS z PostgreSQL 16. Potwierdzono `upgrade`, brak rozbieżności Alembic, `downgrade`, ponowny `upgrade`, zdrowe API i seed siedmiu źródeł. Izolowane kontenery, wolumeny i katalog testowy usunięto po walidacji; produkcyjna baza nie została zmieniona.

Workflow GitHub Actions dla commita `b78e4ff` zakończył się sukcesem. Przed wdrożeniem wykonano świeży backup, następnie zsynchronizowano dokładną zawartość commita, ustawiono uzgodnione limity OpenRouter 1/5/8/10 USD i uruchomiono migrację produkcyjną.

Po wdrożeniu potwierdzono migrację `4167552a1c92`, API `0.2.0`, zdrowe kontenery, gotowość PostgreSQL, siedem zasianych źródeł i działającą pustą listę publiczną. Pusta lista jest oczekiwana, ponieważ żaden program nie może być publikowany przed REVIEW.

Wykonano backup po migracji jako snapshot `0e57cdc7`. Restic nie wykrył błędów, suma dumpa była poprawna, pełne odtworzenie do tymczasowej bazy przeszło, a końcowy monitoring zwrócił `OK`.

## 24. Sprint crawlera źródeł

Użytkownik polecił rozpocząć kolejny sprint. Zakres obejmuje pobieranie HTML i PDF bez LLM, warunkowe żądania ETag/Last-Modified, SHA-256, normalizację treści, trwałe snapshoty, diff oraz automatyczne kierowanie zmian do kolejki REVIEW.

Jako pierwsze źródła wykonawcze pozostają WFOŚiGW Warszawa / Czyste Powietrze oraz regulamin Gminy Nadarzyn. Crawler ma działać w odseparowanym zadaniu Docker jako nieuprzywilejowany użytkownik, zapisywać pliki w drzewie objętym backupem i uruchamiać się co sześć godzin. OpenRouter nie jest częścią tego sprintu i klucz API pozostaje niewymagany.

Zaimplementowano adapter HTTP z retry, timeoutem, limitem odpowiedzi, identyfikatorem aplikacji, redirectami i warunkowymi nagłówkami. HTML jest oczyszczany z elementów wykonywalnych i normalizowany wraz z linkami, a tekst PDF jest ekstrahowany przez `pypdf`. System zapisuje surowy SHA-256, hash treści znormalizowanej, rozmiar, metadane HTTP, snapshot i opcjonalny unified diff. Pierwsza treść oraz późniejsze zmiany trafiają do REVIEW bez automatycznej publikacji.

Migrację `a8d2f6c4b901` wdrożono po backupie `1d863da0`. API 0.3.0 oraz wszystkie stałe kontenery wróciły do stanu healthy, a harmonogram crawlera został dodany na minutę 15 co sześć godzin.

Pierwsze pobranie Nadarzyna zakończyło się sukcesem i zapisało PDF 360899 B. Kolejne żądanie wykorzystało ETag i otrzymało HTTP 304 bez nowego REVIEW. Pierwsza próba WFOŚiGW ujawniła brak certyfikatu pośredniego po stronie serwera. Nie wyłączono TLS; do standardowego magazynu dodano publiczny certyfikat `home pl OV TLS G2 R35 CA`, pobrany z adresu AIA i zweryfikowany odciskiem SHA-256. Następne pobranie WFOŚiGW zakończyło się sukcesem, a kolejne miało identyczne hashe i nie utworzyło duplikatu REVIEW.

Stan końcowy to cztery rekordy sprawdzeń, dwie rzeczywiste wersje źródeł i dwa oczekujące zadania REVIEW. Snapshoty źródłowe znajdują się w `/opt/dotacje-ai/data/documents/sources`. Backup `81688635` przeszedł kontrolę Restic, odtworzenie plików, kontrolę sum i pełny import PostgreSQL do bazy tymczasowej. Dokumentację techniczną zapisano w `CRAWLER_PIPELINE.md`.

## 25. Plan Sprintu 03 — ekstrakcja i REVIEW

Użytkownik poprosił o zaplanowanie kolejnego sprintu. Przyjęto cel przeprowadzenia pełnego przepływu od istniejącego snapshotu przez walidowaną ekstrakcję OpenRouter i ręczny REVIEW do osobnej, jawnej publikacji programu.

Ze względów bezpieczeństwa panel webowy administratora nie będzie w tym sprincie wystawiany bez uwierzytelnienia. Operacje list, show, approve, reject i publish zostaną przygotowane jako CLI dostępne przez konto `deploy` i SSH. Publikacja nie będzie skutkiem samego zatwierdzenia.

Plan obejmuje wersjonowany schemat danych i dowodów, ekstrakcję deterministyczną, budżety OpenRouter 1/5/8/10 USD, benchmark do 0,50 USD, idempotencję, audyt, test konfliktu Nadarzyna oraz pierwszą kontrolowaną publikację. Szczegóły zapisano w `SPRINT_03_EXTRACTION_REVIEW_PLAN.md`.

## 26. Realizacja Sprintu 03 i benchmark OpenRouter

Zaimplementowano migrację `c4e7b9a210f3`, wersjonowany schemat ekstrakcji, deterministyczne reguły, kontrolę kosztów, klienta OpenRouter oraz prywatny workflow REVIEW przez SSH. Operacje approve i publish są rozdzielone, a wynik LLM nigdy nie jest publikowany automatycznie.

Pierwszy test produkcyjny wykrył fałszywą deterministyczną interpretację historycznych treści WFOŚiGW. Bramkę poprawiono: złożone strony zawsze wymagają LLM, natomiast samymi regułami może przejść tylko jawnie dopuszczone, stabilne źródło. Następnie dostosowano ścisły JSON Schema do rzeczywistych ograniczeń OpenRouter/OpenAI: usunięto nieobsługiwany parametr `temperature`, wartości domyślne, `format: uri` oraz wzorce Decimal, a pola liczbowe ograniczono do liczb.

Użytkownik wkleił klucz OpenRouter do rozmowy. Na jego jawne polecenie użyto go tymczasowo na VPS, ale oznaczono jako skompromitowany i wymagający rotacji. Wartość klucza nie trafiła do Git, dokumentacji ani wyników terminala.

Benchmark zakończył się trzema wynikami `ready_for_review`. Nadarzyn został rozpoznany jako zakończony 31.07.2026, z kwotą 6000 PLN i poziomem 100%. Dwa snapshoty WFOŚiGW zostały oznaczone jako otwarte i pozostają do ręcznego porównania. Łączny zapisany koszt wyniósł 0,026836 USD; ponowne uruchomienie nie zwiększyło kosztu.

Nic nie zostało zatwierdzone ani opublikowane. Publiczne API nadal zwraca pustą listę. API 0.4.0, HTTPS i pięć kontenerów są zdrowe. Snapshot Restic `8fc846f5` przeszedł kontrolę integralności, sumę SHA-256 i pełny import do tymczasowej bazy. Najbliższe działania to rotacja klucza, ręczny REVIEW i osobna decyzja o pierwszej publikacji.

## 27. Plan Sprintu 04 — pierwsza publikacja i portal publiczny

Użytkownik polecił przygotować kolejny sprint i zdecydował, że rotacja ujawnionego klucza OpenRouter nastąpi na samym końcu. Do czasu rotacji przyjęto zakaz nowych wywołań LLM; Sprint 04 wykorzysta wyłącznie trzy zapisane wyniki `ready_for_review`.

Plan rozpoczyna się od ręcznej decyzji dla Nadarzyna i dwóch wyników WFOŚiGW, następnie obejmuje rozszerzenie publicznego API, zastąpienie technicznego frontendu aplikacją Next.js, listę dotacji, filtry, karty programów, strony lokalizacji i kategorii, SEO, dostępność, testy, wdrożenie oraz pierwszą osobną publikację. Panel administratora pozostaje prywatnym CLI przez SSH; publiczny panel bez uwierzytelnienia nie powstanie.

Ostatnim etapem będzie unieważnienie starego klucza, bezpieczne wpisanie nowego bezpośrednio na VPS i kontrola, że stary klucz przestał działać. Szczegółowy zakres i kryteria odbioru zapisano w `SPRINT_04_PUBLIC_PORTAL_PLAN.md`.

## 24 września 2026 — rozpoczęcie Sprintu 04 i portal publiczny

Na polecenie użytkownika rozpoczęto Sprint 04 bez natychmiastowej rotacji ujawnionego klucza OpenRouter. Nie wykonano żadnego nowego wywołania LLM i nie kopiowano wartości klucza.

Rozszerzono publiczne API o dokumenty i zatwierdzoną historię wersji. Dodano test potwierdzający, że nieopublikowane programy nie są widoczne. Placeholder Node zastąpiono frontendem Next.js 16.3.6 z App Routerem, TypeScript, filtrowaną listą, kartą programu, stronami Mazowsza, Nadarzyna i kategorii, stanami pustym/błędu/404 oraz podstawowym SEO. Workflow GitHub Actions rozbudowano o typecheck i produkcyjny build frontendu.

Lokalnie przeszły Ruff, 23 testy API, typecheck i build. GitHub Actions run 22 zakończył się sukcesem. Przed wdrożeniem wykonano szyfrowany backup Restic `570de219`. Na VPS wdrożono commit `99f22c7`; API raportuje wersję `0.5.0`, pięć kontenerów jest zdrowych, a wszystkie publiczne trasy MVP zwracają HTTP 200. Lista pozostaje pusta, ponieważ nie wykonano automatycznego approve ani publish.

Przejrzano trzy zadania REVIEW. Rekomendacja: zatwierdzić Nadarzyn, zatwierdzić pełniejszy wynik bazowy Czystego Powietrza i odrzucić jego słabszy duplikat. Identyfikatory, uzasadnienia i bezpieczna kolejność operacji zostały zapisane w `SPRINT_04_REVIEW_DECISION.md`. Dalsza publikacja czeka na jawną decyzję właściciela.

Użytkownik zatwierdził rekomendację. Wykonano `approve` dla Nadarzyna i pełniejszego wyniku Czystego Powietrza oraz `reject` dla duplikatu. Kontrola przed publikacją potwierdziła po jednej wersji każdego programu, jeden dokument Nadarzyna, trzy dokumenty Czystego Powietrza oraz komplet wpisów audit log. Publiczne API nadal zwracało wtedy `404` dla obu kart.

Następnie wykonano dwie osobne operacje `publish`. Lista publiczna zawiera dwa programy, filtry Nadarzyna i Czystego Powietrza działają, a landing, lista, strony lokalizacji i obie karty zwracają HTTP 200. Po publikacji wykonano backup `bdb9f3f2`; kontrola Restic, suma SHA-256 i pełne odtworzenie do tymczasowej bazy zakończyły się sukcesem. Klucz OpenRouter nie został użyty ani zmieniony i nadal czeka na końcową rotację.

## 28. Rozszerzenie kart o warunki i formularze

Użytkownik poprosił, aby portal pobierał więcej danych i przedstawiał warunki przyznania dotacji, beneficjentów, kwoty, ważne informacje oraz komplet oficjalnych formularzy potrzebnych do złożenia wniosku. Analiza wykazała, że istniejący model przechowywał głównie opis, pojedynczą kwotę i ogólne linki, mimo że crawler zachowywał bogatszą treść źródłową.

Wprowadzono `extraction-v2` z sekcją `details`, wskazaniami źródeł i typami zasobów aplikacyjnych. Prompt OpenRouter ma teraz wyodrębniać praktyczne wnioski bez zgadywania i bez tworzenia nieistniejących linków. Wynik AI nadal nie może opublikować się automatycznie. Publiczny frontend otrzymał osobne sekcje dla beneficjentów, warunków, wariantów finansowania, ograniczeń, kroków, wymaganych dokumentów oraz formularzy.

Na podstawie oficjalnych dokumentów uzupełniono obie karty. Nadarzyn zawiera wniosek, oświadczenie, regulamin, uchwałę i stronę gminy. Czyste Powietrze zawiera GWD, instrukcję WOD, instrukcję złożenia wniosku, aktualne dokumenty i załącznik z limitami kosztów. Oba programy otrzymały zatwierdzoną wersję 2.

Commit `12833a7` przeszedł GitHub Actions run 27. Lokalnie przeszły Ruff, 24 testy API i typecheck; build produkcyjny frontendu przeszedł w CI i na VPS. Po wdrożeniu pięć kontenerów jest zdrowych, API i obie karty odpowiadają przez HTTPS, a logi nie zawierają błędów. Wbudowana kontrola graficzna przeglądarki nie była dostępna, dlatego zweryfikowano build, API i wyrenderowany HTML. Backup `0049f91e` przeszedł kontrolę Restic, sum i pełne odtworzenie PostgreSQL. Nie wykonano nowego wywołania OpenRouter ani nie zmieniono klucza.

## 29. Zamknięcie braków MVP-0

Użytkownik polecił wykonać wszystkie brakujące zadania MVP-0 bez zatrzymywania się po kolejne potwierdzenia. Rozszerzono API i frontend o pełne filtry, sortowanie, paginację, trasę powiatu, canonical i dynamiczną sitemap. Dodano chroniony Basic Auth panel administratora, rate limiting i nagłówki bezpieczeństwa.

Wprowadzono monitor dokumentów: pobieranie, SHA-256, niezmienne wersje, dostępność i historię kontroli. Potwierdzone 404 oznacza dokument wycofany, natomiast chwilowy błąd sieci nie kasuje ostatniego poprawnego stanu. Dodano harmonogram pipeline crawler → ekstrakcja, codzienną kontrolę dokumentów i godzinną kontrolę statusów z obowiązkowym REVIEW.

Źródło Moje Ciepło przeszło pełny przepływ: crawl, snapshot, OpenRouter, ręczne porównanie z oficjalnymi informacjami, approve i osobny publish. Publiczna karta zawiera termin 26.02.2027, warianty 30%/45%, limit 21 000 zł, warunki EP, listę załączników, GWD i oficjalne wzory. Portal zawiera trzy opublikowane programy, a kolejka REVIEW została opróżniona po odrzuceniu redundantnego wyniku mieszającego historyczne wersje Czystego Powietrza.

Aktualny łańcuch TLS serwisu Czyste Powietrze nie był kompletny. Dodano wskazany przez certyfikat pośredni `nazwaSSL DV TLS G2 E29 CA` bez wyłączania weryfikacji. Dwa stare PDF-y zwracające 404 usunięto z zasobów karty i zastąpiono aktualnym oficjalnym katalogiem dokumentów edycji od 20.07.2026.

GitHub Actions potwierdził pełny pakiet 26 testów API, migrację PostgreSQL, lint, typecheck i build Next.js. Produkcja raportuje API 0.6.0, pięć zdrowych kontenerów, działający HTTPS, panel 401/200 zależnie od uwierzytelnienia, aktywne nagłówki bezpieczeństwa oraz monitoring `OK`. Powtarzalny skrypt wydania wykonuje backup, pobiera dokładny zielony commit, wdraża, migruje, przeładowuje Caddy, seeduje źródła i instaluje cron.

Klucz OpenRouter pozostaje tymczasowy i ujawniony. Jego bezpieczna rotacja wymaga zalogowania właściciela do OpenRouter albo osobnego Management API Key; nowej wartości nie wolno przekazywać w rozmowie. Zewnętrzny backup i zewnętrzne alarmy pozostają obowiązkowym zakresem przed betą, zgodnie z wcześniejszą decyzją właściciela, a nie brakiem MVP-0.

Podczas końcowego odbioru wykryto cztery nowe zadania REVIEW dla Czystego Powietrza. Analiza zapisanych diffów wykazała, że jedyną zmianą był dynamiczny licznik odwiedzin strony WFOŚiGW. Wszystkie cztery zadania odrzucono bez zmiany danych publicznych. Crawler otrzymał filtr licznika i porównanie zgodne ze starszym formatem snapshotu, dzięki czemu pierwsze pobranie po wdrożeniu również nie generuje fałszywej zmiany.

Poprawka `920cc22` przeszła GitHub Actions run 35 z 28 testami API. Po wdrożeniu wykonano dwa pobrania kontrolne: oba zwróciły `unchanged` i `review_created=false`, a koszt OpenRouter pozostał na poziomie `0.059997 USD`. Końcowy skrypt odbiorowy potwierdził trzy programy, zero oczekujących REVIEW, zero niedostępnych dokumentów, panel 401/200, nagłówki bezpieczeństwa i pięć zdrowych kontenerów. Monitoring zwrócił `OK`. Snapshot Restic `09097500` przeszedł kontrolę pakietów, odtworzenie 115 plików i katalogów, SHA-256 dumpa oraz pełny import PostgreSQL do bazy tymczasowej.
