# Backup i monitoring DotacjeAI

Aktualizacja: 2026-09-23.

## Przyjęte rozwiązanie

- backup MVP: `restic` z zaszyfrowanym repozytorium lokalnym na VPS,
- szyfrowanie: wykonywane przez Restic przed zapisaniem danych w repozytorium,
- zakres: PostgreSQL oraz katalogi `documents`, `uploads` i `exports`,
- retencja: 7 kopii dziennych, 5 tygodniowych i 12 miesięcznych,
- monitoring wewnętrzny: HTTPS, API, pięć kontenerów, dysk i wiek backupu,
- monitoring lokalny: zadanie uruchamiane co 5 minut i zapisujące wynik do logu,
- backup zewnętrzny: odłożony do etapu przed betą; rekomendowany Cloudflare R2, Backblaze B2 albo storage dostawcy VPS.

Sekrety aplikacji nie są kopiowane jako jawne pliki. Hasła, klucze i hasło Restic muszą być dodatkowo przechowywane w menedżerze haseł właściciela. Bez nich odtworzenie zaszyfrowanej kopii nie będzie możliwe.

## Pliki produkcyjne

- skrypt backupu: `/opt/dotacje-ai/app/server/backup_dotacje_ai.sh`,
- konfiguracja lokalnego repozytorium: `/opt/dotacje-ai/app/server/configure_local_backup.sh`,
- test odtworzenia: `/opt/dotacje-ai/app/server/verify_backup.sh`,
- instalacja harmonogramu: `/opt/dotacje-ai/app/server/install_user_cron.sh`,
- kontrola lokalna: `/opt/dotacje-ai/app/server/monitor_health.sh`,
- konfiguracja Restic: `/opt/dotacje-ai/secrets/restic.env`,
- hasło szyfrowania: `/opt/dotacje-ai/secrets/restic-password`,
- konfiguracja heartbeat: `/opt/dotacje-ai/secrets/monitoring.env`,
- logi: `/opt/dotacje-ai/backups/logs/`.

## Aktywacja lokalnego backupu MVP

1. Uruchomić `/opt/dotacje-ai/app/server/configure_local_backup.sh`.
2. Skrypt generuje losowe hasło, zapisuje je z trybem `0600` i inicjalizuje repozytorium w `/opt/dotacje-ai/backups/restic-repository`.
3. Uruchomić ręcznie `backup_dotacje_ai.sh`.
4. Uruchomić `verify_backup.sh`, który odtwarza pliki i importuje dump do osobnej, tymczasowej bazy PostgreSQL.
5. Uruchomić `install_user_cron.sh`, aby włączyć harmonogram.

Hasło Restic należy przed betą umieścić w menedżerze haseł właściciela. Lokalna kopia na tym samym VPS nie chroni przed awarią dysku, usunięciem VPS ani przejęciem całego serwera.

## Harmonogram

Po poprawnym teście dodać do crontab użytkownika `deploy`:

```cron
30 2 * * * /opt/dotacje-ai/app/server/backup_dotacje_ai.sh >> /opt/dotacje-ai/backups/logs/backup.log 2>&1
*/5 * * * * /opt/dotacje-ai/app/server/monitor_health.sh >> /opt/dotacje-ai/backups/logs/monitor.log 2>&1
```

Harmonogram należy uruchomić dopiero po poprawnym ręcznym backupie i teście odtworzenia.

## Monitoring i przyszłe alarmy

W MVP skrypt działa lokalnie co 5 minut i zapisuje wyniki do `/opt/dotacje-ai/backups/logs/monitor.log`. Przed betą w Better Stack należy utworzyć monitor HTTP dla `https://dotacjeai.eu/health`, drugi dla `https://dotacjeai.eu/api/health` oraz heartbeat z oczekiwanym sygnałem co 5 minut. Adres heartbeat należy wpisać bezpośrednio do `/opt/dotacje-ai/secrets/monitoring.env`.

Skrypt wysyła heartbeat dopiero po przejściu wszystkich kontroli, więc brak sygnału oznacza awarię aplikacji, kontenera, dysku albo backupu.

## Test okresowy

Co najmniej raz w miesiącu uruchomić `verify_backup.sh`. Skrypt wykonuje `restic check`, odtwarza najnowszy snapshot do katalogu tymczasowego, sprawdza sumę SHA-256 i wykonuje pełny import PostgreSQL do osobnej, tymczasowej bazy.
