#!/usr/bin/env bash
set -uo pipefail

# ── Pytende — verificação pós-deploy ──
# Hook opcional do setup_deploy.sh (pycodebr/scsi_v1), no lugar do seed_demo.
# Também pode ser rodado à mão: bash scripts/post_deploy.sh
# Não cria usuário: só confere o deploy e mostra o comando do superusuário.

REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_DIR"

FAIL=0
ok()   { echo "[OK] $1"; }
fail() { echo "[ERRO] $1"; FAIL=1; }

# DOMAIN lido do .env com o mesmo parser seguro do deploy.sh (sem source).
DOMAIN=""
if [ -f .env ]; then
    while IFS= read -r line || [ -n "$line" ]; do
        line="${line%$'\r'}"
        case "$line" in DOMAIN=*) DOMAIN="${line#DOMAIN=}" ;; esac
    done < .env
    DOMAIN="${DOMAIN#\"}"; DOMAIN="${DOMAIN%\"}"
    DOMAIN="${DOMAIN#\'}"; DOMAIN="${DOMAIN%\'}"
fi
[ -n "$DOMAIN" ] || fail "DOMAIN não encontrado no .env."

# 1. Espera o container do app (até 120 s).
APP=""
for _ in $(seq 1 60); do
    APP="$(docker ps --filter name=pytende_app -q | head -n1)"
    [ -n "$APP" ] && break
    sleep 2
done
if [ -z "$APP" ]; then
    fail "Container pytende_app não apareceu em 120 s."
    exit 1
fi
ok "Container do app: $APP"

# 2. check --deploy e migrations aplicadas.
if docker exec "$APP" python manage.py check --deploy; then
    ok "check --deploy executado"
else
    fail "check --deploy falhou"
fi
PLAN="$(docker exec "$APP" python manage.py showmigrations --plan 2>&1)" || fail "showmigrations falhou"
if printf '%s\n' "$PLAN" | grep -qF '[ ]'; then
    fail "Há migrations pendentes:"
    printf '%s\n' "$PLAN" | grep -F '[ ]'
else
    ok "Nenhuma migration pendente"
fi

# 3. Healthcheck pelo domínio público.
if [ -n "$DOMAIN" ]; then
    HEALTH="$(curl -fsS "https://${DOMAIN}/health/" 2>&1)" || true
    case "$HEALTH" in
        *'"status": "ok"'*) ok "https://${DOMAIN}/health/ respondeu $HEALTH" ;;
        *) fail "https://${DOMAIN}/health/ não respondeu ok: ${HEALTH:-<vazio>}" ;;
    esac
fi

# 4. Próximo passo manual.
echo ""
echo "Crie o superusuário (uma vez):"
echo "  APP=\$(docker ps --filter name=pytende_app -q | head -1)"
echo "  docker exec -it \"\$APP\" python manage.py createsuperuser"

exit "$FAIL"
