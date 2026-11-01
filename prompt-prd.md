<context>
Você vai escrever o PRD do **Pytende**, um sistema de controle de atendimentos feito com Python e Django.

Problema que o sistema resolve: uma pessoa recebe pedidos de trabalho de clientes e perde o controle do que já fez e do que ainda falta fazer. O Pytende registra cada pedido como um atendimento e mostra a situação de cada um.

O projeto já existe neste diretório. Antes de escrever qualquer coisa, confira o estado real dele. No momento em que este prompt foi escrito, o repositório tinha:
- `.venv/` com Python 3.13.11;
- `requirements.txt` com `Django==6.1.2`, `asgiref` e `sqlparse`;
- projeto Django `core/` (settings, urls, asgi, wsgi) e `manage.py`;
- `.env` presente e listado no `.gitignore`;
- nenhum app de domínio, nenhum `README.md`, nenhum `.env.example` e nenhuma pasta `design_system/`.

Fontes obrigatórias:
1. O código e os arquivos reais deste repositório.
2. O repositório de referência https://github.com/pycodebr/scsi, branch `main`.
3. O design system Wise: https://getdesign.md/design-md/wise/DESIGN.md e https://getdesign.md/design-md/wise/preview
4. `design_system/design-system.html`, se existir.
</context>

<role>
Você atua como arquiteto de software e product manager sênior, especialista em Django e em Spec-Driven Development. Você escreve PRDs que um agente de IA ou um dev júnior consegue executar sprint por sprint sem precisar adivinhar nada.
</role>

<objective>
Gere o arquivo `PRD.md` na raiz do projeto. Ele DEVE conter requisitos, arquitetura, critérios de aceite verificáveis, sprints pequenas com checklists `- [ ]`, o plano de deploy de UMA rota escolhida e a lista de decisões pendentes.

CRITICAL: esta tarefa é só de documentação. Você NÃO DEVE implementar a aplicação, criar apps, models, views, templates, migrations, testes ou qualquer outro arquivo além do `PRD.md`.
</objective>

<non_negotiable_rules>
1. Você DEVE inspecionar o ambiente antes de escrever: rode `.venv/bin/python --version`, leia `requirements.txt`, `core/settings.py` e `.gitignore`, e liste a árvore do projeto. O PRD DEVE refletir as versões instaladas de fato e NÃO DEVE propor recriar o projeto `core` nem o `.venv`.
2. Você DEVE confirmar que a versão do Django instalada é compatível com a versão do Python. Se não for, registre o conflito em "Decisões pendentes" e não troque a versão por conta própria.
3. Você DEVE analisar o repositório SCSI (branch `main`) como referência de estrutura de pastas, organização de apps, padrões de código, README, `.env.example`, testes e deploy. Se não conseguir acessá-lo, você DEVE declarar isso logo no início do PRD, em uma seção "Limitações da análise", e marcar como suposição tudo o que dependeria dele. NÃO DEVE fingir que leu o repositório.
4. Do SCSI você DEVE aproveitar só padrões de estrutura, documentação e deploy. Você NÃO DEVE copiar regras de negócio de seguros, entidades, telas ou funcionalidades do SCSI.
5. Você NÃO DEVE adicionar funcionalidades que não estão em `<functional_requirements>`. Toda ideia extra vai, no máximo, para "Fora desta versão" ou "Decisões pendentes", nunca para uma sprint.
6. Você DEVE ler o DESIGN.md da Wise e usá-lo como design system obrigatório: cores em HEX, tipografia, espaçamentos, raios, sombras e componentes. Se `design_system/design-system.html` não existir, o PRD DEVE incluir uma tarefa na primeira sprint de interface para criar esse arquivo a partir do DESIGN.md da Wise. Se não conseguir acessar as URLs da Wise, declare isso em "Limitações da análise".
7. Você DEVE escolher exatamente UMA rota de deploy (A ou B). Justifique com critérios explícitos (escopo, número de usuários, custo, complexidade operacional e alinhamento com o SCSI), registre a rota descartada e diga em que situação valeria migrar para ela. O plano de deploy DEVE cobrir só a rota escolhida.
8. Todo critério de aceite DEVE ser testável e escrito no formato **Dado / Quando / Então**. Critério vago ("funciona bem", "é intuitivo") é proibido.
9. Toda regra de negócio DEVE apontar para pelo menos um teste automatizado com o runner do Django (`python manage.py test`) dentro de alguma sprint.
10. Cada sprint DEVE ser pequena (entregável em uma sessão de trabalho), ter objetivo próprio, checklist `- [ ]` com tarefas atômicas e uma "Definição de pronto" que inclua os testes passando.
11. Nomes de código (apps, models, campos, URLs, views, templates) DEVEM estar em inglês e seguir a PEP 8. Os textos que o usuário vê DEVEM estar em português brasileiro.
12. Escreva o PRD em português brasileiro, em Markdown, sem emojis.
</non_negotiable_rules>

<tech_specs>
Todas as especificações abaixo são obrigatórias:
- Versões compatíveis de Python e Django, conferidas no ambiente antes de tudo.
- Ambiente virtual `.venv` e `requirements.txt` na raiz do projeto.
- Projeto Django principal `core`, com os domínios separados em apps.
- Código em inglês, PEP 8 e recursos nativos do Django.
- Interface em português brasileiro (`LANGUAGE_CODE = "pt-br"`) e `TIME_ZONE = "America/Sao_Paulo"`, com `USE_TZ = True`.
- Autenticação e permissões com os recursos nativos do Django (`django.contrib.auth`, `LoginView`, `LogoutView`, `LoginRequiredMixin` ou equivalente).
- Campos `created_at` e `updated_at` em todos os modelos de negócio.
- Segredos em `.env`, ignorado pelo Git. O `.env.example` só pode ter placeholders.
- Testes automatizados das regras principais com o runner do Django.
- `README.md` com instruções de execução e configuração, sempre atualizado. Toda sprint que mudar algo de execução ou configuração DEVE ter uma tarefa para atualizar o README.
- Referência visual em `design_system/design-system.html`, construído a partir do design system Wise.
- Deploy, escolha exatamente uma rota:
  - **Rota A (primeira publicação):** SQLite, arquivos estáticos com `collectstatic`, `SECRET_KEY`, `DEBUG` e `ALLOWED_HOSTS` lidos de variáveis de ambiente, publicação em hospedagem Python gerenciada (PythonAnywhere).
  - **Rota B (arquitetura do IA Builders):** PostgreSQL, Docker Compose no desenvolvimento e Docker Swarm com Traefik em produção, como no SCSI.
- Multi-tenant, Celery/RabbitMQ e agentes de IA ficam fora desta versão.
</tech_specs>

<functional_requirements>
<user>
- Um único responsável usa o sistema. A conta dele é criada com `python manage.py createsuperuser`. Não existe cadastro público.
</user>

<access>
- O responsável entra com usuário e senha e pode sair (logout) de qualquer tela.
- Sem login, nenhuma página de atendimentos abre: o sistema redireciona para a tela de login. Depois de entrar, ele volta para a página que tinha pedido (parâmetro `next`).
- Usuário ou senha errados mostram uma mensagem de erro que não diz qual dos dois está incorreto.
</access>

<screens>
Exatamente quatro telas:
1. Login.
2. Lista de atendimentos, que é a tela inicial depois do login.
3. Novo atendimento.
4. Edição do atendimento.
</screens>

<create>
- O responsável cadastra um atendimento com cliente, assunto e descrição. Cliente e assunto são obrigatórios; a descrição é opcional.
- O cliente é um campo de texto (nome da pessoa ou da empresa). Não existe cadastro separado de clientes.
- Todo atendimento novo começa com status "pendente".
- Depois de salvar, o sistema volta para a lista e mostra uma mensagem de confirmação (framework `messages` do Django).
</create>

<edit_and_status>
- O responsável edita cliente, assunto, descrição e status de um atendimento.
- Os status são "pendente", "em andamento" e "concluído". A troca é livre, em qualquer ordem, inclusive para reabrir um atendimento concluído.
- O status também pode ser alterado direto na lista, sem abrir a edição. Essa alteração DEVE usar POST com proteção CSRF.
- Quando o status passa para "concluído", o sistema grava a data e a hora da conclusão. Quando um atendimento concluído é reaberto, essa data é apagada. Essa regra DEVE valer tanto na edição quanto na troca pela lista, e o PRD DEVE dizer em que camada ela fica (por exemplo, no model) para não haver duplicação.
- Um formulário com erro mostra a mensagem junto do campo e mantém o que já foi digitado.
</edit_and_status>

<list_and_filter>
- A lista mostra cliente, assunto, status e data de abertura, do mais recente para o mais antigo.
- O filtro por status tem as opções "todos", "pendente", "em andamento" e "concluído". O filtro fica na URL (query string, por exemplo `?status=pending`), então recarregar a página não perde a seleção.
- Atendimentos concluídos continuam salvos e aparecem no filtro "concluído", com a data de conclusão.
- Quando o filtro escolhido não tem atendimentos, a lista mostra um aviso de lista vazia e um atalho para cadastrar um novo.
</list_and_filter>

<admin>
- O admin do Django lista os atendimentos, com busca por cliente e assunto e filtro por status, para consultas e correções.
</admin>

<main_journey>
O responsável entra, vê os pendentes, muda um atendimento para "em andamento", conclui quando termina o trabalho, filtra os concluídos e encontra esse atendimento com a data de conclusão.

Essa jornada DEVE virar um critério de aceite ponta a ponta e um teste automatizado.
</main_journey>

<out_of_scope>
Nada desta lista pode aparecer em sprint, model, tela ou rota:
- Vários usuários, perfis de acesso e cadastro público de contas.
- Cadastro separado de clientes, histórico de contatos e área do cliente.
- Exclusão de atendimentos pela interface. Se precisar excluir, o responsável usa o admin.
- Mensagens e notificações por e-mail ou WhatsApp, pagamentos, anexos, prazos, prioridades, relatórios, gráficos, API e assistente de IA.
- Multi-tenant, Celery/RabbitMQ e agentes de IA.
</out_of_scope>
</functional_requirements>

<non_functional_requirements>
- Interface responsiva (celular, tablet e desktop), seguindo o design system Wise.
- Validação de dados e controle de acesso em todas as páginas privadas.
- Persistência dos dados e testes das regras de negócio.
- Plano de deploy com variáveis de ambiente, custos estimados e rotina de backup.
- Segurança mínima de produção: `DEBUG=False`, `ALLOWED_HOSTS` restrito, cookies seguros sob HTTPS e checagem com `python manage.py check --deploy`.
</non_functional_requirements>

<execution_steps>
Siga esta ordem:
1. **Diagnóstico do ambiente:** inspecione o repositório e registre versões, arquivos existentes e lacunas.
2. **Análise do SCSI:** leia estrutura, README, `.env.example`, testes e deploy. Anote o que vai ser adaptado e o que vai ser descartado por ser específico de seguros.
3. **Análise do design system Wise:** extraia os tokens (cores HEX, tipografia, espaçamentos, raios, sombras) e os componentes que as quatro telas precisam (botões, inputs, badges de status, tabela ou lista, mensagens, estado vazio).
4. **Escolha da rota de deploy:** decida entre A e B usando os critérios da regra 7.
5. **Redação do PRD:** escreva o `PRD.md` seguindo `<prd_structure>`.
6. **Autoverificação:** revise o PRD contra `<self_check>` e corrija o que falhar antes de entregar.
</execution_steps>

<prd_structure>
O `PRD.md` DEVE ter estas seções, nesta ordem:
1. **Visão geral:** problema, objetivo, público e escopo resumido.
2. **Limitações da análise:** o que não deu para acessar e quais suposições foram feitas. Se não houver nenhuma, escreva "Nenhuma".
3. **Referências analisadas:** SCSI (o que foi adaptado e o que foi descartado), Wise e estado atual do repositório.
4. **Requisitos funcionais:** numerados (RF-01, RF-02, ...), cobrindo tudo de `<functional_requirements>`.
5. **Requisitos não funcionais:** numerados (RNF-01, ...).
6. **Regras de negócio:** numeradas (RN-01, ...), incluindo status inicial, troca livre de status, data de conclusão e apagamento ao reabrir.
7. **Fora desta versão.**
8. **Arquitetura:** stack com versões, estrutura de pastas, apps de domínio, model `Ticket` (ou o nome escolhido) com campos, tipos, `choices`, `ordering` e índices, mapa de URLs, views, forms, templates, settings por ambiente e onde fica a regra da data de conclusão.
9. **Design system:** tokens da Wise em HEX, componentes, comportamento responsivo e o papel do arquivo `design_system/design-system.html`.
10. **Telas:** para cada uma das quatro telas, os elementos, os estados (vazio, erro, sucesso) e a navegação.
11. **Critérios de aceite:** formato Dado / Quando / Então, ligados aos RFs e RNs, incluindo a jornada principal ponta a ponta.
12. **Estratégia de testes:** o que é testado em models, forms, views, autenticação e jornada principal, e o comando para rodar.
13. **Sprints:** cada sprint com objetivo, checklist `- [ ]`, testes da sprint e definição de pronto. Comece pela fundação (settings, `.env`, `.env.example`, README) e termine com o deploy.
14. **Plano de deploy da rota escolhida:** justificativa da escolha, rota descartada e gatilho para migrar, passo a passo, variáveis de ambiente (nome, finalidade, exemplo com placeholder), custos estimados com a data da consulta, backup (frequência, onde fica, como restaurar) e checklist pós-deploy.
15. **Decisões pendentes:** cada item com contexto, opções, recomendação e quem decide.
16. **Matriz de rastreabilidade:** tabela RF/RN → critério de aceite → teste → sprint.
</prd_structure>

<quality_bar>
- Um agente de IA consegue executar qualquer sprint lendo só o PRD, sem inventar nada.
- Todos os requisitos de `<functional_requirements>` aparecem no PRD, e a matriz de rastreabilidade prova isso.
- Versões, caminhos e nomes de arquivo batem com o repositório real.
- As sprints são incrementais: cada uma deixa o sistema rodando e com os testes passando.
- O design system aparece com valores concretos (HEX, px ou rem, nomes de fonte), não com adjetivos.
- Custos de deploy vêm com fonte e data da consulta, ou marcados como estimativa a confirmar.
</quality_bar>

<self_check>
Antes de entregar, confirme cada item. Se algum falhar, corrija o PRD:
- [ ] Nenhum arquivo além do `PRD.md` foi criado ou alterado.
- [ ] Versões de Python e Django conferidas no ambiente e citadas no PRD.
- [ ] Acesso ao SCSI e à Wise confirmado, ou a limitação declarada.
- [ ] Nenhuma regra, entidade ou tela de seguros veio do SCSI.
- [ ] Nenhuma funcionalidade fora do escopo entrou em sprint.
- [ ] Exatamente quatro telas especificadas.
- [ ] Regra da data de conclusão (gravar ao concluir, apagar ao reabrir) coberta na edição e na lista, com teste.
- [ ] Filtro por status persistido na URL, com teste.
- [ ] Redirecionamento para o login com `next` e mensagem genérica de erro, com teste.
- [ ] Todo critério de aceite em Dado / Quando / Então.
- [ ] Toda sprint com checklist `- [ ]` e definição de pronto.
- [ ] Uma única rota de deploy, justificada, com variáveis, custos e backup.
- [ ] `.env.example` previsto só com placeholders e `.env` mantido fora do Git.
</self_check>

<forbidden_output_patterns>
- Implementar código, criar apps ou rodar migrations.
- Requisitos genéricos que serviriam para qualquer sistema.
- Critérios de aceite subjetivos ou impossíveis de testar.
- Sprints grandes ou com tarefas do tipo "implementar o sistema".
- Funcionalidades extras: dashboard, gráficos, prioridades, prazos, notificações, API, exclusão pela interface, multiusuário, cadastro de clientes.
- Copiar regras de negócio, nomes de entidades ou textos do SCSI.
- Plano de deploy para as duas rotas.
- Inventar versões, preços ou conteúdo de repositório que você não verificou.
- Segredos reais no PRD ou em exemplos de `.env.example`.
- Emojis e texto de preenchimento.
</forbidden_output_patterns>

<final_response>
Depois de salvar o `PRD.md`, responda em português com:
1. O caminho do arquivo gerado.
2. A rota de deploy escolhida e o motivo, em uma frase.
3. As limitações de acesso encontradas (SCSI, Wise) ou "nenhuma".
4. O número de sprints e as decisões pendentes mais importantes.
</final_response>
