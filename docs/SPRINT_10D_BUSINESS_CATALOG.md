# Sprint 10D — prawdziwy katalog programów dla firm

Data wdrożenia: 2026-09-27.

## Wynik

Sprint dostarcza kontrolowany katalog 40 programów i naborów dla przedsiębiorstw:

- 24 nabory otwarte,
- 2 nabory planowane,
- 14 świeżo zakończonych, zachowanych informacyjnie z prawidłowym statusem,
- programy PARP, NCBR, BGK oraz krajowe i regionalne Fundusze Europejskie,
- 40 scenariuszy pozytywnych, 40 negatywnych i 40 scenariuszy „brak danych”.

Źródłem bazowym jest oficjalny wykaz Ministerstwa Funduszy i Polityki Regionalnej „Nabory z Funduszy Europejskich i KPO we wrześniu 2026 roku” oraz dołączone do niego arkusze krajowe i regionalne. Dwa programy BGK zostały sprawdzone na oficjalnych stronach BGK.

## Zasady jakości danych

- Katalog przechowuje oficjalny URL, instytucję, daty, status, grupę docelową, obszar, budżet całego naboru i dowód pochodzenia rekordu.
- Budżet konkursu nie jest prezentowany jako maksymalna kwota dla jednego wnioskodawcy.
- Brak potwierdzonej wartości PKD, de minimis lub wkładu własnego jest pokazywany jako „do potwierdzenia w regulaminie”, a nie uzupełniany szacunkiem.
- Kody PKD, de minimis, koszty kwalifikowane, wkład własny i reguła konsorcjum mają osobną, ustrukturyzowaną sekcję na karcie programu.
- Nabory zakończone nie otrzymują wyniku kwalifikującego z powodu blokującej reguły statusu.
- AI nie podejmuje decyzji o kwalifikacji. Matching pozostaje deterministyczny i pokazuje dowód źródłowy.

## Implementacja

- Manifest: `content/business-programs-2026-09.json`.
- Walidacja i idempotentny import: `app.services.business_catalog`.
- CLI: `python -m app.cli.import_business_catalog`.
- Wersja aplikacji: `0.12.0`.
- Import tworzy lub aktualizuje program, źródło, wersję, dokument, relacje filtrów i audit log.
- Ponowne uruchomienie tego samego manifestu nie tworzy kolejnych wersji.
- Oficjalny wykaz zbiorczy jest monitorowany cyklicznie; zmiany nadal wymagają standardowego REVIEW. Strony pojedynczych naborów są zapisane jako dowody i będą włączane do monitoringu etapami podczas wzbogacania regulaminów.

## Testy

Test `test_business_catalog.py` sprawdza:

1. dokładnie 40 unikalnych programów,
2. obecność PARP, NCBR, BGK i źródeł regionalnych,
3. dowód dla pól firmowych,
4. wynik pozytywny, negatywny i „brak danych” dla każdego programu,
5. idempotencję importu 40 + 40 rekordów.

## Operacje produkcyjne

Po wdrożeniu obrazu API katalog importuje się poleceniem:

```bash
cd /opt/dotacje-ai/app/infra
docker compose run --rm --no-deps api python -m app.cli.import_business_catalog
```

Kontrola odbiorowa powinna potwierdzić liczbę kart, rozkład statusów, działanie filtrów firmowych, trzy warianty matchingu oraz brak nowych nieuzasadnionych zadań REVIEW.

## Ograniczenie świadome

Arkusze miesięczne potwierdzają przede wszystkim status, termin, grupę docelową, zakres i budżet naboru. Szczegółowe wartości pomocy publicznej i pełne listy kosztów będą stopniowo wzbogacane z regulaminów indywidualnych. Do tego czasu aplikacja jawnie sygnalizuje brak danych zamiast obiecywać kwalifikację.

## Odbiór produkcyjny

- Commit aplikacji: `aee5bdb3400e9ee2fee0f253c2a771a79e65175d`.
- GitHub Actions: run 54, wynik `success`.
- API: wersja `0.12.0`.
- Publiczny katalog firmowy: 40 kart, w tym 24 otwarte, 2 planowane i 14 zakończonych.
- Wszystkie pięć kontenerów: `healthy`.
- Publiczna karta BGK i sekcja warunków firmowych: HTTP 200.
- Backup przed wdrożeniem: Restic `075946ec`; kontrola repozytorium, sum SHA-256 i pełne odtworzenie PostgreSQL zakończone poprawnie.
- Monitoring: `OK` dla HTTPS, API, kontenerów, dysku i świeżości backupu.
