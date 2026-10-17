#!/usr/bin/env python3
"""Coleta cards, MRs e a próxima tarefa da fila (só leitura). Imprime JSON."""
import json, os, re, subprocess, sys, urllib.parse
from datetime import date

HOME = os.path.expanduser("~/.claude")
RM = "redmine.verytecnologia.com.br"
RM_IP = "186.250.243.22"
GL = "https://gitlab.seds.com.br/api/v4/projects/dni%2Fauxilio-aluguel"


def env(name):
    out = {}
    for line in open(f"{HOME}/{name}"):
        if "=" in line and not line.startswith("#"):
            k, v = line.strip().split("=", 1)
            out[k] = v.strip('"\'')
    return out


def get(url, header, resolve=None):
    cmd = ["curl", "-sk", "--max-time", "25", "-H", header]
    if resolve:
        cmd += ["--resolve", resolve]
    r = subprocess.run(cmd + [url], capture_output=True, text=True)
    try:
        return json.loads(r.stdout)
    except Exception:
        return None


CFG_FIELDS = ("name", "redmine_user_id", "gitlab_username")
try:
    cfg = json.load(open(f"{HOME}/workflow.json"))
except FileNotFoundError:
    cfg = {}
missing = [f for f in CFG_FIELDS if not cfg.get(f)]
if "--whoami" in sys.argv:
    # Só informa a identidade já guardada pelo /workflow (sem tocar nas APIs), para a skill confirmar com o usuário.
    print(json.dumps({"found": not missing, "missing": missing,
                      **{f: cfg.get(f) for f in CFG_FIELDS + ("redmine_profile_url", "gitlab_profile_url", "task_status_confirmed")}}, ensure_ascii=False))
    sys.exit(0)
if missing:
    print(json.dumps({"setup_needed": missing}, ensure_ascii=False))
    sys.exit(1)
rm_key = env("redmine.env")["REDMINE_API_KEY"]
gl_key = env("gitlab.env")
gl_token = gl_key.get("GITLAB_TOKEN") or next(iter(gl_key.values()))
uid, guser = cfg["redmine_user_id"], cfg["gitlab_username"]
today = date.today().isoformat()
warnings = []


def redmine(path):
    return get(f"https://{RM}{path}", f"X-Redmine-API-Key: {rm_key}", f"{RM}:443:{RM_IP}")


def gitlab(path):
    return get(f"{GL}{path}", f"PRIVATE-TOKEN: {gl_token}")


mrs_raw = gitlab(f"/merge_requests?author_username={guser}&state=all&order_by=updated_at&per_page=30")
if mrs_raw is None:
    warnings.append("GitLab não respondeu (VPN ligada?)")
    mrs_raw = []

mrs = []
for m in mrs_raw:
    if m["state"] == "closed":
        continue
    if m["state"] == "merged" and not (m.get("merged_at") or "").startswith(today):
        continue
    detail = gitlab(f"/merge_requests/{m['iid']}") or {}
    pipe = (detail.get("head_pipeline") or {}).get("status")
    card = re.search(r"task-(\d+)", m["source_branch"])
    mrs.append({
        "iid": m["iid"], "url": m["web_url"], "state": m["state"], "pipeline": pipe,
        "title": m["title"], "source": m["source_branch"], "target": m["target_branch"],
        "card_id": int(card.group(1)) if card else None,
    })
mrs.sort(key=lambda x: x["iid"])

card_ids = {m["card_id"] for m in mrs if m["card_id"]}
# Card em foco: o da branch atual (task-NNNN) ou o passado em --card; entra mesmo sem MR (ainda não aberto).
focus = None
if "--card" in sys.argv:
    focus = int(sys.argv[sys.argv.index("--card") + 1])
else:
    branch = subprocess.run(["git", "branch", "--show-current"], capture_output=True, text=True).stdout.strip()
    m_branch = re.search(r"task-(\d+)", branch)
    focus = int(m_branch.group(1)) if m_branch else None
if focus:
    card_ids.add(focus)
card_ids = sorted(card_ids)
cards = {}
for cid in card_ids:
    d = redmine(f"/issues/{cid}.json")
    if d:
        cards[cid] = d["issue"]
    else:
        warnings.append(f"Redmine não respondeu para o card {cid}")

card_rows = [{
    "id": c["id"], "url": f"https://{RM}/issues/{c['id']}", "subject": c["subject"],
    "status": c["status"]["name"], "closed": bool(c.get("closed_on")), "estimated": c.get("estimated_hours"),
    "has_mr": any(m["card_id"] == c["id"] for m in mrs),
} for c in sorted(cards.values(), key=lambda c: c["id"])]

nxt = None
queue = redmine(f"/issues.json?assigned_to_id={uid}&status_id=1&limit=100&sort=id")
for c in (queue or {}).get("issues", []):
    has_mr = any(m["card_id"] == c["id"] for m in mrs)
    if c["id"] != focus and re.match(r"\[(Frontend|Backend|FullStack)", c["subject"]) and not has_mr:
        nxt = {"id": c["id"], "url": f"https://{RM}/issues/{c['id']}", "subject": c["subject"],
               "estimated": c.get("estimated_hours"), "description": c.get("description", "")}
        break

open_cards = [c for c in card_rows if not c["closed"]]
current = None
if open_cards:
    c = next((x for x in open_cards if x["id"] == focus), open_cards[-1])
    current = {**c, "mr": next((m for m in mrs if m["card_id"] == c["id"]), None)}
pending_merge = [c["id"] for c in open_cards if current and c["id"] != current["id"] and c["has_mr"]]

day = None
if "--day" in sys.argv:
    # Visão completa: todos os cards do usuário no projeto da pasta atual, criados ou fechados hoje.
    repo = os.path.basename(subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True).stdout.strip())
    project_id = {"auxilio-aluguel": 63}.get(repo)
    if "--project" in sys.argv:
        project_id = int(sys.argv[sys.argv.index("--project") + 1])
    if project_id is None:
        print(json.dumps({"error": f"projeto Redmine desconhecido para '{repo}'; passe --project <id>"}, ensure_ascii=False))
        sys.exit(1)
    pool = redmine(f"/issues.json?project_id={project_id}&assigned_to_id={uid}&status_id=*&limit=100&sort=id") or {}
    all_mrs = gitlab(f"/merge_requests?author_username={guser}&state=all&per_page=50") or []
    day = []
    for c in pool.get("issues", []):
        if not ((c.get("created_on") or "").startswith(today) or (c.get("closed_on") or "").startswith(today)):
            continue
        mid = next((m for m in all_mrs if re.search(rf"task-{c['id']}\b", m["source_branch"])), None)
        d = redmine(f"/issues/{c['id']}.json") or {}
        spent = (d.get("issue") or {}).get("spent_hours")
        pipe = None
        if mid:
            pipe = ((gitlab(f"/merge_requests/{mid['iid']}") or {}).get("head_pipeline") or {}).get("status")
        day.append({"id": c["id"], "url": f"https://{RM}/issues/{c['id']}", "subject": c["subject"], "status": c["status"]["name"],
                    "closed": bool(c.get("closed_on")), "estimated": c.get("estimated_hours"), "spent": spent,
                    "mr": mid and {"iid": mid["iid"], "url": mid["web_url"], "state": mid["state"], "pipeline": pipe}})
    day = {"project_id": project_id, "cards": day}

print(json.dumps({"today": today, "day": day, "current": current, "pending_merge": pending_merge, "next": nxt, "warnings": warnings}, ensure_ascii=False, indent=1))
