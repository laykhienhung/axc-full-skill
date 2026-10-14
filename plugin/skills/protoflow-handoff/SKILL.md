---
name: protoflow-handoff
description: Handoff phase — for one confirmed, healthy feature, emit a CLT-DevSpec-native change folder (proposal, design, spec, tasks, db, ui + mockups) plus TestForge test cases and a trace table into handoff/<feature>/, keeping every ProtoFlow id visible. Refuses while the feature has an unresolved CONFLICT, an open question on a confirmed requirement, or unconfirmed requirements. Emits files only — never edits the DevSpec board or anything outside handoff/.
---

> **Pack root:** `${CLAUDE_PLUGIN_ROOT}`. In this pack's reference files, a path written as `<pack>/…` is under that root; project files (`devspec/`, `protoflow/`, `tests/`) stay relative to the working repo.

# protoflow-handoff

Convert a feature's confirmed discovery docs into a package a developer picks up in CLT-DevSpec, keeping the traceability chain intact (source → REQ/BR → spec → task → test). **Copy, don't translate:** `requirements.md` already uses SHALL + WHEN/THEN, so it maps onto DevSpec `spec.md` directly. **You READ `docs/` (and `prototype/` for mockups); you WRITE only `product-model.json` and `handoff/<feature>/`.**

## Read first

All `${CLAUDE_PLUGIN_ROOT}/references/…` paths are relative to the **repo root**. Read `${CLAUDE_PLUGIN_ROOT}/references/ids.md`, `${CLAUDE_PLUGIN_ROOT}/references/registry.md` (health gate), `${CLAUDE_PLUGIN_ROOT}/references/product-model.md`, and every file in `${CLAUDE_PLUGIN_ROOT}/references/templates/handoff/` — its `README.md` says which DevSpec skill each shape comes from. Those templates are the format contract; don't improvise headings.

## Input

`<project-id> <feature>` from the command argument.

- Either missing → ask. `protoflow/<project>/` or `docs/features/<feature>/` missing → STOP and say which.
- One feature → one change; the change id **is** the feature id.

## Step 1 — Gate (refuse rather than emit something unhealthy)

Run the `/protoflow-status` scan for this feature (as `${CLAUDE_PLUGIN_ROOT}/skills/protoflow-status/SKILL.md` defines). STOP and list the exact blocking items when any of:

- its Handoff is `blocked` — an unresolved `CONFLICT` item, or an `UNKNOWN` attached to a confirmed REQ;
- any non-rejected `REQ-` is not `Status: confirmed` (the customer hasn't signed off the whole feature);
- it has no non-rejected `REQ-` or no `AC-`.

The message names each blocker with its id/label and doc, and says how to clear it: "resolve the conflict in `rules.md` and mark it confirmed/rejected", "confirm REQ-007 with the customer", then re-run `/protoflow-status` and `/protoflow-handoff`. Unconfirmed BR/FLOW/SCR/AC don't block, but list them as warnings in the report.

## Step 2 — Recompile the model

Regenerate `product-model.json` in full as `${CLAUDE_PLUGIN_ROOT}/references/product-model.md` defines — run `python ${CLAUDE_PLUGIN_ROOT}/references/scripts/protoflow_compile.py <project>` (the same compile as `/protoflow-prototype` Step 1; it also refreshes `docs/spec.html`), so handoff reads the current docs. Work from that model plus the docs below. Skip `Status: rejected` items everywhere except proposal Out-of-scope.

## Step 3 — Emit `handoff/<feature>/`

Number the feature's confirmed REQs in doc order as `[req-1]`, `[req-2]`, … — this mapping is used by every file below and recorded in `TRACE.md`. Fill each template from `${CLAUDE_PLUGIN_ROOT}/references/templates/handoff/`; no YAML frontmatter anywhere.

1. **`proposal.md`** — Why = the Business context narrowed to this feature + its Feature-scope item and provenance; What this delivers = the main use case and confirmed REQs as observed behavior; In scope = one bullet per REQ (`<title> (REQ-xxx)`); Out of scope = rejected REQ/BR and neighbouring features the flows hand off to. Don't add `_approved_by` — DevSpec's own approval adds it.
2. **`spec.md`** — one `### Requirement: <title> (REQ-xxx) [req-N]` per confirmed REQ: the REQ's SHALL sentence verbatim (exactly one SHALL), then each `Scenario: WHEN … THEN …` as `#### Scenario: <short label>` with `- **WHEN** …` / `- **THEN** …` bullets (no GIVEN). Finish each with a `Rules:` line listing its BR ids with their statements (cross-cutting ones marked). Every requirement needs ≥1 scenario — if a REQ has none, STOP and send the BA back to `/protoflow-spec`.
3. **`design.md`** — Approach from the use cases + flows and the architecture module; Architecture as an ASCII flow of the FLOW steps (screens → steps → rule checks → tables); a Business rules table (BR id, statement, where enforced); Impact Area:
   - Decision Defaults — one row per `DECISION` item that settles a gray area (from deep-dive answers) and per `ASSUMPTION` item (the assumption as the default; fallback "ask the BA" unless one was discussed);
   - Blast Radius — the architecture modules and tables touched, each tagged `safe/reversible` or `risky/irreversible`, with "(paths to confirm by dev)" — ProtoFlow has no view of the codebase, never invent file paths;
   - Risk / reversibility — anything destructive, or "None identified at discovery; additive only."
4. **`db.md`** — only if the feature's REQ/SCR cite `ENT-` ids with `db-design.md` tables: `**Source**: file-derived (…)`, `**Dialect**:` from db-design/architecture (else "unspecified"), one `### <table>  (new)` grid per table with `| col | type | null | default | note |` (note = PK/FK/unique + the `ENT-xxx.field` it came from), Impact (other features sharing the table), Open questions (db-related UNKNOWNs, else "None.").
5. **`ui.md` + `mockups/`** — only if the feature has `SCR-` items: one `## <screen name> (SCR-xxx)` block per screen with Layout (the SCR ASCII sketch verbatim), States, Interactions (actions → flow steps, rule messages), Components ("to confirm by dev — …"). For each screen write `mockups/<scr-id-lowercase>-<slug>.html`: **one self-contained static file** (inline CSS, no scripts, no CDN), the screen's structure from the SCR (and the prototype screen if it exists), with every listed state stacked as labeled sections down the page (empty / error / success …) — DevSpec's rule is that states are visible by scrolling, not clicking.
6. **`tasks.md`** — a draft for `/devspec-plan` to refine (keep the italic draft line). One `## N. <REQ title> [req-N]` section per requirement; subtasks `- [ ] N.M [layer] …` derived from the REQ's links — `[db]` for its tables (migration, additive only), `[backend]` for the SHALL + each BR to enforce, `[frontend]` for each SCR, `[test]` for each AC verifying it. Each section ends with a `Verify:` line naming its AC ids; when no automated check is obvious use `Verify: MANUAL: BA confirms AC-xxx in the running app` **and** add the matching `- [ ] N.x MANUAL: …` box. Never name source files you haven't seen.
7. **`testforge/<feature>-cases.csv`** — one row per non-rejected `AC-`, header exactly as the template: TC ID = AC id; Area = `<feature> / <SCR-id>` from the AC's flow/screen; Test Scenario = AC title; Pre-condition = Given; Test Steps = the When, split into numbered lines inside one quoted cell; Test Data = concrete values from the AC or `-`; Expected Result = Then; Type = `Negative` when it verifies a BR violation, else `Positive`; Priority = `High` for ACs on the main scenario, else `Medium`; Tags = `REQ-xxx [req-N] AC-xxx BR-xxx`. Standard CSV quoting (`"` doubled). TestForge has no requirement link of its own — Tags is how the trace survives.
8. **`TRACE.md`** — one row per REQ, BR, FLOW, SCR, ENT, AC of the feature: ProtoFlow id → where it landed.

## Step 4 — Coverage check before finishing

- Every `[req-N]` in `spec.md` appears in `tasks.md`, and `tasks.md` cites no `[req-N]` that `spec.md` lacks (DevSpec's req-coverage rule).
- Every REQ has ≥1 AC row in the CSV.
- Every id in `TRACE.md` exists in the docs.

Fix the output, not the docs, if a check fails; if the docs themselves are incomplete, STOP and report.

## Step 5 — Write rules

- `handoff/<feature>/` is derived. If it already exists, show what changed in the docs since (by id) and ask before overwriting; then replace the folder's contents in full.
- **Never write outside `handoff/<feature>/`** (plus `product-model.json`). Don't create or edit `devspec/changes/` or `devspec/changes/tasks.yml`; never push, open a PR, or call an external service.

## Step 6 — Report

Regenerate the registry (`${CLAUDE_PLUGIN_ROOT}/skills/protoflow-status/SKILL.md`) — the feature is now `handed-off`. Then tell the BA:

- files emitted, `[req-N]` count, AC/test-case count, any warnings (unconfirmed BR/FLOW/SCR/AC);
- next steps for the dev team: copy `handoff/<feature>/` to `devspec/changes/<feature>/`, review with `/devspec-plan`, and register it on the board — print a ready-to-paste entry:

  ```yaml
    <feature>:
      title: <feature title>
      tasks_md: changes/<feature>/tasks.md
      depends_on: []        # + features whose cross-cutting BR/ENT this one relies on, if already on the board
      skills: []
      status: pending
      owner: ""
      notes: "from ProtoFlow <project> — see TRACE.md"
  ```

- TestForge: `testforge/<feature>-cases.csv` loads with `testforge-gen` (`read_cases.py`);
- next in ProtoFlow: the other features not yet `handed-off`, each with its next command per the Next-steps table in `${CLAUDE_PLUGIN_ROOT}/skills/protoflow-status/SKILL.md` (e.g. `/protoflow-handoff <project> <other-feature>` for one that is `confirmed` + `ready`); and `/protoflow-guide <project>` to refresh the flow library with this feature.
