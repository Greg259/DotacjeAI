# Sprint 10B — zaawansowane dopasowanie i programy dla firm

Aktualizacja: 2026-09-26.

## Cel

Rozszerzyć deterministyczne dopasowanie o szczegółowe kryteria gospodarstw domowych i przedsiębiorstw oraz automatycznie wykrywać kandydatów na programy z oficjalnych katalogów. AI służy wyłącznie do ekstrakcji reguł; wynik kwalifikacji oblicza kod na danych zatwierdzonych przez administratora.

## Zrealizowany zakres techniczny

- profile osób fizycznych: roczny dochód gospodarstwa, liczba osób, budżet projektu i wkład własny;
- profile firm: budżet, wkład własny, pomoc de minimis, status startupu, inwestor VC i planowane konsorcjum;
- pola istniejące: wielkość firmy, forma prawna, rok założenia, zatrudnienie, obrót i PKD;
- wersjonowane `eligibility_rules` w zatwierdzonym programie;
- operatory: równość, wykluczenie, lista dopuszczalna, lista wykluczona, minimum, maksimum, przedział, zgodność list oraz wartości logiczne;
- pola wyliczane: wiek firmy, miesięczny dochód na osobę i procent wkładu własnego;
- każda reguła przechowuje oficjalny URL, lokalizator w regulaminie, cytat dowodowy i informację, czy blokuje kwalifikację;
- wynik `eligible`, `possible` albo `not_eligible` zależy wyłącznie od reguł deterministycznych;
- brak wartości profilu daje `missing_data`, a nie negatywną decyzję;
- panel administratora pokazuje diagnostykę dopasowań wszystkich zapisanych profili;
- publiczny ekran wyniku pokazuje dowód i link źródłowy każdej reguły.

## Wykrywanie programów

Monitorowane są oficjalne indeksy:

- katalog naborów PARP;
- wyszukiwarka Funduszy Europejskich;
- oficjalne archiwum konkursów NCBR;
- szczegółowe strony PARP: Ścieżka SMART, Start-up Booster Poland i Promocja marki innowacyjnych MŚP.

Indeksy nie są traktowane jak pojedynczy program. Po pobraniu system wyodrębnia oficjalne linki zawierające sygnały takie jak nabór, dotacja, przedsiębiorstwo, MŚP, startup, VC, B+R albo innowacje. Kandydat trafia do panelu administratora. Nie jest automatycznie publikowany.

Serwis PARP zwraca automatycznemu klientowi wyzwanie Incapsula zamiast treści strony. Bezpośrednie źródła PARP pozostają zapisane, ale nieaktywne w automatycznym crawlerze, żeby nie tworzyć fałszywych wyników ani cyklicznych alarmów. Programy PARP mogą być nadal wykrywane przez oficjalną wyszukiwarkę Funduszy Europejskich i następnie weryfikowane ręcznie.

## Bezpieczeństwo decyzji

- AI nie ustala wyniku kwalifikacji;
- reguła bez oficjalnego dowodu nie powinna zostać zatwierdzona;
- warunek nieobsługiwany strukturalnie pozostaje opisem programu, a nie automatyczną decyzją;
- wynik jest oceną wstępną i nie zastępuje decyzji instytucji;
- programy wykryte w katalogu wymagają REVIEW przed publikacją.

## Testy

Testy obejmują zgodność pozytywną firmy z programem B+R, przekroczenie limitu obrotu, brak danych, wyliczenie wkładu własnego, nieblokujący warunek VC, dowody źródłowe, filtrowanie oficjalnych domen oraz rozdzielenie profilu nieruchomości i firmy.

## Granica wdrożenia danych

Dodanie źródła nie oznacza publikacji programu. Po pierwszym pobraniu szczegółowych stron firmowych należy sprawdzić wynik ekstrakcji w REVIEW, porównać terminy i regulaminy, a dopiero potem zatwierdzić i opublikować poprawne rekordy.

## Rozszerzenie 10C — sugestie użytkowników

Zalogowany użytkownik może zgłosić własną stronę HTTPS z dotacjami lub wsparciem. Strona nie jest pobierana przed akceptacją administratora. Po akceptacji crawler traktuje ją jako indeks, wykrywa istotne linki z tej samej domeny, a administrator osobno uruchamia monitorowanie i analizę wybranego programu. Szczegóły, zabezpieczenia oraz testy opisuje `SPRINT_10C_USER_SOURCE_SUGGESTIONS.md`.
