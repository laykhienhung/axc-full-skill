#!/usr/bin/env python3
"""Validate converted cases and write them into the common TestCase template (.xlsx).

Inputs:
  extract.json      output of extract_manual.py (source order, groups, abbreviations)
  converted*.json   one or more files, each a list of
                    {key, type, type_reason, summary, priority, pre, action, input,
                     checkpoint, expected}   (or {"cases": [...]})

This script owns TC # numbering: <PREFIX>_<ABBR>_<NNN>, NNN restarting per group in source
order. Group abbreviations come from extract.json, overridden by --abbr (JSON {group: ABBR}).

Validation (exit 2, one JSON line per bad key on stderr, nothing written):
  - every extracted key converted exactly once, no unknown keys
  - type in Auto/Manual, priority in High/Medium/Low, summary/action/expected non-empty
  - Action, Input Data, Test check Point and Expected Result are numbered 1..n with the SAME n
    (Pre_Condition, when present, numbered 1..m)
  - the "[suggested]" tag (synthetic sample data) appears only in Input Data

Usage:
  python write_template.py extract.json converted_1.json [converted_2.json ...]
      --out OUT.xlsx --prefix OEMBLL --repo-path "CARIS Upgrade/..."
      [--abbr abbr.json] [--sheet-name NAME] [--template X.xlsx] [--regression General] [--force]
"""
import argparse
import json
import re
import sys
from copy import copy
from pathlib import Path

HERE = Path(__file__).resolve().parent
TEMPLATE = HERE.parent / "assets" / "testcase-template.xlsx"
COLUMNS = ["tc", "type", "summary", "repo_path", "priority", "regression", "pre", "action",
           "input", "checkpoint", "expected"]
TYPES = {"auto": "Auto", "manual": "Manual"}
PRIORITIES = {"high": "High", "medium": "Medium", "low": "Low"}
NUM = re.compile(r"^\s*(\d+)\.\s")
BAD_SHEET_CHARS = re.compile(r"[\[\]:*?/\\]")
SUGGESTED = "[suggested]"  # tag on synthetic sample input, allowed only in Input Data
TBD = re.compile(r"\bTBD\b")


def numbers(block):
    """Leading step numbers of a numbered block; non-numbered lines are continuations."""
    return [int(m.group(1)) for line in (block or "").splitlines() if (m := NUM.match(line))]


def check_numbered(name, block, errs):
    nums = numbers(block)
    if not nums:
        errs.append(f"{name}: not a numbered list ('1. ...')")
    elif nums != list(range(1, len(nums) + 1)):
        errs.append(f"{name}: numbering must run 1..n, got {nums}")
    return len(nums)


def validate(case):
    errs = []
    if (case.get("type") or "").strip().lower() not in TYPES:
        errs.append(f"type must be Auto or Manual, got {case.get('type')!r}")
    if (case.get("priority") or "").strip().lower() not in PRIORITIES:
        errs.append(f"priority must be High/Medium/Low, got {case.get('priority')!r}")
    for f in ("summary", "action", "input", "checkpoint", "expected"):
        if not (case.get(f) or "").strip():
            errs.append(f"{f}: empty")
    counts = {f: check_numbered(f, case.get(f), errs)
              for f in ("action", "input", "checkpoint", "expected") if (case.get(f) or "").strip()}
    if len(set(counts.values())) > 1:
        errs.append(f"step counts differ: {counts}")
    if (case.get("pre") or "").strip():
        check_numbered("pre", case["pre"], errs)
    for f in ("summary", "pre", "action", "checkpoint", "expected"):
        if SUGGESTED in (case.get(f) or "").lower():
            errs.append(f"{f}: {SUGGESTED} is allowed only in input")
    return errs


def load_converted(paths):
    out = []
    for p in paths:
        data = json.loads(Path(p).read_text(encoding="utf-8"))
        out += data["cases"] if isinstance(data, dict) else data
    return out


def build_rows(extract, converted, prefix, repo_path, abbr_override, regression):
    """-> (rows, problems). problems = [{"key", "errors"}]."""
    abbr = {g["name"]: g["abbr"] for g in extract["groups"]} | abbr_override
    order = [c["key"] for c in extract["cases"]]
    group_of = {c["key"]: c["group"] for c in extract["cases"]}
    by_key, problems = {}, []
    for c in converted:
        k = c.get("key")
        if k not in group_of:
            problems.append({"key": k, "errors": ["unknown key (not in extract.json)"]})
        elif k in by_key:
            problems.append({"key": k, "errors": ["converted more than once"]})
        else:
            by_key[k] = c
    for k in order:
        if k not in by_key:
            problems.append({"key": k, "errors": ["missing (not converted)"]})
        elif errs := validate(by_key[k]):
            problems.append({"key": k, "errors": errs})
    if problems:
        return [], problems

    counters, rows = {}, []
    for k in order:
        c, a = by_key[k], abbr[group_of[k]]
        counters[a] = counters.get(a, 0) + 1
        rows.append({
            "key": k, "tc": f"{prefix}_{a}_{counters[a]:03d}",
            "type": TYPES[c["type"].strip().lower()], "summary": c["summary"].strip(),
            "repo_path": repo_path, "priority": PRIORITIES[c["priority"].strip().lower()],
            "regression": regression, "pre": (c.get("pre") or "").strip(),
            "action": c["action"].strip(), "input": c["input"].strip(),
            "checkpoint": c["checkpoint"].strip(), "expected": c["expected"].strip(),
        })
    return rows, []


def write_xlsx(rows, template, out, sheet_name):
    import openpyxl
    wb = openpyxl.load_workbook(template)
    ws = wb.worksheets[0]
    data_style = [copy(c._style) for c in ws[2]] if ws.max_row >= 2 else None
    if ws.max_row >= 2:
        ws.delete_rows(2, ws.max_row)
    ws.title = BAD_SHEET_CHARS.sub("", sheet_name).strip()[:31] or "TestCases"
    for i, row in enumerate(rows, start=2):
        for j, field in enumerate(COLUMNS, start=1):
            cell = ws.cell(i, j, row[field])
            if data_style and j <= len(data_style):
                cell._style = copy(data_style[j - 1])
    ws.auto_filter.ref = f"A1:{openpyxl.utils.get_column_letter(len(COLUMNS))}{len(rows) + 1}"
    wb.save(out)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("extract")
    ap.add_argument("converted", nargs="+")
    ap.add_argument("--out", required=True)
    ap.add_argument("--prefix", required=True)
    ap.add_argument("--repo-path", required=True)
    ap.add_argument("--abbr")
    ap.add_argument("--sheet-name")
    ap.add_argument("--template", default=str(TEMPLATE))
    ap.add_argument("--regression", default="General")
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()
    for stream in (sys.stdout, sys.stderr):  # Windows pipes default to cp1252
        stream.reconfigure(encoding="utf-8")

    out = Path(args.out)
    if out.exists() and not args.force:
        sys.exit(f"{out} exists. Pass --force to overwrite.")
    try:
        import openpyxl  # noqa: F401
    except ImportError:
        sys.exit("openpyxl not installed. Run: python -m pip install openpyxl")
    prefix = re.sub(r"[^A-Za-z0-9]", "", args.prefix).upper()
    if not prefix:
        sys.exit("--prefix must contain letters or digits.")

    extract = json.loads(Path(args.extract).read_text(encoding="utf-8"))
    abbr = json.loads(Path(args.abbr).read_text(encoding="utf-8")) if args.abbr else {}
    rows, problems = build_rows(extract, load_converted(args.converted), prefix,
                                args.repo_path, abbr, args.regression)
    if problems:
        for p in problems:
            print(json.dumps(p, ensure_ascii=False), file=sys.stderr)
        print(f"{len(problems)} case(s) failed validation; nothing written.", file=sys.stderr)
        return 2

    tcs = [r["tc"] for r in rows]
    if len(set(tcs)) != len(tcs):  # two groups sharing an --abbr override
        sys.exit("Duplicate TC # produced; give each group a distinct abbreviation.")
    write_xlsx(rows, args.template, out, args.sheet_name or extract["suggest"]["screen"])
    summary = {"out": str(out), "cases": len(rows),
               "by_type": {t: sum(r["type"] == t for r in rows) for t in ("Auto", "Manual")},
               "by_priority": {p: sum(r["priority"] == p for r in rows)
                               for p in ("High", "Medium", "Low")},
               "tc_range": [tcs[0], tcs[-1]] if tcs else [],
               "input_values": {"suggested": sum(r["input"].lower().count(SUGGESTED) for r in rows),
                                "tbd": sum(len(TBD.findall(r["input"])) for r in rows)}}
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
