# OpenRouter — modele dla DotacjeAI

Aktualizacja: 2026-09-24. Ceny i dostępność należy ponownie sprawdzać w publicznym katalogu OpenRouter przed zmianą konfiguracji.

## Konfiguracja produkcyjna

```dotenv
LLM_PROVIDER=openrouter
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
OPENROUTER_API_KEY=
LLM_MODEL_FAST=openai/gpt-6-luna
LLM_MODEL_STRONG=openai/gpt-6-luna-pro
LLM_MODEL_VALIDATOR=openai/gpt-6-luna
LLM_DAILY_BUDGET_USD=1
LLM_WARNING_BUDGET_USD=5
LLM_CRITICAL_BUDGET_USD=8
LLM_MONTHLY_BUDGET_USD=10
```

Klucz pozostaje pusty w przykładzie i repozytorium. Produkcyjny klucz jest przechowywany wyłącznie w `/opt/dotacje-ai/secrets/app.env` z trybem `0600`.

## Wybór modeli

| Rola | Model | Input / 1M | Output / 1M | Uzasadnienie |
|---|---|---:|---:|---|
| domyślna ekstrakcja | `openai/gpt-6-luna` | 0,10 USD | 0,50 USD | niski koszt, duży kontekst, JSON Schema |
| naprawa trudnego wyniku | `openai/gpt-6-luna-pro` | 0,10 USD | 0,50 USD | tryb Pro tylko po błędzie walidacji |
| alternatywa do benchmarku | `google/gemini-2.5-flash-lite` | 0,10 USD | 0,40 USD | tani structured output; nie jest obecnie modelem produkcyjnym |

Ceny pochodzą z publicznego endpointu `GET https://openrouter.ai/api/v1/models` odczytanego 2026-09-24. OpenRouter może je zmienić.

## Wymagania techniczne

- `response_format.type=json_schema`,
- `json_schema.strict=true`,
- `provider.require_parameters=true`,
- brak parametrów niewspieranych przez wybrany model,
- wszystkie pola ścisłego schematu wymagane, a opcjonalność reprezentowana przez `null`,
- końcowa walidacja Pydantic po odpowiedzi modelu,
- maksymalnie jedna próba naprawcza,
- zapis modelu, tokenów, kosztu, czasu i statusu,
- brak automatycznej publikacji.

Dokumentacja: [Structured Outputs](https://openrouter.ai/docs/guides/features/structured-outputs), [Models API](https://openrouter.ai/docs/api/api-reference/models/get-models).

## Wynik pierwszego benchmarku

- 3 kandydatów gotowych do ręcznego REVIEW,
- 8 rozliczonych odpowiedzi, wliczając odpowiedzi odrzucone podczas dostrajania schematu,
- 255521 tokenów wejściowych i 22984 wyjściowe,
- koszt łączny: 0,026836 USD,
- ponowne uruchomienie: 0 nowych wywołań i 0 dodatkowego kosztu.

Klucz użyty podczas benchmarku został ujawniony w rozmowie i musi zostać obrócony przed dalszą eksploatacją.
