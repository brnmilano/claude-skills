#!/usr/bin/env python3
"""Soma os tokens gastos pelo Claude Code na janela do dia (lê ~/.claude/projects/**/*.jsonl).

Uso: python3 -I tokens.py <work-resume.json>   # usa window.start/end do JSON da coleta
Acrescenta a chave "tokens" ao próprio JSON e imprime o resumo.
Mensagens duplicadas no transcript são contadas uma vez (por message.id).
"""
import glob, json, os, sys
from datetime import datetime

path = sys.argv[1]
data = json.load(open(path))
start = datetime.fromisoformat(data["window"]["start"])
end = datetime.fromisoformat(data["window"]["end"])
# US$ por milhão de tokens: (entrada, saída, escrita de cache 5 min = 1,25x entrada, leitura de cache).
# Fonte: tabela de preços da API (claude-api skill, 2026-10-06). Haiku 5.5: faixa até 100K tokens de prompt.
# Não distingue TTL de 1 h (2x) nos transcripts: custo de escrita é estimativa.
PRICES = {
    "claude-sonnet-5-5": (2.00, 10.00, 2.50, 0.20),
    "claude-sonnet-5": (2.00, 10.00, 2.50, 0.20),
    "claude-opus-5-5": (4.00, 20.00, 5.00, 0.20),
    "claude-opus-5": (5.00, 25.00, 6.25, 0.50),
    "claude-opus-4-8": (5.00, 25.00, 6.25, 0.50),
    "claude-opus-4-7": (5.00, 25.00, 6.25, 0.50),
    "claude-opus-4-6": (5.00, 25.00, 6.25, 0.50),
    "claude-fable-5-1": (10.00, 50.00, 12.50, 0.25),
    "claude-fable-5": (10.00, 50.00, 12.50, 0.25),
    "claude-haiku-5-5": (0.10, 0.50, 0.125, 0.01),
    "claude-haiku-4-5": (1.00, 5.00, 1.25, 0.10),
    "claude-sonnet-4-6": (3.00, 15.00, 3.75, 0.30),
}
FIELDS = ("input_tokens", "output_tokens", "cache_creation_input_tokens", "cache_read_input_tokens")

seen = {}  # message.id -> (projeto, modelo, usage)
for f in glob.glob(os.path.expanduser("~/.claude/projects/**/*.jsonl"), recursive=True):
    proj = os.path.relpath(f, os.path.expanduser("~/.claude/projects")).split(os.sep)[0]
    for line in open(f, errors="replace"):
        if '"usage"' not in line:
            continue
        try:
            d = json.loads(line)
            m = d.get("message") or {}
            u = m.get("usage")
            ts = datetime.fromisoformat(d["timestamp"].replace("Z", "+00:00"))
        except (ValueError, KeyError, AttributeError):
            continue
        if u and m.get("id") and start <= ts <= end and m.get("model") != "<synthetic>":
            seen[m["id"]] = (proj, m.get("model", "?"), u)

def blank():
    return {k: 0 for k in FIELDS} | {"mensagens": 0, "custo_usd": 0.0}


def cost(model, u):
    pr = PRICES.get(model)
    if not pr:
        return None
    return sum((u.get(k) or 0) * v for k, v in zip(FIELDS, pr)) / 1e6

total, by_model, by_proj = blank(), {}, {}
for proj, model, u in seen.values():
    for bucket in (total, by_model.setdefault(model, blank()), by_proj.setdefault(proj, blank())):
        for k in FIELDS:
            bucket[k] += u.get(k) or 0
        bucket["mensagens"] += 1
        bucket["custo_usd"] += cost(model, u) or 0
for b in (total, *by_model.values(), *by_proj.values()):
    b["total"] = sum(b[k] for k in FIELDS)
    b["custo_usd"] = round(b["custo_usd"], 4)
semprecos = sorted(m for m in by_model if m not in PRICES)

data["tokens"] = {"total": total, "por_modelo": by_model, "por_projeto": by_proj,
                  "precos_usd_por_mtok": {m: PRICES[m] for m in by_model if m in PRICES},
                  "modelos_sem_preco": semprecos}
json.dump(data, open(path, "w"), ensure_ascii=False, indent=1)
print(f'tokens: total={total["total"]:,} (entrada={total["input_tokens"]:,} saida={total["output_tokens"]:,} '
      f'cache_escrita={total["cache_creation_input_tokens"]:,} cache_leitura={total["cache_read_input_tokens"]:,}) '
      f'em {total["mensagens"]} respostas; custo estimado US$ {total["custo_usd"]:.2f}')
if semprecos:
    print("AVISO: sem preço para", ", ".join(semprecos), "(custo subestimado)")
