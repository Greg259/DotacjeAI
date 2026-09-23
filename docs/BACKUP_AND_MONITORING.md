# Backup i monitoring DotacjeAI

Aktualizacja: 2026-09-23.

## Przyjęte rozwiązanie

- backup: `restic` i prywatny bucket Cloudflare R2,
- szyfrowanie: wykonywane po stronie Restic przed wysłaniem,
- zakres: PostgreSQL oraz katalogi `documents`, `uploads` i `exports`,
- retencja: 7 kopii dziennych, 5 tygodniowych i 12 miesięcznych,
- monitoring wewnętrzny: HTTPS, API, pięć kontenerów, dysk i wiek backupu,
- monitoring zewnętrzny: Better Stack; alternatywnie HetrixTools.

Sekrety aplikacji nie są kopiowane jako jawne pliki. Hasła, klucze i hasło Restic muszą być dodatkowo przechowywane w menedżerze haseł właściciela. Bez nich odtworzenie zaszyfrowanej kopii nie będzie możliwe.

## Pliki produkcyjne

- skrypt backupu: `/opt/dotacje-ai/app/server/backup_dotacje_ai.sh`,
- test odtworzenia: `/opt/dotacje-ai/app/server/verify_backup.sh`,
- kontrola lokalna: `/opt/dotacje-ai/app/server/monitor_health.sh`,
- konfiguracja Restic: `/opt/dotacje-ai/secrets/restic.env`,
- hasło szyfrowania: `/opt/dotacje-ai/secrets/restic-password`,
- konfiguracja heartbeat: `/opt/dotacje-ai/secrets/monitoring.env`,
- logi: `/opt/dotacje-ai/backups/logs/`.

## Aktywacja Cloudflare R2

1. W Cloudflare utworzyć prywatny bucket, np. `dotacje-ai-backup`.
2. Utworzyć token R2 ograniczony do odczytu i zapisu tego jednego bucketa.
3. Na VPS skopiować `server/restic.env.example` do `/opt/dotacje-ai/secrets/restic.env`.
4. Wprowadzić Account ID, nazwę bucketa oraz klucze bezpośrednio na VPS. Nie przesyłać ich w czacie i nie commitować.
5. Wygenerować długie, losowe hasło Restic i zapisać je jednocześnie w pliku `restic-password` oraz menedżerze haseł.
6. Nadać obu plikom właściciela `deploy:deploy` i tryb `0600`.
7. Załadować zmienne i wykonać jednorazowo `restic init`.
8. Uruchomić ręcznie backup, a następnie `verify_backup.sh`.

## Harmonogram

Po poprawnym teście dodać do crontab użytkownika `deploy`:

```cron
30 2 * * * /opt/dotacje-ai/app/server/backup_dotacje_ai.sh >> /opt/dotacje-ai/backups/logs/backup.log 2>&1
*/5 * * * * /opt/dotacje-ai/app/server/monitor_health.sh >> /opt/dotacje-ai/backups/logs/monitor.log 2>&1
```

Nie uruchamiać harmonogramu backupu przed skonfigurowaniem i przetestowaniem R2.

## Monitoring zewnętrzny

W Better Stack utworzyć monitor HTTP dla `https://dotacjeai.eu/health`, drugi dla `https://dotacjeai.eu/api/health` oraz heartbeat z oczekiwanym sygnałem co 5 minut. Adres heartbeat wpisać bezpośrednio do `/opt/dotacje-ai/secrets/monitoring.env`.

Skrypt wysyła heartbeat dopiero po przejściu wszystkich kontroli, więc brak sygnału oznacza awarię aplikacji, kontenera, dysku albo backupu.

## Test okresowy

Co najmniej raz w miesiącu uruchomić `verify_backup.sh`. Skrypt wykonuje `restic check`, odtwarza najnowszy snapshot do katalogu tymczasowego i sprawdza sumę SHA-256 dumpa. Pełny test importu PostgreSQL do osobnej bazy należy wykonywać przed istotnym wdrożeniem oraz co kwartał.
