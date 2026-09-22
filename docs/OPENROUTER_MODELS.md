# OpenRouter - rekomendacja modeli dla DotacjeAI

Data rekomendacji: 2026-09-22

## Rekomendowany zestaw startowy

### Model szybki

`openai/gpt-5.6-luna`

Zastosowanie:

- klasyfikacja, czy zmiana źródła jest istotna,
- ekstrakcja prostych pól,
- deduplikacja i tagowanie,
- streszczenia na podstawie zatwierdzonych danych.

Model obsługuje pliki, duży kontekst i structured outputs. Według katalogu OpenRouter koszt wynosi obecnie 0,20 USD za milion tokenów wejściowych i 1,20 USD za milion tokenów wyjściowych.

### Model dokładny

`openai/gpt-5.6-luna-pro`

Zastosowanie:

- złożone regulaminy,
- konfliktujące zapisy i wyjątki,
- analiza wymagań kwalifikacyjnych,
- ponowna analiza wyniku o niskiej pewności.

Wariant Pro używa silniejszego trybu rozumowania, zachowując obsługę structured outputs i plików PDF.

### Model walidacyjny / alternatywny

`google/gemini-3.8-flash`

Zastosowanie:

- drugi niezależny od OpenAI odczyt trudnego dokumentu,
- analiza dokumentów zawierających tabele, obrazy lub skany,
- testy porównawcze ekstrakcji.

Model przyjmuje tekst, obrazy i PDF, obsługuje JSON Schema i ma kontekst około miliona tokenów. Nie powinien być wywoływany dla każdej zmiany - tylko do walidacji trudnych przypadków.

## Konfiguracja aplikacji

```dotenv
LLM_PROVIDER=openrouter
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
OPENROUTER_API_KEY=
LLM_MODEL_FAST=openai/gpt-5.6-luna
LLM_MODEL_STRONG=openai/gpt-5.6-luna-pro
LLM_MODEL_VALIDATOR=google/gemini-3.8-flash
LLM_DAILY_BUDGET_USD=5
LLM_MONTHLY_BUDGET_USD=100
```

## Zasady implementacyjne

- Wymuszać `response_format.type=json_schema`, `strict=true` i walidację Pydantic.
- Ustawiać `provider.require_parameters=true`, aby routing wybierał tylko endpointy obsługujące wymagane parametry.
- Dla danych użytkowników wymuszać `provider.data_collection=deny` i, jeśli dostępne, `provider.zdr=true`.
- Nie wysyłać niepotrzebnych danych osobowych ani całych prywatnych dokumentów.
- Zapisywać model, wersję promptu, tokeny, koszt i wynik walidacji.
- Nie używać aliasu `openrouter/auto` w przepływach audytowalnych; jawny model daje powtarzalniejsze wyniki.
- Uruchomić test porównawczy na 20-30 rzeczywistych regulaminach przed ostatecznym wyborem modeli.

## Uwaga o prywatności

OpenRouter przekazuje wejście do wybranego dostawcy modelu. Polityki retencji i trenowania mogą różnić się między providerami. Dla dokumentów użytkowników potrzebna jest konfiguracja prywatności, minimalizacja danych oraz osobna analiza RODO.
