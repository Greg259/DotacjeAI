# DotacjeAI — roadmapa do pełnego MVP

Aktualizacja: 2026-09-26.

## Punkt wyjścia

MVP-0 jest ukończone i działa produkcyjnie. Portal publiczny udostępnia 11 programów z 12 oficjalnych źródeł, crawler, analizę AI, ręczny REVIEW, historię zmian, dokumenty, filtry oraz panel administratora.

Pełne MVP, nazywane dalej MVP-1, powinno dodatkowo pozwalać użytkownikowi:

1. założyć i bezpiecznie odzyskać konto;
2. opisać dom, mieszkanie albo wspólnotę oraz planowaną inwestycję;
3. otrzymać wyjaśniony wynik dopasowania do programu;
4. obserwować programy i otrzymywać powiadomienia o ważnych zmianach;
5. zarządzać swoimi danymi i usunąć konto.

## Sprint 08 — infrastruktura i bezpieczeństwo przed betą

Priorytet: P0. Ten sprint należy zakończyć przed przyjmowaniem danych użytkowników.

1. Skonfigurować zaszyfrowany backup Restic poza VPS, np. w magazynie zgodnym z S3.
2. Wykonać pełny test odtworzenia bazy i dokumentów z kopii zewnętrznej.
3. Dodać zewnętrzny monitoring domeny i alarm e-mail lub telefoniczny, działający również po awarii całego VPS.
4. Unieważnić ujawniony klucz OpenRouter, utworzyć nowy z limitem 10 USD i wprowadzić go bezpośrednio na VPS.
5. Przygotować zaszyfrowaną kopię odzyskiwania kluczy SSH oraz dostęp z drugiego komputera.
6. Włączyć ochronę gałęzi `main`, wymagane CI i pracę przez pull request dla zmian produkcyjnych.
7. Obserwować harmonogramy crawlera, dokumentów, statusów, kosztów i backupu przez minimum kilka dni.

Definition of Done:

- utrata VPS nie powoduje utraty bazy ani dokumentów;
- awaria serwera powoduje alarm poza serwerem;
- skompromitowany klucz OpenRouter nie działa;
- wszystkie zadania cykliczne wykonują się bez niewyjaśnionych błędów.

## Sprint 09 — konta użytkowników i profile nieruchomości

Priorytet: P0 dla MVP-1.

1. Dodać rejestrację, logowanie, wylogowanie, weryfikację adresu e-mail i reset hasła.
2. Wprowadzić role `user`, `editor` i `admin` oraz testy izolacji danych.
3. Stosować bezpieczne sesje w ciasteczkach `HttpOnly`, `Secure` i `SameSite` oraz ochronę CSRF.
4. Dodać limitowanie prób logowania i rejestr zdarzeń bezpieczeństwa.
5. Zbudować profil beneficjenta: osoba fizyczna, właściciel, współwłaściciel, najemca albo wspólnota.
6. Zbudować profil nieruchomości: lokalizacja, rodzaj budynku/lokalu, stan nowy lub istniejący, źródło ciepła i podstawowe parametry techniczne.
7. Dodać cele inwestycji: PV, magazyn energii lub ciepła, pompa ciepła, CWU, mikrowiatrak, wymiana źródła ciepła i termomodernizacja.
8. Dodać zgodę na regulamin i politykę prywatności, eksport danych oraz usunięcie konta.

Definition of Done:

- użytkownik może utworzyć, zweryfikować, odzyskać i usunąć konto;
- użytkownik widzi i edytuje wyłącznie własne profile;
- jeden użytkownik może mieć więcej niż jedną nieruchomość;
- administrator nie poznaje hasła użytkownika.

## Sprint 10 — silnik dopasowania i rekomendacje

Priorytet: P0 dla wartości produktu.

Stan: wykonany 2026-09-26 w wersji deterministycznej, rozszerzonej o wiele profili oraz profile przedsiębiorstw. Produkcyjne wyniki firmowe wymagają teraz dodania źródeł NCBR/PARP.

1. Zbudować deterministyczny silnik reguł na danych zatwierdzonych przez administratora.
2. Dla każdego warunku zwracać `spełniony`, `niespełniony` albo `brak danych`.
3. Pokazywać wynik dopasowania wraz z konkretnym uzasadnieniem i źródłem warunku.
4. Nie pozwalać modelowi AI samodzielnie decydować o kwalifikacji; AI może jedynie pomagać w ekstrakcji i wyjaśnianiu zatwierdzonych reguł.
5. Dodać ranking programów dla wybranego profilu oraz listę danych, które użytkownik musi uzupełnić.
6. Obsłużyć wykluczenia, różne poziomy dofinansowania, progi dochodowe, lokalizację i terminy.
7. Przygotować ręcznie sprawdzone scenariusze testowe dla wszystkich programów publicznych.

Definition of Done:

- użytkownik otrzymuje powtarzalny wynik z wyjaśnieniem;
- każda decyzja wskazuje zatwierdzoną regułę lub informuje o braku danych;
- zmiana wersji programu powoduje ponowne przeliczenie dopasowania;
- testy obejmują przypadki pozytywne, negatywne i niejednoznaczne.

## Sprint 11 — obserwowanie programów i powiadomienia

Priorytet: P1, ale wymagany do pełnego MVP-1.

1. Wybrać dostawcę poczty transakcyjnej i skonfigurować SPF, DKIM oraz DMARC.
2. Dodać obserwowanie programu, kategorii lub dopasowań do profilu.
3. Wysyłać powiadomienia o nowym programie, zmianie terminu, kwoty, regulaminu, formularza oraz zamknięciu naboru.
4. Dodać przypomnienia przed końcem terminu.
5. Dodać preferencje częstotliwości, bezpieczny link rezygnacji i wyciszanie kategorii.
6. Zapewnić deduplikację, retry, historię wysyłki i kolejkę błędów.
7. Nie wysyłać powiadomienia przed zatwierdzeniem zmiany przez administratora.

Definition of Done:

- zatwierdzona zmiana dociera dokładnie raz do właściwych użytkowników;
- użytkownik może wyłączyć każde powiadomienie;
- błędy wysyłki są widoczne w panelu i ponawiane bez duplikatów;
- cały przepływ `źródło → REVIEW → publikacja → matching → e-mail` przechodzi test end-to-end.

## Sprint 12 — stabilizacja i uruchomienie bety

Priorytet: P0 przed zaproszeniem użytkowników zewnętrznych.

1. Wykonać testy end-to-end najważniejszych ścieżek na telefonie i komputerze.
2. Przeprowadzić kontrolę bezpieczeństwa logowania, sesji, uprawnień, panelu administratora, rate limitów i sekretów.
3. Sprawdzić wydajność listy, kart, matchingu i zadań cyklicznych przy zakładanym ruchu MVP.
4. Uzupełnić regulamin, politykę prywatności, informację RODO, okresy retencji oraz zastrzeżenie, że wynik nie jest decyzją instytucji przyznającej dotację.
5. Dodać obsługę błędów aplikacji i alarmowanie administratora bez zapisywania sekretów ani wrażliwych danych.
6. Przygotować procedury obsługi użytkownika, korekty danych, incydentu, wycofania wdrożenia i odtworzenia backupu.
7. Przeprowadzić zamkniętą betę na małej grupie użytkowników i poprawić błędy blokujące.

Definition of Done:

- nie ma błędów krytycznych ani wysokiego ryzyka bezpieczeństwa;
- kompletna ścieżka użytkownika działa produkcyjnie;
- administrator otrzymuje alarmy i potrafi odtworzyć usługę;
- dokumenty prawne i procedury operacyjne są opublikowane;
- beta potwierdza, że wyniki są zrozumiałe i użyteczne.

## Warunek uznania całego MVP za gotowe

MVP-1 jest gotowe, gdy nowy użytkownik może bez pomocy administratora:

```text
zarejestrować konto
→ potwierdzić e-mail
→ utworzyć profil nieruchomości
→ zobaczyć dopasowane programy i uzasadnienie
→ otworzyć warunki, źródła i formularze
→ zacząć obserwować program
→ otrzymać jedno poprawne powiadomienie po zatwierdzonej zmianie
→ pobrać lub usunąć swoje dane
```

Równocześnie administrator musi móc wykryć awarię, przejrzeć zmianę, opublikować poprawkę, sprawdzić koszt AI i odtworzyć system z zewnętrznego backupu.

## Poza pełnym MVP

Do kolejnych wersji można odłożyć:

- płatne abonamenty i fakturowanie;
- przesyłanie prywatnych dokumentów do analizy AI;
- automatyczne wypełnianie lub składanie wniosków;
- aplikacje mobilne;
- chatbot doradczy;
- ogólnopolskie pokrycie setek źródeł;
- Cloudflare, CDN i architekturę wieloserwerową, dopóki ruch nie uzasadnia ich kosztu.

## Decyzje potrzebne od właściciela

Przed Sprintem 08–09 trzeba wybrać:

1. zewnętrzny magazyn backupów;
2. usługę zewnętrznego monitoringu i kanał alarmów;
3. dostawcę poczty transakcyjnej;
4. dane podmiotu publikującego regulamin i politykę prywatności;
5. początkową grupę użytkowników beta.
