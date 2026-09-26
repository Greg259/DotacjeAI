# Sprint 05 — punkt 4: przegląd wizualny i dostępność

Data realizacji: 26.09.2026  
Środowisko: produkcja `https://dotacjeai.eu`

## Zakres

Wykonano przegląd:

- strony głównej w widoku desktopowym 1440 px,
- listy dotacji w widoku mobilnym,
- szczegółowej karty programu na desktopie,
- szczegółowej karty programu na emulowanym ekranie 390 × 844 px,
- podstawowej semantyki dokumentu i przepełnienia poziomego,
- widoczności polskich znaków, statusów, źródeł i dat weryfikacji.

Do powtarzalnej kontroli dodano `tools/visual_audit.mjs`. Narzędzie korzysta z lokalnego protokołu diagnostycznego przeglądarki i raportuje szerokość viewportu, `scrollWidth`, liczbę `h1` i `main`, język dokumentu, skip-link oraz elementy wychodzące poza viewport.

## Wykryty błąd krytyczny

Pierwszy przegląd ujawnił uszkodzone polskie znaki w głównych polach trzech nowych programów. Rozbudowane sekcje kart były poprawne, ale tytuły, organizatorzy i opisy zapisane przez wcześniejszy potok PowerShell → SSH zawierały znaki `?`.

Naprawa:

- dodano walidowane narzędzie `program_core_cli.sh`;
- korekta jest zapisywana jako kolejna zatwierdzona wersja programu i wpis audit log;
- dane są wczytywane z plików UTF-8 znajdujących się bezpośrednio na VPS;
- poprawiono trzy programy, tworząc wersję 3 każdego z nich;
- test produkcyjny potwierdził poprawne ciągi `Ciepłe Mieszkanie`, `Środowiska` i `część 2`.

## Poprawki dostępności i responsywności

- dodano link „Przejdź do treści” widoczny po uzyskaniu fokusu;
- dodano wyraźny styl `:focus-visible` dla obsługi klawiaturą;
- główny element strony otrzymał stały punkt docelowy `main-content`;
- dodano bezpieczne zawijanie długich nagłówków i opisów;
- poprawiono mobilne wyrażenie szerokości `.shell` przez użycie `calc()`;
- potwierdzono jeden nagłówek `h1`, jeden element `main` i `lang="pl"`.

## Wynik końcowy

Dla emulowanego viewportu 390 px:

- `clientWidth`: 390,
- `scrollWidth`: 390,
- elementy poza viewportem: 0,
- skip-link: obecny,
- polskie znaki: poprawne.

Pełny test odbiorowy po poprawkach:

- 6 programów publicznych,
- 0 zadań REVIEW,
- 0 niedostępnych dokumentów,
- panel administratora 401 bez danych i 200 z uwierzytelnieniem,
- pięć kontenerów `healthy`,
- commit produkcyjny `39a4daa57b3ab203fa4c7c99f460b7124e862f11`,
- GitHub Actions `success`,
- backup przed wdrożeniem `3e52402c`.
