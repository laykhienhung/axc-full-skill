#!/usr/bin/env python3
"""ProtoFlow compiler — the deterministic half of /protoflow-prototype (and /protoflow-handoff, /protoflow-status).

Reads protoflow/<project>/docs/ (truth) and writes only derived files:

  python .claude/references/scripts/protoflow_compile.py <project>              product-model.json + docs/spec.html
         … --slices                                                    + prototype/.slices/<SCR-id>.json (one per screen)
         … --notes                                                     + prototype/notes.js (each screen's open items as review notes)
         … --schema                                                    docs/_global/db-design.md → prototype/schema.sql (SQLite)
         … --seed                                                      prototype/seed.spec.json → prototype/seed.sql (see SEED_HELP)
         … --check-db                                                  load schema.sql + seed.sql in SQLite: errors, FK violations,
                                                                       row counts, check-constraint states with no seeded row
         … --screens                                                   docs + prototype/test.spec.json → prototype/screens.js
         … --brief                                                     prototype/.slices/_brief.md (rules + ctx/ui.js/app.js API +
                                                                       personas) — the one file a screen-writing agent reads
         … --plan                                                      print which prototype files are new / stale / unchanged /
                                                                       orphaned / hand-edited (needs .manifest.json)
         … --manifest                                                  rewrite prototype/.manifest.json from the generated files
         … --registry                                                  docs/INDEX.md + docs/board.yml (registry.md rules)
         … --date YYYY-MM-DD                                           compile date (default: today)

Run from the repo root. Standard library only. Output is stable: same docs → byte-identical files.
"""
import argparse, datetime, hashlib, json, os, re, sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
HEADER_KEYS = {"Status", "Type", "Source", "Confirmed"}
ID_RE = r"(?:REQ|BR|UC|FLOW|SCR|AC|ENT)-\d+"
LADDER = ["grounded", "explored", "specced", "prototyped", "confirmed", "handed-off"]
ICON = {"grounded": "🌫", "explored": "💬", "specced": "🔨", "prototyped": "🖥", "confirmed": "✅", "handed-off": "📦"}
DOCS = ("requirements.md", "rules.md", "flows.md", "screens.md", "acceptance.md")


# ------------------------------------------------------------------ markdown → items
def read(path):
    if not os.path.exists(path):
        return ""
    with open(path, encoding="utf-8") as f:
        return f.read()


def plain(s):
    s = re.sub(r"\*\*(.+?)\*\*", r"\1", s)
    s = re.sub(r"(?<![\w*])\*(?!\s)(.+?)\*(?!\w)", r"\1", s)
    s = re.sub(r"`([^`]+)`", r"\1", s)
    return s.strip()


def split_items(text):
    """Every ### block that carries an item header (Status/Type/Source/Confirmed) → (section, heading, lines)."""
    items, section, cur = [], "", None
    for line in text.splitlines():
        if line.startswith("### "):
            cur = [section, line[4:].strip(), []]
            items.append(cur)
        elif line.startswith("## "):
            section, cur = line[3:].strip(), None
        elif line.startswith("# "):
            cur = None
        elif cur is not None:
            cur[2].append(line)
    return [i for i in items if any(l.startswith("- **Status:**") for l in i[2]) and "<" not in i[1]]


_MERMAID = {"last": ""}          # the first ```mermaid block of the item parse_item just read (FLOW items carry one)

NODE_RE = re.compile(r"([A-Za-z0-9_]+)\s*(\(\[.*?\]\)|\(\(.*?\)\)|\[\[.*?\]\]|\[.*?\]|\{.*?\}|\(.*?\)|>.*?\])?")
EDGE_RE = re.compile(r"\s*(?:(-->|---|-\.->|==>|-\.-)(?:\s*\|([^|]*)\|)?|--\s*([^->][^>]*?)\s*-->)\s*")


def parse_mermaid_flowchart(src):
    """A FLOW's ```mermaid flowchart block → {nodes:[{id,label,kind}], edges:[{from,to,label}]}, or None.
    kind: decision ({…}), terminal (([…]) / ((…)) / (…)), step (anything else). Unknown lines are skipped."""
    nodes, edges = {}, []

    def node(m):
        nid, shape = m.group(1), m.group(2) or ""
        lab = shape.strip("[](){}>/\\").strip().strip('"') if shape else ""
        kind = "decision" if shape.startswith("{") else "terminal" if shape.startswith("(") else "step"
        if nid not in nodes:
            nodes[nid] = {"id": nid, "label": plain(lab) or nid, "kind": kind}
        elif lab:
            nodes[nid].update(label=plain(lab), kind=kind)
        return nid

    for raw in (src or "").splitlines():
        line = raw.strip()
        if not line or re.match(r"^(flowchart|graph|%%|classDef|class |style |linkStyle|subgraph|end$|direction)", line):
            continue
        m = NODE_RE.match(line)
        if not m:
            continue
        prev, pos = node(m), m.end()
        while True:
            e = EDGE_RE.match(line, pos)
            if not e:
                break
            n = NODE_RE.match(line, e.end())
            if not n:
                break
            nxt = node(n)
            edges.append({"from": prev, "to": nxt, "label": plain((e.group(2) or e.group(3) or "").strip().strip('"'))})
            prev, pos = nxt, n.end()
    return {"nodes": list(nodes.values()), "edges": edges} if nodes else None


def split_steps(items):
    """Use-case main paths written inline ("1. Opens … 2. Chooses …") → one entry per step."""
    out = []
    for s in items:
        parts = [p.strip() for p in re.split(r"(?:^|\s)\d+\.\s+", s) if p.strip()]
        out += parts if len(parts) > 1 else [s]
    return out


def parse_item(heading, lines):
    m = re.match(rf"^({ID_RE})\s+—\s+(.*)$", heading)
    iid, title = (m.group(1), m.group(2)) if m else ("", heading)
    hdr, body = {}, []
    for l in lines:
        hm = re.match(r"^- \*\*(\w+):\*\*\s?(.*)$", l)
        if hm and hm.group(1) in HEADER_KEYS and not body:
            hdr[hm.group(1)] = hm.group(2).strip()
        elif hdr and (body or l.strip()):
            body.append(l)
    sketch, out, code, lang, in_code = "", [], [], "", False
    _MERMAID["last"] = ""
    for l in body:
        if l.startswith("```"):
            if in_code:
                if lang in ("", "text"):
                    sketch = "\n".join(code)
                elif lang == "mermaid" and not _MERMAID["last"]:
                    _MERMAID["last"] = "\n".join(code)
                code, in_code = [], False
            else:
                in_code, lang = True, l[3:].strip()
        elif in_code:
            code.append(l)
        else:
            out.append(l)
    fields, last, prose = {}, None, []
    for l in out:
        km = re.match(r"^- \*\*([^*]+?):\*\*\s?(.*)$", l)
        lm = re.match(r"^(\s+)(?:[-*]|\d+\.)\s+(.*)$", l)
        if km:
            last = km.group(1)
            fields.setdefault(last, {"value": km.group(2).strip(), "list": []})
        elif lm and last:
            lst = fields[last]["list"]
            if len(lm.group(1)) <= 3 or not lst:
                lst.append(lm.group(2).strip())
            else:
                lst[-1] += " " + lm.group(2).strip()
        elif l.strip() and last and l.startswith("     "):
            if fields[last]["list"]:
                fields[last]["list"][-1] += " " + l.strip()
        elif l.strip() and (not last or not l.startswith(" ")):
            prose.append(l)
        elif not l.strip() and prose:
            prose.append("")
    base = {"id": iid, "title": plain(title), "status": hdr.get("Status", "proposed"), "type": hdr.get("Type", ""),
            "source": plain(hdr.get("Source", "")), "confirmed": plain(hdr.get("Confirmed", ""))}
    text = re.sub(r"\n{3,}", "\n\n", "\n".join(plain(p) if p.strip() else "" for p in prose).strip())
    return base, fields, text, sketch


ids = lambda s, p: re.findall(p + r"-\d+", s or "")
fval = lambda f, k: f.get(k, {}).get("value", "")


def flist(f, k):
    x = f.get(k)
    if not x:
        return []
    if x["list"]:
        return [plain(v) for v in x["list"]]
    return [plain(v) for v in re.split(r";\s*", x["value"])] if x["value"] else []


def fall(f, k):
    x = f.get(k, {"value": "", "list": []})
    return plain(" ".join(p for p in [x["value"]] + x["list"] if p))


# ------------------------------------------------------------------ per-doc compilers
def c_requirements(text):
    out = []
    for _, head, lines in split_items(text):
        base, f, prose, _ = parse_item(head, lines)
        if base["id"].startswith("REQ-"):
            shall, scen, cur = [], [], None
            for l in lines:
                km = re.match(r"^- \*\*([^*]+?):\*\*\s?(.*)$", l)
                if km:
                    cur = km.group(1)
                    (shall if cur == "SHALL" else scen if cur == "Scenario" else []).append(km.group(2))
                elif cur == "SHALL" and re.match(r"^\s+[-*]\s+", l):
                    shall.append("- " + re.sub(r"^\s+[-*]\s+", "", l))
            base.update(text="\n".join(plain(x) for x in shall + scen), rules=ids(fval(f, "Rules"), "BR"),
                        entities=ids(fval(f, "Entities"), "ENT"))
        else:
            base.update(text=prose, rules=[], entities=[])
        out.append(base)
    return out


def c_rules(text, scope="local"):
    out = []
    for _, head, lines in split_items(text):
        base, f, prose, _ = parse_item(head, lines)
        if base["id"].startswith("BR-"):
            base.update(text=fall(f, "Rule"), appliesTo=ids(fval(f, "Applies to"), "REQ"),
                        spans=[s.strip() for s in plain(fval(f, "Spans features")).split(",") if s.strip()])
        else:
            base["text"] = prose
        base["scope"] = scope
        out.append(base)
    return out


def c_flows(text):
    ucs, flows = [], []
    for _, head, lines in split_items(text):
        base, f, prose, _ = parse_item(head, lines)
        if base["id"].startswith("UC-"):
            ucs.append({**base, "actor": plain(fval(f, "Actor")), "goal": plain(fval(f, "Goal")),
                        "pre": [p.strip() for p in re.split(r";\s*", plain(fval(f, "Preconditions"))) if p.strip()],
                        "main": split_steps(flist(f, "Main path")), "reqs": ids(fval(f, "Requirements"), "REQ")})
        elif base["id"].startswith("FLOW-"):
            flows.append({**base, "text": plain(fval(f, "Trigger")), "trigger": plain(fval(f, "Trigger")), "steps": flist(f, "Steps"),
                          "rules": ids(fval(f, "Rules"), "BR"), "screens": ids(fval(f, "Screens"), "SCR"),
                          "graph": parse_mermaid_flowchart(_MERMAID["last"])})
        else:
            flows.append({**base, "text": prose, "steps": [], "rules": [], "screens": []})
    return ucs, flows


def c_screens(text):
    out = []
    for _, head, lines in split_items(text):
        base, f, prose, sketch = parse_item(head, lines)
        if not base["id"].startswith("SCR-"):
            base.update(text=prose, elements=[], fields=[], actions=[], states=[], flows=[], entities=[], sketch="")
            out.append(base)
            continue
        fields = []
        for x in flist(f, "Fields"):
            binds = list(re.finditer(r"([^,(:]+?)\s*\((?:bound to |count of )?(ENT-\d+)\.(\w+)", x))
            if len(binds) > 1:
                pre = x.split(":")[0].strip() + ": " if ":" in x.split("(")[0] else ""
                fields += [{"label": pre + b.group(1).strip(" :"), "bind": f"{b.group(2)}.{b.group(3)}"} for b in binds]
                continue
            b = re.search(r"(ENT-\d+)\.(\w+)", x) or re.search(r"(ENT-\d+)()", x)
            fields.append({"label": re.split(r"\s*\(", x)[0].strip(), "bind": (b.group(1) + ("." + b.group(2) if b.group(2) else "")) if b else ""})
        actions = []
        for a in flist(f, "Actions"):
            parts = re.split(r"\s*→\s*", a)
            tgt = parts[1] if len(parts) > 1 else ""
            fl = ids(tgt, "FLOW")
            actions.append({"label": parts[0].strip(), "flow": fl[0] if fl else "", "target": "" if fl else tgt.strip()})
        base.update(text=plain(fval(f, "Purpose")), purpose=plain(fval(f, "Purpose")),
                    elements=[x["label"] for x in fields] + [a["label"] for a in actions], fields=fields, actions=actions,
                    states=[re.split(r"\s*\(", s)[0].strip() for s in flist(f, "States")], statesDetail=flist(f, "States"),
                    flows=ids(fval(f, "Flows"), "FLOW"), entities=ids(fval(f, "Entities"), "ENT"), sketch=sketch)
        out.append(base)
    return out


def c_acceptance(text):
    out = []
    for _, head, lines in split_items(text):
        base, f, prose, _ = parse_item(head, lines)
        if base["id"].startswith("AC-"):
            g = []
            for l in lines:
                gm = re.match(r"^- \*\*(Given|When|Then|And)\*\*\s+(.*)$", l)
                if gm:
                    g.append(f"{gm.group(1)} {plain(gm.group(2))}")
                elif g and re.match(r"^\s+-\s+", l):
                    g[-1] += "\n  " + plain(l.strip()[2:])
            va = ids(fval(f, "Verifies"), "(?:REQ|BR)")
            reqs = [x for x in va if x.startswith("REQ-")]
            base.update(gherkin="\n".join(g), text="\n".join(g), verifies=(reqs or va or [""])[0], verifiesAll=va)
        else:
            base.update(gherkin="", text=prose, verifies="", verifiesAll=[])
        out.append(base)
    return out


# ------------------------------------------------------------------ project compile
def compile_project(P, date):
    D = os.path.join(P, "docs")
    grounding = read(os.path.join(D, "_global", "grounding.md"))
    m = re.search(r"## Business context\s*\n(.*?)\n## ", grounding, re.S)
    context = plain(re.sub(r"\s*\((?:materials\.txt|see)[^)]*\)", "", m.group(1).strip())) if m else ""
    sm = re.search(r"## Feature scope\s*\n(.*?)(?=\n## )", grounding, re.S)
    scope = []
    for _, head, lines in split_items("## Feature scope\n" + (sm.group(1) if sm else "")):
        base, _, prose, _ = parse_item(head, lines)
        scope.append({"id": head.strip(), "status": base["status"], "source": base["source"], "text": prose})

    entities = []
    CARD = {"1:N": "||--o{", "N:1": "}o--||", "1:1": "||--||"}
    for _, head, lines in split_items(read(os.path.join(D, "_global", "entities.md"))):
        base, f, _, _ = parse_item(head, lines)
        if not base["id"]:
            continue
        names = []
        for k in f:
            if k.startswith("Fields"):
                for n in re.findall(r"`(\w+)`", f[k]["value"] + " " + " ".join(f[k]["list"])):
                    if n not in names and not n.isupper():
                        names.append(n)
        rels = [{"to": r.group(3).strip(), "card": CARD[r.group(4)], "label": r.group(1)}
                for r in re.finditer(r"(has many|has one|belongs to) (ENT-\d+) ([\w -]+?) \((1:N|N:1|1:1)", fval(f, "Relationships"))]
        entities.append({**base, "name": base["title"], "note": plain(fval(f, "Fields"))[:160],
                         "fields": [{"name": n, "type": "", **({"key": "PK"} if n == "id" else {})} for n in names], "relations": rels})

    glossary = [{"term": a, "def": plain(b), "source": c}
                for a, b, c in re.findall(r"^\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|$", read(os.path.join(D, "_global", "glossary.md")), re.M)
                if a != "Term" and not a.startswith("-")]

    dbDesign = []
    for _, head, lines in split_items(read(os.path.join(D, "_global", "db-design.md"))):
        base, f, _, _ = parse_item(head, lines)
        tm = re.match(r"^(\w+)\s*\((?:from )?(ENT-\d+)\)", head)
        cols = []
        for row in re.findall(r"^\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*([^|]*?)\s*\|\s*([^|]*?)\s*\|$", "\n".join(lines), re.M):
            if row[0] in ("Column",) or row[0].startswith("-"):
                continue
            key = "PK" if "PK" in row[2] else "FK" if "FK" in row[2] or "references" in row[2] else None
            cols.append({"name": row[0], "type": row[1], **({"key": key} if key else {}), "constraints": row[2], "note": row[3]})
        dbDesign.append({"table": tm.group(1) if tm else head.split()[0], "entity": tm.group(2) if tm else "", "columns": cols,
                         "indexes": re.findall(r"`([^`]+)`", fval(f, "Indexes"))})

    modules = []
    for _, head, lines in split_items(read(os.path.join(D, "_global", "architecture.md"))):
        base, f, _, _ = parse_item(head, lines)
        modules.append({"name": base["title"], "description": plain(fval(f, "Responsibility")), "dependsOn": [],
                        "features": [s.strip() for s in plain(fval(f, "Features it serves")).split(",") if s.strip()]})

    grules = c_rules(read(os.path.join(D, "_global", "rules.md")), "global")
    order = [s["id"] for s in scope]
    FD = os.path.join(D, "features")
    folders = sorted((d for d in os.listdir(FD) if os.path.isdir(os.path.join(FD, d))) if os.path.isdir(FD) else [],
                     key=lambda d: (order.index(d) if d in order else 999, d))
    features, counts = [], {}
    for fid in folders:
        rd = lambda n: read(os.path.join(FD, fid, n))
        reqs, rules = c_requirements(rd("requirements.md")), c_rules(rd("rules.md"))
        local_rules = list(rules)
        rules += [r for r in grules if fid in r.get("spans", [])]
        ucs, flows = c_flows(rd("flows.md"))
        screens, acc = c_screens(rd("screens.md")), c_acceptance(rd("acceptance.md"))
        local = reqs + local_rules + flows + screens + acc
        has = lambda arr, p: any(x["id"].startswith(p) for x in arr)
        rq = [r for r in reqs if r["id"]]
        if has(reqs, "REQ-") and has(rules, "BR-") and has(flows, "FLOW-") and has(screens, "SCR-"):
            status = "specced"
            if os.path.isdir(os.path.join(P, "prototype", fid)):
                status = "prototyped"
            if rq and all(r["status"] == "confirmed" for r in rq):
                status = "confirmed"
            if os.path.isdir(os.path.join(P, "handoff", fid)):
                status = "handed-off"
        else:
            status = "explored" if any(x["type"] == "UNKNOWN" for x in local) else "grounded"
        confirmed_ids = {r["id"] for r in rq if r["status"] == "confirmed"}
        conflicts = [(doc, parse_item(h, l)[0]["title"]) for doc in DOCS for _, h, l in split_items(rd(doc))
                     if parse_item(h, l)[0]["type"] == "CONFLICT" and parse_item(h, l)[0]["status"] != "rejected"]
        attached = [x for x in local if x["type"] == "UNKNOWN" and set(ids(x["text"] + " " + x["source"], "REQ")) & confirmed_ids]
        counts[fid] = {"req": len(rq), "br": sum(1 for r in local_rules if r["id"]),
                       "open_q": sum(1 for x in local if x["type"] == "UNKNOWN"), "conflict": len(conflicts),
                       "confirmed": len(confirmed_ids), "conflicts": conflicts,
                       "handoff": "blocked" if conflicts or attached else ("ready" if LADDER.index(status) >= 2 else "—")}
        ents = []
        for x in reqs + screens:
            ents += [e for e in x.get("entities", []) if e not in ents]
        sc = next((s for s in scope if s["id"] == fid), None)
        features.append({"id": fid, "title": fid.replace("-", " ").capitalize(),
                         "module": next((m["name"] for m in modules if fid in m["features"]), "Ungrouped"), "status": status,
                         "provenance": sc["source"] if sc else "", "entities": sorted(ents), "useCases": ucs,
                         "requirements": reqs, "rules": rules, "flows": flows, "screens": screens, "acceptance": acc})

    flowE2E = []
    specced = [f for f in features if LADDER.index(f["status"]) >= 2]
    if len(specced) > 1:
        for f in specced:
            main = next((fl for fl in f["flows"] if fl["id"]), None)
            for s in (main["steps"] if main else []):
                flowE2E.append({"step": re.sub(r"\s*\((?:BR|FLOW)-[^)]*\)", "", s), "module": f["module"], "feature": f["id"]})

    model = {"project": os.path.basename(P), "generated": date, "context": context, "modules": modules, "flowE2E": flowE2E,
             "global": {"entities": entities, "dbDesign": dbDesign, "glossary": glossary}, "features": features}
    extra = {"scope": scope, "counts": counts, "grules": grules, "grounding": grounding,
             "entities_md": read(os.path.join(D, "_global", "entities.md"))}
    return model, extra


# ------------------------------------------------------------------ helpers
def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def item_index(model):
    idx = {e["id"]: e for e in model["global"]["entities"]}
    for f in model["features"]:
        for k in ("useCases", "requirements", "rules", "flows", "screens", "acceptance"):
            for it in f[k]:
                if it.get("id"):
                    idx.setdefault(it["id"], {**it, "_feature": f["id"]})
    return idx


sha = lambda s: hashlib.sha256(s.encode("utf-8")).hexdigest()[:16]


def sources_hash(idx, src):
    return sha(json.dumps([idx.get(i) for i in src], sort_keys=True, ensure_ascii=False))


def generated_files(proto):
    for dp, dn, fn in os.walk(proto):
        dn[:] = [d for d in dn if not d.startswith(".")]
        for n in sorted(fn):
            p = os.path.join(dp, n)
            if n.endswith((".js", ".sql")):
                yield os.path.relpath(p, proto).replace(os.sep, "/"), read(p)


def file_sources(rel, text, model):
    found = list(dict.fromkeys(re.findall(ID_RE, text)))
    if rel != "screens.js":
        # A link to another screen (go("SCR-003"), a HOME map) is navigation, not content: a module depends on its own
        # SCR only, so editing one screen's doc doesn't mark every screen that links to it as stale.
        own = re.match(r".*/(SCR-\d+)\.js$", rel)
        found = [i for i in found if not i.startswith("SCR-") or (own and i == own.group(1))]
    if rel in ("schema.sql", "seed.sql") or not found:
        found += [e["id"] for e in model["global"]["entities"] if e["id"] not in found]
    return sorted(found, key=lambda x: (x.split("-")[0], int(x.split("-")[1])))


def compress(nums):
    out, i = [], 0
    while i < len(nums):
        j = i
        while j + 1 < len(nums) and nums[j + 1] == nums[j] + 1:
            j += 1
        a, b = f"BR-{nums[i]:03d}", f"{nums[j]:03d}"
        out.append(a if i == j else f"{a}–{b}")
        i = j + 1
    return ", ".join(out)


def registry(P, model, extra):
    feats, counts = model["features"], extra["counts"]
    furthest = max((LADDER.index(f["status"]) for f in feats), default=-1)
    phase = {-1: "grounding", 0: "grounding", 1: "exploration", 2: "specification", 3: "prototype", 4: "confirmation", 5: "handoff"}[furthest]
    rows, yml = [], []
    for f in feats:
        c = counts[f["id"]]
        proto = "✓" if os.path.isdir(os.path.join(P, "prototype", f["id"])) else "—"
        rows.append(f"| {f['id']} | {ICON[f['status']]} {f['status']} | {c['req']} | {c['br']} | {c['open_q']} | {c['conflict']} | {proto} | {c['handoff']} |")
        yml += [f"  {f['id']}:", f"    status: {f['status']}", f"    req: {c['req']}", f"    br: {c['br']}", f"    open_q: {c['open_q']}",
                f"    conflict: {c['conflict']}", f"    prototype: {'true' if proto == '✓' else 'false'}",
                "    handoff: " + ('"—"' if c["handoff"] == "—" else c["handoff"])]
    nconf = sum(c["conflict"] for c in counts.values())
    gconf = sum(1 for _, h, l in split_items(extra["grounding"]) if parse_item(h, l)[0]["type"] == "CONFLICT" and parse_item(h, l)[0]["status"] != "rejected")
    where = "; ".join(f'{fid}: {doc} "{title}"' for fid, c in counts.items() for doc, title in c["conflicts"])
    openq = sum(c["open_q"] for c in counts.values())
    conf = sum(c["confirmed"] for c in counts.values())
    total = sum(c["req"] for c in counts.values())
    g = model["global"]
    gr = "✓" if extra["grounding"].strip() else "—"
    erd = "✓" if "erDiagram" in extra["entities_md"] else "—"
    brs = sorted(int(r["id"][3:]) for r in extra["grules"] if r["id"])
    cross = f" · cross-cutting rules {len(brs)} ({compress(brs)})" if brs else ""
    index = "\n".join([
        f"# {model['project']} — Feature Registry",
        f"_Phase: {phase.upper()} · derived, do not hand-edit · regenerate with `/protoflow-status`_", "",
        "## Features", "",
        "| Feature | Status | REQ | BR | Open-Q | Conflict | Proto | Handoff |",
        "|---------|--------|-----|----|--------|----------|-------|---------|",
        *(rows or ["| _(none yet — features appear after a `/protoflow-explore` deep-dive)_ | | | | | | | |"]), "",
        "## Health (handoff blockers)",
        f"- 🔴 Conflicts unresolved: {nconf}" + (f" ({where})" if where else ""),
        f"- 🟡 Open questions: {openq}",
        f"- 🟢 Confirmed reqs: {conf} / {total}", "",
        "## Global",
        f"grounding.md {gr} · glossary {len(g['glossary'])} terms · entities {len(g['entities'])} (ENT-*) · ERD {erd}{cross}", "",
        "## Legend",
        "🌫 grounded → 💬 explored → 🔨 specced → 🖥 prototyped → ✅ confirmed → 📦 handed-off", ""])
    board = "\n".join([
        "# DERIVED by /protoflow-status — do not hand-edit",
        "# Machine twin of docs/INDEX.md. One entry per feature.",
        f"project: {model['project']}", f"phase: {phase}",
        "features:" + ("" if yml else " {}"), *yml,
        "health:", f"  conflicts: {nconf}", f"  grounding_conflicts: {gconf}", f"  open_questions: {openq}",
        f"  confirmed_reqs: {conf}", f"  total_reqs: {total}", ""])
    write(os.path.join(P, "docs", "INDEX.md"), index)
    write(os.path.join(P, "docs", "board.yml"), board)
    blocked = [f["id"] for f in feats if counts[f["id"]]["handoff"] == "blocked"]
    return {"features": len(feats), "blocked": blocked, "open_questions": openq}


DROP = {"source", "confirmed", "elements", "statesDetail", "verifiesAll", "gherkin", "note", "relations", "appliesTo", "spans"}


def slim(v):
    """Slices carry what a screen author needs, not provenance: drop source/confirmed/duplicates and empty values."""
    if isinstance(v, dict):
        return {k: slim(x) for k, x in v.items() if k not in DROP and x not in ("", [], None)}
    if isinstance(v, list):
        return [slim(x) for x in v]
    return v


def screen_slices(model, idx):
    """One compact context per live screen: the SCR, its flows, the rules/reqs they cite, the entities it binds, the use cases
    that name its reqs, and every id-less item (open question / assumption / conflict) of its feature that concerns it."""
    out = {}
    for f in model["features"]:
        for s in f["screens"]:
            if not s["id"] or s["status"] == "rejected":
                continue
            flows = [idx[x] for x in s["flows"] if x in idx]
            rule_ids = sorted({r for fl in flows for r in fl.get("rules", [])})
            reqs = [r for r in f["requirements"] if r["id"] and (set(r["rules"]) & set(rule_ids) or set(r["entities"]) & set(s["entities"]))]
            req_ids = {r["id"] for r in reqs}
            out[s["id"]] = {"feature": f["id"], "screen": s, "flows": flows,
                            "rules": [idx[r] for r in rule_ids if r in idx], "requirements": reqs,
                            "useCases": [u for u in f["useCases"] if set(u["reqs"]) & req_ids],
                            "entities": [idx[e] for e in s["entities"] if e in idx],
                            # review-note candidates: open items of this feature that cite something on this screen
                            # (or sit in screens.md without citing anything), plus the screen's own ASSUMPTION/CONFLICT items
                            "openItems": [x for k in ("requirements", "rules", "flows", "screens", "acceptance") for x in f[k]
                                          if not x["id"] and x["status"] != "rejected" and x["type"] in ("ASSUMPTION", "UNKNOWN", "CONFLICT")
                                          and (set(re.findall(ID_RE, x["text"] + " " + x["source"])) & ({s["id"]} | set(s["flows"]) | set(rule_ids) | req_ids)
                                               or (k == "screens" and not re.findall(ID_RE, x["text"])))]
                                         + [r for r in reqs + [idx[b] for b in rule_ids if b in idx] if r.get("type") in ("ASSUMPTION", "CONFLICT")]}
    # related: another feature this screen's docs point to by name ("reuses the <feature> listing") → that feature's agreed
    # decisions, facts and rules, so the screen writer applies them without being told where to look.
    byid = {f["id"]: f for f in model["features"]}
    for sid, sl in out.items():
        # only what the screen itself, its flows, rules and requirements say — not provenance or "spans features" lists
        text = json.dumps(slim({k: sl[k] for k in ("screen", "flows", "rules", "requirements")}), ensure_ascii=False)
        rel = {}
        for fid, f in byid.items():
            if fid == sl["feature"] or not re.search(r"(?<![\w-])" + re.escape(fid) + r"(?![\w-])", text):
                continue
            items = [{"title": x["title"], "type": x["type"], "text": x.get("text", "")} for k in ("requirements", "rules", "flows", "screens") for x in f[k]
                     if x["status"] != "rejected" and (x["id"].startswith(("REQ-", "BR-")) or x["type"] in ("DECISION", "FACT"))]
            if items:
                rel[fid] = items
        if rel:
            sl["related"] = rel
    return out


NOTE_KIND = {"ASSUMPTION": "Assumed", "UNKNOWN": "Open question", "CONFLICT": "Conflict"}


def write_notes(proto, slices):
    """prototype/notes.js — every screen's open items as review-only notes; router.js renders them under the page."""
    def first(t, n=240):
        t = re.sub(r"\s+", " ", t or "").strip()
        m = re.match(r"(.+?[.?!])(\s|$)", t)
        t = m.group(1) if m and len(m.group(1)) > 40 else t
        return t if len(t) <= n else t[:n - 1].rstrip() + "…"
    notes, total = {}, 0
    for sid, sl in slices.items():
        seen, arr = set(), []
        for x in sl["openItems"]:
            key = (x.get("id") or "") + x["title"]
            if key in seen:
                continue
            seen.add(key)
            cited = re.findall(ID_RE, (x.get("text") or "") + " " + (x.get("source") or ""))
            arr.append({"kind": NOTE_KIND.get(x["type"], "Assumed"), "text": f"{x['title']} — {first(x.get('text'))}",
                        "ref": x.get("id") or (cited[0] if cited else sid)})
        notes[sid] = arr
        total += len(arr)
    write(os.path.join(proto, "notes.js"), "// DERIVED by protoflow_compile.py --notes from the docs' open items — do not hand-edit; re-run the script.\n"
          "// Rendered by router.js under each screen, in review mode only.\nexport const NOTES = "
          + json.dumps(notes, indent=1, ensure_ascii=False) + ";\n")
    return total


# ------------------------------------------------------------------ seed spec → seed.sql
SEED_HELP = """seed.spec.json → seed.sql. Shape: {"tables": {"<table>": {"cols": [...], "rows": [[...], ...], "each": {...}}}}
  rows   literal rows in `cols` order. Values: string / number / true / false / null, or a date token:
         "@now", "@now-3d", "@now+2h", "@now-30m" → datetime('now', …) ('YYYY-MM-DD HH:MM:SS'); "@date-10d" → date('now', …).
  _name  a table whose name starts with "_" is a helper: usable as `of`, never written to SQL.
  each   generated rows (one block, or a list of blocks): {"of": "<earlier table>", "where": {"col": value}, "cross": {"k": [values]}, "repeat": N,
         "row": {"col": "template"}}. One row per (row of `of` matching `where`) × (cross combination) × (1..repeat).
         Templates: "{of.col}", "{k}" (a cross key), "{i}" (1-based counter in the table), "{rand:0-12}", "{pick:a|b|c}".
         A template that is exactly one {…} keeps the value's type (number stays a number). Deterministic: same spec → same SQL."""


def expand_seed(proto):
    import random
    spec_path = os.path.join(proto, "seed.spec.json")
    if not os.path.exists(spec_path):
        return "no seed.spec.json — seed.sql left as is"
    spec = json.loads(read(spec_path))
    data, out = {}, ["-- GENERATED by /protoflow-prototype (protoflow_compile.py --seed from seed.spec.json) — edit the spec, not this file.",
                     "-- Seed data only. Never connect the prototype to a customer production database.", ""]
    for c in spec.get("comments", []):
        out.insert(2, "-- " + c)

    def sql(v):
        if v is None:
            return "null"
        if isinstance(v, bool):
            return "1" if v else "0"
        if isinstance(v, (int, float)):
            return repr(v)
        m = re.fullmatch(r"@(now|date)(?:([+-])(\d+)([dhm]))?", str(v))
        if m:
            fn = "datetime" if m.group(1) == "now" else "date"
            if not m.group(2):
                return f"{fn}('now')"
            unit = {"d": "days", "h": "hours", "m": "minutes"}[m.group(4)]
            return f"{fn}('now','{m.group(2)}{m.group(3)} {unit}')"
        return "'" + str(v).replace("'", "''") + "'"

    for table, t in spec["tables"].items():
        cols, rows = list(t["cols"]), [dict(zip(t["cols"], r)) for r in t.get("rows", [])]
        blocks = t.get("each") or []
        for b, e in enumerate(blocks if isinstance(blocks, list) else [blocks]):
            rnd = random.Random(f"{table}/{b}")
            parents = data[e["of"]] if e.get("of") else [{}]
            parents = [p for p in parents if all(p.get(k) == v for k, v in e.get("where", {}).items())]
            keys = list(e.get("cross", {}))
            combos = [{}]
            for k in keys:
                combos = [{**c, k: v} for c in combos for v in e["cross"][k]]
            i = len(rows)
            for p in parents:
                for c in combos:
                    for _ in range(e.get("repeat", 1)):
                        i += 1
                        def ev(expr):
                            if expr.startswith("of."):
                                return p.get(expr[3:])
                            if expr == "i":
                                return i
                            if expr.startswith("rand:"):
                                lo, hi = map(int, expr[5:].split("-"))
                                return rnd.randint(lo, hi)
                            if expr.startswith("pick:"):
                                o = expr[5:].split("|")[(i - 1) % len(expr[5:].split("|"))]
                                return int(o) if re.fullmatch(r"-?\d+", o) else float(o) if re.fullmatch(r"-?\d+\.\d+", o) else o
                            return c.get(expr, "{" + expr + "}")
                        r = {}
                        for col, tpl in e["row"].items():
                            if isinstance(tpl, str) and re.fullmatch(r"\{[^{}]+\}", tpl):
                                r[col] = ev(tpl[1:-1])
                            elif isinstance(tpl, str):
                                r[col] = re.sub(r"\{([^{}]+)\}", lambda m: str(ev(m.group(1))), tpl)
                            else:
                                r[col] = tpl
                        rows.append(r)
            cols += [k for k in e["row"] if k not in cols]
        data[table] = rows
        if rows and not table.startswith("_"):
            out.append(f"insert into {table} ({', '.join(cols)}) values")
            out.append(",\n".join("  (" + ", ".join(sql(r.get(c)) for c in cols) + ")" for r in rows) + ";")
            out.append("")
    write(os.path.join(proto, "seed.sql"), "\n".join(out))
    return {k: len(v) for k, v in data.items()}


def check_db(proto):
    """Load schema.sql + seed.sql into an in-memory SQLite with foreign keys on — the same engine the browser runs."""
    import sqlite3
    db = sqlite3.connect(":memory:")
    db.execute("pragma foreign_keys=on")
    res = {"ok": True}
    for f in ("schema.sql", "seed.sql"):
        try:
            db.executescript(read(os.path.join(proto, f)))
        except sqlite3.Error as e:
            return {"ok": False, "file": f, "error": str(e)}
    fk = db.execute("pragma foreign_key_check").fetchall()
    if fk:
        res.update(ok=False, foreignKeyViolations=[list(r) for r in fk[:20]])
    tables = [r[0] for r in db.execute("select name from sqlite_master where type='table' and name not like 'sqlite_%'")]
    res["rows"] = {t: db.execute(f'select count(*) from "{t}"').fetchone()[0] for t in tables}
    # every value a check (… in (…)) constraint allows should appear in at least one seeded row (each state is demoable)
    missing = []
    for t, sql_ in db.execute("select name, sql from sqlite_master where type='table'"):
        for col, vals in re.findall(r"(\w+)\s+TEXT[^,]*?check\s*\(\s*\w+\s+in\s*\(([^)]*)\)", sql_ or "", re.I):
            for v in re.findall(r"'([^']*)'", vals):
                if not db.execute(f'select 1 from "{t}" where "{col}" = ? limit 1', [v]).fetchone():
                    missing.append(f"{t}.{col}={v}")
    if missing:
        res["statesWithoutRows"] = missing
    res["empty"] = [t for t, n in res["rows"].items() if n == 0]
    return res


CTX_API = """ctx (2nd arg of render): h, query(sql, params) → rows, one(sql, params) → row|null, run(sql, params) → changes,
  go(SCR, params), params (query string), toast(msg), ok(msg), violate(BR, customerMsg) → node (also toasts),
  note(kind, text, ref) → review-only node, add(...nodes) (appends to the page, skips null/false), rerender()."""

SCREEN_RULES = """Rules for every screen module (prototype/<feature>/<SCR-id>.js):
- First line: `// GENERATED by /protoflow-prototype from <SCR-id> (<feature>) — edit the docs, not this file.` then ONE line `// Page type: <type> — <layout in a phrase>`.
- `export default { id, title, async render(root, ctx) { … } }`. Customer screens start with appNav(ctx, key) and end with the app footer if app.js has one.
- Build with the ui.js kit below; hand-write markup only for what the kit lacks. Engagement-specific CSS → a few lines appended to app.css by the lead, never per screen.
- Fields bound to the named entity column, labels in the customer's words, values formatted through app.js (never raw codes / ISO dates).
- Actions walk the linked FLOW steps (comment `// FLOW-00x step n`), then ctx.go(next SCR). Labels state the action. Unspecced target → "coming soon" toast, never a dead button.
- Every BR the flows cite is checked in the handler; violation → ctx.violate("BR-00x", "<what happened + what to do>"). Never the id in visible text.
- States: loading → ui.loading(slot, ui.skeleton(…), build); empty → ui.emptyState; submitting → ui.busy(btn); error → friendly text + ctx.note("Error", detail); success → ctx.ok + page reflects it.
- Traceability: `ref` (data-ref) on the heading (SCR), each action (REQ/FLOW), each rule message (BR). Open items are rendered automatically from notes.js — add ctx.note only for "Simulated" parts or to say what the page does meanwhile.
- SQLite booleans are 0/1: `x ? node : null`, never `x && node`. Native `el.append()` / `replaceChildren()` PRINT null — pass optional nodes through h(…) / ctx.add or `.filter(Boolean)` first. Plain ES modules, no framework, no CDN.
- An overlay screen (drawer, modal, sheet, toast — it has a cross-screen contract below) exports that opener AND a default render that draws hostPage(ctx) from app.js and then opens itself, so its URL works too. Build it with the kit overlays (ui.drawer / modal / confirm / sheet / toastCard).
- Shared logic between screens lives in app.js or a GENERATED helper module — import it, never copy it."""


def api_lines(path):
    """`name(signature)` + its one-line comment for every top-level export of a JS module (comment lines directly above)."""
    if not os.path.exists(path):
        return []
    lines, out = read(path).splitlines(), []
    for i, l in enumerate(lines):
        m = re.match(r"^export (?:async )?(?:function\s+(\w+)\s*\(([^)]*)\)|const\s+(\w+)\s*=\s*(?:async\s+)?(\([^)]*\)|\w+(?=\s*=>))?)", l)
        if not m:
            continue
        name, sig = (m.group(1), m.group(2)) if m.group(1) else (m.group(3), (m.group(4) or "").strip("()"))
        j, doc = i - 1, []
        while j >= 0 and lines[j].startswith("//"):
            doc.insert(0, lines[j][2:].strip())
            j -= 1
        doc = " ".join(doc)
        out.append(f"- `{name}({sig.strip()[:70]})`" + (f" — {doc[:260]}" if doc else ""))
    return out


def walk_lines(proto):
    try:
        spec = json.loads(read(os.path.join(proto, "test.spec.json")) or "{}")
    except ValueError:
        return ["(test.spec.json unreadable)"]
    out = [f"- {w.get('name')}: at {w.get('at')} as {w.get('as', '—')} {json.dumps(w.get('params', {}), ensure_ascii=False) if w.get('params') else ''} → "
           + " · ".join(json.dumps(st, ensure_ascii=False) for st in w.get("steps", [])) for w in spec.get("walks", [])]
    out += [f"- samples {k}: {json.dumps(v, ensure_ascii=False)}" for k, v in spec.get("samples", {}).items()]
    return out or ["(no test.spec.json yet)"]


def write_brief(proto):
    """prototype/.slices/_brief.md — everything a screen-writing agent needs besides its slice, in one short file."""
    ui = os.path.join(proto, "ui.js") if os.path.exists(os.path.join(proto, "ui.js")) else os.path.join(ROOT, "references", "templates", "prototype", "ui.js")
    app = read(os.path.join(proto, "app.js"))
    personas = re.findall(r'\{\s*id:\s*"([^"]+)",\s*label:\s*"([^"]+)"', app)
    feats = re.findall(r'\{\s*id:\s*"([\w-]+)",\s*title:', read(os.path.join(proto, "screens.js")))
    body = ["# Screen-writing brief (DERIVED by protoflow_compile.py --brief — do not hand-edit)", "",
            "Read this + your slice (.slices/<SCR-id>.json). A slice's `related` holds the agreed decisions of other features your screen reuses (e.g. \"works like the X listing\") — apply them. Open other files only if something here is unclear.", "",
            SCREEN_RULES, "", "## ctx API", CTX_API, "",
            "## ui.js kit — `import * as ui from \"../ui.js\"` (or named imports)", *api_lines(ui), "",
            "## app.js — `import { … } from \"../app.js\"`", *(api_lines(os.path.join(proto, "app.js")) or ["(not written yet)"]), "",
            "## Personas (\"View as\")", *([f"- `{i}` — {l}" for i, l in personas] or ["(none)"]), "",
            "## Cross-screen contracts (other files call these — export exactly this)",
            *([f"- {scr}: {c}" for scr, cs in sorted(contracts(proto).items()) for c in dict.fromkeys(cs)] or ["(none)"]), "",
            "## Self-test (screens.js) — your screen must satisfy every walk that starts at or reaches it, with these exact labels",
            "Steps: click = visible text or aria-label (or css:), fill = field label, expect = visible text, expectRule = a [data-ref=BR-…] element "
            "(ctx.violate gives one), expectAt = route or [data-ref=SCR-…] on screen.",
            *walk_lines(proto), "",
            "## Features with screens", ", ".join(feats) or "(none)", ""]
    write(os.path.join(proto, ".slices", "_brief.md"), "\n".join(body))
    return {"uiExports": len(api_lines(ui)), "appExports": len(api_lines(os.path.join(proto, "app.js"))), "personas": len(personas)}


# ------------------------------------------------------------------ generated shared files (domain-neutral)
SQL_TYPES = [(r"(uuid|text|varchar.*|char.*|citext|timestamptz|timestamp.*|date|time.*|jsonb?|enum.*|interval|inet|email)", "TEXT"),
             (r"(int|integer|bigint|smallint|serial|bigserial|int4|int8)", "INTEGER"),
             (r"(numeric.*|decimal.*|real|float.*|double.*|money)", "REAL"),
             (r"(bool|boolean)", "INTEGER")]


def sqlite_type(t):
    t = t.strip().lower()
    return next((ty for pat, ty in SQL_TYPES if re.fullmatch(pat, t)), "TEXT")


def gen_schema(P):
    """docs/_global/db-design.md → prototype/schema.sql (SQLite). Deterministic; app-level constraints become comments."""
    text = read(os.path.join(P, "docs", "_global", "db-design.md"))
    blocks, app, tables = [], [], 0
    for _, head, lines in split_items(text):
        base, f, _, _ = parse_item(head, lines)
        tm = re.match(r"^(\w+)\s*\((?:from )?(ENT-\d+)\)", head)
        if not tm or base["status"] == "rejected":
            continue
        table, ent = tm.groups()
        cols, tcons = [], []
        for name, typ, cons, note in re.findall(r"^\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*([^|]*?)\s*\|\s*([^|]*?)\s*\|$", "\n".join(lines), re.M):
            if name == "Column" or name.startswith("-"):
                continue
            name, typ, cons, note = plain(name), plain(typ), plain(cons), plain(note)
            if "range" in typ.lower():                                   # tstzrange slot → slot_start / slot_end
                cols += [f"{name}_start TEXT", f"{name}_end TEXT"]
                continue
            c, parts = cons.lower(), [name, sqlite_type(typ)]
            if re.search(r"\bpk\b|primary key", c):
                parts.append("primary key")
            if "not null" in c:
                parts.append("not null")
            if re.search(r"\bunique\b(?!\s*\()", c):
                parts.append("unique")
            m = re.search(r"default\s+([^,]+)", cons, re.I)
            if m:
                v = m.group(1).strip()
                v = {"false": "0", "true": "1"}.get(v.lower(), v)
                if v.lower() not in ("now", "now()", "current_timestamp", "gen_random_uuid()"):
                    parts.append("default " + (v if re.fullmatch(r"-?\d+(\.\d+)?", v) else "'" + v.strip("'\"") + "'"))
            m = re.search(r"check\s+in\s*\(([^)]*)\)", cons, re.I)
            if m:
                vals = ", ".join("'" + x.strip().strip("'\"") + "'" for x in m.group(1).split(","))
                parts.append(f"check ({name} in ({vals}))")
            else:
                m = re.search(r"check\s*([<>]=?|!=|=)\s*(-?[\d.]+)", cons, re.I)
                if m:
                    parts.append(f"check ({name} {m.group(1)} {m.group(2)})")
            m = re.search(r"(?:FK\s*(?:→|->)\s*|references\s+)(\w+)[.(](\w+)", cons, re.I)
            if m:
                parts.append(f"references {m.group(1)}({m.group(2)})")
            cols.append(" ".join(parts))
            if "app-level" in (note + " " + cons).lower() or re.search(r"\b(at most|exactly one|≤|<=)\b", note, re.I):
                app.append(f"-- app-level: {table}.{name} — {note}")
        x = f.get("Indexes", {"value": "", "list": []})
        raw = x["value"] + " " + " ".join(x["list"])
        idx_re = r"`(\w+)`\s*(unique\s+)?on\s*\(((?:[^()]|\([^()]*\))*)\)"
        idx = [f"create {'unique ' if u else ''}index {n} on {table} ({cl.strip()});" for n, u, cl in re.findall(idx_re, raw, re.I)]
        tcons += [f"unique ({cl.strip()})" for cl in re.findall(r"\bunique\s*\(([^()]*)\)", re.sub(idx_re, "", raw, flags=re.I), re.I)]
        if "app-level" in raw.lower():
            app.append(f"-- app-level: {table} — {plain(raw)}")
        blocks.append(f"-- {ent} {table}\ncreate table {table} (\n  " + ",\n  ".join(cols + tcons) + "\n);" + ("\n" + "\n".join(idx) if idx else ""))
        tables += 1
    if not tables:
        return "no db-design.md tables — write schema.sql by hand from entities.md"
    nm = re.search(r"## Notes\s*\n(.*)", text, re.S)
    for l in (nm.group(1).splitlines() if nm else []):
        if "app-level" in l.lower():
            app.append("-- app-level: " + plain(l.lstrip("- ")))
    head = ["-- GENERATED by /protoflow-prototype (protoflow_compile.py --schema from docs/_global/db-design.md) — edit the docs, not this file.",
            "-- SQLite: uuid/text/timestamps → TEXT ('YYYY-MM-DD HH:MM:SS'), int → INTEGER, numeric → REAL, boolean → INTEGER 0/1.",
            "-- Constraints SQLite can't express are enforced by the screen that owns the rule:", *dict.fromkeys(app), ""]
    write(os.path.join(P, "prototype", "schema.sql"), "\n".join(head) + "\n" + "\n\n".join(blocks) + "\n")
    return {"tables": tables, "appLevel": len(set(app))}


def gen_screens(P, model):
    """prototype/test.spec.json ({entry, samples, walks}) + the model → prototype/screens.js (FEATURES, SCREENS, WALKS)."""
    spec = json.loads(read(os.path.join(P, "prototype", "test.spec.json")) or "{}")
    feats = [f for f in model["features"] if LADDER.index(f["status"]) >= 2]
    live = lambda f: [s for s in f["screens"] if s["id"] and s["status"] != "rejected"]
    entry = spec.get("entry")
    feats.sort(key=lambda f: 0 if any(s["id"] == entry for s in live(f)) else 1)       # entry feature first (stable)
    samples, lines, imports = spec.get("samples", {}), [], []
    for f in feats:
        scr = sorted(live(f), key=lambda s: 0 if s["id"] == entry else 1)
        if not scr:
            continue
        lines.append(f'  {{ id: "{f["id"]}", title: {json.dumps(f["title"])}, screens: [')
        for s in scr:
            smp = f", samples: {json.dumps(samples[s['id']], ensure_ascii=False)}" if s["id"] in samples else ""
            lines.append(f'    {{ id: "{s["id"]}", title: {json.dumps(s["title"], ensure_ascii=False)}{smp} }},')
            imports.append(f'  "{s["id"]}": () => import("./{f["id"]}/{s["id"]}.js"),')
        lines.append("  ] },")
    walks = ",\n".join("  " + json.dumps(w, ensure_ascii=False) for w in spec.get("walks", []))
    js = "\n".join(["// GENERATED by /protoflow-prototype (protoflow_compile.py --screens from the docs + test.spec.json) — edit those, not this file.",
                    "// Specced features in Feature-scope order, the entry screen's feature first — the router opens its first screen on \"/\".",
                    "export const FEATURES = [", *lines, "];", "", "export const SCREENS = {", *imports, "};", "",
                    "// Scripted click-throughs run by window.protoSelftest() — one per FLOW happy path and per BR reachable from the UI.",
                    "export const WALKS = [", walks, "];", ""])
    write(os.path.join(P, "prototype", "screens.js"), js)
    return {"screens": len(imports), "walks": len(spec.get("walks", [])), "sampled": len(samples)}


def contracts(proto):
    """Cross-screen contracts: every `import("./<f>/SCR-x.js")).fn(` in app.js / helper modules → SCR-x must export fn."""
    out = {}
    for rel, text in generated_files(proto):
        if not rel.endswith(".js") or re.search(r"/SCR-\d+\.js$", rel):
            continue
        for scr, fn, args in re.findall(r"import\(\"\./[\w-]+/(SCR-\d+)\.js\"\)\)\.(\w+)\(([^)]*)\)", text):
            out.setdefault(scr, []).append(f"export function {fn}({args})  ← called from {rel}")
    return out


# ------------------------------------------------------------------ main
def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")   # the report carries the docs' text; Windows consoles/pipes default to cp1252
    ap = argparse.ArgumentParser()
    ap.add_argument("project")
    ap.add_argument("--date", default=datetime.date.today().isoformat())
    for flag in ("slices", "notes", "schema", "seed", "check-db", "screens", "brief", "plan", "manifest", "registry",
                 "library-draft", "library", "force"):
        ap.add_argument("--" + flag, action="store_true")
    a = ap.parse_args()
    P = os.path.join(os.getcwd(), "protoflow", a.project)  # engagements live in the working repo, not under .claude/
    if not os.path.isdir(P):
        sys.exit(f"protoflow/{a.project}/ not found — run /protoflow-new {a.project} first")
    model, extra = compile_project(P, a.date)
    js = json.dumps(model, indent=2, ensure_ascii=False)
    write(os.path.join(P, "product-model.json"), js + "\n")
    tpl = read(os.path.join(ROOT, "references", "templates", "spec.html"))
    spec = re.sub(r'(<script id="model">)(.*?)(</script>)',
                  lambda m: m.group(1) + "\nconst MODEL = " + js.replace("</script", "<\\/script") + ";\n" + m.group(3), tpl, count=1, flags=re.S)
    write(os.path.join(P, "docs", "spec.html"), spec)
    report = {"features": [{"id": f["id"], "status": f["status"],
                            "screens": [s["id"] for s in f["screens"] if s["id"] and s["status"] != "rejected"]} for f in model["features"]],
              "dbDesignTables": len(model["global"]["dbDesign"]), "entities": len(model["global"]["entities"])}

    idx = item_index(model)
    proto = os.path.join(P, "prototype")
    if a.slices or a.notes:
        slices = screen_slices(model, idx)
    if a.slices:
        for sid, slice_ in slices.items():
            write(os.path.join(proto, ".slices", f"{sid}.json"), json.dumps(slim(slice_), ensure_ascii=False, separators=(",", ":")) + "\n")
        report["slices"] = len(slices)
    if a.notes:
        report["notes"] = write_notes(proto, slices)
    if a.schema:
        report["schema"] = gen_schema(P)
    if a.seed:
        report["seed"] = expand_seed(proto)
    if a.check_db:
        report["db"] = check_db(proto)
    if a.screens:
        report["screens"] = gen_screens(P, model)
    if a.brief:
        report["brief"] = write_brief(proto)

    man_path = os.path.join(proto, ".manifest.json")
    if a.plan:
        man = json.loads(read(man_path) or "{}")
        plan = {"new": [], "stale": [], "unchanged": [], "orphaned": [], "handEdited": []}
        live = {s: f["id"] for f in report["features"] for s in f["screens"]}
        for scr, fid in live.items():
            rel = f"{fid}/{scr}.js"
            if rel not in man or not os.path.exists(os.path.join(proto, rel)):
                plan["new"].append(rel)
        for rel, e in man.items():
            path = os.path.join(proto, rel)
            m = re.match(r"^([\w-]+)/(SCR-\d+)\.js$", rel)
            if m and m.group(2) not in live:
                plan["orphaned"].append(rel)
                continue
            if not os.path.exists(path):
                plan["new"].append(rel)
                continue
            text = read(path)
            if "GENERATED by /protoflow-prototype" not in text or sha(text) != e.get("fileHash"):
                plan["handEdited"].append(rel)
            (plan["stale"] if sources_hash(idx, e["sources"]) != e["hash"] else plan["unchanged"]).append(rel)
        report["plan"] = plan

    if a.manifest:
        man = {}
        for rel, text in generated_files(proto):
            if rel in ("router.js", "db.js") or "GENERATED by /protoflow-prototype" not in text:
                continue                                  # shell files are written once and preserved, not tracked
            src = file_sources(rel, text, model)
            man[rel] = {"sources": src, "hash": sources_hash(idx, src), "fileHash": sha(text)}
        write(man_path, json.dumps(man, indent=2) + "\n")
        report["manifest"] = len(man)

    if a.registry:
        report["registry"] = registry(P, model, extra)
    if a.library_draft or a.library:
        import protoflow_library as lib                     # the flow library (/protoflow-guide) — same folder as this script
        if a.library_draft:
            report["libraryDraft"] = lib.write_draft(P, model, extra, force=a.force)
        if a.library:
            report["library"] = lib.validate_and_render(P, ROOT)
            if not report["library"].get("ok"):
                print(json.dumps(report, indent=1, ensure_ascii=False))
                sys.exit(1)
    print(json.dumps(report, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
