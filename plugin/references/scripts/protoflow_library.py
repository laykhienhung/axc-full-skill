"""ProtoFlow flow library — the deterministic half of /protoflow-guide.

Used by protoflow_compile.py:
  --library-draft   product-model.json → guides/library.json   (deterministic draft; the LLM then refines lanes,
                    platforms, inputs/outputs and summaries — never steps or branches the docs don't have)
  --library         validate guides/library.json → guides/library.html (template copy) + guides/library.md

Domain-neutral: nothing here assumes a product type. Standard library only. Shape: .claude/references/user-guide.md.
"""
import json, os, re
from collections import deque

ID_RE = re.compile(r"\b(?:REQ|BR|UC|FLOW|SCR|AC|ENT)-\d+")
REFS_IN_TEXT = re.compile(r"\s*\((?:[^()]*\b(?:REQ|BR|UC|FLOW|SCR|AC|ENT)-\d+[^()]*)\)")
SYSTEM_VERBS = ("check", "validate", "verify", "store", "save", "create", "record", "notify", "send", "compute", "calculate",
                "mark", "refuse", "reject", "add ", "append", "update", "set ", "generate", "process", "apply", "delete",
                "remove", "hide", "keep", "show", "recalculate", "log ", "copy", "move", "merge", "count", "sort", "filter",
                "kiểm", "lưu", "tạo", "gửi", "tính", "đánh dấu", "cập nhật", "sinh", "xoá", "xóa", "hiển thị")
EXCEPTION_LABELS = re.compile(r"^(no|not|false|fail|failed|error|invalid|refused?|rejected?|cancel(led)?|expired|deleted|closed|"
                              r"không|sai|lỗi|huỷ|hủy)\b", re.I)
USER_CHOICE = re.compile(r"\b(which|choose|chooses|pick|action|confirm|sort|remember|wants?|chọn|xác nhận|muốn)\b", re.I)
STATUS_WORDS = {"final": "final", "blocked": "blocked", "in-review": "in-review", "no-flow": "no-flow"}


def read(p):
    return open(p, encoding="utf-8").read() if os.path.exists(p) else ""


def clean(s):
    """Reader-facing text: drop "(BR-012)"-style references and stray ids, tidy spaces."""
    s = REFS_IN_TEXT.sub("", str(s or ""))
    s = ID_RE.sub("", s)
    return re.sub(r"\s{2,}", " ", s).replace(" ,", ",").replace(" .", ".").strip()


TITLES = {}     # FLOW/UC/SCR id → title, filled by build_draft so a label pointing at another item reads as its name


def resolve(s):
    """Reader text that cites other items ("Post - FLOW-001", "FLOW-053 or FLOW-054 has saved") → their titles, then clean."""
    s = re.sub(r"\b(?:FLOW|UC|SCR)-\d+\b", lambda m: f"“{TITLES[m.group(0)]}”" if m.group(0) in TITLES else m.group(0), str(s or ""))
    return clean(s)


def detect_language(text):
    vi = len(re.findall(r"[ăâđêôơưạảấầẩẫậắằẳẵặẹẻẽếềểễệỉịọỏốồổỗộớờởỡợụủứừửữựỳỵỷỹ]", text.lower()))
    return "vi" if vi > max(40, len(text) / 400) else "en"


def short_actor(a):
    a = re.sub(r"\s*\(.*?\)", "", a or "").strip()
    a = re.split(r"\s*(?:,| or | and | hoặc | và )\s*", a)[0].strip()
    return a[:1].upper() + a[1:] if a else ""


def words(s):
    return {w for w in re.findall(r"[a-zà-ỹ0-9]{3,}", (s or "").lower())}


# ------------------------------------------------------------------ draft
def feature_status(f, counts):
    c = counts.get(f["id"], {})
    if f["status"] in ("confirmed", "handed-off"):
        return "blocked" if c.get("handoff") == "blocked" else "final"
    if f["status"] in ("specced", "prototyped"):
        return "in-review"
    return "no-flow"


def blockers(f, counts, model_feature):
    out = [f"{d}: {t} (conflict)" for d, t in counts.get(f["id"], {}).get("conflicts", [])]
    confirmed = {r["id"] for r in model_feature["requirements"] if r.get("status") == "confirmed"}
    for kind in ("requirements", "rules", "flows", "screens", "acceptance"):
        for x in model_feature.get(kind, []):
            if x.get("type") == "UNKNOWN" and set(ID_RE.findall(x.get("text", "") + " " + x.get("source", ""))) & confirmed:
                out.append(f"{kind}.md: {x['title']}")
    return out


LIFECYCLE_RE = re.compile(r"lifecycle|status|state|vòng đời|trạng thái", re.I)


def lifecycle_defs(model):
    ents = {e["id"]: e["name"] for e in model["global"]["entities"]}
    out = []
    for t in model["global"]["dbDesign"]:
        for c in t["columns"]:
            m = re.search(r"check\s+in\s*\(([^)]*)\)", c.get("constraints", ""), re.I)
            if m and re.search(r"(status|state)$", c["name"], re.I):
                states = [s.strip().strip("'\"") for s in m.group(1).split(",") if s.strip()]
                if len(states) >= 2:
                    out.append({"id": f"{t['table']}.{c['name']}", "entity": ents.get(t["entity"], t["table"]),
                                "entityId": t["entity"], "states": states, "transitions": []})
    # transitions from lifecycle-like FLOW graphs whose node labels name the states
    for f in model["features"]:
        for fl in f["flows"]:
            g = fl.get("graph")
            if not g or not LIFECYCLE_RE.search(fl["title"]):
                continue
            lab = {n["id"]: n["label"].strip().lower() for n in g["nodes"]}
            for lc in out:
                st = {s.lower(): s for s in lc["states"]}
                hits = [e for e in g["edges"] if lab.get(e["from"], "").split(",")[0] in st and lab.get(e["to"], "").split(",")[0] in st]
                for e in hits:
                    tr = {"from": st[lab[e["from"]].split(",")[0]], "to": st[lab[e["to"]].split(",")[0]], "label": clean(e["label"])}
                    if not any(x["from"] == tr["from"] and x["to"] == tr["to"] for x in lc["transitions"]):
                        lc["transitions"].append(tr)
                if hits:
                    lc.setdefault("flows", []).append(fl["id"])
    return out


def draft_flow(fl, feat, model, lifecycles):
    screens = {s["id"]: s for s in feat["screens"] if s.get("id")}
    ucs = [u for u in feat.get("useCases", []) if u.get("id") and u.get("status") != "rejected"]
    tw = words(fl["title"] + " " + " ".join(fl.get("steps", [])))
    uc = max(ucs, key=lambda u: len(tw & words(u["title"] + " " + u.get("goal", ""))), default=None)
    actor = short_actor(uc["actor"]) if uc else "User"
    lanes = [{"id": "input", "name": "Input", "kind": "input"}, {"id": "actor", "name": actor or "User", "kind": "actor"},
             {"id": "system", "name": "System", "kind": "system"}, {"id": "output", "name": "Output", "kind": "output"}]
    scr_titles = [screens[s]["title"] for s in fl.get("screens", []) if s in screens]
    first_screen = scr_titles[0] if scr_titles else ""

    g = fl.get("graph")
    # a state machine (lifecycle-titled FLOW without decisions) is drawn as a state diagram, not a swimlane
    if g and g.get("nodes") and LIFECYCLE_RE.search(fl["title"]) and not any(n["kind"] == "decision" for n in g["nodes"]):
        return {"id": fl["id"], "title": resolve(fl["title"]), "summary": resolve(fl.get("trigger") or fl.get("text", "")),
                "draft": fl.get("status") == "proposed", "view": "lifecycle",
                "lanes": [{"id": "system", "name": "System", "kind": "system"}],
                "nodes": [{"id": n["id"], "label": resolve(n["label"]), "kind": "state", "lane": "system", "ref": fl["id"]} for n in g["nodes"]],
                "edges": [{"from": e["from"], "to": e["to"], "label": resolve(e["label"])} for e in g["edges"]],
                "inputs": [], "steps": [], "outputs": [], "terms": [], "lifecycle": None, "team": team_detail(fl, feat)}
    if g and g.get("nodes"):
        nodes = [{"id": n["id"], "label": resolve(n["label"]), "kind": "decision" if n["kind"] == "decision" else "step"} for n in g["nodes"]]
        edges = [{"from": e["from"], "to": e["to"], "label": resolve(e["label"])} for e in g["edges"]]
    else:
        steps = [resolve(s) for s in fl.get("steps", []) if resolve(s)]
        nodes = [{"id": f"S{i + 1}", "label": s, "kind": "step"} for i, s in enumerate(steps)]
        edges = [{"from": f"S{i + 1}", "to": f"S{i + 2}", "label": ""} for i in range(len(steps) - 1)]
    if not nodes:
        return None
    ids = {n["id"] for n in nodes}
    has_in = {e["to"] for e in edges}
    has_out = {e["from"] for e in edges}
    roots = [n["id"] for n in nodes if n["id"] not in has_in] or [nodes[0]["id"]]
    leaves = [n["id"] for n in nodes if n["id"] not in has_out]
    for n in nodes:
        # the trigger (first node) is the actor's; a decision is a system check unless it reads as the actor's choice
        if n["kind"] == "decision":
            sysy = not USER_CHOICE.search(n["label"])
        else:
            sysy = n["id"] not in roots and n["label"].lower().startswith(SYSTEM_VERBS)
        n["lane"] = "system" if sysy else "actor"
        n["platform"] = "System (auto)" if sysy else ("Web" if n["kind"] == "step" else "")
        n["screen"] = first_screen if n["lane"] == "actor" and n["kind"] == "step" else ""
        n["ref"] = fl["id"]
    start, end = "START", "END"
    while start in ids: start += "_"
    while end in ids: end += "_"
    nodes.insert(0, {"id": start, "label": "Start", "kind": "start", "lane": "actor", "platform": "", "screen": "", "ref": ""})
    edges = [{"from": start, "to": r, "label": ""} for r in roots] + edges
    if leaves:
        nodes.append({"id": end, "label": "End", "kind": "end", "lane": "actor", "platform": "", "screen": "", "ref": ""})
        edges += [{"from": l, "to": end, "label": ""} for l in leaves]

    # exception phase: nodes reachable from Start only through an exception-labelled edge
    adj = {}
    for e in edges:
        if not EXCEPTION_LABELS.match(e["label"] or ""):
            adj.setdefault(e["from"], []).append(e["to"])
    seen, q = {start}, deque([start])
    while q:
        for nx in adj.get(q.popleft(), []):
            if nx not in seen:
                seen.add(nx); q.append(nx)
    for n in nodes:
        if n["id"] not in seen and n["kind"] not in ("start", "end"):
            n["phase"] = "exception"

    # inputs: entities the flow's screens bind to — those the flow names first, at most three (the LLM trims further)
    ents = {e["id"]: e["name"] for e in model["global"]["entities"]}
    used = []
    for sid in fl.get("screens", []):
        for fld in screens.get(sid, {}).get("fields", []):
            for eid in re.findall(r"ENT-\d+", fld.get("bind", "")):
                if eid not in used:
                    used.append(eid)
    said = " ".join([fl["title"]] + [n["label"] for n in nodes]).lower()
    used.sort(key=lambda eid: ents.get(eid, "").lower() not in said)
    entry = next((n for n in nodes if n["kind"] in ("step", "decision")), None)
    inputs = [{"no": f"I-{i + 1}", "input": ents.get(eid, eid), "type": "Data", "goesTo": entry["label"] if entry else "",
               "node": entry["id"] if entry else "", "ref": eid} for i, eid in enumerate(used[:3])]
    outputs = []
    for i, l in enumerate(leaves):
        n = next(x for x in nodes if x["id"] == l)
        when = next((e["label"] for e in edges if e["to"] == l and e["label"]), "")
        outputs.append({"no": f"O-{i + 1}", "output": n["label"], "when": when, "node": l})
    step_rows = [{"step": n["label"], "role": actor if n["lane"] == "actor" else "System (auto)", "screen": n["screen"] or ""}
                 for n in nodes if n["kind"] == "step"]

    terms = [g["term"] for g in model["global"]["glossary"]
             if re.search(r"\b" + re.escape(g["term"].lower()) + r"\b", " ".join(n["label"] for n in nodes).lower())]
    said = " ".join([fl["title"]] + [n["label"] for n in nodes]).lower()
    lc = next((l["id"] for l in lifecycles if fl["id"] in l.get("flows", [])), None) \
        or next((l["id"] for l in lifecycles if l["entityId"] in feat.get("entities", []) and l["entity"].lower() in said), None)
    return {"id": fl["id"], "title": resolve(fl["title"]), "summary": resolve(fl.get("trigger") or fl.get("text", "")),
            "draft": fl.get("status") == "proposed", "lanes": lanes, "nodes": nodes, "edges": edges,
            "inputs": inputs, "steps": step_rows, "outputs": outputs, "terms": terms, "lifecycle": lc,
            "team": team_detail(fl, feat)}


def team_detail(fl, feat):
    """Rules the flow cites, requirements governed by those rules, ACs verifying those requirements — verbatim, with ids."""
    rules = [r for r in feat["rules"] if r.get("id") in fl.get("rules", []) and r.get("status") != "rejected"]
    rids = {r["id"] for r in rules}
    reqs = [r for r in feat["requirements"] if r.get("id") and r.get("status") != "rejected" and set(r.get("rules", [])) & rids] \
        or [r for r in feat["requirements"] if r.get("id") and r.get("status") != "rejected"]
    qids = {r["id"] for r in reqs}
    acc = [a for a in feat["acceptance"] if a.get("id") and a.get("status") != "rejected" and set(a.get("verifiesAll") or [a.get("verifies")]) & qids]
    item = lambda x, text: {"id": x["id"], "title": x["title"], "text": text, "draft": x.get("status") == "proposed"}
    return {"reqs": [item(r, r.get("text", "")) for r in reqs], "rules": [item(r, r.get("text", "")) for r in rules],
            "acceptance": [item(a, a.get("gherkin") or a.get("text", "")) for a in acc]}


def build_draft(P, model, extra):
    counts = extra.get("counts", {})
    lifecycles = lifecycle_defs(model)
    product = model["project"]
    app = read(os.path.join(P, "prototype", "app.js"))
    m = re.search(r'BRAND\s*=\s*\{\s*name:\s*"([^"]+)"', app)
    if m:
        product = m.group(1)
    features, mods = [], {}
    by_id = {f["id"]: f for f in model["features"]}
    TITLES.clear()
    for f in model["features"]:
        for k in ("flows", "useCases", "screens"):
            TITLES.update({x["id"]: clean(x["title"]) for x in f.get(k, []) if x.get("id") and x.get("title")})
    order = [s["id"] for s in extra.get("scope", []) if s["status"] != "rejected"]
    for fid in order + [f["id"] for f in model["features"] if f["id"] not in order]:
        scope = next((s for s in extra.get("scope", []) if s["id"] == fid), None)
        f = by_id.get(fid)
        if not f and (not scope or scope["status"] != "confirmed"):
            continue
        status = feature_status(f, counts) if f else "no-flow"
        flows = []
        if f and status != "no-flow":
            flows = [d for d in (draft_flow(fl, f, model, lifecycles) for fl in f["flows"]
                                 if fl.get("id", "").startswith("FLOW-") and fl.get("status") != "rejected") if d]
        module = f["module"] if f else "Ungrouped"
        mods.setdefault(module, []).append(fid)
        features.append({"id": fid, "title": (f["title"] if f else fid.replace("-", " ").capitalize()), "module": module,
                         "status": status, "summary": clean(scope["text"]) if scope else "",
                         "blockers": blockers(f, counts, f) if f and status == "blocked" else [], "flows": flows})
    lang_src = extra.get("grounding", "") + " " + model.get("context", "")
    return {"project": model["project"], "product": product, "generated": model["generated"], "language": detect_language(lang_src),
            "modules": [{"id": re.sub(r"[^a-z0-9]+", "-", k.lower()).strip("-") or "ungrouped", "name": k, "features": v} for k, v in mods.items()],
            "features": features, "glossary": [{"term": g["term"], "def": g["def"]} for g in model["global"]["glossary"]],
            "lifecycles": [{k: v for k, v in l.items() if k != "entityId"} for l in lifecycles]}


def write_draft(P, model, extra, force=False):
    lib = build_draft(P, model, extra)
    G = os.path.join(P, "guides")
    os.makedirs(G, exist_ok=True)
    target = os.path.join(G, "library.json")
    path = target if (force or not os.path.exists(target)) else os.path.join(G, ".library.draft.json")
    open(path, "w", encoding="utf-8").write(json.dumps(lib, indent=1, ensure_ascii=False) + "\n")
    n = sum(len(f["flows"]) for f in lib["features"])
    rep = {"file": os.path.relpath(path, P).replace("\\", "/"), "features": len(lib["features"]), "flows": n,
           "byStatus": {s: sum(1 for f in lib["features"] if f["status"] == s) for s in STATUS_WORDS},
           "lifecycles": len(lib["lifecycles"]), "language": lib["language"]}
    if path != target:                                  # a refined library exists: say which flows the docs changed
        try:
            old = json.loads(read(target))
        except ValueError:
            old = {"features": []}
        sig = lambda fl: json.dumps([sorted((x["id"], x["label"]) for x in fl["nodes"] if x["kind"] not in ("start", "end")),
                                     sorted((e["from"], e["to"], e["label"]) for e in fl["edges"])], ensure_ascii=False)
        flows = lambda L: {fl["id"]: (f["id"], fl) for f in L.get("features", []) for fl in f.get("flows", [])}
        # the refined copy may have relabelled nodes, so compare the new draft with the previous draft when there is one
        prev = os.path.join(G, ".library.prev.json")
        base = flows(json.loads(read(prev))) if os.path.exists(prev) else flows(old)
        new = flows(lib)
        rep["diff"] = {"new": sorted(k for k in new if k not in flows(old)),
                       "changed": sorted(k for k in new if k in base and sig(new[k][1]) != sig(base[k][1])),
                       "removed": sorted(k for k in flows(old) if k not in new),
                       "featureStatus": {f["id"]: f["status"] for f in lib["features"]
                                         if f["status"] != next((o["status"] for o in old.get("features", []) if o["id"] == f["id"]), None)}}
    else:
        open(os.path.join(G, ".library.prev.json"), "w", encoding="utf-8").write(json.dumps(lib, ensure_ascii=False) + "\n")
    return rep


# ------------------------------------------------------------------ validate
READER_FIELDS_FLOW = ("title", "summary")


def validate(lib):
    errs = []
    def leak(where, s):
        if s and ID_RE.search(str(s)):
            errs.append(f"{where}: reader text contains a spec id: {ID_RE.search(str(s)).group(0)}")
    for k in ("project", "product", "generated", "language", "modules", "features"):
        if k not in lib:
            errs.append(f"missing top-level key: {k}")
    if lib.get("language") not in ("en", "vi"):
        errs.append("language must be \"en\" or \"vi\"")
    fids = {f["id"] for f in lib.get("features", [])}
    for m in lib.get("modules", []):
        for fid in m.get("features", []):
            if fid not in fids:
                errs.append(f"module {m.get('name')}: unknown feature {fid}")
    lcs = {l["id"] for l in lib.get("lifecycles", [])}
    for l in lib.get("lifecycles", []):
        for t in l.get("transitions", []):
            if t["from"] not in l["states"] or t["to"] not in l["states"]:
                errs.append(f"lifecycle {l['id']}: transition {t['from']}→{t['to']} uses an unknown state")
    for f in lib.get("features", []):
        if f.get("status") not in STATUS_WORDS:
            errs.append(f"{f['id']}: status must be one of {', '.join(STATUS_WORDS)}")
        leak(f"{f['id']}.summary", f.get("summary"))
        for fl in f.get("flows", []):
            w = f"{f['id']}/{fl.get('id')}"
            for k in READER_FIELDS_FLOW:
                leak(f"{w}.{k}", fl.get(k))
            lanes = {l["id"] for l in fl.get("lanes", [])}
            nodes = {n["id"]: n for n in fl.get("nodes", [])}
            if not nodes:
                errs.append(f"{w}: no nodes")
                continue
            for n in nodes.values():
                if n.get("lane") not in lanes:
                    errs.append(f"{w}: node {n['id']} is in unknown lane {n.get('lane')}")
                if n.get("kind") not in (("state",) if fl.get("view") == "lifecycle" else ("start", "end", "step", "decision", "data")):
                    errs.append(f"{w}: node {n['id']} has unknown kind {n.get('kind')}")
                for k in ("label", "screen", "platform"):
                    leak(f"{w}.node {n['id']}.{k}", n.get(k))
            out = {}
            for e in fl.get("edges", []):
                if e["from"] not in nodes or e["to"] not in nodes:
                    errs.append(f"{w}: edge {e['from']}→{e['to']} points at a missing node")
                    continue
                out.setdefault(e["from"], []).append(e)
                leak(f"{w}.edge {e['from']}→{e['to']}.label", e.get("label"))
            if fl.get("view") == "lifecycle":
                continue                                    # a state diagram has no start / end / decision rules
            for n in nodes.values():
                if n["kind"] == "decision":
                    o = out.get(n["id"], [])
                    if len(o) < 2:
                        errs.append(f"{w}: decision {n['id']} \"{n['label']}\" needs ≥2 outgoing branches (has {len(o)})")
                    elif any(not (e.get("label") or "").strip() for e in o):
                        errs.append(f"{w}: decision {n['id']} \"{n['label']}\" has an unlabelled branch")
            starts = [n for n in nodes.values() if n["kind"] == "start"]
            ends = {n["id"] for n in nodes.values() if n["kind"] == "end"}
            if not starts or not ends:
                errs.append(f"{w}: needs at least one start and one end node")
            for s in starts:
                seen, q = {s["id"]}, deque([s["id"]])
                while q:
                    for e in out.get(q.popleft(), []):
                        if e["to"] not in seen:
                            seen.add(e["to"]); q.append(e["to"])
                if not seen & ends:
                    errs.append(f"{w}: start {s['id']} never reaches an end")
            for k, arr in (("inputs", "input"), ("outputs", "output")):
                for r in fl.get(k, []):
                    leak(f"{w}.{k} {r.get('no')}", r.get(arr))
                    if r.get("node") and r["node"] not in nodes:
                        errs.append(f"{w}.{k} {r.get('no')}: node {r['node']} does not exist")
            for r in fl.get("steps", []):
                leak(f"{w}.steps", r.get("step"))
            if fl.get("lifecycle") and fl["lifecycle"] not in lcs:
                errs.append(f"{w}: unknown lifecycle {fl['lifecycle']}")
    for g in lib.get("glossary", []):
        leak(f"glossary {g.get('term')}", g.get("def"))
    return errs


# ------------------------------------------------------------------ render
def render_md(lib):
    T = (lambda en, vi: vi if lib.get("language") == "vi" else en)
    st = {"final": T("Final", "Chốt"), "blocked": T("Blocked", "Đang vướng"), "in-review": T("In review", "Đang duyệt"),
          "no-flow": T("No flow yet", "Chưa có flow")}
    esc = lambda s: str(s or "").replace("|", "\\|").replace("\n", "<br>")
    tbl = lambda head, rows: ("| " + " | ".join(head) + " |\n|" + "|".join("---" for _ in head) + "|\n" +
                              "\n".join("| " + " | ".join(esc(c) for c in r) + " |" for r in rows) + "\n") if rows else ""
    md = [f"# {lib['product']} — {T('Flow library', 'Thư viện flow')}", "",
          f"_{T('Generated', 'Sinh ngày')} {lib['generated']} · /protoflow-guide · {T('derived — do not edit', 'tài liệu sinh — không sửa tay')}_", ""]
    for m in lib["modules"]:
        md += [f"## {m['name']}", ""]
        for fid in m["features"]:
            f = next(x for x in lib["features"] if x["id"] == fid)
            md += [f"- **{f['title']}** — {st[f['status']]}" + (f" · {f['summary']}" if f.get("summary") else "")]
            md += [f"  - [{fl['title']}](#{fl['id'].lower()})" for fl in f["flows"]]
        md += [""]
    lcs = {l["id"]: l for l in lib.get("lifecycles", [])}
    for f in lib["features"]:
        for fl in f["flows"]:
            lane = {l["id"]: l["name"] for l in fl["lanes"]}
            md += [f'<a id="{fl["id"].lower()}"></a>', f"## {fl['title']}", "", f"_{f['title']} · {st[f['status']]}_", ""]
            if fl.get("summary"):
                md += [fl["summary"], ""]
            if fl.get("view") == "lifecycle":
                md += ["```mermaid", "stateDiagram-v2"] + [f'  {n["id"]} : {n["label"]}' for n in fl["nodes"]]
                md += [f'  {e["from"]} --> {e["to"]}' + (f': {e["label"]}' if e.get("label") else "") for e in fl["edges"]] + ["```", ""]
                continue
            md += ["```mermaid", "flowchart TD"]
            for l in fl["lanes"]:
                inner = [n for n in fl["nodes"] if n["lane"] == l["id"]]
                if not inner:
                    continue
                md += [f'  subgraph {l["id"]}["{l["name"]}"]']
                for n in inner:
                    lab = n["label"].replace('"', "'") + (f"<br/><small>{n['platform']}</small>" if n.get("platform") else "")
                    shape = {"decision": ('{"', '"}'), "start": ('(["', '"])'), "end": ('(["', '"])'), "data": ('[/"', '"/]')}.get(n["kind"], ('["', '"]'))
                    md += [f'    {n["id"]}{shape[0]}{lab}{shape[1]}']
                md += ["  end"]
            for r in fl.get("inputs", []):
                if r.get("node"):
                    md += [f'  {r["no"].replace("-", "_")}[/"{r["input"]}"/] --> {r["node"]}']
            for e in fl["edges"]:
                md += [f'  {e["from"]} -->' + (f'|{e["label"]}|' if e.get("label") else "") + f' {e["to"]}']
            md += ["```", ""]
            md += [f"**{T('Input', 'Đầu vào')}**", "", tbl(["#", T("Input", "Đầu vào"), T("Type", "Loại"), T("Goes to", "Đi vào bước")],
                                                           [[r["no"], r["input"], r.get("type", ""), r.get("goesTo", "")] for r in fl.get("inputs", [])])]
            md += [f"**{T('Steps and screens', 'Bước ↔ màn hình')}**", "", tbl([T("Step", "Bước"), T("Role", "Vai trò"), T("Screen", "Màn hình")],
                                                                                [[r["step"], r.get("role", ""), r.get("screen", "")] for r in fl.get("steps", [])])]
            md += [f"**{T('Output', 'Đầu ra')}**", "", tbl(["#", T("Output", "Đầu ra"), T("When", "Điều kiện")],
                                                           [[r["no"], r["output"], r.get("when", "")] for r in fl.get("outputs", [])])]
            lc = lcs.get(fl.get("lifecycle"))
            if lc:
                md += [f"**{T('Lifecycle', 'Vòng đời trạng thái')} — {lc['entity']}**", "", " → ".join(lc["states"]), ""]
                md += [f"- {t['from']} → {t['to']}" + (f" ({t['label']})" if t.get("label") else "") for t in lc.get("transitions", [])] + [""]
            terms = [g for g in lib.get("glossary", []) if g["term"] in fl.get("terms", [])]
            if terms:
                md += [f"**{T('Terms', 'Thuật ngữ')}**", "", tbl([T("Term", "Thuật ngữ"), T("Meaning", "Nghĩa")], [[g["term"], g["def"]] for g in terms])]
            tm = fl.get("team", {})
            if any(tm.get(k) for k in ("reqs", "rules", "acceptance")):
                md += [f"<details><summary>{T('Team view — spec detail', 'Góc nhìn đội dự án — chi tiết spec')}</summary>", ""]
                for k, head in (("reqs", T("Requirements", "Yêu cầu")), ("rules", T("Business rules", "Quy tắc")), ("acceptance", T("Acceptance", "Nghiệm thu"))):
                    if tm.get(k):
                        md += [f"**{head}**", ""] + [f"- **{x['id']} {x['title']}**" + (" _(draft)_" if x.get("draft") else "") + f"  \n  {esc(x['text'])}" for x in tm[k]] + [""]
                md += ["</details>", ""]
    return "\n".join(md) + "\n"


def validate_and_render(P, ROOT):
    G = os.path.join(P, "guides")
    src = os.path.join(G, "library.json")
    if not os.path.exists(src):
        return {"ok": False, "errors": ["guides/library.json is missing — run --library-draft first"]}
    try:
        lib = json.loads(read(src))
    except ValueError as e:
        return {"ok": False, "errors": [f"guides/library.json is not valid JSON: {e}"]}
    errs = validate(lib)
    if errs:
        return {"ok": False, "errors": errs[:60], "errorCount": len(errs)}
    tpl = read(os.path.join(ROOT, "references", "templates", "library.html"))
    js = json.dumps(lib, ensure_ascii=False, separators=(",", ":")).replace("</script", "<\\/script")
    html, n = re.subn(r'(?m)(^<script id="library">)(.*?)(</script>)', lambda m: m.group(1) + "\nconst LIBRARY = " + js + ";\n" + m.group(3),
                      tpl, count=1, flags=re.S)
    if not n:
        return {"ok": False, "errors": [".claude/references/templates/library.html has no <script id=\"library\"> block"]}
    html = re.sub(r"<title>.*?</title>", f"<title>{lib['product']} — {'Thư viện flow' if lib['language'] == 'vi' else 'Flow library'}</title>", html, count=1)
    open(os.path.join(G, "library.html"), "w", encoding="utf-8").write(html)
    open(os.path.join(G, "library.md"), "w", encoding="utf-8").write(render_md(lib))
    draft = os.path.join(G, ".library.draft.json")
    if os.path.exists(draft):                           # merged: this draft is the baseline the next diff compares with
        os.replace(draft, os.path.join(G, ".library.prev.json"))
    flows = sum(len(f["flows"]) for f in lib["features"])
    return {"ok": True, "files": ["guides/library.html", "guides/library.md"], "features": len(lib["features"]), "flows": flows,
            "byStatus": {s: sum(1 for f in lib["features"] if f["status"] == s) for s in STATUS_WORDS}}
