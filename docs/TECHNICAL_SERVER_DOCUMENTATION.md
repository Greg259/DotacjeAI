# DotacjeAI - dokumentacja techniczna serwera

Stan na: 2026-09-22 po aktualizacji i kontrolowanym restarcie.

## 1. Przeznaczenie

VPS stanowi pojedynczy host środowiska MVP DotacjeAI. Uruchamia reverse proxy, frontend, API, PostgreSQL i Redis. Analiza LLM będzie wykonywana przez zewnętrzne API OpenRouter - na serwerze nie jest uruchamiany lokalny model językowy.

## 2. System i zasoby

| Element | Stan |
|---|---|
| Dostawca | Time4VPS |
| Hostname | `5qq8.l.time4vps.cloud` |
| System | Ubuntu 24.04.5 LTS |
| Kernel | `6.8.0-139-generic` |
| Wirtualizacja | KVM |
| CPU | 3 vCPU |
| RAM | 7,8 GiB; po uruchomieniu usług około 7,1 GiB dostępne |
| Swap | 2 GiB, plik `/swapfile`, `vm.swappiness=10` |
| Dysk | 99 GiB; około 74 GiB wolne po wdrożeniu |
| Strefa czasowa | `Europe/Warsaw` |
| Synchronizacja czasu | NTP aktywne |

System został zaktualizowany. W czasie ostatniej weryfikacji liczba oczekujących aktualizacji wynosiła 0.

## 3. Oprogramowanie bazowe

| Komponent | Wersja / stan |
|---|---|
| Docker Engine | 29.1.3 |
| Docker Compose | 2.40.3 |
| Caddy | 2.11.4 |
| UFW | aktywny |
| Fail2ban | aktywny, jail `sshd` |
| AppArmor | aktywny |
| unattended-upgrades | aktywne |

## 4. Konta i dostęp

### `root`

Bezpośrednie logowanie `root` przez SSH jest wyłączone. Ujawnione podczas pierwszej konfiguracji hasło zostało zmienione 2026-09-23. Konto pozostaje dostępne wyłącznie lokalnie przez przetestowaną Emergency Console Time4VPS lub przez `sudo` użytkownika `deploy`.

### `deploy`

Utworzono użytkownika `deploy` należącego do grup:

- `deploy`,
- `sudo`,
- `docker`,
- `users`.

Konto ma osobne hasło lokalne do `sudo` oraz publiczny klucz RSA 4096 w `authorized_keys`. Klucz prywatny jest przechowywany wyłącznie na komputerze administratora i chroniony passphrase. Logowanie kluczem, `sudo` oraz Docker zostały sprawdzone w nowej sesji.

Członkostwo w grupie `docker` daje w praktyce uprawnienia administracyjne.

Efektywne ustawienia SSH:

- `PubkeyAuthentication yes`,
- `PasswordAuthentication no`,
- `KbdInteractiveAuthentication no`,
- `PermitRootLogin no`,
- `PermitEmptyPasswords no`,
- `MaxAuthTries 3`,
- `X11Forwarding no`.

Plik: `/etc/ssh/sshd_config.d/00-dotacje-ai-hardening.conf`. Przed zmianą zachowano kopie konfiguracji z oznaczeniem `before-dotacje-ai-20260923`. Usługa `ssh` jest aktywna i włączona przy starcie systemu.

## 5. Firewall i porty

Domyślna polityka UFW:

- połączenia przychodzące: blokowane,
- połączenia wychodzące: dozwolone.

Publiczne reguły:

| Port | Protokół | Przeznaczenie |
|---:|---|---|
| 22 | TCP | SSH |
| 80 | TCP | HTTP / Caddy |
| 443 | TCP i UDP | przyszłe HTTPS oraz HTTP/3 |

PostgreSQL `5432`, Redis `6379`, API `8000` i frontend `3000` nie są publikowane bezpośrednio na hoście.

## 6. Fail2ban

Aktywny jest jail `sshd` z parametrami:

- maksymalnie 5 nieudanych prób,
- okno obserwacji 10 minut,
- blokada na 1 godzinę,
- akcja blokująca przez UFW,
- źródło logów: systemd journal.

Konfiguracja: `/etc/fail2ban/jail.d/dotacje-ai-sshd.local`.

## 7. Struktura plików

```text
/opt/dotacje-ai/
|-- app/                     # bieżący kod i Compose
|   |-- apps/api/
|   |-- apps/frontend/
|   |-- docs/
|   `-- infra/
|-- data/
|   |-- documents/           # archiwum dokumentów programów
|   |-- uploads/             # przyszłe prywatne pliki użytkowników
|   |-- exports/
|   `-- caddy/
|-- backups/
|   |-- postgres/
|   `-- files/
|-- secrets/
|   `-- app.env              # prawa 600, poza repozytorium
`-- logs/
```

Dokumentacja operatorska znajduje się również w `/home/deploy/Codex/ProjektDotacje`.

## 8. Architektura Docker Compose

```text
Internet
   |
   v
Caddy :80/:443
   |-- /api/* -> FastAPI :8000
   `-- pozostałe -> frontend :3000

FastAPI
   |-- PostgreSQL :5432
   `-- Redis :6379
```

### Kontenery

| Usługa | Obraz | Limit pamięci | CPU | Healthcheck |
|---|---|---:|---:|---|
| `caddy` | `caddy:2-alpine` | 256 MB | 0,25 | `/health` |
| `frontend` | lokalny obraz Node 20 Alpine | 512 MB | 0,50 | `/health` |
| `api` | lokalny obraz Python 3.11 / FastAPI | 768 MB | 0,75 | `/api/health` |
| `postgres` | `postgres:16-alpine` | 2 GB | 1,00 | `pg_isready` |
| `redis` | `redis:7-alpine` | 512 MB | 0,25 | `redis-cli ping` |

Wszystkie kontenery mają `restart: unless-stopped`, limity logów i przeszły test automatycznego powrotu po restarcie VPS.

### Sieci

- `dotacje-ai_edge` - Caddy, frontend i API.
- `dotacje-ai_backend` - sieć wewnętrzna API, PostgreSQL i Redis; oznaczona jako `internal`.

### Wolumeny

- `dotacje-ai_caddy_data`,
- `dotacje-ai_caddy_config`,
- `dotacje-ai_postgres_data`,
- `dotacje-ai_redis_data`.

## 9. Endpointy techniczne

| Endpoint | Oczekiwany wynik |
|---|---|
| `GET /` | techniczna strona DotacjeAI |
| `GET /health` | `200 ok` |
| `GET /api/health` | `{"status":"ok","service":"api"}` |

Caddy obsługuje domenę produkcyjną `dotacjeai.eu` i automatyczne certyfikaty TLS. Ruch HTTP jest automatycznie przekierowywany do HTTPS. `www.dotacjeai.eu` ma własny certyfikat i jest przekierowywane na domenę główną.

## 10. Sekrety

Plik produkcyjny: `/opt/dotacje-ai/secrets/app.env`.

- katalog `secrets`: prawa 700,
- plik `app.env`: prawa 600,
- właściciel: `deploy`,
- hasła PostgreSQL i Redis zostały wygenerowane losowo,
- `OPENROUTER_API_KEY` jest tymczasowo ustawiony w chronionym pliku `app.env`; ponieważ został ujawniony w rozmowie, wymaga pilnej rotacji,
- prawdziwe sekrety nie znajdują się w dokumentacji ani `.env.example`.

## 11. Zarządzanie

```bash
cd /opt/dotacje-ai/app/infra

docker compose --env-file /opt/dotacje-ai/secrets/app.env ps
docker compose --env-file /opt/dotacje-ai/secrets/app.env logs --tail=200
docker compose --env-file /opt/dotacje-ai/secrets/app.env up -d --build
docker compose --env-file /opt/dotacje-ai/secrets/app.env restart
```

## 12. Stan implementacji aplikacji

Obecne środowisko jest szkieletem infrastrukturalnym, a nie gotowym produktem:

- frontend jest technicznym placeholderem Node, nie docelowym Next.js,
- FastAPI udostępnia obecnie tylko healthcheck,
- baza PostgreSQL działa, ale nie ma jeszcze migracji ani tabel domenowych,
- Redis działa, ale nie ma jeszcze workera i schedulera,
- nie ma jeszcze crawlera, panelu administratora, kont użytkowników ani alertów,
- OpenRouter nie jest wywoływany, ponieważ klucz API nie został ustawiony.

## 13. Backup i odtwarzanie

Utworzono katalogi backupów, ale nie skonfigurowano jeszcze:

- automatycznego `pg_dump`,
- backupu dokumentów,
- szyfrowania kopii,
- wysyłki do zewnętrznego storage,
- retencji,
- testu odtworzenia.

Do czasu wykonania tych punktów backup aplikacyjny należy uznawać za niewdrożony.

## 14. Znane ryzyka i zadłużenie

1. Logowanie `root` hasłem nadal jest dostępne.
2. Hasło roota zostało wcześniej przekazane w rozmowie i powinno zostać zmienione.
3. HSTS nie jest jeszcze włączony; należy go aktywować dopiero po okresie stabilnej pracy HTTPS.
4. Brak zewnętrznego backupu i monitoringu dostępności.
5. Około 6,7 GB starych obrazów Docker jest potencjalnie odzyskiwalne, ale nie zostało usunięte bez dodatkowej weryfikacji.
6. Sekrety są w pliku środowiskowym; docelowo można rozważyć Docker secrets lub zewnętrzny secret manager.
