# DotacjeAI - optymalizacja kosztów OpenRouter

Stan cen: 2026-09-22. Ceny OpenRouter i dostępność providerów mogą się zmieniać, dlatego aplikacja powinna pobierać koszt zwrócony przez API i przechowywać go przy każdym wywołaniu.

## 1. Wniosek

Tak - większość operacji DotacjeAI może korzystać z modeli znacznie tańszych niż GPT-5.6 Luna. Najbardziej opłacalny układ to lokalna ekstrakcja tekstu z HTML/PDF, tani model dla publicznych danych oraz eskalacja do mocniejszego modelu tylko przy niskiej pewności albo złożonym regulaminie.

## 2. Porównanie cen

Cena za milion tokenów, wejście / wyjście:

| Model | Input | Output | Kontekst | Structured outputs | Rola |
|---|---:|---:|---:|---|---|
| `deepseek/deepseek-v4-flash-0731` | od $0,05 | od $0,16 | 1,31M | tak | najtańsza analiza publicznego tekstu |
| `openai/gpt-5-nano` | $0,05 | $0,40 | 400K | tak | tania ekstrakcja i walidacja |
| `z-ai/glm-5.3-flash` | $0,075 | $0,25 | 1,31M | tak | alternatywny model testowy |
| `google/gemini-2.5-flash-lite` | $0,10 | $0,40 | 1,05M | tak | nie wdrażać - wycofanie 2026-10-20 |
| `openai/gpt-5.6-luna` | $0,20 | $1,20 | 1,05M | tak | mocniejsza eskalacja |
| `openai/gpt-5.6-luna-pro` | $0,20 | $1,20 | 1,05M | tak | trudne, niejednoznaczne przypadki |
| `google/gemini-3.1-flash-lite` | $0,25 | $1,50 | 1,05M | tak | bezpośrednia analiza PDF/obrazu |

Źródła:

- [DeepSeek V4 Flash 0731](https://openrouter.ai/deepseek/deepseek-v4-flash-0731)
- [GPT-5 Nano](https://openrouter.ai/openai/gpt-5-nano/providers)
- [GLM 5.3 Flash](https://openrouter.ai/z-ai/glm-5.3-flash)
- [Gemini 2.5 Flash Lite](https://openrouter.ai/google/gemini-2.5-flash-lite)
- [GPT-5.6 Luna](https://openrouter.ai/openai/gpt-5.6-luna)
- [GPT-5.6 Luna Pro](https://openrouter.ai/openai/gpt-5.6-luna-pro)
- [Gemini 3.1 Flash Lite](https://openrouter.ai/google/gemini-3.1-flash-lite)

## 3. Przykładowy koszt pojedynczej analizy

Założenie: 50 000 tokenów wejścia i 2 000 tokenów odpowiedzi. Kwoty nie uwzględniają opłaty za zakup kredytów, cache, dodatkowych tokenów reasoning ani zmian cen providerów.

| Model | Koszt jednego przebiegu | Koszt 1000 przebiegów |
|---|---:|---:|
| DeepSeek V4 Flash 0731 | około $0,00282 | około $2,82 |
| GPT-5 Nano | około $0,00330 | około $3,30 |
| GLM 5.3 Flash | około $0,00425 | około $4,25 |
| GPT-5.6 Luna | około $0,01240 | około $12,40 |
| Gemini 3.1 Flash Lite | około $0,01550 | około $15,50 |

DeepSeek w tym scenariuszu jest około 77% tańszy od GPT-5.6 Luna. Największe oszczędności powstaną jednak przez niewywoływanie LLM, kiedy hash i deterministyczny diff nie wykazują istotnej zmiany.

## 4. Rekomendowany routing

```dotenv
LLM_MODEL_CLASSIFY=deepseek/deepseek-v4-flash-0731
LLM_MODEL_EXTRACT=deepseek/deepseek-v4-flash-0731
LLM_MODEL_VALIDATE=openai/gpt-5-nano
LLM_MODEL_STRONG=openai/gpt-5.6-luna-pro
LLM_MODEL_MULTIMODAL=google/gemini-3.1-flash-lite
```

### Poziom 0 - bez LLM

- ETag, Last-Modified i HTTP status,
- SHA-256 znormalizowanej treści,
- diff tekstowy,
- wykrywanie nowych linków i dokumentów,
- reguły dat, kwot i lokalizacji, gdy parser ma pewną strukturę.

### Poziom 1 - tani model publiczny

`deepseek/deepseek-v4-flash-0731`:

- klasyfikacja zmiany,
- ekstrakcja danych z lokalnie wydobytego tekstu,
- tagowanie i deduplikacja,
- dane wyłącznie z publicznych dokumentów urzędowych.

### Poziom 2 - walidacja

`openai/gpt-5-nano`:

- drugi niezależny odczyt przy niskiej pewności,
- walidacja zgodności z JSON Schema,
- proste dopasowanie wymagania do profilu bez danych nadmiarowych.

### Poziom 3 - model mocny

`openai/gpt-5.6-luna-pro`:

- wyjątki i sprzeczności w regulaminie,
- wymagania zależne od wielu paragrafów,
- przypadki oznaczone przez tańszy model jako niepewne,
- ponowna analiza odrzucona przez walidację.

### Poziom 4 - multimodal

`google/gemini-3.1-flash-lite`:

- skany, tabele i wykresy, których nie obsłuży lokalny OCR,
- bezpośrednie wejście PDF tylko wtedy, gdy ekstrakcja lokalna zawiedzie.

## 5. Batch i cache

- Batch może obniżyć koszt części modeli o około 50%, ale nadaje się wyłącznie do zadań asynchronicznych.
- Batch stosować dla publicznych dokumentów, nie dla prywatnych danych użytkowników bez sprawdzenia zasad retencji.
- Cache promptów wykorzystać dla stałych instrukcji i schematów, jeśli provider je obsługuje.
- Nie wysyłać całej historii wersji; wysyłać aktualny dokument, istotny diff i potrzebne fragmenty źródeł.

## 6. Warunki wdrożenia tańszego modelu

Cena nie może być jedynym kryterium. Przed aktywacją należy przygotować 20-30 reprezentatywnych regulaminów i mierzyć:

- poprawność pól,
- kompletność wymagań,
- poprawność cytowania strony/paragrafu,
- liczbę nieobsługiwanych wyjątków,
- zgodność z JSON Schema,
- koszt i czas odpowiedzi,
- zgodność wyników po ponownym uruchomieniu.

Model tani powinien zostać domyślnym dopiero po osiągnięciu ustalonego progu jakości. Dane o niskiej pewności zawsze trafiają do REVIEW.

## 7. Prywatność

- Dla danych użytkowników wymuszać `provider.data_collection=deny`.
- Jeśli dostępne, wymuszać `provider.zdr=true`.
- Dla publicznych dokumentów można korzystać z szerszej puli providerów.
- Dla prywatnych dokumentów używać jawnej listy zatwierdzonych providerów.
- Nie używać aliasu `openrouter/auto` w audytowalnym pipeline.

Dokumentacja funkcji JSON Schema: [Structured Outputs](https://openrouter.ai/docs/guides/features/structured-outputs).
