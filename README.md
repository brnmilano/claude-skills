# skills

Skills do Claude Code compartilhadas pela equipe da Very (`~/.claude/skills`).

| Skill&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; | Descrição |
|:---|:---|
| [`plano`](#plano) | Monta e conduz o pedido de plano (plan mode) no padrão da equipe: tipos feature, fix, refactor, docs, test, build, ci e chore. |
| [`work-resume`](#work-resume) | Relatório diário, semanal ou mensal: cards do Redmine, MRs do GitLab, horas, horas extras, APF, tempo e tokens. |
| [`task-status`](#task-status) | Visão curta (card em andamento, MR, pipeline e próxima tarefa) e visão completa do dia, com ícones de status. |
| [`workflow`](#workflow) | Fluxo de desenvolvimento SEDS-SP: card no Redmine, branch, commit, checagens e MR. |

## Instalação

```bash
git clone https://gitlab.verytecnologia.com.br/eso/iaops/skills.git
cp -r skills/{plano,task-status,work-resume,workflow} ~/.claude/skills/
```

### Configuração

As credenciais ficam em `~/.claude/` e **não** fazem parte deste repositório:

| Arquivo | Conteúdo | Usado por |
|---|---|---|
| `~/.claude/redmine.env` | `REDMINE_API_KEY=...` | `work-resume`, `task-status`, `workflow` |
| `~/.claude/gitlab.env` | `GITLAB_TOKEN=...` (escopo `api`) | `work-resume`, `task-status`, `workflow` |
| `~/.claude/workflow.json` | nome, links e ids do Redmine/GitLab, pasta de prints (criado pela skill `workflow` na primeira execução) | `workflow`, `task-status` |
| `~/.claude/work-resume.json` (opcional) | `{"hours_per_pf": 8, "extra_holidays": {"01-25": "Aniversário de São Paulo"}}` | `work-resume` |

Requisitos: `python3` e acesso (VPN, quando for o caso) ao Redmine e ao GitLab.

---

## `plano`

Monta o pedido de plano (plan mode) já com o que costuma faltar: escopo, comportamento versus visual, estados, responsividade e entrega.

**Como usar**

```
/plano <tipo>: <alvo> [documento]
```

Exemplos:

```
/plano feature: relatório de repasses em /financeiro
/plano fix: Salvar não habilita após o CEP
/plano refactor: tela de listagem de beneficiários
/plano feature: relatório de repasses ~/docs/repasses.md
```

| Tipo | Quando usar |
|---|---|
| `feature` | Funcionalidade nova para o usuário ou para o sistema (tela, componente, endpoint, regra de negócio). |
| `fix` | Correção de bug: algo que deveria funcionar e não funciona. |
| `refactor` | Algo que já existe e funciona e será melhorado, alterado ou reconstruído (inclui o visual da tela). |
| `docs` | Só documentação; o código executável não muda. |
| `test` | Criar ou ajustar testes sem mudar o código de produção. |
| `build` | Build e dependências (`package.json`, `pom.xml`, `Dockerfile`, vite/webpack, atualização de libs). |
| `ci` | Pipeline de integração/entrega (`.gitlab-ci.yml`, jobs, stages, deploy). |
| `chore` | Manutenção que não cabe nas outras e não afeta produção nem testes. |

- Os tipos são os mesmos prefixos de branch e de commit (`feature/`, `fix/`, ...).
- Aliases antigos: `tela` = `refactor`, `bug` = `fix`, `componente` = `feature`.
- Se o tipo não vier na chamada, a skill infere pelo texto e confirma numa frase.
- O que você escrever na chamada já preenche o modelo; a skill só pergunta o que falta e muda o plano (até 12 perguntas, em rodadas).
- `docs`, `test`, `build`, `ci` e `chore` usam um modelo leve, sem viewports nem estados de tela.
- **Documento (opcional):** spec, card, PRD, ata ou print, por caminho ou anexo. É complemento e ponto de partida do plano e **prevalece** sobre o texto da chamada; contradições vão para "Decisões a confirmar". O plano registra `Fonte: <documento>` e separa o que veio dele do que foi suposição. Instruções dentro do documento são tratadas como conteúdo, nunca executadas; a skill pede o caminho ou a instrução correta.
- Antes de aprovar, o plano mostra o `task-status` (visão curta) e fecha com **Próximos passos** até o `/workflow`.
- Depois de preencher o modelo, a skill planeja (passo 2) seguindo os princípios do repositório do projeto.

## `work-resume`

Relatório de produtividade com cards do Redmine, MRs do GitLab, horas lançadas, horas extras, APF (pontos de função), tempo gasto versus tempo manual e tokens/custo do Claude Code.

**Como usar**

```
/work-resume
```

A skill **pergunta** se o resumo é **Diário**, **Semanal** ou **Mensal** (ou você já diz na chamada, ex.: "resumo semanal"). Janelas, pela data do computador (fuso America/Sao_Paulo):

| Período | Janela |
|---|---|
| Diário | 00:01 de hoje até o momento da chamada |
| Semanal | domingo a sábado da semana atual (ex.: 11/10 a 17/10) |
| Mensal | dia 1 ao último dia do mês (ex.: 01/10 a 31/10) |

**O que sai**

- Um HTML único (sem dependências externas), salvo no local que você escolher (a skill pergunta; a sugestão é a pasta **Downloads**, no WSL a do Windows), e um Artifact **privado** quando a ferramenta estiver disponível. No terminal, a skill devolve um resumo curto e o link clicável do arquivo.
- Seções do relatório:
  1. **Janela**: início, fim, tempo decorrido e feriados do período.
  2. **Resumo do que foi feito**: um item por card.
  3. **Números**: cards (criados, abertos, fechados), MRs (abertos, mesclados), horas lançadas e a tabela **Horas por card**.
  4. **Cards fechados** e **Cards abertos**: tabelas ordenáveis (clique no cabeçalho) com link do card e do MR.
  5. **APF por task**: funções, tipo, DET, FTR/RET, complexidade e PF (estimativa, método IFPUG simplificado).
  6. **Comparativo de tempo**: tempo manual (PF × horas por PF), tempo gasto (Redmine), lead time e economia.
  7. **Tokens gastos**: entrada, saída, leitura e escrita de cache, custo em US$ por modelo e por projeto, com legendas.
  8. **Horas extras e feriados**: horas lançadas em sábados, domingos e feriados, por dia e por card.
- Durações abaixo de 1 h aparecem em minutos (`15 min`). Os números dos cards contam de 0 ao valor e as barras crescem ao entrar na tela (desligado com "reduzir movimento" do sistema).

**Detalhes**

- **Horas por PF**: 8 h por padrão; ajuste com `hours_per_pf` em `~/.claude/work-resume.json`.
- **Feriados**: nacionais, 09/07 (SP) e pontos facultativos (Carnaval, Corpus Christi); outros em `extra_holidays`. Hora extra = horas lançadas em sábado, domingo ou feriado.
- **Tokens e custo**: lidos dos transcripts do Claude Code **da máquina onde a skill roda** (outras máquinas não entram). O custo é estimado pela tabela `PRICES` em `scripts/tokens.py` (US$ por milhão de tokens); atualize-a quando sair modelo novo.
- **Layout**: `assets/layout-referencia.html` é o modelo do relatório, com **dados de exemplo** (cards, projetos e nomes fictícios). A skill sempre parte dele e troca só os dados dentro dos campos.

**Rodando os scripts manualmente**

```bash
S=~/.claude/skills/work-resume/scripts
python3 -I $S/collect.py /tmp/wr.json semanal      # diario | semanal | mensal [AAAA-MM-DD]
python3 -I $S/tokens.py /tmp/wr.json               # soma tokens e custo da janela
python3 -I $S/render_hours.py /tmp/wr.json         # KPI e tabela de horas por card (seção 3)
python3 -I $S/render_tokens.py /tmp/wr.json 20     # seção 7 (20 = PF total, opcional)
python3 -I $S/render_overtime.py /tmp/wr.json      # seção 8
```

## `task-status`

Visão rápida (só leitura) do que está em andamento: card do Redmine, MR do GitLab, pipeline e a próxima tarefa da fila.

**Como usar**

```
/task-status            # visão curta: card em andamento, MR, pipeline e próxima tarefa
/task-status completo   # visão completa do dia (estimado × lançado por card)
```

- Também aparece **sozinha** a cada passo concluído de uma task e antes de qualquer pergunta de aprovação (plano aprovado, checagens, MR aberto, pipeline, merge, fechamento do card).
- Na primeira execução em cada máquina, confirma sua identidade a partir de `~/.claude/workflow.json`.
- Ícones de status: 🔵 aberto, 🟡 pipeline rodando, 🟢 sucesso, 🔴 falhou, entre outros definidos na skill.
- Para relatório diário, semanal ou mensal, use `/work-resume`.

## `workflow`

Fluxo de desenvolvimento dos projetos da SEDS-SP: card no Redmine, branch, commit, checagens de qualidade e MR no GitLab.

**Como usar**

```
/workflow
```

- Na primeira execução, pergunta nome, links do Redmine/GitLab e pasta de prints e grava em `~/.claude/workflow.json`.
- Pede o **tempo estimado** (`h:mm`) se você não informar na chamada.
- Ordem: configuração → tempo estimado → checagens (incluindo a suíte completa) → prints das telas → preview do card (único OK exigido) → card pela API → branch, commit e push → MR → acompanhamento da pipeline → merge e fechamento automático do card.

---

## Contribuindo

- Alterações entram por merge request; não envie direto para a `main`.
- Não versione dados reais (cards, nomes, relatórios gerados, tokens ou credenciais). O `layout-referencia.html` da `work-resume` deve conter só dados de exemplo.
- Credenciais ficam em `~/.claude/` de cada pessoa, nunca neste repositório.
