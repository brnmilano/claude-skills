---
name: workflow
description: Fluxo de desenvolvimento dos projetos da SEDS-SP — cards no Redmine, branch, commit, checagens de qualidade e MR. Usar ao iniciar uma nova task ou preparar um commit/MR.
---

## Projetos que usam esta skill

- Projeto PMAS-Web (https://redmine.verytecnologia.com.br/projects/pmas-web)
- Projeto Auxílio Aluguel (https://redmine.verytecnologia.com.br/projects/auxilio-aluguel)
- Projeto CONSEAS (https://redmine.verytecnologia.com.br/projects/conseas)
- Projeto BB-Agil (https://redmine.verytecnologia.com.br/projects/bb-agil)
- Projeto Intranet SEDS-SP (https://redmine.verytecnologia.com.br/projects/intranet-seds-sp)
- Projeto Monitora (https://redmine.verytecnologia.com.br/projects/monitora)
- Projeto SIGMA (https://redmine.verytecnologia.com.br/projects/sigma)

## Primeira execução (configuração do usuário)

- Os dados do usuário ficam em `~/.claude/workflow.json` (permissão 600), **sem** chaves nem tokens (esses ficam em `redmine.env` e `gitlab.env`). Campos:

  | Campo                 | Origem                                                              |
  | --------------------- | ------------------------------------------------------------------- |
  | `name`                | Perguntado ao usuário                                               |
  | `redmine_profile_url` | Perguntado ao usuário (ex.: `https://redmine.verytecnologia.com.br/users/123`) |
  | `redmine_user_id`     | Extraído do link do Redmine (número depois de `/users/`)            |
  | `gitlab_profile_url`  | Perguntado ao usuário (ex.: `https://gitlab.seds.com.br/fulano`)    |
  | `gitlab_username`     | Extraído do link do GitLab (último trecho do caminho)               |
  | `prints_base_dir`     | Perguntado ao usuário: a pasta onde ficarão as pastas de prints (ex.: `C:\Users\fulano\Desktop` ou `/home/fulano/Prints`) |

- **Quando perguntar**: ao invocar o /workflow, **antes de qualquer outra ação** (inclusive antes do tempo estimado), verificar se o arquivo existe com todos os campos. Se não existir, perguntar **numa única mensagem** o nome, os links dos perfis do Redmine e do GitLab e a pasta onde os prints devem ser salvos. Se faltar só um campo, perguntar apenas ele. **Perguntar uma única vez**: com o arquivo completo, nunca mais perguntar. O comando `/workflow setup` refaz a configuração.
- **Nome**: o nome completo como aparece no Redmine e no GitLab.
- **Links**: se um link não tiver o formato esperado (não for do host `redmine.verytecnologia.com.br` ou `gitlab.seds.com.br`, ou não contiver o id/usuário), explicar o formato e perguntar de novo; não adivinhar.
- **Pasta dos prints**: aceitar caminho do Windows (`C:\...`, convertido com `wslpath -u`) ou do Linux, e gravar já convertido para o formato do Linux/WSL. A pasta informada precisa já existir e **não pode estar dentro de um repositório git** (`git -C <pasta> rev-parse` deve falhar); caso contrário, explicar e perguntar de novo. Se o usuário não souber o caminho, sugerir a Área de Trabalho do Windows, obtida com `wslpath "$(powershell.exe -NoProfile -Command '[Environment]::GetFolderPath("Desktop")' | tr -d '\r')"` (respeita a Área de Trabalho redirecionada para o OneDrive).
- **Validação**: depois de gravar o arquivo, e se `redmine.env` e `gitlab.env` já existirem, conferir pelas APIs que os dados batem com as chaves: `GET /users/current.json` (Redmine) deve devolver o mesmo `id` de `redmine_user_id`, e `GET /user` (GitLab) o mesmo `username` de `gitlab_username`. Se divergir, mostrar o que veio da API e o que foi informado, e perguntar qual está certo; não prosseguir com dados conflitantes. Se as chaves ainda não existirem, gravar o arquivo e validar na primeira vez em que forem criadas.
- **Uso**: `redmine_user_id` é o `assigned_to_id` do card e `gitlab_username` identifica o autor do MR (`assignee`), no lugar de consultar a API a cada vez. O `name` entra nas mensagens ao usuário.

## Ao invocar o /workflow

- **Tempo estimado**: se o usuário não informou o tempo estimado (formato `h:mm`) na própria chamada, pedir essa informação **antes de qualquer outra ação**, inclusive antes das checagens de qualidade.

## Ordem de execução

Ao invocar o /workflow, executar nesta ordem, sem pular etapas:

0. Configuração do usuário (só na primeira execução; ver "Primeira execução").
1. Tempo estimado (pedir se não foi informado).
2. Checagens de qualidade ("Desenvolvimento incremental"), incluindo a suíte completa.
3. Prints das telas ("Prints das telas").
4. Preview do card e OK explícito do usuário ("Card no Redmine").
5. Criação do card pela API.
6. Branch, commit e push ("Após a criação do Card").
7. Abertura do MR no GitLab pela API ("MR (GitLab)").
8. Acompanhamento da pipeline do MR ("Acompanhamento da pipeline"). Se quebrar, avisar o usuário e parar.
9. Aguardar o merge. Com o MR mesclado e a pipeline passando, fechar o card automaticamente ("Fechamento automático do card").

O único OK exigido do usuário é o do preview do card (etapa 4); as demais etapas seguem sem pausa, salvo erro.

## Desenvolvimento incremental

Sempre que o /workflow for chamado, deverá rodar os seguintes comandos, antes de seguir para a próxima, rodando nesta ordem:

1. `npx tsc -b` (typecheck)
2. `npx eslint <arquivos alterados>` (lint)
3. `npx vitest run <arquivo ou escopo alterado>` (teste)
4. `npm run build` (build)´
5. `outras checagens de qualidade específicas do projeto, caso existam`

Rodar a suíte completa (`npx vitest run`, sem escopo) antes de criar o card para pegar efeitos colaterais em outros arquivos.

## Prints das telas

- Prints/screenshots das telas alteradas **só são tirados quando o /workflow é invocado** — nunca durante o desenvolvimento normal, nem ao validar um ajuste de layout fora do /workflow.
- Os prints deverão ser a última etapa da skill /workflow.
- Tirar o print de cada tela alterada pela task depois das checagens da seção "Desenvolvimento incremental", para anexar ao card do Redmine.
- Cada tela é impressa em **3 larguras** (menor, intermediária e maior), que bastam para mostrar a responsividade (largura × altura da janela):

  | Dispositivo (DevTools) | Largura | Altura sugerida | Sufixo do arquivo |
  | ---------------------- | ------- | --------------- | ----------------- |
  | Dispositivo móvel      | 500px   | 900px           | `p`               |
  | Tablet                 | 768px   | 1024px          | `m`               |
  | Laptop G               | 1920px  | 1080px          | `g`               |

- Nome do arquivo: `task-NNNN-<tela>-<sufixo>.png` (ex.: `task-3820-login-m.png`); o sufixo é sempre `p` (pequeno, 500px), `m` (médio, 768px) ou `g` (grande, 1920px).
- Tirar os prints **em sequência** e em segundo plano (capturas em paralelo colidem; cada uma leva cerca de 1 minuto), cada Chrome com `--user-data-dir` próprio.
- Salvar sempre em **uma subpasta por card**: `<prints_base_dir>/Prints - <nome-do-projeto>/<NNNN>/`, onde `prints_base_dir` é a pasta informada pelo usuário e gravada em `~/.claude/workflow.json` (ver "Primeira execução"), `<nome-do-projeto>` é o projeto em que a task foi desenvolvida (ex.: `Prints - Auxilio Aluguel`, `Prints - PMAS-Web`, `Prints - CONSEAS`, `Prints - BB-Agil`, `Prints - Intranet SEDS-SP`, `Prints - Monitora`, `Prints - SIGMA`) e `<NNNN>` é o número do card. Dentro dela ficam só os prints daquele card (3 larguras por tela/estado), com o nome `task-NNNN-<tela>-<sufixo>.png`.
- **Criar a pasta**: o número do card só existe depois que ele é criado, então os prints são tirados numa subpasta provisória chamada literalmente `NNNN` (`<prints_base_dir>/Prints - <nome-do-projeto>/NNNN/`, criada com `mkdir -p` antes do primeiro print, e os arquivos com `task-NNNN-…`). Se já existir uma pasta `NNNN` com prints de outra task ainda sem card, não misturar: pedir ao usuário para resolver antes. Nunca criar a pasta base nem outras pastas além dessas. Esta regra tem precedência sobre a pasta Downloads do `~/.claude/CLAUDE.md`. Nunca salvar dentro do repositório; informar o caminho final na resposta.
- **Depois de criar o card** (passo 6 do "Fluxo de criação"): renomear a pasta `NNNN` para o número real do card e renomear cada arquivo `task-NNNN-…` para `task-<número>-…`, **antes** do upload dos anexos (o `filename` enviado ao Redmine é o nome já renomeado). Informar o caminho final da pasta na resposta.

## Card no Redmine

- Título: frase curta descrevendo os principais aspectos da entrega.
  - Ex: [Frontend] Concluir integração de atualização do Presidente do Conselho e exclusão de dados do conselho
- Descrição: toda seção sempre entra como cabeçalho markdown com **5 `#` antes do nome**,
  nunca em negrito e nunca com outra quantidade de `#`. As seções são, nesta ordem:
  - `##### Escopo da atividade` — checklist (`- [ ]`) dos itens a implementar.
  - `##### Critérios de aceite` — checklist (`- [ ]`) do que valida a entrega como pronta. Último
    item sempre fixo: "Projeto compilando, testes passando e lint sem erros." (não detalhar
    comandos como `tsc -b`/`eslint`/`vitest` aqui).
  - `##### Resultado esperado` — um parágrafo curto.
  - `##### Melhorias aplicadas` (opcional, sem checkbox) — ajustes secundários que não fazem parte do escopo principal.
- **Observações** - Sempre adicionar o #####, é visualmente melhor ao redmine.
- **Criação automática** - O Claude cria o card pela **API REST do Redmine** (`https://redmine.verytecnologia.com.br`), sem navegador (a extensão Claude in Chrome não funciona no WSL). A chave de API fica em `~/.claude/redmine.env` (`REDMINE_API_KEY=...`, permissão 600); ler com `source ~/.claude/redmine.env` e **nunca** exibir, logar ou commitar a chave. Se o arquivo não existir, parar e pedir ao usuário para criá-lo. Campos:

  | Campo                            | Valor                                                                          |
  | -------------------------------- | ------------------------------------------------------------------------------ |
  | Projeto                          | O projeto em que a task foi desenvolvida (ex.: PMAS-Web)                       |
  | Tipo                             | Sempre `Task`                                                                  |
  | Título                           | Conforme as regras acima (com o sufixo `[Frontend]`/`[Backend]`/`[FullStack]`) |
  | Descrição                        | Markdown com as seções `#####` acima, separada por ambiente                    |
  | Situação                         | Sempre `Nova`                                                                  |
  | Prioridade                       | Não alterar (manter o padrão do formulário)                                    |
  | Atribuído para                   | Sempre o próprio usuário (`<< mim >>`, `redmine_user_id` de `~/.claude/workflow.json`) |
  | Início e Data prevista           | Data do dia da criação do card nos dois campos                                 |
  | Tempo estimado                   | O valor informado pelo usuário (ver "Ao invocar o /workflow")                  |
  | % Terminado                      | Sempre `0 %`                                                                   |
  | Privado                          | Nunca marcar; o card é sempre público                                          |
  | Sprint, Planejamento, Tarefa mãe | Deixar em branco                                                               |
  | Arquivos                         | Anexar os prints da seção "Prints das telas" (da subpasta `Prints - <Projeto>/<NNNN>/` do card, via upload da API)   |

- **Fluxo de criação**:
  1. Mostrar um **preview** ao usuário neste formato padrão (não listar Sprint, Planejamento, Tarefa mãe, % Terminado nem Privado):
     - Tabela `Campo | Valor` com **somente** estas linhas, nesta ordem: `Projeto / Tipo / Situação` (ex.: `CONSEAS / Task / Nova`), `Título` (em code), `Início e Data prevista` (`AAAA-MM-DD`), `Tempo estimado` (`h:mm`), `Prioridade / Atribuído` (`Padrão do formulário / << mim >>`) e `Arquivos` (nomes em code).
     - Em seguida, **Descrição** com o texto inteiro em um bloco de código, com as seções `#####`.
     - Fechar informando que o card só é criado após um "OK" ou "pode criar" explícito. Pedido de ajuste no preview não é autorização: reapresentar o preview e aguardar.
  2. Aguardar o OK explícito do usuário. Criar o card é uma ação externa e irreversível; sem OK, não chamar a API de criação.
  3. Resolver os IDs por nome com `GET /projects.json`, `/trackers.json` e `/issue_statuses.json` (header `X-Redmine-API-Key`). O projeto é o `identifier` da lista "Projetos que usam esta skill" (ex.: `pmas-web`).
  4. Para cada print: `POST /uploads.json?filename=<arquivo>.png` com `Content-Type: application/octet-stream` e `--data-binary @<arquivo>`; guardar o `token` retornado.
  5. `POST /issues.json` com `project_id`, `tracker_id` (Task), `status_id` (Nova), `subject`, `description`, `start_date` e `due_date` (`YYYY-MM-DD`, hoje), `estimated_hours` (ex.: `2.0`), `done_ratio: 0`, `is_private: false`, `assigned_to_id` (o `redmine_user_id` de `~/.claude/workflow.json`) e `uploads: [{token, filename, content_type: "image/png"}]`. Não enviar prioridade, sprint, planejamento nem tarefa mãe. Montar o JSON com `python3`/`jq` (nunca concatenar a descrição à mão) para escapar corretamente.
  6. Ler `issue.id` da resposta (NNNN), **renomear a pasta e os arquivos dos prints** (ver "Prints das telas" → "Depois de criar o card") e usá-lo diretamente no nome da branch e nos comandos git. Se a API retornar erro (ex.: campo obrigatório ausente), parar, mostrar o erro e aguardar; não tentar de novo às cegas, para não duplicar o card.
  7. Seguir **sem pausa** para a seção "Após a criação do Card" (branch, commit e push). Informar o número e o link (`.../issues/NNNN`) do card ao usuário junto com o resultado final.
- **Fechamento do card** - Feito pelo Claude em dois casos: (a) **automaticamente**, quando o MR da task for mesclado com a pipeline passando (ver "Fechamento automático do card"), sem pedir OK, pois o /workflow já o autoriza; (b) quando o usuário pedir para fechar o card manualmente, caso em que, antes de executar, mostrar o que será alterado (situação, % terminado, datas se mudarem e o tempo gasto) e aguardar o OK explícito. Equivale a clicar em "Editar" no Redmine e salvar. Mesma chave de API da criação. Valores:

  | Campo         | Valor                                                                                   |
  | ------------- | --------------------------------------------------------------------------------------- |
  | Situação      | `Resolvida` (`status_id` 3)                                                             |
  | % Terminado   | `100 %` (`done_ratio: 100`)                                                             |
  | Tempo gasto   | O mesmo valor do Tempo estimado do card (`estimated_hours`)                             |
  | Comentário    | O mesmo texto do Título do card                                                         |
  | Atividade     | Sempre `Desenvolvimento` (`activity_id` 9)                                              |
  | Responder     | Comentário que cita a descrição com todas as caixinhas marcadas (`- [x]`)                 |
  | Datas         | Só alterar Início/Data prevista se a data real de término for outra                     |

  Passos pela API:
  1. `GET /issues/NNNN.json` para ler `subject`, `estimated_hours` e `description`.
  2. `POST /time_entries.json` com `{"time_entry": {"issue_id": NNNN, "hours": <estimated_hours>, "activity_id": 9, "comments": "<subject>", "spent_on": "AAAA-MM-DD"}}` (`spent_on` = hoje).
  3. `PUT /issues/NNNN.json` com `{"issue": {"status_id": 3, "done_ratio": 100, "notes": "<comentário do botão Responder>"}}`. As caixinhas são marcadas **pelo botão "Responder"**, nunca editando a descrição: o `notes` é a citação da descrição que o botão geraria, com cada `- [ ]` trocado por `- [x]`. Formato do `notes`: a linha `<Nome do autor do card> escreveu:` seguida da descrição inteira com cada linha prefixada por `> ` (linhas em branco viram `> `). A descrição original do card **não é alterada**.
  4. Conferir com `GET /issues/NNNN.json` (situação Resolvida, 100 %, `spent_hours` igual ao estimado, comentário com a citação e todas as caixinhas `- [x]` no histórico do card; descrição original intacta) e informar o resultado. Se algum passo falhar, parar e mostrar o erro; não repetir o `POST /time_entries.json` às cegas, para não duplicar o tempo gasto.
  Os IDs acima valem para o Redmine da Very; em caso de dúvida, conferir em `/issue_statuses.json` e `/enumerations/time_entry_activities.json`.
- **Observações** - Sempre criar o sufixo `[Frontend] | [Backend] | [FullStack]` no título do card de acordo com o que foi desenvolvido na task. Se for apenas Frontend, colocar `[Frontend]` no título do card. Se for apenas Backend, colocar `[Backend]` no título do card. Se for ambos, colocar `[FullStack]` no título do card.
- **Observações** - Sempre separar a descrição do card por ambiente de desenvolvimento. Caso tenha alterações no Frontend e Backend, separar a descrição do card em duas partes, uma para o Frontend e outra para o Backend.

## Branch

- Padrão: `feature/`, `fix/`, `docs/`, `test/`, `build/`, `refactor/`, `chore/`, `ci/` + `task-NNNN-slug`, onde `NNNN` é o número do card no Redmine e `slug` é
  sempre em inglês (mesmo com o card/título em português).
- Criada a partir da branch `develop` atualizado — ou empilhada sobre outra feature branch ainda em aberto, se a nova task depender do trabalho dela (deixar isso explícito para o usuário, incluindo o efeito de squash-merge na branch de origem sobre o diff da nova MR).
- Exemplo: `feature/task-1234-implement-educacao-tab-and-restructure-bloco-4`
- Exemplo: `fix/task-1234-fix-educacao-tab-and-restructure-bloco-4`
- Exemplo: `docs/task-1234-update-educacao-tab-and-restructure-bloco-4`
- Exemplo: `test/task-1234-test-educacao-tab-and-restructure-bloco-4`
- Exemplo: `refactor/task-1234-refactor-educacao-tab-and-restructure-bloco-4`
- Exemplo: `chore/task-1234-chore-educacao-tab-and-restructure-bloco-4`
- Exemplo: `ci/task-1234-ci-educacao-tab-and-restructure-bloco-4`
- **Observações**: O Claude cria a branch automaticamente, depois de criar o card e obter o número dele (ver "Após a criação do Card"), a partir da branch `develop` atualizada.

## Commit

- Padrão: `feature:`, `fix:`, `docs:`, `test:`, `build:`, `refactor:`, `chore:`, `ci:` + mensagem curta descrevendo a mudança mais importante, baseada só no que está staged.
- Sempre em inglês (diferente do card/MR, que ficam em português).
- Exemplo: `feature: implement Educação tab and restructure Bloco 4 into a single tabbed page`
- Exemplo: `fix: fix Educação tab and restructure Bloco 4 into a single tabbed page`
- Exemplo: `docs: update Educação tab and restructure Bloco 4 into a single tabbed page`
- Exemplo: `test: test Educação tab and restructure Bloco 4 into a single tabbed page`
- Exemplo: `build: build Educação tab and restructure Bloco 4 into a single tabbed page`
- Exemplo: `refactor: refactor Educação tab and restructure Bloco 4 into a single tabbed page`
- Exemplo: `chore: chore Educação tab and restructure Bloco 4 into a single tabbed page`
- Exemplo: `ci: ci Educação tab and restructure Bloco 4 into a single tabbed page`
- **Observações**: O Claude faz o commit automaticamente: `git add <arquivos da task>` (sempre arquivo a arquivo, nunca `git add -A`/`git add .`) e `git commit -m "<mensagem>"`, com a mensagem baseada nas alterações feitas.

## Push

- Padrão: `git push --set-upstream origin feature/task-3041-education-tab-and-block4-tabs` + --set-upstream é necessário na primeira vez que a branch é criada, para criar o tracking remoto.
- Exemplo: `git push --set-upstream origin feature/task-1234-implement-educacao-tab-and-restructure-bloco-4`
- **Observações**: O Claude faz o push automaticamente com `git push --set-upstream origin feature/task-NNNN-slug`. Nunca usar `--force`.

## Após a criação do Card

- O Claude cria o card (ver "Criação automática") e já obtém o número dele na página criada; o usuário nunca precisa informá-lo, e esta etapa começa automaticamente logo após a criação do card.
- Com o número do card, o Claude **executa** (não apenas sugere) os comandos para finalizar a task, nesta ordem:
  1. `git stash push -u -m "task-NNNN"` — guardar todas as alterações (inclusive arquivos novos) antes de trocar de branch.
  2. `git checkout develop` — voltar para a branch padrão de desenvolvimento.
  3. `git pull` — atualizar a branch de desenvolvimento.
  4. `git checkout -b feature/task-NNNN-slug` — criar a branch da task, com o prefixo adequado ao que foi desenvolvido.
  5. `git stash pop` — restaurar as alterações na nova branch.
  6. `git status --short` — conferir os arquivos alterados; só entram no commit os arquivos da task.
  7. `git add <arquivos da task>` e `git commit -m "feature: implement Educação tab and restructure Bloco 4 into a single tabbed page"` — commit final, com a mensagem no padrão da seção "Commit".
  8. `git push --set-upstream origin feature/task-NNNN-slug` — enviar para o remoto.
- Se qualquer comando falhar (`pull`, `checkout`, `stash pop` com conflito, hook de commit, push rejeitado), **parar**, mostrar o erro ao usuário e aguardar. Se o `stash pop` conflitar, o stash é mantido pelo Git: informar que as alterações continuam em `git stash list`. Não improvisar com `--force`, `reset --hard`, `stash drop` ou `--no-verify`.
- Com o push concluído, seguir **sem pausa** para a seção "MR (GitLab)". Informar o nome da branch, o hash do commit e o resultado do push junto com o resultado final.

## MR (GitLab)

- **Autenticação**: o Claude usa a **API REST do GitLab** em `https://gitlab.seds.com.br/api/v4`, sem navegador. O token fica em `~/.claude/gitlab.env` (`GITLAB_TOKEN=...`, permissão 600, escopo `api`); ler com `source ~/.claude/gitlab.env` e **nunca** exibir, logar ou commitar o token. Se o arquivo não existir, parar e pedir ao usuário para criá-lo (Preferences > Access Tokens no GitLab). Enviar o token no header `PRIVATE-TOKEN`.
- **Projeto**: derivar o caminho do remoto (`git remote get-url origin`, ex.: `git@gitlab.seds.com.br:dni/pmas/frontend.git` → `dni/pmas/frontend`) e usá-lo URL-encoded como `:id` (`dni%2Fpmas%2Ffrontend`).
- **Criação**: `POST /projects/:id/merge_requests` com:

  | Campo                  | Valor                                                                                   |
  | ---------------------- | --------------------------------------------------------------------------------------- |
  | `source_branch`        | A branch da task (`<prefixo>/task-NNNN-slug`)                                           |
  | `target_branch`        | `develop` (ou a feature branch de origem, se a branch foi empilhada)                    |
  | `title`                | A mesma mensagem do commit principal (em inglês)                                        |
  | `description`          | Em português: link do card (`https://redmine.verytecnologia.com.br/issues/NNNN`) e as seções `Escopo da atividade` e `Resultado esperado` do card |
  | `assignee_id`          | O `id` do `gitlab_username` de `~/.claude/workflow.json` (`GET /users?username=<gitlab_username>`) |
  | `remove_source_branch` | `true`                                                                                  |

  Montar o JSON com `python3`/`jq` (nunca concatenar a descrição à mão). Não ativar `merge_when_pipeline_succeeds` nem `squash` por conta própria: o merge é decisão de quem revisa.
- Ler `iid` e `web_url` da resposta e informar o link do MR ao usuário. Se a API retornar erro (ex.: já existe MR aberto para a branch), parar, mostrar o erro e aguardar; não criar um segundo MR às cegas.
- **O Claude nunca mescla o MR.** O merge é feito pelo usuário ou revisor no GitLab.

## Acompanhamento da pipeline

- Após criar o MR, acompanhar a pipeline em segundo plano, sem bloquear a conversa, consultando a cada 30–60 s: `GET /projects/:id/merge_requests/:iid` (campos `head_pipeline.status`, `head_pipeline.id` e `state`). Se ainda não houver pipeline, aguardar até 2 minutos antes de avisar que ela não iniciou.
- Estados: `created`, `pending`, `running` → continuar acompanhando; `success` → seguir para o merge; `failed` → tratar a falha (abaixo); `canceled` ou `skipped` → avisar o usuário e perguntar como proceder.
- **Quando a pipeline quebrar**, parar e avisar o usuário **antes de qualquer tentativa de correção**, mostrando de forma específica:
  1. Quais jobs falharam e em qual stage: `GET /projects/:id/pipelines/:pid/jobs?scope[]=failed`.
  2. O erro de cada um: `GET /projects/:id/jobs/:job_id/trace`, mostrando só o trecho relevante (as últimas linhas e a mensagem de erro, sem despejar o log inteiro). Nunca exibir segredos que apareçam no log.
  3. Como resolver: a causa provável e a correção sugerida (arquivo, linha e mudança), reproduzindo localmente o comando que falhou (ex.: `npx eslint`, `npx vitest run <arquivo>`, `npm run build`) quando possível.
  4. Se for falha de infraestrutura (runner indisponível, timeout, erro de rede), dizer isso e sugerir retentar o job em vez de alterar código.
- Corrigir só depois do aval do usuário. Aprovada a correção, seguir o padrão de commit e push da mesma branch (novo commit, nunca `--force`) e voltar a acompanhar a nova pipeline.
- Se o MR for fechado sem merge (`state: closed`), parar e avisar; **não** fechar o card.

## Fechamento automático do card

- Continuar acompanhando o MR até `state: merged`. Se o usuário encerrar a sessão antes, o fechamento fica pendente e pode ser feito depois com o pedido manual.
- Com `state: merged` **e** a última pipeline do MR em `success`, fechar o card **sem pedir OK**, com os mesmos valores e passos de "Fechamento do card": Situação `Resolvida`, `% Terminado` 100, tempo gasto igual ao estimado, comentário igual ao título do card, atividade `Desenvolvimento` e citação da descrição com as caixinhas marcadas (`- [x]`). `spent_on` é a data do merge.
- Se o MR foi mesclado mas a pipeline não estiver em `success`, **não** fechar o card: avisar o usuário e aguardar instruções.
- Ao final, informar o número do card, o link do MR, o link do card e o resultado da conferência (`GET /issues/NNNN.json`). Se algum passo falhar, aplicar as regras de erro do "Fechamento do card" (parar, mostrar o erro, não repetir o `POST /time_entries.json`).

## Usuários específicos

- O usuário `bruno_milano`, possui alias que abreviam os comandos do git, sendo eles:
  - gcb = git checkout -b
  - gst = git status --short
  - ga = git add
  - gcm = git commit -m
  - gpl = git pull
  - gps = git push
  - gco = git checkout
  - gd = git diff

- O Claude executa sempre os comandos completos do git. Os alias só valem quando for preciso mostrar um comando para o usuário `bruno_milano` rodar por conta própria (ex.: ao pedir que ele resolva um conflito).
