# Sprint 05 — katalog, panel administratora i portal publiczny

Data realizacji: 26.09.2026  
Zakres: wyłącznie punkty 5, 6 i 7 zatwierdzonego planu; wcześniejsze punkty pozostają odłożone.

## Wynik

Sprint został wykonany produkcyjnie. Portal zawiera sześć ręcznie zatwierdzonych programów, kolejka REVIEW jest pusta, a wszystkie kontrolowane dokumenty są dostępne.

Nowe programy:

1. `przydomowe-magazyny-energii` — status `planned`; nabór PME2 zapowiedziany na IV kwartał 2026 r.
2. `moja-elektrownia-wiatrowa` — status `closed`; nabór zamknięty 20.02.2026 r.
3. `cieple-mieszkanie` — status `unknown`, prezentowany jako wymagający sprawdzenia w konkretnej gminie.

Każdy program przeszedł przepływ `crawl → snapshot → OpenRouter → REVIEW → korekta operatora → approve → osobny publish`. Wynik AI nie został opublikowany automatycznie.

## Punkt 5 — rozszerzenie katalogu

- crawler priorytetowy obejmuje trzy nowe oficjalne źródła;
- zapisano wersjonowane snapshoty i dowody pól;
- karty zawierają warunki, beneficjentów, kwoty lub wyjaśnienie braku jednej kwoty, ważne ograniczenia, kroki złożenia wniosku i oficjalne materiały;
- filtry obejmują lokalizację Polska, typ nieruchomości, beneficjenta i kategorie inwestycji;
- kontrola dokumentów zakończyła się wynikiem: 0 niedostępnych linków.

## Punkt 6 — panel administratora

- ręczne uruchomienie crawla wybranego źródła;
- filtrowanie REVIEW po statusie, źródle i dacie;
- grupowanie wyników według źródła;
- koszt LLM widoczny przy zadaniu oraz miesięczna suma na pulpicie;
- ostrzeżenie o nowszym snapshocie;
- możliwość ponowienia nieudanej ekstrakcji z licznikiem prób i osobnym kluczem idempotencji;
- historia ostatnich operacji z audit logu;
- wszystkie operacje zmieniające dane pozostają chronione Basic Auth i kontrolą `Origin`.

## Punkt 7 — portal publiczny

- rozwijany panel filtrów i czytelne czyszczenie filtrów na urządzeniach mobilnych;
- komunikaty dla programów planowanych, zakończonych oraz wymagających lokalnego potwierdzenia;
- dokładna data i godzina ostatniej kontroli linków;
- dane strukturalne `GovernmentService` JSON-LD na karcie programu;
- polskie etykiety typów nieruchomości, w tym `existing_building`;
- rozbudowane sekcje: dla kogo, warunki, kwoty, ograniczenia, kroki, dokumenty i historia zmian.

## Walidacja produkcyjna

- GitHub Actions dla głównego wdrożenia: `success`, commit `8b5c4e7cabc8c68b1d23b19b69639148e42097c3`;
- pięć usług Docker: `healthy`;
- `/health` i `/api/health`: OK;
- publiczne programy: 6;
- zadania REVIEW: 0;
- niedostępne dokumenty: 0;
- koszt OpenRouter w miesiącu po sprincie: `0.067923 USD`;
- sitemap, panel 401/200 i nagłówki bezpieczeństwa: OK;
- backup przed wdrożeniem: snapshot Restic `2459ca90`.

## Odłożone zadania

Zgodnie z decyzją właściciela nie realizowano teraz wcześniejszych punktów planu. Nadal pozostają:

1. rotacja ujawnionego klucza OpenRouter po zakończeniu prac nad całością;
2. backup w niezależnej lokalizacji poza VPS i GitHubem;
3. alarm zewnętrzny niezależny od tego VPS;
4. osobny przegląd wizualny i dostępności na rzeczywistych urządzeniach;
5. rozpoczęcie MVP-1 dopiero po świadomej decyzji: konta, profil nieruchomości, matching, obserwowane programy i e-mail.
