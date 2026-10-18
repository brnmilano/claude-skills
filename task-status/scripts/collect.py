#!/usr/bin/env python3
"""Coleta cards, MRs e a próxima tarefa da fila (só leitura). Imprime JSON."""
import json, os, re, subprocess, sys, urllib.parse
from datetime import datetime
from zoneinfo import ZoneInfo

HOME = os.path.expanduser("~/.claude")
RM = "redmine.verytecnologia.com.br"
RM_IP = "186.250.243.22"
GL_HOST = "https://gitlab.seds.com.br/api/v4"
GL_CA = os.path.expanduser("~/.config/glab-cli/gitlab.seds.com.br.pem")  # CA autoassinada da SEDS (a mesma do glab)
# Caminho do projeto no GitLab -> id do projeto no Redmine (fila e visão do dia).
REDMINE_PROJECTS = {"dni/auxilio-aluguel": 63, "dni/pmas/frontend": 61, "dni/pmas/backend": 61}


def gitlab_project_path():
    """Caminho do projeto GitLab (ex.: dni/pmas/frontend), lido do remote origin; padrão: Auxílio Aluguel."""
    url = subprocess.run(["git", "remote", "get-url", "origin"], capture_output=True, text=True).stdout.strip()
    m = re.search(r"gitlab\.seds\.com\.br[:/](.+?)(?:\.git)?$", url)
    return m.group(1) if m else "dni/auxilio-aluguel"


GL_PATH = gitlab_project_path()
GL = f"{GL_HOST}/projects/{urllib.parse.quote(GL_PATH, safe='')}"


def env(name):
    out = {}
    for line in open(f"{HOME}/{name}"):
        if "=" in line and not line.startswith("#"):
            k, v = line.strip().split("=", 1)
            out[k] = v.strip('"\'')
    return out


def get(url, header, resolve=None):
    # Verifica o TLS com a CA da SEDS no GitLab; o -k fica só como último recurso (sem a CA instalada).
    tls = ["--cacert", GL_CA] if url.startswith(GL_HOST) and os.path.exists(GL_CA) else ["-k"]
    cmd = ["curl", "-s", *tls, "--max-time", "25", "-H", header]
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
today = datetime.now(ZoneInfo("America/Sao_Paulo")).date().isoformat()  # fuso de SP: em UTC o dia vira às 21h
warnings = []


def is_today(iso):
    """O Redmine devolve UTC ('...Z'); compara o dia já no fuso de São Paulo."""
    if not iso:
        return False
    return datetime.fromisoformat(iso.replace("Z", "+00:00")).astimezone(ZoneInfo("America/Sao_Paulo")).date().isoformat() == today


def redmine(path):
    return get(f"https://{RM}{path}", f"X-Redmine-API-Key: {rm_key}", f"{RM}:443:{RM_IP}")


def gitlab(path):
    return get(f"{GL}{path}", f"PRIVATE-TOKEN: {gl_token}")


mrs_raw = gitlab(f"/merge_requests?author_username={guser}&state=all&order_by=updated_at&per_page=30")
if mrs_raw is None:
    warnings.append("GitLab não respondeu (VPN ligada?)")
    mrs_raw = []
elif not isinstance(mrs_raw, list):  # ex.: {"message": "404 Project Not Found"} ou token inválido
    warnings.append(f"GitLab recusou a consulta em {GL_PATH}: {mrs_raw.get('message') or mrs_raw.get('error')}")
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
queue_project = REDMINE_PROJECTS.get(GL_PATH)
# A fila é do projeto da pasta atual: card de outro projeto (ex.: Conseas) não entra.
queue = redmine(f"/issues.json?assigned_to_id={uid}&status_id=1&limit=100&sort=id" + (f"&project_id={queue_project}" if queue_project else ""))
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
    project_id = REDMINE_PROJECTS.get(GL_PATH)
    if "--project" in sys.argv:
        project_id = int(sys.argv[sys.argv.index("--project") + 1])
    if project_id is None:
        print(json.dumps({"error": f"projeto Redmine desconhecido para '{GL_PATH}'; passe --project <id>"}, ensure_ascii=False))
        sys.exit(1)
    pool = redmine(f"/issues.json?project_id={project_id}&assigned_to_id={uid}&status_id=*&limit=100&sort=id:desc&updated_on=%3E%3D{today}")  # só o que mexeu hoje; id:desc evita cortar os cards novos or {}
    all_mrs = gitlab(f"/merge_requests?author_username={guser}&state=all&per_page=50") or []
    day = []
    for c in pool.get("issues", []):
        if not (is_today(c.get("created_on")) or is_today(c.get("closed_on"))):
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
