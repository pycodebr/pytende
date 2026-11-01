#!/usr/bin/env bash
set -euo pipefail

# ── Pytende — gerador guiado do .env de produção ──
# Hook opcional do setup_deploy.sh (pycodebr/scsi_v1). Também roda à mão:
#   bash scripts/generate_env.sh
#   printf 'pytende.example.com\nadmin@example.com\n' | ENV_FILE=/caminho/.env bash scripts/generate_env.sh
# Pergunta só DOMAIN e ACME_EMAIL. Gera SECRET_KEY e POSTGRES_PASSWORD.
# Se o arquivo já existir, faz backup e PRESERVA toda chave que já tem valor
# (SECRET_KEY e POSTGRES_PASSWORD não podem mudar depois que o banco existe).
# Nunca imprime segredos.

ENV_FILE="${ENV_FILE:-.env}"

# Respostas: do terminal quando houver um; senão, do stdin (ensaio, automação).
if (exec </dev/tty) 2>/dev/null; then
    INPUT=/dev/tty
else
    INPUT=/dev/stdin
fi

# Cópia do .env atual (se existir), lida chave a chave por current().
# Sem arrays associativos: o script também roda no bash 3.2 do macOS (ensaio).
BACKUP=""
if [ -f "$ENV_FILE" ]; then
    BACKUP="${ENV_FILE}.bak.$(date +%Y%m%d%H%M%S)"
    cp "$ENV_FILE" "$BACKUP"
    chmod 600 "$BACKUP"
    echo "Backup do .env atual: $BACKUP"
fi

current() {
    local wanted="$1" line key value=""
    [ -n "$BACKUP" ] || return 0
    while IFS= read -r line || [ -n "$line" ]; do
        line="${line%$'\r'}"
        case "$line" in ''|\#*) continue ;; esac
        [ "${line#*=}" = "$line" ] && continue
        key="${line%%=*}"
        [ "$key" = "$wanted" ] && value="${line#*=}"
    done < "$BACKUP"
    printf '%s' "$value"
}

ask() {
    local prompt="$1" default="$2" answer=""
    printf '%s [%s]: ' "$prompt" "$default" >&2
    IFS= read -r answer < "$INPUT" || true
    printf '%s' "${answer:-$default}"
}

DOMAIN_DEFAULT="$(current DOMAIN)"; DOMAIN_DEFAULT="${DOMAIN_DEFAULT:-pytende.pycodebr.com.br}"
DOMAIN="$(ask 'Domínio do Pytende (DOMAIN)' "$DOMAIN_DEFAULT")"
EMAIL_DEFAULT="$(current ACME_EMAIL)"; EMAIL_DEFAULT="${EMAIL_DEFAULT:-admin@${DOMAIN#*.}}"
ACME_EMAIL="$(ask 'E-mail da conta Let'"'"'s Encrypt (ACME_EMAIL)' "$EMAIL_DEFAULT")"
[ -n "$DOMAIN" ] || { echo "DOMAIN não pode ficar vazio." >&2; exit 1; }
[ -n "$ACME_EMAIL" ] || { echo "ACME_EMAIL não pode ficar vazio." >&2; exit 1; }

SECRET_KEY="$(current SECRET_KEY)"
if [ -z "$SECRET_KEY" ]; then
    SECRET_KEY="$(python3 -c "import secrets; print(secrets.token_urlsafe(50))")"
fi
POSTGRES_PASSWORD="$(current POSTGRES_PASSWORD)"
if [ -z "$POSTGRES_PASSWORD" ]; then
    if command -v openssl >/dev/null 2>&1; then
        POSTGRES_PASSWORD="$(openssl rand -hex 24)"
    else
        POSTGRES_PASSWORD="$(python3 -c "import secrets; print(secrets.token_hex(24))")"
    fi
fi

value_or() { local v; v="$(current "$1")"; printf '%s' "${v:-$2}"; }

POSTGRES_DB="$(value_or POSTGRES_DB pytende)"
POSTGRES_USER="$(value_or POSTGRES_USER pytende)"

umask 077
TMP="$(mktemp "${ENV_FILE}.tmp.XXXXXX")"
{
    echo "# Pytende - .env de produção gerado por scripts/generate_env.sh em $(date '+%Y-%m-%d %H:%M:%S')"
    echo "# Nunca versione este arquivo."
    echo ""
    echo "# --- Django ---"
    echo "SECRET_KEY=${SECRET_KEY}"
    echo "DEBUG=False"
    echo "ALLOWED_HOSTS=$(value_or ALLOWED_HOSTS "${DOMAIN},localhost")"
    echo "CSRF_TRUSTED_ORIGINS=$(value_or CSRF_TRUSTED_ORIGINS "https://${DOMAIN}")"
    echo ""
    echo "# --- Banco de dados (PostgreSQL) ---"
    echo "POSTGRES_DB=${POSTGRES_DB}"
    echo "POSTGRES_USER=${POSTGRES_USER}"
    echo "POSTGRES_PASSWORD=${POSTGRES_PASSWORD}"
    echo "DATABASE_URL=$(value_or DATABASE_URL "postgres://${POSTGRES_USER}:${POSTGRES_PASSWORD}@db:5432/${POSTGRES_DB}")"
    echo ""
    echo "# --- Produção ---"
    echo "SECURE_SSL_REDIRECT=$(value_or SECURE_SSL_REDIRECT True)"
    echo "SECURE_HSTS_SECONDS=$(value_or SECURE_HSTS_SECONDS 3600)"
    echo ""
    echo "# --- Deploy (docker-stack.yml) ---"
    echo "DOMAIN=${DOMAIN}"
    echo "ACME_EMAIL=${ACME_EMAIL}"
    echo "# Preenchida pelo setup_deploy.sh (saída crua de htpasswd -nbB, com um único \$)"
    echo "TRAEFIK_DASHBOARD_AUTH=$(current TRAEFIK_DASHBOARD_AUTH)"
} > "$TMP"
mv "$TMP" "$ENV_FILE"
chmod 600 "$ENV_FILE"

echo "Arquivo gravado: $ENV_FILE (permissão 600). Chaves:"
grep -E '^[A-Z_]+=' "$ENV_FILE" | cut -d= -f1 | sed 's/^/  - /'
