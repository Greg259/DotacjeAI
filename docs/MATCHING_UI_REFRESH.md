# Rozdzielenie matchingu i odświeżenie interfejsu

Data wdrożenia: 2026-09-28.

## Matching według rodzaju profilu

- Profil `property` otrzymuje wyłącznie programy sklasyfikowane dla nieruchomości albo beneficjentów prywatnych.
- Profil `business` otrzymuje wyłącznie programy posiadające klasyfikację wielkości firmy albo firmowego beneficjenta.
- Program spoza rodzaju profilu nie jest prezentowany nawet jako wynik negatywny.
- Program bez wystarczającej klasyfikacji rodzaju beneficjenta nie trafia do żadnej puli do czasu uzupełnienia danych.
- Pozostałe reguły — status, lokalizacja, kategoria inwestycji i szczegółowe warunki — są liczone dopiero po wybraniu właściwej puli.

Produkcja zawiera 11 programów w puli nieruchomości oraz 40 programów w puli firm. Część wspólna wynosi 0. Test prawdziwego profilu nieruchomości konta testowego zwrócił 11 wyników i 0 programów o prefiksie katalogu firmowego.

## Interfejs

- nowy spójny system kolorów, powierzchni, obramowań, odstępów i cieni;
- bardziej czytelna hierarchia nagłówków, kart, filtrów, formularzy i wyników dopasowania;
- komunikacja strony głównej i katalogu obejmuje zarówno osoby prywatne, jak i firmy;
- jasny i ciemny motyw z zapamiętywaniem ustawienia w `localStorage` oraz domyślnym użyciem preferencji systemowej;
- dostępny przycisk zmiany motywu z etykietą dla czytników ekranu;
- układ desktopowy, tabletowy i mobilny z punktami przejścia 1020, 760 i 540 px;
- dwurzędowa nawigacja mobilna, jednokolumnowe filtry i formularze oraz pełnoszerokie przyciski akcji;
- zachowane widoczne focusy, skip-link i obsługa `prefers-reduced-motion`.

## Odbiór

- commit produkcyjny: `0f4ffe59b28157666206d9f811d98380371bc172`;
- GitHub Actions run 60: `success`;
- testy jednostkowe potwierdzają brak wzajemnego przenikania programów domu i firmy;
- typecheck i produkcyjny build Next.js zakończone sukcesem lokalnie, w CI i na VPS;
- wizualnie sprawdzono stronę główną i katalog na desktopie oraz w układzie mobilnym;
- pięć kontenerów ma stan `healthy`, HTTPS i API odpowiadają poprawnie;
- backup Restic `b6c9acbc` przeszedł kontrolę repozytorium, sumy oraz pełne odtworzenie PostgreSQL.
