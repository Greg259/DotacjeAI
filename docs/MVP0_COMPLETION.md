# DotacjeAI — zamknięcie MVP-0

Data odbioru: 2026-09-26.

## Wynik

MVP-0 jest wdrożone produkcyjnie pod adresem `https://dotacjeai.eu`. Portal działa publicznie bez kont użytkowników, a operacje administracyjne są dostępne pod `/admin` wyłącznie po uwierzytelnieniu.

Opublikowane programy:

1. Czyste Powietrze — województwo mazowieckie, status `open`.
2. Dofinansowanie do wymiany źródła ciepła w Gminie Nadarzyn, status `closed` po 31.07.2026.
3. Moje Ciepło, status `open`, nabór do 26.02.2027.

## Zrealizowany zakres

- crawler HTML i PDF z ETag, Last-Modified, SHA-256, retry, limitem rozmiaru i weryfikacją TLS,
- snapshoty źródeł, diff i brak wywołania LLM przy niezmienionym hashu,
- ekstrakcja OpenRouter do ścisłego schematu `extraction-v2`, zapis kosztu, tokenów i wersji promptu,
- obowiązkowy REVIEW z osobnymi akcjami edit, approve, reject i publish,
- panel administratora z listą źródeł, błędami, kolejką REVIEW, diffem, kosztem LLM i kontrolą dokumentów,
- wersjonowanie kart programów oraz pobranych dokumentów,
- pełne karty: beneficjenci, warunki, warianty finansowania, ważne ograniczenia, kroki, załączniki i oficjalne formularze,
- publiczna lista, filtry, sortowanie, paginacja, strony programu, regionu, powiatu, gminy i kategorii,
- canonical, dynamiczna sitemap, robots.txt, nagłówki bezpieczeństwa i rate limiting,
- automatyczna propozycja zmiany statusu po dacie z obowiązkowym REVIEW,
- harmonogram crawler → ekstrakcja co 6 godzin, kontrola dokumentów codziennie i kontrola statusów co godzinę,
- backup PostgreSQL i danych przez Restic, monitoring co 5 minut oraz powtarzalny skrypt wydania dokładnego commitu.

## Kryteria odbioru

| Kryterium | Stan |
|---|---|
| Dwa pierwsze źródła pobierane automatycznie | wykonane |
| Trzecie źródło i pełny pionowy przepływ AI | wykonane — Moje Ciepło |
| Brak LLM przy niezmienionej treści | wykonane |
| Snapshot, diff i historia wersji | wykonane |
| Nadarzyn automatycznie rozpoznany jako zakończony | wykonane |
| AI nie omija ręcznego REVIEW | wykonane |
| Administrator może edytować, zatwierdzić, odrzucić i publikować | wykonane |
| Publiczny portal i komplet filtrów bez logowania | wykonane |
| Oficjalne źródła, dokumenty i data weryfikacji na kartach | wykonane |
| Monitoring linków i niezmienne wersje dokumentów | wykonane |
| Testy, migracja, backup i monitoring przed wydaniem | wykonane |

## Stan produkcji przy odbiorze

- wdrożony commit aplikacji `920cc22afd0979a446d7eed145928987d19c15ea`, GitHub Actions run 35 `success`;
- API `0.6.0`, migracja `e7f2a1c8d904`;
- pięć stałych kontenerów ma stan `healthy`;
- `/health`, `/api/health`, trzy karty, filtry i sitemap odpowiadają przez HTTPS;
- `/admin` zwraca `401` bez danych oraz `200` po poprawnym uwierzytelnieniu;
- HSTS, CSP, `X-Frame-Options`, `Permissions-Policy` i `nosniff` są aktywne;
- kolejka REVIEW nie zawiera oczekujących zadań;
- miesięczny koszt zapisanych wywołań LLM: `0.059997 USD`;
- crawler ignoruje techniczny licznik odwiedzin strony WFOŚiGW; dwa kolejne pobrania po poprawce nie utworzyły REVIEW ani kosztu LLM;
- snapshot Restic `09097500` przeszedł kontrolę repozytorium, sumy SHA-256 i pełny import PostgreSQL do bazy tymczasowej;
- zaszyfrowane backupy Restic oraz monitoring lokalny działają zgodnie z harmonogramem.

Hasło startowe administratora nie jest przechowywane w Git. Uprawniony operator może je odczytać po SSH z `/opt/dotacje-ai/secrets/admin-initial-password`; plik ma pozostać chroniony i docelowo powinien zostać zastąpiony hasłem zapisanym w menedżerze haseł.

## Świadomie poza MVP-0

- konta użytkowników, profile nieruchomości, matching i obserwowane programy,
- e-mail i alerty dla użytkowników,
- prywatne dokumenty oraz płatności,
- zewnętrzna kopia backupu i zewnętrzny monitoring całego VPS — obowiązkowe przed betą,
- większy katalog źródeł ponad trzy opublikowane programy.

## Jedyna czynność wymagająca właściciela

Ujawniony wcześniej klucz OpenRouter jest nadal kluczem tymczasowym. Nie można bezpiecznie utworzyć jego następcy bez zalogowania właściciela do panelu OpenRouter lub osobnego Management API Key. Właściciel powinien utworzyć nowy klucz z limitem 10 USD, wpisać go bezpośrednio do `/opt/dotacje-ai/secrets/app.env`, zrestartować zadania API i unieważnić stary klucz. Nowej wartości nie wolno przesyłać w rozmowie ani zapisywać w Git.

## Następny etap

Po rotacji klucza należy obserwować MVP-0 przez kilka dni, następnie dodać zewnętrzny backup i alarm spoza VPS. Dopiero potem rozpoczynać MVP-1: konta, profil domu lub mieszkania, matching, obserwowane programy i powiadomienia e-mail.
