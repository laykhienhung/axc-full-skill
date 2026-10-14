#!/usr/bin/env python3
"""Read test cases from CSV/TSV/XLSX into normalized JSON for the model to turn into specs.

Emits: [{ "id", "title", "preconditions", "steps": [{"n","action","expected"}], "expected",
          "data", "screen", "hash" }]

Column detection is fuzzy (case/space/underscore-insensitive) against common headers:
  id/key/testcase/TC #   -> id   ("TC #" = the common template written by testforge-convert)
  title/name/summary     -> title
  precondition(s)        -> preconditions
  step/action/description-> step action  (numbered rows accumulate into one case)
  test data/data         -> data (test inputs; "-" means none)
  expected/result        -> expected

The header may be any of the first 10 rows (title/banner rows above it are skipped).

`screen` = sheet name (CSV/TSV: file stem). `hash` = first 12 hex of SHA-1 over the normalized
preconditions + each step's action/expected — equal steps give equal hashes regardless of case
or whitespace. With no id column, a row with a title starts a new case and `id` is left empty in
--all-sheets mode (the batch planner assigns one) or numbered CASE-<n> otherwise.

Usage:
  python read_cases.py <file.csv|.tsv|.xlsx> [--sheet NAME | --all-sheets]

--all-sheets reads every sheet; sheets without a step/action column are skipped and reported on
stderr as "skipped: <sheet>: <reason>" so stdout stays pure JSON.
XLSX needs openpyxl. If missing, the script says so — install it or export to CSV instead.
CSV with one row per case (steps in a single cell separated by newlines / numbered) is
also handled: a multiline step cell is split into individual steps.
"""
import argparse
import csv
import hashlib
import json
import re
import sys
from pathlib import Path

ALIASES = {
    "id": ["id", "key", "testcase", "testcaseid", "tcid", "caseid", "tckey", "tc", "tcno"],
    "title": ["title", "name", "summary", "scenario", "testscenario", "testcasename"],
    "preconditions": ["precondition", "preconditions", "pre", "setup"],
    "action": ["step", "steps", "action", "actions", "description", "teststep", "teststeps",
               "stepaction"],
    "data": ["testdata", "data", "input", "inputdata"],
    "expected": ["expected", "expectedresult", "result", "expectedoutput", "expectedresults"],
    "n": ["no", "num", "number", "stepno", "seq", "order", "position"],
}


HEADER_SCAN = 10  # rows searched for the header


def canon(h: str) -> str:
    return re.sub(r"[^a-z0-9]", "", (h or "").lower())


def map_columns(headers):
    canon_headers = [canon(h) for h in headers]
    col = {}
    for field, names in ALIASES.items():
        wanted = {canon(n) for n in names}
        for i, ch in enumerate(canon_headers):
            if ch in wanted:
                col[field] = i
                break
    return col


def split_multiline_steps(cell: str):
    """A single cell holding many steps -> list of step strings."""
    parts = [p.strip() for p in re.split(r"[\r\n]+", cell) if p.strip()]
    # strip leading "1." / "1)" / "- "
    return [re.sub(r"^\s*(\d+[.)]|[-*])\s*", "", p) for p in parts]


def norm(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").lower()).strip()


def case_hash(c) -> str:
    parts = [norm(c["preconditions"])]
    for s in c["steps"]:
        parts += [norm(s["action"]), norm(s["expected"])]
    if c.get("data"):  # only when present, so hashes of data-less cases stay stable
        parts.append(norm(c["data"]))
    return hashlib.sha1("\x1f".join(parts).encode("utf-8")).hexdigest()[:12]


def xlsx_sheets(path: Path):
    try:
        import openpyxl
    except ImportError:
        sys.exit("openpyxl not installed. Run: python -m pip install openpyxl  "
                 "(or export the sheet to CSV)")
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    return wb


def sheet_rows(ws):
    return [["" if c is None else str(c) for c in row] for row in ws.iter_rows(values_only=True)]


def load_sheets(path: Path, sheet, all_sheets):
    """-> list of (screen, rows)."""
    ext = path.suffix.lower()
    if ext in (".csv", ".tsv"):
        delim = "\t" if ext == ".tsv" else ","
        with path.open(newline="", encoding="utf-8-sig") as f:
            return [(path.stem, [r for r in csv.reader(f, delimiter=delim)])]
    if ext in (".xlsx", ".xlsm"):
        wb = xlsx_sheets(path)
        if all_sheets:
            return [(ws.title, sheet_rows(ws)) for ws in wb.worksheets]
        ws = wb[sheet] if sheet else wb.active
        return [(ws.title, sheet_rows(ws))]
    sys.exit(f"Unsupported file type: {ext}. Use CSV, TSV, or XLSX.")


def parse_rows(rows, screen, blank_ids):
    """Rows of one sheet -> (cases, skip_reason). skip_reason is None when parsed."""
    if not rows:
        return [], "empty sheet"
    # Header row may sit under a title/banner row: take the first of the top rows with a
    # step/action column.
    for h in range(min(len(rows), HEADER_SCAN)):
        col = map_columns(rows[h])
        if "action" in col:
            break
    else:
        return [], "no step/action column"
    data = rows[h + 1:]

    def cell(row, field):
        i = col.get(field)
        return row[i].strip() if i is not None and i < len(row) else ""

    has_id = "id" in col
    cases = {}
    order = []
    last_id = None
    for row in data:
        if not any(c.strip() for c in row):
            continue
        if has_id:
            cid = cell(row, "id").upper() or last_id or "CASE-1"
        elif cell(row, "title") or last_id is None:
            cid = f"CASE-{len(order) + 1}"  # no id column: a titled row starts a new case
        else:
            cid = last_id
        last_id = cid
        if cid not in cases:
            cases[cid] = {"id": cid, "title": cell(row, "title"),
                          "preconditions": cell(row, "preconditions"),
                          "steps": [], "expected": cell(row, "expected"),
                          "data": ""}
            order.append(cid)
        c = cases[cid]
        if not c["title"] and cell(row, "title"):
            c["title"] = cell(row, "title")
        d = cell(row, "data")
        if d and d != "-":
            c["data"] = f'{c["data"]}\n{d}' if c["data"] else d

        action = cell(row, "action")
        expected = cell(row, "expected")
        if "\n" in action or "\r" in action:  # one-row-per-case with stacked steps
            exp_lines = split_multiline_steps(expected) if ("\n" in expected or "\r" in expected) else []
            steps = split_multiline_steps(action)
            for j, s in enumerate(steps):
                c["steps"].append({"n": len(c["steps"]) + 1, "action": s,
                                   "expected": exp_lines[j] if j < len(exp_lines) else ""})
        elif action:
            c["steps"].append({"n": len(c["steps"]) + 1, "action": action, "expected": expected})
        if expected and not c["steps"]:
            c["expected"] = expected

    out = []
    for cid in order:
        c = cases[cid]
        if not has_id and blank_ids:
            c["id"] = ""
        c["screen"] = screen
        c["hash"] = case_hash(c)
        out.append(c)
    return out, None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("file")
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--sheet", default=None)
    g.add_argument("--all-sheets", action="store_true")
    args = ap.parse_args()
    for stream in (sys.stdout, sys.stderr):  # Windows pipes default to cp1252
        stream.reconfigure(encoding="utf-8")

    path = Path(args.file)
    if not path.exists():
        sys.exit(f"File not found: {path}")
    sheets = load_sheets(path, args.sheet, args.all_sheets)

    result = []
    for screen, rows in sheets:
        cases, reason = parse_rows(rows, screen, blank_ids=args.all_sheets)
        if reason:
            if not args.all_sheets:
                if reason == "empty sheet":
                    sys.exit("Empty file.")
                sys.exit(f"Could not find a step/action column in headers: {rows[0]}\n"
                         f"Rename a column to one of: {ALIASES['action']}")
            print(f"skipped: {screen}: {reason}", file=sys.stderr)
            continue
        result += cases

    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
