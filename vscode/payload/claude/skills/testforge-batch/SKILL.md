---
name: testforge-batch
description: "Batch-generate verified Playwright E2E specs from a multi-screen Excel workbook (one sheet = one screen, up to 100 cases) using parallel per-screen agents. Reads every sheet, shows one plan table, and after a single confirmation fans out a Workflow (one agent per screen, each with its own headless browser, capped concurrency), then merges fixtures and runs the full regression. Use when the user says: batch, whole workbook, many test cases, excel with multiple screens/sheets, generate all cases, parallel generation, faster testforge, /testforge-batch. For a single case use testforge-gen instead."
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, Workflow
---

# Testforge Batch

IRON LAW (from `testforge-gen`): never ship a selector or spec that was not verified against the live app. A case is `passed` only after a green run you can paste.

Input: `<workbook.xlsx> [--concurrency N]` (default N = 5, min 1). A workbook converted by `/testforge-convert` (the common TestCase template) is valid input. Its `Type = Manual` rows are still in the sheet, so point them out in the plan table.

```
Testforge Batch Progress:
- [ ] Phase 1: Overview — read, plan, show table ⛔ STOP for confirmation
- [ ] Phase 2: Fan-out — Workflow, one agent per screen
- [ ] Phase 3: Fan-in — merge fixtures, full run, report
```

## Phase 1: Overview

1. **Python launcher.** Try `python --version`, then `python3`, then `py -3`, and use the first that works as `$PY` (Windows usually has only `python`).
2. **openpyxl.** `$PY -c "import openpyxl"`. If it's missing, tell the user to run `$PY -m pip install openpyxl` (or run it with their OK) before continuing.
3. **Read** into a temp dir (not the repo):
   ```bash
   T=$(mktemp -d)
   $PY .claude/skills/testforge-gen/scripts/read_cases.py <workbook> --all-sheets > $T/cases.json 2> $T/skipped.txt
   $PY .claude/skills/testforge-batch/scripts/plan_batch.py $T/cases.json --root . --skipped $T/skipped.txt > $T/plan.json
   ```
   Planner exit 2 = over 100 cases or a sheet-slug clash. Relay its message and stop.
4. **Show the plan table**:

   | Screen (sheet) | Slug / folder | POM | new | suffix | skip |
   |---|---|---|---|---|---|
   | Package Code | `package-code` | new / extend | 3 | 1 | 0 |

   Also list skipped sheets with their reasons, `warnings` (generated ids, slug fallbacks), and any `suffix` case (`<ID>` → `<ID>-V<n>`).

   **Run mode.** Read `.env` (Read tool) for `HEADED=` and `SLOWMO=` lines; a shell export of the same name also counts. `.env` missing or no `HEADED=true` → headless. Add one line under the table: `Run mode: headed (slowMo <n>ms)` or `Run mode: headless`. `playwright.config.ts` applies it to every run (agents and Phase 3), so agents need no extra flag. When headed and concurrency > 3, add: "headed windows use more CPU and may cause timeout flakiness; consider --concurrency 3".
5. **STOP.** Ask: "Generate **N** cases across **M** screens with concurrency **C**?" Write NOTHING under `tests/` before a yes. On no, end cleanly.

## Phase 2: Fan-out

Invoke the saved workflow with the plan as a real JSON object (not a string):

```
Workflow({ scriptPath: ".claude/skills/testforge-batch/workflows/testforge-batch.js",
           args: { plan: <plan.json contents>, concurrency: C,
                   repoRoot: "<absolute repo path>",
                   packRoot: ".claude",
                   briefPath: ".claude/skills/testforge-batch/references/agent-brief.md" } })
```

Each agent follows `references/agent-brief.md`. In short: it probes its own browser (`references/probe-capture.md`), never the MCP. It writes only its POM plus `tests/e2e/<slug>/`, never `test-fixtures.ts`. It runs its specs with `--reporter=line` and gives each case at most 3 attempts.

If the run is interrupted, relaunch with the same `scriptPath` + `args` and `resumeFromRunId` (finished screens return from cache). Screens in `failedScreens` are reported, never silently dropped.

## Phase 3: Fan-in

1. **Merge fixtures in ONE edit** to `tests/fixtures/test-fixtures.ts`. For each result's `fixture` not already present:
   - `import { <class> } from '<import>';` next to the other page imports
   - `<name>: <class>;` in `type Pages`, before `evidence`
   - `<name>: async ({ page }, use, testInfo) => { await use(new <class>(page, testInfo)); },` before `evidence`, the same shape as `loginPage`
2. **Typecheck.** `npx tsc --noEmit -p .`. The only acceptable error is the known `tests/e2e/example.spec.ts` arity one (`devspec/context/rules.md`). Anything else, fix it (usually a fixture typo) before running.
3. **Full run** of every spec file from all results, configured reporters (this records history in `test-evidence/`). It follows `HEADED` / `SLOWMO` from `.env` like every run, so with `HEADED=true` it is headed too:
   ```bash
   npx playwright test <all specFiles> --workers=1 --reporter=line,html,./tests/common/test-report-reporter.ts
   ```
   `line` gives console output to paste. `html` plus the history reporter are the configured ones: a CLI `--reporter` replaces the config, so list all three.
4. **Report** in chat:

   | Screen | Spec | Status | Attempts | Deviations |
   |---|---|---|---|---|

   Status values:
   - `passed`: green in the full run
   - `failed`: red in the agent
   - `failed-in-fanin`: passed in the agent, red in the full run (a cross-screen regression; do not re-dispatch automatically)
   - `not-captured`
   - `skip`: from the plan

   Then list the failed screens with their error, and link `test-evidence/report.html`.

Partial failure is normal. Keep every green spec, and never block the batch on one screen.

## Anti-Patterns

- Calling `mcp__playwright__*` from the batch or its agents. It's one shared browser, so agents collide.
- Asking for confirmation per case. There is one gate: the plan table.
- Letting agents edit `test-fixtures.ts`, or merging fixtures one at a time.
- Running agents' specs with the configured reporters. N processes would race on `runs.jsonl` / `report.html`.
- Weakening an assertion to turn a case green, or reporting `passed` without a run.
- Hand-editing slugs, ids or suffixes. `plan_batch.py` owns naming, so re-run it instead.

## Self-test

`$PY .claude/skills/testforge-batch/scripts/selftest_batch.py all` checks the reader and planner (grouping, naming, limits, collisions) without touching the repo.
