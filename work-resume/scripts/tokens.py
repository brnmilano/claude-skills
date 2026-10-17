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
    return {k: 0 for k in FIELDS} | {"mensagens": 0}

total, by_model, by_proj = blank(), {}, {}
for proj, model, u in seen.values():
    for bucket in (total, by_model.setdefault(model, blank()), by_proj.setdefault(proj, blank())):
        for k in FIELDS:
            bucket[k] += u.get(k) or 0
        bucket["mensagens"] += 1
for b in (total, *by_model.values(), *by_proj.values()):
    b["total"] = sum(b[k] for k in FIELDS)

data["tokens"] = {"total": total, "por_modelo": by_model, "por_projeto": by_proj}
json.dump(data, open(path, "w"), ensure_ascii=False, indent=1)
print(f'tokens: total={total["total"]:,} (entrada={total["input_tokens"]:,} saida={total["output_tokens"]:,} '
      f'cache_escrita={total["cache_creation_input_tokens"]:,} cache_leitura={total["cache_read_input_tokens"]:,}) '
      f'em {total["mensagens"]} respostas')
