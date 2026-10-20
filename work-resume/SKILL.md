---
name: work-resume
description: Use when o usuário chamar /work-resume ou pedir o balanço, resumo ou fechamento do dia ("o que fiz hoje", "resumo das últimas horas", "cards e MRs de hoje", "relatório diário"), ou quiser métricas de produtividade, APF, pontos de função, tempo gasto versus tempo manual, Redmine e GitLab no dia.
---

# work-resume

Resumo do que foi feito desde **00:01 do dia** (fuso America/Sao_Paulo) até o momento da chamada, com cards, MRs e comparativo APF. Ex.: chamado às 13:16 → janela de 13h15min.

## Passos

1. **Coletar**: `python3 -I ~/.claude/skills/work-resume/scripts/collect.py <scratchpad>/work-resume.json [AAAA-MM-DD]` (data opcional; padrão hoje). Usa `~/.claude/redmine.env` e `~/.claude/gitlab.env` (nunca exibir chaves). Se imprimir `AVISO` de arquivo ausente, informar e pedir ao usuário para criá-lo; seguir com o que foi coletado. Se o host não resolver (VPN/rede), parar e avisar; não improvisar.
1b. **Tokens**: `python3 -I ~/.claude/skills/work-resume/scripts/tokens.py <scratchpad>/work-resume.json` (depois da coleta; soma os transcripts do Claude Code desta máquina na mesma janela e grava a chave `tokens` no JSON).
2. **Ler o JSON** e montar o relatório (abaixo). Cards = **todos** os criados no dia (`created_today`) ∪ concluídos no dia (`closed_today`), sem descartar nenhum. Separar em **Fechados** (`closed_on` preenchido, situação final) e **Abertos** (sem `closed_on`); um card criado e fechado no dia entra em Fechados; MRs = criados ou mesclados no dia. Liga MR ↔ card por `card_id`, que o `collect.py` preenche e documenta em `card_link`: `branch` (número em `task-NNNN`), `issue` (link `issues/NNNN` do card na descrição) ou `keyword` (termo camelCase do título que só aparece na descrição de um card; é inferência, então marcar no relatório). MR com `card_id` nulo não tem card. Cada MR traz também `project` (último trecho do caminho no GitLab) e `project_path`.
3. **Gerar o HTML** (uma página só, com tabelas e gráficos): carregar antes as skills `artifact-design` e `dataviz`. Escrever primeiro em `<scratchpad>/work-resume-AAAA-MM-DD.html`, depois (a) **perguntar à pessoa onde salvar o HTML** (`AskUserQuestion`), sugerindo como primeira opção a pasta Downloads do Windows (no WSL, `/mnt/c/Users/<usuário>/Downloads`; `ls /mnt/c/Users/` mostra o usuário) e aceitando outro caminho em "Outro"; copiar o arquivo para o local escolhido (criar a pasta se não existir) e (b) publicar com a ferramenta Artifact **privado** (padrão da ferramenta; nunca compartilhar nem tornar público, pois traz cards, MRs e tempos). Nunca gravar dentro de um repositório git (se o caminho escolhido estiver em um, avisar e pedir outro). Informar o caminho escolhido e o link do Artifact. Sem Artifact disponível, entregar só o arquivo.
4. **Responder no terminal** com o resumo curto (seções 1–3 e o total de tokens), o caminho do HTML e o link do Artifact privado.

## Conteúdo do relatório

1. **Janela**: início 00:00, fim, tempo decorrido (`h min`).
2. **Resumo do que foi feito**: 1 bullet por card, a partir do título, escopo e diff do MR (em português, objetivo).
3. **Números**: total de cards do dia, cards criados, cards abertos, cards fechados, MRs abertos, MRs mesclados.
4. **Tabelas de itens**: duas tabelas, **Cards fechados** e **Cards abertos**, cada uma com `Card | Título | Situação | Link do card | MR | Estado | Link do MR` e a contagem no título. Seção vazia: escrever "nenhum".
5. **APF por task** (todos os cards do dia, abertos e fechados, com a coluna `Situação`): tabela com as funções identificadas, `Card | Função | Tipo | DET | FTR/RET | Complexidade | PF`, e total de PF por card.
6. **Comparativo de tempo** por card e média: `Card | PF | Tempo manual (PF × h/PF) | Tempo gasto (Redmine spent_hours) | Lead time (criação do card → merge) | Economia (h e %)`. Abertos e fechados entram na mesma métrica: linha final com médias e totais gerais, mais subtotais de Fechados e Abertos. Cards ainda sem tempo gasto: usar `estimated_hours` marcado como "estimado".
7. **Tokens gastos** (`tokens` do JSON): tabela com entrada, saída, cache escrito, cache lido e total; separar "tokens novos" (entrada + saída + cache escrito) de "cache lido", que domina o total e custa bem menos. Detalhar por modelo e por projeto, e incluir tokens por PF (tokens novos ÷ PF total) quando houver PF. Só vale para as sessões desta máquina e não atribui tokens a cada card.

## Layout do HTML

- Largura máxima da página: `main{max-width:1024px}`.
- As tabelas **Cards fechados** e **Cards abertos** usam as mesmas colunas, com larguras idênticas para ficarem alinhadas uma sobre a outra: `table-layout:fixed` e um `<colgroup>` único copiado nas duas, com Card 76px, Título flexível, Projeto 130px, Situação 104px e MR 210px (`min-width:760px` na tabela, dentro do `.tw` com rolagem horizontal). Um MR por linha na célula, com `white-space:nowrap` no texto do MR.

## Gráficos (simples, na própria página, SVG/CSS sem biblioteca externa)

1. **Cards do dia**: barras Fechados × Abertos (e MRs abertos × mesclados).
2. **Tempo por card**: barras agrupadas `Tempo manual (APF)` × `Tempo gasto`, uma dupla por card.
3. **PF por card**: barras horizontais, cor por situação.
4. **Tokens**: barra empilhada tokens novos × cache lido (ou rosca por modelo).

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

- Contar o tempo de ontem: a janela começa em 00:00 de **hoje**, não 24h para trás.
- Mostrar APF sem as funções que o compõem: sempre incluir a tabela de funções.
- Inventar tempo gasto de card sem lançamento: marcar como estimado.
- Somar tokens sem deduplicar por `message.id` (o transcript repete respostas); o `tokens.py` já cuida disso.
- Gravar o relatório sem perguntar o local, ou dentro de um repositório git; publicar o Artifact como público ou compartilhado.