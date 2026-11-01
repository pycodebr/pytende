# Deploy do Pytende no Docker Swarm (VPS)

Guia de operação da Rota B: PostgreSQL 16, Docker Swarm de um nó e Traefik v3.6 com Let's Encrypt (DNS-01 na Cloudflare). O ambiente é preparado pelo `setup_deploy.sh` público do `pycodebr/scsi_v1`, que usa os hooks `scripts/generate_env.sh` e `scripts/post_deploy.sh` deste repositório. A fonte de verdade das decisões continua sendo a seção 14 do [PRD](../../PRD.md).

Arquivos usados:

| Arquivo | Papel |
|---|---|
| `docker-stack.yml` | Stack com `traefik`, `app` e `db`; redes `traefik_public` e `pytende_internal` externas; secret `CLOUDFLARE_DNS_API_TOKEN` |
| `scripts/deploy.sh` | Redeploy: lê o `.env` sem `source`, valida, faz pull/build/push, roda `check --deploy` dentro da imagem, `docker stack deploy` e força o rollout do `app`. Com `--skip-build`, só reconcilia a stack |
| `scripts/generate_env.sh` | Gera o `.env` de produção (pergunta `DOMAIN` e `ACME_EMAIL`, gera `SECRET_KEY` e senha do banco, preserva valores existentes, `chmod 600`) |
| `scripts/post_deploy.sh` | Confere o deploy: `check --deploy`, migrations aplicadas e `https://<DOMAIN>/health/` |
| `scripts/backup.sh` | `pg_dump` compactado em `~/backups/`, com rotação de 30 dias |

## Pré-requisitos (o que ter em mãos)

| Item | Detalhe |
|---|---|
| VPS | Ubuntu 24.04 LTS, nova, dedicada, com acesso root por SSH e as portas 80 e 443 livres (D-02). Nunca rodar o setup numa VPS que já sirva Nginx ou outra stack. |
| Domínio | `pytende.pycodebr.com.br` (D-03), na zona `pycodebr.com.br`, que já usa a Cloudflare |
| Registros DNS na Cloudflare | `A pytende -> <IP_DA_VPS>` e `A *.pytende -> <IP_DA_VPS>`, os dois **sem proxy** ("DNS only") (L-09) |
| Token da Cloudflare | Token de API restrito à zona `pycodebr.com.br` com as permissões `Zone:Zone:Read` e `Zone:DNS:Edit` (usado pelo Traefik no DNS-01) |
| Token do GHCR | Token clássico do GitHub com o escopo `write:packages` (e `read:packages`) para a organização `pycodebr` (D-07) |
| Acesso ao repositório | O `setup_deploy.sh` gera uma chave SSH na VPS; adicionar a chave pública como deploy key **só de leitura** em `pycodebr/pytende` (D-08) |
| Basic Auth do dashboard | Usuário e senha escolhidos na hora; o script gera o hash |

## Passo a passo

Comandos para o primeiro deploy na VPS.

1. **Local:** confirmar `python manage.py test` passando, ensaio da Sprint 11 aprovado e push do `main` para `origin`.
2. **DNS:** na Cloudflare, criar os dois registros A da seção "Pré-requisitos".
3. **Setup da VPS:** acessar a VPS como root e rodar o script público:
   ```bash
   curl -fsSL https://raw.githubusercontent.com/pycodebr/scsi_v1/main/scripts/setup_deploy.sh -o setup_deploy.sh && sudo bash setup_deploy.sh
   ```
4. **Respostas das perguntas do script:**

   | Pergunta | Resposta |
   |---|---|
   | Nome do usuário de deploy | `deploy` |
   | Fuso horário | `America/Sao_Paulo` |
   | Tamanho do swap em GB | `2` |
   | Nome do projeto (igual ao repositório) | `pytende` |
   | IP público para o Swarm | o IP público da VPS (sugerido pelo script) |
   | Chave SSH do GitHub | adicionar a chave mostrada como deploy key só de leitura em `pycodebr/pytende` e confirmar |
   | URL do repositório em SSH | `git@github.com:pycodebr/pytende.git` |
   | Usuário/organização do GitHub | `pycodebr` |
   | Token do GHCR | o token `write:packages` (digitado sem aparecer na tela) |
   | Usar o gerador de `.env`? | `S` (roda `scripts/generate_env.sh`); responder `DOMAIN` e `ACME_EMAIL` |
   | Basic Auth do Traefik | usuário e senha do dashboard |
   | Token da Cloudflare | o token da seção "Pré-requisitos" |
   | O DNS já aponta para a VPS? | `S`, depois de conferir com `dig +short pytende.pycodebr.com.br` |

   O script prepara o servidor (atualizações, fail2ban, swap, UFW com 22/80/443, Docker, Swarm, usuário `deploy`), clona o projeto em `/home/deploy/pytende`, faz build, push e pull da imagem, cria as redes e o secret, faz o `docker stack deploy` e roda `scripts/post_deploy.sh`.
5. **Verificação:**
   ```bash
   docker stack services pytende                 # três serviços em 1/1
   docker service logs -f pytende_traefik        # emissão do certificado
   docker service logs -f pytende_app            # migrations e gunicorn
   curl -I http://pytende.pycodebr.com.br/       # 301 ou 308 para https
   curl -fsS https://pytende.pycodebr.com.br/health/
   ```
6. **Superusuário:**
   ```bash
   APP=$(docker ps --filter name=pytende_app -q | head -1)
   docker exec -it "$APP" python manage.py createsuperuser
   ```
7. **Testes no servidor:** `docker exec "$APP" python manage.py test` (o banco `test_pytende` é criado e apagado no próprio PostgreSQL da stack).
8. **Checklist pós-deploy:** seção "Checklist pós-deploy".

**Redeploy** (depois de cada push no `main`), na VPS como `deploy`:

```bash
cd ~/pytende
bash scripts/backup.sh                 # backup antes de atualizar
bash scripts/deploy.sh                 # pull, build, push, validação, deploy, rollout
```

Se um rollout falhar e o Swarm voltar para a versão anterior, corrija a causa, rode `bash scripts/deploy.sh --skip-build` para reler o `.env` e confira as variáveis com `docker service inspect --format '{{range .Spec.TaskTemplate.ContainerSpec.Env}}{{println .}}{{end}}' pytende_app`.

## Variáveis de ambiente

Conteúdo exato do `.env.example` (criado na Sprint 1):

```dotenv
# =============================================================================
# Pytende - variáveis de ambiente
# Copie para `.env` e preencha. Nunca versione o `.env`.
# Em produção, gere o .env com scripts/generate_env.sh.
# =============================================================================

# --- Django ---
# Gere com: python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
SECRET_KEY=troque-por-uma-chave-gerada
DEBUG=True
# Listas separadas por vírgula
ALLOWED_HOSTS=localhost,127.0.0.1
CSRF_TRUSTED_ORIGINS=http://localhost:8000,http://127.0.0.1:8000

# --- Banco de dados (PostgreSQL) ---
# Gere a senha com: openssl rand -hex 24
POSTGRES_DB=pytende
POSTGRES_USER=pytende
POSTGRES_PASSWORD=troque-esta-senha
# Local (.venv): host localhost. Produção (Swarm): host db.
DATABASE_URL=postgres://pytende:troque-esta-senha@localhost:5432/pytende

# --- Produção (usadas só quando DEBUG=False) ---
SECURE_SSL_REDIRECT=True
SECURE_HSTS_SECONDS=3600

# --- Deploy (usadas só pelo docker-stack.yml) ---
DOMAIN=pytende.example.com
ACME_EMAIL=admin@example.com
# Preenchida pelo setup_deploy.sh (saída crua de htpasswd -nbB, com um único $)
TRAEFIK_DASHBOARD_AUTH=
```

| Variável | Finalidade | Exemplo de desenvolvimento | Exemplo de produção (placeholder) |
|---|---|---|---|
| `SECRET_KEY` | Assinatura de sessões, cookies e tokens CSRF | `troque-por-uma-chave-gerada` | `<gerada-pelo-generate_env.sh>` |
| `DEBUG` | Liga páginas de erro detalhadas | `True` | `False` |
| `ALLOWED_HOSTS` | Hosts aceitos pelo Django | `localhost,127.0.0.1` | `pytende.pycodebr.com.br,localhost` |
| `CSRF_TRUSTED_ORIGINS` | Origens aceitas em POST | `http://localhost:8000,http://127.0.0.1:8000` | `https://pytende.pycodebr.com.br` |
| `POSTGRES_DB` | Nome do banco criado pelo container `postgres` | `pytende` | `pytende` |
| `POSTGRES_USER` | Usuário do banco | `pytende` | `pytende` |
| `POSTGRES_PASSWORD` | Senha do banco | `troque-esta-senha` | `<openssl-rand-hex-24>` |
| `DATABASE_URL` | Conexão do Django | `postgres://pytende:<senha>@localhost:5432/pytende` | `postgres://pytende:<senha>@db:5432/pytende` |
| `SECURE_SSL_REDIRECT` | Redireciona HTTP para HTTPS no Django | `True` (ignorado com `DEBUG=True`) | `True` |
| `SECURE_HSTS_SECONDS` | Tempo de HSTS | `3600` (ignorado com `DEBUG=True`) | `3600` na primeira semana; depois `31536000` |
| `DOMAIN` | Domínio do Traefik (roteador, certificado, dashboard) | `pytende.example.com` | `pytende.pycodebr.com.br` |
| `ACME_EMAIL` | E-mail da conta Let's Encrypt | `admin@example.com` | `<email-do-responsavel>` |
| `TRAEFIK_DASHBOARD_AUTH` | Basic Auth do dashboard (`usuario:$2y$...`) | vazio | `<preenchido-pelo-setup_deploy.sh>` |

Ficam fora do `.env`: o token da Cloudflare (Docker Secret `CLOUDFLARE_DNS_API_TOKEN`) e o token do GHCR (usado só no `docker login` e, como fallback, em `GITHUB_TOKEN` na hora do deploy). `LANGUAGE_CODE` e `TIME_ZONE` são fixos no código por requisito.

## Problemas comuns

| Sintoma | Causa provável | Correção |
|---|---|---|
| `pytende_app` em 0/1 e `400 DisallowedHost` no log | `localhost` ou o domínio faltando em `ALLOWED_HOSTS` | Corrigir o `.env` e rodar `bash scripts/deploy.sh --skip-build` |
| Loop de redirecionamento HTTPS | `SECURE_PROXY_SSL_HEADER` ausente | Conferir o bloco de produção do `core/settings.py` (bloco `if not DEBUG:`) |
| 403 CSRF em todos os POSTs | `CSRF_TRUSTED_ORIGINS` sem `https://<DOMAIN>` | Corrigir o `.env` e reimplantar |
| Certificado não é emitido | Token da Cloudflare sem permissão na zona ou DNS sem propagar | `docker service logs pytende_traefik`; conferir permissões e `dig` |
| Healthcheck derruba o app no primeiro deploy | Migrations demorando mais que o `start_period` | Aumentar `start_period` para 600s |
| Redes `pytende_pytende_internal` duplicadas | Rede declarada sem `external: true` | Usar o `docker-stack.yml` do repositório |
| `app` não acha o banco | `DATABASE_URL` com host `localhost` em produção | Usar host `db` |

## Backup

| Item | Definição |
|---|---|
| O que | Banco `pytende` (único dado de negócio; não há uploads). O `.env` da VPS é copiado à parte, uma vez, para um cofre de senhas. |
| Como | `pg_dump --clean --if-exists --no-owner` executado dentro do container `pytende_db`, compactado com `gzip` |
| Frequência | Diária às 03:00 (fuso da VPS: `America/Sao_Paulo`) pelo cron do usuário `deploy`; e manual antes de cada redeploy |
| Onde fica | `/home/deploy/backups/db_AAAAMMDD_HHMMSS.sql.gz`, com retenção de 30 dias |
| Cópia fora da VPS | Semanal, manual: `scp deploy@<IP_DA_VPS>:~/backups/db_*.sql.gz ~/Backups/pytende/` no Mac do Felipe (D-11) |
| Teste de restauração | Uma vez logo após o primeiro deploy (CA-50) e depois a cada três meses |

O script `scripts/backup.sh`:

```bash
#!/usr/bin/env bash
set -euo pipefail

BACKUP_DIR="${BACKUP_DIR:-$HOME/backups}"
RETENTION_DAYS="${RETENTION_DAYS:-30}"
DATE="$(date +%Y%m%d_%H%M%S)"

mkdir -p "$BACKUP_DIR"

DB_CONTAINER="$(docker ps -q -f name=pytende_db | head -n1)"
[ -n "$DB_CONTAINER" ] || { echo "ERRO: container pytende_db não encontrado."; exit 1; }

echo "[$(date)] Backup do PostgreSQL..."
docker exec "$DB_CONTAINER" sh -c 'pg_dump --clean --if-exists --no-owner -U "$POSTGRES_USER" "$POSTGRES_DB"' \
    | gzip > "${BACKUP_DIR}/db_${DATE}.sql.gz"

echo "[$(date)] Rotação: removendo backups com mais de ${RETENTION_DAYS} dias..."
find "$BACKUP_DIR" -name 'db_*.sql.gz' -mtime +"$RETENTION_DAYS" -delete

echo "[$(date)] Backup concluído: db_${DATE}.sql.gz"
```

Cron (`crontab -e` como `deploy`):

```
0 3 * * * /home/deploy/pytende/scripts/backup.sh >> /home/deploy/backups/backup.log 2>&1
```

**Restauração:**

1. Parar o app para evitar escrita: `docker service scale pytende_app=0`.
2. Restaurar:
   ```bash
   DB=$(docker ps -q -f name=pytende_db | head -n1)
   gunzip -c ~/backups/db_AAAAMMDD_HHMMSS.sql.gz \
     | docker exec -i "$DB" sh -c 'psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB"'
   ```
3. Subir o app: `docker service scale pytende_app=1`.
4. Entrar no sistema e conferir se os atendimentos esperados aparecem.

## Checklist pós-deploy

- [ ] `docker stack services pytende` mostra `pytende_traefik`, `pytende_app` e `pytende_db` em 1/1.
- [ ] `https://pytende.pycodebr.com.br/` redireciona para `/login/?next=/` com certificado válido do Let's Encrypt.
- [ ] `http://pytende.pycodebr.com.br/` redireciona para HTTPS.
- [ ] `https://pytende.pycodebr.com.br/health/` responde `{"status": "ok"}`.
- [ ] `https://traefik.pytende.pycodebr.com.br/` pede Basic Auth.
- [ ] Login com usuário errado mostra "Usuário ou senha inválidos.".
- [ ] Login correto leva à Lista.
- [ ] Os estilos carregam (fonte Inter, botão verde `#9fe870`, fundo `#e8ebe6`).
- [ ] Cadastrar um atendimento de teste, trocar o status pela lista para "Em andamento" e depois "Concluído", conferir a data em `/?status=completed` no horário de São Paulo.
- [ ] Reabrir o atendimento de teste e conferir que a data some.
- [ ] Sair pela barra de navegação.
- [ ] Uma URL inexistente devolve 404 genérica, sem traceback (prova de `DEBUG=False`).
- [ ] `/admin/` abre e a busca e o filtro de status funcionam.
- [ ] Nas ferramentas do navegador, os cookies `sessionid` e `csrftoken` têm o atributo `Secure`, e a resposta tem o header `Strict-Transport-Security`.
- [ ] `docker exec "$APP" python manage.py check --deploy` só com o aviso `security.W021`.
- [ ] `docker exec "$APP" python manage.py test` passando.
- [ ] O cron de backup gerou o primeiro arquivo em `~/backups/`.
- [ ] Teste de restauração (CA-50) feito, atendimento de teste excluído pelo admin depois, e data registrada no README.
- [ ] Portas abertas na VPS só 22, 80 e 443 (`sudo ufw status`), e a 5432 não responde de fora.

## Ensaio local da stack (sem VPS)

Valida a stack, o `.env` gerado e o `scripts/deploy.sh` sem VPS. Não cobre a emissão real do certificado nem o push no GHCR.

```bash
# 1. imagem de produção e .env de ensaio (gerador alimentado pelo stdin)
docker build -t ghcr.io/pycodebr/pytende:latest .
mkdir -p /tmp/pytende-envtest
printf 'pytende.example.com\nadmin@example.com\n' | ENV_FILE=/tmp/pytende-envtest/.env bash scripts/generate_env.sh
sed -i.bak 's|^TRAEFIK_DASHBOARD_AUTH=.*|TRAEFIK_DASHBOARD_AUTH=admin:$2y$05$hashdeensaio|' /tmp/pytende-envtest/.env

# 2. Swarm de um nó em Docker-in-Docker
docker run -d --privileged --name pytende_swarm_test \
  -v "$PWD":/repo:ro -v /tmp/pytende-envtest:/envtest:ro docker:27-dind
docker save ghcr.io/pycodebr/pytende:latest | docker exec -i pytende_swarm_test docker load
docker exec pytende_swarm_test sh -c '
  apk add -q bash git curl &&
  docker swarm init &&
  docker network create --driver overlay --attachable traefik_public &&
  docker network create --driver overlay --attachable --internal pytende_internal &&
  printf dummy | docker secret create CLOUDFLARE_DNS_API_TOKEN - &&
  mkdir /work && cd /repo && tar --exclude=.venv --exclude=.git -cf - . | tar -xf - -C /work &&
  cp /envtest/.env /work/.env &&
  cd /work && bash scripts/deploy.sh --skip-build'
```

Verificações dentro do container `pytende_swarm_test` (CA-49):

```bash
docker exec pytende_swarm_test docker service ls
docker exec pytende_swarm_test curl -sk --resolve pytende.example.com:443:127.0.0.1 -o /dev/null -w '%{http_code}\n' https://pytende.example.com/login/
docker exec pytende_swarm_test curl -sk --resolve pytende.example.com:443:127.0.0.1 -o /dev/null -w '%{http_code}\n' https://pytende.example.com/static/css/tokens.css
docker exec pytende_swarm_test curl -s -o /dev/null -w '%{http_code}\n' -H 'Host: pytende.example.com' http://127.0.0.1/
```

Esperado: três serviços em 1/1, `200`, `200` e `301` ou `308`. Com o token falso da Cloudflare, o Traefik serve um certificado próprio (por isso o `-k`). Para investigar um serviço que não sobe: `docker exec pytende_swarm_test docker service ps --no-trunc pytende_app`.

Limpeza: `docker exec pytende_swarm_test docker stack rm pytende; docker rm -f pytende_swarm_test; rm -rf /tmp/pytende-envtest`.
