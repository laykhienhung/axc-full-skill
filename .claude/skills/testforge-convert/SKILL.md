---
name: testforge-convert
description: "Convert ONE sheet of a manual QA checklist workbook (columns like No. / Testcase ID / Test Case Desc. / Precondition / Steps / Check point / Expected Result / Status / Priority / Remark, with coloured section-header rows) into the common TestCase template (TC # / Type Manual-Auto / Summary / Test Repository Path / Priority / Must-have Regression / Pre_Condition / Action / Input Data / Test check Point / Expected Result). Rewrites each case into aligned numbered steps, classifies Auto vs Manual, numbers TC # as PREFIX_SECTION_NNN, validates, and writes a styled .xlsx that /testforge-gen and /testforge-batch can read directly. Use when the user says: convert test case, convert checklist, manual test case to template, standardize test cases, common template, TestCase Sample format, reformat excel test cases, /testforge-convert. Does not touch the live app."
allowed-tools: Read, Write, Bash, Glob, Grep, Agent
---

# Testforge Convert

IRON LAW: never invent test data. Every value in the output comes from the source case. Anything missing is written `TBD`. The one exception is a synthetic Input Data sample whose shape the step's wording fixes (a length, a character class, an invalid format, a page size the source names), and it must end with ` [suggested]`. Business data such as codes, names and accounts stays `TBD`. The scripts own the TC # values and the xlsx layout; Claude only rewrites case text.

Input: `<checklist.xlsx> [--sheet NAME] [--out path]`. One sheet per run.

```
Testforge Convert Progress:
- [ ] 1. Setup (python + openpyxl)
- [ ] 2. Pick the sheet
- [ ] 3. Extract
- [ ] 4. Gate: show plan ⛔ STOP for confirmation
- [ ] 5. Convert (inline, or parallel chunk agents)
- [ ] 6. Write + validate (fix rounds ≤ 2)
- [ ] 7. Report
```

Scripts live in `.claude/skills/testforge-convert/scripts/` (`$S` below).

## 1. Setup
Try `python --version`, then `python3`, then `py -3`, and use the first that works as `$PY`. Run `$PY -c "import openpyxl"`. If openpyxl is missing, ask the user to run `$PY -m pip install openpyxl`, or run it yourself with their OK. Work in `T=$(mktemp -d)`, never in the repo.

## 2. Pick the sheet
No `--sheet` given → `$PY $S/extract_manual.py <file> --list`. Show the sheets that have cases and their counts, and ask which one to convert. Sheets marked "no Desc + Steps header" are in a different format (formula sheets, data-validation matrices) and can't be converted.

## 3. Extract
```bash
$PY $S/extract_manual.py <file> --sheet "<sheet>" --chunks-dir $T/chunks --chunk-size 40 > $T/extract.json
```
This gives you `suggest` (prefix, screen, repo_path), `groups` (section → ABBR, count) and `cases`. Each case carries its section `path`, the inherited `section_pre`, and the source fields. Read `extract.json` with the Read tool and don't print it to chat.

## 4. Gate ⛔
Show one table and the proposals:

| Group (section) | ABBR | Cases | TC # range |
|---|---|---|---|
| Permission | PERM | 8 | OEMBLL_PERM_001–008 |

- Prefix: `suggest.prefix`. Screen / output sheet name: `suggest.screen`.
- Test Repository Path: `suggest.repo_path`. It's built from the Information sheet's `Module(s):`. Tell the user they may want to add their numbering, e.g. `CARIS Upgrade/1. Ocean Export/...`.
- Must-have Regression: `General`.
- Output: `--out`, or by default next to the source: `<stem> - <sheet> (template).xlsx`. If that file already exists, say so: the writer refuses to overwrite unless `--force` is passed.
- Note `hidden_rows` if it's non-zero. Those rows are collapsed outline groups in the source, and they're still converted.

STOP and ask: "Convert **N** cases with prefix **P**? (edit prefix / path / ABBRs if needed)". Write edited abbreviations to `$T/abbr.json` as `{"<group name>": "ABBR"}`.

## 5. Convert
Follow `references/conversion-rules.md` exactly. Read it before you convert anything.
- **≤ 40 cases:** convert inline and write the list to `$T/converted_1.json`.
- **More:** launch one `general-purpose` Agent per chunk file, at most 5 at a time and all in one message per wave. Brief each one with:
  - the absolute paths of `references/conversion-rules.md`, its `chunk_<k>.json` and the output file `$T/converted_<k>.json`
  - "Convert every case in the chunk, keep each `key`, write a JSON list, reply only `done <count>`"

  An agent must not edit anything else.

## 6. Write + validate
```bash
$PY $S/write_template.py $T/extract.json $T/converted_*.json --out "<out>" --prefix <P> \
    --repo-path "<path>" [--abbr $T/abbr.json] [--sheet-name "<screen>"]
```
Exit 2 means validation failed and nothing was written. stderr has one JSON line per bad `key` with its errors: misaligned numbering, a bad type or priority, missing or duplicate keys. Re-convert **only those keys** into `$T/converted_fix<round>.json`. Delete the bad entries from the earlier files first, or the writer reports them as duplicates. Then re-run. Do at most 2 fix rounds; after that, report the keys that still fail and don't write a partial file.

## 7. Report
- Output path and the writer's summary: total, Auto/Manual, priorities, TC # range, and the `suggested` / `tbd` Input Data counts. Ask the user to review the `[suggested]` values; they are samples, not source data.
- Per-group counts.
- Manual cases: TC #, summary and `type_reason`. Collapse them by reason when there are more than 15.
- Next step: `/testforge-gen "<out>"` for a few cases, or `/testforge-batch "<out>"` (≤ 100 cases per run). Both read `TC #`, `Summary`, `Pre_Condition`, `Action`, `Input Data` and `Expected Result`. Mention that Manual cases are still in the file, so they should pick which Auto cases to automate.

## Anti-Patterns
- Filling a value the source doesn't have (an account, a code, a message text) instead of `TBD`.
- A suggested value without the ` [suggested]` tag, a tag outside Input Data, or a guessed business code or account written as a suggestion.
- Hand-writing TC # values, or editing the xlsx after the writer. Re-run the writer instead.
- Multi-line steps, or Expected Result with more or fewer lines than Action. This breaks the step alignment that testforge-gen relies on.
- Converting several sheets in one run, or skipping the gate.
- Letting Status, Remark or bug IDs decide Type.

## Self-test
`$PY $S/selftest_convert.py` checks offline, in a temp dir:
- extraction (section levels, inherited preconditions, groups, ABBRs)
- writer validation and TC # numbering, `[suggested]` placement and counts
- the round trip through `read_cases.py`
