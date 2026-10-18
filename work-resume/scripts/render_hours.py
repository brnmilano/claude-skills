#!/usr/bin/env python3
"""Gera, para a seção "3. Números", o card (KPI) de horas lançadas e a tabela de horas por card.

Uso: python3 -I render_hours.py <work-resume.json> [id,id,...]
Imprime duas linhas: 1) o <div> do KPI; 2) o bloco <h3>+tabela. IDs opcionais limitam a tabela aos cards do relatório
(horas em outros cards entram numa linha "Outros cards"). Horas = lançamentos do Redmine no período.
"""
import json, sys
from collections import defaultdict

d = json.load(open(sys.argv[1]))
only = {int(x) for x in sys.argv[2].split(",")} if len(sys.argv) > 2 else None
cards = {c["id"]: c for c in d.get("cards", [])}
per = defaultdict(float)
for e in d.get("time_entries", []):
    per[e["issue_id"]] += e["hours"]
ids = sorted(i for i in (only if only is not None else cards) if i in cards)
outros = round(sum(h for i, h in per.items() if i not in ids), 2)
total = round(sum(per.values()), 2)
def hh(x):  # < 1 h em minutos (0,25 h = 15 min); senão 1 casa (6,0 h) ou 2 quando preciso (1,25 h)
    if x < 1:
        return f"{round(x * 60)} min"
    return (f"{x:.1f}" if abs(x * 10 - round(x * 10)) < 1e-9 else f"{x:.2f}").replace(".", ",") + " h"
periodo = {"diario": "do dia", "semanal": "da semana", "mensal": "do mês"}.get(d.get("period"), "do dia")
kpi = f'<div><b>{f"{total:g}".replace(".", ",")}</b>horas lançadas</div>'
rows = []
for i in ids:
    c = cards[i]
    h = round(per.get(i, 0), 2)
    rows.append(f'<tr><td><a href="{c["url"]}" target="_blank" rel="noopener">#{i}</a></td><td>{c["subject"]}</td><td>{c["project"]}</td><td>{hh(h) if h else "—"}</td></tr>')
if outros:
    rows.append(f'<tr><td>—</td><td>Outros cards ou lançamentos sem card</td><td>—</td><td>{hh(outros)}</td></tr>')
rows.append(f'<tr class="sub"><td colspan="3">Total {periodo}</td><td>{hh(total)}</td></tr>')
tbl = (f'<h3>Horas por card</h3><div class="tw"><table><thead><tr><th>Card</th><th>Título</th><th>Projeto</th><th>Horas lançadas</th></tr></thead><tbody>'
       + "".join(rows) + '</tbody></table></div>'
       + '<p class="mut">Horas lançadas no Redmine; card sem lançamento aparece com "—" (o comparativo da seção 6 usa a estimativa nesses casos).</p>')
print(kpi)
print(tbl)
