# PRD - Pytende: Controle de Atendimentos

| Item | Valor |
|---|---|
| Documento | Product Requirement Document (fonte única de verdade do projeto) |
| Versão | 1.1 (deploy alterado para a Rota B: VPS com Docker Swarm) |
| Data | 2026-11-01 |
| Método | Spec-Driven Development: cada sprint é executada lendo só este documento |
| Repositório | `https://github.com/pycodebr/pytende` (branch `main`) |
| Status | Planejamento. Nada foi implementado. Todos os checkboxes começam desmarcados. |

Histórico: a versão 1.0 usava a Rota A (SQLite + PythonAnywhere). Na versão 1.1, Felipe escolheu a Rota B (PostgreSQL, Docker Compose no desenvolvimento e Docker Swarm com Traefik em VPS). Requisitos funcionais, regras de negócio e telas não mudaram.

---

## 1. Visão geral

### 1.1 Problema

Uma pessoa recebe pedidos de trabalho de clientes por vários canais e perde o controle do que já fez e do que ainda falta fazer. Não existe um lugar único que diga, para cada pedido, se ele está parado, em andamento ou concluído, nem quando foi concluído.

### 1.2 Objetivo

O Pytende registra cada pedido como um **atendimento** e mostra a situação de cada um. O responsável cadastra o atendimento, muda o status conforme trabalha e consulta, por filtro, o que está pendente, em andamento ou concluído, com a data e a hora da conclusão.

### 1.3 Público

| Perfil | Descrição | Como acessa |
|---|---|---|
| Responsável (único usuário) | Profissional que atende pedidos de clientes (pessoas ou empresas) e precisa saber o que já fez e o que falta. Usa celular, tablet e desktop. | Conta criada por `python manage.py createsuperuser`. Entra com usuário e senha. Também usa o admin do Django para consultas e correções. |

Não existe cadastro público, nem outros perfis.

### 1.4 Escopo resumido

- Login e logout com os recursos nativos do Django.
- Exatamente quatro telas: Login, Lista de atendimentos (tela inicial), Novo atendimento, Edição do atendimento.
- Um model de negócio: `Ticket` (atendimento), com cliente em texto livre, assunto, descrição, status e data de conclusão.
- Troca de status na edição e direto na lista (POST com CSRF).
- Data de conclusão gravada ao concluir e apagada ao reabrir, com a regra numa camada só (model).
- Filtro por status na query string.
- Admin do Django com busca e filtro.
- Deploy na Rota B: PostgreSQL 16, Docker Compose no desenvolvimento e Docker Swarm com Traefik numa VPS em produção, no padrão do SCSI.

---

## 2. Limitações da análise

Todas as fontes obrigatórias foram acessadas em 2026-11-01. As limitações abaixo são de conteúdo das fontes ou de coisas que esta tarefa (só documentação) não executa.

| # | Limitação | Suposição ou tratamento adotado |
|---|---|---|
| L-01 | O SCSI (`pycodebr/scsi`, branch `main`, commit `aaddb90e88987ea2d2bca114e4cdd7c0a0f36ae3`, de 2026-06-25) **não tem `README.md` na raiz**. A documentação de execução está em `docs/` (MkDocs). | O padrão de README do Pytende foi adaptado de `docs/local-dev.md`. O guia de deploy fica em `docs/deploy/swarm.md`, um arquivo Markdown simples, sem MkDocs. |
| L-02 | Os 15 arquivos `*/tests.py` do SCSI são stubs vazios (3 linhas cada). O SCSI não tem padrão de testes para adaptar. | A estratégia de testes (seção 12) segue a documentação do Django (`django.test.TestCase`, `Client`, `unittest.mock`), não o SCSI. |
| L-03 | O SCSI usa `Django==6.0.5`. O Pytende usa `Django==6.1.2`. No PyPI, os classifiers de `django-environ 0.14.0` (2026-06-18) e `whitenoise 6.12.0` (2026-02-27) declaram suporte até Django 6.0, não 6.1. `gunicorn 26.2.0` e `psycopg 3.3.6` não declaram versão de Django. | Suposição: as quatro bibliotecas funcionam com Django 6.1.2. A Sprint 1 valida `django-environ` e `psycopg`; a Sprint 2 valida `gunicorn` e `whitenoise` com `manage.py check` e testes. Se falhar, vale a decisão D-04. |
| L-04 | O DESIGN.md da Wise usa a fonte proprietária **Wise Sans** para displays. | O próprio DESIGN.md indica substituto: **Inter** peso 900. O preview oficial carrega `Inter:wght@400;600;900` do Google Fonts. O Pytende usa só Inter. |
| L-05 | O DESIGN.md cita "medium shadow" em `ex-toast` e `ex-modal-card` sem valor. | O preview (`getdesign.md/design-md/wise/preview`) define `--shadow-md` e `--shadow-lg` como `0 0 0 1px` na cor `mute` (`#868685`) e o anel de foco como `0 0 0 2px #ffffff, 0 0 0 3px #0e0f0c`. Esses valores foram adotados. |
| L-06 | O deploy no Swarm usa o script público `setup_deploy.sh` do repositório `pycodebr/scsi_v1` (commit `6f443a7397830cd6c34a701346ac415f3b9c0fc7`, de 2026-10-12). O script foi lido, mas não executado nesta tarefa. | A Sprint 11 ensaia a stack num Swarm de um nó em Docker-in-Docker antes do deploy real (seção 14.11). |
| L-07 | No `docker-stack.yml` do `scsi_v1`, as redes `scsi_v1_internal` e `scsi_v1_egress` são declaradas pela própria stack, mas o `setup_deploy.sh` cria antes as redes `<stack>_internal` e `<stack>_egress`. Isso gera redes duplicadas com prefixo. | No Pytende, `pytende_internal` é declarada `external: true` na stack. O Pytende não usa `pytende_egress` porque nenhum serviço chama APIs externas. |
| L-08 | O `setup_deploy.sh` roda `seed_demo --force` quando o projeto não tem `scripts/post_deploy.sh`. O Pytende não tem dados de demonstração. | O Pytende traz `scripts/post_deploy.sh` (hook opcional do script), que substitui o seed. |
| L-09 | O certificado universal gratuito da Cloudflare cobre o domínio e um nível de subdomínio. Com o proxy da Cloudflare ligado, `traefik.pytende.pycodebr.com.br` (dois níveis) ficaria sem certificado na borda. A documentação da Cloudflare não foi consultada nesta data. | Os registros DNS do Pytende ficam **sem proxy** ("DNS only", nuvem cinza). O TLS é emitido pelo Traefik via Let's Encrypt DNS-01. A confirmar na Sprint 12 (D-03). |
| L-10 | O preço da VPS na Hostinger é promocional e vale para contrato de 24 meses. A renovação custa mais. | Os dois valores estão na seção 14.10, com a data da consulta. |
| L-11 | A base life (`/Users/azambuja/Documents/Obsidian/life`) foi consultada e não tem notas sobre o Pytende. | Nenhuma decisão anterior sobre o projeto foi herdada. |

---

## 3. Referências analisadas

### 3.1 SCSI (`https://github.com/pycodebr/scsi`, branch `main`) e scripts públicos (`https://github.com/pycodebr/scsi_v1`)

Arquivos lidos no `scsi`: `core/settings.py`, `core/urls.py`, `base/models.py`, `base/mixins.py`, `base/management/commands/wait_for_db.py`, `accounts/urls.py`, `.env.example`, `.gitignore`, `.dockerignore`, `Dockerfile`, `requirements.txt`, `static/css/tokens.css`, `scripts/backup.sh`, `docs/local-dev.md`, `docs/deploy.md`, `docs/backup.md`, a árvore `templates/` e o índice do `PRD.md`.

Arquivos lidos no `scsi_v1`: `docker-stack.yml`, `docker-compose.yml`, `Dockerfile`, `.dockerignore`, `entrypoint.sh`, `scripts/deploy.sh`, `scripts/setup_deploy.sh`, `scripts/backup.sh`, `scripts/README.md`.

**O que foi adaptado (só estrutura, documentação e deploy):**

| Padrão no SCSI | Onde | Adaptação no Pytende |
|---|---|---|
| Projeto `core` com apps de domínio na raiz e `app_name` em cada `urls.py` | `core/urls.py`, `accounts/urls.py` | Apps `base`, `accounts` e `tickets` na raiz, namespaces `accounts:` e `tickets:` |
| Model abstrata com `created_at` e `updated_at` e `verbose_name` em português | `base/models.py` (`BaseModel`) | `base.models.BaseModel`, só com timestamps (sem tenant) |
| Comando `wait_for_db` | `base/management/commands/wait_for_db.py` | Mesmo papel: o entrypoint espera o PostgreSQL antes de migrar |
| Settings único lendo `.env` com `django-environ` e `DATABASE_URL` via `env.db()` | `core/settings.py` | Mesmo padrão, com menos variáveis e sem default de SQLite |
| Lista `LOCAL_APPS` separada de `DJANGO_APPS` | `core/settings.py` | Mesmo padrão |
| Bloco `if not DEBUG:` com `SECURE_PROXY_SSL_HEADER`, `SECURE_SSL_REDIRECT`, `SECURE_REDIRECT_EXEMPT = [r'^health/$']`, HSTS e cookies seguros | `core/settings.py` | Mesmo padrão, sem `SECURE_HSTS_PRELOAD` |
| WhiteNoise com `CompressedStaticFilesStorage` | `core/settings.py` | Mesmo padrão |
| Endpoint `/health/` sem banco e sem login para healthcheck do container e do Traefik | `core/urls.py` | `core/views.py` + rota `health` |
| `LOGIN_URL`, `LOGIN_REDIRECT_URL`, `LOGOUT_REDIRECT_URL` com nomes de rota | `core/settings.py` | `accounts:login`, `tickets:list`, `accounts:login` |
| `LogoutView` nativa e login em `accounts/urls.py` | `accounts/urls.py` | `LoginView` e `LogoutView` nativas, sem registro nem recuperação de senha |
| `MESSAGE_TAGS` mapeando níveis do `messages` para classes CSS | `core/settings.py` | Classes próprias do design system Wise |
| Templates no nível do projeto: `templates/base.html`, `base_auth.html`, `base_app.html` e `templates/<app>/<model>_list.html` / `_form.html` | `templates/` | Mesma organização |
| `static/css/tokens.css` derivado de `design_system/design-system.html` | `static/css/tokens.css` | Mesmo papel, com os tokens da Wise |
| `.env.example` comentado por bloco, com placeholders do tipo `troque-...` | `.env.example` | Mesmo estilo, só com as variáveis do Pytende |
| `Dockerfile` com `python:3.13-slim`, `PYTHONUNBUFFERED`, `ENTRYPOINT ["./entrypoint.sh"]` | `Dockerfile` | Mesmo padrão, sem `build-essential`/`libpq-dev` (usa `psycopg[binary]`) |
| `.dockerignore` | `.dockerignore` | Mesmo conteúdo (exclui `.env`; `design_system/` fica na imagem, usado pelo T-04) |
| `entrypoint.sh`: `wait_for_db`, `migrate` com advisory lock do PostgreSQL, `collectstatic --clear`, `exec "$@"` | `entrypoint.sh` | Mesmo fluxo |
| `docker-compose.yml` de desenvolvimento com `app` (runserver, volume `.:/app`) e `db` (`postgres:16`, healthcheck `pg_isready`) | `docker-compose.yml` | Só `app` e `db` |
| `docker-stack.yml` com Traefik `v3.6` (provider Swarm, redirect HTTP para HTTPS, Let's Encrypt DNS-01 na Cloudflare, certificado wildcard, dashboard com Basic Auth), `app` com gunicorn, labels do Traefik, healthcheck e rate limit, `db` com `postgres:16` | `docker-stack.yml` | Só `traefik`, `app` e `db`; redes externas; `restart_policy: any` |
| `scripts/deploy.sh`: parser seguro do `.env` (sem `source`), validações, build com tag do commit e `latest`, push no GHCR, `docker stack deploy --with-registry-auth`, rollout forçado | `scripts/deploy.sh` | `STACK_NAME="pytende"`, imagem `ghcr.io/pycodebr/pytende`, rollout só do `app`, validação do `.env` dentro da imagem |
| `setup_deploy.sh` (fase 1 como root: update, fail2ban, swap, UFW, Docker, Swarm, usuário `deploy`; fase 2 como `deploy`: chave SSH, clone, GHCR, `.env`, redes, Basic Auth, secret da Cloudflare, DNS, deploy) e hooks opcionais `scripts/generate_env.sh` e `scripts/post_deploy.sh` | `scsi_v1/scripts/setup_deploy.sh` | Usado sem alteração; o Pytende traz os dois hooks |
| Backup com `pg_dump`, `gzip`, carimbo de data, rotação de 30 dias e cron diário às 3h | `scripts/backup.sh`, `docs/backup.md` | Mesmo padrão, sem backup de mídia |
| Guia de deploy passo a passo com checklist | `docs/deploy.md` | `docs/deploy/swarm.md` e seção 14 |

**O que foi descartado:**

| Item do SCSI | Motivo |
|---|---|
| Apps `insurance`, `insurers`, `claims`, `commissions`, `crm`, `partners`, `clients`, `documents`, `reports`, `dashboard`, `notifications` e todas as entidades, regras e telas de seguros | Domínio de corretora de seguros. Proibido pela regra 4 e fora do escopo. |
| `tenants`, `TenantAwareModel`, `TenantMiddleware`, `TenantQuerysetMixin` | Multi-tenant fora desta versão |
| `ai_agents`, LangChain, OpenAI, Celery, RabbitMQ, Redis, `django_celery_beat`, serviços `celery_worker`, `celery_beat`, `rabbitmq`, `redis`, `worker-entrypoint.sh`, rede `<stack>_egress` | Fora desta versão |
| `accounts.User` com login por e-mail, papéis (`RoleRequiredMixin`), registro, membros e recuperação de senha | Um único usuário e nenhum cadastro público. A troca de modelo de usuário é a decisão D-01. |
| `PerPageMixin` e paginação | Paginação não está nos requisitos (ver seção 7) |
| Volumes `media_data` e `static_data` | Não há uploads; os estáticos são gerados dentro do container a cada início e servidos pelo WhiteNoise |
| Métricas Prometheus no Traefik, `django-prometheus`, `monitoring-stack.yml`, `setup_monitoring.sh` | Observabilidade não está nos requisitos (ver seção 7) |
| Tema Duralux / Bootstrap 5 | O design system obrigatório é o da Wise |
| MkDocs (`mkdocs.yml`) | O projeto exige `README.md`; o guia de deploy é um Markdown simples |
| Mídia protegida, `seed_demo`, `templatetags/brl_tags.py` | Sem uploads, sem dados de demonstração e sem valores monetários |

### 3.2 Design system Wise

- `https://getdesign.md/design-md/wise/DESIGN.md`: lido por completo (24.577 bytes). Fonte de cores, tipografia, espaçamentos, raios, componentes, breakpoints e regras de uso.
- `https://getdesign.md/design-md/wise/preview`: lido (HTML de 95.921 bytes). Fonte dos valores de sombra e foco, da URL do Google Fonts e das larguras de contêiner (`1200px`, `720px`, `480px`).
- Os tokens extraídos estão na seção 9.

### 3.3 Estado atual do repositório (inspecionado em 2026-11-01)

| Item | Estado real |
|---|---|
| Python do `.venv` | `Python 3.13.11` (`.venv/bin/python --version`) |
| Django instalado | `6.1.2` (`.venv/bin/python -m django --version`) |
| Pacotes no `.venv` | `asgiref 3.13.0`, `Django 6.1.2`, `sqlparse 0.6.0`, `pip 26.2.2` |
| `requirements.txt` | `asgiref==3.13.0`, `Django==6.1.2`, `sqlparse==0.6.0` |
| Compatibilidade Python x Django | Compatível. Metadados do Django 6.1.2: `Requires-Python >=3.12`, classifiers 3.12, 3.13 e 3.14. Nenhum conflito a registrar. |
| Compatibilidade Django x PostgreSQL | O backend PostgreSQL do Django 6.1.2 exige PostgreSQL 15 ou mais novo (`minimum_database_version = (15,)` em `django/db/backends/postgresql/features.py`). A imagem `postgres:16` do SCSI atende. |
| `python manage.py check` | `System check identified no issues (0 silenced).` |
| Projeto Django | `core/` com `settings.py`, `urls.py`, `asgi.py`, `wsgi.py`, `__init__.py`; `manage.py` aponta para `core.settings` |
| `core/settings.py` | Padrão do `startproject` 6.1.2: `SECRET_KEY` escrita no código, `DEBUG = True`, `ALLOWED_HOSTS = []`, `LANGUAGE_CODE = 'en-us'`, `TIME_ZONE = 'UTC'`, `USE_TZ = True`, SQLite em `BASE_DIR / 'db.sqlite3'`, `STATIC_URL = 'static/'`, `MAILERS` com backend de console. Não lê o `.env`. |
| `core/urls.py` | Só `admin/` |
| `.env` | Existe e é ignorado pelo Git (`.gitignore:135:.env`). Tem chaves de PostgreSQL (agora no escopo) e chaves fora do escopo: RabbitMQ, Celery/Redis, OpenAI, Anthropic, LangSmith e SMTP (decisão D-05). Os valores não foram lidos nem copiados para este PRD. |
| `.gitignore` | Modelo toptal para Django; ignora `.env`, `.venv`, `db.sqlite3`, `staticfiles/`, `__pycache__/`, `.claude`, `.DS_Store` |
| `db.sqlite3` | Não existe. Nenhuma migration foi aplicada (relevante para D-01). |
| Apps de domínio, `templates/`, `static/`, `README.md`, `.env.example`, `design_system/`, `Dockerfile`, `docker-compose.yml`, `docker-stack.yml`, `scripts/`, `docs/` | Não existem |
| Git | Branch `main`, um commit (`5ba6d4b first commit`), remoto `origin` em `https://github.com/pycodebr/pytende.git`. `prompt-prd.md` não versionado. |
| DNS | `pycodebr.com.br` usa os nameservers da Cloudflare (`hunts.ns.cloudflare.com`, `pam.ns.cloudflare.com`). `pytende.pycodebr.com.br` ainda não tem registro A. |
| Risco | A `SECRET_KEY` gerada pelo `startproject` está no histórico do Git (commit `5ba6d4b`). Ela deve ser tratada como pública e nunca usada em produção (tarefa da Sprint 1). |

---

## 4. Requisitos funcionais

| ID | Requisito |
|---|---|
| RF-01 | Existe um único usuário, o responsável. A conta é criada com `python manage.py createsuperuser`. Não existe rota, tela ou formulário de cadastro público. |
| RF-02 | O responsável entra com usuário e senha na tela de Login. |
| RF-03 | O responsável pode sair (logout) de qualquer tela privada por um botão na barra de navegação. O logout usa POST com CSRF (exigência da `LogoutView` desde o Django 5.0) e leva à tela de Login. |
| RF-04 | Sem login, nenhuma página de atendimentos abre: lista, novo, edição e troca de status redirecionam para a tela de Login. Nas telas (GET), o parâmetro `next` guarda o caminho pedido, com a query string. |
| RF-05 | Depois de entrar, o responsável volta para o caminho em `next`. Sem `next`, ou com `next` apontando para outro domínio, ele vai para a Lista de atendimentos. |
| RF-06 | Usuário ou senha errados mostram a mensagem "Usuário ou senha inválidos.", a mesma nos dois casos, sem dizer qual campo está errado. |
| RF-07 | O sistema tem exatamente quatro telas: Login, Lista de atendimentos (tela inicial depois do login), Novo atendimento e Edição do atendimento. |
| RF-08 | O responsável cadastra um atendimento com cliente, assunto e descrição. Cliente e assunto são obrigatórios; a descrição é opcional. O cliente é texto livre (nome da pessoa ou da empresa), sem cadastro separado. |
| RF-09 | Depois de salvar um novo atendimento, o sistema volta para a lista e mostra "Atendimento cadastrado com sucesso." (framework `messages`). |
| RF-10 | O responsável edita cliente, assunto, descrição e status de um atendimento. Depois de salvar, o sistema volta para a lista e mostra "Atendimento atualizado com sucesso." |
| RF-11 | O responsável altera o status direto na lista, sem abrir a edição, por um formulário POST com token CSRF em cada linha. Depois da troca, ele volta para a lista com o mesmo filtro e vê a mensagem `Status de "<assunto>" alterado para <status>.` |
| RF-12 | Um formulário com erro (novo, edição ou login) mostra a mensagem junto do campo e mantém o que já foi digitado. |
| RF-13 | A lista mostra, para cada atendimento, cliente, assunto, status, data de abertura e data de conclusão (`—` quando não concluído), do mais recente para o mais antigo. |
| RF-14 | A lista tem filtro por status com as opções "Todos", "Pendente", "Em andamento" e "Concluído". O filtro fica na query string (`?status=pending`, `?status=in_progress`, `?status=completed`; "Todos" é a lista sem o parâmetro). Recarregar a página mantém a seleção. |
| RF-15 | Atendimentos concluídos continuam salvos e aparecem no filtro "Concluído" com a data e a hora da conclusão. |
| RF-16 | Quando o filtro escolhido não tem atendimentos, a lista mostra um aviso de lista vazia e um botão "Cadastrar atendimento" que leva à tela Novo atendimento. |
| RF-17 | O admin do Django lista os atendimentos com busca por cliente e assunto e filtro por status, para consultas e correções. A exclusão de atendimentos só existe no admin. |
| RF-18 | Jornada principal: o responsável entra, vê os pendentes, muda um atendimento para "em andamento", conclui quando termina o trabalho, filtra os concluídos e encontra esse atendimento com a data de conclusão. |

---

## 5. Requisitos não funcionais

| ID | Requisito | Verificação |
|---|---|---|
| RNF-01 | Interface responsiva em celular (< 768px), tablet (768px a 1023px) e desktop (>= 1024px), sem rolagem horizontal da página a partir de 360px de largura e com alvos de toque de no mínimo 48px de altura. | CA-33 (verificação manual na Sprint 10) |
| RNF-02 | Toda cor, fonte, espaçamento, raio e sombra vem dos tokens da seção 9, definidos em `static/css/tokens.css` e documentados em `design_system/design-system.html`. | T-04 |
| RNF-03 | Todas as views de atendimentos usam `LoginRequiredMixin`. Nenhuma página privada abre sem login. | T-13, T-87 |
| RNF-04 | Toda entrada do usuário é validada no servidor por forms do Django e pelas constraints do banco. | T-50 a T-56, T-39, T-40 |
| RNF-05 | Os dados persistem em PostgreSQL 16: container `db` do Docker Compose no desenvolvimento e serviço `db` do Swarm, com volume `pg_data`, em produção. Migrations versionadas em `tickets/migrations/`. Os testes rodam contra PostgreSQL. | Sprints 1 e 3 |
| RNF-06 | `python manage.py test` passa ao final de toda sprint. | Definição de pronto de cada sprint |
| RNF-07 | Segredos ficam só no `.env`, que é ignorado pelo Git e pelo Docker (`.dockerignore`), com permissão 600 na VPS. O `.env.example` tem só placeholders. O token da Cloudflare fica num Docker Secret, fora do `.env`. | T-02, CA-35 |
| RNF-08 | Produção com `DEBUG=False`, `ALLOWED_HOSTS` restrito ao domínio publicado e a `localhost` (healthcheck), HTTPS pelo Traefik com Let's Encrypt, redirecionamento HTTP para HTTPS, `SECURE_PROXY_SSL_HEADER`, `SECURE_SSL_REDIRECT=True`, HSTS, cookies seguros e `python manage.py check --deploy` sem avisos fora da lista aceita no README. | CA-34 |
| RNF-09 | Código (apps, models, campos, URLs, views, templates) em inglês e seguindo a PEP 8. Textos visíveis ao usuário em português brasileiro. | Revisão na definição de pronto |
| RNF-10 | `README.md` sempre atualizado com instalação, configuração, execução, testes, deploy e backup. | Tarefa de README em cada sprint que muda execução ou configuração |
| RNF-11 | Acessibilidade mínima: todo campo com `<label>` associado, mensagens de erro ligadas ao campo por `aria-describedby`, foco visível com o anel de foco da seção 9, filtro ativo com `aria-current="page"` e mensagens em região `role="status"` ou `role="alert"`. | T-63, T-73, revisão manual na Sprint 10 |
| RNF-12 | Plano de deploy com variáveis de ambiente, custos estimados com data, ensaio local da stack e rotina de backup com restauração testada. | Seção 14, CA-49, CA-50 |
| RNF-13 | Dependências Python mínimas: as três já instaladas mais `django-environ`, `psycopg[binary]`, `gunicorn` e `whitenoise`. Nenhuma biblioteca JavaScript. | Revisão do `requirements.txt` |
| RNF-14 | O container `app` expõe `/health/` (sem login, sem consulta ao banco, resposta JSON `{"status": "ok"}`) para o healthcheck do Swarm e do Traefik, e espera o banco (`wait_for_db`) antes de migrar. | T-05, T-06 |

---

## 6. Regras de negócio

| ID | Regra | Onde fica | Testes |
|---|---|---|---|
| RN-01 | Todo atendimento novo começa com status `pending` ("Pendente"), mesmo que o POST de cadastro envie outro status. | Default do campo `Ticket.status` e ausência do campo `status` em `TicketCreateForm` | T-30, T-53, T-72 |
| RN-02 | Os únicos status válidos são `pending` ("Pendente"), `in_progress` ("Em andamento") e `completed` ("Concluído"). Qualquer outro valor é rejeitado. | `TicketStatus` (TextChoices), forms e `CheckConstraint` `tickets_status_valid` | T-31, T-40, T-55, T-84 |
| RN-03 | A troca de status é livre, em qualquer ordem, inclusive para reabrir um atendimento concluído. | Ausência de qualquer restrição de transição no model e nos forms | T-35 |
| RN-04 | Quando o status passa para `completed`, o sistema grava a data e a hora atuais em `completed_at`. | `Ticket._sync_completed_at()`, chamado por `Ticket.clean()` e `Ticket.save()` | T-32, T-36, T-76, T-83, T-92 |
| RN-05 | Quando um atendimento concluído é reaberto (status passa para `pending` ou `in_progress`), `completed_at` volta a ser vazio (`NULL`). | `Ticket._sync_completed_at()` | T-33, T-36, T-77, T-83 |
| RN-06 | Salvar um atendimento que já estava concluído, sem mudar o status (por exemplo, corrigir a descrição), mantém a data de conclusão original. | `Ticket._sync_completed_at()` (só grava quando `completed_at` está vazio) | T-34 |
| RN-07 | As regras RN-04 a RN-06 valem igualmente na edição, na troca pela lista e no admin, sem lógica duplicada em views ou forms. O banco recusa um registro com status `completed` sem data, ou com data e outro status. | Model `Ticket` e `CheckConstraint` `tickets_completed_at_matches_status` | T-39, T-76, T-83, T-92 |
| RN-08 | Cliente (até 150 caracteres) e assunto (até 200 caracteres) são obrigatórios e não aceitam texto só com espaços. Descrição é opcional e sem limite. | Campos do model e forms (`strip=True`, padrão do Django) | T-50, T-51, T-52, T-56 |
| RN-09 | A lista ordena do mais recente para o mais antigo pela data de abertura (`created_at`), com `id` decrescente como desempate. | `Ticket.Meta.ordering` | T-37, T-60 |
| RN-10 | Não existe exclusão de atendimentos pela interface. Excluir só pelo admin. | Ausência de rota e botão de exclusão | T-67, T-87 |
| RN-11 | A troca de status pela lista aceita só POST com token CSRF válido. GET devolve 405 e POST sem token devolve 403. | `TicketStatusUpdateView.http_method_names` e `CsrfViewMiddleware` | T-81, T-82 |
| RN-12 | Datas são armazenadas em UTC (`USE_TZ = True`) e exibidas no fuso `America/Sao_Paulo`, no formato `dd/mm/aaaa HH:MM`. | Settings e filtro `date:"d/m/Y H:i"` nos templates | T-01, T-66 |

---

## 7. Fora desta versão

Nada desta lista aparece em sprint, model, tela ou rota.

| Item | Observação |
|---|---|
| Vários usuários, perfis de acesso, cadastro público de contas | RF-01 |
| Cadastro separado de clientes, histórico de contatos, área do cliente | Cliente é texto livre |
| Exclusão de atendimentos pela interface | Só pelo admin (RN-10) |
| Mensagens e notificações por e-mail ou WhatsApp | O backend de e-mail de console em `MAILERS` continua como está; sem SMTP |
| Pagamentos, anexos, prazos, prioridades, relatórios, gráficos, dashboard | |
| API e assistente de IA | |
| Multi-tenant, Celery/RabbitMQ, Redis, agentes de IA | |
| Recuperação de senha por e-mail e troca de senha pela interface | A troca de senha pode ser feita no admin ou com `python manage.py changepassword` dentro do container |
| Paginação e busca textual na lista | A busca existe só no admin (RF-17). Paginação vira candidata quando a lista ficar lenta (ver D-09). |
| Modelo de usuário customizado | Ver D-01 |
| Tema escuro, PWA, exportação de dados | |
| Stack de monitoramento (`setup_monitoring.sh`: Prometheus, Grafana, Loki) e `django-prometheus` | Observabilidade não está nos requisitos. Pode ser instalada depois, sem mudar o app, se for decidida. |
| CI/CD (GitHub Actions) e deploy por digest | O deploy é manual pelo `scripts/deploy.sh` na VPS |
| Cópia de backup automática fora da VPS | Nesta versão é manual e semanal (D-11) |

---

## 8. Arquitetura

### 8.1 Stack

| Camada | Tecnologia | Versão | Origem |
|---|---|---|---|
| Linguagem | Python | 3.13.11 no `.venv`; imagem `python:3.13-slim` no container | `.venv` existente (não recriar); imagem igual à do SCSI |
| Framework | Django | 6.1.2 | `requirements.txt` existente |
| Dependências do Django | asgiref, sqlparse | 3.13.0, 0.6.0 | `requirements.txt` existente |
| Leitura do `.env` | django-environ | 0.14.0 | A instalar na Sprint 1 (L-03, D-04) |
| Driver do banco | psycopg[binary] | 3.3.6 | A instalar na Sprint 1 |
| Banco | PostgreSQL | 16 (imagem `postgres:16`) | Igual ao SCSI; Django 6.1.2 exige 15 ou mais |
| Servidor WSGI | gunicorn | 26.2.0 | A instalar na Sprint 2 |
| Arquivos estáticos | whitenoise | 6.12.0 | A instalar na Sprint 2 |
| Autenticação | `django.contrib.auth` (`LoginView`, `LogoutView`, `LoginRequiredMixin`, `auth.User`) | Django 6.1.2 | Nativo |
| Mensagens | `django.contrib.messages` | Django 6.1.2 | Nativo |
| Templates | Django Template Language | Django 6.1.2 | Nativo |
| CSS | CSS puro com custom properties | | Sem framework |
| Fonte | Inter 400, 600 e 900 (Google Fonts) | | Substituto da Wise Sans indicado no DESIGN.md |
| Testes | `django.test` (runner `python manage.py test`) contra PostgreSQL | Django 6.1.2 | Nativo |
| Desenvolvimento | Docker Compose (`docker compose`) | instalado na máquina do Felipe | Rota B |
| Produção | Docker Swarm de um nó, Traefik `v3.6`, imagem no GHCR (`ghcr.io/pycodebr/pytende`) | | Rota B, igual ao `scsi_v1` |
| VPS | Ubuntu 24.04 LTS nova e dedicada (Hostinger KVM 1, D-02) | | Rota B |

Versões de pacotes conferidas no PyPI em 2026-11-01.

### 8.2 Visão de componentes (produção)

```mermaid
graph TB
    Browser[Navegador do responsável<br/>celular, tablet, desktop] -->|HTTPS| DNS[Cloudflare DNS<br/>pytende.pycodebr.com.br<br/>sem proxy]
    DNS --> Traefik
    subgraph VPS[VPS Ubuntu 24.04 - Docker Swarm de um nó]
        Traefik[pytende_traefik<br/>Traefik v3.6, portas 80/443<br/>Let's Encrypt DNS-01] -->|rede traefik_public| App[pytende_app<br/>gunicorn + WhiteNoise<br/>Django 6.1.2]
        App -->|rede pytende_internal| DB[(pytende_db<br/>postgres:16<br/>volume pg_data)]
        Cron[cron do usuário deploy<br/>scripts/backup.sh 03:00] -->|docker exec pg_dump| DB
        Cron --> Backups[(~/backups/db_*.sql.gz)]
    end
    GHCR[(ghcr.io/pycodebr/pytende)] -->|docker pull| App
    Traefik -->|DNS-01| CF[Cloudflare API<br/>Docker Secret CLOUDFLARE_DNS_API_TOKEN]
```

Dentro do container `app`, o Django tem os apps `accounts` (login e logout), `tickets` (domínio) e `base` (`BaseModel` e `wait_for_db`), mais o admin.

### 8.3 Visão de componentes (desenvolvimento)

```mermaid
graph LR
    Dev[Navegador local] -->|http://localhost:8000| AppDev[Compose app<br/>runserver + volume .:/app]
    AppDev --> DBDev[(Compose db<br/>postgres:16<br/>127.0.0.1:5432)]
    Venv[.venv local<br/>manage.py test / runserver] --> DBDev
```

Há dois jeitos de rodar localmente, ambos contra o mesmo PostgreSQL do Compose:
- `docker compose up` sobe `app` e `db`.
- `docker compose up -d db` mais o `.venv` local (`.venv/bin/python manage.py runserver` e `manage.py test`). É o caminho mais rápido para testes.

### 8.4 Estrutura de pastas (alvo ao fim da Sprint 12)

Arquivos marcados com `(existe)` já estão no repositório. Os demais são criados nas sprints indicadas.

```
pytende/
├── .dockerignore                 Sprint 2
├── .env                          (existe, ignorado pelo Git; ajustado pelo Felipe na Sprint 1)
├── .env.example                  Sprint 1
├── .gitignore                    (existe)
├── Dockerfile                    Sprint 2
├── PRD.md                        este documento
├── README.md                     Sprint 1, atualizado nas sprints seguintes
├── docker-compose.yml            Sprint 1 (db), Sprint 2 (app)
├── docker-stack.yml              Sprint 11
├── entrypoint.sh                 Sprint 2
├── manage.py                     (existe)
├── requirements.txt              (existe; recebe pacotes nas Sprints 1 e 2)
├── core/                         (existe)
│   ├── __init__.py               (existe)
│   ├── asgi.py                   (existe)
│   ├── settings.py               (existe; alterado nas Sprints 1, 2, 4, 5 e 10)
│   ├── tests.py                  Sprint 1
│   ├── urls.py                   (existe; alterado nas Sprints 2 e 5)
│   ├── views.py                  Sprint 2 (health_check)
│   └── wsgi.py                   (existe)
├── base/                         Sprint 2
│   ├── __init__.py
│   ├── apps.py
│   ├── management/
│   │   ├── __init__.py
│   │   └── commands/
│   │       ├── __init__.py
│   │       └── wait_for_db.py
│   ├── migrations/__init__.py
│   ├── models.py                 Sprint 3 (BaseModel abstrata)
│   └── tests.py
├── accounts/                     Sprint 5 (sem models)
│   ├── __init__.py
│   ├── apps.py
│   ├── forms.py                  LoginForm
│   ├── tests.py
│   └── urls.py
├── tickets/                      Sprint 3
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── forms.py                  Sprints 6, 8 e 9
│   ├── migrations/
│   │   ├── __init__.py
│   │   └── 0001_initial.py
│   ├── models.py
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── test_admin.py
│   │   ├── test_forms.py
│   │   ├── test_journey.py
│   │   ├── test_models.py
│   │   ├── test_urls.py
│   │   ├── test_views_form.py
│   │   ├── test_views_list.py
│   │   └── test_views_status.py
│   ├── urls.py                   Sprint 5
│   └── views.py                  Sprint 5
├── templates/                    Sprint 4
│   ├── base.html
│   ├── base_auth.html
│   ├── base_app.html             Sprint 5
│   ├── includes/
│   │   ├── form_field.html
│   │   └── messages.html
│   ├── accounts/
│   │   └── login.html            Sprint 5
│   └── tickets/
│       ├── ticket_form.html      Sprints 6 e 8 (Novo e Edição)
│       └── ticket_list.html      Sprint 5
├── static/                       Sprint 4
│   └── css/
│       ├── app.css
│       └── tokens.css
├── design_system/                Sprint 4
│   └── design-system.html
├── docs/
│   └── deploy/
│       └── swarm.md              Sprint 11
└── scripts/                      Sprint 11
    ├── backup.sh
    ├── deploy.sh
    ├── generate_env.sh
    └── post_deploy.sh
```

Arquivos gerados que não entram no Git: `staticfiles/`, `__pycache__/` (já cobertos pelo `.gitignore`).

### 8.5 Apps

| App | Responsabilidade | Models | Observação |
|---|---|---|---|
| `base` | Classe abstrata com timestamps para todos os models de negócio e comando `wait_for_db` | `BaseModel` (abstrata, sem tabela) | Padrão do SCSI, sem tenant |
| `accounts` | Login e logout com as views nativas e o form de login com mensagem genérica | Nenhum (usa `auth.User`) | Sem registro, sem recuperação de senha |
| `tickets` | Domínio de atendimentos: model, admin, forms, views, URLs | `Ticket` | Único app de domínio |

`INSTALLED_APPS` fica assim (padrão do SCSI):

```python
DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

LOCAL_APPS = [
    'base',
    'accounts',
    'tickets',
]

INSTALLED_APPS = DJANGO_APPS + LOCAL_APPS
```

### 8.6 Modelo de dados

```mermaid
erDiagram
    AUTH_USER {
        int id PK
        string username
        string password
        bool is_superuser
        bool is_staff
    }
    TICKET {
        bigint id PK
        varchar150 client
        varchar200 subject
        text description
        varchar20 status
        timestamptz completed_at "NULL quando nao concluido"
        timestamptz created_at
        timestamptz updated_at
    }
```

`Ticket` não tem chave estrangeira para `auth.User`: existe um único responsável (RF-01), e um vínculo de dono seria funcionalidade de multiusuário.

#### `base.models.BaseModel` (abstrata)

| Campo | Tipo | Opções | `verbose_name` |
|---|---|---|---|
| `created_at` | `DateTimeField` | `auto_now_add=True` | `criado em` |
| `updated_at` | `DateTimeField` | `auto_now=True` | `atualizado em` |

`Meta`: `abstract = True`.

#### `tickets.models.TicketStatus` (nível de módulo)

Fica fora da classe `Ticket` para poder ser usada dentro de `Ticket.Meta.constraints` (uma classe aninhada não enxerga atributos da classe externa).

```python
class TicketStatus(models.TextChoices):
    PENDING = 'pending', 'Pendente'
    IN_PROGRESS = 'in_progress', 'Em andamento'
    COMPLETED = 'completed', 'Concluído'
```

#### `tickets.models.Ticket(BaseModel)`

| Campo | Tipo | Opções | `verbose_name` | Regra |
|---|---|---|---|---|
| `id` | `BigAutoField` | padrão do Django 6.x (`DEFAULT_AUTO_FIELD` não é definido no settings) | | |
| `client` | `CharField` | `max_length=150` | `cliente` | RN-08 |
| `subject` | `CharField` | `max_length=200` | `assunto` | RN-08 |
| `description` | `TextField` | `blank=True` | `descrição` | RN-08 |
| `status` | `CharField` | `max_length=20`, `choices=TicketStatus.choices`, `default=TicketStatus.PENDING` | `status` | RN-01, RN-02 |
| `completed_at` | `DateTimeField` | `null=True`, `blank=True`, `editable=False` | `concluído em` | RN-04 a RN-07 |
| `created_at` | herdado de `BaseModel` | | `criado em` | Data de abertura exibida na lista |
| `updated_at` | herdado de `BaseModel` | | `atualizado em` | |

`Meta`:

```python
class Meta:
    verbose_name = 'atendimento'
    verbose_name_plural = 'atendimentos'
    ordering = ['-created_at', '-id']
    indexes = [
        models.Index(fields=['-created_at'], name='tickets_created_idx'),
        models.Index(fields=['status', '-created_at'], name='tickets_status_created_idx'),
    ]
    constraints = [
        models.CheckConstraint(
            condition=models.Q(status__in=TicketStatus.values),
            name='tickets_status_valid',
        ),
        models.CheckConstraint(
            condition=(
                models.Q(status=TicketStatus.COMPLETED, completed_at__isnull=False)
                | (~models.Q(status=TicketStatus.COMPLETED) & models.Q(completed_at__isnull=True))
            ),
            name='tickets_completed_at_matches_status',
        ),
    ]
```

No Django 6.x, `CheckConstraint` usa o argumento `condition` (o antigo `check` foi removido).

`__str__`: retorna `f'{self.client} - {self.subject}'`.

### 8.7 Onde fica a regra da data de conclusão

A regra (RN-04, RN-05, RN-06) fica **só no model `Ticket`**, num método privado chamado por `clean()` e por `save()`. Views, forms e admin não tocam em `completed_at`.

```python
def _sync_completed_at(self):
    if self.status == TicketStatus.COMPLETED:
        if self.completed_at is None:
            self.completed_at = timezone.now()
    else:
        self.completed_at = None

def clean(self):
    super().clean()
    self._sync_completed_at()

def save(self, *args, **kwargs):
    self._sync_completed_at()
    update_fields = kwargs.get('update_fields')
    if update_fields is not None and 'status' in update_fields:
        kwargs['update_fields'] = {*update_fields, 'completed_at'}
    super().save(*args, **kwargs)

def change_status(self, new_status):
    self.status = new_status
    self.save(update_fields=['status', 'updated_at'])
```

Como cada caminho passa por ela:

| Caminho | Fluxo | Garante a regra |
|---|---|---|
| Edição (`TicketUpdateView`) | `ModelForm.is_valid()` chama `instance.full_clean()`, que chama `clean()`. Depois `form.save()` chama `save()`. | Sim |
| Lista (`TicketStatusUpdateView`) | `ticket.change_status(status)` chama `save(update_fields=...)`, que inclui `completed_at`. | Sim |
| Admin (`TicketAdmin`) | O form do admin chama `full_clean()` e depois `save()`. `completed_at` é só leitura. | Sim |
| `QuerySet.update()` | Não passa por `save()`. | Proibido nas views. Se for usado por engano, a `CheckConstraint` `tickets_completed_at_matches_status` recusa o registro inconsistente com `IntegrityError` (T-39). |

`timezone` é `from django.utils import timezone`. Os testes controlam o horário com `unittest.mock.patch('django.utils.timezone.now', return_value=...)`.

### 8.8 Mapa de URLs

`core/urls.py`:

```python
urlpatterns = [
    path('health/', health_check, name='health'),
    path('admin/', admin.site.urls),
    path('', include('accounts.urls')),
    path('', include('tickets.urls')),
]
```

| Caminho | Nome | View | Métodos | Login | Tela |
|---|---|---|---|---|---|
| `/login/` | `accounts:login` | `LoginView` (nativa) com `LoginForm` | GET, POST | Não | 1. Login |
| `/logout/` | `accounts:logout` | `LogoutView` (nativa) | POST | | Não é tela |
| `/` | `tickets:list` | `TicketListView` | GET | Sim | 2. Lista de atendimentos |
| `/tickets/new/` | `tickets:create` | `TicketCreateView` | GET, POST | Sim | 3. Novo atendimento |
| `/tickets/<int:pk>/edit/` | `tickets:update` | `TicketUpdateView` | GET, POST | Sim | 4. Edição do atendimento |
| `/tickets/<int:pk>/status/` | `tickets:update_status` | `TicketStatusUpdateView` | POST | Sim | Não é tela (ação da lista) |
| `/health/` | `health` | `core.views.health_check` | GET | Não | Não é tela (healthcheck do container e do Traefik) |
| `/admin/` | `admin:*` | Admin do Django | | Staff | Não conta como tela da aplicação |

Não existem `register/`, `signup/`, `password-reset/` nem rotas de exclusão.

`accounts/urls.py`:

```python
app_name = 'accounts'

urlpatterns = [
    path(
        'login/',
        auth_views.LoginView.as_view(
            template_name='accounts/login.html',
            authentication_form=LoginForm,
        ),
        name='login',
    ),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
]
```

`tickets/urls.py`: `app_name = 'tickets'`, com os quatro caminhos da tabela.

### 8.9 Views

| View | Base | Atributos e comportamento |
|---|---|---|
| `core.views.health_check` | função | `return JsonResponse({'status': 'ok'})`. Não consulta o banco e não exige login. Isento do redirecionamento HTTPS (`SECURE_REDIRECT_EXEMPT`). |
| `LoginView` (nativa) | `django.contrib.auth.views.LoginView` | `template_name='accounts/login.html'`, `authentication_form=LoginForm`. Já trata `next` e ignora `next` para outro domínio (`url_has_allowed_host_and_scheme`). |
| `LogoutView` (nativa) | `django.contrib.auth.views.LogoutView` | Só POST. Redireciona para `LOGOUT_REDIRECT_URL` (`accounts:login`). |
| `TicketListView` | `LoginRequiredMixin, ListView` | `model=Ticket`, `template_name='tickets/ticket_list.html'`, `context_object_name='tickets'`. `get_queryset()`: lê `request.GET.get('status')`; se o valor está em `TicketStatus.values`, filtra por ele; caso contrário (ausente ou inválido), devolve todos. `get_context_data()` adiciona `current_status` (valor válido ou `''`), `status_filters`, uma lista de dicionários `{'value', 'label', 'url', 'is_active'}` na ordem Todos, Pendente, Em andamento, Concluído, e `status_choices` (para o select de cada linha). Sem paginação. |
| `TicketCreateView` | `LoginRequiredMixin, SuccessMessageMixin, CreateView` | `form_class=TicketCreateForm`, `template_name='tickets/ticket_form.html'`, `success_url=reverse_lazy('tickets:list')`, `success_message='Atendimento cadastrado com sucesso.'`. Contexto extra: `page_title='Novo atendimento'`, `submit_label='Cadastrar atendimento'`. |
| `TicketUpdateView` | `LoginRequiredMixin, SuccessMessageMixin, UpdateView` | `model=Ticket`, `form_class=TicketUpdateForm`, mesmo template, `success_url=reverse_lazy('tickets:list')`, `success_message='Atendimento atualizado com sucesso.'`. Contexto extra: `page_title='Editar atendimento'`, `submit_label='Salvar alterações'`. pk inexistente devolve 404. |
| `TicketStatusUpdateView` | `LoginRequiredMixin, View` | `http_method_names=['post']`. `post()`: `ticket = get_object_or_404(Ticket, pk=pk)`; `form = TicketStatusForm(request.POST)`; se válido, `ticket.change_status(form.cleaned_data['status'])` e `messages.success(request, f'Status de "{ticket.subject}" alterado para {ticket.get_status_display()}.')`; se inválido, não altera nada e `messages.error(request, 'Status inválido. Nenhuma alteração foi feita.')`. Redireciona para `request.POST['next']` se `url_has_allowed_host_and_scheme(next, allowed_hosts={request.get_host()}, require_https=request.is_secure())`; senão, para `tickets:list`. `handle_no_permission()` é sobrescrito para `redirect_to_login(reverse('tickets:list'))`, porque `next` apontando para uma rota só POST daria 405 depois do login. |

Nenhuma view usa `QuerySet.update()` nem `QuerySet.delete()`.

### 8.10 Forms

| Form | Base | Campos | Detalhes |
|---|---|---|---|
| `accounts.forms.LoginForm` | `AuthenticationForm` | `username`, `password` | `error_messages = {**AuthenticationForm.error_messages, 'invalid_login': 'Usuário ou senha inválidos.'}`. Labels "Usuário" e "Senha". Widgets com `autocomplete="username"` e `autocomplete="current-password"`. |
| `tickets.forms.TicketCreateForm` | `ModelForm` (`Ticket`) | `client`, `subject`, `description` | Labels "Cliente", "Assunto", "Descrição (opcional)". `error_messages`: `client.required='Informe o cliente.'`, `subject.required='Informe o assunto.'`. Placeholder do cliente: "Nome da pessoa ou da empresa". `description` com `Textarea(attrs={'rows': 5})`. Sem campo `status` (RN-01). |
| `tickets.forms.TicketUpdateForm` | `TicketCreateForm` | `client`, `subject`, `description`, `status` | `Meta.fields` acrescenta `status` com label "Status" e widget `Select`. |
| `tickets.forms.TicketStatusForm` | `forms.Form` | `status` | `ChoiceField(choices=TicketStatus.choices, error_messages={'required': 'Status inválido.', 'invalid_choice': 'Status inválido.'})`. |

Mensagens de tamanho máximo usam a tradução nativa do Django em pt-br.

### 8.11 Templates

| Template | Estende | Conteúdo |
|---|---|---|
| `templates/base.html` | | `<html lang="pt-br">`, `<meta name="viewport" content="width=device-width, initial-scale=1">`, `<title>{% block title %}{% endblock %} - Pytende</title>`, preconnect e link do Google Fonts, links para `css/tokens.css` e `css/app.css` via `{% static %}`, blocos `body_class` e `body`. |
| `templates/base_auth.html` | `base.html` | Página com fundo `canvas` (`#ffffff`) e card de autenticação centralizado (máx. 480px). |
| `templates/base_app.html` | `base.html` | Barra de navegação (wordmark "Pytende" com link para a lista, botão "Novo atendimento", formulário POST de logout com botão "Sair"), `{% include 'includes/messages.html' %}` e bloco `content` num contêiner de no máximo 1200px. |
| `templates/includes/messages.html` | | Lista as mensagens de `messages` com a classe vinda de `MESSAGE_TAGS`; sucesso com `role="status"`, erro com `role="alert"`. |
| `templates/includes/form_field.html` | | Recebe `field`: renderiza `<label for>`, o widget com `aria-describedby="<id>-error"` quando há erro, a classe `input--error` e as mensagens de erro do campo logo abaixo. |
| `templates/accounts/login.html` | `base_auth.html` | Tela 1 |
| `templates/tickets/ticket_list.html` | `base_app.html` | Tela 2 |
| `templates/tickets/ticket_form.html` | `base_app.html` | Telas 3 e 4 (o mesmo template, com `page_title` e `submit_label` vindos da view) |

### 8.12 Admin

```python
@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ('client', 'subject', 'status', 'created_at', 'completed_at')
    list_filter = ('status',)
    search_fields = ('client', 'subject')
    readonly_fields = ('completed_at', 'created_at', 'updated_at')
```

`tickets/apps.py`: `verbose_name = 'Atendimentos'`.

### 8.13 Comando `wait_for_db`

`base/management/commands/wait_for_db.py` (padrão do SCSI):

- Argumento `--timeout` (inteiro, segundos, padrão 60).
- Em laço, chama `connections['default'].ensure_connection()`; se der `OperationalError`, escreve "Aguardando o banco de dados..." e tenta de novo a cada 1 segundo.
- Ao conectar, escreve "Banco de dados disponível." e termina com código 0.
- Ao estourar o tempo, levanta `CommandError(f'Banco indisponível após {timeout}s: {exc}')`.

### 8.14 Settings por ambiente

Um único `core/settings.py` (padrão do SCSI). O comportamento de cada ambiente muda só pelas variáveis do `.env`.

```python
import environ
from django.contrib import messages

BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env(
    DEBUG=(bool, False),
    ALLOWED_HOSTS=(list, []),
    CSRF_TRUSTED_ORIGINS=(list, []),
)
environ.Env.read_env(BASE_DIR / '.env')

SECRET_KEY = env('SECRET_KEY')          # sem default: falha se faltar
DEBUG = env('DEBUG')
ALLOWED_HOSTS = env('ALLOWED_HOSTS')
CSRF_TRUSTED_ORIGINS = env('CSRF_TRUSTED_ORIGINS')

DATABASES = {
    'default': env.db('DATABASE_URL'),  # sem default: PostgreSQL obrigatório
}
```

`environ.Env.read_env` não sobrescreve variáveis que já existem no ambiente. Por isso o `environment:` do Compose e o `env_file` do Swarm têm prioridade sobre o arquivo `.env`.

| Setting | Desenvolvimento (`.env` local) | Produção (`.env` na VPS) | Sprint |
|---|---|---|---|
| `SECRET_KEY` | Chave nova, gerada localmente | Outra chave nova, com 50 caracteres ou mais | 1 |
| `DEBUG` | `True` | `False` | 1 |
| `ALLOWED_HOSTS` | `localhost,127.0.0.1` | `pytende.pycodebr.com.br,localhost` (`localhost` para o healthcheck do container) | 1 |
| `CSRF_TRUSTED_ORIGINS` | `http://localhost:8000,http://127.0.0.1:8000` | `https://pytende.pycodebr.com.br` | 1 |
| `DATABASES` | `env.db('DATABASE_URL')`, apontando para `localhost:5432` (`.venv`) ou `db:5432` (container) | `env.db('DATABASE_URL')`, apontando para `db:5432` | 1 |
| `LANGUAGE_CODE` | `'pt-br'` fixo no código | igual | 1 |
| `TIME_ZONE` | `'America/Sao_Paulo'` fixo no código | igual | 1 |
| `USE_I18N`, `USE_TZ` | `True` | igual | 1 |
| `STATIC_URL` | `'static/'` | igual | |
| `STATIC_ROOT` | `BASE_DIR / 'staticfiles'` | igual (`/app/staticfiles` no container) | 2 |
| `MIDDLEWARE` | `'whitenoise.middleware.WhiteNoiseMiddleware'` logo depois de `SecurityMiddleware` | igual | 2 |
| `STORAGES` | `{'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'}, 'staticfiles': {'BACKEND': 'whitenoise.storage.CompressedStaticFilesStorage'}}` | igual | 2 |
| `STATICFILES_DIRS` | `[BASE_DIR / 'static']` | igual | 4 |
| `TEMPLATES['DIRS']` | `[BASE_DIR / 'templates']` | igual | 4 |
| `MESSAGE_TAGS` | `{messages.SUCCESS: 'message--success', messages.ERROR: 'message--error', messages.INFO: 'message--info', messages.WARNING: 'message--warning', messages.DEBUG: 'message--info'}` | igual | 4 |
| `LOGIN_URL` | `'accounts:login'` | igual | 5 |
| `LOGIN_REDIRECT_URL` | `'tickets:list'` | igual | 5 |
| `LOGOUT_REDIRECT_URL` | `'accounts:login'` | igual | 5 |
| `MAILERS` | Mantido como está (console) | igual | |
| Bloco `if not DEBUG:` | Inativo | Ver abaixo | 10 |

Bloco de produção (Sprint 10):

```python
if not DEBUG:
    # O TLS termina no Traefik; o app recebe HTTP interno com X-Forwarded-Proto.
    # A porta 8000 não é publicada: só o Traefik alcança o app.
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SECURE_SSL_REDIRECT = env.bool('SECURE_SSL_REDIRECT', default=True)
    # O healthcheck do container bate em http://localhost:8000/health/ sem passar pelo Traefik.
    SECURE_REDIRECT_EXEMPT = [r'^health/$']
    SECURE_HSTS_SECONDS = env.int('SECURE_HSTS_SECONDS', default=3600)
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
```

---

## 9. Design system

Fonte: DESIGN.md e preview da Wise (seção 3.2). `static/css/tokens.css` define estes valores como custom properties; `static/css/app.css` só usa `var(--...)`, sem HEX solto. `design_system/design-system.html` é a referência visual (seção 9.7).

### 9.1 Cores

| Token CSS | HEX | Token Wise | Uso no Pytende |
|---|---|---|---|
| `--color-primary` | `#9fe870` | `primary` | Botão primário (único CTA por tela) |
| `--color-on-primary` | `#0e0f0c` | `on-primary` | Texto sobre o botão primário |
| `--color-primary-active` | `#cdffad` | `primary-active` | Hover e active do botão primário |
| `--color-primary-neutral` | `#c5edab` | `primary-neutral` | Reservado (não usado nas quatro telas) |
| `--color-primary-pale` | `#e2f6d5` | `primary-pale` | Fundo do badge "Concluído" |
| `--color-ink` | `#0e0f0c` | `ink` | Texto principal, títulos, bordas de input, filtro ativo |
| `--color-ink-deep` | `#163300` | `ink-deep` | Reservado |
| `--color-body` | `#454745` | `body` | Texto secundário, textos de ajuda |
| `--color-mute` | `#868685` | `mute` | Placeholder, `—` de data vazia, anel de sombra |
| `--color-canvas` | `#ffffff` | `canvas` | Cards, barra de navegação, fundo da tela de login |
| `--color-canvas-soft` | `#e8ebe6` | `canvas-soft` | Fundo das telas privadas, cabeçalho da tabela, card de login, estado vazio, botão secundário |
| `--color-positive` | `#2ead4b` | `positive` | Faixa lateral da mensagem de sucesso |
| `--color-positive-deep` | `#054d28` | `positive-deep` | Texto do badge "Concluído" |
| `--color-warning` | `#ffd11a` | `warning` | Fundo do badge "Pendente" |
| `--color-warning-deep` | `#b86700` | `warning-deep` | Reservado |
| `--color-warning-content` | `#4a3b1c` | `warning-content` | Texto do badge "Pendente" |
| `--color-negative` | `#d03238` | `negative` | Borda de input com erro, faixa lateral da mensagem de erro |
| `--color-negative-deep` | `#a72027` | `negative-deep` | Texto da mensagem de erro do campo |
| `--color-negative-darkest` | `#a7000d` | `negative-darkest` | Texto da mensagem de erro de login |
| `--color-negative-bg` | `#320707` | `negative-bg` | Reservado |
| `--color-accent-orange` | `#ffc091` | `accent-orange` | Reservado |
| `--color-accent-cyan` | `#38c8ff` | `accent-cyan` | Fundo do badge "Em andamento" (decisão D-10) |

Regra da Wise respeitada: o verde `#9fe870` é só CTA, nunca indicador de sucesso. O sucesso usa a família `positive`.

### 9.2 Tipografia

Família única: `--font-sans: "Inter", system-ui, -apple-system, sans-serif;` com `font-feature-settings: "calt";`. Carregamento: `https://fonts.googleapis.com/css2?family=Inter:wght@400;600;900&display=swap`.

| Token CSS | Tamanho / altura de linha | Peso | Espaçamento entre letras | Token Wise | Uso no Pytende |
|---|---|---|---|---|---|
| `--text-display-md` | 40px / 34px | 900 | 0 | `display-md` | Wordmark "Pytende" na tela de Login |
| `--text-display-sm` | 32px / 38.4px | 600 | -0.96px | `display-sm` | Título de página no desktop e tablet |
| `--text-display-xs` | 24px / 31.2px | 600 | -0.48px | `display-xs` | Título de página no celular; wordmark da barra de navegação (com peso 900) |
| `--text-body-lg` | 20px / 30px | 400 | 0 | `body-lg` | Texto do estado vazio |
| `--text-body-md` | 16px / 24px | 400 | 0 | `body-md` | Texto padrão, inputs |
| `--text-body-md-strong` | 16px / 24px | 600 | 0 | `body-md-strong` | Assunto na lista |
| `--text-body-sm` | 14px / 20px | 400 | 0 | `body-sm` | Células da tabela, mensagens, erros de campo |
| `--text-body-sm-strong` | 14px / 20px | 600 | 0 | `body-sm-strong` | Labels, badges, links da navegação, filtros |
| `--text-caption` | 12px / 16px | 400 | 0 | `caption` | Cabeçalho da tabela (maiúsculas), rótulos dos cards no celular |
| `--text-button-md` | 16px / 24px | 600 | 0 | `button-md` | Rótulo de botões |

Os tokens `display-mega` (126px), `display-xxl` (96px), `display-xl` (64px) e `display-lg` (47px) são de páginas de marketing e não aparecem nas quatro telas. Eles ficam documentados em `design-system.html`.

### 9.3 Espaçamento, raios e sombras

| Token CSS | Valor | Token Wise |
|---|---|---|
| `--space-xxs` | 2px | `spacing.xxs` |
| `--space-xs` | 4px | `spacing.xs` |
| `--space-sm` | 8px | `spacing.sm` |
| `--space-md` | 12px | `spacing.md` |
| `--space-lg` | 16px | `spacing.lg` |
| `--space-xl` | 24px | `spacing.xl` |
| `--space-2xl` | 32px | `spacing.2xl` |
| `--space-3xl` | 48px | `spacing.3xl` |
| `--radius-none` | 0px | `rounded.none` |
| `--radius-sm` | 8px | `rounded.sm` |
| `--radius-md` | 12px | `rounded.md` |
| `--radius-lg` | 16px | `rounded.lg` |
| `--radius-xl` | 24px | `rounded.xl` |
| `--radius-pill` | 9999px | `rounded.pill` |
| `--shadow-ring` | `0 0 0 1px #868685` | `--shadow-md` / `--shadow-lg` do preview |
| `--focus-ring` | `0 0 0 2px #ffffff, 0 0 0 3px #0e0f0c` | anel de foco do preview |
| `--container-max` | 1200px | contêiner da Wise |
| `--container-form` | 720px | largura de formulário do preview |
| `--container-auth` | 480px | largura do card de autenticação do preview |

Elevação (Wise): nível 0 sem sombra; nível 1 com borda de 1px `#0e0f0c` (inputs e botão terciário); nível 2 é o card branco sobre o fundo `#e8ebe6`, sem sombra (o contraste de superfície faz a elevação). Só as mensagens usam `--shadow-ring`.

### 9.4 Componentes

| Componente | Especificação | Base Wise |
|---|---|---|
| Barra de navegação | Fundo `#ffffff`, padding 12px 24px (12px 16px no celular), altura mínima 64px. Wordmark "Pytende" Inter 900 24px `#0e0f0c`. À direita: botão primário "Novo atendimento" e botão terciário "Sair" (dentro de `<form method="post">`). No celular, os dois botões ficam com padding 8px 16px. | `nav-bar`, `nav-link` |
| Botão primário | Fundo `#9fe870`, texto `#0e0f0c`, 16px/24px peso 600, padding 12px 24px, raio 24px, altura mínima 48px, sem borda. Hover e active: fundo `#cdffad`. Foco: `--focus-ring`. | `button-primary` |
| Botão secundário | Fundo `#e8ebe6`, texto `#0e0f0c`, mesma tipografia, padding e raio. Usado em "Cancelar" e no botão "Atualizar" do select de status. | `button-secondary` |
| Botão terciário | Fundo `#ffffff`, texto `#0e0f0c`, borda 1px `#0e0f0c`, mesma tipografia, padding e raio. Usado em "Sair" e "Editar". | `button-tertiary` |
| Input de texto, textarea e select | Fundo `#ffffff`, texto `#0e0f0c`, borda 1px `#0e0f0c`, raio 12px, padding 12px 16px, 16px/24px peso 400, largura 100%, altura mínima 48px. Placeholder `#868685`. Foco: `--focus-ring`. | `text-input` |
| Label | 14px/20px peso 600 `#0e0f0c`, margem inferior 8px. | `body-sm-strong` |
| Erro de campo | Borda do input `#d03238`; mensagem abaixo, 14px/20px peso 400 `#a72027`, margem superior 4px, com `id="<campo>-error"`. | família `negative` |
| Erro de login (não ligado a campo) | Bloco acima dos campos: fundo `#ffffff`, borda 1px `#d03238`, raio 12px, padding 12px 16px, texto 14px `#a7000d`, `role="alert"`. | família `negative` |
| Badge de status | Raio 9999px, padding 4px 12px, 14px/20px peso 600, `white-space: nowrap`. Pendente: fundo `#ffd11a`, texto `#4a3b1c`. Em andamento: fundo `#38c8ff`, texto `#0e0f0c`. Concluído: fundo `#e2f6d5`, texto `#054d28`. | `badge-positive` e paleta semântica |
| Filtro por status | `<nav aria-label="Filtrar por status">` com links em formato de pílula: raio 9999px, padding 8px 16px, 14px/20px peso 600, altura mínima 48px, `flex-wrap: wrap`, espaço de 8px. Inativo: fundo `#ffffff`, texto `#0e0f0c`, borda 1px `#0e0f0c`. Ativo: fundo `#0e0f0c`, texto `#ffffff`, `aria-current="page"`. | `button-tertiary` e polaridade invertida da Wise |
| Card de conteúdo | Fundo `#ffffff`, raio 24px, padding 24px (16px no celular), sem borda e sem sombra. | `card-content` |
| Tabela (desktop e tablet) | Dentro do card. Cabeçalho: fundo `#e8ebe6`, 12px/16px peso 400, maiúsculas, texto `#454745`. Células: padding 12px 16px, 14px/20px; assunto em 16px peso 600. Linha: borda inferior 1px `#e8ebe6`. Colunas: Cliente, Assunto, Status, Aberto em, Concluído em, Ações. | `ex-data-table-cell` |
| Linha como card (celular) | Abaixo de 768px, cada `<tr>` vira um bloco com fundo `#ffffff`, raio 16px, padding 16px, margem inferior 12px. Cada célula mostra o rótulo (atributo `data-label`) em 12px `#454745` acima do valor. O cabeçalho fica visível só para leitores de tela. | `rounded.lg` |
| Ações da linha | Link "Editar" (botão terciário) e formulário de status: `<label class="visually-hidden">`, `<select name="status">` com o status atual selecionado e botão secundário "Atualizar". No celular ocupam a largura toda, empilhados com espaço de 8px. | |
| Mensagem (toast) | Fundo `#ffffff`, raio 24px, padding 12px 16px, `--shadow-ring`, 14px/20px `#0e0f0c`, faixa lateral esquerda de 4px: `#2ead4b` (sucesso) ou `#d03238` (erro). Fica no topo do conteúdo, abaixo da barra de navegação. Sem fechamento automático e sem JavaScript. | `ex-toast` |
| Estado vazio | Fundo `#e8ebe6`, raio 24px, padding 48px (24px no celular), texto centralizado 20px/30px peso 400 `#0e0f0c` e botão primário "Cadastrar atendimento". | `ex-empty-state-card` |
| Card de login | Fundo `#e8ebe6`, raio 24px, padding 24px, largura máxima 480px, centralizado na página `#ffffff` com margem superior de 48px. | `ex-auth-form-card` |
| Bloco de datas (Edição) | Lista de definição em 14px `#454745`: "Aberto em dd/mm/aaaa HH:MM" e "Concluído em dd/mm/aaaa HH:MM" ou "Concluído em —". | `body-sm` |

### 9.5 Comportamento responsivo

| Faixa | Largura | Comportamento |
|---|---|---|
| Celular | < 768px | Gutter lateral de 16px. Título 24px. Tabela vira cards empilhados. Botões dos formulários com largura 100%. Filtros quebram linha. |
| Tablet | 768px a 1023px | Gutter de 24px. Título 32px. Tabela completa; a coluna "Concluído em" pode quebrar a data em duas linhas. |
| Desktop | >= 1024px | Contêiner centralizado com no máximo 1200px. Formulários com no máximo 720px. Título 32px. |

Regras para todas as faixas: nenhuma rolagem horizontal da página a partir de 360px; alvos de toque com no mínimo 48px de altura; nenhum layout depende de JavaScript.

### 9.6 Regras de uso (Do / Don't da Wise aplicados)

- Um único botão primário verde por tela: "Entrar" (Login), "Novo atendimento" na barra (Lista), "Cadastrar atendimento" (Novo), "Salvar alterações" (Edição). O botão "Cadastrar atendimento" do estado vazio é o CTA principal quando a lista está vazia.
- Botões e cards sempre arredondados (24px). Nada de cantos retos em elementos de interface.
- O verde nunca aparece sobre fundo verde.
- Nenhuma cor fora da tabela 9.1.

### 9.7 Papel de `design_system/design-system.html`

- Arquivo HTML autônomo (abre direto no navegador, sem Django), criado na Sprint 4. É a referência visual que o agente consulta antes de escrever qualquer template.
- Contém, nesta ordem: paleta (amostra, nome do token e HEX), escala tipográfica, espaçamentos, raios, anel de sombra e de foco, botões (primário, secundário, terciário, com hover e foco), inputs (normal, foco, erro com mensagem), select, badges dos três status, filtro (ativo e inativo), tabela de atendimentos (desktop) e a mesma lista como cards (celular), mensagens de sucesso e erro, estado vazio, barra de navegação e card de login.
- Declara os mesmos custom properties de `static/css/tokens.css`, com os mesmos valores. O teste T-04 garante que todo HEX de `tokens.css` aparece em `design-system.html`.
- Usa textos de exemplo do domínio do Pytende (por exemplo, cliente "Padaria Bom Dia", assunto "Atualizar cardápio do site"), nunca textos do SCSI ou da Wise.

---

## 10. Telas

### 10.1 Tela 1 - Login (`/login/`, `templates/accounts/login.html`)

| Item | Especificação |
|---|---|
| Layout | `base_auth.html`: página `#ffffff`, card de login centralizado |
| Elementos | Wordmark "Pytende" (40px peso 900); subtítulo "Controle de atendimentos" (16px `#454745`); campo "Usuário"; campo "Senha" (`type="password"`); campo oculto `next` com o valor recebido; botão primário "Entrar" com largura 100% |
| Título da aba | "Entrar - Pytende" |
| Estado de erro | Bloco de erro "Usuário ou senha inválidos." acima dos campos; o campo Usuário mantém o valor digitado; o campo Senha volta vazio (comportamento nativo e seguro) |
| Estado de campo vazio | Mensagem nativa do Django em pt-br ("Este campo é obrigatório.") abaixo do campo |
| Sucesso | Redireciona para `next` válido ou para `/` |
| Navegação | Sem barra de navegação, sem link de cadastro, sem "esqueci minha senha" |

### 10.2 Tela 2 - Lista de atendimentos (`/`, `templates/tickets/ticket_list.html`)

| Item | Especificação |
|---|---|
| Layout | `base_app.html`: barra de navegação, mensagens, contêiner |
| Elementos | Título "Atendimentos"; filtro com "Todos" (`/`), "Pendente" (`/?status=pending`), "Em andamento" (`/?status=in_progress`), "Concluído" (`/?status=completed`); card com a tabela |
| Colunas | Cliente; Assunto; Status (badge); Aberto em (`created_at`, `dd/mm/aaaa HH:MM`); Concluído em (`completed_at` no mesmo formato, ou `—`); Ações (Editar e formulário de status) |
| Formulário de status por linha | `<form method="post" action="{% url 'tickets:update_status' ticket.pk %}">`, `{% csrf_token %}`, `<input type="hidden" name="next" value="{{ request.get_full_path }}">`, `<label for="status-{{ ticket.pk }}" class="visually-hidden">Status de {{ ticket.subject }}</label>`, select com os três status (atual selecionado), botão "Atualizar" |
| Título da aba | "Atendimentos - Pytende" |
| Estado vazio (sem filtro) | Texto "Você ainda não tem atendimentos cadastrados." e botão "Cadastrar atendimento" (`tickets:create`) |
| Estado vazio (com filtro) | Texto `Nenhum atendimento com status "<rótulo>".` e botão "Cadastrar atendimento" |
| Sucesso | Mensagem vinda do cadastro, da edição ou da troca de status |
| Erro | Mensagem "Status inválido. Nenhuma alteração foi feita." |
| Navegação | Wordmark e "Todos" levam a `/`; "Novo atendimento" leva à Tela 3; "Editar" leva à Tela 4; "Sair" faz logout |
| Ausente de propósito | Botão ou link de exclusão, paginação, busca |

### 10.3 Tela 3 - Novo atendimento (`/tickets/new/`, `templates/tickets/ticket_form.html`)

| Item | Especificação |
|---|---|
| Elementos | Título "Novo atendimento"; card com os campos "Cliente" (obrigatório, placeholder "Nome da pessoa ou da empresa"), "Assunto" (obrigatório) e "Descrição (opcional)" (textarea, 5 linhas); botão primário "Cadastrar atendimento"; botão secundário "Cancelar" (link para `/`) |
| Status | Não aparece. Texto de ajuda abaixo do título: "Todo atendimento novo começa como Pendente." (14px `#454745`) |
| Título da aba | "Novo atendimento - Pytende" |
| Estado de erro | HTTP 200, cada erro abaixo do seu campo ("Informe o cliente.", "Informe o assunto."), borda vermelha no campo, valores digitados mantidos em todos os campos |
| Sucesso | Redireciona para `/` com "Atendimento cadastrado com sucesso." |
| Navegação | Barra de navegação completa; "Cancelar" volta para a lista |

### 10.4 Tela 4 - Edição do atendimento (`/tickets/<pk>/edit/`, `templates/tickets/ticket_form.html`)

| Item | Especificação |
|---|---|
| Elementos | Título "Editar atendimento"; bloco de datas ("Aberto em ...", "Concluído em ..." ou "Concluído em —"); campos "Cliente", "Assunto", "Descrição (opcional)" e "Status" (select com os três status), preenchidos; botão primário "Salvar alterações"; botão secundário "Cancelar" (link para `/`) |
| Título da aba | "Editar atendimento - Pytende" |
| Estado de erro | HTTP 200, erros junto dos campos, valores digitados mantidos (inclusive o status escolhido) |
| Sucesso | Redireciona para `/` com "Atendimento atualizado com sucesso."; `completed_at` gravado ou apagado conforme RN-04 a RN-06 |
| Atendimento inexistente | HTTP 404 |
| Navegação | Barra de navegação completa; "Cancelar" volta para a lista |
| Ausente de propósito | Botão de exclusão |

### 10.5 Fluxo de navegação

```mermaid
flowchart TD
    A[Acessa qualquer URL privada] --> B{Autenticado?}
    B -- Não --> L[Tela 1: Login<br/>?next=caminho pedido]
    L -- Credenciais inválidas --> E[Login com<br/>'Usuário ou senha inválidos.'] --> L
    L -- Credenciais válidas --> N{next válido?}
    N -- Sim --> P[Página pedida]
    N -- Não --> LI
    B -- Sim --> P
    P --> LI[Tela 2: Lista<br/>?status=...]
    LI -- Novo atendimento --> NV[Tela 3: Novo]
    NV -- Salvar válido --> LI
    NV -- Erro --> NV
    LI -- Editar --> ED[Tela 4: Edição]
    ED -- Salvar válido --> LI
    ED -- Erro --> ED
    LI -- Atualizar status POST --> LI
    LI -- Sair POST --> L
    NV -- Sair POST --> L
    ED -- Sair POST --> L
```

---

## 11. Critérios de aceite

Cada critério é verificável por um teste automatizado (coluna Teste) ou, quando indicado, por verificação manual com passos definidos.

| ID | Requisitos | Dado | Quando | Então | Teste |
|---|---|---|---|---|---|
| CA-01 | RF-01 | um banco sem usuários e a variável `DJANGO_SUPERUSER_PASSWORD` definida | o comando `createsuperuser --noinput --username responsavel --email responsavel@example.com` é executado | existe um usuário `responsavel` com `is_superuser=True` e `is_staff=True`, e `self.client.login(username='responsavel', password=<senha>)` devolve `True` | T-10 |
| CA-02 | RF-01, RF-07 | um visitante anônimo | ele acessa `/register/`, `/signup/` ou `/accounts/signup/` | a resposta é 404 | T-11 |
| CA-03 | RF-02 | o usuário `responsavel` existe | o visitante faz GET em `/login/` | a resposta é 200, contém os campos `username` e `password` e os rótulos "Usuário" e "Senha" | T-12 |
| CA-04 | RF-04, RNF-03 | um visitante anônimo | ele faz GET em `/?status=pending`, `/tickets/new/` ou `/tickets/<pk>/edit/` | a resposta é 302 para `/login/?next=` seguido do caminho pedido codificado (por exemplo `/login/?next=/%3Fstatus%3Dpending`) | T-13 |
| CA-05 | RF-04 | um visitante anônimo e um atendimento pendente | ele faz POST em `/tickets/<pk>/status/` com `status=completed` | a resposta é 302 para `/login/?next=/` e o atendimento continua pendente | T-13 |
| CA-06 | RF-05 | um visitante na URL `/login/?next=/%3Fstatus%3Dpending` | ele envia usuário e senha corretos com `next=/?status=pending` | a resposta é 302 para `/?status=pending` | T-14 |
| CA-07 | RF-05 | um visitante em `/login/` sem `next` | ele envia usuário e senha corretos | a resposta é 302 para `/` | T-15 |
| CA-08 | RF-05 | um visitante em `/login/` | ele envia credenciais corretas com `next=https://exemplo-externo.com/` | a resposta é 302 para `/` | T-16 |
| CA-09 | RF-06, RF-12 | o usuário `responsavel` existe | o visitante envia senha errada para `responsavel` e, em outra tentativa, um usuário inexistente | as duas respostas são 200, ambas contêm exatamente "Usuário ou senha inválidos.", nenhuma contém "senha incorreta" nem "usuário não existe", e o campo usuário mantém o valor digitado | T-17 |
| CA-10 | RF-03 | o responsável autenticado | ele faz GET em `/logout/` | a resposta é 405 e a sessão continua ativa | T-18 |
| CA-11 | RF-03 | o responsável autenticado em qualquer tela privada (Lista, Novo, Edição) | a tela é carregada | o HTML contém um `<form method="post" action="/logout/">` com `csrfmiddlewaretoken` e o botão "Sair" | T-19 |
| CA-12 | RF-03 | o responsável autenticado | ele faz POST em `/logout/` | a resposta é 302 para `/login/` e um GET seguinte em `/` redireciona para o login | T-20 |
| CA-13 | RF-07, RN-10 | o projeto completo | as rotas de `core.urls`, `accounts.urls` e `tickets.urls` são listadas | os nomes são exatamente `{health}` (além do include do admin), `{login, logout}` e `{list, create, update, update_status}` | T-87 |
| CA-14 | RF-08, RF-09, RN-01 | o responsável autenticado na Tela 3 | ele envia cliente "Padaria Bom Dia", assunto "Atualizar cardápio do site" e descrição vazia | um `Ticket` é criado com status `pending` e `completed_at` nulo, a resposta é 302 para `/`, e a lista seguinte mostra "Atendimento cadastrado com sucesso." | T-71 |
| CA-15 | RN-01 | o responsável autenticado | ele envia o cadastro com o campo extra `status=completed` | o atendimento criado tem status `pending` e `completed_at` nulo | T-72 |
| CA-16 | RF-08, RF-12, RN-08 | o responsável autenticado na Tela 3 | ele envia cliente com três espaços, assunto vazio e descrição "Detalhes" | a resposta é 200, nenhum `Ticket` é criado, "Informe o cliente." e "Informe o assunto." aparecem junto dos campos e a textarea contém "Detalhes" | T-73 |
| CA-17 | RF-10 | um atendimento pendente | o responsável envia a Tela 4 com assunto "Assunto revisado" | o atendimento é atualizado, a resposta é 302 para `/` e a lista mostra "Atendimento atualizado com sucesso." | T-75 |
| CA-18 | RF-10, RN-04, RN-07 | um atendimento pendente e o relógio em 2026-11-03 17:30 UTC | o responsável envia a Tela 4 com status `completed` | `completed_at` é 2026-11-03 17:30 UTC | T-76 |
| CA-19 | RF-10, RN-05, RN-07 | um atendimento concluído | o responsável envia a Tela 4 com status `pending` | `completed_at` fica nulo | T-77 |
| CA-20 | RN-06 | um atendimento concluído em 2026-11-03 17:30 UTC | ele é salvo de novo com status `completed` e outra descrição, com o relógio em 2026-11-05 10:00 UTC | `completed_at` continua 2026-11-03 17:30 UTC | T-34 |
| CA-21 | RF-10, RF-12 | um atendimento existente | o responsável envia a Tela 4 com assunto vazio e status `in_progress` | a resposta é 200, o banco não muda, "Informe o assunto." aparece junto do campo e o select mostra `in_progress` selecionado | T-78 |
| CA-22 | RF-10 | nenhum atendimento com pk 9999 | o responsável faz GET em `/tickets/9999/edit/` | a resposta é 404 | T-79 |
| CA-23 | RF-11 | um atendimento pendente e o responsável na URL `/?status=pending` | ele faz POST em `/tickets/<pk>/status/` com `status=in_progress` e `next=/?status=pending` | o status passa a `in_progress`, a resposta é 302 para `/?status=pending` e a página seguinte mostra `Status de "<assunto>" alterado para Em andamento.` | T-80 |
| CA-24 | RF-11, RN-11 | o responsável autenticado | ele faz GET em `/tickets/<pk>/status/` | a resposta é 405 | T-81 |
| CA-25 | RF-11, RN-11 | um `Client(enforce_csrf_checks=True)` autenticado | ele faz POST em `/tickets/<pk>/status/` sem `csrfmiddlewaretoken` | a resposta é 403 e o status não muda | T-82 |
| CA-26 | RF-11, RN-04, RN-05, RN-07 | um atendimento em andamento | o responsável troca pela lista para `completed` e depois para `in_progress` | depois da primeira troca `completed_at` tem valor; depois da segunda, é nulo | T-83 |
| CA-27 | RN-02 | um atendimento pendente | o responsável faz POST em `/tickets/<pk>/status/` com `status=archived` | o status continua `pending`, a resposta é 302 e a página seguinte mostra "Status inválido. Nenhuma alteração foi feita." | T-84 |
| CA-28 | RF-11 | um atendimento pendente | o responsável faz POST de troca de status com `next=https://exemplo-externo.com/` | a resposta é 302 para `/` | T-85 |
| CA-29 | RN-03 | um atendimento em cada status | ele passa por todas as seis transições possíveis entre os três status | todas são salvas sem erro e `completed_at` segue RN-04 e RN-05 em cada uma | T-35 |
| CA-30 | RF-13, RN-09 | três atendimentos criados em horários diferentes | o responsável abre `/` | os três aparecem do mais recente para o mais antigo, com cliente, assunto, rótulo do status, data de abertura e `—` em "Concluído em" | T-60 |
| CA-31 | RF-14 | um atendimento em cada status | o responsável abre `/?status=pending`, `/?status=in_progress` e `/?status=completed` | cada página mostra só o atendimento daquele status, e abrir a mesma URL de novo dá o mesmo resultado | T-61 |
| CA-32 | RF-14 | um atendimento em cada status | o responsável abre `/` e `/?status=xyz` | as duas páginas mostram os três atendimentos e o filtro "Todos" marcado | T-62 |
| CA-33 | RNF-01 | o ambiente local com 5 atendimentos (um com assunto de 200 caracteres) | o responsável abre Login, Lista, Novo e Edição no modo responsivo do navegador em 360px, 768px e 1280px | em todas as larguras `document.documentElement.scrollWidth` é menor ou igual à largura da janela, todos os botões e links de ação medem pelo menos 48px de altura e, em 360px, a lista aparece como cards | Manual (Sprint 10) |
| CA-34 | RNF-08 | variáveis de produção (`DEBUG=False`, `ALLOWED_HOSTS` do domínio e `localhost`, `SECRET_KEY` nova, `SECURE_HSTS_SECONDS=3600`) | `python manage.py check --deploy` é executado | a saída tem no máximo o aviso `security.W021` (HSTS preload), listado como aceito no README | Manual (Sprints 10 e 12) |
| CA-35 | RNF-07 | o repositório | `git check-ignore .env` é executado, o `.dockerignore` e o `.env.example` são lidos | o primeiro comando imprime `.env`, o `.dockerignore` contém a linha `.env`, e o `.env.example` tem só os valores placeholder da seção 14.6 | T-02 |
| CA-36 | RF-14, RNF-11 | o responsável em `/?status=completed` | a página é carregada | o link "Concluído" tem `aria-current="page"` e nenhum outro link do filtro tem | T-63 |
| CA-37 | RF-16 | nenhum atendimento concluído | o responsável abre `/?status=completed` | a página mostra `Nenhum atendimento com status "Concluído".` e um link para `/tickets/new/` com o texto "Cadastrar atendimento" | T-64 |
| CA-38 | RF-16 | nenhum atendimento | o responsável abre `/` | a página mostra "Você ainda não tem atendimentos cadastrados." e o link "Cadastrar atendimento" | T-64 |
| CA-39 | RF-15 | um atendimento concluído em 2026-11-03 17:30 UTC | o responsável abre `/?status=completed` | o atendimento aparece com "03/11/2026 14:30" na coluna "Concluído em" | T-65 |
| CA-40 | RN-12 | um atendimento criado em 2026-11-01 15:00 UTC | o responsável abre `/` | a coluna "Aberto em" mostra "01/11/2026 12:00" | T-66 |
| CA-41 | RN-10 | um atendimento qualquer | o responsável abre a Lista e a Edição | nenhum dos HTMLs contém "Excluir" nem um link para rota de exclusão | T-67 |
| CA-42 | RF-17 | atendimentos com cliente "Padaria Bom Dia" e assunto "Revisar contrato" | o superusuário abre `/admin/tickets/ticket/?q=Padaria` e `/admin/tickets/ticket/?q=contrato` | cada busca devolve só o atendimento correspondente | T-90 |
| CA-43 | RF-17 | um atendimento em cada status | o superusuário abre `/admin/tickets/ticket/?status__exact=completed` | só o concluído aparece | T-91 |
| CA-44 | RF-17, RN-07 | um atendimento pendente | o superusuário salva no admin com status `completed` | `completed_at` passa a ter valor | T-92 |
| CA-45 | RF-18 | o superusuário `responsavel` criado por `createsuperuser` e dois atendimentos pendentes ("Padaria Bom Dia / Atualizar cardápio do site" e "Studio Lume / Revisar logotipo") | ele acessa `/?status=pending` sem login, entra pelo login com `next`, vê os dois pendentes, troca "Atualizar cardápio do site" para "em andamento" pela lista, confere em `/?status=in_progress`, conclui pela lista com o relógio em 2026-11-03 17:30 UTC e abre `/?status=completed` | ele volta para `/?status=pending` depois do login; o atendimento some dos pendentes depois da primeira troca; aparece em "em andamento"; e em `/?status=completed` aparece só "Atualizar cardápio do site", com "03/11/2026 14:30" na coluna "Concluído em" | T-95 |
| CA-46 | RF-08, RN-08 | o formulário de cadastro | é enviado cliente com 151 caracteres ou assunto com 201 caracteres | o form é inválido e aponta erro no campo correspondente | T-56 |
| CA-47 | RNF-14 | um visitante anônimo | ele faz GET em `/health/` | a resposta é 200 com JSON `{"status": "ok"}` e nenhuma consulta ao banco é feita (`assertNumQueries(0)`) | T-05 |
| CA-48 | RNF-14 | o banco disponível; depois, `ensure_connection` simulado para sempre falhar com `OperationalError` | `call_command('wait_for_db', timeout=1)` é executado | no primeiro caso o comando termina sem erro e escreve "Banco de dados disponível."; no segundo, levanta `CommandError` | T-06 |
| CA-49 | RNF-12 | a imagem construída localmente e um Swarm de um nó em Docker-in-Docker com o `.env` de ensaio | `bash scripts/deploy.sh --skip-build` é executado | `docker service ls` mostra `pytende_traefik`, `pytende_app` e `pytende_db` em 1/1; pelo Traefik, `/login/` responde 200, `/static/css/tokens.css` responde 200 e `http://` responde com redirecionamento para `https://` | Manual (Sprint 11) |
| CA-50 | RNF-12 | um atendimento de teste cadastrado em produção e um backup gerado por `scripts/backup.sh` | o atendimento é excluído pelo admin e o backup é restaurado pelo procedimento da seção 14.8 | o atendimento de teste volta a aparecer na lista | Manual (Sprint 12) |

---

## 12. Estratégia de testes

### 12.1 Princípios

- Runner nativo: `python manage.py test`, contra o PostgreSQL do Docker Compose. Duas formas equivalentes:
  - `docker compose up -d db` e depois `.venv/bin/python manage.py test` (o `.env` local aponta `DATABASE_URL` para `localhost:5432`).
  - `docker compose run --rm app python manage.py test` (a partir da Sprint 2).
- O usuário do PostgreSQL definido em `POSTGRES_USER` é superusuário do container, então o Django consegue criar e apagar o banco `test_pytende`.
- Base `django.test.TestCase` (transação por teste).
- Usuário de teste criado com `User.objects.create_superuser(...)` em `setUpTestData`. Testes de view usam `self.client.force_login(user)`, exceto os testes de autenticação, que usam o formulário de login de verdade.
- Horário controlado com `unittest.mock.patch('django.utils.timezone.now', return_value=datetime(..., tzinfo=datetime.timezone.utc))`.
- Mensagens verificadas com `list(get_messages(response.wsgi_request))` ou seguindo o redirect (`follow=True`).
- Nenhum teste depende de rede externa, de Selenium ou do Google Fonts.

### 12.2 Catálogo de testes

| ID | Arquivo | Classe e método | O que verifica | Sprint |
|---|---|---|---|---|
| T-01 | `core/tests.py` | `SettingsTests.test_locale_and_timezone_settings` | `LANGUAGE_CODE == 'pt-br'`, `TIME_ZONE == 'America/Sao_Paulo'`, `USE_TZ is True`, `USE_I18N is True`, `DATABASES['default']['ENGINE'] == 'django.db.backends.postgresql'` | 1 |
| T-02 | `core/tests.py` | `EnvExampleTests.test_env_example_contains_only_placeholders` | `.env.example` existe; as chaves são exatamente as da seção 14.6; `SECRET_KEY` é `troque-por-uma-chave-gerada`; `POSTGRES_PASSWORD` é `troque-esta-senha`; `TRAEFIK_DASHBOARD_AUTH` está vazio; `DOMAIN` termina em `example.com`; nenhum valor começa com `django-insecure-`. A partir da Sprint 2, também verifica que `.dockerignore` contém a linha `.env`. | 1, 2 |
| T-03 | `core/tests.py` | `TemplateTests.test_base_template_loads_design_tokens` | `render_to_string('base.html')` contém `lang="pt-br"`, `css/tokens.css`, `css/app.css` e a URL do Google Fonts | 4 |
| T-04 | `core/tests.py` | `DesignSystemTests.test_tokens_match_design_system` | `finders.find('css/tokens.css')` e `finders.find('css/app.css')` existem; todo HEX de `tokens.css` aparece em `design_system/design-system.html`; `app.css` não contém nenhum HEX | 4 |
| T-05 | `core/tests.py` | `HealthCheckTests.test_health_returns_ok_without_queries` | CA-47 | 2 |
| T-06 | `base/tests.py` | `WaitForDbTests.test_wait_for_db_succeeds_and_times_out` | CA-48 (`patch('django.db.backends.base.base.BaseDatabaseWrapper.ensure_connection', side_effect=OperationalError)` no segundo caso) | 2 |
| T-10 | `accounts/tests.py` | `AuthTests.test_superuser_created_by_command_can_log_in` | CA-01 (`call_command('createsuperuser', interactive=False, ...)` com `patch.dict(os.environ, {'DJANGO_SUPERUSER_PASSWORD': ...})`) | 5 |
| T-11 | `accounts/tests.py` | `AuthTests.test_public_signup_routes_do_not_exist` | CA-02 | 5 |
| T-12 | `accounts/tests.py` | `AuthTests.test_login_page_renders_fields_in_portuguese` | CA-03 | 5 |
| T-13 | `accounts/tests.py` | `AuthTests.test_anonymous_user_is_redirected_to_login_with_next` | CA-04 e CA-05 (lista na Sprint 5; Novo na 6; Edição na 8; troca de status na 9) | 5, 6, 8, 9 |
| T-14 | `accounts/tests.py` | `AuthTests.test_login_redirects_to_next_url` | CA-06 | 5 |
| T-15 | `accounts/tests.py` | `AuthTests.test_login_without_next_redirects_to_ticket_list` | CA-07 | 5 |
| T-16 | `accounts/tests.py` | `AuthTests.test_login_ignores_external_next_url` | CA-08 | 5 |
| T-17 | `accounts/tests.py` | `AuthTests.test_invalid_credentials_show_generic_error` | CA-09 | 5 |
| T-18 | `accounts/tests.py` | `AuthTests.test_logout_requires_post` | CA-10 | 5 |
| T-19 | `accounts/tests.py` | `AuthTests.test_logout_form_present_on_private_screens` | CA-11 (Lista na Sprint 5; Novo na 6; Edição na 8) | 5, 6, 8 |
| T-20 | `accounts/tests.py` | `AuthTests.test_logout_ends_session` | CA-12 | 5 |
| T-30 | `tickets/tests/test_models.py` | `TicketModelTests.test_new_ticket_starts_pending` | RN-01: `Ticket.objects.create(client=..., subject=...)` tem status `pending` e `completed_at` nulo | 3 |
| T-31 | `tickets/tests/test_models.py` | `TicketModelTests.test_status_choices` | RN-02: `TicketStatus.choices == [('pending', 'Pendente'), ('in_progress', 'Em andamento'), ('completed', 'Concluído')]` | 3 |
| T-32 | `tickets/tests/test_models.py` | `TicketModelTests.test_completing_sets_completed_at` | RN-04 com horário controlado | 3 |
| T-33 | `tickets/tests/test_models.py` | `TicketModelTests.test_reopening_clears_completed_at` | RN-05 para `pending` e para `in_progress` | 3 |
| T-34 | `tickets/tests/test_models.py` | `TicketModelTests.test_resaving_completed_ticket_keeps_completed_at` | RN-06, CA-20 | 3 |
| T-35 | `tickets/tests/test_models.py` | `TicketModelTests.test_all_status_transitions_are_allowed` | RN-03, CA-29 (seis transições com `subTest`) | 3 |
| T-36 | `tickets/tests/test_models.py` | `TicketModelTests.test_change_status_applies_completion_rule` | `change_status()` grava e apaga `completed_at` e atualiza `updated_at` | 3 |
| T-37 | `tickets/tests/test_models.py` | `TicketModelTests.test_default_ordering_newest_first` | RN-09 (inclui empate de `created_at` resolvido por `-id`) | 3 |
| T-38 | `tickets/tests/test_models.py` | `TicketModelTests.test_timestamps_are_managed` | `created_at` fixo, `updated_at` muda ao salvar | 3 |
| T-39 | `tickets/tests/test_models.py` | `TicketModelTests.test_constraint_rejects_inconsistent_completed_at` | `Ticket.objects.filter(pk=...).update(status='completed')` com `completed_at` nulo levanta `IntegrityError` (dentro de `transaction.atomic()`) | 3 |
| T-40 | `tickets/tests/test_models.py` | `TicketModelTests.test_constraint_rejects_unknown_status` | `update(status='archived')` levanta `IntegrityError` | 3 |
| T-41 | `tickets/tests/test_models.py` | `TicketModelTests.test_str` | `str(ticket) == 'Padaria Bom Dia - Atualizar cardápio do site'` | 3 |
| T-50 | `tickets/tests/test_forms.py` | `TicketFormTests.test_create_form_requires_client_and_subject` | Erros "Informe o cliente." e "Informe o assunto." | 6 |
| T-51 | `tickets/tests/test_forms.py` | `TicketFormTests.test_create_form_description_is_optional` | Form válido sem descrição | 6 |
| T-52 | `tickets/tests/test_forms.py` | `TicketFormTests.test_create_form_rejects_blank_spaces` | Cliente e assunto só com espaços são inválidos | 6 |
| T-53 | `tickets/tests/test_forms.py` | `TicketFormTests.test_create_form_has_no_status_field` | `'status' not in TicketCreateForm().fields` | 6 |
| T-54 | `tickets/tests/test_forms.py` | `TicketFormTests.test_update_form_fields_and_status_choices` | Campos `client, subject, description, status`; status inválido rejeitado | 8 |
| T-55 | `tickets/tests/test_forms.py` | `TicketFormTests.test_status_form_rejects_unknown_status` | `TicketStatusForm({'status': 'archived'})` inválido com "Status inválido." | 9 |
| T-56 | `tickets/tests/test_forms.py` | `TicketFormTests.test_fields_respect_max_length` | CA-46 | 6 |
| T-60 | `tickets/tests/test_views_list.py` | `TicketListViewTests.test_list_shows_columns_and_newest_first` | CA-30 | 5 |
| T-61 | `tickets/tests/test_views_list.py` | `TicketListViewTests.test_list_filters_by_status_query_string` | CA-31 | 7 |
| T-62 | `tickets/tests/test_views_list.py` | `TicketListViewTests.test_list_without_or_with_invalid_filter_shows_all` | CA-32 | 7 |
| T-63 | `tickets/tests/test_views_list.py` | `TicketListViewTests.test_list_marks_active_filter` | CA-36 | 7 |
| T-64 | `tickets/tests/test_views_list.py` | `TicketListViewTests.test_list_empty_state_with_create_link` | CA-37 e CA-38 | 7 |
| T-65 | `tickets/tests/test_views_list.py` | `TicketListViewTests.test_completed_filter_shows_completed_at` | CA-39 | 7 |
| T-66 | `tickets/tests/test_views_list.py` | `TicketListViewTests.test_list_dates_use_sao_paulo_timezone` | CA-40 | 5 |
| T-67 | `tickets/tests/test_views_list.py` | `TicketListViewTests.test_screens_have_no_delete_action` | CA-41 (Lista na Sprint 7; Edição acrescentada na 8) | 7, 8 |
| T-70 | `tickets/tests/test_views_form.py` | `TicketCreateViewTests.test_create_page_renders` | GET 200 com os três campos, sem `status`, título "Novo atendimento" | 6 |
| T-71 | `tickets/tests/test_views_form.py` | `TicketCreateViewTests.test_create_valid_ticket_redirects_with_message` | CA-14 | 6 |
| T-72 | `tickets/tests/test_views_form.py` | `TicketCreateViewTests.test_create_ignores_posted_status` | CA-15 | 6 |
| T-73 | `tickets/tests/test_views_form.py` | `TicketCreateViewTests.test_create_invalid_keeps_data_and_shows_errors` | CA-16, incluindo `aria-describedby` no campo com erro | 6 |
| T-74 | `tickets/tests/test_views_form.py` | `TicketUpdateViewTests.test_update_page_prefilled` | GET 200 com valores atuais e bloco de datas | 8 |
| T-75 | `tickets/tests/test_views_form.py` | `TicketUpdateViewTests.test_update_valid_redirects_with_message` | CA-17 | 8 |
| T-76 | `tickets/tests/test_views_form.py` | `TicketUpdateViewTests.test_update_to_completed_sets_completed_at` | CA-18 | 8 |
| T-77 | `tickets/tests/test_views_form.py` | `TicketUpdateViewTests.test_update_reopen_clears_completed_at` | CA-19 | 8 |
| T-78 | `tickets/tests/test_views_form.py` | `TicketUpdateViewTests.test_update_invalid_keeps_data_and_shows_errors` | CA-21 | 8 |
| T-79 | `tickets/tests/test_views_form.py` | `TicketUpdateViewTests.test_update_unknown_ticket_returns_404` | CA-22 | 8 |
| T-80 | `tickets/tests/test_views_status.py` | `TicketStatusUpdateViewTests.test_status_change_updates_and_redirects_to_next` | CA-23 | 9 |
| T-81 | `tickets/tests/test_views_status.py` | `TicketStatusUpdateViewTests.test_status_change_rejects_get` | CA-24 | 9 |
| T-82 | `tickets/tests/test_views_status.py` | `TicketStatusUpdateViewTests.test_status_change_requires_csrf_token` | CA-25 | 9 |
| T-83 | `tickets/tests/test_views_status.py` | `TicketStatusUpdateViewTests.test_status_change_to_completed_sets_date_and_reopen_clears` | CA-26 | 9 |
| T-84 | `tickets/tests/test_views_status.py` | `TicketStatusUpdateViewTests.test_status_change_invalid_value_keeps_status` | CA-27 | 9 |
| T-85 | `tickets/tests/test_views_status.py` | `TicketStatusUpdateViewTests.test_status_change_ignores_external_next` | CA-28 | 9 |
| T-86 | `tickets/tests/test_views_status.py` | `TicketStatusUpdateViewTests.test_status_change_unknown_ticket_returns_404` | POST em pk inexistente devolve 404 | 9 |
| T-87 | `tickets/tests/test_urls.py` | `UrlTests.test_only_expected_routes_exist` | CA-13 | 9 |
| T-90 | `tickets/tests/test_admin.py` | `TicketAdminTests.test_admin_search_by_client_and_subject` | CA-42 | 3 |
| T-91 | `tickets/tests/test_admin.py` | `TicketAdminTests.test_admin_filter_by_status` | CA-43 | 3 |
| T-92 | `tickets/tests/test_admin.py` | `TicketAdminTests.test_admin_save_applies_completion_rule` | CA-44 (POST no formulário de alteração do admin) | 3 |
| T-95 | `tickets/tests/test_journey.py` | `MainJourneyTests.test_main_journey` | CA-45, de ponta a ponta com `django.test.Client`, sem `force_login` | 10 |

### 12.3 Cobertura por camada

| Camada | Testes |
|---|---|
| Settings, configuração e infraestrutura | T-01, T-02, T-03, T-04, T-05, T-06 |
| Models e regras de negócio | T-30 a T-41 |
| Forms | T-50 a T-56 |
| Views de atendimento | T-60 a T-67, T-70 a T-79, T-80 a T-86, T-87 |
| Autenticação | T-10 a T-20 |
| Admin | T-90 a T-92 |
| Jornada principal | T-95 |
| Deploy e backup | CA-49 e CA-50 (manuais) |

### 12.4 Comandos

```bash
docker compose up -d db                              # sobe o PostgreSQL local
.venv/bin/python manage.py test                      # suíte completa
.venv/bin/python manage.py test tickets              # só o app tickets
.venv/bin/python manage.py test tickets.tests.test_models
.venv/bin/python manage.py test --verbosity 2        # lista cada teste
docker compose run --rm app python manage.py test    # mesma suíte dentro do container
```

---

## 13. Sprints

Regras para todas as sprints:

- Ative o `.venv` existente (`source .venv/bin/activate`). Não recrie o `.venv` nem o projeto `core`.
- Mantenha o PostgreSQL local de pé (`docker compose up -d db`) a partir da Sprint 1.
- Toda sprint termina com `python manage.py check` sem problemas e `python manage.py test` passando.
- Só marque `[x]` depois de implementar e verificar.
- Nenhuma tarefa fora do que está descrito aqui.

### Sprint 1 - Fundação de configuração e PostgreSQL local

**Objetivo:** settings lendo o `.env`, localização em pt-br e fuso de São Paulo, PostgreSQL local no Docker Compose, `.env.example`, README inicial e primeiros testes.

**Pré-requisito:** D-01 decidida antes do primeiro `migrate` (recomendação: manter `auth.User`).

- [X] Conferir `.venv/bin/python --version` (`Python 3.13.11`), `.venv/bin/python -m django --version` (`6.1.2`) e `docker compose version` (Docker Compose v2 instalado). Evidência (2026-11-01): Python 3.13.11, Django 6.1.2, Docker Compose v5.6.1 (Docker 29.9.2).
- [X] Instalar no `.venv` `django-environ==0.14.0` e `psycopg[binary]==3.3.6` e acrescentar ao `requirements.txt` as linhas `django-environ==0.14.0` e `psycopg[binary]==3.3.6`, mantendo os pinos existentes e a ordem alfabética. Evidência: `pip install` sem erro, `pip check` sem conflitos; `psycopg-binary 3.3.6` veio como dependência do extra.
- [X] Em `core/settings.py`, importar `environ`, criar `env` e chamar `environ.Env.read_env(BASE_DIR / '.env')`, como na seção 8.14.
- [X] Trocar a `SECRET_KEY` escrita no código por `env('SECRET_KEY')`, sem default. Evidência: sem `.env` e sem variável, o Django levanta `ImproperlyConfigured: Set the SECRET_KEY environment variable`.
- [X] Trocar `DEBUG` e `ALLOWED_HOSTS` por `env(...)` e acrescentar `CSRF_TRUSTED_ORIGINS = env('CSRF_TRUSTED_ORIGINS')`.
- [X] Trocar `DATABASES` (SQLite) por `{'default': env.db('DATABASE_URL')}`, sem default. Evidência: sem `DATABASE_URL`, `ImproperlyConfigured: Set the DATABASE_URL environment variable`; com ela, o engine é `django.db.backends.postgresql`.
- [X] Definir `LANGUAGE_CODE = 'pt-br'` e `TIME_ZONE = 'America/Sao_Paulo'`; manter `USE_I18N = True` e `USE_TZ = True`. Evidência: `/admin/login/` responde 200 com `<html lang="pt-br">`; `timezone.localtime().tzname()` retorna `-03`.
- [X] Reorganizar `INSTALLED_APPS` em `DJANGO_APPS` e `LOCAL_APPS` (vazia por enquanto).
- [X] Criar `docker-compose.yml` só com o serviço `db` da seção 14.3.4. Evidência: `docker compose config --quiet` sem erro.
- [X] Criar `.env.example` com exatamente o conteúdo da seção 14.6. Evidência: as 13 chaves e a ordem são conferidas pelo T-02.
- [X] (Felipe) Atualizar o `.env` local a partir do `.env.example`: gerar uma `SECRET_KEY` nova com `.venv/bin/python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"`, gerar `POSTGRES_PASSWORD` com `openssl rand -hex 24`, montar `DATABASE_URL=postgres://pytende:<senha>@localhost:5432/pytende` e decidir sobre as chaves fora do escopo (D-05). O agente não lê nem imprime o `.env`. Executado pelo agente a pedido do Felipe em 2026-11-01: o `.env` foi regravado a partir do `.env.example` (mesmas 13 chaves, `chmod 600`, valores nunca impressos). Desvios: a `SECRET_KEY` foi gerada com `secrets.token_urlsafe(50)` (a saída de `get_random_secret_key` pode ter `$` e `#`, que o Docker Compose interpreta ao ler o `.env`); a senha com `secrets.token_hex(24)`, equivalente a `openssl rand -hex 24`. Antes disso o agente só conferiu quais chaves tinham valor, sem ler os valores: todas as de segredo (banco, RabbitMQ, Redis, OpenAI, Anthropic, LangSmith, SMTP) estavam vazias, então a D-05 foi resolvida pela opção (a), removendo as chaves fora do escopo sem perder dado. O `.env` antigo foi guardado fora do projeto.
- [X] Rodar `git check-ignore .env` e confirmar a saída `.env`. Evidência: `.gitignore:135:.env	.env`.
- [X] Rodar `docker compose up -d db` e esperar o healthcheck ficar `healthy` (`docker compose ps`). Evidência: `pytende-db-1  Up 5 seconds (healthy)  127.0.0.1:5432->5432/tcp`; volume `pytende_pg_data`.
- [X] Criar `core/tests.py` com T-01 e T-02.
- [X] Rodar `python manage.py migrate` contra o PostgreSQL. Evidência: 18 migrations aplicadas (`contenttypes`, `auth`, `admin`, `sessions`); `showmigrations` sem pendentes e `makemigrations --check --dry-run` sem mudanças. Decisão D-01 assumida seguindo a recomendação (a): `auth.User` nativo.
- [X] Criar `README.md` com: descrição do Pytende, requisitos (Python 3.13.11, Django 6.1.2, Docker com Compose v2), ativação do `.venv`, `pip install -r requirements.txt`, criação do `.env` a partir do `.env.example`, geração da `SECRET_KEY` e da senha do banco, `docker compose up -d db`, `migrate`, `createsuperuser`, `runserver` e `python manage.py test`. Incluir a nota: se a porta 5432 já estiver ocupada por outro PostgreSQL local, pare o outro serviço antes.

**Testes da sprint:** T-01, T-02.

**Definição de pronto:**
- [X] `python manage.py check` sem problemas. Evidência: `System check identified no issues (0 silenced).`
- [X] `python manage.py test` com T-01 e T-02 passando contra PostgreSQL. Evidência: `Ran 2 tests ... OK`, com o banco `test_pytende` criado e destruído no PostgreSQL do Compose.
- [X] `python manage.py runserver` sobe sem erro. Evidência: `GET /admin/login/` responde 200 e o log não mostra erro.
- [X] `core/settings.py` não contém nenhuma chave secreta nem configuração de SQLite. Evidência: `grep -i "django-insecure\|sqlite\|SECRET_KEY = '"` sem ocorrências.
- [X] README descreve como rodar o projeto do zero. Evidência: as afirmações do README foram conferidas (nome do volume, variáveis obrigatórias).

### Sprint 2 - Container da aplicação

**Objetivo:** imagem Docker de produção, entrypoint com espera do banco e migrations, endpoint de healthcheck, WhiteNoise e serviço `app` no Compose.

- [X] Instalar no `.venv` `gunicorn==26.2.0` e `whitenoise==6.12.0` e acrescentá-los ao `requirements.txt`. Evidência: `pip install` sem erro e `pip check` sem conflitos; `requirements.txt` com 7 pinos em ordem alfabética.
- [X] Rodar `python manage.py startapp base`; manter `apps.py`, `migrations/__init__.py`, `models.py` (vazio até a Sprint 3) e `tests.py`; apagar `admin.py` e `views.py`. Evidência: o app tem `__init__.py`, `apps.py`, `migrations/__init__.py`, `models.py` (stub do `startapp`, sem models) e `tests.py`; `admin.py` e `views.py` apagados.
- [X] Acrescentar `'base'` em `LOCAL_APPS`.
- [X] Criar `base/management/__init__.py`, `base/management/commands/__init__.py` e `base/management/commands/wait_for_db.py` (seção 8.13). Evidência: coberto pelo T-06 (sucesso imprime "Banco de dados disponível."; falha levanta `CommandError` "Banco indisponível após 1s"); o entrypoint usa o comando com `--timeout 90`.
- [X] Criar `core/views.py` com `health_check` (seção 8.9) e a rota `health/` em `core/urls.py` (seção 8.8). Evidência: T-05 (200, `{"status": "ok"}`, 0 queries) e `curl` em `/health/` retornando 200.
- [X] Em `core/settings.py`, definir `STATIC_ROOT`, acrescentar o `WhiteNoiseMiddleware` e `STORAGES` (seção 8.14). Evidência: `collectstatic` copiou 130 arquivos; com `DEBUG=False` o WhiteNoise serviu `/static/admin/css/base.css` (200, `text/css`) e, com `Accept-Encoding: gzip`, `Content-Encoding: gzip` (24.538 B para 5.357 B).
- [X] Criar `Dockerfile`, `.dockerignore` e `entrypoint.sh` (seção 14.3); `chmod +x entrypoint.sh`. Evidência: `sh -n entrypoint.sh` OK, permissão `-rwxr-xr-x`; o `CMD` gunicorn foi exercitado em container com `DEBUG=False` (gunicorn 26.2.0, 2 workers, `/health/` 200).
- [X] Acrescentar o serviço `app` ao `docker-compose.yml` (seção 14.3.4). Evidência: `docker compose config --quiet` sem erro; `docker compose up` sobe `app` (`0.0.0.0:8000->8000`) e `db` (healthy).
- [X] Criar T-05 em `core/tests.py` e T-06 em `base/tests.py`; ampliar T-02 com a verificação do `.dockerignore`. Evidência: o T-02 agora também confere a linha `.env` no `.dockerignore`.
- [X] Rodar `docker compose build` e `docker compose up`; conferir `http://localhost:8000/health/` com `{"status": "ok"}` e `http://localhost:8000/admin/` com os estilos do admin carregados. Evidência: imagem `pytende-app` (303 MB); `/health/` retorna `{"status": "ok"}` (200); `/admin/` redireciona (302) para `/admin/login/`, que responde 200 com `lang="pt-br"` e CSS do admin (`base.css`, `login.css`) servidos com 200.
- [X] Rodar `docker compose run --rm app python manage.py test`. Evidência: `Ran 4 tests ... OK` dentro do container (rodado com o `app` parado).
- [X] Atualizar o README com a seção "Rodando com Docker Compose" (`docker compose up`, `docker compose run --rm app python manage.py createsuperuser`, logs, como parar). Evidência: seção criada; também atualizados "Estado atual" e "Testes".

**Testes da sprint:** T-05, T-06, T-02 ampliado.

**Definição de pronto:**
- [X] `docker compose up` sobe `app` e `db` sem erro e o entrypoint mostra "Banco de dados disponível." e o resultado do `migrate`. Evidência: o log do `app` mostra ">>> Aguardando o banco de dados...", "Banco de dados disponível." e "Running migrations: No migrations to apply." (as 18 migrations da Sprint 1 já estavam aplicadas), seguido do `collectstatic` e do servidor.
- [X] `python manage.py test` passando no `.venv` e dentro do container (Sprints 1 e 2). Evidência: `Ran 4 tests ... OK` no `.venv` e `Ran 4 tests ... OK` no container (T-01, T-02, T-05, T-06).

### Sprint 3 - Modelo de domínio e admin

**Objetivo:** model `Ticket` com todas as regras de negócio, migration e admin, com testes.

- [X] Em `base/models.py`, criar `BaseModel` conforme a seção 8.6. Evidência: `BaseModel` abstrata com `created_at`/`updated_at` e `verbose_name` em português.
- [X] Rodar `python manage.py startapp tickets` e acrescentar `'tickets'` em `LOCAL_APPS`. Evidência: `tests.py` de stub e `views.py` removidos (as views entram na Sprint 5).
- [X] Em `tickets/apps.py`, definir `verbose_name = 'Atendimentos'`.
- [X] Em `tickets/models.py`, criar `TicketStatus` e `Ticket` com campos, `Meta`, `ordering`, índices e constraints da seção 8.6.
- [X] Implementar `_sync_completed_at()`, `clean()`, `save()`, `change_status()` e `__str__()` conforme a seção 8.7. Evidência: coberto por T-32 a T-36.
- [X] Rodar `python manage.py makemigrations tickets` e conferir que gera `tickets/migrations/0001_initial.py` com os dois índices e as duas constraints. Evidência: `0001_initial.py` com `tickets_created_idx`, `tickets_status_created_idx`, `tickets_status_valid` e `tickets_completed_at_matches_status`.
- [X] Rodar `python manage.py migrate`. Evidência: `Applying tickets.0001_initial... OK` no PostgreSQL do Compose.
- [X] Criar `TicketAdmin` em `tickets/admin.py` conforme a seção 8.12.
- [X] Trocar `tickets/tests.py` pelo pacote `tickets/tests/` (com `__init__.py`).
- [X] Criar `tickets/tests/test_models.py` com T-30 a T-41. Evidência: 12 testes (T-30 a T-41) passando.
- [X] Criar `tickets/tests/test_admin.py` com T-90 a T-92. Evidência: 3 testes (T-90 a T-92) passando; o T-92 usa POST real no formulário de alteração do admin.
- [X] Atualizar o README com a seção "Admin" (`/admin/`, uso de busca e filtro, exclusão só pelo admin).

**Testes da sprint:** T-30 a T-41, T-90 a T-92.

**Definição de pronto:**
- [X] `python manage.py makemigrations --check --dry-run` não detecta mudanças pendentes. Evidência: `No changes detected`.
- [X] `python manage.py test` passando (Sprints 1 a 3). Evidência: `Ran 19 tests ... OK`.
- [X] Nenhuma view, form ou admin escreve em `completed_at`. Evidência: `completed_at` só aparece no model e em `readonly_fields`/`list_display` do admin (leitura).

### Sprint 4 - Design system e layout base

**Objetivo:** referência visual `design_system/design-system.html`, tokens CSS e templates base. É a primeira sprint de interface.

- [X] Criar `design_system/design-system.html` com o conteúdo listado na seção 9.7, usando só os valores da seção 9. Evidência: arquivo autônomo com as 16 seções na ordem da 9.7 (paleta, tipografia, espaçamentos, raios, sombra e foco, botões com hover e foco, inputs normal/foco/erro, select, badges, filtro, tabela desktop, cards do celular, mensagens, estado vazio, navegação e login), com os tokens e os componentes embutidos. Os quatro tokens de marketing (`display-mega`, `xxl`, `xl`, `lg`) usam as alturas de linha do DESIGN.md da Wise (107.1px, 81.6px, 54.4px e 70.5px).
- [X] Criar `static/css/tokens.css` com as custom properties da seção 9 (cores, fonte, tipografia, espaçamentos, raios, sombras, contêineres), com um comentário no topo dizendo que os valores vêm de `design_system/design-system.html`.
- [X] Criar `static/css/app.css` com os componentes da seção 9.4 e as faixas responsivas da seção 9.5, usando só `var(--...)`, mais a classe `.visually-hidden`. Evidência: nenhum HEX no arquivo (T-04). Decisão: o Django 6.1 já marca o widget com erro com `aria-invalid="true"` e `aria-describedby="<id>_error"`; o `app.css` aplica a borda de erro por `.input--error` e por `[aria-invalid="true"]`, e o `form_field.html` usa o id nativo `<id>_error` na lista de erros. Na barra do celular, as ações quebram linha para caber em 360px.
- [X] Em `core/settings.py`, definir `TEMPLATES[0]['DIRS'] = [BASE_DIR / 'templates']`, `STATICFILES_DIRS = [BASE_DIR / 'static']` e `MESSAGE_TAGS` (seção 8.14).
- [X] Criar `templates/base.html` e `templates/base_auth.html` (seção 8.11).
- [X] Criar `templates/includes/messages.html` e `templates/includes/form_field.html` (seção 8.11). Evidência: sucesso com `role="status"`, erro com `role="alert"` (via `DEFAULT_MESSAGE_LEVELS`).
- [X] Acrescentar T-03 e T-04 em `core/tests.py`.
- [X] Atualizar o README com a seção "Design system" (onde ficam `design-system.html` e `tokens.css` e a regra de não usar valores fora dos tokens).

**Testes da sprint:** T-03, T-04.

**Definição de pronto:**
- [X] `design_system/design-system.html` abre direto no navegador e mostra todos os componentes da seção 9.7. Evidência: aberto via `file://` no Chromium headless em 1280px e 390px; as 16 seções presentes e conferidas por captura.
- [X] `python manage.py findstatic css/tokens.css` encontra o arquivo. Evidência: `Found 'css/tokens.css' here: .../static/css/tokens.css`.
- [X] `python manage.py test` passando (Sprints 1 a 4). Evidência: `Ran 21 tests ... OK`.

### Sprint 5 - Autenticação e lista protegida

**Objetivo:** login, logout e a Lista de atendimentos (sem filtro), acessível só com login.

- [X] Rodar `python manage.py startapp accounts`; manter `apps.py`, `forms.py` (novo), `urls.py` (novo) e `tests.py`; apagar `models.py`, `admin.py`, `views.py` e `migrations/` gerados, porque o app não tem models. Evidência: o app tem só `__init__.py`, `apps.py`, `forms.py`, `urls.py` e `tests.py`; `makemigrations --check` sem mudanças.
- [X] Acrescentar `'accounts'` em `LOCAL_APPS`.
- [X] Criar `LoginForm` em `accounts/forms.py` (seção 8.10).
- [X] Criar `accounts/urls.py` com `login` e `logout` (seção 8.8).
- [X] Definir `LOGIN_URL`, `LOGIN_REDIRECT_URL` e `LOGOUT_REDIRECT_URL` (seção 8.14).
- [X] Criar `TicketListView` em `tickets/views.py`, por enquanto sem filtro (seção 8.9).
- [X] Criar `tickets/urls.py` com `app_name = 'tickets'` e o caminho `''` com nome `list`.
- [X] Atualizar `core/urls.py` com os `include` da seção 8.8.
- [X] Criar `templates/accounts/login.html` (seção 10.1).
- [X] Criar `templates/base_app.html` com a barra de navegação (wordmark e formulário de logout; o botão "Novo atendimento" entra na Sprint 6).
- [X] Criar `templates/tickets/ticket_list.html` com a tabela, as colunas da seção 10.2, os badges de status e o layout de cards no celular (o filtro, o estado vazio e as ações entram nas Sprints 7, 8 e 9; enquanto não há atendimentos, o card fica vazio sem texto).
- [X] Criar `accounts/tests.py` com T-10 a T-20 (T-13 e T-19 cobrindo só a lista nesta sprint). Evidência: 11 testes (T-10 a T-20) passando.
- [X] Criar `tickets/tests/test_views_list.py` com T-60 e T-66.
- [X] Atualizar o README com a seção "Primeiro acesso" (criar o superusuário e entrar em `/login/`).

**Testes da sprint:** T-10 a T-20, T-60, T-66.

**Definição de pronto:**
- [X] Acessar `/` sem login leva a `/login/?next=/`; entrar leva de volta a `/`. Evidência: contra o app do Compose, `GET /` deu 302 para `/login/?next=/`; o POST de login com `next=/` deu 302 para `/`, e o `GET /` seguinte respondeu 200.
- [X] `python manage.py test` passando (Sprints 1 a 5). Evidência: `Ran 34 tests ... OK`.

### Sprint 6 - Novo atendimento

**Objetivo:** Tela 3 funcionando com validação, mensagem e status inicial pendente.

- [X] Criar `TicketCreateForm` em `tickets/forms.py` (seção 8.10).
- [X] Criar `TicketCreateView` (seção 8.9) e o caminho `tickets/new/` com nome `create`.
- [X] Criar `templates/tickets/ticket_form.html` (seção 10.3), usando `includes/form_field.html` para cada campo. Evidência: campos renderizados um a um por `includes/form_field.html`; texto de ajuda "Todo atendimento novo começa como Pendente." só no cadastro.
- [X] Acrescentar o botão primário "Novo atendimento" na barra de `base_app.html`. Evidência: decisão: nas telas de formulário o mesmo botão aparece como terciário (bloco `nav_new_class`), para manter um único botão verde por tela (regra 9.6), já que o CTA ali é "Cadastrar atendimento" ou "Salvar alterações".
- [X] Criar `tickets/tests/test_forms.py` com T-50 a T-53 e T-56.
- [X] Criar `tickets/tests/test_views_form.py` com T-70 a T-73. Evidência: T-73 confere `aria-invalid="true"` e `aria-describedby="id_client_error"`/`"id_subject_error"` apontando para as listas de erro.
- [X] Ampliar T-13 e T-19 para incluir `/tickets/new/`.

**Testes da sprint:** T-50 a T-53, T-56, T-70 a T-73, T-13 e T-19 ampliados.

**Definição de pronto:**
- [X] Cadastrar pelo navegador volta para a lista com a mensagem e o atendimento como "Pendente". Evidência: Chromium headless contra o app do Compose: envio vazio mostrou "Informe o cliente." e "Informe o assunto." junto dos campos; envio válido voltou para `/` com "Atendimento cadastrado com sucesso." e a linha com o badge "Pendente".
- [X] `python manage.py test` passando (Sprints 1 a 6). Evidência: `Ran 43 tests ... OK`.

### Sprint 7 - Filtro por status e estado vazio

**Objetivo:** filtro na query string, filtro ativo marcado e estado vazio com atalho para cadastro.

- [X] Implementar em `TicketListView.get_queryset()` o filtro por `status` e em `get_context_data()` as chaves `current_status` e `status_filters` (seção 8.9). Evidência: valor fora de `TicketStatus.values` é tratado como "Todos". O contexto também traz `current_status_label`, usado no texto do estado vazio.
- [X] Renderizar o filtro em `ticket_list.html` como na seção 9.4, com `aria-current="page"` no item ativo.
- [X] Renderizar os dois textos de estado vazio da seção 10.2, com o botão "Cadastrar atendimento" apontando para `tickets:create`.
- [X] Acrescentar T-61 a T-65 e T-67 em `tickets/tests/test_views_list.py`. Evidência: o T-60 passou a contar os badges (`badge--pending`), porque o rótulo "Pendente" agora também aparece no filtro.

**Testes da sprint:** T-61 a T-65, T-67.

**Definição de pronto:**
- [X] Recarregar `/?status=completed` no navegador mantém o filtro "Concluído" ativo. Evidência: Chromium headless: depois do clique em "Concluído" e do reload, o link ativo (`aria-current="page"`) continua "Concluído" e o estado vazio mostra `Nenhum atendimento com status "Concluído".` com o botão "Cadastrar atendimento".
- [X] `python manage.py test` passando (Sprints 1 a 7). Evidência: `Ran 49 tests ... OK`.

### Sprint 8 - Edição do atendimento

**Objetivo:** Tela 4 com edição de todos os campos e status, aplicando a regra da data de conclusão.

- [X] Criar `TicketUpdateForm` em `tickets/forms.py` (seção 8.10).
- [X] Criar `TicketUpdateView` (seção 8.9) e o caminho `tickets/<int:pk>/edit/` com nome `update`. Evidência: decisão: o bloco de datas usa `saved_dates`, capturado em `get_object()` antes do form, porque num POST com erro o `full_clean()` do ModelForm já aplicou na instância o status enviado (e com ele a regra da data); assim a tela mostra só o que está gravado.
- [X] Ajustar `ticket_form.html` para mostrar o bloco de datas quando houver `object` (seção 10.4).
- [X] Acrescentar o link "Editar" (botão terciário) na coluna Ações de `ticket_list.html`.
- [X] Acrescentar T-54 em `tickets/tests/test_forms.py`.
- [X] Acrescentar T-74 a T-79 em `tickets/tests/test_views_form.py`.
- [X] Ampliar T-13, T-19 e T-67 para incluir `/tickets/<pk>/edit/`.

**Testes da sprint:** T-54, T-74 a T-79, T-13, T-19 e T-67 ampliados.

**Definição de pronto:**
- [X] Concluir pela edição mostra a data na lista; reabrir apaga a data. Evidência: Chromium headless: ao salvar com "Concluído", a lista mostrou o badge "Concluído" e a data 01/11/2026 13:55 em "Concluído em" (e o bloco de datas da edição também); ao voltar para "Pendente", a lista mostrou `—`.
- [X] `python manage.py test` passando (Sprints 1 a 8). Evidência: `Ran 56 tests ... OK`.

### Sprint 9 - Troca de status pela lista

**Objetivo:** troca de status em cada linha da lista por POST com CSRF, mantendo o filtro.

- [X] Criar `TicketStatusForm` em `tickets/forms.py` (seção 8.10).
- [X] Criar `TicketStatusUpdateView` com `http_method_names = ['post']`, validação de `next` e `handle_no_permission()` (seção 8.9), e o caminho `tickets/<int:pk>/status/` com nome `update_status`. Evidência: `handle_no_permission()` usa `redirect_to_login(reverse('tickets:list'))`; `next` validado com `url_has_allowed_host_and_scheme`.
- [X] Acrescentar o formulário de status por linha em `ticket_list.html` (seção 10.2). Evidência: a lista passa `status_choices` no contexto. Ajuste de layout no `app.css` (e na cópia do `design-system.html`): a partir de 1280px "Editar", select e "Atualizar" ficam numa linha, com largura mínima para Cliente e Assunto; de 1024px a 1279px quebram em duas linhas; no tablet ficam empilhados. Medido no Chromium headless com 6 atendimentos (um com assunto longo): a tabela cabe no card em 1440, 1280, 1279, 1024, 1023, 900 e 768px, e em 767px e 360px vira cards.
- [X] Acrescentar T-55 em `tickets/tests/test_forms.py`.
- [X] Criar `tickets/tests/test_views_status.py` com T-80 a T-86.
- [X] Criar `tickets/tests/test_urls.py` com T-87.
- [X] Ampliar T-13 com o POST anônimo em `/tickets/<pk>/status/` (CA-05).

**Testes da sprint:** T-55, T-80 a T-87, T-13 ampliado.

**Definição de pronto:**
- [X] Trocar o status em `/?status=pending` volta para `/?status=pending` com a mensagem. Evidência: Chromium headless: na lista filtrada por Pendente, trocar para "Em andamento" e clicar em "Atualizar" voltou para `/?status=pending`, com o filtro Pendente ativo, a mensagem `Status de "Cadastro pelo navegador" alterado para Em andamento.` e o atendimento fora da lista.
- [X] `python manage.py test` passando (Sprints 1 a 9). Evidência: `Ran 65 tests ... OK`.

### Sprint 10 - Jornada principal, responsividade e segurança de produção

**Objetivo:** teste ponta a ponta da jornada, verificação responsiva e settings de produção prontos para o `check --deploy`.

- [X] Criar `tickets/tests/test_journey.py` com T-95 (CA-45). Evidência: T-95 percorre CA-45 com `createsuperuser`, login real com `next`, duas trocas pela lista e o filtro Concluído com "03/11/2026 14:30".
- [X] Acrescentar em `core/settings.py` o bloco `if not DEBUG:` da seção 8.14. Evidência: decisão: o Django 6.1 acrescentou o check `mail.E001`, que no `check --deploy` trata o backend de console como erro (e faria o `deploy.sh` abortar com `--fail-level ERROR`). Como o Pytende não envia e-mail (seção 7), o bloco de produção silencia só esse check (`SILENCED_SYSTEM_CHECKS = ['mail.E001']`) e o `MAILERS` de console continua.
- [X] Rodar `DEBUG=False SECRET_KEY=<chave-de-50-caracteres-gerada> ALLOWED_HOSTS=pytende.example.com,localhost CSRF_TRUSTED_ORIGINS=https://pytende.example.com SECURE_HSTS_SECONDS=3600 .venv/bin/python manage.py check --deploy` (as variáveis do shell têm prioridade sobre o `.env`) e registrar os avisos. Evidência: antes do ajuste: `mail.E001` (erro) e `security.W021`; depois: `System check identified 1 issue (1 silenced)`, só o `security.W021`.
- [X] Documentar no README a seção "Checagem de produção" com o comando acima e o único aviso aceito: `security.W021` (HSTS sem preload, porque `pycodebr.com.br` não está na lista de preload). Qualquer outro aviso deve ser corrigido.
- [X] Executar a verificação manual de CA-33 em 360px, 768px e 1280px no modo responsivo do navegador e corrigir `app.css` até passar. Evidência: Chromium headless (Playwright) contra o app do Compose, com 7 atendimentos (um com assunto de 200 caracteres): Login, Lista, Novo e Edição em 360px, 768px e 1280px com `scrollWidth` igual à largura da janela e nenhum botão, link, select ou input com menos de 48px de altura; em 360px cada `<tr>` da lista tem `display: block` (cards). Correções no `app.css`: no tablet, o select de status fica com largura mínima e padding lateral menor para não cortar "Em andamento".
- [X] Verificar com o teclado (Tab) que todos os campos, botões e links mostram o anel de foco da seção 9.3. Evidência: Tab percorreu Lista e Edição; todos os elementos focados (wordmark, botões, filtros, selects, inputs e links) tinham o `box-shadow` do `--focus-ring`.

**Testes da sprint:** T-95; verificações manuais CA-33 e CA-34.

**Definição de pronto:**
- [X] `python manage.py test` passando (todas as sprints), no `.venv` e no container. Evidência: `Ran 66 tests ... OK` no `.venv` e `Ran 66 tests ... OK` em `docker compose run --rm app python manage.py test`.
- [X] `check --deploy` só com o aviso aceito.
- [X] CA-33 verificado nas três larguras.

### Sprint 11 - Stack de produção, scripts e ensaio local

**Objetivo:** arquivos de deploy no padrão `scsi_v1` e stack ensaiada num Swarm local de um nó, sem VPS.

**Pré-requisito:** D-02, D-03 e D-07 decididas.

- [X] Criar `docker-stack.yml` com o conteúdo da seção 14.3.5. Evidência: cópia literal da seção 14.3.5.
- [X] Criar `scripts/deploy.sh` (seção 14.3.6), `scripts/post_deploy.sh` (seção 14.3.7), `scripts/generate_env.sh` (seção 14.3.8) e `scripts/backup.sh` (seção 14.8), com permissão de execução. Evidência: pré-requisitos D-02, D-03 e D-07 assumidos pelas recomendações (a), por autorização do Felipe em 2026-11-01 para seguir as recomendações sem perguntar. O `generate_env.sh` não usa arrays associativos, para rodar também no bash 3.2 do macOS no ensaio; ele preserva as chaves existentes (conferido: a `SECRET_KEY` não muda na segunda execução e há backup `.env.bak.*`).
- [X] Rodar `bash -n` em cada script e corrigir erros de sintaxe. Evidência: os quatro scripts passam em `bash -n`; todos com `-rwxr-xr-x`.
- [X] Criar `docs/deploy/swarm.md` com o conteúdo das seções 14.4 a 14.9 (o que ter em mãos, resposta de cada pergunta do `setup_deploy.sh`, verificação, redeploy, backup, restauração e tabela de problemas comuns). Evidência: gerado a partir das seções 14.4 a 14.9 e 14.11, com a tabela dos arquivos de deploy no topo.
- [X] Executar o ensaio da seção 14.11 e registrar o resultado de CA-49. Evidência: CA-49 aprovado num Swarm de um nó em `docker:27-dind`: `pytende_traefik`, `pytende_app` e `pytende_db` em 1/1; `/login/` 200, `/static/css/tokens.css` 200, `http://` 301 para `https://pytende.example.com/`, `/health/` `{"status": "ok"}`, `/` 302 para `/login/?next=/` e header `Strict-Transport-Security: max-age=3600; includeSubDomains`. No mesmo ensaio, `scripts/backup.sh` gerou `db_20261101_170957.sql.gz`, o atendimento de teste foi excluído e voltou após a restauração do procedimento 14.8 (ensaio local do CA-50; o CA-50 de produção continua na Sprint 12). Defeito encontrado e corrigido: dentro da imagem de produção (`DEBUG=False`), 51 dos 66 testes falhavam com 301 por causa do `SECURE_SSL_REDIRECT`; `core/test_runner.py` (`TEST_RUNNER`) desliga só esse redirect durante a suíte. Depois da correção, `Ran 66 tests ... OK` dentro do `pytende_app` da stack e `check --deploy` só com `security.W021`.
- [X] Atualizar o README com as seções "Deploy (Docker Swarm)" e "Backup e restauração", apontando para `docs/deploy/swarm.md`.

**Testes da sprint:** CA-49 (manual); `python manage.py test` continua passando.

**Definição de pronto:**
- [X] No ensaio, os três serviços ficaram 1/1, `/login/` e `/static/css/tokens.css` responderam 200 pelo Traefik e `http://` redirecionou para `https://`.
- [X] `docker stack config -c docker-stack.yml` sem erro com o `.env` de ensaio exportado. Evidência: `stack config OK` dentro do DinD com o `.env` de ensaio exportado pelo mesmo parser literal do `deploy.sh`.
- [X] `python manage.py test` passando. Evidência: `Ran 66 tests ... OK` no `.venv`, no `.venv` com `DEBUG=False` e no container da stack.

### Sprint 12 - Deploy na VPS e backup

**Objetivo:** Pytende publicado em `https://pytende.pycodebr.com.br`, com backup diário e restauração testada.

**Pré-requisito:** D-08 decidida.

- [ ] Fazer commit e push para `origin/main` (com autorização do Felipe).
- [ ] (Felipe) Contratar a VPS (D-02), com Ubuntu 24.04 LTS, nova e dedicada ao Pytende.
- [ ] (Felipe) Criar o token da Cloudflare e o token do GHCR (seção 14.4).
- [ ] (Felipe) Executar o passo a passo da seção 14.5.
- [ ] (Felipe) Criar o superusuário dentro do container `app` (seção 14.5, passo 6).
- [ ] (Felipe) Configurar o cron de backup (seção 14.8).
- [ ] (Felipe) Fazer o teste de restauração (CA-50) e registrar a data no README.
- [ ] (Felipe) Percorrer o checklist pós-deploy (seção 14.9).

**Testes da sprint:** suíte completa dentro do container de produção (`docker exec <container> python manage.py test`); CA-34 no servidor; CA-50; checklist pós-deploy.

**Definição de pronto:**
- [ ] `python manage.py test` passando dentro do container `pytende_app`.
- [ ] Todos os itens da seção 14.9 marcados.
- [ ] Um backup gerado pelo cron existe em `~/backups/` e foi restaurado com sucesso uma vez.

---

## 14. Plano de deploy da rota escolhida

### 14.1 Escolha: Rota B (PostgreSQL + Docker Compose + Docker Swarm com Traefik)

**Decisão:** Rota B, definida pelo Felipe na revisão da versão 1.0 deste PRD.

| Critério | Rota B (escolhida) | Rota A (descartada) |
|---|---|---|
| Escopo | Atende as quatro telas com três serviços (`traefik`, `app`, `db`). A infraestrutura é maior que o escopo exige, mas é a mesma usada nos outros sistemas da PycodeBR. | Atende o escopo com um web app WSGI. |
| Número de usuários | Um usuário. O PostgreSQL sobra para essa carga, mas não limita o crescimento. | Um usuário. O SQLite atende. |
| Custo | VPS Hostinger KVM 1 a partir de R$ 29,99/mês (contrato de 24 meses, consultado em 2026-11-01); domínio já existente na Cloudflare. | US$ 0 ou US$ 10/mês no PythonAnywhere (consultado em 2026-11-01). |
| Complexidade operacional | Maior: VPS, Docker, Swarm, Traefik, certificados, PostgreSQL e backup com `pg_dump`. Fica menor porque o `setup_deploy.sh` público automatiza a preparação da VPS e o primeiro deploy, e o `scripts/deploy.sh` automatiza os seguintes. | Menor: o PythonAnywhere cuida do servidor. |
| Alinhamento com o SCSI | Total: mesma arquitetura, mesmos scripts e o mesmo fluxo de operação do IA Builders. | Parcial: só estrutura de apps e documentação. |

**Justificativa:** a Rota B põe o Pytende no mesmo padrão de operação dos outros sistemas da PycodeBR, reaproveita o `setup_deploy.sh` e o fluxo de deploy já conhecidos, e deixa dev e produção no mesmo banco (PostgreSQL 16). O custo extra de operação é pago uma vez pela automação dos scripts.

**Rota descartada:** Rota A (SQLite, `collectstatic`, PythonAnywhere).

**Quando valeria migrar para a Rota A:**
- O custo da VPS (R$ 59,99/mês na renovação) deixar de se justificar para um sistema de um usuário com pouco uso.
- Ninguém estiver disponível para manter a VPS (atualizações do Ubuntu, Docker, renovação de tokens).
- Caminho: exportar com `docker exec <app> python manage.py dumpdata --natural-foreign --exclude contenttypes --exclude auth.permission > dump.json`, trocar `DATABASE_URL` por `sqlite:////home/<usuario>/pytende/db.sqlite3` (suportado pelo `env.db`), rodar `migrate` e `loaddata dump.json` no PythonAnywhere, e seguir o plano da versão 1.0 deste PRD.

### 14.2 Topologia de produção

| Serviço | Imagem | Redes | Volumes | Réplicas | Recursos (limite / reserva) | Observação |
|---|---|---|---|---|---|---|
| `pytende_traefik` | `traefik:v3.6` | `traefik_public` | `letsencrypt`, `/var/run/docker.sock` (leitura) | 1 (nó manager) | 0.5 CPU, 192M / 0.15 CPU, 64M | Portas 80 e 443; redirect HTTP para HTTPS; Let's Encrypt DNS-01 na Cloudflare; dashboard em `traefik.<DOMAIN>` com Basic Auth |
| `pytende_app` | `ghcr.io/pycodebr/pytende:latest` | `traefik_public`, `pytende_internal` | nenhum | 1 | 1.0 CPU, 512M / 0.25 CPU, 256M | gunicorn com 2 workers; atualização `start-first` com rollback |
| `pytende_db` | `postgres:16` | `pytende_internal` | `pg_data` | 1 | 1.0 CPU, 1024M / 0.25 CPU, 256M | Sem porta publicada |

| Rede | Tipo | Criada por |
|---|---|---|
| `traefik_public` | overlay, attachable, externa | `setup_deploy.sh` (ou `docker network create --driver overlay --attachable traefik_public`) |
| `pytende_internal` | overlay, attachable, `--internal` (sem saída para a internet), externa | `setup_deploy.sh` (ou `docker network create --driver overlay --attachable --internal pytende_internal`) |

| Secret | Uso | Criado por |
|---|---|---|
| `CLOUDFLARE_DNS_API_TOKEN` | Desafio DNS-01 do Let's Encrypt | `setup_deploy.sh` (ou `printf '<TOKEN>' \| docker secret create CLOUDFLARE_DNS_API_TOKEN -`) |

### 14.3 Arquivos de deploy

#### 14.3.1 `Dockerfile` (Sprint 2)

```dockerfile
FROM python:3.13-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN chmod +x entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["./entrypoint.sh"]
CMD ["gunicorn", "core.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "2", "--timeout", "60", "--access-logfile", "-", "--error-logfile", "-"]
```

`psycopg[binary]` traz a `libpq` embutida, então a imagem não precisa de `build-essential` nem `libpq-dev`.

#### 14.3.2 `.dockerignore` (Sprint 2)

```
.git
.gitignore
.venv
env/
*.pyc
__pycache__/
db.sqlite3
db.sqlite3-journal
.env
media/
staticfiles/
.DS_Store
*.log
```

#### 14.3.3 `entrypoint.sh` (Sprint 2)

Mesmo fluxo do `scsi_v1`:

```sh
#!/bin/sh
set -e

echo ">>> Aguardando o banco de dados..."
python manage.py wait_for_db --timeout 90

echo ">>> Aplicando migrations (advisory lock para mais de uma réplica)..."
python <<'PY'
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.core.management import call_command
from django.db import connection

with connection.cursor() as cursor:
    cursor.execute('SELECT pg_advisory_lock(1)')
    try:
        call_command('migrate', '--noinput')
    finally:
        cursor.execute('SELECT pg_advisory_unlock(1)')
PY

echo ">>> Coletando arquivos estáticos..."
python manage.py collectstatic --noinput --clear

exec "$@"
```

O lock evita que duas réplicas migrem ao mesmo tempo durante uma atualização `start-first`.

#### 14.3.4 `docker-compose.yml` (desenvolvimento; `db` na Sprint 1, `app` na Sprint 2)

```yaml
services:
  app:
    build: .
    command: python manage.py runserver 0.0.0.0:8000
    env_file: .env
    environment:
      DATABASE_URL: postgres://${POSTGRES_USER}:${POSTGRES_PASSWORD}@db:5432/${POSTGRES_DB}
    volumes:
      - .:/app
    ports:
      - '8000:8000'
    depends_on:
      db:
        condition: service_healthy

  db:
    image: postgres:16
    environment:
      POSTGRES_DB: ${POSTGRES_DB}
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - pg_data:/var/lib/postgresql/data
    ports:
      - '127.0.0.1:5432:5432'
    healthcheck:
      test: ['CMD-SHELL', 'pg_isready -U ${POSTGRES_USER} -d ${POSTGRES_DB}']
      interval: 5s
      timeout: 5s
      retries: 5

volumes:
  pg_data:
```

O `environment` do `app` troca o host do banco para `db` dentro do Compose; o `.env` local continua com `localhost` para o `.venv`. A porta do banco só escuta em `127.0.0.1`.

#### 14.3.5 `docker-stack.yml` (Sprint 11)

```yaml
version: "3.9"

services:
  traefik:
    image: traefik:v3.6
    command:
      - "--api.dashboard=true"
      - "--api.insecure=false"
      - "--providers.swarm=true"
      - "--providers.swarm.endpoint=unix:///var/run/docker.sock"
      - "--providers.swarm.exposedByDefault=false"
      - "--providers.swarm.network=traefik_public"
      - "--entrypoints.web.address=:80"
      - "--entrypoints.web.http.redirections.entrypoint.to=websecure"
      - "--entrypoints.web.http.redirections.entrypoint.scheme=https"
      - "--entrypoints.websecure.address=:443"
      - "--certificatesresolvers.letsencrypt.acme.email=${ACME_EMAIL}"
      - "--certificatesresolvers.letsencrypt.acme.storage=/letsencrypt/acme.json"
      - "--certificatesresolvers.letsencrypt.acme.dnschallenge=true"
      - "--certificatesresolvers.letsencrypt.acme.dnschallenge.provider=cloudflare"
      - "--certificatesresolvers.letsencrypt.acme.dnschallenge.delaybeforecheck=10"
      - "--certificatesresolvers.letsencrypt.acme.dnschallenge.resolvers=1.1.1.1:53,8.8.8.8:53"
      - "--entrypoints.websecure.http.tls.certresolver=letsencrypt"
      - "--entrypoints.websecure.http.tls.domains[0].main=${DOMAIN}"
      - "--entrypoints.websecure.http.tls.domains[0].sans=*.${DOMAIN}"
      - "--log.level=INFO"
      - "--accesslog=true"
      - "--accesslog.format=json"
    environment:
      CF_DNS_API_TOKEN_FILE: /run/secrets/CLOUDFLARE_DNS_API_TOKEN
    secrets:
      - CLOUDFLARE_DNS_API_TOKEN
    ports:
      - { target: 80, published: 80, protocol: tcp, mode: ingress }
      - { target: 443, published: 443, protocol: tcp, mode: ingress }
    volumes:
      - letsencrypt:/letsencrypt
      - /var/run/docker.sock:/var/run/docker.sock:ro
    networks:
      - traefik_public
    deploy:
      replicas: 1
      placement:
        constraints:
          - node.role == manager
      restart_policy:
        condition: any
        delay: 10s
      labels:
        - "traefik.enable=true"
        - "traefik.http.routers.pytende-traefik.rule=Host(`traefik.${DOMAIN}`)"
        - "traefik.http.routers.pytende-traefik.entrypoints=websecure"
        - "traefik.http.routers.pytende-traefik.tls.certresolver=letsencrypt"
        - "traefik.http.routers.pytende-traefik.service=api@internal"
        - "traefik.http.routers.pytende-traefik.middlewares=pytende-traefik-auth"
        - "traefik.http.middlewares.pytende-traefik-auth.basicauth.users=${TRAEFIK_DASHBOARD_AUTH}"
        - "traefik.http.services.pytende-traefik.loadbalancer.server.port=8080"
      resources:
        limits: { cpus: "0.5", memory: 192M }
        reservations: { cpus: "0.15", memory: 64M }

  app:
    image: ghcr.io/pycodebr/pytende:latest
    env_file: .env
    networks:
      - traefik_public
      - pytende_internal
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8000/health/', timeout=5)"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 180s
    deploy:
      replicas: 1
      update_config:
        parallelism: 1
        delay: 15s
        order: start-first
        failure_action: rollback
        monitor: 30s
      rollback_config:
        parallelism: 1
        order: stop-first
      restart_policy:
        condition: any
        delay: 10s
      labels:
        - "traefik.enable=true"
        - "traefik.http.routers.pytende.rule=Host(`${DOMAIN}`)"
        - "traefik.http.routers.pytende.entrypoints=websecure"
        - "traefik.http.routers.pytende.tls=true"
        - "traefik.http.routers.pytende.tls.certresolver=letsencrypt"
        - "traefik.http.services.pytende.loadbalancer.server.port=8000"
        - "traefik.http.services.pytende.loadbalancer.healthcheck.path=/health/"
        - "traefik.http.services.pytende.loadbalancer.healthcheck.interval=15s"
        - "traefik.http.services.pytende.loadbalancer.healthcheck.hostname=${DOMAIN}"
        - "traefik.http.middlewares.pytende-ratelimit.ratelimit.average=100"
        - "traefik.http.middlewares.pytende-ratelimit.ratelimit.burst=50"
        - "traefik.http.routers.pytende.middlewares=pytende-ratelimit"
      resources:
        limits: { cpus: "1.0", memory: 512M }
        reservations: { cpus: "0.25", memory: 256M }

  db:
    image: postgres:16
    env_file: .env
    volumes:
      - pg_data:/var/lib/postgresql/data
    networks:
      - pytende_internal
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U $${POSTGRES_USER} -d $${POSTGRES_DB}"]
      interval: 10s
      timeout: 5s
      retries: 5
      start_period: 30s
    deploy:
      replicas: 1
      restart_policy:
        condition: any
        delay: 5s
      resources:
        limits: { cpus: "1.0", memory: 1024M }
        reservations: { cpus: "0.25", memory: 256M }

networks:
  traefik_public:
    external: true
  pytende_internal:
    external: true

volumes:
  pg_data:
  letsencrypt:

secrets:
  CLOUDFLARE_DNS_API_TOKEN:
    external: true
```

Diferenças conscientes em relação ao `scsi_v1`:
- `restart_policy: any` em vez de `on-failure`. O Swarm encerra um container doente com SIGTERM, o PostgreSQL sai com código 0, e `on-failure` não agendaria a troca.
- Redes do projeto `external: true` (L-07).
- Sem os IPs da Cloudflare em `forwardedHeaders.trustedIPs`, porque os registros DNS ficam sem proxy (L-09). Se o proxy for ligado no futuro, copie a lista do `docker-stack.yml` do `scsi_v1`.
- Sem métricas Prometheus, sem Celery, RabbitMQ e Redis.

#### 14.3.6 `scripts/deploy.sh` (Sprint 11)

Adaptação direta do `scripts/deploy.sh` do `scsi_v1`, executado na VPS como usuário `deploy`. Mudanças:

| Item | Valor no Pytende |
|---|---|
| Variáveis do topo | `REGISTRY="ghcr.io/pycodebr"`, `IMAGE="$REGISTRY/pytende"`, `STACK_NAME="pytende"`, `STACK_FILE="docker-stack.yml"`; a URL final é `https://${DOMAIN}`, lida do `.env` |
| Carga do `.env` | O mesmo parser seguro do `scsi_v1` (lê `KEY=VALUE` literalmente, sem `source`) |
| Validações que abortam | Swarm ativo; secret `CLOUDFLARE_DNS_API_TOKEN` existe; redes `traefik_public` e `pytende_internal` existem; variáveis obrigatórias não vazias: `SECRET_KEY`, `DATABASE_URL`, `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `DOMAIN`, `ACME_EMAIL`, `TRAEFIK_DASHBOARD_AUTH`; `DEBUG=False`; `ALLOWED_HOSTS` contém `${DOMAIN}` e `localhost` |
| Build e push | `git pull` da branch atual; `docker build -t "$IMAGE:$VERSION" -t "$IMAGE:latest" .` com `VERSION` = hash curto do commit; push das duas tags (com o mesmo fallback de login por `GITHUB_TOKEN` do `scsi_v1`, usuário `pycodebr`) |
| Validação dentro da imagem (antes do deploy) | `docker run --rm --env-file .env --entrypoint python "$IMAGE:$VERSION" manage.py check --deploy --fail-level ERROR`; se falhar, aborta sem tocar na stack |
| Deploy | `docker stack deploy -c "$STACK_FILE" --with-registry-auth "$STACK_NAME"` |
| Rollout forçado | Só `pytende_app` (`docker service update --force pytende_app`) |
| Opção `--skip-build` | Igual ao `scsi_v1`: pula `git pull`, build, push e a validação na imagem; só reconcilia a stack e força o rollout |
| Saída final | `docker service ls` filtrado por `pytende_`, versão, imagem, URL e o comando de `createsuperuser` |

#### 14.3.7 `scripts/post_deploy.sh` (Sprint 11)

Hook opcional do `setup_deploy.sh` que substitui o `seed_demo`. Comportamento:

1. Espera até 120 segundos o container `pytende_app` aparecer (`docker ps --filter name=pytende_app -q`).
2. Roda dentro dele `python manage.py check --deploy` e `python manage.py showmigrations --plan`, e falha se alguma linha tiver `[ ]` (migration pendente).
3. Faz `curl -fsS https://${DOMAIN}/health/` (com `DOMAIN` lido do `.env` pelo mesmo parser seguro) e falha se a resposta não tiver `"status": "ok"`.
4. Imprime o comando para criar o superusuário (passo 6 da seção 14.5). Não cria usuário sozinho.
5. Termina com código 0 se tudo passou e 1 caso contrário.

#### 14.3.8 `scripts/generate_env.sh` (Sprint 11)

Hook opcional do `setup_deploy.sh` ("gerar guiado"). Comportamento:

1. Arquivo de saída: `${ENV_FILE:-.env}`. Se já existir, copia para `.env.bak.<AAAAMMDDHHMMSS>` e **preserva** o valor atual de toda chave que já tem valor (principalmente `SECRET_KEY` e `POSTGRES_PASSWORD`, que não podem mudar depois que o banco existe).
2. Lê as respostas de `/dev/tty` quando ele pode ser aberto (`(exec </dev/tty) 2>/dev/null`); senão, do stdin (usado no ensaio).
3. Pergunta só `DOMAIN` (padrão `pytende.pycodebr.com.br`) e `ACME_EMAIL`.
4. Gera: `SECRET_KEY` com `python3 -c "import secrets; print(secrets.token_urlsafe(50))"`; `POSTGRES_PASSWORD` com `openssl rand -hex 24`.
5. Escreve as chaves da tabela 14.6 com os valores de produção: `DEBUG=False`, `ALLOWED_HOSTS=${DOMAIN},localhost`, `CSRF_TRUSTED_ORIGINS=https://${DOMAIN}`, `POSTGRES_DB=pytende`, `POSTGRES_USER=pytende`, `DATABASE_URL=postgres://pytende:${POSTGRES_PASSWORD}@db:5432/pytende`, `SECURE_SSL_REDIRECT=True`, `SECURE_HSTS_SECONDS=3600` e `TRAEFIK_DASHBOARD_AUTH` vazio (o `setup_deploy.sh` preenche).
6. Aplica `chmod 600` e não imprime nenhum segredo, só a lista de chaves gravadas.

### 14.4 Pré-requisitos (o que ter em mãos)

| Item | Detalhe |
|---|---|
| VPS | Ubuntu 24.04 LTS, nova, dedicada, com acesso root por SSH e as portas 80 e 443 livres (D-02). Nunca rodar o setup numa VPS que já sirva Nginx ou outra stack. |
| Domínio | `pytende.pycodebr.com.br` (D-03), na zona `pycodebr.com.br`, que já usa a Cloudflare |
| Registros DNS na Cloudflare | `A pytende -> <IP_DA_VPS>` e `A *.pytende -> <IP_DA_VPS>`, os dois **sem proxy** ("DNS only") (L-09) |
| Token da Cloudflare | Token de API restrito à zona `pycodebr.com.br` com as permissões `Zone:Zone:Read` e `Zone:DNS:Edit` (usado pelo Traefik no DNS-01) |
| Token do GHCR | Token clássico do GitHub com o escopo `write:packages` (e `read:packages`) para a organização `pycodebr` (D-07) |
| Acesso ao repositório | O `setup_deploy.sh` gera uma chave SSH na VPS; adicionar a chave pública como deploy key **só de leitura** em `pycodebr/pytende` (D-08) |
| Basic Auth do dashboard | Usuário e senha escolhidos na hora; o script gera o hash |

### 14.5 Passo a passo

Comandos para executar no futuro, na Sprint 12.

1. **Local:** confirmar `python manage.py test` passando, ensaio da Sprint 11 aprovado e push do `main` para `origin`.
2. **DNS:** na Cloudflare, criar os dois registros A da seção 14.4.
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
   | Token da Cloudflare | o token da seção 14.4 |
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
8. **Checklist pós-deploy:** seção 14.9.

**Redeploy** (depois de cada push no `main`), na VPS como `deploy`:

```bash
cd ~/pytende
bash scripts/backup.sh                 # backup antes de atualizar
bash scripts/deploy.sh                 # pull, build, push, validação, deploy, rollout
```

Se um rollout falhar e o Swarm voltar para a versão anterior, corrija a causa, rode `bash scripts/deploy.sh --skip-build` para reler o `.env` e confira as variáveis com `docker service inspect --format '{{range .Spec.TaskTemplate.ContainerSpec.Env}}{{println .}}{{end}}' pytende_app`.

### 14.6 Variáveis de ambiente

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

### 14.7 Problemas comuns

| Sintoma | Causa provável | Correção |
|---|---|---|
| `pytende_app` em 0/1 e `400 DisallowedHost` no log | `localhost` ou o domínio faltando em `ALLOWED_HOSTS` | Corrigir o `.env` e rodar `bash scripts/deploy.sh --skip-build` |
| Loop de redirecionamento HTTPS | `SECURE_PROXY_SSL_HEADER` ausente | Conferir o bloco de produção da seção 8.14 |
| 403 CSRF em todos os POSTs | `CSRF_TRUSTED_ORIGINS` sem `https://<DOMAIN>` | Corrigir o `.env` e reimplantar |
| Certificado não é emitido | Token da Cloudflare sem permissão na zona ou DNS sem propagar | `docker service logs pytende_traefik`; conferir permissões e `dig` |
| Healthcheck derruba o app no primeiro deploy | Migrations demorando mais que o `start_period` | Aumentar `start_period` para 600s |
| Redes `pytende_pytende_internal` duplicadas | Rede declarada sem `external: true` | Usar o `docker-stack.yml` da seção 14.3.5 |
| `app` não acha o banco | `DATABASE_URL` com host `localhost` em produção | Usar host `db` |

### 14.8 Backup

| Item | Definição |
|---|---|
| O que | Banco `pytende` (único dado de negócio; não há uploads). O `.env` da VPS é copiado à parte, uma vez, para um cofre de senhas. |
| Como | `pg_dump --clean --if-exists --no-owner` executado dentro do container `pytende_db`, compactado com `gzip` |
| Frequência | Diária às 03:00 (fuso da VPS: `America/Sao_Paulo`) pelo cron do usuário `deploy`; e manual antes de cada redeploy |
| Onde fica | `/home/deploy/backups/db_AAAAMMDD_HHMMSS.sql.gz`, com retenção de 30 dias |
| Cópia fora da VPS | Semanal, manual: `scp deploy@<IP_DA_VPS>:~/backups/db_*.sql.gz ~/Backups/pytende/` no Mac do Felipe (D-11) |
| Teste de restauração | Uma vez na Sprint 12 (CA-50) e depois a cada três meses |

Conteúdo de `scripts/backup.sh` (Sprint 11):

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

### 14.9 Checklist pós-deploy

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

### 14.10 Custos estimados

| Item | Valor | Fonte e data |
|---|---|---|
| VPS Hostinger KVM 1 (1 vCPU, 4 GB RAM, 50 GB NVMe, 4 TB de tráfego) | R$ 29,99/mês no contrato de 24 meses (R$ 719,76 no total); renovação a R$ 59,99/mês | `https://www.hostinger.com/br/servidor-vps`, consultado em 2026-11-01 (preço promocional) |
| VPS Hostinger KVM 2 (2 vCPU, 8 GB RAM, 100 GB NVMe), alternativa | R$ 42,99/mês no contrato de 24 meses (R$ 1.031,76); renovação a R$ 77,99/mês | mesma fonte e data |
| Domínio | Sem custo adicional: subdomínio de `pycodebr.com.br`, que já existe | Zona conferida por `dig NS` em 2026-11-01 |
| Cloudflare (DNS e token de API) | Estimativa: sem custo no plano Free | Não consultado nesta data; a confirmar |
| GHCR (imagem privada da organização) | Estimativa: dentro da cota gratuita do GitHub Packages para uma imagem pequena | Não consultado nesta data; a confirmar |
| Let's Encrypt | Sem custo | Serviço gratuito por definição do projeto Let's Encrypt |

Consumo estimado na KVM 1: limites somados dos três serviços de 2,5 CPU e 1,7 GB de RAM (reservas de 0,65 CPU e 576 MB), dentro dos 4 GB da máquina.

### 14.11 Ensaio local da stack (Sprint 11)

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

---

## 15. Decisões pendentes

| ID | Contexto | Opções | Recomendação | Quem decide | Prazo |
|---|---|---|---|---|---|
| D-01 | Ainda não houve `migrate`. A documentação do Django recomenda definir um modelo de usuário customizado antes do primeiro `migrate`, porque trocar depois é trabalhoso. O escopo tem um único usuário criado por `createsuperuser`. | (a) Usar `auth.User` nativo. (b) Criar `accounts.User(AbstractUser)` sem campos extras e `AUTH_USER_MODEL = 'accounts.User'`. | (a): o escopo não pede nada além do `auth.User`, e multiusuário está fora desta versão. | Felipe | Antes da Sprint 1. Assumida a opção (a) em 2026-11-01, ao executar a Sprint 1; o `migrate` local já foi aplicado com `auth.User` nativo (banco de desenvolvimento descartável: `docker compose down -v` recria do zero se Felipe preferir a opção (b)). |
| D-02 | Tamanho e provedor da VPS. Os três serviços cabem em 4 GB de RAM. | (a) Hostinger KVM 1 (1 vCPU, 4 GB). (b) Hostinger KVM 2 (2 vCPU, 8 GB). (c) Outro provedor. | (a): sobra memória para o Pytende; se um dia a VPS receber o monitoramento opcional, subir para (b). | Felipe | Antes da Sprint 11 |
| D-03 | Domínio público e proxy da Cloudflare (L-09). | (a) `pytende.pycodebr.com.br` com registros sem proxy. (b) `pytende.pycodebr.com.br` com proxy, e o dashboard do Traefik em `traefik-pytende.pycodebr.com.br` (um nível só). (c) Domínio próprio novo. | (a): sem custo, sem limitação de certificado na borda e igual ao fluxo do `setup_deploy.sh`. | Felipe | Antes da Sprint 11 |
| D-04 | `django-environ 0.14.0` e `whitenoise 6.12.0` não declaram suporte ao Django 6.1 nos classifiers (L-03). | (a) Usar as duas versões (padrão do SCSI). (b) Trocar `django-environ` por `python-dotenv` + `os.environ`; servir estáticos pelo Traefik com um container Nginx. | (a), validado por `check` e pelos testes nas Sprints 1 e 2. Se falhar, (b) só para a biblioteca que falhou. | Agente executor, com aviso ao Felipe se precisar trocar | Sprints 1 e 2 |
| D-05 | O `.env` atual tem chaves de PostgreSQL (agora usadas) e chaves fora do escopo (RabbitMQ, Celery/Redis, OpenAI, Anthropic, LangSmith, SMTP), possivelmente com chaves de API reais. | (a) Remover as chaves fora do escopo do `.env` do Pytende. (b) Manter, ignoradas pelo settings. | (a): reduz a superfície de vazamento e deixa o `.env` igual ao `.env.example`. Se as chaves forem reais e usadas em outros projetos, guardá-las no lugar de origem. | Felipe | Sprint 1. Resolvida com a opção (a) em 2026-11-01: as chaves fora do escopo estavam todas vazias e foram removidas do `.env`. |
| D-06 | A `SECRET_KEY` do `startproject` está no histórico do Git (commit `5ba6d4b`). | (a) Só trocar a chave (Sprint 1) e nunca usá-la em produção. (b) Reescrever o histórico para apagá-la. | (a): a chave só valeu para desenvolvimento; reescrever histórico exige force-push. | Felipe | Sprint 1 |
| D-07 | Registro da imagem. O `setup_deploy.sh` exige um registry. | (a) GHCR privado em `ghcr.io/pycodebr/pytende`, com token `write:packages`. (b) GHCR público. | (a): mantém a imagem privada, como o código. | Felipe | Antes da Sprint 11 |
| D-08 | Acesso da VPS ao repositório privado `pycodebr/pytende`. | (a) Deploy key SSH só de leitura, gerada pelo `setup_deploy.sh`. (b) Token pessoal do GitHub na VPS. | (a): acesso restrito a um repositório e sem token pessoal no servidor. | Felipe | Antes da Sprint 12 |
| D-09 | A lista não tem paginação (fora desta versão). Com muitos atendimentos, a página fica pesada. | (a) Manter sem paginação. (b) Planejar paginação numa versão futura. | (a) nesta versão; reavaliar se a lista passar de cerca de 500 atendimentos. | Felipe | Depois do uso real |
| D-10 | A Wise não define cor para um status intermediário. O PRD usa `accent-cyan` (`#38c8ff`) no badge "Em andamento". | (a) `#38c8ff` com texto `#0e0f0c`. (b) `#e8ebe6` com borda 1px `#0e0f0c`. | (a): diferencia bem os três status sem usar o verde da marca. | Felipe | Sprint 4 |
| D-11 | Cópia do backup fora da VPS. | (a) Manual e semanal por `scp` para o Mac. (b) Automática e criptografada para um storage externo (exige nova ferramenta e credencial). (c) Snapshots do provedor da VPS (disponibilidade e preço não consultados). | (a) nesta versão; reavaliar (b) se o Pytende passar a guardar dados que não podem ser perdidos nem por uma semana. | Felipe | Sprint 12 |

---

## 16. Matriz de rastreabilidade

| Requisito / Regra | Critérios de aceite | Testes | Sprint |
|---|---|---|---|
| RF-01 | CA-01, CA-02 | T-10, T-11 | 5 |
| RF-02 | CA-03 | T-12 | 5 |
| RF-03 | CA-10, CA-11, CA-12 | T-18, T-19, T-20 | 5, 6, 8 |
| RF-04 | CA-04, CA-05 | T-13 | 5, 6, 8, 9 |
| RF-05 | CA-06, CA-07, CA-08 | T-14, T-15, T-16 | 5 |
| RF-06 | CA-09 | T-17 | 5 |
| RF-07 | CA-02, CA-13 | T-11, T-87 | 5, 9 |
| RF-08 | CA-14, CA-16, CA-46 | T-50, T-51, T-52, T-56, T-70, T-71, T-73 | 6 |
| RF-09 | CA-14 | T-71 | 6 |
| RF-10 | CA-17, CA-18, CA-19, CA-21, CA-22 | T-54, T-74, T-75, T-76, T-77, T-78, T-79 | 8 |
| RF-11 | CA-23, CA-24, CA-25, CA-26, CA-28 | T-80, T-81, T-82, T-83, T-85, T-86 | 9 |
| RF-12 | CA-09, CA-16, CA-21 | T-17, T-73, T-78 | 5, 6, 8 |
| RF-13 | CA-30 | T-60 | 5 |
| RF-14 | CA-31, CA-32, CA-36 | T-61, T-62, T-63 | 7 |
| RF-15 | CA-39 | T-65 | 7 |
| RF-16 | CA-37, CA-38 | T-64 | 7 |
| RF-17 | CA-42, CA-43, CA-44 | T-90, T-91, T-92 | 3 |
| RF-18 | CA-45 | T-95 | 10 |
| RN-01 | CA-14, CA-15 | T-30, T-53, T-72 | 3, 6 |
| RN-02 | CA-27 | T-31, T-40, T-54, T-55, T-84 | 3, 8, 9 |
| RN-03 | CA-29 | T-35 | 3 |
| RN-04 | CA-18, CA-26, CA-44 | T-32, T-36, T-76, T-83, T-92 | 3, 8, 9 |
| RN-05 | CA-19, CA-26 | T-33, T-36, T-77, T-83 | 3, 8, 9 |
| RN-06 | CA-20 | T-34 | 3 |
| RN-07 | CA-18, CA-19, CA-26, CA-44 | T-39, T-76, T-77, T-83, T-92 | 3, 8, 9 |
| RN-08 | CA-16, CA-46 | T-50, T-51, T-52, T-56 | 6 |
| RN-09 | CA-30 | T-37, T-60 | 3, 5 |
| RN-10 | CA-13, CA-41 | T-67, T-87 | 7, 8, 9 |
| RN-11 | CA-24, CA-25 | T-81, T-82 | 9 |
| RN-12 | CA-39, CA-40 | T-01, T-65, T-66 | 1, 5, 7 |
| RNF-01 | CA-33 | Manual | 4, 10 |
| RNF-02 | | T-03, T-04 | 4 |
| RNF-03 | CA-04, CA-05, CA-13 | T-13, T-87 | 5 a 9 |
| RNF-04 | CA-16, CA-21, CA-27, CA-46 | T-39, T-40, T-50 a T-56 | 3, 6, 8, 9 |
| RNF-05 | | T-01, T-30 a T-41 | 1, 3 |
| RNF-06 | | Suíte completa | 1 a 12 |
| RNF-07 | CA-35 | T-02 | 1, 2 |
| RNF-08 | CA-34 | Manual (`check --deploy`) | 10, 12 |
| RNF-09 | | Revisão na definição de pronto | 1 a 12 |
| RNF-10 | | Tarefas de README | 1, 2, 3, 4, 5, 10, 11, 12 |
| RNF-11 | CA-16, CA-36 | T-63, T-73; revisão manual | 4, 7, 10 |
| RNF-12 | CA-49, CA-50 | Manual (ensaio e restauração); checklist 14.9 | 11, 12 |
| RNF-13 | | Revisão do `requirements.txt` | 1, 2 |
| RNF-14 | CA-47, CA-48 | T-05, T-06 | 2 |

Contagem para conferência: 18 RFs, 12 RNs e 14 RNFs, todos com pelo menos uma linha acima; 50 critérios de aceite (CA-01 a CA-50); 66 testes automatizados (T-01 a T-06, T-10 a T-20, T-30 a T-41, T-50 a T-56, T-60 a T-67, T-70 a T-79, T-80 a T-87, T-90 a T-92, T-95).
