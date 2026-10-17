---
name: plano
description: Monta e conduz o pedido de plano (plan mode) no padrão do Bruno, em qualquer projeto. Variantes - tela (refatoração de tela), componente (UI de biblioteca ou compartilhado) e bug. Usar ao iniciar "/plano", "vamos criar um /plan" ou quando for planejar uma refatoração, componente ou correção antes de codar.
---

Padrão de criação de plano extraído dos planos já aprovados (CONSEAS, PMASWeb, Auxílio Aluguel, seds-ui).
Objetivo: o pedido já nasce com o que costumava faltar (escopo, comportamento vs. visual, estados,
responsividade, entrega), para o plano sair certo na primeira rodada e sobrar menos ajuste por print.

## Como usar

`/plano [tela|componente|bug] <alvo e o que o Bruno já souber>`

- Se o tipo não vier, inferir pelo texto e confirmar numa frase ("Trato como refatoração de tela, certo?").
- O que o Bruno escreveu na chamada já preenche campos do modelo: **não perguntar de novo**.
- Esta skill **é** o processo de design: não invocar `superpowers:brainstorming` antes dela.

## Passo 1: preencher o modelo

Montar o modelo abaixo com o que já se sabe (texto da chamada, prints, `CLAUDE.md`/`AGENTS.md` do projeto,
memória). Para cada campo **sem resposta e que mude o plano**, perguntar com `AskUserQuestion` (no máximo
12 perguntas no total; a ferramenta aceita até 4 por chamada, então fazer em rodadas; opção recomendada
primeiro). Campo que tem padrão claro no projeto: assumir e declarar a suposição no plano, sem perguntar.

### Bloco base (todos os tipos)

```
Contexto
- Projeto/rota: <projeto> · <rota> · acessada por <caminho de navegação>
- Situação atual: <print ou descrição>  |  Referência: <tela/componente já pronto que serve de modelo>

Escopo
- Dentro: <o que muda>
- Fora: <o que NÃO muda>
- Muda comportamento ou só visual? <visual | comportamento: qual>
- Afeta outros usuários do componente/layout compartilhado? <sim/não, quais>

Padrões a seguir
- <loading / estados vazio e erro / responsividade / espaçamento / estrutura de pastas>

Restrições
- Banco: não rodar migrate/seed/down -v; avisar antes de qualquer ação que toque o banco.
- <branch, o que não rodar, ex.: "eu rodo as checagens">

Entrega e verificação
- Entregar em <1 MR | um MR por grupo>
- Como o Bruno vai conferir: <navegador/print>  |  Viewports: 500/768/1920
```

Regras do bloco base:
- **Restrições de banco** valem sempre; nunca remover (ver memória `feedback-shared-db-inform-first`).
- **Viewports:** mesmos valores da skill `workflow`: 500px (móvel, `p`), 768px (tablet, `m`) e 1920px
  (laptop G, `g`). Exigir o resultado explícito na verificação. O plano só prevê a conferência; os prints
  oficiais continuam sendo tirados pelo `/workflow`.
- Se mudar o comportamento (não só o visual), perguntar qual tela serve de referência (ex.: busca com
  Buscar/Limpar + toast vs. filtro a cada tecla).
- Componente de lib com visual diferente do local (cor, borda, sombra): perguntar se **sobrescreve para manter o
  visual atual** ou **aceita o da lib**.
- Mais de ~10 arquivos ou mais de uma tela: perguntar como dividir a entrega (um MR por grupo).

### Variante `tela` (refatoração de tela, a mais usada)

Acrescentar ao bloco base:

```
- Estados obrigatórios: loading único (um só para a página), vazio com mensagem, erro com "tentar novamente"
- Busca/filtros: seguir <tela de referência>
- Componentes: usar todos os da <lib> que existirem; onde o visual diferir, <sobrescrever | aceitar o da lib>
- Estrutura de pastas: components/<Nome>/<Nome>.tsx + .test.tsx, types/, utils/constants.ts (strings)
- Testes: criar os que faltarem nos arquivos tocados
```

Confirmar a estrutura de pastas **antes → depois** quando houver movimentação de arquivos (plano rejeitado
no CONSEAS por não trazê-la). Respeitar [[feedback-feature-types-constants-structure]] e
[[feedback-jsdoc-pt-br-pattern]] quando aplicável ao projeto.

### Variante `componente` (UI de biblioteca ou compartilhado)

Acrescentar ao bloco base:

```
- Componente(s) e base no DS: <ex.: BrButton do gov.br>
- Modelo a seguir: <componente existente> (props, teste, story)
- API: props, variantes, estados; nomes exportados e risco de colisão
- Entregáveis: .tsx, index.ts, .test.tsx, .stories.tsx, export em src/index.ts, changeset
- Como testar: um `it` por comportamento (render, evento, estado, className mesclado)
```

Antes de planejar, ler o componente-modelo e extrair o padrão dele (estrutura de pasta, constantes de classe,
JSDoc, `className` mesclado por último).

### Variante `bug` (rascunho: não veio de planos anteriores; refinar com o uso)

Acrescentar ao bloco base:

```
- Sintoma: <o que acontece> · Esperado: <o que deveria acontecer>
- Reprodução: <passos, rota, usuário, dados>  |  Evidência: <print, log, erro colado>
- Causa conhecida ou suspeita: <se houver>; senão, investigar antes de propor a correção
- Escopo da correção: só a causa; sem refatorar ao redor
- Teste de regressão: um teste que falhe antes e passe depois
```

Sem causa conhecida, o plano começa pela investigação (hipóteses e como confirmá-las) e só depois propõe a
correção. Seguir também `superpowers:systematic-debugging` se estiver disponível e o projeto não o proibir.

## Passo 2: planejar

1. Entrar em plan mode (`EnterPlanMode`) com o modelo preenchido como pedido.
2. Explorar o código **somente leitura**: tela/componente atual, a referência indicada, convenções do projeto.
3. Apresentar o plano com `ExitPlanMode`, nesta estrutura (omitir seção que não se aplica):
   - **Contexto**: situação atual, objetivo, escopo confirmado.
   - **Decisões já tomadas** (respostas do Bruno) e **Decisões a confirmar** (com recomendação).
   - **Arquivos** (antes → depois quando houver mudança de estrutura) e **Mudanças por arquivo**.
   - **Reuso**: o que já existe e será aproveitado, para não criar duplicado.
   - **Testes**: o que criar/ajustar, cobrindo loading, erro, vazio, permissão e responsividade quando houver.
   - **Fora de escopo** e **Riscos**.
   - **Docs** a atualizar, se o projeto tiver convenção.
   - **Verificação**: comandos de checagem do projeto + conferência visual nos viewports + o que o Bruno
     confere no navegador. Respeitar quem roda o quê (ex.: "eu rodo as checagens" → só listar os comandos).
4. Não criar branch, card ou commit na aprovação do plano: isso é o `/workflow`, quando o Bruno pedir.

## Princípios

- Pergunte pouco e só o que muda o plano; o resto vira suposição declarada.
- Respostas e plano sempre em português.
- Pedido incompleto não é motivo para travar: monte o modelo com o que há e pergunte só as lacunas.
<!-- teste do hook -->
