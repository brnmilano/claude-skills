# claude-skills

Skills pessoais do Claude Code (`~/.claude/skills`).

| Skill | Descrição |
|---|---|
| `plano` | Monta e conduz o pedido de plano (plan mode) no padrão do Bruno: variantes tela, componente e bug. |
| `work-resume` | Balanço diário: cards do Redmine, MRs do GitLab, tempo, APF e tokens. |
| `workflow` | Fluxo de desenvolvimento SEDS-SP: card no Redmine, branch, commit, checagens e MR. |

## Instalação

```bash
git clone https://github.com/brnmilano/claude-skills.git
cp -r claude-skills/{plano,work-resume,workflow} ~/.claude/skills/
```

Credenciais (`redmine.env`, `gitlab.env`) ficam em `~/.claude/` e não fazem parte deste repositório.

## Sincronização automática

As alterações em `~/.claude/skills/{plano,work-resume,workflow}` são enviadas para este repositório por `~/.claude/sync-skills.sh`, que faz `rsync` para um clone local, commit (`chore: sync <skills>`) e push. Ele é acionado de duas formas:

- **Hook `PostToolUse`** (`Edit|Write`) no `~/.claude/settings.json`: dispara quando o Claude edita uma dessas skills.
- **Cron a cada 15 minutos**: cobre edições feitas fora do Claude (editor, Windows).

Antes do commit, o script verifica o diff em busca de padrões de segredo (`glpat-`, `ghp_`, `*_TOKEN=...` etc.) e aborta sem enviar nada se achar. O resultado de cada execução fica em `~/.claude/sync-skills.log`.

### Ponto de atenção

O disparo pelo hook com um `Edit` real do Claude Code ainda não foi observado em funcionamento; só foi testado simulando o JSON que o hook recebe. Se, após alterar uma skill, o repositório não atualizar na hora:

1. Abra uma nova sessão do Claude Code ou rode `/hooks`, porque o `settings.json` pode não ser relido durante a sessão.
2. Confira `~/.claude/sync-skills.log`.
3. Em último caso, o cron atualiza em até 15 minutos (só roda com o WSL ligado).
