---
name: protoflow-guide
description: Final stage — publish the engagement as a flow library in guides/ — one self-contained HTML site (plus Markdown) listing every feature with its status (Final / Blocked / In review / No flow yet), and for each flow plain numbered Steps (who acts, screen, every branch spelled out) with a zoomable swimlane Diagram as the alternative view (Input · actor · System · Output lanes, labelled decisions, exception branch), plus short cards for inputs, outputs, states and terms. A Team view toggle adds ids, blockers and the REQ/BR/AC behind each flow. Domain-neutral — works for any engagement. Use once at least one feature is specced; re-run whenever the docs change. Never edits docs.
---

# protoflow-guide

Publish what the engagement has settled as a **flow library**: one page per process flow, readable by the customer and usable by the team to build and test. **You READ `docs/`, `product-model.json` and `prototype/app.js`; you WRITE only `product-model.json` and `guides/`.**

**Split of work.** One script, `.claude/references/scripts/protoflow_compile.py`, does the deterministic parts. It parses each FLOW's mermaid graph, drafts lanes, nodes, inputs, outputs, lifecycles and team detail, validates, and renders. You do only the judgement in Step 4. Never hand-write `library.html` / `library.md`, and never hand-compile what the script drafts.

Each run is self-contained: all state lives in the docs, plus the refined `guides/library.json` from the previous run.

## Read first

All `.claude/references/…` paths are relative to the **repo root**. Read `.claude/references/user-guide.md`: the contract, with feature statuses, the `LIBRARY` shape, the draft heuristics, the validation rules and the reader-vs-team split. Also read `.claude/references/prototype-ui.md` › what the customer must never see. Skim `.claude/references/templates/library.html` only if a view bug needs fixing.

## Input

`<project-id>` from the command argument.

- No project id → ask the BA for one.
- `protoflow/<project>/` missing → STOP: "No engagement `<project>`. Run `/protoflow-new <project>` first."
- `guides/` missing → create it.

## Step 1 — Compile and draft

```bash
python .claude/references/scripts/protoflow_compile.py <project> --library-draft
```

This regenerates `product-model.json`. FLOWs carry `graph` parsed from their ```` ```mermaid ```` block. It also writes the draft:

- **No `guides/library.json` yet** → the draft is written there. Refine all of it (Step 4).
- **`library.json` exists** → the draft goes to `guides/.library.draft.json`. The report's `libraryDraft.diff` lists `new`, `changed` and `removed` flows, plus features whose `status` changed. Merge only those into `library.json`:
  - copy new flows from the draft and refine them;
  - replace changed flows from the draft and refine them again;
  - drop removed ones;
  - update the changed statuses, blockers and team detail.
  
  Leave unchanged flows as they are. If the diff is empty and no status changed, skip to Step 5.

If the script fails on a doc, report the parse problem and the doc location, and stop. Never fix `docs/` here.

## Step 2 — Gate

From the report's feature statuses (the `/protoflow-status` ladder):

- No feature is `specced` or beyond → STOP. List each feature with its status and its next command from the Next-steps table in `.claude/skills/protoflow-status/SKILL.md`. Say: "There are no flows to publish yet — run `/protoflow-spec <project> <feature>` first."
- Otherwise show the BA one line per status: Final / Blocked / In review / No flow yet, with the features in each. Then continue. Don't ask for confirmation; the library is derived and cheap to regenerate.

## Step 3 — Read what the draft needs

For each flow you refine, read its slice of the model: the FLOW (steps, rules, screens), the use cases sharing its REQs (actors), its screens (titles, fields, actions), and the glossary. Open a feature doc only when the model leaves something unclear.

## Step 4 — Refine `guides/library.json` (the judgement)

Edit only `guides/library.json`. Per flow:

1. **Lanes:** one actor lane per role that acts in the flow, named the way the customer names it ("Mod / Admin", "Warehouse clerk"). Add a second actor lane only when the FLOW shows a hand-off between roles.
2. **Each node's lane:** what the person does or decides → their lane. What the system checks, stores, computes or sends → System. A decision belongs to whoever answers it.
3. **Platform** per step: "Web" / "Mobile" / "System (auto)" / "Master data" / "Email" / …, as the docs say. **Screen** on actor steps, using the screen title.
4. **Branches:**
   - Every decision has ≥2 outgoing edges, each labelled with its answer.
   - When a decision really has one path (a choice of buttons that lead to the same step), make it a step ("Choose Resolve or Dismiss").
   - When the docs state an "otherwise" the mermaid omits, add that edge.
   - Never invent a branch the docs don't state.
5. **Exception phase** (`phase: "exception"`): only nodes reached through an error / rejection branch.
6. **Inputs / outputs:**
   - Keep the inputs the flow really consumes, at most about four. Type each one: "Master data" for reference data, "Record" for transactional data, "Document" for files.
   - Outputs are what the flow produces, with `when`.
7. **Titles and summaries:**
   - Feature `title`: a readable name ("Q&A accepted answer", not the folder id).
   - One plain sentence `summary` per feature and flow, in the docs' language.
   - Nothing marketing-like, and no comparable-system provenance notes.
8. Keep `steps` in sync with the nodes (step, role, screen).
9. **Labels read as steps.** The default Steps view prints node and edge labels as plain sentences, so write a step as a short action ("Create the account"), a decision as a question ("Username free?"), and an edge label as its answer ("yes", "no", "newest"). Mark an error / rejection target `phase: "exception"` so it shows as "If not" instead of a numbered step.

Reader text never holds spec ids, item types, sources or statuses: everything except `id`, `ref` and `team`. Never invent behavior, screens, messages or rules the docs don't state. Leave a field empty instead.

For a large project, refine features in parallel, one subagent per batch of about four features, all in one message, `model: "sonnet"`. Each subagent edits a separate scratch JSON holding only its features. You then merge the results into `library.json`.

## Step 5 — Validate and render

```bash
python .claude/references/scripts/protoflow_compile.py <project> --library
```

On `ok: false`, fix each listed error in `library.json` and re-run until `ok: true`. This writes `guides/library.html` and `guides/library.md`, and makes the merged draft the baseline for the next diff.

## Step 6 — Look at it

Serve `guides/` over http (`python -m http.server <port> --directory protoflow/<project>/guides`, or a launch.json entry and the browser pane) and check:

- the index (ready count, status filter, search);
- one busy flow at desktop width, in both views: **Steps** (numbering, who acts, "Checks" groups, every branch says where it goes) and **Diagram** (lanes, branch labels, legend, zoom and fit); Copy for AI;
- Team view: ids, blockers and REQ/BR/AC appear;
- the light and dark themes.

Then run a JS scan over every route (`LIBRARY.features` → `#/f/<f>` and `#/f/<f>/<flow>`) with Team view off, once with `localStorage["pfl-view"]` = `"steps"` and once `"diagram"`. The visible text of `#main` must have no `(REQ|BR|UC|FLOW|SCR|AC|ENT)-\d` and no `undefined` / `NaN` / `[object`. Fix what you find in `library.json`, or in the template if it is a view bug. If no browser is available, say so in the report.

## Step 7 — Report

Tell the BA:

- the files written under `protoflow/<project>/guides/`;
- the features per status, with each blocked feature's blockers;
- flows drawn, how many were refined this run (new / changed), and any flow the docs leave too thin to draw well (no mermaid, no steps). That gap belongs in `/protoflow-spec`;
- the file opens straight from disk. Print / PDF gives a copy to send. Team view is for the project team;
- re-run `/protoflow-guide <project>` after any doc change. The library is not updated by other commands;
- next in ProtoFlow: the features not final, each with its next command from the Next-steps table.

## Guardrails

- **Never write outside `guides/`** (plus `product-model.json`). Never edit `docs/`, `prototype/` or `handoff/`. If the docs are wrong or a flow can't be drawn, say which item and stop there: fix the docs, not the library.
- `library.html`, `library.md` and the draft files are script output. Never patch them, and never ask the BA to hand-edit anything in `guides/`.
- Never include `rejected` items; never put spec ids or review-layer wording in reader text.
- Never invent steps, branches, screens, messages or rules the docs don't state.
- Never send, publish or upload the library; sharing it is the BA's step.
