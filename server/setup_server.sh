#!/usr/bin/env bash
set -Eeuo pipefail

export DEBIAN_FRONTEND=noninteractive

apt-get update
apt-get dist-upgrade -y
apt-get install -y ca-certificates curl git jq openssl rsync ufw fail2ban unattended-upgrades docker-compose-v2

timedatectl set-timezone Europe/Warsaw

if ! swapon --show=NAME --noheadings | grep -qx /swapfile; then
    if [ ! -f /swapfile ]; then
        fallocate -l 2G /swapfile
        chmod 600 /swapfile
        mkswap /swapfile
    fi
    swapon /swapfile
fi
if ! grep -q '^/swapfile ' /etc/fstab; then
    printf '/swapfile none swap sw 0 0\n' >> /etc/fstab
fi
printf 'vm.swappiness=10\n' > /etc/sysctl.d/99-dotacje-ai.conf
sysctl --system >/dev/null

if ! id deploy >/dev/null 2>&1; then
    adduser --disabled-password --gecos '' deploy
fi
usermod -aG sudo,docker deploy

install -d -m 0755 -o deploy -g deploy /opt/dotacje-ai
install -d -m 0755 -o deploy -g deploy \
    /opt/dotacje-ai/app \
    /opt/dotacje-ai/data/documents \
    /opt/dotacje-ai/data/uploads \
    /opt/dotacje-ai/data/exports \
    /opt/dotacje-ai/data/caddy \
    /opt/dotacje-ai/backups/postgres \
    /opt/dotacje-ai/backups/files \
    /opt/dotacje-ai/logs
install -d -m 0700 -o deploy -g deploy /opt/dotacje-ai/secrets
install -d -m 0755 -o deploy -g deploy /home/deploy/Codex/ProjektDotacje

rsync -a --delete --exclude server /tmp/ProjektDotacje/ /opt/dotacje-ai/app/
rsync -a --delete /tmp/ProjektDotacje/docs/ /home/deploy/Codex/ProjektDotacje/
cp /tmp/ProjektDotacje/README.md /home/deploy/Codex/ProjektDotacje/README.md
chown -R deploy:deploy /opt/dotacje-ai/app /home/deploy/Codex
find /opt/dotacje-ai/app -type d -exec chmod 0755 {} +
find /opt/dotacje-ai/app -type f -exec chmod 0644 {} +
find /home/deploy/Codex -type d -exec chmod 0755 {} +
find /home/deploy/Codex -type f -name '*.md' -exec chmod 0644 {} +

if [ ! -f /opt/dotacje-ai/secrets/app.env ]; then
    postgres_password="$(openssl rand -hex 32)"
    redis_password="$(openssl rand -hex 32)"
    cat > /opt/dotacje-ai/secrets/app.env <<EOF
APP_ENV=production
POSTGRES_DB=dotacje
POSTGRES_USER=dotacje
POSTGRES_PASSWORD=${postgres_password}
REDIS_PASSWORD=${redis_password}
LLM_PROVIDER=openrouter
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
OPENROUTER_API_KEY=
LLM_MODEL_FAST=openai/gpt-6-luna
LLM_MODEL_STRONG=openai/gpt-6-luna-pro
LLM_MODEL_VALIDATOR=openai/gpt-6-luna
LLM_DAILY_BUDGET_USD=5
LLM_MONTHLY_BUDGET_USD=100
EOF
fi
chown deploy:deploy /opt/dotacje-ai/secrets/app.env
chmod 600 /opt/dotacje-ai/secrets/app.env

cat > /etc/fail2ban/jail.d/dotacje-ai-sshd.local <<'EOF'
[DEFAULT]
bantime = 1h
findtime = 10m
maxretry = 5
banaction = ufw

[sshd]
enabled = true
backend = systemd
port = ssh
EOF

systemctl enable --now docker fail2ban unattended-upgrades

ufw default deny incoming
ufw default allow outgoing
ufw allow 22/tcp comment 'SSH'
ufw allow 80/tcp comment 'HTTP'
ufw allow 443/tcp comment 'HTTPS'
ufw --force enable

cd /opt/dotacje-ai/app/infra
sudo -u deploy docker compose --env-file /opt/dotacje-ai/secrets/app.env config --quiet
sudo -u deploy docker compose --env-file /opt/dotacje-ai/secrets/app.env up -d --build

systemctl restart fail2ban

echo 'SERVER_SETUP_COMPLETE'
