# DotacjeAI — przekazanie sesji do dalszej pracy

Aktualizacja: 2026-09-30.

Ten dokument jest krótkim punktem startowym dla nowej sesji Codexa. Pełna chronologia znajduje się w `docs/CONVERSATION_LOG.md`, aktualny stan techniczny w `docs/IMPLEMENTATION_STATUS.md`, a plany w `docs/NEXT_STEPS_PLAN.md` i `docs/MVP1_ROADMAP.md`.

## Jak rozpocząć kolejną sesję

1. Otwórz w Codexie repozytorium:

   `D:\Codex\DotacjeAI`

2. W nowej rozmowie wklej:

   > Przeczytaj w całości `docs/CONTINUE_SESSION.md`, a następnie potrzebne sekcje `docs/IMPLEMENTATION_STATUS.md`, `docs/CONVERSATION_LOG.md` i `docs/NEXT_STEPS_PLAN.md`. Sprawdź `git status`, aktualny commit, GitHub Actions i stan produkcji. Kontynuuj projekt DotacjeAI od istniejącego stanu; nie twórz infrastruktury od początku i nie nadpisuj istniejących zmian.

3. Następnie dopisz konkretne nowe zadanie, np.:

   > Następne zadanie: przygotuj i wykonaj kolejny sprint produkcyjny.

Na drugim komputerze należy najpierw sklonować `git@github.com:Greg259/DotacjeAI.git`, skonfigurować własny klucz SSH użytkownika i otworzyć sklonowany katalog w Codexie. Nie należy kopiować prywatnego klucza z pierwszego komputera.

## Lokalizacje

- lokalne repozytorium: `D:\Codex\DotacjeAI`
- GitHub: `git@github.com:Greg259/DotacjeAI.git`
- produkcja: `https://dotacjeai.eu`
- aplikacja na VPS: `/opt/dotacje-ai/app`
- sekrety na VPS: `/opt/dotacje-ai/secrets` — nie kopiować do Git ani dokumentacji
- dane i dokumenty: `/opt/dotacje-ai/data`
- backupy: `/opt/dotacje-ai/backups`
- kopia dokumentacji dla Codexa na VPS: `/home/deploy/Codex/ProjektDotacje`
- konto wdrożeniowe SSH: `deploy@185.69.52.106`
- lokalny klucz używany na tym komputerze: `C:\Users\grzeg\.ssh\id_rsa_time4vps`

Przykładowe wejście na VPS z PowerShell:

```powershell
ssh -i "$env:USERPROFILE\.ssh\id_rsa_time4vps" -o IdentitiesOnly=yes deploy@185.69.52.106
```

## Stan projektu

- Ubuntu 24.04, Docker Compose, Caddy/HTTPS, PostgreSQL, Redis, fail2ban i UFW działają produkcyjnie.
- Publiczny katalog zawiera 51 programów: 11 dla nieruchomości i 40 dla przedsiębiorstw.
- Programy nieruchomości i firm są rozdzielane przed uruchomieniem właściwych reguł dopasowania.
- Użytkownik może mieć wiele profili nieruchomości i przedsiębiorstw.
- Matching jest deterministyczny; AI pomaga w ekstrakcji danych, ale nie podejmuje decyzji o kwalifikacji.
- Programy pokazują warunki, kwoty, ważne informacje, dokumenty, formularze i instrukcje aplikowania.
- Przy każdym wyniku dostępny jest chroniony, drukowalny raport dopasowania z danymi profilu, dowodami z regulaminu i formularzami.
- Użytkownicy mogą zgłaszać własne źródła, lecz crawler uruchamia się dopiero po akceptacji administratora.
- Interfejs jest responsywny, ma jasny i ciemny motyw.
- Backup Restic i monitoring lokalny VPS działają cyklicznie.
- Ostatni wdrożony commit kodu raportów: `63c2dbe01f079e26b24f49f8395a7478a8a30603`.
- Ostatni znany commit dokumentacji przed tym plikiem: `3bf7d29c1d7be964d561284af12e140c0293fbf4`.
- Backup przed wdrożeniem raportów: `e0b2271e`; kontrola repozytorium, odtworzenie 474 plików i katalogów, suma dumpa oraz pełny import PostgreSQL zakończyły się poprawnie.

## Konta testowe

Istnieją aktywne konta testowe o znormalizowanych loginach:

- `michalk`
- `dominik`

Oba mają rolę `user`. Hasła celowo nie są zapisane w tym dokumencie, repozytorium ani na serwerze w postaci jawnej. Konto `dominik` zostało utworzone i sprawdzone 2026-09-30; świeże logowanie zwróciło HTTP 200.

## Ostatnio wykonane zadanie

Dodano raport dopasowania dostępny z listy wyników. Raport pokazuje:

- dane pochodzące z profilu użytkownika,
- wynik i uzasadnienie każdej reguły,
- brakujące dane,
- dowody, cytaty, paragrafy i oficjalne źródła,
- beneficjentów, warunki, kwoty i ograniczenia,
- dane firmowe: PKD, de minimis, koszty, wkład własny i konsorcjum,
- wymagane dokumenty,
- instrukcję składania wniosku,
- wnioski, formularze i regulaminy,
- przycisk drukowania lub zapisu do PDF w układzie A4.

Test produkcyjny na rzeczywistym profilu potwierdził HTTP 200, 11 dopasowań, 5 reguł, 3 zasoby aplikacyjne i 5 dokumentów dla sprawdzanego programu.

## Najważniejsze otwarte zadania

Przed publiczną betą nadal należy przede wszystkim:

1. obrócić ujawniony wcześniej klucz OpenRouter i podać nowy wyłącznie bezpośrednio na VPS,
2. wdrożyć backup przechowywany poza tym VPS,
3. wdrożyć zewnętrzny monitoring i alarmowanie niezależne od VPS,
4. dodać e-mail, potwierdzanie adresu i odzyskiwanie hasła,
5. wykonać testy bezpieczeństwa, prywatności i zamkniętą betę,
6. rozbudować alerty o zmianach oraz obserwowane programy,
7. kontynuować weryfikację katalogu i obsługę kolejki REVIEW,
8. przed sprzedażą przygotować płatności, pakiety, obsługę organizacji/doradców i finalne dokumenty prawne.

Aktualną kolejność zawsze porównać z `docs/NEXT_STEPS_PLAN.md` oraz stanem produkcji, ponieważ cron i administrator mogą zmienić liczbę zadań REVIEW.

## Zasady bezpiecznej kontynuacji

- Nie umieszczać kluczy API, haseł, ciasteczek ani prywatnych kluczy SSH w rozmowie, Git, logach i Markdownach.
- Nie kopiować prywatnego klucza SSH między komputerami; każda osoba i każde urządzenie powinny mieć osobną parę kluczy.
- Przed wdrożeniem uruchomić testy, build i GitHub Actions.
- Wdrażać dokładny zielony commit przez `server/deploy_release.sh`.
- Przed wdrożeniem wykonać backup, a po wdrożeniu uruchomić `server/acceptance_check.sh` i okresowo `server/verify_backup.sh`.
- Zachować istniejące dane produkcyjne i kolejkę REVIEW; nie zatwierdzać automatycznie zmian wygenerowanych przez AI.
- Dokumentację Markdown aktualizować w repozytorium oraz kopiować do `/home/deploy/Codex/ProjektDotacje`.
