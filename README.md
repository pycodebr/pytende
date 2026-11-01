# Pytende

Sistema de controle de atendimentos feito com Python e Django.

Uma pessoa recebe pedidos de trabalho de clientes e perde o controle do que já fez e do que ainda falta fazer. O Pytende registra cada pedido como um atendimento e mostra a situação de cada um (pendente, em andamento ou concluído), com a data e a hora da conclusão.

O escopo completo, as regras de negócio, as telas e o plano de sprints estão no [PRD.md](PRD.md).

## Estado atual

Sprints 1 e 2 concluídas: o projeto lê as configurações do `.env`, usa PostgreSQL, tem idioma e fuso de São Paulo e roda em container (Docker Compose), com gunicorn e WhiteNoise prontos para produção. As telas e os atendimentos entram nas próximas sprints.

## Requisitos

- Python 3.13.11
- Django 6.1.2 (instalado pelo `requirements.txt`)
- Docker com Docker Compose v2 (`docker compose version`), usado para o PostgreSQL 16 local

## Como rodar localmente

Todos os comandos abaixo são executados na raiz do projeto.

### 1. Ambiente virtual e dependências

```bash
python3.13 -m venv .venv        # só se a pasta .venv ainda não existir
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Arquivo `.env`

O `.env` guarda os segredos e a configuração local. Ele é ignorado pelo Git e nunca deve ser versionado. Crie-o a partir do modelo:

```bash
cp .env.example .env
chmod 600 .env
```

Depois troque os placeholders do `.env`:

| Variável | Como preencher |
|---|---|
| `SECRET_KEY` | `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"` |
| `POSTGRES_PASSWORD` | `openssl rand -hex 24` |
| `DATABASE_URL` | `postgres://pytende:<senha>@localhost:5432/pytende`, com a mesma senha de `POSTGRES_PASSWORD` |

Dica: se a `SECRET_KEY` gerada tiver caracteres como `$` ou `#`, prefira `python -c "import secrets; print(secrets.token_urlsafe(50))"`, que só usa letras, números, `-` e `_` e é seguro também para o Docker Compose.

As variáveis de produção (`SECURE_*`, `DOMAIN`, `ACME_EMAIL`, `TRAEFIK_DASHBOARD_AUTH`) só são usadas no deploy e podem ficar como estão no desenvolvimento.

### 3. Banco de dados (PostgreSQL)

```bash
docker compose up -d db
docker compose ps              # espere o status (healthy)
```

O banco fica em `127.0.0.1:5432`, com os dados no volume `pytende_pg_data`. A senha só é aplicada na primeira vez que o volume é criado: se mudar `POSTGRES_PASSWORD` depois, apague o volume (`docker compose down -v`, que apaga todos os dados locais) e suba o banco de novo.

Se a porta 5432 já estiver ocupada por outro PostgreSQL na sua máquina, pare o outro serviço antes de subir o banco do Pytende.

### 4. Migrations, usuário e servidor

```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

O servidor sobe em http://127.0.0.1:8000/. Por enquanto só o admin do Django (http://127.0.0.1:8000/admin/) está disponível; as telas do Pytende chegam nas próximas sprints.

Não existe cadastro público: o único usuário do sistema é o criado com `createsuperuser`.

## Rodando com Docker Compose

Além do jeito local acima (`.venv` + banco no Docker), dá para rodar o app inteiro em container. Isso exige o `.env` pronto (passo 2), mas não o `.venv`.

```bash
docker compose up --build           # sobe app e db (use -d para rodar em segundo plano)
docker compose run --rm app python manage.py createsuperuser
docker compose logs -f app          # acompanha o log do app
docker compose stop                 # para os containers (mantém os dados)
```

O app fica em http://localhost:8000/ e o healthcheck em http://localhost:8000/health/ (responde `{"status": "ok"}`, sem login e sem consultar o banco).

Ao iniciar, o container executa o `entrypoint.sh`, que: espera o PostgreSQL ficar disponível (`wait_for_db`), aplica as migrations com um lock no banco (seguro com mais de uma réplica) e roda o `collectstatic`. Só depois sobe o servidor. No Compose o servidor é o `runserver` (código da pasta do projeto montado no container, com recarga automática); a imagem em si usa o gunicorn, e é ela que vai para produção.

O container usa o mesmo `.env`, mas troca o host do banco para `db` (nome do serviço no Compose). Por isso o `DATABASE_URL` do `.env` continua apontando para `localhost`, que é o que o `.venv` local usa.

Os arquivos estáticos coletados ficam em `staticfiles/` (ignorado pelo Git) e são servidos pelo WhiteNoise.

## Testes

Com o PostgreSQL de pé (`docker compose up -d db`):

```bash
python manage.py test
```

Ou dentro do container. Pare o `app` antes: o entrypoint de cada container recoleta os estáticos na mesma pasta, e dois ao mesmo tempo podem se atrapalhar.

```bash
docker compose stop app
docker compose run --rm app python manage.py test
docker compose up -d app     # opcional: sobe o app de novo
```

O Django cria e apaga o banco `test_pytende` automaticamente.

Se aparecer o aviso `No directory at: .../staticfiles/` do WhiteNoise, é só porque os estáticos ainda não foram coletados. Ele some depois do primeiro `docker compose up` ou de `python manage.py collectstatic --noinput`.

## Comandos úteis

```bash
docker compose up -d db        # sobe o PostgreSQL
docker compose stop db         # para o PostgreSQL (mantém os dados)
docker compose down            # remove o container (mantém os dados)
docker compose down -v         # remove o container e APAGA os dados locais
python manage.py check         # confere a configuração do projeto
```

## Configuração

O `core/settings.py` lê tudo de variáveis de ambiente (via `django-environ`). Variáveis já definidas no shell ou no Docker têm prioridade sobre o arquivo `.env`.

- Idioma: `pt-br`. Fuso horário: `America/Sao_Paulo`. As datas são guardadas em UTC e exibidas no fuso de São Paulo.
- Banco: `DATABASE_URL` é obrigatória (PostgreSQL). O projeto não tem fallback para SQLite.
- `SECRET_KEY` também é obrigatória: sem ela o Django não inicia.
