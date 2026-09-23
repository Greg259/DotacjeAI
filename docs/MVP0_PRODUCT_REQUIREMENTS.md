# DotacjeAI — wymagania produktu MVP-0

Aktualizacja: 2026-09-23.

## Cel

MVP-0 jest publicznym portalem dotacji bez kont użytkowników. System pobiera oficjalne strony i dokumenty, wykrywa zmiany, wykonuje kontrolowaną ekstrakcję AI, przekazuje wynik administratorowi do zatwierdzenia i publikuje zweryfikowane informacje wraz ze źródłami oraz historią zmian.

Pierwszy obszar geograficzny to województwo mazowieckie, ze szczególnym uwzględnieniem Gminy Nadarzyn.

## Zakres MVP-0

- publiczny portal bez logowania,
- oficjalne źródła i dokumenty PDF,
- crawler z wersjonowaniem i SHA-256,
- wykrywanie zmian przed uruchomieniem LLM,
- ekstrakcja strukturalna przez OpenRouter,
- walidacja odpowiedzi AI,
- panel jednego administratora,
- obowiązkowe ręczne zatwierdzenie przed publikacją,
- historia zmian programu,
- filtry lokalizacji, nieruchomości, beneficjenta, inwestycji, statusu, terminu i poziomu wsparcia.

Poza zakresem MVP-0 pozostają rejestracja, profile nieruchomości użytkowników, matching osobisty, obserwowane programy, powiadomienia e-mail, płatności i prywatne dokumenty. Funkcje te należą do MVP-1.

## Pierwszy pionowy przepływ

```text
oficjalna strona lub PDF
-> pobranie nagłówków i treści
-> zapis URL, czasu i SHA-256
-> wykrycie zmiany
-> snapshot i diff
-> ekstrakcja OpenRouter do JSON
-> walidacja schematu
-> zadanie REVIEW
-> zatwierdzenie administratora
-> publikacja programu
-> historia zmian
```

Brak zmiany hasha kończy zadanie bez wywołania LLM. Wynik o niskiej pewności, sprzeczne daty albo brak jednoznacznego statusu zawsze tworzą zadanie REVIEW.

## Pierwsze źródła produkcyjne

1. WFOŚiGW w Warszawie — „Czyste Powietrze”; pierwszy pełny crawler.
2. Gmina Nadarzyn — dotacja na wymianę nieefektywnego źródła ciepła; pierwszy test automatycznego statusu `zakończona`.

Kolejne oficjalne źródła referencyjne:

- NFOŚiGW — harmonogram naborów,
- „Moje Ciepło”,
- przydomowe magazyny energii,
- „Moja Elektrownia Wiatrowa”,
- „Ciepłe Mieszkanie” i nabory prowadzone przez poszczególne gminy.

Dokładne adresy oraz stan weryfikacji znajdują się w `SOURCE_CATALOG.md`.

## Publiczne adresy portalu

- `/dotacje`,
- `/dotacje/{slug}`,
- `/region/mazowieckie`,
- `/powiat/pruszkowski`,
- `/gmina/nadarzyn`,
- `/kategoria/fotowoltaika`,
- `/kategoria/magazyny-energii`,
- `/kategoria/pompy-ciepla`.

Adresy muszą być stabilne, czytelne, posiadać canonical oraz działać niezależnie od późniejszego dodania kont użytkowników.

## Statusy programu

Dozwolone wartości:

- `open` — nabór otwarty,
- `planned` — nabór zapowiedziany, ale jeszcze nierozpoczęty,
- `suspended` — nabór czasowo wstrzymany,
- `closed` — termin minął lub nabór oficjalnie zamknięto,
- `unknown` — źródło nie pozwala ustalić statusu.

Status wynika z oficjalnego komunikatu i dat. Samo istnienie strony programu nie oznacza statusu `open`. Po przekroczeniu daty końcowej system proponuje `closed`, ale pierwsza publikacja i każda sprzeczność wymagają zatwierdzenia administratora.

## Dane programu

Każdy opublikowany program musi zawierać:

- nazwę i slug,
- organizatora,
- krótki opis,
- status naboru,
- datę rozpoczęcia i zakończenia,
- lokalizację i zasięg,
- typ nieruchomości,
- typ beneficjenta,
- kategorie inwestycji,
- maksymalną kwotę,
- poziom lub procent wsparcia,
- warunki kwalifikacji,
- oficjalny URL,
- dokumenty źródłowe,
- datę ostatniej weryfikacji,
- historię wersji,
- wskazanie źródła dla danych wyekstrahowanych przez AI.

Pole może mieć wartość nieustaloną. System nie może uzupełniać brakujących danych domysłem modelu.

## Filtry MVP-0

1. Lokalizacja: kraj, województwo, powiat, gmina.
2. Typ nieruchomości: dom jednorodzinny, mieszkanie, wspólnota mieszkaniowa, nowy dom, istniejący budynek.
3. Beneficjent: osoba fizyczna, właściciel, współwłaściciel, najemca, wspólnota mieszkaniowa.
4. Cel inwestycji: fotowoltaika, magazyn energii, magazyn ciepła, pompa ciepła, CWU, mikrowiatrak, termomodernizacja, wymiana źródła ciepła.
5. Status: otwarta, planowana, wstrzymana, zakończona.
6. Termin rozpoczęcia i zakończenia.
7. Maksymalna kwota dotacji.
8. Procent lub poziom wsparcia.
9. Data ostatniej weryfikacji.

Branża, rodzaj firmy i wielkość przedsiębiorstwa nie należą do pierwszego zakresu.

## OpenRouter i kontrola kosztów

- twardy limit miesięczny: 10 USD,
- ostrzeżenia po osiągnięciu 5 USD i 8 USD,
- po osiągnięciu 10 USD zatrzymanie niekrytycznych wywołań AI,
- brak automatycznego podnoszenia budżetu,
- brak wywołania LLM, gdy źródło nie zmieniło hasha,
- zapis modelu, tokenów, kosztu, czasu, wersji promptu i wyniku walidacji,
- tani model do ekstrakcji podstawowej, mocniejszy tylko dla trudnych lub niejednoznacznych dokumentów.

Sekret produkcyjny ma nazwę `OPENROUTER_API_KEY` i zostanie wpisany ręcznie do `/opt/dotacje-ai/secrets/app.env`. Nie może pojawić się w rozmowie, repozytorium, dokumentacji ani logach.

## Minimalny panel administratora

- logowanie jednego administratora,
- lista źródeł i czas ostatniej kontroli,
- status pobrania i błędy,
- podgląd snapshotu i diffu,
- podgląd dokumentów PDF,
- wynik ekstrakcji wraz z cytowanym źródłem pola,
- edycja, zatwierdzenie i odrzucenie,
- historia działań i zmian statusu,
- podgląd wykorzystania budżetu OpenRouter.

## Kryteria ukończenia MVP-0

- oba pierwsze źródła są pobierane automatycznie,
- niezmienione źródło nie uruchamia LLM,
- zmiana tworzy snapshot i diff,
- Nadarzyn jest prawidłowo oznaczony jako zakończony po terminie naboru 2026,
- wynik AI nie może ominąć REVIEW,
- administrator może zatwierdzić i opublikować program,
- portal publiczny filtruje i wyświetla dane bez logowania,
- każda karta wskazuje oficjalne źródło, dokumenty i datę ostatniej weryfikacji,
- testy, migracje, backup i monitoring przechodzą przed wdrożeniem.
