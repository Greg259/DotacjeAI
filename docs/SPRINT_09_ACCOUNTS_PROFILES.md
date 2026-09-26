# Sprint 09A — konta i profile nieruchomości

Data: 2026-09-26.

## Cel

Pierwsza część Sprintu 09 udostępnia działające konta oparte na nazwie użytkownika i haśle, bez zbierania oraz potwierdzania adresu e-mail. Użytkownik może tworzyć profile nieruchomości, pobrać swoje dane i trwale usunąć konto.

Integracja poczty, odzyskiwanie hasła przez e-mail, matching oraz powiadomienia pozostają następnymi etapami.

## Zakres

- publiczna rejestracja i logowanie nazwą użytkownika;
- role `user`, `editor` i `admin`; samodzielna rejestracja zawsze nadaje rolę `user`;
- solone hashowanie hasła algorytmem scrypt;
- losowe, niejawne tokeny sesji; w bazie zapisywany jest wyłącznie SHA-256 tokenu;
- sesja w ciasteczku `HttpOnly`, `Secure`, `SameSite=Lax`;
- osobny token CSRF dla wszystkich operacji zmieniających dane;
- profile domu jednorodzinnego, mieszkania i wspólnoty;
- beneficjent, lokalizacja, stan budynku, źródło ciepła, rok budowy i powierzchnia;
- wybór wielu planowanych inwestycji;
- tworzenie, odczyt, edycja i usuwanie wyłącznie własnych profili;
- eksport konta i profili do JSON bez hasła i tokenów;
- usunięcie konta po ponownym podaniu hasła wraz z sesjami i profilami;
- wersjonowana akceptacja regulaminu i informacji o prywatności;
- techniczne strony regulaminu i prywatności dla wersji testowej;
- CLI do bezpiecznego tworzenia kont technicznych i testowych bez hasła w Git.

## Model danych

Migracja `d9f4a2c68130` dodaje:

- `users` — konto, rola, aktywność oraz daty zgód;
- `user_sessions` — zahashowane tokeny, CSRF, termin wygaśnięcia i podstawowe dane bezpieczeństwa;
- `property_profiles` — strukturalne dane nieruchomości należące do użytkownika;
- `profile_investment_categories` — cele planowanej inwestycji.

Usunięcie użytkownika usuwa zależne sesje, profile oraz kategorie profili. Lokalizacja może zostać usunięta bez kasowania profilu — wtedy profil zachowuje pozostałe dane i otrzymuje pustą lokalizację.

## Endpointy

| Metoda | Ścieżka | Cel |
|---|---|---|
| POST | `/api/auth/register` | rejestracja i rozpoczęcie sesji |
| POST | `/api/auth/login` | logowanie |
| GET | `/api/auth/me` | dane bieżącego konta |
| POST | `/api/auth/logout` | wylogowanie |
| GET | `/api/auth/export` | eksport danych JSON |
| DELETE | `/api/auth/me` | usunięcie konta po potwierdzeniu hasła |
| GET | `/api/profiles/options` | słowniki formularza profilu |
| GET/POST | `/api/profiles` | lista i utworzenie profilu |
| GET/PUT/DELETE | `/api/profiles/{id}` | odczyt, edycja i usunięcie własnego profilu |

## Interfejs

- `/konto/rejestracja`;
- `/konto/logowanie`;
- `/konto`;
- `/konto/profil/nowy`;
- `/konto/profil/{id}`;
- `/regulamin`;
- `/prywatnosc`.

## Konto testowe `user1`

Konto produkcyjne `user1` należy utworzyć po migracji przy użyciu CLI. Hasło jest generowane losowo i zapisywane wyłącznie w chronionym pliku `/opt/dotacje-ai/secrets/user1-initial-password` z prawami `600`. Nie trafia do kodu, dokumentacji, Git ani rozmowy.

## Ograniczenia bieżącego etapu

- adres e-mail nie jest zbierany;
- nie ma potwierdzania adresu ani automatycznego resetu hasła;
- administrator może awaryjnie ustawić nowe hasło przez CLI;
- role redaktora i administratora są zapisane w modelu, ale istniejący panel `/admin` nadal jest chroniony osobnym Basic Auth;
- profile nie są jeszcze oceniane przez silnik dopasowania;
- dokumenty prawne są techniczną wersją dla testów i wymagają danych administratora przed publiczną betą.

## Następny etap

Sprint 10 powinien wykorzystać zapisane profile do deterministycznego matchingu `spełnione / niespełnione / brak danych`, bez przekazywania AI decyzji o kwalifikacji.
