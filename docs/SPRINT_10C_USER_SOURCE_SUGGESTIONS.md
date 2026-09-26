# Sprint 10C — źródła zgłaszane przez użytkowników

Aktualizacja: 2026-09-26.

## Cel

Zalogowany użytkownik może zaproponować publiczną stronę zawierającą dotacje, nabory lub inne formy wsparcia. System nie pobiera zgłoszonego adresu przed decyzją administratora. Dopiero zaakceptowane źródło dołącza do cyklicznego skanowania.

## Przepływ

1. Użytkownik podaje adres HTTPS, opcjonalny tytuł i krótką informację, czego szukać.
2. Zgłoszenie otrzymuje status `pending` i pojawia się w panelu administratora.
3. Administrator otwiera stronę i wybiera akceptację albo odrzucenie.
4. Akceptacja tworzy aktywne źródło typu `INDEX`; odrzucenie zapisuje decyzję widoczną dla użytkownika.
5. Harmonogram pobiera zaakceptowaną stronę i wykrywa linki związane z dotacjami, naborami, firmami, startupami, VC, B+R lub innowacjami.
6. Wykryte pozycje pozostają kandydatami. Administrator wybiera „Monitoruj i analizuj”, aby utworzyć szczegółowe źródło programu.
7. Szczegółowe źródło przechodzi istniejący proces crawler → OpenRouter → REVIEW. AI pomaga w ekstrakcji, lecz nie publikuje programu i nie decyduje o kwalifikacji.

## Zabezpieczenia

- wymagane jest zalogowane konto oraz poprawny token CSRF;
- dozwolone są wyłącznie adresy HTTPS;
- odrzucane są `localhost`, domeny `.local` oraz prywatne i lokalne adresy IP podane bezpośrednio;
- jedna osoba może mieć najwyżej pięć oczekujących zgłoszeń;
- ten sam adres nie może być zgłoszony dwa razy przez tego samego użytkownika;
- przed decyzją administratora nie jest wykonywane żadne pobranie;
- linki spoza zaakceptowanej domeny są dopuszczane automatycznie wyłącznie dla znanych domen urzędowych;
- wykrycie linku, ekstrakcja AI, zatwierdzenie danych i publikacja są rozdzielonymi etapami;
- akceptacja, odrzucenie i rozpoczęcie monitorowania są zapisywane w dzienniku audytowym.

## Dane użytkownika

Historia zgłoszeń jest widoczna na koncie wraz ze statusem i notatką administratora. Trafia także do eksportu JSON. Usunięcie konta usuwa zgłoszenia użytkownika; zaakceptowane źródło pozostaje niezależnym rekordem katalogu, jeżeli administrator zdecydował o jego monitorowaniu.

## Testy odbiorowe

- walidacja HTTPS oraz blokada adresów prywatnych;
- wymaganie sesji i CSRF;
- utworzenie zgłoszenia i blokada duplikatu;
- lista zgłoszeń ograniczona do właściciela;
- akceptacja tworząca aktywne źródło indeksowe;
- wykrywanie istotnych linków z zaakceptowanej domeny i odrzucanie obcych domen;
- regresja pełnego zestawu testów API oraz typecheck frontendu.
