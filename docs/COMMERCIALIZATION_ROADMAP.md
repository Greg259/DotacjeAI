# DotacjeAI — roadmapa do bety i produktu sprzedażowego

Aktualizacja: 2026-09-27.

## Stan produktu

DotacjeAI ma działający portal publiczny, konta i wiele profili, crawler, wersjonowanie źródeł i dokumentów, ekstrakcję OpenRouter, ręczny REVIEW, deterministyczne dopasowanie z uzasadnieniem oraz możliwość zgłaszania własnych źródeł. Produkcja zawiera 11 opublikowanych programów. To jest działający rdzeń technologiczny, ale jeszcze nie kompletny produkt komercyjny.

## Najważniejsze braki przed publiczną betą

1. Zewnętrzny, szyfrowany backup poza VPS i test pełnego odtworzenia.
2. Zewnętrzny monitoring domeny, który alarmuje także po awarii całego VPS.
3. Unieważnienie ujawnionego klucza OpenRouter i wprowadzenie nowego bezpośrednio na VPS.
4. Ochrona gałęzi `main`, obowiązkowe CI i procedura zmian produkcyjnych.
5. Weryfikacja e-maila, odzyskiwanie hasła i historia zdarzeń bezpieczeństwa konta.
6. Obserwowanie programów, kategorii i wyników profilu oraz powiadomienia o zmianach.
7. Produkcyjne programy dla firm z NCBR, PARP, BGK, Funduszy Europejskich i programów regionalnych.
8. Zamknięcie bieżących zadań REVIEW oraz kontrola jakości wszystkich reguł używanych w matchingu.
9. Testy E2E, wydajność, monitoring błędów, okresy retencji, finalny regulamin i dokumentacja RODO.

## Plan kolejnych sprintów

### Sprint 08 — bezpieczeństwo i ciągłość działania

- backup do zewnętrznego magazynu S3/B2/R2;
- pełny test odtworzenia poza VPS;
- zewnętrzny uptime monitoring i alert e-mail/SMS;
- rotacja klucza OpenRouter;
- recovery kit kluczy SSH i dostęp z drugiego komputera;
- ochrona `main`, pull requesty i obowiązkowe CI;
- przegląd sekretów, logów, retencji i aktualizacji systemu.

To jest P0 przed przyjęciem większej liczby użytkowników.

### Sprint 10D — katalog firmowy i jakość dopasowania

- ręcznie zweryfikować kandydatów NCBR/PARP/Funduszy Europejskich;
- dodać BGK, programy regionalne i najważniejsze instrumenty startup/VC;
- osiągnąć co najmniej 30–50 aktualnych programów firmowych;
- dodać pełne kryteria PKD, wielkości firmy, regionu, kosztów kwalifikowanych, wkładu własnego, de minimis i konsorcjum;
- przygotować złoty zestaw testowy dla każdego programu;
- mierzyć kompletność, świeżość, fałszywe dopasowania i czas od publikacji źródła do zatwierdzenia.

### Sprint 09B — e-mail i bezpieczeństwo konta

- adres e-mail, potwierdzenie adresu i reset hasła;
- zmiana hasła, wylogowanie wszystkich sesji i historia logowań;
- limity prób, blokada nadużyć i komunikaty o zdarzeniach bezpieczeństwa;
- migracja istniejących kont testowych bez utraty profili;
- wersjonowane zgody marketingowe oddzielone od zgód wymaganych usługą.

### Sprint 11 — obserwowanie i powiadomienia

- obserwowanie programu, kategorii, lokalizacji i dopasowań profilu;
- alert o nowym programie, zmianie terminu, kwoty, regulaminu lub formularza;
- przypomnienia przed zakończeniem naboru;
- wysyłka natychmiastowa albo dzienny/tygodniowy digest;
- deduplikacja, retry, rezygnacja jednym kliknięciem i historia dostarczenia;
- brak wysyłki przed zatwierdzeniem zmiany przez administratora.

### Sprint 12 — beta produkcyjna

- pełne E2E na telefonie i komputerze;
- audyt sesji, CSRF, panelu administratora, rate limitów i izolacji danych;
- test wydajności oraz kontrolowany rollback;
- monitoring wyjątków bez danych osobowych i sekretów;
- finalna polityka prywatności, regulamin, retencja i opis profilowania;
- audyt WCAG 2.2 AA i dostępności procesu zakupu;
- zamknięta beta z 10–20 użytkownikami i mierzeniem powodzenia kluczowych zadań.

### Sprint 13 — monetyzacja

- zdefiniować pakiety i limity funkcji;
- płatność jednorazowa za raport oraz abonament za alerty;
- obsługa faktur, anulowania, zwrotów, statusów płatności i webhooków;
- limity planów egzekwowane po stronie API;
- strona cenowa, okres próbny i czytelny moment uzyskania wartości;
- analityka lejka: rejestracja → profil → dopasowanie → obserwowanie → zakup.

Hipoteza cenowa do testu, nie gotowy cennik:

- Free: katalog i jedno podstawowe dopasowanie;
- Raport: około 39–69 zł jednorazowo;
- Alerty użytkownika/firmy: około 29–59 zł miesięcznie;
- Doradca/instalator: około 199–499 zł miesięcznie za wielu klientów, raporty i pracę zespołową.

### Sprint 14 — onboarding firm przez NIP i raport sprzedażowy

- integracja z oficjalnym API REGON po NIP/KRS/REGON;
- automatyczne uzupełnianie nazwy, lokalizacji, formy prawnej i kodów PKD;
- pytania tylko o dane, których nie ma w rejestrze;
- porównanie programu z profilem w mniej niż minutę;
- generowany PDF z dopasowaniami, brakami, ryzykami, źródłami i terminami;
- wezwanie do obserwowania programu albo kontaktu z doradcą.

Oficjalne API REGON jest bezpłatne, dostępne również dla podmiotów komercyjnych i pozwala wyszukiwać po NIP, REGON lub KRS: https://api.stat.gov.pl/Home/RegonApi?lang=pl

### Sprint 15 — wersja B2B dla doradców i instalatorów

- organizacje, zespoły, zaproszenia i role;
- wielu klientów i profili w jednym panelu;
- status szansy: nowa, do analizy, kontakt, przygotowanie wniosku, złożona, wygrana, odrzucona;
- notatki, zadania, eksport CSV/PDF i historia kontaktu;
- raport z logo partnera oraz bezpieczny link dla klienta;
- API/webhook do CRM;
- rozliczanie liczby klientów, użytkowników lub raportów.

### Sprint 16 — wzrost i pokrycie rynku

- strony SEO dla województw, powiatów, branż, PKD i typów beneficjentów;
- landing pages dla konkretnych problemów, nie tylko nazw programów;
- partnerstwa z doradcami, księgowymi, instalatorami i organizacjami przedsiębiorców;
- program poleceń i mierzenie źródła leadu;
- publikowany wskaźnik świeżości i pokrycia źródeł;
- proces dodawania nowych źródeł z SLA oraz kolejką jakości.

## Mocne strony DotacjeAI

1. **Dowody zamiast samego wyniku.** Każdy warunek może wskazywać oficjalny URL, dokument, lokalizator i cytat dowodowy.
2. **AI nie podejmuje decyzji.** Model pomaga w ekstrakcji, natomiast wynik kwalifikacji oblicza deterministyczny silnik na zatwierdzonych regułach.
3. **Historia i świeżość.** System przechowuje snapshoty, hashe, różnice, historię zmian i stan dokumentów.
4. **Ręczna bramka jakości.** Dane nie są automatycznie publikowane po odpowiedzi modelu.
5. **Profile prywatne i firmowe.** Jedno konto może porównywać kilka nieruchomości i przedsiębiorstw.
6. **Lokalne źródła.** Produkt potrafi monitorować gminne strony i formularze, których ogólne wyszukiwarki często nie opisują szczegółowo.
7. **Niski koszt AI.** LLM uruchamia się dopiero po zmianie źródła, z limitami kosztów i zapisem wykorzystania.
8. **Działająca produkcja.** HTTPS, kontenery, migracje, backup, monitoring lokalny i CI są już uruchomione.

## Największe słabości i ryzyka

- 11 programów to za mało, aby obiecać szerokie pokrycie rynku;
- część wartości zależy od ręcznego REVIEW, więc trzeba mierzyć czas i koszt obsługi jednego programu;
- brak e-maila, alertów i obserwowania ogranicza retencję użytkowników;
- brak NIP/REGON zwiększa tarcie w profilu firmy;
- brak płatności, planów i analityki uniemożliwia sprawdzenie gotowości klientów do zapłaty;
- profilowanie wymaga jasnej informacji, wyjaśnialności, korekty danych i oceny obowiązków RODO;
- produkt ogólny konkuruje z darmową Wyszukiwarką Dotacji oraz serwisami mającymi setki programów;
- PARP stosuje zabezpieczenie antybotowe, więc potrzebny jest alternatywny legalny kanał danych albo ręczna ścieżka;
- lokalny backup na tym samym VPS i lokalny monitoring nie chronią przed utratą całej maszyny;
- wiedza operacyjna nadal jest skupiona u jednej osoby.

## Pozycjonowanie rekomendowane

Nie sprzedawać DotacjeAI jako „kolejnej listy dotacji”. Oficjalna Wyszukiwarka Dotacji już pozwala filtrować według podmiotu, lokalizacji i dziedziny, a konkurenci reklamują setki naborów.

Rekomendowana obietnica:

> DotacjeAI pokazuje nie tylko, jaka dotacja może pasować, ale także dlaczego, którego warunku brakuje, gdzie dokładnie znajduje się ten warunek w oficjalnym dokumencie i co zmieniło się od ostatniej kontroli.

Najlepszy pierwszy płatny segment to doradcy dotacyjni, instalatorzy OZE/termomodernizacji i małe biura obsługujące wielu klientów. Mają powtarzalny problem, większą skłonność do abonamentu i mogą używać wielu profili oraz raportów. Portal dla osoby prywatnej powinien pozostać kanałem pozyskiwania leadów i dowodem jakości danych.

## Obserwacje rynkowe

- oficjalny portal Funduszy Europejskich ma wyszukiwarkę opartą o typ podmiotu, lokalizację i dziedzinę oraz publikuje aktualizowane harmonogramy: https://funduszeeuropejskie.gov.pl/nabory-wnioskow/
- DotacjaPro reklamuje dopasowanie po NIP, dane GUS/REGON, 600+ naborów, raport za 49 zł i alerty za 29 zł miesięcznie: https://dotacjapro.pl/
- KiedyNabory koncentruje się na wąskim rynku KFS/BUR, historii zmian, alertach, zespołach i cenach od około 99–190 zł miesięcznie: https://kiedynabor.pl/
- Radar Dotacji łączy monitoring z usługą przygotowania i rozliczania wniosków za 499 zł netto miesięcznie: https://radar-dotacji.pl/
- unijny Funding & Tenders Portal zapewnia rozbudowane wyszukiwanie i RSS, więc przewaga nie może polegać wyłącznie na agregowaniu linków: https://ec.europa.eu/info/funding-tenders/opportunities/portal/

Wnioski cenowe są hipotezą wynikającą z publicznych ofert konkurencji i wymagają rozmów z klientami oraz testów płatności.

## Co zwiększa wartość firmy przy przyszłej sprzedaży

1. Powtarzalny przychód MRR i niski churn, nie sama liczba rejestracji.
2. Udokumentowane pokrycie źródeł, szybkość wykrywania i dokładność dopasowań.
3. Własny, zweryfikowany zbiór wersjonowanych reguł i dowodów źródłowych.
4. Proces jakości, który można przekazać zespołowi, a nie wiedza jednej osoby.
5. Umowy, prawa do kodu, lista licencji open source, polityka danych i legalne kanały pozyskania treści.
6. Zewnętrzny backup, monitoring, procedury incydentów i brak ujawnionych sekretów.
7. Zespół klientów B2B, integracje i API zwiększające koszt zmiany dostawcy.
8. Mierzone wskaźniki: aktywacja, konwersja, retencja, czas REVIEW, świeżość danych, pokrycie i liczba skutecznych alertów.

## Rekomendowana kolejność

Najpierw Sprint 08, potem 10D, 09B, 11 i 12. Dopiero stabilną betę należy rozszerzyć o płatności w Sprincie 13. Równolegle można przeprowadzić 10–15 rozmów z doradcami i instalatorami, ale nie budować rozbudowanego panelu B2B przed potwierdzeniem, że przynajmniej kilku z nich chce za niego płacić.
