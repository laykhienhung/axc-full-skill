#!/usr/bin/env python3
"""Self-test for the batch tooling: read_cases.py (--all-sheets) and plan_batch.py.

Usage: python selftest_batch.py [reader|planner|collision|all]   (default: all)
Builds throwaway workbooks / repo trees in a temp dir; never touches the real repo.
"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
READER = HERE.parent.parent / "testforge-gen" / "scripts" / "read_cases.py"
PLANNER = HERE / "plan_batch.py"
HEAD = ["ID", "Title", "Preconditions", "Steps", "Expected Result"]


def run(script, *args):
    p = subprocess.run([sys.executable, str(script), *map(str, args)],
                       capture_output=True, text=True, encoding="utf-8")
    return p.returncode, p.stdout, p.stderr


def workbook(path, sheets):
    import openpyxl
    wb = openpyxl.Workbook()
    wb.remove(wb.active)
    for title, rows in sheets.items():
        ws = wb.create_sheet(title)
        for r in rows:
            ws.append(r)
    wb.save(path)


def check(cond, msg):
    if not cond:
        raise AssertionError(msg)
    print(f"  ok  {msg}")


def plan(tmp, cases, root=None):
    cj = tmp / "cases.json"
    cj.write_text(json.dumps(cases), encoding="utf-8")
    return run(PLANNER, cj, "--root", root or tmp)


def case(cid, screen, steps, pre="", title="t"):
    return {"id": cid, "title": title, "preconditions": pre, "screen": screen,
            "hash": "", "steps": [{"n": i + 1, "action": s, "expected": ""}
                                  for i, s in enumerate(steps)], "expected": ""}


def test_reader(tmp):
    print("reader")
    wb = tmp / "book.xlsx"
    workbook(wb, {
        "Login": [HEAD,
                  ["LOGIN-TC-1", "Login ok", "", "Open login", "Form shown"],
                  ["", "", "", "Submit creds", "Home shown"],
                  ["LOGIN-TC-2", "Login  BAD", "", "OPEN   login ", "form shown"]],
        "Package Code": [HEAD,
                         ["PKG-TC-1", "Add", "", "1. Open\n2. Add row\n3. Save", "1. a\n2. b\n3. c"],
                         ["PKG-TC-2", "Search", "", "Search", "Grid"],
                         ["PKG-TC-3", "Delete", "", "Delete", "Gone"]],
        "Cover": [["Workbook", "Owner"], ["Carrier", "QA"]],
    })
    code, out, err = run(READER, wb, "--all-sheets")
    check(code == 0, f"reader exits 0 (stderr: {err.strip()})")
    cases = json.loads(out)
    check(len(cases) == 5, "5 cases across 2 sheets")
    check([c["screen"] for c in cases].count("Login") == 2, "2 cases on screen Login")
    check([c["screen"] for c in cases].count("Package Code") == 3, "3 cases on screen Package Code")
    check("skipped: Cover: no step/action column" in err, "Cover skipped on stderr")
    check(len(cases[0]["steps"]) == 2, "numbered rows accumulate into one case")
    check(len(cases[2]["steps"]) == 3, "multiline step cell split into 3 steps")
    check(all(len(c["hash"]) == 12 for c in cases), "every case has a 12-hex hash")

    noise = tmp / "noise.xlsx"
    workbook(noise, {"A": [HEAD, ["X-1", "t", "", "Open login", "form shown"]],
                     "B": [HEAD, ["X-2", "t", "", "  OPEN   Login ", "Form   SHOWN"]]})
    c2 = json.loads(run(READER, noise, "--all-sheets")[1])
    check(c2[0]["hash"] == c2[1]["hash"], "hash ignores case/whitespace noise")

    code, out, _ = run(READER, wb)
    single = json.loads(out)
    check(code == 0 and len(single) == 2 and "screen" in single[0], "without --all-sheets only the active sheet (Login) is read")
    check(list(single[0].keys())[:5] == ["id", "title", "preconditions", "steps", "expected"],
          "existing keys keep their order without the flag")

    noid = tmp / "noid.xlsx"
    workbook(noid, {"Screen": [["Title", "Steps"], ["A", "1. x\n2. y"], ["B", "z"]]})
    c3 = json.loads(run(READER, noid, "--all-sheets")[1])
    check(len(c3) == 2 and c3[0]["id"] == "", "no id column: titled rows are separate cases, id blank")


def test_planner(tmp):
    print("planner")
    root = tmp / "repo"
    (root / "tests" / "e2e").mkdir(parents=True)
    (root / "tests" / "pages").mkdir(parents=True)
    (root / "tests" / "pages" / "package-code.page.ts").write_text("", encoding="utf-8")
    code, out, err = plan(tmp, [case("CBE-1", "Carrier Booking Entry", ["a"]),
                                case("PKG-1", "Package Code", ["b"]),
                                case("", "Package Code", ["c"], title="no id")], root)
    check(code == 0, f"planner exits 0 ({err.strip()})")
    p = json.loads(out)
    s = p["screens"][0]
    check(s["slug"] == "carrier-booking-entry", "slug carrier-booking-entry")
    check(s["pomFile"] == "tests/pages/carrier-booking-entry.page.ts", "POM file path")
    check(s["pomClass"] == "CarrierBookingEntryPage", "POM class CarrierBookingEntryPage")
    check(s["fixture"] == "carrierBookingEntryPage", "fixture carrierBookingEntryPage")
    check(s["cases"][0]["specFile"] == "tests/e2e/carrier-booking-entry/CBE-1.spec.ts", "spec path")
    check(not s["pomExists"] and p["screens"][1]["pomExists"], "pomExists reflects tests/pages")
    check(p["screens"][1]["cases"][1]["specId"] == "PACKAGE-CODE-2" and p["warnings"],
          "missing id -> <SLUG-UPPER>-<n> + warning")

    sk = tmp / "skipped.txt"
    sk.write_text("skipped: Cover: no step/action column\n", encoding="utf-8")
    cj = tmp / "cases.json"
    p = json.loads(run(PLANNER, cj, "--root", root, "--skipped", sk)[1])
    check(p["skippedSheets"] == [{"sheet": "Cover", "reason": "no step/action column"}],
          "Cover listed under skippedSheets, no screen for it")
    check(all(x["screen"] != "Cover" for x in p["screens"]), "no Cover screen")

    code, _, err = plan(tmp, [case(f"T-{i}", "S", ["x"]) for i in range(101)], root)
    check(code == 2 and "split the workbook" in err, "101 cases refused")
    code, _, err = plan(tmp, [case("A", "Package Code", ["x"]), case("B", "package-code", ["y"])], root)
    check(code == 2 and "Package Code" in err and "package-code" in err, "slug clash names both sheets")


def test_collision(tmp):
    print("collision")
    root = tmp / "crepo"
    e2e = root / "tests" / "e2e" / "login"
    e2e.mkdir(parents=True)

    def spec(sid, h):
        head = f"// testforge-source-hash: {h}\n" if h else ""
        (e2e / f"{sid}.spec.ts").write_text(head + "import x;\n", encoding="utf-8")

    spec("LOGIN-TC-1", "abc")
    spec("OLD-1", None)
    spec("TWO-1", "aaa")
    spec("TWO-1-V2", "bbb")

    def one(cid, h, extra=None):
        cs = [dict(case(cid, "Login", ["x"]), hash=h)] + (extra or [])
        return json.loads(plan(tmp, cs, root)[1])["screens"][0]["cases"]

    c = one("LOGIN-TC-1", "abc")[0]
    check(c["action"] == "skip", "unchanged case -> skip")
    c = one("LOGIN-TC-1", "def")[0]
    check(c["action"] == "suffix" and c["specId"] == "LOGIN-TC-1-V2"
          and c["specFile"].endswith("LOGIN-TC-1-V2.spec.ts"), "changed case -> -V2")
    c = one("TWO-1", "ccc")[0]
    check(c["specId"] == "TWO-1-V3", "-V2 taken -> -V3")
    c = one("TWO-1", "bbb")[0]
    check(c["action"] == "skip" and c["specId"] == "TWO-1-V2", "hash match on -V2 -> skip")
    c = one("OLD-1", "zzz")[0]
    check(c["action"] == "suffix" and c["specId"] == "OLD-1-V2", "hashless legacy spec -> suffix")
    cs = one("NEW-1", "h1", [dict(case("NEW-1", "Login", ["y"]), hash="h2"),
                             dict(case("NEW-1", "Login", ["x"]), hash="h1")])
    check([x["action"] for x in cs] == ["new", "suffix", "skip"]
          and cs[1]["specId"] == "NEW-1-V2", "in-workbook duplicates: new, suffix, skip")


def main():
    which = sys.argv[1] if len(sys.argv) > 1 else "all"
    tests = {"reader": test_reader, "planner": test_planner, "collision": test_collision}
    if which != "all" and which not in tests:
        sys.exit(f"unknown part {which}; use reader|planner|collision|all")
    with tempfile.TemporaryDirectory() as t:
        for name, fn in tests.items():
            if which in ("all", name):
                fn(Path(t))
    print("PASS")


if __name__ == "__main__":
    try:
        main()
    except AssertionError as e:
        print(f"FAIL: {e}")
        sys.exit(1)
