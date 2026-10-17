---
name: task-status
description: Use quando o usuário chamar /task-status ou pedir a tabela de resumo/status dos cards e MRs ("status dos cards", "como estão os MRs", "próxima tarefa da fila"), e AUTOMATICAMENTE a cada passo concluído de uma task e antes de qualquer pergunta de aprovação (criar card, abrir/aceitar MR, aprovar plano). Mostra o card em andamento, seu MR e a pipeline com ícones coloridos e, depois, a próxima tarefa da fila; ao fim da task, a visão completa do dia.
---

# task-status

Visão rápida (só leitura) do que está em andamento: cards do Redmine, MRs do GitLab, status das pipelines e a próxima tarefa da fila. Para relatório diário/semanal/mensal use `/work-resume`; esta skill não gera HTML.

## Passos

0. **Identidade (primeira execução nesta máquina)**: rode `python3 -I ~/.claude/skills/task-status/scripts/collect.py --whoami`. A fonte é `~/.claude/workflow.json`, o mesmo arquivo que a skill `/workflow` já grava (campos `name`, `redmine_user_id`, `gitlab_username`); nunca peça de novo o que já existe lá.
   - `found: true`: **confirme com o usuário** ("Você é <name> (Redmine <id>, GitLab <usuário>)?", via AskUserQuestion com Sim/Não). Sim: siga. Não: pergunte o usuário do Redmine (link do perfil, `.../users/NNN`) e do GitLab (link do perfil, último trecho é o usuário), e grave em `workflow.json` sem apagar os outros campos.
   - `found: false`: pergunte numa única mensagem o link do perfil do Redmine e o do GitLab (e o nome, se faltar), extraia `redmine_user_id` e `gitlab_username`, grave em `~/.claude/workflow.json` (permissão 600) e valide pelas APIs (`GET /users/current.json` e `GET /user`). Se a chave do Redmine/GitLab não existir (`~/.claude/redmine.env`, `~/.claude/gitlab.env`), avise e peça ao usuário para criá-las.
   - Confirmar só na primeira vez em cada máquina: depois da confirmação, grave `"task_status_confirmed": true` em `workflow.json` e nas próximas chamadas pule esta etapa (o `--whoami` devolve esse campo).
1. **Coletar**: `python3 -I ~/.claude/skills/task-status/scripts/collect.py` (imprime JSON). Usa `~/.claude/workflow.json`, `~/.claude/redmine.env` e `~/.claude/gitlab.env` (nunca exibir chaves). O Redmine é acessado com `--resolve` pelo IP quando o DNS falha (VPN ligada); o GitLab exige a VPN ligada. Se um dos dois não responder, avisar qual e mostrar só o que veio.
2. **Montar a tabela só do card em andamento** (campo `current` do JSON: o card aberto mais recente, com o seu MR). Nada de cards já resolvidos nem de MRs já mesclados. Sempre em tabela, com URL completa, sem texto de anexos na coluna Status:

   | ID | Link | Status |
   |---|---|---|
   | #NNNN | https://redmine.verytecnologia.com.br/issues/NNNN | ícone + situação |
   | !N | https://gitlab.seds.com.br/dni/auxilio-aluguel/-/merge_requests/N | ícone + pipeline · ícone + merge |

   ID à esquerda (só `#NNNN`/`!N`, sem link) e Link com a URL completa. O card em foco é o da branch atual (`task-NNNN`) ou o passado com `--card NNNN`; antes do MR existir, mostrar só a linha do card.

   Só duas linhas. Se `pending_merge` não for vazio, acrescentar uma única linha de texto depois da tabela: "Outros cards aguardando merge: #A, #B" (sem tabela e sem links). Sem `current`, dizer que não há card em andamento.
3. **Pular uma linha** e trazer **a próxima tarefa da fila** em tabela (`Campo | Valor`: Card (URL completa), Título, Situação, Telas/escopo resumido, Atenção/dependências). A fila é o campo `next` do JSON (menor id de card `Nova` atribuído ao usuário, com título iniciado por `[Frontend]`, `[Backend]` ou `[FullStack]`, sem MR). Se `next` for nulo, dizer apenas que não há card seu livre na fila. **Mostrar só o que é do usuário**: nunca listar cards de outras pessoas. Cite se há observação pendente (ex.: atualizar dependência) vinda da memória. Terminar perguntando se quer começar pelo `/plano`.

## Visão completa do dia (`--day`)

Mostrar **sempre que uma task terminar** (card fechado após o merge, ou quando o usuário pedir `/task-status completo`), depois da visão curta. Rode `python3 -I ~/.claude/skills/task-status/scripts/collect.py --day` e use o campo `day` (todos os cards do usuário no projeto da pasta atual, criados ou fechados hoje, com MR, pipeline, horas estimadas e lançadas). Projeto desconhecido: pergunte o id ou use `--project <id>`. Tabela:

| ID | Link | Status | Estimado | Lançado |
|---|---|---|---|---|
| #NNNN | https://redmine.verytecnologia.com.br/issues/NNNN | ícones aprovados | h | h |
| !N | https://gitlab.seds.com.br/dni/auxilio-aluguel/-/merge_requests/N | ícones aprovados | | |

Uma linha para o card e outra logo abaixo para o seu MR. A coluna **ID** vem primeiro (só `#NNNN` ou `!N`, sem link) e a coluna **Link** traz apenas a URL completa, sem texto nem título. Estimado e Lançado só na linha do card. Fechar com uma linha de totais (cards, fechados x abertos, horas estimadas x lançadas). Só cards do usuário.

## Quando mostrar automaticamente

Além de quando o usuário chamar `/task-status`, mostre a **visão curta** (card em andamento + próxima tarefa) sozinho, sem ser pedido, **a cada passo concluído** do desenvolvimento de uma task e **imediatamente antes de qualquer pergunta de aprovação** ("posso criar o card?", "posso abrir o MR?", "posso aceitar o MR?", plano pronto para aprovar, tempo estimado etc.). Rode o `collect.py` de novo a cada vez, para o status vir atualizado. Ao terminar uma task (card fechado), mostre também a visão completa do dia (`--day`).

Passos que contam: plano aprovado, dependência atualizada, implementação concluída, checagens (tsc, eslint, vitest, build), prints, preview do card, card criado, branch/commit/push, MR aberto, pipeline concluída, merge e fechamento do card.

## Ícones aprovados

| Situação | Ícone |
|---|---|
| Card criado / aberto (Nova, Em andamento) | 🔵 Aberto |
| Pipeline iniciando / rodando | 🟡 Pipeline rodando |
| Pipeline com sucesso | 🟢 Pipeline com sucesso |
| Pipeline falhou | 🔴 Pipeline falhou |
| MR mesclado | 🟣 Mesclado |
| Card fechado (Resolvida/Fechada) | ✅ Resolvida |
| Aguardando o usuário (ex.: merge) | ⏳ Aguardando merge |

MR aberto com pipeline verde leva "🟢 Pipeline com sucesso · ⏳ Aguardando merge".

## Regras

- Só leitura: não criar, editar nem fechar nada, não commitar, não mesclar.
- Nunca inventar status: tudo vem do JSON; sem dado, escrever "sem informação".
- Texto em português; links completos e clicáveis.
