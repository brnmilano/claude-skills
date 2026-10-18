#!/usr/bin/env python3
"""Gera o HTML da seção "7. Tokens gastos" a partir da chave `tokens` do JSON do work-resume.

Uso: python3 -I render_tokens.py <work-resume.json> [PF_total]
Imprime o bloco HTML (usa só classes do layout de referência). PF_total opcional: habilita "tokens novos por PF".
"""
import json, re, sys

d = json.load(open(sys.argv[1]))["tokens"]
pf = float(sys.argv[2]) if len(sys.argv) > 2 else 0
F = ("input_tokens", "output_tokens", "cache_creation_input_tokens", "cache_read_input_tokens")
prices = d.get("precos_usd_por_mtok", {})


def n(x):
    return f"{x:,.0f}".replace(",", ".")


def compact(x):  # 746 · 162,1k · 273,0 milhões (formato pedido pelo usuário)
    if x < 1000:
        return n(x)
    if x < 1e6:
        return f"{x / 1e3:,.1f}k".replace(".", ",")
    v = f"{x / 1e6:,.1f}".replace(".", ",")
    return f"{v} milhão" if x < 2e6 else f"{v} milhões"


def usd(x):
    return "US$ " + f"{x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def short(m):
    mm = re.match(r"claude-(\w+?)-(\d+)(?:-(\d+))?$", m)
    return f"{mm[1].capitalize()} {mm[2]}" + (f".{mm[3]}" if mm[3] else "") if mm else m


def proj(p):
    return re.sub(r"^-home-[^-]+-[^-]+-work-", "", p) if "-work-" in p else "~ (fora dos repositórios)"


def parts(u, model):  # custo por tipo de token
    pr = prices.get(model)
    return [(u.get(k) or 0) * v / 1e6 for k, v in zip(F, pr)] if pr else [0, 0, 0, 0]


tot = d["total"]
cost_by = [sum(parts(u, m)[i] for m, u in d["por_modelo"].items()) for i in range(4)]
novos = tot[F[0]] + tot[F[1]] + tot[F[2]]
models = ", ".join(short(m) for m in d["por_modelo"])
DESC = {
    "in": "Texto novo enviado ao Claude que ainda não estava guardado em cache: suas perguntas e arquivos lidos pela primeira vez. Cobrado a preço cheio de entrada.",
    "out": "Tudo o que o Claude escreveu de volta: respostas, código, comandos e raciocínio. É o tipo mais caro por token (5× o preço da entrada).",
    "read": "Contexto já guardado (histórico da conversa, instruções, arquivos) que o Claude relê a cada resposta sem reprocessar. Cada token lido custa uma fração do preço da entrada, mas o contexto é relido a cada resposta, então o volume se acumula.",
    "write": "Primeira vez que um trecho do contexto é guardado no cache para ser reaproveitado depois. Custa 25% a mais que a entrada normal, mas evita pagar preço cheio de entrada nas respostas seguintes.",
    "new": "Entrada nova + saída + escrita de cache: o trabalho realmente novo da sessão, sem contar o que só foi relido do cache. É a base do indicador de tokens por PF.",
    "all": "Tudo somado, incluindo as leituras de cache. O número fica enorme por causa do cache e não representa trabalho novo.",
    "cost": "Estimativa em dólares: tokens de cada tipo × preço por milhão do modelo. É valor de tabela da API, não a fatura.",
}
resp = tot["mensagens"] or 1
in_price = cost_by[0] / tot[F[0]] * 1e6 if tot[F[0]] else None


def pct(x):
    return "&lt;0,01%" if 0 < x < 0.0001 else f"{x * 100:.2f}%".replace(".", ",")


def metrics(v, c, price=True):
    """Colunas numéricas: preço por milhão, × a entrada, % dos tokens, % do custo, média por resposta."""
    pm = c / v * 1e6 if price and v else None
    mult = f"{pm / in_price:.2f}×".replace(".", ",") if pm is not None and in_price else "—"
    return [usd(pm) if pm is not None else "—", mult, pct(v / tot["total"]),
            pct(c / (tot["custo_usd"] or 1)) if c else "—", compact(v / resp)]


rows = [
    ("Entrada nova (input)", tot[F[0]], cost_by[0], DESC["in"]),
    ("Saída (output)", tot[F[1]], cost_by[1], DESC["out"]),
    ("Leitura de cache", tot[F[3]], cost_by[3], DESC["read"]),
    ("Escrita de cache", tot[F[2]], cost_by[2], DESC["write"]),
]
td = lambda cells: "".join(f"<td>{x}</td>" for x in cells)
h = ['<h2>7. Tokens gastos</h2><div class="tw"><table><thead><tr><th>Item</th><th>Valor</th><th>Exato</th><th>Custo (US$)</th><th>Preço por milhão</th><th>× a entrada</th><th>% dos tokens</th><th>% do custo</th><th>Média por resposta</th></tr></thead><tbody>']
for name, v, c, ds in rows:
    h.append(f"<tr>{td([name, compact(v), n(v), usd(c)] + metrics(v, c))}</tr>")
h.append(f'<tr class="sub">{td(["Tokens novos (entrada + saída + escrita)", compact(novos), n(novos), "—"] + metrics(novos, 0, False))}</tr>')
h.append(f'<tr class="sub">{td(["Total geral (com cache lido)", compact(tot["total"]), n(tot["total"]), "—"] + metrics(tot["total"], 0, False))}</tr>')
h.append(f'<tr class="sub"><td>Custo total</td><td colspan="2">modelo {models}</td><td>{usd(tot["custo_usd"])}</td><td>—</td><td>—</td><td>—</td><td>100,00%</td><td>{usd(tot["custo_usd"] / resp)}</td></tr></tbody></table></div>')
h.append('<div class="cards">' + "".join(f'<div><b>{t}</b>{DESC[k]}</div>' for t, k in (
    ("Entrada nova (input)", "in"), ("Saída (output)", "out"), ("Leitura de cache", "read"), ("Escrita de cache", "write"),
    ("Tokens novos", "new"), ("Total geral", "all"), ("Custo total", "cost"))) + "</div>")


def table(title, items, label):
    out = [f'<h3>{title}</h3><div class="tw"><table><thead><tr><th>{label}</th><th>Entrada</th><th>Saída</th><th>Leitura de cache</th><th>Escrita de cache</th><th>Respostas</th><th>Custo (US$)</th></tr></thead><tbody>']
    for name, u in items:
        out.append(f'<tr><td>{name}</td><td>{compact(u[F[0]])}</td><td>{compact(u[F[1]])}</td><td>{compact(u[F[3]])}</td><td>{compact(u[F[2]])}</td><td>{n(u["mensagens"])}</td><td>{usd(u["custo_usd"])}</td></tr>')
    out.append("</tbody></table></div>")
    return "".join(out)


h.append(table("Por modelo", [(short(m), u) for m, u in d["por_modelo"].items()], "Modelo"))
h.append(table("Por projeto", [(proj(p), u) for p, u in d["por_projeto"].items()], "Projeto"))

# gráfico: custo por tipo de token
labels = ["Cache lido", "Saída", "Cache escrito", "Entrada"]
vals = [cost_by[3], cost_by[1], cost_by[2], cost_by[0]]
mx = max(vals) or 1
svg = [f'<h3>Custo por tipo de token</h3><svg viewBox="0 0 620 {len(vals) * 26 + 4}" role="img" width="100%">']
for i, (lb, v) in enumerate(zip(labels, vals)):
    y = i * 26
    w = max(v / mx * 380, 1)
    svg.append(f'<text x="0" y="{y + 17}" class="t">{lb}</text><rect x="110" y="{y + 4}" width="{w:.1f}" height="18" fill="var(--c1)" rx="2"/><text x="{110 + w + 5:.1f}" y="{y + 17}" class="t">{usd(v)} ({v / (tot["custo_usd"] or 1) * 100:.0f}%)</text>')
svg.append("</svg>")
h.append("".join(svg))
legend = (
    '<h3>Como ler esta seção</h3><ul class="mut">'
    "<li><b>Valor × Exato:</b> o mesmo número; \"Valor\" é abreviado (k = mil) para leitura rápida e \"Exato\" mostra a contagem completa.</li>"
    "<li><b>Respostas:</b> quantas vezes o Claude respondeu no período. Cada resposta relê o contexto do cache, por isso a leitura de cache cresce tanto.</li>"
    "<li><b>Custo (US$):</b> estimativa pela tabela de preços da API. Cada tipo de token tem um preço diferente: a leitura de cache é barata por token, mas o volume é tão grande que costuma ser a maior fatia do custo.</li>"
    "<li><b>Por modelo:</b> separa o gasto por modelo do Claude usado (cada um tem preço diferente). <b>Por projeto:</b> separa por pasta de trabalho onde o Claude Code rodou; \"~ (fora dos repositórios)\" são conversas fora dos repositórios, como ajustes de skill.</li>"
    "<li><b>Custo por tipo de token:</b> mostra para onde foi cada dólar; a % é a fatia do custo total.</li>"
    "<li><b>Tokens novos por PF:</b> tokens novos ÷ pontos de função do período; mede quanto de IA foi gasto por unidade de entrega.</li>"
    "<li><b>Escopo:</b> só as sessões do Claude Code <u>desta máquina</u>; sessões em outro computador não entram. Não atribui tokens a cada card.</li></ul>"
)
h.append(legend)
extra = (f" Custo por PF: {usd(tot['custo_usd'] / pf)}." if pf else "") + f" Tokens novos por PF: {n(novos / pf)} ({n(novos)} ÷ {pf:g} PF)." if pf else ""
h.append(f'<p class="mut">Respostas contadas: {n(tot["mensagens"])}.{extra} Custo estimado pela tabela de preços da API (US$ por milhão de tokens); escrita de cache a 1,25× a entrada (TTL de 5 min). </p>')
if d.get("modelos_sem_preco"):
    h.append(f'<p class="mut">Sem preço cadastrado: {", ".join(d["modelos_sem_preco"])} (custo subestimado).</p>')
print("\n".join(h))
