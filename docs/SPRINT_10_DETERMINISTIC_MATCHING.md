# Sprint 10 — deterministyczne dopasowanie dotacji

Data: 2026-09-26.

## Cel

Każdy użytkownik może tworzyć wiele niezależnych profili dotacyjnych i porównywać każdy z nich z opublikowanymi programami. Profil może opisywać nieruchomość prywatną albo przedsiębiorstwo/organizację.

Przykład jednego konta:

- `Dom w Nadarzynie` — Czyste Powietrze, pompy ciepła i termomodernizacja;
- `Firma — projekty B+R` — przyszłe programy NCBR, PARP i Funduszy Europejskich;
- `Wspólnota mieszkaniowa` — programy dla budynków wielorodzinnych.

Wyniki są obliczane osobno. Dane jednego profilu nie wpływają na drugi.

## Profile przedsiębiorstw

Profil `business` przechowuje:

- nazwę przedsiębiorstwa lub organizacji;
- lokalizację;
- typ beneficjenta: przedsiębiorstwo, MŚP, organizacja badawcza albo konsorcjum;
- wielkość: mikro, mała, średnia albo duża;
- formę prawną;
- rok rozpoczęcia działalności;
- liczbę pracowników i roczny obrót;
- opcjonalne kody PKD/branżowe;
- cele: B+R, innowacje, cyfryzacja, efektywność energetyczna i internacjonalizacja.

Model programów otrzymał strukturalne pole dopuszczalnych wielkości przedsiębiorstwa. Ekstrakcja i ręczne zatwierdzanie potrafią zachować te wartości dla przyszłych programów firmowych.

## Reguły dopasowania

Silnik nie używa LLM i nie zgaduje. Dla każdego programu sprawdza pięć reguł:

1. status i termin naboru;
2. typ beneficjenta;
3. lokalizację wraz z hierarchią gmina → powiat → województwo → Polska;
4. typ i stan nieruchomości albo wielkość przedsiębiorstwa;
5. zgodność celu inwestycji.

Każda reguła zwraca:

- `fulfilled` — spełnione;
- `not_fulfilled` — niespełnione;
- `missing_data` — brak danych do rozstrzygnięcia.

Wynik programu:

- `eligible` — wszystkie reguły są spełnione;
- `possible` — nie ma niespełnionej reguły, ale brakuje danych;
- `not_eligible` — co najmniej jedna reguła jest niespełniona.

Programy są sortowane według wyniku, procentu spełnionych reguł i nazwy. API zwraca rangę oraz listę obszarów wymagających uzupełnienia.

## Interfejs i API

- profil wybiera rodzaj `property` albo `business`;
- panel konta pokazuje dowolną liczbę profili obu rodzajów;
- akcja `Dopasowania` otwiera `/konto/profil/{id}/dopasowania`;
- `GET /api/profiles/{id}/matches` zwraca ranking i wyjaśnienie każdej reguły;
- wynik jest prywatny i wymaga sesji właściciela profilu;
- publiczna lista przyjmuje również filtr `business_size`.

## Granice odpowiedzialności

Wynik jest technicznym porównaniem zatwierdzonych danych, a nie decyzją instytucji. AI nie kwalifikuje użytkownika. Każdy wynik wskazuje powód i wymaga sprawdzenia aktualnego regulaminu.

## Aktualny zakres katalogu firmowego

Kod i baza są gotowe na programy NCBR/PARP, ale aktualny katalog produkcyjny obejmuje głównie dotacje mieszkaniowe i energetyczne dla osób fizycznych. Profil firmy może więc obecnie otrzymać prawidłowe `nie pasuje` albo `brak danych`.

Aby uzyskać użyteczne wyniki dla firm, kolejny sprint katalogowy powinien dodać oficjalne źródła NCBR, PARP i Funduszy Europejskich, a następnie zatwierdzić dla nich beneficjentów, wielkości firm, lokalizacje i kategorie inwestycji.

## Test jakości

Scenariusz referencyjny zawiera jednego użytkownika z dwoma profilami:

- istniejący dom właściciela na Mazowszu;
- małe przedsiębiorstwo realizujące B+R.

Ten sam zestaw programów daje profilowi domu pełne dopasowanie programu mieszkaniowego, a firmie pełne dopasowanie programu testowego dla MŚP. Programy przeznaczone dla drugiego typu profilu są jawnie odrzucane wraz z uzasadnieniem.
