---
name: work-resume
description: Use when o usuário chamar /work-resume ou pedir o balanço, resumo ou fechamento do dia, da semana ou do mês ("o que fiz hoje", "resumo das últimas horas", "cards e MRs de hoje", "relatório diário", "semanal", "mensal"), ou quiser métricas de produtividade, APF, pontos de função, tempo gasto versus tempo manual, Redmine e GitLab no dia.
---

# work-resume

Resumo **diário, semanal ou mensal** (fuso America/Sao_Paulo), com cards, MRs e comparativo APF.

## Período (perguntar sempre)

Ao ser chamada, **perguntar ao usuário** (AskUserQuestion) se o resumo será **Diário**, **Semanal** ou **Mensal**, a menos que ele já tenha dito na chamada. Janelas, pela data do computador:

- **Diário**: 00:01 de hoje até o momento da chamada. Ex.: chamado às 13:16 → janela de 13h15min.
- **Semanal**: domingo a sábado da semana que contém hoje (semana do calendário do Windows). Ex.: 11/10/26 a 17/10/26. O fim é "agora" enquanto a semana não terminou.
- **Mensal**: dia 1 ao último dia do mês. Ex.: 01/10/26 a 31/10/26. O fim é "agora" enquanto o mês não terminou.

Semanal e mensal têm a mesma estrutura; só muda o conjunto de dias. Arquivo: `work-resume-AAAA-MM-DD.html` (diário), `work-resume-semanal-AAAA-MM-DD.html` (data = último dia da janela) e `work-resume-mensal-AAAA-MM.html`.

## Passos

1. **Coletar**: `python3 -I ~/.claude/skills/work-resume/scripts/collect.py <scratchpad>/work-resume.json diario|semanal|mensal [AAAA-MM-DD]` (data opcional; padrão hoje). O JSON traz `period`, `window.first_day/last_day`, `days` (cada dia com `weekday`, `weekend`, `holiday`, `holiday_kind`, `hours` lançadas no Redmine, `overtime_hours`, `future`), `time_entries` e `overtime` (resumo). Cada card traz `spent_in_window` (horas lançadas no período; `spent_hours` é o acumulado de sempre). Feriados: nacionais, 09/07 (SP) e pontos facultativos (Carnaval, Corpus Christi); extras em `~/.claude/work-resume.json` → `"extra_holidays": {"01-25": "Aniversário de São Paulo"}`. Usa `~/.claude/redmine.env` e `~/.claude/gitlab.env` (nunca exibir chaves). Se imprimir `AVISO` de arquivo ausente, informar e pedir ao usuário para criá-lo; seguir com o que foi coletado. Se o host não resolver (VPN/rede), parar e avisar; não improvisar.
1b. **Tokens**: `python3 -I ~/.claude/skills/work-resume/scripts/tokens.py <scratchpad>/work-resume.json` (depois da coleta; soma os transcripts do Claude Code desta máquina na mesma janela e grava a chave `tokens` no JSON).
2. **Ler o JSON** e montar o relatório (abaixo). Cards = **todos** os criados no período (`created_today`) ∪ concluídos no período (`closed_today`; os nomes dos campos são os mesmos nos três períodos), sem descartar nenhum. Separar em **Fechados** (`closed_on` preenchido, situação final) e **Abertos** (sem `closed_on`); um card criado e fechado no período entra em Fechados; MRs = criados ou mesclados no período. Liga MR ↔ card por `card_id`, que o `collect.py` preenche e documenta em `card_link`: `branch` (número em `task-NNNN`), `issue` (link `issues/NNNN` do card na descrição) ou `keyword` (termo camelCase do título que só aparece na descrição de um card; é inferência, então marcar no relatório). MR com `card_id` nulo não tem card. Cada MR traz também `project` (último trecho do caminho no GitLab) e `project_path`.
3. **Gerar o HTML** (uma página só, com tabelas e gráficos): **partir de `~/.claude/skills/work-resume/assets/layout-referencia.html`** (modelo aprovado pelo usuário, com **dados de exemplo anonimizados**: nunca colocar dados reais neste arquivo, pois o repositório `brnmilano/claude-skills` é público) e **trocar apenas os dados dentro dos campos**: mesmo CSS, mesma ordem de seções, mesmas tabelas, colunas, `colgroup`, gráficos e estilos. Informações removidas do layout (não reintroduzir): o texto "(America/Sao_Paulo)" na Janela, a nota sobre cards criados por outra pessoa, e a linha "Projetos: … Horas estimadas … lançadas" abaixo dos Números. Na coluna MR vai só o link com o número (ex.: `!50`), sem projeto nem estado. O ícone de ordenação (⇅, vira ▲/▼ na coluna ativa) fica sempre visível, via CSS `th::after`. As tabelas de cards têm cabeçalhos clicáveis para ordenar (script no fim do `<main>`; manter). Nada de redesenho; só o que o usuário pedir, e então atualizar a referência. As seções novas (Horas extras e feriados) reaproveitam as classes existentes (`.tw`, `table`, `.kpi`, `tr.sub`, `.t`, `.lg`). **Animação de carregamento**: já vem no `layout-referencia.html` (bloco `/*wr-anim*/` no fim do `<main>`; manter). Ao entrar na tela, os números dos cards de `.kpi` contam de 0 até o valor e as barras dos SVGs crescem da esquerda; os textos dos gráficos não mudam. Desligada com "reduzir movimento" do sistema e na impressão. Gráficos continuam SVG/CSS puro, sem biblioteca externa. Escrever primeiro em `<scratchpad>/work-resume-AAAA-MM-DD.html`, depois (a) copiar para Downloads do Windows (`ls /mnt/c/Users/` para saber a máquina) e (b) publicar com a ferramenta Artifact **privado** (padrão da ferramenta; nunca compartilhar nem tornar público, pois traz cards, MRs e tempos). Nunca gravar no repositório. Informar o caminho em Downloads e o link do Artifact. Sem Artifact disponível, entregar só o arquivo.
4. **Responder no terminal** com o resumo curto (seções 1–3 e o total de tokens), o caminho do HTML **como link clicável** e o link do Artifact privado. Link do arquivo: markdown com URL `file:///` do caminho Windows, em formato `[work-resume-AAAA-MM-DD.html](file:///C:/Users/<usuário>/Downloads/work-resume-AAAA-MM-DD.html)` (Windows Terminal abre no navegador padrão com Ctrl+clique); logo depois, o caminho em texto simples (`C:\Users\<usuário>\Downloads\...`) para copiar. O link do Artifact já é uma URL e fica clicável sozinho.

## Conteúdo do relatório

1. **Janela**: período (Diário/Semanal/Mensal), início 00:00 do primeiro dia, fim, tempo decorrido (`h min`; em semanal/mensal, `d h min`). Semanal/mensal: citar o intervalo (ex.: 11/10/2026 a 17/10/2026) e os feriados que caem nele.
2. **Resumo do que foi feito**: 1 bullet por card, a partir do título, escopo e diff do MR (em português, objetivo).
3. **Números**: total de cards do dia, cards criados, cards abertos, cards fechados, MRs abertos, MRs mesclados, **horas lançadas** (total do período). Logo abaixo dos cards de números, a tabela **Horas por card** (`Card | Título | Projeto | Horas lançadas`, com linha de total e "—" para card sem lançamento): gerar com `python3 -I ~/.claude/skills/work-resume/scripts/render_hours.py <scratchpad>/work-resume.json <ids dos cards do relatório>`, que imprime o card de KPI (primeira linha, entra no `.kpi`) e a tabela (segunda, antes do gráfico "Cards do dia e MRs"). As horas vêm dos lançamentos do Redmine (`time_entries`).
4. **Tabelas de itens**: duas tabelas, **Cards fechados** e **Cards abertos**, cada uma com `Card | Título | Situação | Link do card | MR | Estado | Link do MR` e a contagem no título. Seção vazia: escrever "nenhum".
5. **APF por task** (todos os cards do dia, abertos e fechados, com a coluna `Situação`): tabela com as funções identificadas, `Card | Função | Tipo | DET | FTR/RET | Complexidade | PF`, e total de PF por card.
6. **Comparativo de tempo** por card e média: `Card | PF | Tempo manual (PF × h/PF) | Tempo gasto (Redmine spent_hours) | Lead time (criação do card → merge) | Economia (h e %)`. Abertos e fechados entram na mesma métrica: linha final com médias e totais gerais, mais subtotais de Fechados e Abertos. Cards ainda sem tempo gasto: usar `estimated_hours` marcado como "estimado". Tempo gasto = `spent_in_window` (horas lançadas dentro do período); se for 0 mas `spent_hours` > 0, usar `spent_hours` e marcar "acumulado".
7. **Tokens gastos** (`tokens` do JSON): gerar o bloco HTML com `python3 -I ~/.claude/skills/work-resume/scripts/render_tokens.py <scratchpad>/work-resume.json [PF_total]` e colar no lugar da seção (não montar à mão). Formato: tabela `Item | Valor | Exato | Custo (US$) | Preço por milhão | × a entrada | % dos tokens | % do custo | Média por resposta` (valores reais em colunas, não em texto corrido) com Entrada nova (input), Saída (output), Leitura de cache e Escrita de cache em valor compacto (`162,1k`, `273,0 milhões`), subtotal de tokens novos (entrada + saída + escrita), total geral e **Custo total em US$ com o modelo** (ex.: `US$ 42,56 (modelo Sonnet 5.5)`); depois tabelas Por modelo e Por projeto (mesmas colunas, mais respostas e custo) o gráfico de custo por tipo de token e o bloco "Como ler esta seção" (legendas explicativas de cada tipo de token, em cards (`.cards`) logo abaixo da tabela principal, uma legenda por item, na coluna "O que significa" e na lista final; manter). O custo vem de `tokens.py` (tabela `PRICES` em US$/milhão de tokens, escrita de cache a 1,25×; **atualizar `PRICES` quando sair modelo novo ou o preço mudar**; modelo sem preço aparece em `modelos_sem_preco` e o relatório avisa). Só vale para as sessões desta máquina e não atribui tokens a cada card.
8. **Horas extras e feriados** (seção separada, após Tokens; gerar o bloco com `python3 -I ~/.claude/skills/work-resume/scripts/render_overtime.py <scratchpad>/work-resume.json` e colar antes do `<script>` final, sem montar à mão): horas lançadas em **sábados, domingos e feriados** (`days[].overtime_hours`; ponto facultativo não conta como feriado). Conteúdo: KPIs (total de horas lançadas no período, horas extras, dias com hora extra); tabela `Data | Dia | Feriado | Horas lançadas | Hora extra`, uma linha por dia do período (dias futuros omitidos), com feriado, sábado e domingo sinalizados e linha final de totais; lista dos cards com horas lançadas em dia de hora extra (`time_entries` cruzado com `days`). Nenhuma hora extra: escrever "nenhuma". No diário, a seção só lista o dia atual (útil se for fim de semana ou feriado). Sinalizar feriados também na Janela (item 1).

## Layout do HTML

- **Formato de tempo**: durações abaixo de 1 h aparecem em minutos (0,25 h → `15 min`, 0,5 h → `30 min`), em todas as seções, tabelas e rótulos de gráficos; a partir de 1 h, em horas (`1,0 h`, `1,25 h`, `6,0 h`). Os geradores `render_hours.py` e `render_overtime.py` já fazem isso; no resto (seção 6 e gráfico de tempo) converter ao montar.

- Largura máxima da página: `main{max-width:1024px}`.
- As tabelas **Cards fechados** e **Cards abertos** usam as mesmas colunas, com larguras idênticas para ficarem alinhadas uma sobre a outra: `table-layout:fixed` e um `<colgroup>` único copiado nas duas, com Card 76px, Título flexível, Projeto 130px, Situação 104px e MR 210px (`min-width:760px` na tabela, dentro do `.tw` com rolagem horizontal). Um MR por linha na célula, com `white-space:nowrap` no texto do MR.

## Gráficos (simples, na própria página, SVG/CSS sem biblioteca externa)

1. **Cards do dia**: barras Fechados × Abertos (e MRs abertos × mesclados).
2. **Tempo por card**: barras agrupadas `Tempo manual (APF)` × `Tempo gasto`, uma dupla por card.
3. **PF por card**: barras horizontais, cor por situação.
4. **Tokens**: barras do custo (US$) por tipo de token (cache lido, saída, cache escrito, entrada), gerado por `render_tokens.py`.
5. **Horas por dia** (semanal e mensal): uma barra por dia, cor distinta para dias de hora extra (sábado, domingo, feriado); no mensal, barras estreitas com rótulo só no dia do mês.

Cada gráfico com título, rótulos de valor e legenda; cores seguindo `dataviz`, legíveis em tema claro e escuro. Sem dados para um gráfico, omiti-lo.

## Método APF (IFPUG simplificado, estimativa)

Classificar a partir da descrição do card e dos arquivos do MR (`files[].path`, linhas adicionadas):

| Tipo | Quando | Baixa | Média | Alta |
|---|---|---|---|---|
| ALE/ALI (arquivo lógico interno: entidade/tabela/migration) | dados mantidos pela aplicação | 7 | 10 | 15 |
| AIE (interface externa lida) | dados mantidos por outro sistema | 5 | 7 | 10 |
| EE (entrada externa: criar/alterar/excluir) | formulário/endpoint que grava | 3 | 4 | 6 |
| SE (saída externa: relatório/cálculo) | saída com lógica derivada | 4 | 5 | 7 |
| CE (consulta externa: listagem/detalhe) | leitura sem cálculo | 3 | 4 | 6 |

Complexidade por DET (campos) e FTR/RET: poucos campos/1 arquivo → Baixa; intermediário → Média; muitos campos/vários arquivos → Alta. Tarefas só de refactor, teste, lint ou ajuste visual sem função nova de negócio: PF mínimo de 1 por tela/endpoint tocado, dizendo isso na tabela. **Sempre rotular como estimativa** e listar as suposições.

## Produtividade manual

`~/.claude/work-resume.json` guarda `{"hours_per_pf": 8}`. Se não existir, usar 8 h/PF (referência de mercado 6–10) e avisar que o valor é padrão, perguntando uma única vez se quer ajustar. Tempo manual = PF × `hours_per_pf`.

## Erros comuns

- Contar o tempo de ontem: no diário a janela começa em 00:00 de **hoje**, não 24h para trás. Semanal começa no **domingo**, não na segunda.
- Mexer no layout por conta própria: o HTML sai sempre de `assets/layout-referencia.html`, mudando só os dados.
- Mostrar APF sem as funções que o compõem: sempre incluir a tabela de funções.
- Inventar tempo gasto de card sem lançamento: marcar como estimado.
- Somar tokens sem deduplicar por `message.id` (o transcript repete respostas); o `tokens.py` já cuida disso.
- Gravar o relatório fora de Downloads ou dentro do repositório; publicar o Artifact como público ou compartilhado.