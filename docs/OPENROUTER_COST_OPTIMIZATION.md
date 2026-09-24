# DotacjeAI — optymalizacja kosztów OpenRouter

Stan: 2026-09-24.

## Najważniejszy wniosek

Największa oszczędność nie wynika z wyboru najtańszego modelu, lecz z pomijania LLM, gdy hash źródła się nie zmienił, oraz z ponownego używania zapisanego wyniku dla tego samego snapshotu i wersji żądania.

Aktualny układ produkcyjny:

1. ETag, Last-Modified, SHA-256 i diff bez LLM.
2. Reguły deterministyczne dla stabilnych, jawnie dopuszczonych źródeł.
3. `openai/gpt-6-luna` dla złożonej ekstrakcji.
4. `openai/gpt-6-luna-pro` najwyżej raz po błędzie walidacji.
5. Ręczny REVIEW przed zatwierdzeniem i osobna publikacja.

## Limity

| Próg | Wartość |
|---|---:|
| dzienny | 1 USD |
| ostrzeżenie miesięczne | 5 USD |
| alarm krytyczny | 8 USD |
| twardy limit miesięczny | 10 USD |
| limit pierwszego benchmarku | 0,50 USD |

Pierwszy benchmark kosztował 0,026836 USD, czyli około 5,4% limitu benchmarku i około 0,27% limitu miesięcznego.

## Zasady kosztowe

- nie wywoływać LLM dla HTTP 304 ani identycznego hasha,
- ograniczać tekst źródła do skonfigurowanego maksimum,
- zapisywać koszt również dla odpowiedzi odrzuconej przez walidację,
- nie ponawiać prawidłowo zapisanej odpowiedzi,
- mocniejszy model uruchamiać tylko po odrzuceniu wyniku modelu podstawowego,
- nie używać aliasu `openrouter/auto` w audytowalnym przepływie,
- przed każdym wywołaniem sprawdzać koszt dzienny i miesięczny,
- ceny weryfikować przez oficjalny Models API, ponieważ są zmienne.

## Dalszy benchmark

Ostateczny wybór modelu powinien opierać się na zestawie 20–30 ręcznie opisanych regulaminów. Mierzymy poprawność statusu, terminu, kwoty, procentu, beneficjentów, cytatów, zgodność JSON Schema, koszt i czas. Tani model może zostać domyślnym wyłącznie po osiągnięciu ustalonego progu jakości.

Źródła: [OpenRouter Models API](https://openrouter.ai/docs/api/api-reference/models/get-models), [Structured Outputs](https://openrouter.ai/docs/guides/features/structured-outputs).
