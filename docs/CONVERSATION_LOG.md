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
