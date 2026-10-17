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
