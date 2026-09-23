# DotacjeAI - dostęp dla kolejnej osoby i komputera

Data przygotowania: 2026-09-23

## Decyzja

Nie tworzyć paczki zawierającej pliki `.env`, klucze prywatne, hasła lub tokeny.

Każda osoba i każdy komputer otrzymują własną parę kluczy. Na VPS trafia wyłącznie klucz publiczny. Klucz prywatny pozostaje na komputerze właściciela, jest chroniony passphrase i używany przez lokalny `ssh-agent`.

Korzyści:

- dostęp jednej osoby lub utraconego komputera można odwołać bez wymiany kluczy pozostałym,
- wiadomo, do kogo i urządzenia należy dany klucz,
- nie powstaje wspólna kopia sekretów możliwa do przypadkowego wysłania,
- Codex korzysta z uprawnień lokalnego użytkownika bez poznawania passphrase.

## Rekomendowany model

| Obszar | Człowiek | Automatyzacja |
|---|---|---|
| VPS | osobne konto imienne i osobny klucz na każdym komputerze | konto `deploy` oraz dedykowany klucz maszyny/procesu |
| GitHub | własne konto GitHub, 2FA i własny klucz SSH | GitHub Actions z `GITHUB_TOKEN` lub później dedykowany mechanizm wdrożeniowy |
| `sudo` | własne hasło konta, przechowywane przez użytkownika | tylko ściśle potrzebne polecenia; nie udostępniać hasła |
| Sekrety aplikacji | dostęp przez współdzielony sejf z kontrolą uprawnień | plik `/opt/dotacje-ai/secrets/app.env` na VPS lub docelowy secrets manager |
| Codex | korzysta z lokalnego Git, SSH i `ssh-agent` | nie przechowuje prywatnych kluczy w projekcie |

Dla małego zespołu można technicznie dodać kilka publicznych kluczy do konta `deploy`, ale wspólne konto pogarsza audyt i odbieranie uprawnień. Dla drugiego człowieka zalecane jest konto imienne, np. `anna` albo `jan`. Konto `deploy` należy zachować dla wdrożeń i działań technicznych.

Członkostwo w grupie `docker` daje w praktyce uprawnienia administracyjne. Należy je nadawać wyłącznie zaufanym administratorom, którzy faktycznie zarządzają aplikacją.

## Onboarding nowej osoby

### 1. Utworzenie klucza na jej komputerze

Na drugim komputerze, w PowerShell:

```powershell
ssh-keygen -t ed25519 -a 100 -f "$env:USERPROFILE\.ssh\id_ed25519_dotacjeai" -C "imie@komputer-data"
```

Osoba ustawia własną silną passphrase. Nie przekazuje jej właścicielowi projektu ani przez komunikator.

Do przekazania administratorowi służy wyłącznie:

```text
C:\Users\NAZWA\.ssh\id_ed25519_dotacjeai.pub
```

Przed instalacją administrator i użytkownik porównują fingerprint drugim kanałem:

```powershell
ssh-keygen -lf "$env:USERPROFILE\.ssh\id_ed25519_dotacjeai.pub"
```

### 2. Osobne konto na VPS

Administrator tworzy konto imienne. Przykład dla użytkownika `jan`:

```bash
sudo adduser jan
sudo usermod -aG sudo jan
sudo install -d -o jan -g jan -m 0700 /home/jan/.ssh
sudo install -o jan -g jan -m 0600 /dev/null /home/jan/.ssh/authorized_keys
```

Publiczny klucz użytkownika należy dopisać do `/home/jan/.ssh/authorized_keys`. Jeśli osoba ma zarządzać Dockerem:

```bash
sudo usermod -aG docker jan
```

Po dodaniu klucza należy otworzyć nową sesję i sprawdzić:

```bash
whoami
id
sudo -v
docker ps
```

Nie wolno zamykać sesji administratora przed potwierdzeniem nowego dostępu.

### 3. Konfiguracja Windows

Na komputerze nowej osoby uruchomić usługę agenta w oknie CMD jako administrator:

```cmd
sc config ssh-agent start= auto
net start ssh-agent
ssh-add "%USERPROFILE%\.ssh\id_ed25519_dotacjeai"
```

Opcjonalny wpis w `C:\Users\NAZWA\.ssh\config`:

```text
Host dotacjeai
    HostName 185.69.52.106
    User jan
    IdentityFile ~/.ssh/id_ed25519_dotacjeai
    IdentitiesOnly yes
```

Połączenie:

```powershell
ssh dotacjeai
```

Codex uruchomiony na tym komputerze korzysta z tego samego lokalnego klienta SSH i agenta. Klucza prywatnego nie kopiuje się do `D:\Codex`, repozytorium ani ustawień projektu.

## Dostęp do GitHuba

Druga osoba powinna:

1. posiadać własne konto GitHub z włączonym 2FA,
2. dodać własny klucz publiczny SSH do własnego konta,
3. zostać zaproszona jako collaborator do `Greg259/DotacjeAI`,
4. sklonować repozytorium:

```powershell
git clone git@github.com:Greg259/DotacjeAI.git
```

Nie należy przekazywać jej prywatnego klucza właściciela ani danych logowania do konta `Greg259`. GitHub wymaga lokalnej pary kluczy do uwierzytelnienia SSH i pozwala właścicielowi repozytorium zarządzać dostępem collaboratorów.

## Sekrety i pliki ENV

### Produkcja

Plik produkcyjny pozostaje wyłącznie na VPS:

```text
/opt/dotacje-ai/secrets/app.env
```

Nie trafia do GitHuba, folderu dokumentacji ani paczki onboardingowej. Administrator nie musi kopiować go na komputer, aby czytać dokumentację, rozwijać kod lub wykonywać standardowe polecenia Compose na VPS.

### Lokalne środowisko programistyczne

Repozytorium zawiera tylko `.env.example` z nazwami zmiennych i bez wartości. Każda osoba tworzy własny lokalny `.env` i własne testowe dane dostępowe. Klucze produkcyjne nie powinny być używane lokalnie.

### Współdzielone sekrety operacyjne

Jeżeli druga osoba ma być administratorem awaryjnym, potrzebne dane przekazuje się przez zespołowy menedżer haseł z kontrolą dostępu i historią zmian, a nie przez ZIP, e-mail, GitHub lub rozmowę z Codexem.

Zakres może obejmować:

- dostęp do Time4VPS i procedurę Emergency Console,
- hasło awaryjne `root` tylko dla wyznaczonych administratorów,
- konto home.pl/DNS,
- OpenRouter i pocztę, najlepiej jako osobne klucze per środowisko,
- dane zewnętrznego magazynu backupów.

Po odejściu osoby należy odebrać dostęp do sejfu, GitHuba i VPS oraz obrócić wszystkie współdzielone sekrety, do których miała dostęp.

## Bezpieczna paczka onboardingowa

Dozwolona paczka może zawierać wyłącznie materiały niesekretne:

```text
DotacjeAI-onboarding/
|-- README-START.md
|-- ACCESS_ONBOARDING.md
|-- .env.example
|-- ssh_config.example
`-- CHECKLIST.md
```

Nie może zawierać:

- prywatnych kluczy `id_rsa*`, `id_ed25519*`, `.pem` lub `.ppk`,
- produkcyjnego `.env`,
- haseł, tokenów, cookies i kodów odzyskiwania,
- dumpów bazy oraz prywatnych dokumentów użytkowników,
- kopii katalogu `.ssh`,
- aktywnych danych dostępowych do backupu.

Najlepszą paczką startową jest repozytorium GitHub plus ta dokumentacja. Sekrety i uprawnienia są nadawane osobnym, audytowalnym kanałem.

## Offboarding i zgubiony komputer

Dla konta imiennego należy:

1. usunąć jego linię klucza z `authorized_keys` albo zablokować konto,
2. odebrać dostęp collaboratora w GitHubie,
3. odebrać dostęp do menedżera haseł i paneli dostawców,
4. obrócić współdzielone sekrety, które osoba znała,
5. przejrzeć logi SSH, GitHub i paneli administracyjnych.

Dla zgubionego komputera usuwa się tylko publiczny klucz tego urządzenia. Pozostałe osoby i urządzenia zachowują dostęp.

## Lista danych potrzebnych do dodania osoby

Administrator potrzebuje tylko:

- imienia lub identyfikatora do nazwy konta Linux,
- nazwy użytkownika GitHub,
- publicznego klucza SSH do VPS,
- fingerprintu klucza przekazanego drugim kanałem,
- decyzji, czy osoba potrzebuje `sudo`,
- decyzji, czy osoba potrzebuje grupy `docker`,
- zakresu dostępu do wspólnego sejfu sekretów.

Nigdy nie należy prosić o prywatny klucz ani passphrase.
