---
name: testforge-gen
description: "Generate verified Playwright TypeScript E2E tests (Page Object + fixture + spec) for this repo from test cases. Input can be a CSV/TSV/XLSX export or freeform/pasted steps. Drives the live app with the Playwright MCP to capture REAL selectors, encodes them as Page Objects matching the repo basecode, runs the spec to prove it passes, and evolves a shared actions library by extracting repeated page actions. Use when the user says: write test case, generate e2e test, automate this test case, playwright test from CSV/Excel, convert test steps to code, scaffold a page object, capture selectors, record this flow, extract common actions, refactor page objects, testforge, TC-1, CARISDO-TC. Handles custom editable data grids (CyberLogitec IB grid, ag-Grid) that resist normal selectors."
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, mcp__playwright__browser_navigate, mcp__playwright__browser_snapshot, mcp__playwright__browser_find, mcp__playwright__browser_click, mcp__playwright__browser_fill_form, mcp__playwright__browser_type, mcp__playwright__browser_evaluate, mcp__playwright__browser_run_code_unsafe, mcp__playwright__browser_take_screenshot, mcp__playwright__browser_press_key, mcp__playwright__browser_wait_for, mcp__playwright__browser_close
---

> **Pack root:** `${CLAUDE_PLUGIN_ROOT}`. In this pack's reference files, a path written as `<pack>/…` is under that root; project files (`devspec/`, `protoflow/`, `tests/`) stay relative to the working repo.

# Testforge Gen

IRON LAW: NEVER ship a selector or a spec you have not verified against the live app. Capture the real DOM, then run the generated spec green before claiming done. No guessed selectors, no "should pass".

## Workflow

Copy this checklist and track it:

```
Testforge Gen Progress:
- [ ] Step 1: Load the case(s) ⚠️ REQUIRED
  - [ ] 1.1 Resolve input source (CSV / XLSX / freeform)
  - [ ] 1.2 Normalize to steps
  - [ ] 1.3 XLSX with 2+ case sheets → Workbook loop mode (L1–L4) instead of Steps 2–8
- [ ] Step 2: Read the repo basecode ⚠️ REQUIRED
- [ ] Step 3: Confirm plan with user ⚠️ REQUIRED
- [ ] Step 4: Capture real selectors from the live app ⛔ BLOCKING
- [ ] Step 5: Generate Page Object + fixture + spec
- [ ] Step 6: Run the spec until green ⚠️ REQUIRED
- [ ] Step 7: Evolve — extract common actions (offer)
- [ ] Step 8: Report (files, pass/fail, deviations)
```

## Step 1: Load the case(s) ⚠️ REQUIRED

Resolve where the steps come from:
- **CSV / TSV file, or XLSX with `--sheet NAME`**: run the reader (keeps the raw file out of context):
  ```bash
  python ${CLAUDE_PLUGIN_ROOT}/skills/testforge-gen/scripts/read_cases.py <file> [--sheet NAME]
  ```
  Launcher is `python` on Windows (no `python3` there); use `python3` / `py -3` if `python` is missing.
  A workbook in the common TestCase template (`TC #` / `Summary` / `Action` / … from `/testforge-convert`) reads directly. Generate only its `Type = Auto` cases.
- **XLSX without `--sheet`**: read every sheet into a temp dir (not the repo):
  ```bash
  T=$(mktemp -d)
  python ${CLAUDE_PLUGIN_ROOT}/skills/testforge-gen/scripts/read_cases.py <file> --all-sheets > $T/cases.json 2> $T/skipped.txt
  ```
  XLSX needs `openpyxl` (`python -m pip install openpyxl`); if absent, ask the user to install it or export CSV.
  Count the distinct `screen` values in `cases.json`:
  - **1** → re-run the reader with `--sheet <that screen>` (single-sheet mode numbers id-less
    rows itself) and continue with the normal flow below.
  - **2 or more** → go straight to **Workbook loop mode** (section below). Do not ask whether to
    loop or batch; gen runs the workbook itself. `/testforge-batch` appears only as a tip line
    under the loop-mode plan table — never a question, never an automatic hand-off.
- **Freeform / pasted steps**: use them directly; number the steps yourself.

Ask only if the source is ambiguous: "Is this a file path or pasted steps?"

## Step 2: Read the repo basecode ⚠️ REQUIRED

→ Load `references/codegen-conventions.md`, then READ the actual files it lists
(`base.page.ts`, existing `*.page.ts`, `test-fixtures.ts`, a sample spec, `playwright.config.ts`).
The pattern evolves — never generate from memory of a past run.

## Step 3: Confirm plan with user ⚠️ REQUIRED

Present a short plan and STOP for confirmation:
- Which case(s) → which files (`tests/pages/<x>.page.ts`, fixture edit,
  `tests/e2e/<module-slug>/<id>.spec.ts` — module is the feature name, kebab-cased;
  reuse the folder if it already exists).
- The app URL to drive and credentials source (env var vs. case values).
- Any step that looks impossible/ambiguous (flag it now).

Ask: proceed with all cases / only one / view plan only? ⚠️ Do NOT capture or write before confirmation.

## Step 4: Capture real selectors from the live app ⛔ BLOCKING

→ Load `references/playwright-capture.md`. Drive the app step by step, capturing the REAL
selector for each action. If a target is an editable grid/table with no cell inputs,
→ also load `references/custom-grids.md`.

Hard rules (full detail in the references):
- Use `browser_find` (regex) or scoped/`evaluate` queries — a full `browser_snapshot` on a
  real app overflows context. Return small structured objects, not DOM dumps.
- Prefer role/label/placeholder selectors; coordinates only for un-addressable widgets.
- Filter to the VISIBLE element when stale SPA tabs create duplicates.
- Confirm each action's observable effect before scripting the next.
- Test data: `TBD` means resolve a real value from the live app. A value tagged `[suggested]`
  (written by testforge-convert) is a synthetic sample: drop the tag, expand notation like
  `A×101` in code (`'A'.repeat(101)`), and check it against the live field (maxlength, dropdown
  options). If the app makes it impossible, adjust it and say so in the report.

## Step 5: Generate Page Object + fixture + spec

Following `references/codegen-conventions.md`:
1. Write `tests/pages/<feature>.page.ts` — `extends BasePage`, locators in constructor,
   actions as methods. All captured selectors/coordinates/grid quirks live HERE only.
2. Add one fixture property to `tests/fixtures/test-fixtures.ts`.
3. Write `tests/e2e/<module-slug>/<CASE-ID>.spec.ts` (UPPERCASE case id in filename) — extended `test`/`expect`,
   POMs via fixtures, one step-range comment block per group, assertions on observable state.
   The `test()` title is fully UPPERCASE: `test('CARISDO-TC-1: <TITLE IN CAPS>', ...)`.

## Step 6: Run the spec until green ⚠️ REQUIRED

```bash
npx playwright test <CASE-ID> --workers=1 --reporter=line --trace=retain-on-failure
```
`--workers=1` — shared server state (grids, records) makes parallel runs flaky.
`--trace=retain-on-failure` keeps a trace of the failing run — open with
`npx playwright show-trace` to see the exact DOM at the failure instead of re-capturing blind.
If it fails: read the error, re-capture the offending step (Step 4), fix the POM, re-run.
Do NOT edit the assertion to make a real failure pass. Loop until the exit code is 0.

## Step 7: Evolve — extract common actions (offer)

After 2+ Page Objects exist, offer to hoist repeated action sequences into a shared helper:
```bash
python ${CLAUDE_PLUGIN_ROOT}/skills/testforge-gen/scripts/extract_common_actions.py tests/pages
```
The script REPORTS candidates only. If the user approves a candidate:
- Create/extend `tests/pages/common.actions.ts` (or the repo's existing helper) with a named
  method for the sequence.
- Replace each occurrence, keeping behavior identical. Re-run affected specs (Step 6) —
  the refactor is not done until tests are still green.
⚠️ Do NOT auto-refactor without showing candidates and getting a pick.

## Workbook loop mode

Entered from Step 1 when an `.xlsx` has 2+ case sheets (one sheet = one screen). Gen runs every
screen itself, one at a time, with the same visible MCP capture as a single case. It differs from
the single-case flow in four ways: one plan for the whole workbook, names come from the planner,
each case is capped at 3 attempts, and a final full run closes the loop.

### L1. Plan and single confirmation

```bash
python ${CLAUDE_PLUGIN_ROOT}/skills/testforge-batch/scripts/plan_batch.py $T/cases.json --root . --skipped $T/skipped.txt > $T/plan.json
```
Exit 2 = over 100 cases or two sheets mapping to one slug. Relay the planner's message and stop.

Show the plan table (same columns as `/testforge-batch` Phase 1):

| Screen (sheet) | Slug / folder | POM | new | suffix | skip |
|---|---|---|---|---|---|

List skipped sheets with their reasons, the planner's `warnings`, and any `suffix` case
(`<ID>` → `<ID>-V<n>`). Then add one tip line (no question):

> Tip: `/testforge-batch <file>` runs screens in parallel (faster, headless capture).

**STOP.** Ask: "Generate **N** cases across **M** screens, one at a time in the visible browser?"
Write NOTHING under `tests/` before a yes. On no, end cleanly (if the user says they want batch
instead, repeat the command and stop).

Names, folders and spec ids come from `plan.json` only — POM `pomFile`/`pomClass`, fixture
`fixture`, spec `specFile`/`specId`, folder `tests/e2e/<slug>/`. Never hand-edit them; re-run the
planner instead. This keeps gen output identical to what `/testforge-batch` would produce.

### L2. Per-screen loop

For each `plan.screens` entry in order, taking only cases whose `action` is not `skip` (skip
cases are neither captured nor rewritten):
1. **Step 2** — first screen: full basecode read. Later screens: re-read only the POM/fixture
   files changed since the previous screen (unsure → re-read the codegen-conventions list).
2. **Step 4** — capture via the Playwright MCP, as for a single case.
3. **Step 5** — POM at `pomFile`: new, or extend when `pomExists` (add members, never remove or
   rename). One spec per case at `specFile`, `test()` title `'<specId>: <TITLE IN UPPERCASE>'`,
   and the **first line** of every spec is exactly `// testforge-source-hash: <hash>` (the case's
   `hash`), so a later gen or batch run skips unchanged cases. Add the screen's fixture to
   `tests/fixtures/test-fixtures.ts` in the existing `loginPage` shape
   (`<fixture>: async ({ page }, use, testInfo) => { await use(new <pomClass>(page, testInfo)); },`).
4. **Step 6, capped** —
   ```bash
   npx playwright test tests/e2e/<slug>/ --workers=1 --reporter=line --trace=retain-on-failure
   ```
   At most **3 attempts** per case, then move on:
   - `passed` — green in the last run.
   - `failed` — still red after 3 attempts; keep the spec, record the error. Never weaken an assertion.
   - `not-captured` — a step can't be captured after 3 attempts; delete that case's spec, record why.
   - A precondition that needs a server-side setting (role config, Program Configuration, user
     preference) → never change it (shared state). Read the current value: match → test the case;
     mismatch → `not-captured`, reason `requires <setting> = <value>, current = <value>`.
   One case failing never stops the other cases or screens.

Single-case gen (CSV, freeform, `--sheet`) is unchanged: it loops until green and
writes no hash header. Only loop mode caps attempts and writes the header.

### L3. Checkpoint per screen

After each screen, append its result to `$T/progress.json`:
```json
{ "screen": "<screen>", "specFiles": ["…"], "fixture": { "name": "…", "class": "…", "import": "../pages/<slug>.page" },
  "cases": [{ "specId": "…", "status": "passed|failed|not-captured", "attempts": 1, "deviations": ["…"], "error": "" }] }
```
and print one line: `<screen>: <passed>/<total> passed`.

**Resume:** if context was lost mid-loop (compaction), re-read `$T/plan.json` and
`$T/progress.json` and continue at the first screen missing from `progress.json`. Don't rely on
memory of earlier screens.

### L4. Final run, report, extract offer

1. Run every spec written in this loop once, with the configured reporters (this records history
   in `test-evidence/`):
   ```bash
   npx playwright test <all loop spec files> --workers=1 --reporter=line,html,./tests/common/test-report-reporter.ts
   ```
   `line` gives console output to paste. `html` plus the history reporter are the configured ones:
   a CLI `--reporter` replaces the config, so list all three.
2. Report in chat:

   | Screen | Spec | Status | Attempts | Deviations |
   |---|---|---|---|---|

   Status: `passed` (green in the final run), `failed`, `failed-in-fanin` (passed in its screen,
   red in the final run — a cross-screen regression), `not-captured`, `skip` (from the plan).
   Then list failed cases with their error, and link `test-evidence/report.html`.
3. Offer Step 7 (extract common actions) **once**, after the report.

## Anti-Patterns

- Guessing a selector from step text instead of capturing it (e.g. `name: 'Add New'` when
  the button says `Add`).
- Dumping a full `browser_snapshot` into context "to be safe" — it overflows; query instead.
- Raw selectors, coordinates, or class suffixes in the spec — they belong in the Page Object.
- `new PageClass()` in a spec instead of using a fixture.
- Fixed `waitForTimeout` sleeps as the primary sync — assert on state with `toPass`.
- Following a written step that hangs (a confirmation dialog that doesn't exist) — capture
  reality, encode what works, report the deviation.
- Hardcoding a fixed unique key that already exists server-side, making the test un-rerunnable.
- Claiming success without a green run and its exit code.
- Auto-hoisting common actions without user confirmation.
- Loop mode: asking for confirmation per sheet or per case. There is one gate, the plan table.
- Loop mode: retrying a case past 3 attempts, so one stuck case blocks every later screen.
- Loop mode: hand-editing slugs, ids or suffixes. `plan_batch.py` owns naming, so re-run it.
- Loop mode: offering the common-action extraction after each sheet instead of once at the end.
- Loop mode: asking "loop or batch?" or handing off to `/testforge-batch`. Batch is only a tip line.

## Pre-Delivery Checklist

- [ ] No `[TODO]`/placeholder text in generated files.
- [ ] Spec imports `test`/`expect` from `../fixtures/test-fixtures`, uses POM fixtures (no `new`).
- [ ] No raw selectors/coordinates in the spec; all in the Page Object.
- [ ] Every case step maps to a POM call, grouped with step-range comments.
- [ ] `npx playwright test <id>` exits 0 — pasted output, not asserted.
- [ ] Deviations from the written test case surfaced to the user.
- [ ] Credentials/baseURL from env with a documented fallback; no secret as sole source.
