#!/usr/bin/env bash
set -euo pipefail

# ── Pytende — Deploy completo (Docker Swarm, executado NA VPS como "deploy") ──
# Adaptado do scripts/deploy.sh do pycodebr/scsi_v1.
# Uso:
#   bash scripts/deploy.sh                pull + build + push + validação + deploy + rollout
#   bash scripts/deploy.sh --skip-build   só reconcilia a stack e força o rollout do app
#
# Pré-requisitos na VPS (nó manager do Swarm), no diretório do projeto:
#   - .env de produção (gere com scripts/generate_env.sh), com DEBUG=False
#   - secret:  printf '<TOKEN>' | docker secret create CLOUDFLARE_DNS_API_TOKEN -
#   - redes:   docker network create --driver overlay --attachable traefik_public
#              docker network create --driver overlay --attachable --internal pytende_internal
#   - login no GHCR (ou GITHUB_TOKEN com o escopo write:packages exportado)

REGISTRY="ghcr.io/pycodebr"
IMAGE="$REGISTRY/pytende"
STACK_NAME="pytende"
STACK_FILE="docker-stack.yml"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

info()  { echo -e "${GREEN}[OK]${NC} $1"; }
warn()  { echo -e "${YELLOW}[!!]${NC} $1"; }
error() { echo -e "${RED}[ERRO]${NC} $1"; exit 1; }

SKIP_BUILD=0
[ "${1:-}" = "--skip-build" ] && SKIP_BUILD=1

echo "=== Pytende — Deploy ($STACK_NAME) ==="
echo ""

# ── 0. Pré-condições ──
command -v docker >/dev/null 2>&1 || error "Docker não encontrado."
docker info --format '{{.Swarm.LocalNodeState}}' 2>/dev/null | grep -q active \
    || error "Este nó não está em Swarm ativo (rode: docker swarm init)."

REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_DIR"

# ── 1. Carrega o .env (parser seguro: NÃO faz source; valores com & $ * espaços
#       quebrariam o shell. Só exporta KEY=VALUE literalmente.) ──
[ -f .env ] || error "Arquivo .env não encontrado em $REPO_DIR"
echo "--- Carregando .env ---"
while IFS= read -r line || [ -n "$line" ]; do
    line="${line%$'\r'}"
    case "$line" in ''|\#*) continue ;; esac
    [ "${line#*=}" = "$line" ] && continue
    key="${line%%=*}"; value="${line#*=}"
    key="${key#"${key%%[![:space:]]*}"}"; key="${key%"${key##*[![:space:]]}"}"
    case "$key" in ''|*[!A-Za-z0-9_]*) continue ;; esac
    case "$value" in
        \"*\") value="${value#\"}"; value="${value%\"}" ;;
        \'*\') value="${value#\'}"; value="${value%\'}" ;;
    esac
    export "$key=$value"
done < .env
info ".env carregado"

URL="https://${DOMAIN:-}"

# ── 2. Validações que evitam deploy quebrado ──
echo ""
echo "--- Validações ---"
docker secret inspect CLOUDFLARE_DNS_API_TOKEN >/dev/null 2>&1 \
    || error "Secret 'CLOUDFLARE_DNS_API_TOKEN' ausente. Crie: printf '<TOKEN>' | docker secret create CLOUDFLARE_DNS_API_TOKEN -"
for net in traefik_public pytende_internal; do
    docker network ls --format '{{.Name}}' | grep -qx "$net" \
        || error "Rede '$net' ausente. Veja os comandos no topo deste script."
done
for var in SECRET_KEY DATABASE_URL POSTGRES_DB POSTGRES_USER POSTGRES_PASSWORD DOMAIN ACME_EMAIL TRAEFIK_DASHBOARD_AUTH; do
    [ -n "${!var:-}" ] || error "Variável obrigatória vazia no .env: $var"
done
[ "${DEBUG:-}" = "False" ] || error "DEBUG precisa ser 'False' em produção (valor atual: '${DEBUG:-<vazio>}')."
case ",${ALLOWED_HOSTS:-}," in
    *,"${DOMAIN}",*) : ;;
    *) error "ALLOWED_HOSTS não contém '${DOMAIN}'." ;;
esac
case ",${ALLOWED_HOSTS:-}," in
    *,localhost,*) : ;;
    *) error "ALLOWED_HOSTS não contém 'localhost' (o healthcheck do app falharia com DisallowedHost)." ;;
esac
info "Validações concluídas"

# ── 3. Build, push e validação dentro da imagem ──
VERSION="$(git rev-parse --short HEAD 2>/dev/null || echo latest)"
if [ "$SKIP_BUILD" -eq 0 ]; then
    echo ""
    echo "--- Atualizando código (git pull) ---"
    BRANCH="$(git branch --show-current 2>/dev/null || echo '')"
    if [ -n "$BRANCH" ]; then
        git pull origin "$BRANCH" || warn "git pull falhou (seguindo com o código atual)."
        VERSION="$(git rev-parse --short HEAD)"
    else
        warn "Sem branch git detectada; pulando git pull."
    fi

    echo ""
    echo "--- Build da imagem ($IMAGE:$VERSION) ---"
    docker build -t "$IMAGE:$VERSION" -t "$IMAGE:latest" .
    info "Imagem construída"

    echo ""
    echo "--- Push para o GHCR ---"
    if ! docker push "$IMAGE:$VERSION"; then
        warn "Push falhou; tentando login no GHCR..."
        [ -n "${GITHUB_TOKEN:-}" ] || error "Defina GITHUB_TOKEN (escopo write:packages) ou faça 'docker login ghcr.io'."
        echo "$GITHUB_TOKEN" | docker login ghcr.io -u pycodebr --password-stdin
        docker push "$IMAGE:$VERSION"
    fi
    docker push "$IMAGE:latest"
    info "Imagem enviada: $IMAGE:$VERSION"

    echo ""
    echo "--- Validação da imagem (check --deploy) ---"
    docker run --rm --env-file .env --entrypoint python "$IMAGE:$VERSION" \
        manage.py check --deploy --fail-level ERROR \
        || error "check --deploy falhou dentro da imagem. A stack não foi alterada."
    info "check --deploy sem erros"
else
    warn "--skip-build: pulando git pull, build, push e validação da imagem."
fi

# ── 4. Deploy da stack ──
echo ""
echo "--- Deploy da stack ---"
docker stack deploy -c "$STACK_FILE" --with-registry-auth "$STACK_NAME"
info "Stack reconciliada"

# ── 5. Rollout forçado do app (garante a imagem nova e o .env relido) ──
echo ""
echo "--- Rollout do app ---"
docker service update --force "${STACK_NAME}_app" >/dev/null 2>&1 \
    && info "rollout: ${STACK_NAME}_app" \
    || warn "rollout falhou (o serviço ainda não existe?): ${STACK_NAME}_app"

echo ""
echo "--- Aguardando estabilizar ---"
sleep 10

echo ""
echo "--- Status ---"
docker service ls --format "table {{.Name}}\t{{.Mode}}\t{{.Replicas}}\t{{.Image}}" | grep -E "^NAME|^${STACK_NAME}_" || true

echo ""
echo "=== Deploy concluído! ==="
echo "  Versão: $VERSION"
echo "  Imagem: $IMAGE:$VERSION"
echo "  URL:    $URL"
echo ""
echo "  Migrations e collectstatic rodam no entrypoint do app (advisory lock)."
echo "  Superusuário (1x):  APP=\$(docker ps --filter name=${STACK_NAME}_app -q | head -1); docker exec -it \$APP python manage.py createsuperuser"
echo "  Logs:               docker service logs -f ${STACK_NAME}_app"
echo "  TLS/Traefik:        docker service logs -f ${STACK_NAME}_traefik"
