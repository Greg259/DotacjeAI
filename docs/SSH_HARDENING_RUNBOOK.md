# DotacjeAI - bezpieczne utwardzenie SSH

Data przygotowania: 2026-09-23
Status: instrukcja gotowa, zmiany nie zostały jeszcze wykonane.

## Cel

- logowanie do VPS wyłącznie kluczem SSH jako `deploy`,
- działające `sudo` i Docker dla `deploy`,
- brak logowania SSH hasłem,
- brak bezpośredniego logowania SSH jako `root`,
- nowe, nieujawnione hasła lokalne dla `deploy` i `root`.

## Zasady bezpieczeństwa

1. Najpierw sprawdzić dostęp do konsoli ratunkowej VPS u dostawcy.
2. Nie zamykać bieżącej sesji `root` przed zakończeniem wszystkich testów.
3. Otwierać testy w drugiej i trzeciej sesji terminala.
4. Nowych haseł nie wpisywać do rozmowy, skryptów, GitHuba ani dokumentacji.
5. Nie kopiować na serwer żadnego klucza prywatnego. Dla VPS kopiowany jest wyłącznie `id_rsa_time4vps.pub`.
6. Przed przeładowaniem SSH zawsze wykonać `sshd -t`.

## Etap 0 - przygotowanie

Na komputerze administratora istnieją rozdzielone pary kluczy:

- GitHub: `id_ed25519` oraz `id_ed25519.pub`,
- VPS: `id_rsa_time4vps` oraz `id_rsa_time4vps.pub`.

Zalecane jest zabezpieczenie klucza prywatnego passphrase oraz przechowywanie kopii odzyskiwania w bezpiecznym miejscu.

Przed zmianami należy zalogować się do panelu dostawcy VPS i potwierdzić dostęp do konsoli/KVM. Konsola jest drogą odzyskania dostępu, jeśli konfiguracja SSH okaże się błędna.

### SSH Key Management w Time4VPS

W panelu można zapisać ten sam klucz publiczny pod nazwą, np. `grzeg-dotacjeai-2026`. Do pola klucza należy wkleić całą pojedynczą linię wyświetloną lokalnie przez:

```powershell
Get-Content $env:USERPROFILE\.ssh\id_ed25519.pub
```

Nie należy wklejać zawartości pliku `id_ed25519` bez rozszerzenia `.pub`. Według instrukcji Time4VPS zapisany klucz wybiera się podczas instalacji lub reinstalacji systemu. Nie należy zakładać, że samo dodanie go w panelu zmieni działający VPS albo konto `deploy`; klucz zostanie również zainstalowany bezpośrednio w `authorized_keys` istniejącego konta.

Formularz odrzucił istniejący klucz ED25519, ale zaakceptował osobny klucz RSA 4096 utworzony dla VPS:

- prywatny: `C:\Users\grzeg\.ssh\id_rsa_time4vps`,
- publiczny: `C:\Users\grzeg\.ssh\id_rsa_time4vps.pub`,
- nazwa w panelu: `grzeg-dotacjeai-rsa-2026`.

Klucz prywatny RSA powinien być chroniony passphrase i nie może być kopiowany na serwer ani do repozytorium. W dalszych krokach publiczna część RSA będzie instalowana na koncie `deploy`; klucz ED25519 pozostaje używany przez GitHub.

## Etap 1 - dodać klucz publiczny do `deploy`

Z PowerShell na komputerze administratora:

```powershell
scp $env:USERPROFILE\.ssh\id_rsa_time4vps.pub root@185.69.52.106:/tmp/grzeg_id_rsa_time4vps.pub
ssh root@185.69.52.106
```

W otwartej sesji `root`:

```bash
install -d -o deploy -g deploy -m 0700 /home/deploy/.ssh
touch /home/deploy/.ssh/authorized_keys
grep -qxF "$(cat /tmp/grzeg_id_rsa_time4vps.pub)" /home/deploy/.ssh/authorized_keys || cat /tmp/grzeg_id_rsa_time4vps.pub >> /home/deploy/.ssh/authorized_keys
chown deploy:deploy /home/deploy/.ssh/authorized_keys
chmod 0600 /home/deploy/.ssh/authorized_keys
rm /tmp/grzeg_id_rsa_time4vps.pub
namei -l /home/deploy/.ssh/authorized_keys
```

Oczekiwane uprawnienia:

- `/home/deploy`: bez zapisu dla innych użytkowników,
- `.ssh`: `deploy:deploy`, tryb `0700`,
- `authorized_keys`: `deploy:deploy`, tryb `0600`.

## Etap 2 - ustawić hasła lokalne

Konto `deploy` utworzono wcześniej z opcją `--disabled-password`. Bez ustawienia hasła logowanie kluczem zadziała, ale standardowe `sudo` nie będzie mogło potwierdzić tożsamości użytkownika.

W pozostawionej sesji `root`:

```bash
passwd deploy
passwd root
```

Należy ustawić dwa różne, losowe hasła i zapisać je wyłącznie w menedżerze haseł. Hasło `deploy` będzie używane lokalnie przez `sudo`; po końcowej konfiguracji nie będzie akceptowane jako metoda logowania SSH. Nowe hasło `root` pozostaje potrzebne do dostępu przez konsolę dostawcy.

## Etap 3 - test `deploy` przed utwardzeniem

Nie zamykając sesji `root`, otworzyć drugi PowerShell:

```powershell
ssh -i $env:USERPROFILE\.ssh\id_rsa_time4vps deploy@185.69.52.106
```

Po zalogowaniu:

```bash
id
sudo -v
sudo whoami
docker ps
cd /opt/dotacje-ai/app/infra
docker compose --env-file /opt/dotacje-ai/secrets/app.env ps
```

Warunki przejścia dalej:

- `id` pokazuje grupy `sudo` i `docker`,
- `sudo whoami` zwraca `root`,
- `docker ps` działa bez `sudo`,
- wszystkie kontenery mają status `healthy`.

Jeśli którykolwiek test nie przejdzie, nie wolno wyłączać logowania hasłem ani roota.

## Etap 4 - utwardzić konfigurację SSH

W działającej sesji `deploy` po udanym teście:

```bash
sudo cp -a /etc/ssh/sshd_config /etc/ssh/sshd_config.before-dotacje-ai
sudo cp -a /etc/ssh/sshd_config.d /etc/ssh/sshd_config.d.before-dotacje-ai
sudoedit /etc/ssh/sshd_config.d/00-dotacje-ai-hardening.conf
```

Treść pliku:

```text
PubkeyAuthentication yes
PasswordAuthentication no
KbdInteractiveAuthentication no
PermitRootLogin no
PermitEmptyPasswords no
MaxAuthTries 3
X11Forwarding no
```

Następnie:

```bash
sudo chmod 0600 /etc/ssh/sshd_config.d/00-dotacje-ai-hardening.conf
sudo /usr/sbin/sshd -t
sudo /usr/sbin/sshd -T | grep -E '^(pubkeyauthentication|passwordauthentication|kbdinteractiveauthentication|permitrootlogin|permitemptypasswords|maxauthtries|x11forwarding) '
```

Oczekiwane wartości obejmują:

```text
pubkeyauthentication yes
passwordauthentication no
kbdinteractiveauthentication no
permitrootlogin no
permitemptypasswords no
maxauthtries 3
x11forwarding no
```

Dopiero jeśli składnia i konfiguracja efektywna są poprawne:

```bash
sudo systemctl reload ssh
sudo systemctl is-active ssh
```

Użycie `reload` pozwala pozostawić istniejące sesje aktywne.

## Etap 5 - test po przeładowaniu

Otworzyć trzeci PowerShell i ponownie sprawdzić klucz:

```powershell
ssh -i $env:USERPROFILE\.ssh\id_rsa_time4vps deploy@185.69.52.106
```

Sprawdzić odrzucenie hasła:

```powershell
ssh -o PubkeyAuthentication=no -o PreferredAuthentications=password,keyboard-interactive deploy@185.69.52.106
```

Drugie polecenie powinno zakończyć się odmową dostępu. Bezpośrednia próba logowania jako `root` również powinna zostać odrzucona.

## Etap 6 - kontrola usług

W sesji `deploy`:

```bash
sudo systemctl is-active ssh fail2ban docker
sudo fail2ban-client status sshd
sudo ufw status verbose
sudo ss -lntup
cd /opt/dotacje-ai/app/infra
docker compose --env-file /opt/dotacje-ai/secrets/app.env ps
curl -fsS https://dotacjeai.eu/health
curl -fsS https://dotacjeai.eu/api/health
```

Publicznie powinny pozostać dostępne wyłącznie porty 22, 80 i 443. PostgreSQL i Redis nie mogą publikować portów na hoście.

## Procedura wycofania

Jeśli nowa sesja nie działa, ale stara sesja administracyjna pozostaje otwarta:

```bash
sudo mv /etc/ssh/sshd_config.d/00-dotacje-ai-hardening.conf /etc/ssh/sshd_config.d/00-dotacje-ai-hardening.conf.disabled
sudo /usr/sbin/sshd -t
sudo systemctl reload ssh
```

Jeśli wszystkie sesje zostały utracone, należy wykonać te same czynności przez konsolę dostawcy VPS.

## Kryteria zakończenia

- nowa sesja `deploy` działa przy użyciu klucza,
- `sudo` i Docker działają,
- próba logowania hasłem kończy się odmową,
- bezpośrednie logowanie `root` kończy się odmową,
- SSH, fail2ban, UFW, Docker i aplikacja działają,
- nowe hasła znajdują się wyłącznie w menedżerze haseł,
- konfiguracja oraz wyniki testów są zapisane w dokumentacji technicznej.
