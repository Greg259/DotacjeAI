# Przygotowanie serwera DotacjeAI

Data przygotowania: 2026-09-22

## Serwer

- Ubuntu Server 24.04 LTS
- 3 vCPU
- 8 GB RAM
- 100 GB dysku
- publiczne porty: SSH 22, HTTP 80, HTTPS 443

## Wykonane elementy bazowe

1. Aktualizacja pakietów systemowych.
2. Strefa czasowa `Europe/Warsaw` i aktywna synchronizacja NTP.
3. Swap 2 GB z `vm.swappiness=10`.
4. Docker Engine i Docker Compose v2.
5. Fail2ban dla SSH: 5 prób w ciągu 10 minut, blokada na godzinę.
6. Konto `deploy` w grupach `sudo` i `docker`.
7. Struktura `/opt/dotacje-ai`.
8. Sekrety poza katalogiem aplikacji.
9. Minimalny Compose: Caddy, frontend, API, PostgreSQL i Redis.

## Struktura katalogów

```text
/opt/dotacje-ai/
|-- app/
|-- data/
|   |-- documents/
|   |-- uploads/
|   |-- exports/
|   `-- caddy/
|-- backups/
|   |-- postgres/
|   `-- files/
|-- secrets/
`-- logs/
```

## Zarządzanie środowiskiem

```bash
cd /opt/dotacje-ai/app/infra
docker compose --env-file /opt/dotacje-ai/secrets/app.env ps
docker compose --env-file /opt/dotacje-ai/secrets/app.env logs --tail=200
docker compose --env-file /opt/dotacje-ai/secrets/app.env up -d --build
```

## Dalsze kroki bezpieczeństwa

Po dodaniu i sprawdzeniu klucza SSH dla `deploy`:

1. wyłączyć logowanie SSH hasłem,
2. wyłączyć bezpośrednie logowanie `root`,
3. zmienić ujawnione wcześniej hasło roota,
4. ograniczyć SSH do zaufanego adresu lub VPN,
5. skonfigurować zewnętrzny, szyfrowany backup i test odtworzenia.

## HTTPS

- Domena główna: `https://dotacjeai.eu`.
- Certyfikat: automatycznie zarządzany przez Caddy i Let's Encrypt.
- HTTP przekierowuje do HTTPS.
- `https://www.dotacjeai.eu` ma własny certyfikat i przekierowuje do domeny głównej.
