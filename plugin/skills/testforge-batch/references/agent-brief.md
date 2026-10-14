# Screen agent brief (testforge-batch, Phase 2)

You are ONE screen agent in a parallel batch. Other agents are generating other screens at the same time, against the same live app, in the same repo. Your job is to turn your screen's cases into verified Playwright specs, stay strictly inside your own files, and return a structured result. The orchestrator merges fixtures and runs the full regression afterwards.

IRON LAW (inherited from `testforge-gen`): never ship a selector you have not verified against the live app, and never report `passed` without a green run you actually executed.

## Inputs (in your prompt)

- `screen`: the plan entry: `screen`, `slug`, `pomFile`, `pomClass`, `fixture`, `pomExists`, and `cases[]`. Each case has `specId`, `specFile`, `title`, `hash`, `preconditions`, `steps`, `expected`, `data` (test inputs, may be empty or a placeholder like `<existing bkg no>` or `TBD` you must resolve from the live app; a value tagged `[suggested]` is a synthetic sample: drop the tag, expand `A×101` as `'A'.repeat(101)`, check it against the live field and adjust it if needed, noting the change), `action`. Only `new`/`suffix` cases are sent.
- `repoRoot`: absolute repo path. Run every command from there.
- App target: `BASE_URL` from `.env`. Login: `TEST_USER` / `TEST_PASS` / `TEST_TENANT` from `.env`. Concurrent logins as the same user are allowed.
- Run mode: `HEADED` / `SLOWMO` in `.env` are applied by `playwright.config.ts` to every `npx playwright test` run, so with `HEADED=true` your runs open a visible browser on their own. Add no `--headed` flag and never change `.env`. Probe scripts stay `headless: true` in both modes.

## Read first (do not generate from memory)

1. `<pack>/skills/testforge-gen/references/codegen-conventions.md`: authoritative for every file you write.
2. Basecode:
   - `tests/pages/base.page.ts`: `BasePage`; also has `navigateSidebar(top, submenu)`.
   - `tests/pages/login.page.ts`: login steps.
   - `tests/common/env.ts`: `requireCreds()`.
   - `tests/common/locators.ts`: `fieldByLabel()`, `clickFirstVisible()`.
   - `tests/fixtures/test-fixtures.ts`: READ ONLY.
   - `tests/e2e/example.spec.ts`.
3. `devspec/improve/gotchas.md`: app traps (hidden duplicate toolbar buttons, label-adjacent inputs, sidebar viewport).
4. `<pack>/skills/testforge-batch/references/probe-capture.md`: how you capture selectors.
5. If a case targets an editable grid (IBSheet / ag-Grid), also `<pack>/skills/testforge-gen/references/custom-grids.md`.
6. If `pomExists` is true, read the existing `pomFile` fully. You EXTEND it (add locators/methods) and never remove or rename existing members.
7. Do NOT mine git history (`git log` / `git show` of deleted POMs or specs) for a starting point. Removed tests were removed on purpose. Build from the live app plus the current basecode only.

## Files

| You MAY write | You MUST NOT touch |
|---------------|--------------------|
| `pomFile` (your screen's Page Object) | `tests/fixtures/test-fixtures.ts` |
| `tests/e2e/<slug>/*.spec.ts` for your cases only | any other `tests/pages/*.page.ts` |
| probe scripts under `<os.tmpdir()>/testforge-probe/<slug>/` | `tests/common/*`, `playwright.config.ts`, `.env`, other module folders |

FORBIDDEN tools: every `mcp__playwright__*` tool. The MCP is one shared browser and other agents would collide with you. Capture only via probe scripts.

## Specs: because the fixture isn't merged yet

Your POM's fixture does not exist until Phase 3. So that your specs run now **and** stay correct after the merge, each spec does this:
- imports `{ test, expect }` from `../../fixtures/test-fixtures`
- uses the fixture name `<fixture>` exactly as in your plan
- is run by you through a **temporary local fixture shim**: write `tests/e2e/<slug>/_batch-fixture.ts` that extends the shared `test` with only your fixture (`<fixture>: async ({ page }, use, testInfo) => { await use(new <pomClass>(page, testInfo)); }`), and during your runs import from `./_batch-fixture` instead.

Before you return, switch every spec's import back to `../../fixtures/test-fixtures` and **delete `_batch-fixture.ts`**. Report the fixture entry in your result; the orchestrator adds it.

## Spec rules (on top of codegen-conventions)

- First line of every spec is exactly: `// testforge-source-hash: <hash>`, using the case's `hash`.
- Filename = `specFile`. `test()` title = `'<specId>: <TITLE IN UPPERCASE>'`.
- One `test()` per case. Every case step maps to a POM call, with step-range comments.
- Credentials via `requireCreds()`. No literal secrets.
- Unique keys per run for any record you create (`Date.now().toString(36)`), with a comment saying so. Other agents hit the same server.
- No raw selectors in specs. They belong in the POM.

## Run and fix loop

```
npx playwright test tests/e2e/<slug>/ --workers=1 --reporter=line --trace=retain-on-failure
```
`--reporter=line` is mandatory. It replaces the configured reporters, so you do not write `test-evidence/runs.jsonl` / `report.html` concurrently with other agents.

- Per case, at most **3 attempts**. On a failure, read the error (and the trace), re-probe the failing step, fix the POM, re-run.
- Never weaken or delete an assertion to get green. A real failure stays `failed`.
- Could not capture a step at all (grid you can't drive, element you can't find) after 3 tries → `not-captured`, with the reason. Leave no half-written spec for it: delete that spec file.
- Precondition needs a server-side setting (role config, Program Configuration, user preference) → never change it; it is shared state. Read the current value: if it matches, test the case; if not → `not-captured`, reason `requires <setting> = <value>, current = <value>`.
- One case failing never stops the others. Finish every case.
- Reality differs from the written step (label text, missing dialog) → encode what works, record it in `deviations`.

## Cleanup before returning

- `_batch-fixture.ts` deleted; spec imports point at `../../fixtures/test-fixtures`.
- The probe directory `<os.tmpdir()>/testforge-probe/<slug>/` is deleted.
- `git status --short` shows only your `pomFile` and your `tests/e2e/<slug>/` specs.

## Return (structured)

```json
{ "screen": "<screen>", "pomFile": "<pomFile>", "specFiles": ["tests/e2e/<slug>/<specId>.spec.ts"],
  "fixture": { "name": "<fixture>", "class": "<pomClass>", "import": "../pages/<slug>.page" },
  "cases": [{ "specId": "…", "status": "passed|failed|not-captured", "attempts": 1,
              "deviations": ["…"], "error": "" }],
  "notes": "anything the orchestrator must know" }
```
`specFiles` lists only specs that exist on disk (so `not-captured` cases are absent). `status: passed` requires that the case passed in your last run.
