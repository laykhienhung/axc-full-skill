#!/usr/bin/env python3
"""Scan Playwright Page Objects for repeated action sequences worth hoisting.

Reports n-gram sequences of interaction lines (click/fill/type/press/goto/waitFor…)
that recur across 2+ methods or files. Output is candidates only — the model does the
actual refactor with the user's confirmation. Deterministic: no network, no writes.

Usage:
  python3 extract_common_actions.py [pages_dir] [--min-run 2] [--min-count 2] [--json]

Defaults: pages_dir=tests/pages, min-run=2 (lines per sequence), min-count=2 (occurrences).
"""
import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

# Lines that represent a browser action. Normalized by stripping string/number args
# so `fill('a')` and `fill('b')` collapse to the same shape.
ACTION_RE = re.compile(
    r"\b(goto|click|dblclick|fill|type|press|check|uncheck|selectOption|hover|"
    r"setChecked|waitFor|waitForTimeout|waitForURL|waitForLoadState|"
    r"getByRole|getByLabel|getByPlaceholder|getByText|getByTestId|locator|"
    r"mouse\.click|keyboard\.type|keyboard\.press|scrollIntoViewIfNeeded)\b"
)
# Method boundary in a TS class: `async foo(...)` or `foo(...) {`
METHOD_RE = re.compile(r"^\s*(?:async\s+)?(?:private\s+|public\s+|readonly\s+)?"
                       r"([A-Za-z_]\w*)\s*\([^)]*\)\s*(?::[^ {]+\s*)?\{")
STR_RE = re.compile(r"""(['"`]).*?\1""")
NUM_RE = re.compile(r"\b\d+\b")
# Calls whose string args IDENTIFY the target — keep those strings so different targets
# stay distinct. Everything else (fill/type/press/…) has its value args blanked, so the
# same action with different data still collapses to one hoistable shape.
SELECTOR_RE = re.compile(
    r"\b(getByRole|getByLabel|getByPlaceholder|getByText|getByTestId|locator)\b"
)


def normalize(line: str) -> str:
    """Collapse a source line to its action shape.

    Selector calls keep their string args (the role/label/selector is the action's identity,
    so getByRole('button',{name:'Save'}) != getByRole('button',{name:'Delete'})). Value calls
    blank their args (fill('a') == fill('b')) so repeated data-entry still hoists.
    """
    line = line.strip().rstrip(";")
    if not ACTION_RE.search(line):
        return ""
    if not SELECTOR_RE.search(line):
        line = STR_RE.sub("_", line)
    return NUM_RE.sub("_", line)


def method_bodies(text: str):
    """Yield (method_name, [normalized_action_lines]) from one file."""
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        m = METHOD_RE.match(lines[i])
        if not m:
            i += 1
            continue
        name = m.group(1)
        depth = lines[i].count("{") - lines[i].count("}")
        body, i = [], i + 1
        while i < len(lines) and depth > 0:
            depth += lines[i].count("{") - lines[i].count("}")
            norm = normalize(lines[i])
            if norm:
                body.append(norm)
            i += 1
        if body:
            yield name, body


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("pages_dir", nargs="?", default="tests/pages")
    ap.add_argument("--min-run", type=int, default=2, help="min action lines per sequence")
    ap.add_argument("--min-count", type=int, default=2, help="min occurrences to report")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    root = Path(args.pages_dir)
    files = sorted(root.rglob("*.ts")) if root.exists() else []
    if not files:
        print(f"No .ts files under {root}", file=sys.stderr)
        return 1

    # sequence-shape -> list of "file::method" where it occurs
    seqs = defaultdict(list)
    for f in files:
        for name, body in method_bodies(f.read_text(encoding="utf-8")):
            for n in range(args.min_run, min(len(body), 6) + 1):
                for start in range(len(body) - n + 1):
                    key = tuple(body[start:start + n])
                    seqs[key].append(f"{f.name}::{name}")

    # Keep sequences occurring >= min-count across distinct call sites.
    hits = []
    for shape, sites in seqs.items():
        uniq = sorted(set(sites))
        if len(sites) >= args.min_count and len(uniq) >= 2:
            hits.append({"length": len(shape), "count": len(sites),
                         "sites": uniq, "actions": list(shape)})
    # Longer + more frequent first; drop shorter sequences fully contained in a reported longer one.
    hits.sort(key=lambda h: (h["length"], h["count"]), reverse=True)
    kept, seen_long = [], []
    for h in hits:
        joined = "\n".join(h["actions"])
        if any(joined in big for big in seen_long):
            continue
        kept.append(h)
        seen_long.append(joined)

    if args.json:
        print(json.dumps(kept, indent=2))
        return 0

    if not kept:
        print("No repeated action sequences found. Nothing to hoist yet.")
        return 0
    print(f"Found {len(kept)} candidate sequence(s) to hoist into a shared actions helper:\n")
    for i, h in enumerate(kept, 1):
        print(f"[{i}] x{h['count']} across {len(h['sites'])} site(s), {h['length']} actions")
        for s in h["sites"]:
            print(f"      - {s}")
        for a in h["actions"]:
            print(f"      | {a}")
        print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
