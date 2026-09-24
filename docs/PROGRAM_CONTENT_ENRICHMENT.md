# Rozszerzone karty programów i formularze

Stan produkcyjny: 2026-09-24.

## Cel

Karta dotacji nie ogranicza się już do krótkiego opisu, terminu i jednej kwoty. Publiczne API oraz frontend obsługują wersjonowane informacje praktyczne:

- najważniejsze wnioski,
- grupy uprawnionych wnioskodawców,
- warunki przyznania wsparcia,
- warianty kwot i poziomów dofinansowania,
- ograniczenia i ryzyka,
- kroki złożenia wniosku,
- wymagane dokumenty,
- oficjalne formularze, oświadczenia, instrukcje, regulaminy i portale.

Każdy fakt może zawierać `source_reference` oraz `source_url`. Linki formularzy wolno publikować wyłącznie wtedy, gdy prowadzą do oficjalnej strony instytucji lub dokumentu znalezionego w oficjalnym źródle.

## Przepływ danych

1. Crawler zapisuje treść i pliki źródłowe oraz wykrywa zmianę hasha.
2. Ekstrakcja `extraction-v2` tworzy pola podstawowe i sekcję `details`.
3. Model ma zakaz zgadywania wymagań i tworzenia adresów URL. Każdy praktyczny wniosek musi mieć wskazanie źródła.
4. Wynik trafia do prywatnego REVIEW. Nie jest publikowany automatycznie.
5. Zatwierdzona treść tworzy nowy `ProgramVersion`; formularze są synchronizowane do `ProgramDocument`.
6. Publiczne API odczytuje `details` wyłącznie z najnowszej zatwierdzonej wersji.

Ręcznie zweryfikowaną treść można wprowadzić przez:

```bash
cd /opt/dotacje-ai/app
bash server/program_content_cli.sh PROGRAM_SLUG < program-content/PROGRAM_SLUG.json
```

Operacja zapisuje nową wersję i wpis audit log. Pliki wzorcowe dla dwóch pierwszych programów znajdują się w `program-content/`.

## Pierwsze karty produkcyjne

### Gmina Nadarzyn

Karta wskazuje zakończenie naboru 31 lipca 2026 r., limit 6000 zł i do 100% kosztu zakupu urządzenia, wymóg zawarcia umowy przed inwestycją, wyłączenie kosztów montażu oraz listę załączników. Udostępnia oficjalny wniosek, oświadczenie o prawie do nieruchomości, regulamin, uchwałę i stronę ogłoszenia.

### Czyste Powietrze

Karta opisuje beneficjentów, wymóg własności, audyt i DPAE, trzy poziomy wsparcia do 40%, 70% i 100%, rolę operatora oraz sposób złożenia dokumentów. Udostępnia GWD, instrukcję WOD, instrukcję składania wniosku, aktualną stronę dokumentów i załącznik z kosztami kwalifikowanymi.

## Walidacja wdrożenia

- commit aplikacyjny: `12833a7`,
- GitHub Actions run 27: `success`,
- Ruff: bez błędów,
- testy API: 24/24,
- frontend: typecheck i produkcyjny build zakończone sukcesem,
- obie publiczne karty zwracają HTTP 200 i zawierają nowe sekcje,
- obie zatwierdzone wersje programów mają numer 2,
- pięć kontenerów jest zdrowych, a logi po wdrożeniu nie zawierają błędów,
- backup po zmianie: `0049f91e`; kontrola Restic, sum i pełny import PostgreSQL zakończyły się sukcesem.

W tej zmianie nie wykonano nowego wywołania OpenRouter. Treść została opracowana i ręcznie zweryfikowana na podstawie oficjalnych dokumentów. Prompt i schemat są przygotowane do takiej ekstrakcji przy kolejnych zmianach źródeł, ale publikacja nadal wymaga REVIEW.
