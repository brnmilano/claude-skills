#!/usr/bin/env python3
"""Coleta cards (Redmine) e MRs (GitLab) do dia para a skill work-resume.

Uso: python3 collect.py <saida.json> [diario|semanal|mensal] [AAAA-MM-DD]
Janela (America/Sao_Paulo), sempre até agora quando o fim ainda não passou:
  diario  : 00:01 da data até agora (ou 23:59 se for data passada)
  semanal : domingo 00:01 a sábado 23:59 da semana que contém a data
  mensal  : dia 1 00:01 ao último dia do mês 23:59
Também coleta horas lançadas no Redmine por dia e marca feriados, sábados e domingos.
Nunca imprime chaves/tokens.
"""
import json, os, re, ssl, sys, urllib.parse, urllib.request
from calendar import monthrange
from datetime import date, datetime, timedelta, timezone

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


WEEKDAYS = ["segunda", "terça", "quarta", "quinta", "sexta", "sábado", "domingo"]


def easter(y):
    a, b, c = y % 19, y // 100, y % 100
    d, e = b // 4, b % 4
    g = (8 * b + 13) // 25
    h = (19 * a + b - d - g + 15) % 30
    j, k = c // 4, c % 4
    m = (a + 11 * h) // 319
    r = (2 * e + 2 * j - k - h + m + 32) % 7
    mo = (h - m + r + 90) // 25
    return date(y, mo, (h - m + r + mo + 19) % 32)


def holidays_for(y, extra):
    """Feriados nacionais + 09/07 (SP) + pontos facultativos; `extra` = {"MM-DD": nome} do work-resume.json."""
    e = easter(y)
    fixed = {(1, 1): "Confraternização Universal", (4, 21): "Tiradentes", (5, 1): "Dia do Trabalho",
             (7, 9): "Revolução Constitucionalista (SP)", (9, 7): "Independência", (10, 12): "N. Sra. Aparecida",
             (11, 2): "Finados", (11, 15): "Proclamação da República", (11, 20): "Consciência Negra",
             (12, 25): "Natal"}
    out = {date(y, m, d): {"name": n, "kind": "feriado"} for (m, d), n in fixed.items()}
    out[e - timedelta(days=2)] = {"name": "Sexta-feira Santa", "kind": "feriado"}
    for delta, n in ((-48, "Carnaval (segunda)"), (-47, "Carnaval (terça)"), (60, "Corpus Christi")):
        out[e + timedelta(days=delta)] = {"name": n, "kind": "facultativo"}
    for md, n in extra.items():
        mm, dd = md.split("-")
        out[date(y, int(mm), int(dd))] = {"name": n, "kind": "feriado"}
    return out


def paged(url_base, key, headers, gitlab=False, size=100):
    """Percorre todas as páginas (Redmine: offset/limit; GitLab: page/per_page)."""
    items, n = [], 0
    while True:
        sep = "&" if "?" in url_base else "?"
        page = f"{url_base}{sep}page={n // size + 1}&per_page={size}" if gitlab else f"{url_base}{sep}offset={n}&limit={size}"
        data, _ = get(page, headers, gitlab)
        chunk = data if gitlab else data[key]
        items += chunk
        n += len(chunk)
        if len(chunk) < size:
            return items


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
    args = sys.argv[2:]
    period = args.pop(0) if args and args[0] in ("diario", "semanal", "mensal") else "diario"
    day = datetime.strptime(args[0], "%Y-%m-%d").date() if args else datetime.now(TZ).date()
    if period == "semanal":
        first = day - timedelta(days=(day.weekday() + 1) % 7)  # domingo
        last = first + timedelta(days=6)
    elif period == "mensal":
        first, last = day.replace(day=1), day.replace(day=monthrange(day.year, day.month)[1])
    else:
        first = last = day
    start = datetime(first.year, first.month, first.day, 0, 1, tzinfo=TZ)
    now = datetime.now(TZ)
    end = min(now, datetime(last.year, last.month, last.day, 23, 59, tzinfo=TZ))
    try:
        prev = json.load(open(out_path))
        prev = prev if prev.get("window", {}).get("start") == start.isoformat() else {}
    except (OSError, ValueError):
        prev = {}
    result = {
        "period": period,
        "window": {"start": start.isoformat(), "end": end.isoformat(),
                   "first_day": first.isoformat(), "last_day": last.isoformat(),
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
                q = urllib.parse.urlencode({who: rm_user["id"], "status_id": "*",
                                            field: f"><{start_utc}|{end_utc}"})
                for i in paged(f"{REDMINE}/issues.json?{q}", "issues", h):
                    ids[i["id"]] = i
            # horas lançadas no período (por dia e por card)
            q = urllib.parse.urlencode({"user_id": rm_user["id"], "from": first.isoformat(), "to": last.isoformat()})
            entries = paged(f"{REDMINE}/time_entries.json?{q}", "time_entries", h)
            result["time_entries"] = [{"date": e["spent_on"], "hours": e["hours"],
                                       "issue_id": (e.get("issue") or {}).get("id"),
                                       "project": e["project"]["name"],
                                       "activity": (e.get("activity") or {}).get("name")} for e in entries]
            spent_by_card = {}
            for e in result["time_entries"]:
                if e["issue_id"]:
                    spent_by_card[e["issue_id"]] = round(spent_by_card.get(e["issue_id"], 0) + e["hours"], 2)
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
                    "spent_in_window": spent_by_card.get(iid, 0),
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
            q = urllib.parse.urlencode({"scope": "all", "author_id": me["id"],
                                        "updated_after": start.astimezone(timezone.utc).isoformat()})
            mrs = paged(f"{GITLAB}/merge_requests?{q}", None, h, gitlab=True)
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

    # ---------- Dias, feriados e horas extras ----------
    cfg = {}
    try:
        cfg = json.load(open(os.path.join(HOME, ".claude", "work-resume.json")))
    except (OSError, ValueError):
        pass
    hol = {}
    for y in {first.year, last.year}:
        hol.update(holidays_for(y, cfg.get("extra_holidays", {})))
    by_day = {}
    for e in result.get("time_entries", []):
        by_day[e["date"]] = round(by_day.get(e["date"], 0) + e["hours"], 2)
    result["days"], d = [], first
    while d <= last:
        wd, hd = d.weekday(), hol.get(d)
        hours = by_day.get(d.isoformat(), 0)
        extra = wd >= 5 or (hd is not None and hd["kind"] == "feriado")
        result["days"].append({"date": d.isoformat(), "weekday": WEEKDAYS[wd], "weekend": wd >= 5,
                               "holiday": hd["name"] if hd else None, "holiday_kind": hd["kind"] if hd else None,
                               "hours": hours, "overtime_hours": hours if extra else 0,
                               "future": datetime(d.year, d.month, d.day, tzinfo=TZ) > now})
        d += timedelta(days=1)
    result["overtime"] = {"hours": round(sum(x["overtime_hours"] for x in result["days"]), 2),
                          "days": [x["date"] for x in result["days"] if x["overtime_hours"]],
                          "total_hours": round(sum(x["hours"] for x in result["days"]), 2)}

    json.dump(result, open(out_path, "w"), ensure_ascii=False, indent=1)
    print(f'ok: {len(result["cards"])} cards, {len(result["mrs"])} MRs, {len(result["warnings"])} avisos -> {out_path}')
    for w in result["warnings"]:
        print("AVISO:", w)


if __name__ == "__main__":
    main()
