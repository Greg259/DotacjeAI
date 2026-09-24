# Sprint 04 — pierwsza publikacja i publiczny portal MVP-0

Data planu: 2026-09-24  
Stan wejściowy: API 0.4.0, 3 ekstrakcje `ready_for_review`, 3 zadania REVIEW `pending`, 0 opublikowanych programów  
Cel: zakończyć pierwszy pełny pion produktu — od ręcznie sprawdzonego wyniku do działającego publicznego portalu bez logowania

## Status realizacji — 2026-09-24

Sprint rozpoczęty. Zrealizowano pierwszą część techniczną:

- publiczne szczegóły API zawierają dokumenty i wyłącznie zatwierdzoną historię wersji,
- nieopublikowane programy nadal zwracają `404` i nie pojawiają się na liście,
- placeholder Node zastąpiono aplikacją Next.js 16 z App Routerem,
- przygotowano landing, listę z filtrami, kartę programu, strony regionu, gminy i kategorii,
- dodano stany pusty/błąd/404, responsywny wygląd, `robots.txt` i `sitemap.xml`,
- frontend działa jako minimalny obraz Docker `standalone` za Caddy,
- GitHub Actions sprawdza typecheck i produkcyjny build frontendu,
- lokalnie zaliczono 23 testy API, Ruff, typecheck i produkcyjny build Next.js.

Nadal wymagane w tym sprincie:

- ~~zielone CI dla commita sprintu,~~ wykonane dla `99f22c7`,
- ~~backup i wdrożenie API 0.5.0 oraz frontendu na VPS,~~ wykonane; backup `570de219`,
- ~~testy publicznych tras przez HTTPS,~~ wszystkie wymagane trasy zwracają `200`,
- ręczna decyzja właściciela dla trzech zadań REVIEW,
- osobne `approve` i `publish` dopiero po tej decyzji,
- backup i test odtworzenia po pierwszej publikacji,
- rotacja ujawnionego klucza OpenRouter jako ostatnia czynność.

Do czasu rotacji pozostają zablokowane wszystkie nowe wywołania LLM. Istniejący klucz nie jest kopiowany ani wyświetlany.

Stan produkcyjny po wdrożeniu:

- commit aplikacji: `99f22c7608e8fc27d49941adea5c65a39d4b17d4`,
- GitHub Actions run 22: `success`,
- API: `0.5.0`, migracja `c4e7b9a210f3 (head)`,
- kontenery `caddy`, `frontend`, `api`, `postgres` i `redis`: `healthy`,
- `/`, `/dotacje`, strony regionu/gminy/kategorii, `robots.txt`, `sitemap.xml`, `/api/health` i `/api/programs`: HTTP 200,
- publiczna lista pozostaje celowo pusta do czasu jawnej decyzji REVIEW.

Rekomendacje dla trzech zadań opisuje `SPRINT_04_REVIEW_DECISION.md`.

## 1. Rezultat sprintu

Po zakończeniu sprintu użytkownik powinien móc wejść na `dotacjeai.eu`, znaleźć program według lokalizacji, kategorii i statusu, otworzyć jego kartę oraz przejść do oficjalnego źródła. Co najmniej jeden program musi być ręcznie zatwierdzony i opublikowany.

Sprint nie wykonuje nowych analiz OpenRouter do czasu końcowej rotacji klucza. Korzysta wyłącznie z trzech wyników zapisanych w Sprincie 03.

## 2. Priorytety

### P0 — domknięcie REVIEW

1. Wyświetlić pełne dane i dowody Nadarzyna.
2. Potwierdzić status `closed`, termin 31.07.2026, kwotę 6000 PLN i wsparcie 100%.
3. Zdecydować, czy pozostawić ostrzeżenie dotyczące wywnioskowanego typu nieruchomości.
4. Porównać dwa wyniki WFOŚiGW: `new_program` i `source_changed`.
5. Wybrać wynik bazowy WFOŚiGW, a zbędne zadanie odrzucić z uzasadnieniem.
6. Wykonać `approve` wyłącznie dla ręcznie potwierdzonych danych.
7. Sprawdzić utworzone `ProgramVersion`, powiązania i audit log.
8. Wykonać `publish` jako osobną, jawną operację.

Żaden krok approve/publish nie może być wykonany automatycznie ani bez decyzji właściciela.

### P0 — publiczne API gotowe dla frontendu

1. Zachować istniejącą listę `/api/programs` i szczegóły `/api/programs/{slug}`.
2. Rozszerzyć szczegóły programu o dokumenty źródłowe i historię zatwierdzonych wersji.
3. Zapewnić filtry: lokalizacja, status, kategoria, typ nieruchomości i beneficjent.
4. Dodać stabilne sortowanie, paginację i walidację parametrów.
5. Zwracać oficjalny URL oraz `last_verified_at`.
6. Nie ujawniać szkiców, zadań REVIEW, promptów, kosztów ani wewnętrznych identyfikatorów.
7. Dodać testy blokujące wyświetlenie programu przed publikacją.

### P1 — docelowy frontend publiczny

Zastąpić techniczny `server.js` aplikacją Next.js, dobierając aktualną stabilną wersję podczas implementacji.

Wymagane strony:

- `/` — strona główna z prostym wyszukaniem i kategoriami,
- `/dotacje` — lista i filtry zapisane w URL,
- `/dotacje/[slug]` — pełna karta programu,
- `/region/mazowieckie`,
- `/gmina/nadarzyn`,
- `/kategoria/[slug]`.

Karta programu powinna zawierać:

- nazwę, organizatora i status,
- termin naboru,
- kwotę oraz poziom wsparcia,
- beneficjentów, nieruchomości i kategorie,
- krótki opis,
- datę ostatniej weryfikacji,
- oficjalny URL i dokumenty,
- czytelne ostrzeżenie, że portal nie zastępuje regulaminu programu.

### P1 — jakość interfejsu i SEO

1. Responsywny interfejs mobilny i desktopowy.
2. Poprawna polska typografia i kodowanie UTF-8.
3. Dostępność klawiaturą, etykiety formularzy i sensowny kontrast.
4. Stany: ładowanie, pusta lista, błąd API i 404.
5. Tytuły, opisy, canonical, Open Graph, `robots.txt` i `sitemap.xml`.
6. Strony filtrowane renderowane po stronie serwera, aby ich podstawowa treść była dostępna bez JavaScriptu.
7. Brak panelu administratora i logowania w publicznym frontendzie tego sprintu.

Bezpieczny panel webowy administratora zostaje osobnym etapem. W Sprincie 04 administracja nadal odbywa się przez SSH i prywatne CLI.

### P1 — testy i wdrożenie

1. Testy API listy, szczegółów, filtrów, historii i izolacji szkiców.
2. Testy komponentów i tras frontendu.
3. Test end-to-end: lista → filtr Nadarzyn → karta programu → oficjalne źródło.
4. Test pustego wyniku i błędu API.
5. Build produkcyjny w GitHub Actions.
6. Backup przed migracją lub pierwszą publikacją.
7. Wdrożenie dokładnego commita po zielonym CI.
8. Kontrola HTTPS, healthchecków, logów i publicznych tras.
9. Backup po publikacji oraz pełny test odtworzenia.
10. Aktualizacja dokumentacji lokalnie, w GitHubie i w obu katalogach VPS.

### P0 na sam koniec — rotacja klucza OpenRouter

Zgodnie z decyzją właściciela rotacja zostanie wykonana jako ostatni etap sprintu.

Do tego czasu:

- nie uruchamiać nowych ekstrakcji wymagających LLM,
- nie uruchamiać benchmarków ani testowych zapytań do modeli,
- nie zmieniać miesięcznego limitu 10 USD,
- nie kopiować obecnego klucza do żadnego nowego miejsca.

Końcowa procedura:

1. Unieważnić obecny klucz w panelu OpenRouter.
2. Utworzyć nowy klucz z limitem wydatków.
3. Wprowadzić go bezpośrednio do `/opt/dotacje-ai/secrets/app.env`, bez rozmowy, Git i historii powłoki.
4. Potwierdzić tryb pliku `0600`.
5. Zweryfikować uwierzytelnienie bez wypisywania wartości klucza.
6. Potwierdzić, że stary klucz nie działa.
7. Wykonać backup konfiguracji bez zapisywania jawnego sekretu.
8. Zapisać w dokumentacji wyłącznie datę rotacji i identyfikator klucza, nigdy jego wartość.

## 3. Kolejność wykonania

```text
zamrożenie nowych wywołań LLM
→ ręczny REVIEW Nadarzyna i WFOŚiGW
→ approve wybranych wyników
→ rozbudowa publicznego API
→ frontend Next.js
→ testy i CI
→ osobne publish
→ test portalu produkcyjnego
→ backup i restore test
→ rotacja klucza OpenRouter
→ końcowa dokumentacja
```

Publikację można wykonać dopiero po przejściu testów karty programu i po ręcznym potwierdzeniu danych.

## 4. Poza zakresem Sprintu 04

- konta użytkowników,
- profile nieruchomości i matching,
- subskrypcje i e-mail,
- płatności,
- prywatne dokumenty,
- OCR,
- publiczny panel administratora,
- automatyczne zatwierdzanie lub publikowanie,
- rozszerzenie na wszystkie siedem źródeł,
- zewnętrzny backup i zewnętrzny monitoring; pozostają wymagane przed betą.

## 5. Kryteria odbioru

Sprint jest ukończony, gdy:

- co najmniej Nadarzyn został ręcznie zatwierdzony i opublikowany,
- dla obu wyników WFOŚiGW istnieje jawna decyzja approve albo reject,
- `/api/programs` pokazuje wyłącznie opublikowane rekordy,
- portal działa bez logowania na urządzeniu mobilnym i desktopowym,
- działają lista, filtry, karta, strony lokalizacji i kategorii,
- każda karta ma oficjalne źródło i datę weryfikacji,
- szkice oraz dane administracyjne nie są dostępne publicznie,
- testy, build, lint i GitHub Actions przechodzą,
- HTTPS i wszystkie kontenery są zdrowe,
- backup po publikacji przechodzi pełne odtworzenie,
- podczas sprintu nie wykonano nowych wywołań LLM przed rotacją,
- stary klucz OpenRouter został unieważniony, a nowy bezpiecznie ustawiony na samym końcu,
- dokumentacja jest zgodna lokalnie, w GitHubie oraz w obu kopiach na VPS.

## 6. Decyzje potrzebne od właściciela

1. Potwierdzenie approve/reject dla Nadarzyna.
2. Wybór właściwego wyniku WFOŚiGW i decyzja dla duplikatu.
3. Osobna zgoda na publish każdego programu.
4. Opcjonalnie: logo i preferencje kolorystyczne. Ich brak nie blokuje sprintu — zostanie użyty prosty, neutralny styl.
5. Końcowe wykonanie rotacji klucza bez przekazywania nowej wartości w rozmowie.

## 7. Następny sprint

Po ukończeniu portalu publicznego: bezpieczne uwierzytelnienie administratora i webowy panel REVIEW albo rozszerzenie źródeł o harmonogram NFOŚiGW. Priorytet zostanie wybrany na podstawie pracy z pierwszymi opublikowanymi programami.
