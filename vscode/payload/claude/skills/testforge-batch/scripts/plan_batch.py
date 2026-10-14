#!/usr/bin/env python3
"""Turn read_cases.py --all-sheets output into a deterministic batch plan (plan.json).

Groups cases by screen (sheet), derives slug / module folder / Page Object file + class /
fixture name per screen, and resolves each case's target spec against existing specs:
  new     - id free
  skip    - same id (or one of its -V<n>) already on disk with the same source hash
  suffix  - id taken with a different/missing hash -> lowest free <ID>-V<n> (n >= 2)

Usage:
  python plan_batch.py <cases.json> [--root .] [--skipped <reader stderr file>] [--max 100]

Exit 2 on: more than --max cases, or two sheets mapping to one slug.
"""
import argparse
import json
import re
import sys
from pathlib import Path

HASH_RE = re.compile(r"^//\s*testforge-source-hash:\s*([0-9a-f]+)")


def slugify(name: str) -> str:
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", name.lower())).strip("-")


def pascal(slug: str) -> str:
    return "".join(p[:1].upper() + p[1:] for p in slug.split("-") if p)


def camel(slug: str) -> str:
    p = pascal(slug)
    return p[:1].lower() + p[1:]


def existing_specs(root: Path):
    """UPPERCASE spec id -> source hash ('' when the spec has no hash header)."""
    out = {}
    for f in (root / "tests" / "e2e").rglob("*.spec.ts"):
        sid = f.name[: -len(".spec.ts")].upper()
        first = f.read_text(encoding="utf-8").splitlines()[:1]
        m = HASH_RE.match(first[0]) if first else None
        out[sid] = m.group(1) if m else ""
    return out


def resolve(cid: str, h: str, taken: dict):
    """-> (action, specId). `taken` is updated so in-workbook duplicates collide too."""
    variants = [cid] + [f"{cid}-V{n}" for n in range(2, 1000) if f"{cid}-V{n}" in taken]
    for v in variants:
        if v in taken and taken[v] == h:
            return "skip", v
    if cid not in taken:
        taken[cid] = h
        return "new", cid
    n = 2
    while f"{cid}-V{n}" in taken:
        n += 1
    sid = f"{cid}-V{n}"
    taken[sid] = h
    return "suffix", sid


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("cases")
    ap.add_argument("--root", default=".")
    ap.add_argument("--skipped", default=None, help="file holding read_cases.py stderr")
    ap.add_argument("--max", type=int, default=100)
    args = ap.parse_args()
    for stream in (sys.stdout, sys.stderr):  # Windows pipes default to cp1252
        stream.reconfigure(encoding="utf-8")

    root = Path(args.root)
    cases = json.loads(Path(args.cases).read_text(encoding="utf-8"))
    skipped = []
    if args.skipped and Path(args.skipped).exists():
        for line in Path(args.skipped).read_text(encoding="utf-8").splitlines():
            m = re.match(r"skipped: (.*?): (.*)$", line)
            if m:
                skipped.append({"sheet": m.group(1), "reason": m.group(2)})

    if len(cases) > args.max:
        print(f"{len(cases)} cases > {args.max} — split the workbook into smaller files",
              file=sys.stderr)
        return 2

    screens, order, warnings = {}, [], []
    slug_owner = {}
    for c in cases:
        name = c.get("screen") or "screen"
        if name not in screens:
            slug = slugify(name)
            if not slug:
                slug = f"screen-{len(order) + 1}"
                warnings.append(f"sheet '{name}' has no ASCII letters — using slug '{slug}'")
            if slug in slug_owner:
                print(f"sheets '{slug_owner[slug]}' and '{name}' both map to slug '{slug}' — "
                      f"rename one", file=sys.stderr)
                return 2
            slug_owner[slug] = name
            screens[name] = {
                "screen": name, "slug": slug,
                "pomFile": f"tests/pages/{slug}.page.ts", "pomClass": f"{pascal(slug)}Page",
                "fixture": f"{camel(slug)}Page",
                "pomExists": (root / "tests" / "pages" / f"{slug}.page.ts").exists(),
                "cases": [],
            }
            order.append(name)
        screens[name]["cases"].append(c)

    taken = existing_specs(root)
    for name in order:
        s = screens[name]
        planned = []
        for i, c in enumerate(s["cases"], 1):
            cid = (c.get("id") or "").strip().upper()
            if not cid:
                cid = f"{s['slug'].upper()}-{i}"
                warnings.append(f"{name}: case '{c.get('title', '')}' has no id — assigned {cid}")
            action, sid = resolve(cid, c["hash"], taken)
            planned.append({
                "id": cid, "specId": sid, "title": c.get("title", ""), "hash": c["hash"],
                "specFile": f"tests/e2e/{s['slug']}/{sid}.spec.ts", "action": action,
                "preconditions": c.get("preconditions", ""), "steps": c.get("steps", []),
                "expected": c.get("expected", ""), "data": c.get("data", ""),
            })
        s["cases"] = planned

    plan = {"total": len(cases), "screens": [screens[n] for n in order],
            "skippedSheets": skipped, "warnings": warnings}
    print(json.dumps(plan, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
