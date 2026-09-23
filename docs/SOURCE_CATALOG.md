# DotacjeAI — katalog źródeł MVP-0

Stan weryfikacji: 2026-09-23.

Statusy są danymi zmiennymi. Crawler ma je ponownie ustalać z oficjalnych źródeł; poniższa tabela stanowi punkt początkowy i zestaw testowy.

| Priorytet | Program lub źródło | Oficjalny URL | Stan początkowy | Rola w MVP |
|---|---|---|---|---|
| P0 | WFOŚiGW Warszawa — Czyste Powietrze | https://wfosigw.pl/czyste-powietrze/ogloszenie-o-naborze/ | otwarta; zmiana programu 20.07.2026 | pierwszy pełny crawler strony i załączników |
| P0 | Gmina Nadarzyn — regulamin dotacji na wymianę źródła ciepła | https://www.nadarzyn.pl/plik%2C23325%2Cregulamin-zalacznik-nr-1-do-uchwaly-nr-xxv-564-2026-pdf.pdf | zakończona; termin 31.07.2026 | test PDF, daty końcowej i statusu `closed` |
| P1 | NFOŚiGW — harmonogram naborów | https://www.gov.pl/web/nfosigw/harmonogram-naborow | mieszane: otwarte i planowane | źródło zbiorcze i wykrywanie zmian statusów |
| P1 | Moje Ciepło | https://mojecieplo.gov.pl/ | otwarta do 26.02.2027 lub wyczerpania środków | pompy ciepła, CWU, nowy dom |
| P1 | Przydomowe magazyny energii | https://przydomowemagazyny.gov.pl/ | wymaga śledzenia części i kolejnych naborów | PV, magazyn energii i magazyn ciepła |
| P1 | Moja Elektrownia Wiatrowa | https://mojaelektrowniawiatrowa.gov.pl/ | zakończona 20.02.2026 | test wcześniejszego zamknięcia po wyczerpaniu budżetu |
| P1 | Ciepłe Mieszkanie | https://czystepowietrze.gov.pl/inne-programy/cieple-mieszkanie | nabory zależne od gmin | mieszkania, najemcy i wspólnoty mieszkaniowe |

## Potwierdzone reguły testowe

### Czyste Powietrze

- oficjalna strona WFOŚiGW w Warszawie,
- program i dokumentacja zmienione 20.07.2026,
- dotyczy właścicieli lub współwłaścicieli budynków jednorodzinnych albo wydzielonych lokali w takich budynkach,
- wymaga monitorowania strony oraz załączników i regulaminów.

### Gmina Nadarzyn

- regulamin przyjęty w 2026 r.,
- dotacja obejmuje do 100% udokumentowanego kosztu zakupu nowego źródła ciepła,
- maksymalna kwota: 6000 zł,
- termin składania wniosków w 2026 r.: 31.07.2026,
- według stanu na 23.09.2026 program ma być prezentowany jako zakończony,
- sam dokument powinien pozostać dostępny w historii programu.

Znana sprzeczność źródeł: starsza oficjalna podstrona `https://www.nadarzyn.pl/816%2Cwymiana-kotlow-do-centralnego-ogrzewania` nadal opisuje uchwałę z 2021 r. oraz warunki 60% i maksymalnie 5000 zł. Dla edycji 2026 pierwszeństwo ma nowszy, datowany regulamin PDF wskazujący 100% i maksymalnie 6000 zł. Crawler ma zachować obie wersje, rozpoznać konflikt i utworzyć zadanie REVIEW.

### Moje Ciepło

- nabór ciągły do 26.02.2027 albo do wyczerpania środków,
- beneficjenci: osoby fizyczne inwestujące w nowe budynki jednorodzinne,
- kategorie: pompa ciepła, ogrzewanie i CWU.

### Moja Elektrownia Wiatrowa

- nabór zamknięto 20.02.2026 o 08:00,
- przyczyną było wyczerpanie dostępnej alokacji przed pierwotnym terminem,
- statusu nie wolno ustalać wyłącznie na podstawie pierwotnej daty końcowej.

### Ciepłe Mieszkanie

- program jest realizowany przez gminy,
- obejmuje lokale w budynkach wielorodzinnych, określonych najemców i wspólnoty mieszkaniowe 3–7 lokali,
- centralna strona programu nie wystarcza do ustalenia dostępności dla mieszkańca; konieczne jest monitorowanie strony właściwej gminy.

## Zasady wiarygodności

- źródło oficjalne ma pierwszeństwo przed artykułem, agregatorem i materiałem marketingowym,
- każdy dokument otrzymuje URL, czas pobrania, typ MIME, SHA-256 i wersję,
- status, termin, kwota i poziom wsparcia muszą wskazywać dowód źródłowy,
- sprzeczność między harmonogramem, stroną programu i PDF-em tworzy zadanie REVIEW,
- brak danych jest zapisywany jako `unknown`, bez zgadywania przez LLM.
