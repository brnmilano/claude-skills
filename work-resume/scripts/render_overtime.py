#!/usr/bin/env python3
"""Gera o HTML da seção "8. Horas extras e feriados" a partir do JSON do work-resume (collect.py).

Uso: python3 -I render_overtime.py <work-resume.json>
Hora extra = horas lançadas no Redmine em sábado, domingo ou feriado (ponto facultativo não conta).
"""
import json, sys
from collections import defaultdict

d = json.load(open(sys.argv[1]))
days = [x for x in d["days"] if not x["future"]]
cards = {c["id"]: c for c in d.get("cards", [])}


def hh(x):  # < 1 h em minutos (0,25 h = 15 min); senão 1 casa (6,0 h) ou 2 quando preciso (1,25 h)
    if x < 1:
        return f"{round(x * 60)} min"
    return (f"{x:.1f}" if abs(x * 10 - round(x * 10)) < 1e-9 else f"{x:.2f}").replace(".", ",") + " h"


def br(iso):
    return f"{iso[8:10]}/{iso[5:7]}/{iso[:4]}"


def mark(x):
    out = []
    if x["holiday"]:
        out.append(f'{x["holiday"]}' + (" (ponto facultativo)" if x["holiday_kind"] == "facultativo" else " (feriado)"))
    if x["weekend"]:
        out.append("fim de semana")
    return "; ".join(out) or "—"


tot = round(sum(x["hours"] for x in days), 2)
ext = round(sum(x["overtime_hours"] for x in days), 2)
nd = sum(1 for x in days if x["overtime_hours"])
h = ['<h2>8. Horas extras e feriados</h2>']
h.append(f'<div class="kpi"><div><b>{f"{tot:g}".replace(".", ",")}</b>horas lançadas no período</div><div><b>{f"{ext:g}".replace(".", ",")}</b>horas extras (sáb, dom e feriados)</div><div><b>{nd}</b>dias com hora extra</div></div>')
h.append('<p class="mut">Hora extra = horas lançadas no Redmine em sábado, domingo ou feriado. Pontos facultativos (Carnaval, Corpus Christi) aparecem sinalizados, mas não contam como hora extra.</p>')
rows = ['<div class="tw"><table><thead><tr><th>Data</th><th>Dia</th><th>Feriado / fim de semana</th><th>Horas lançadas</th><th>Hora extra</th></tr></thead><tbody>']
for x in days:
    oe = x["overtime_hours"]
    cell = f"<b>{hh(oe)}</b>" if oe else "—"
    rows.append(f'<tr><td>{br(x["date"])}</td><td>{x["weekday"]}</td><td>{mark(x)}</td><td>{hh(x["hours"])}</td><td>{cell}</td></tr>')
rows.append(f'<tr class="sub"><td colspan="3">Total</td><td>{hh(tot)}</td><td>{hh(ext)}</td></tr></tbody></table></div>')
h.append("".join(rows))

oday = {x["date"] for x in days if x["overtime_hours"]}
agg = defaultdict(float)
for e in d.get("time_entries", []):
    if e["date"] in oday:
        agg[(e["date"], e["issue_id"], e["project"])] += e["hours"]
h.append("<h3>Cards com horas em dias de hora extra</h3>")
if agg:
    h.append('<div class="tw"><table><thead><tr><th>Data</th><th>Card</th><th>Título</th><th>Projeto</th><th>Horas</th></tr></thead><tbody>')
    for (dt, iid, pj), hr in sorted(agg.items(), key=lambda kv: (kv[0][0], kv[0][1] or 0)):
        c = cards.get(iid)
        link = f'<a href="{c["url"]}" target="_blank" rel="noopener">#{iid}</a>' if c else (f"#{iid}" if iid else "—")
        h.append(f'<tr><td>{br(dt)}</td><td>{link}</td><td>{c["subject"] if c else ("(sem card)" if not iid else "—")}</td><td>{pj}</td><td>{hh(hr)}</td></tr>')
    h.append("</tbody></table></div>")
else:
    h.append("<p>nenhuma</p>")
print("\n".join(h))
