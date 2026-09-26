# Sprint 07 — jakość i rozwój katalogu

Data realizacji: 26.09.2026  
Stan: wdrożony produkcyjnie.

## Wynik

- katalog źródeł rozszerzono z 7 do 12 oficjalnych źródeł;
- katalog publiczny rozszerzono z 6 do 11 ręcznie zatwierdzonych programów;
- dodano Pruszków, Brwinów, Michałowice i Raszyn oraz komplet sześciu gmin powiatu pruszkowskiego w słowniku lokalizacji;
- pięć nowych źródeł przeszło `crawl → snapshot → OpenRouter → REVIEW → approve → publish`;
- brak automatycznej publikacji wyników AI;
- API ma wersję `0.7.0`, a migracja bazy `b7c2e4f190ad`.

## Wykrywanie zmian

Crawler klasyfikuje zmiany jako:

- `regulation` — regulamin, uchwała lub program priorytetowy;
- `deadline` — termin rozpoczęcia lub zakończenia naboru;
- `funding_amount` — kwota albo poziom wsparcia;
- `application_form` — dodany, usunięty lub zastąpiony formularz;
- `call_closed` — zakończenie, wstrzymanie albo wyczerpanie środków;
- `other` — pozostała zmiana wymagająca REVIEW.

Klasyfikacja jest wskazówką dla operatora. Nie zmienia automatycznie publicznych danych.

## Dokumenty

- dokumenty mają stan `current`, `needs_review`, `superseded` albo `unavailable`;
- nowy hash istniejącego dokumentu tworzy zadanie `document_changed`;
- zatwierdzenie zmiany zapisuje audit log i przywraca stan `current`;
- usunięty z zatwierdzonej listy materiał pozostaje w historii jako `superseded`;
- portal pokazuje użytkownikowi ostrzeżenie przy materiale nieaktualnym lub niedostępnym;
- wykryto jeden historyczny link Ciepłego Mieszkania zwracający HTTP 404; pozostaje jawnie oznaczony jako `unavailable`.

## Kompletność programu

Panel `/admin` oblicza wynik na podstawie 14 kryteriów: opisu, statusu, lokalizacji, beneficjentów, kategorii, kluczowych informacji, grupy docelowej, warunków, finansowania, ograniczeń, kroków, wymaganych dokumentów, formularzy i aktualnego dokumentu. Panel pokazuje procent, liczbę spełnionych kryteriów i listę braków.

## Benchmark OpenRouter

Zestaw `apps/api/benchmarks/regulations.json` zawiera 20 ręcznie sprawdzonych przypadków opartych na oficjalnych materiałach. Wynik produkcyjnego benchmarku 45 pól krytycznych:

| Model | Trafność | Koszt 20 przypadków | Średnie opóźnienie | Błędy formatu |
|---|---:|---:|---:|---:|
| `openai/gpt-6-luna` | 93,33% | 0,0013096 USD | 2203 ms | 0 |
| `openai/gpt-oss-20b` | 91,11% | 0,001243716 USD | 10614 ms | 0 |
| `openai/gpt-5-nano` | 86,67% | 0,011232 USD | 10009 ms | 0 |
| `deepseek/deepseek-v4-flash` | 84,44% | 0,0028655839 USD | 8958 ms | 0 |

Rekomendacja: pozostawić `openai/gpt-6-luna` jako model szybki. W tej próbie był najdokładniejszy i najszybszy, a różnica kosztu względem `gpt-oss-20b` wyniosła około 0,000066 USD na 20 przypadków. `gpt-oss-20b` może być ponownie zbadany przy znacznie większej skali.

Pełny wynik jest w `apps/api/benchmarks/results-2026-09-26.json` oraz `/opt/dotacje-ai/data/exports/sprint07-model-benchmark.json` na VPS. Łączny koszt benchmarku: około 0,016651 USD. Jest raportowany osobno od tabeli `llm_runs`.

## Poprawka wykryta produkcyjnie

Pierwsza ekstrakcja Brwinowa nie zawierała dowodu statusu. Pipeline kończył zadanie błędem mimo dostępnego modelu awaryjnego. Routing poprawiono: brak krytycznych dowodów oznacza teraz odrzucenie odpowiedzi szybkiego modelu i automatyczne przejście do modelu mocniejszego. Test regresji potwierdza oba wywołania. Po poprawce wszystkie pięć ekstrakcji osiągnęło `ready_for_review`.

## Walidacja

- Ruff: poprawny;
- frontend typecheck i build: poprawne;
- 33 testy API poza znanym ograniczeniem lokalnego katalogu tymczasowego Windows: poprawne;
- pełny zestaw na Linuksie w GitHub Actions: `success`, run `36236185356`;
- commit produkcyjny implementacji: `b49291213034293030e039287531b6cbd65f74a4`;
- pięć kontenerów produkcyjnych: `healthy`;
- backup po publikacji i kontroli dokumentów: `64959196`;
- koszt zapisany w `llm_runs`: `0.092188 USD`, plus benchmark `0.016651 USD`;
- ujawniony wcześniej klucz OpenRouter pozostaje do końcowej rotacji zgodnie z decyzją właściciela.
