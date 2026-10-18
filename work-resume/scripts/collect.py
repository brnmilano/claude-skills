#!/usr/bin/env python3
"""Coleta cards (Redmine) e MRs (GitLab) do dia para a skill work-resume.

Uso: python3 collect.py <saida.json> [AAAA-MM-DD]
Janela: de 00:01 (America/Sao_Paulo) da data até agora (ou 23:59 se for data passada).
Nunca imprime chaves/tokens.
"""
import json, os, re, ssl, sys, urllib.parse, urllib.request
from datetime import datetime, timedelta, timezone

REDMINE = "https://redmine.verytecnologia.com.br"
GITLAB = "https://gitlab.seds.com.br/api/v4"
TZ = timezone(timedelta(hours=-3))  # America/Sao_Paulo (sem horário de verão desde 2019)
HOME = os.path.expanduser("~")


def load_env(path):
    out = {}
    try:
        for line in open(path):
            if "=" in line and not line.lstrip().startswith("#"):
                k, v = line.strip().split("=", 1)
                out[k] = v.strip().strip('"').strip("'")
    except FileNotFoundError:
        pass
    return out


def ctx_for(host_is_gitlab):
    ctx = ssl.create_default_context()
    pem = os.path.join(HOME, ".certs", "gitlab-seds.pem")
    if host_is_gitlab and os.path.exists(pem):
        ctx.load_verify_locations(pem)
    return ctx


def get(url, headers, gitlab=False):
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, context=ctx_for(gitlab), timeout=25) as r:
        return json.load(r), r.headers


def parse_dt(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00")).astimezone(TZ) if s else None


def hours_between(a, b):
    return round((b - a).total_seconds() / 3600, 2) if a and b else None


def link_card(mr, cards):
    """Liga um MR a um card do dia. Devolve (card_id, origem) ou (None, None).

    Ordem de confiança: 1) `task-NNNN` na branch; 2) link `issues/NNNN` de um card
    do dia no título/descrição; 3) identificador camelCase do título (ex.: `maxSelections`)
    que aparece na descrição de exatamente um card do dia. A origem fica em `card_link`
    para o relatório poder sinalizar o que foi inferido.
    """
    mt = re.search(r"task-(\d+)", mr["source_branch"])
    if mt:
        return int(mt.group(1)), "branch"
    for i in re.findall(r"issues/(\d+)", mr["title"] + " " + mr["description"]):
        if int(i) in cards:
            return int(i), "issue"
    votes = set()
    for tok in set(re.findall(r"\b[A-Za-z]*[a-z][A-Z][A-Za-z]*\b", mr["title"])):
        owners = [cid for cid, c in cards.items() if tok in c.get("description", "")]
        if len(owners) == 1:
            votes.add(owners[0])
    if len(votes) == 1:
        return votes.pop(), "keyword"
    return None, None


def main():
    out_path = sys.argv[1]
    day = datetime.strptime(sys.argv[2], "%Y-%m-%d").date() if len(sys.argv) > 2 else datetime.now(TZ).date()
    start = datetime(day.year, day.month, day.day, 0, 1, tzinfo=TZ)
    now = datetime.now(TZ)
    end = now if day == now.date() else datetime(day.year, day.month, day.day, 23, 59, tzinfo=TZ)
    try:
        prev = json.load(open(out_path))
        prev = prev if prev.get("window", {}).get("start") == start.isoformat() else {}
    except (OSError, ValueError):
        prev = {}
    result = {
        "window": {"start": start.isoformat(), "end": end.isoformat(),
                   "elapsed_hours": hours_between(start, end)},
        "warnings": [], "cards": [], "mrs": [],
    }

    # ---------- Redmine ----------
    try:
        rm_key = load_env(os.path.join(HOME, ".claude", "redmine.env")).get("REDMINE_API_KEY")
        rm_user = None
        if not rm_key:
            result["warnings"].append("redmine.env ausente: criar ~/.claude/redmine.env com REDMINE_API_KEY=...")
        else:
            h = {"X-Redmine-API-Key": rm_key}
            me, _ = get(f"{REDMINE}/users/current.json", h)
            rm_user = me["user"]
            result["redmine_user"] = {"id": rm_user["id"], "name": f'{rm_user["firstname"]} {rm_user["lastname"]}'}
            start_utc = start.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            end_utc = end.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            ids = {}
            # criados no dia (autor) e concluídos no dia (atribuído ao usuário)
            for field, who in (("created_on", "author_id"), ("closed_on", "assigned_to_id")):
                q = urllib.parse.urlencode({who: rm_user["id"], "status_id": "*", "limit": 100,
                                            field: f"><{start_utc}|{end_utc}"})
                data, _ = get(f"{REDMINE}/issues.json?{q}", h)
                for i in data["issues"]:
                    ids[i["id"]] = i
            for iid in sorted(ids):
                d, _ = get(f"{REDMINE}/issues/{iid}.json?include=journals", h)
                i = d["issue"]
                created, closed = parse_dt(i.get("created_on")), parse_dt(i.get("closed_on"))
                result["cards"].append({
                    "id": iid, "url": f"{REDMINE}/issues/{iid}", "project": i["project"]["name"],
                    "subject": i["subject"], "status": i["status"]["name"],
                    "created_on": created.isoformat(), "closed_on": closed.isoformat() if closed else None,
                    "created_today": start <= created <= end,
                    "closed_today": bool(closed and start <= closed <= end),
                    "estimated_hours": i.get("estimated_hours"), "spent_hours": i.get("spent_hours"),
                    "done_ratio": i.get("done_ratio"), "description": i.get("description", ""),
                })
    except OSError as e:  # rede/VPN: reaproveita os cards da coleta anterior, se houver
        result["warnings"].append(f"Redmine inacessível ({e.__class__.__name__}); " + ("usando cards da coleta anterior" if prev.get("cards") else "cards não coletados"))
        result["cards"] = prev.get("cards", [])
        if prev.get("redmine_user"):
            result["redmine_user"] = prev["redmine_user"]

    # ---------- GitLab ----------
    gl_token = load_env(os.path.join(HOME, ".claude", "gitlab.env")).get("GITLAB_TOKEN")
    if not gl_token:
        result["warnings"].append("gitlab.env ausente: criar ~/.claude/gitlab.env com GITLAB_TOKEN=... (escopo api); MRs não coletados")
    else:
        try:
            h = {"PRIVATE-TOKEN": gl_token}
            me, _ = get(f"{GITLAB}/user", h, gitlab=True)
            result["gitlab_user"] = me["username"]
            q = urllib.parse.urlencode({"scope": "all", "author_id": me["id"], "per_page": 100,
                                        "updated_after": start.astimezone(timezone.utc).isoformat()})
            mrs, _ = get(f"{GITLAB}/merge_requests?{q}", h, gitlab=True)
            for m in mrs:
                created, merged = parse_dt(m["created_at"]), parse_dt(m.get("merged_at"))
                created_today = start <= created <= end
                merged_today = bool(merged and start <= merged <= end)
                if not (created_today or merged_today):
                    continue
                pid, iid = m["project_id"], m["iid"]
                files = []
                try:
                    diffs, _ = get(f"{GITLAB}/projects/{pid}/merge_requests/{iid}/diffs?per_page=100", h, gitlab=True)
                    for df in diffs:
                        adds = sum(1 for l in df.get("diff", "").splitlines() if l.startswith("+") and not l.startswith("+++"))
                        dels = sum(1 for l in df.get("diff", "").splitlines() if l.startswith("-") and not l.startswith("---"))
                        files.append({"path": df["new_path"], "new": df.get("new_file", False), "added": adds, "removed": dels})
                except Exception as e:  # diff indisponível não derruba o relatório
                    result["warnings"].append(f"MR !{iid}: diffs indisponíveis ({e.__class__.__name__})")
                path = m["web_url"].split("/-/")[0].split("://", 1)[-1].split("/", 1)[-1]
                result["mrs"].append({
                    "iid": iid, "url": m["web_url"], "title": m["title"], "state": m["state"],
                    "project": path.rsplit("/", 1)[-1], "project_path": path,
                    "source_branch": m["source_branch"], "target_branch": m["target_branch"],
                    "created_at": created.isoformat(), "merged_at": merged.isoformat() if merged else None,
                    "created_today": created_today, "merged_today": merged_today,
                    "lead_hours": hours_between(created, merged), "description": m.get("description") or "",
                    "files": files,
                    "lines_added": sum(f["added"] for f in files), "lines_removed": sum(f["removed"] for f in files),
                })
            known = {c["id"]: c for c in result["cards"]}
            for m in result["mrs"]:
                m["card_id"], m["card_link"] = link_card(m, known)
        except OSError as e:  # rede/VPN: não derruba o relatório
            result["warnings"].append(f"GitLab inacessível ({e.__class__.__name__}: {e}); MRs não coletados")

    json.dump(result, open(out_path, "w"), ensure_ascii=False, indent=1)
    print(f'ok: {len(result["cards"])} cards, {len(result["mrs"])} MRs, {len(result["warnings"])} avisos -> {out_path}')
    for w in result["warnings"]:
        print("AVISO:", w)


if __name__ == "__main__":
    main()
