---
name: protoflow-prototype
description: Prototype phase — compile docs/ into product-model.json, render the interactive spec dashboard docs/spec.html, and scaffold a throwaway clickable prototype (HTML/CSS/JS + SQLite-WASM with seed data) under prototype/ that looks and behaves like the real website — one product page per SCR-, business rules enforced, traceability kept in a hidden review layer. Re-runs regenerate only what changed. Use once a feature is specced, and after every doc change during customer review. Never edits docs/ to fit the prototype.
---

# protoflow-prototype

Give the customer fast, executable feedback grounded in the current spec. The prototype is proof-of-understanding — thrown away, not shipped; the docs are what seed real development. **You READ `docs/` (truth) and WRITE only derived output: `product-model.json`, `docs/spec.html`, the registry, and `prototype/`. Data flows docs → model → prototype, never back.**

**The customer must feel they are using the real product, not reading a spec.** Every screen renders as a page of a live website: branded navigation, a fitting page type, the customer's own wording, realistic data. Traceability is fully kept, but it lives in a review layer the BA switches on (`data-ref`, `ctx.note`, the review panel), never in the page body. `.claude/references/prototype-ui.md` is the binding contract for how screens look and read.

**Split of work.** Everything deterministic — parsing the docs, the model, `spec.html`, per-screen context, review notes, the SQLite schema, seed expansion + DB check, screens.js, the screen-writer brief, change detection, manifest hashes, the registry — is done by one script, `.claude/references/scripts/protoflow_compile.py` (standard-library Python, run from the repo root). Spend your effort only on what needs judgement: page design, copy, seed content, the screen modules. Never hand-compile what the script produces. **Speed comes from writing less:** the `ui.js` kit + its CSS mean a screen is data, handlers and a few kit calls; the seed is a compact spec; the schema, screen list, review notes and screen-writer brief are generated; screen agents get a one-line prompt.

## Read first

All `.claude/references/…` paths are relative to the **repo root**. The skill is **domain-neutral**: nothing in the shell, kit or script assumes a shop, a booking tool or any other product type — the docs decide what the product is.
- Always: `.claude/references/prototype-ui.md` (the customer-view contract and done checklist).
- When writing shared files (first run, or `app.js` / seed / test spec stale): `.claude/references/templates/prototype/app.example.js`, `test.spec.example.json`, and the export list of `ui.js` (the kit — skim the one-line comments, don't study the bodies).
- Screen writers read **only** `prototype/.slices/_brief.md` + their own slice. Don't read the raw feature docs or `product-model.md` to write a screen; open a doc only when a slice leaves something unclear.

## Input

`<project-id> [feature]` from the command argument.

- No project id → ask. `protoflow/<project>/` missing → STOP, point to `/protoflow-new`.
- No feature is `specced` or beyond (the script's report shows each feature's status) → STOP: "Nothing to prototype yet — run `/protoflow-spec <project> <feature>` first."
- A `feature` argument limits Steps 3–4 to that feature's screens; the model, dashboard and registry always cover the whole project. During customer review, prefer re-running with the feature that changed.

## Timing

Record a timestamp (`date +%T`) at the start of each step and report the step durations at the end — they show where the next speed-up should go.

## Step 1 — Compile, slice, notes, plan (one command)

```bash
python .claude/references/scripts/protoflow_compile.py <project> --slices --notes --plan
```

It regenerates `product-model.json` (shape: `.claude/references/product-model.md`) and `docs/spec.html`, writes one compact context file per screen to `prototype/.slices/<SCR-id>.json`, writes `prototype/notes.js` (every screen's open items — assumptions, open questions, conflicts — as review-only notes the router renders under the page, so screens don't hand-write them), and prints a JSON report:
- each feature's status and live screen ids, `dbDesignTables`, `entities`;
- `plan`: `new` / `stale` / `unchanged` / `orphaned` / `handEdited` prototype files, from `prototype/.manifest.json`.

The plan decides the rest of the run:
- **unchanged** → don't open, don't rewrite. On a re-run after a small doc edit this is most of the prototype — a re-run with nothing stale is just Step 1 + Step 6 (seconds).
- **new / stale** → (re)generate in Steps 3–4.
- **orphaned** (its `SCR-` is now rejected or gone) → delete the module (`--screens` drops it from `screens.js`). Never delete a feature folder whose docs still exist.
- **handEdited** (GENERATED banner missing, or content differs from what the manifest recorded) → ask the BA before overwriting.
- No manifest yet → everything is new.

If the script fails on a doc, fix nothing in `docs/`: report the parse problem and the doc location, and stop.

## Step 2 — Shell (write once, then preserve)

If `prototype/` has no shell yet, copy `index.html`, `app.css`, `ui.js`, `db.js`, `router.js`, `serve.py` from `.claude/references/templates/prototype/`, replacing `__PROJECT__` with the project id and `__PRODUCT__` with the product name. Theme by editing only the token block at the top of the copied `app.css` (`--brand`, `--brand-soft`, `--radius`, `--display` font, `--max` width) — pick a color that fits the customer's brand or industry. If the shell exists, leave it — the BA may have tuned it. Never copy the `*.example.*` files. An engagement scaffolded under an older shell keeps it; delete the shell files to regenerate them against the current templates.

`ui.js` is the **domain-neutral component kit**: page head, crumbs, buttons, icons, placeholder images (`art`), media cards, amounts (with a previous value struck through), label/value lists (`kv`), timelines, badges, stats, tables, tabs, side menu, split layout, forms and inline errors, busy state, number stepper, option pills, swatches, checkbox lists, range slider, filter sidebar, chips, toolbar, load-more, gallery, progress steps, conversation (`chat`), skeletons + `loading()`, empty and result states, and overlays (drawer, modal, confirm, sheet, toast card) that close on Esc / backdrop / navigation. Every builder skips `null`/`false` children. `app.css` already styles every one of them, plus hover/scroll-reveal motion (`class: "reveal"`). Screens compose the kit; they don't re-invent markup or CSS.

The shell is chrome-free for the customer; the review panel (⋯ tab bottom-right, or the `` ` `` key) holds review mode, show ids, "View as", reset data. Routing is path-based (`/<feature>/<SCR-id>`), so `serve.py` (SPA fallback, correct `.js` MIME types, works from any folder) must serve it. The router also exposes `window.protoSelftest()` (Step 5).

## Step 3 — Shared files (only when new or stale)

Generated by the script (don't hand-write): `schema.sql` (from `db-design.md`) and `screens.js` (from the docs + `test.spec.json`). Written by the lead (judgement): `seed.spec.json`, `app.js`, `test.spec.json`, a few lines of theme. In this order:

1. **Schema:** `python .claude/references/scripts/protoflow_compile.py <project> --schema`. It translates every `db-design.md` table to SQLite (types, PK, FK, `not null`, `unique`, `check`, `default`, indexes, a range → `<name>_start`/`<name>_end`) and lists the constraints SQLite can't express as `-- app-level:` comments for the screens that own those rules. Only when `db-design.md` has no tables, write `schema.sql` by hand from `entities.md` (one table per `ENT-`, its id in a comment) and say so in the report.
2. **`seed.spec.json` → `seed.sql`:** write the compact spec, never the SQL — literal `rows` in `cols` order for hand-picked records (personas, the rows each BR needs), `_helper` tables and `each` blocks for bulk (child rows per parent, combinations, repeated records). Dates are tokens (`"@now-3d"`, `"@date+10d"`) so the product always looks current. Full syntax: `SEED_HELP` in the script. Content: 3–8 plausible rows per table (more where a screen needs content to browse), consistent across FKs, at least one row per status value, rows that let each BR be demonstrated, one seeded user per persona and state the screens need, fictional names in the customer's locale, never personal data from `materials/`. Then `--seed --check-db`: it writes `seed.sql`, loads schema + seed into SQLite (the engine the browser runs) and reports SQL errors, FK violations, row counts, empty tables and `statesWithoutRows`. Fix the spec until `ok: true`.
3. **`app.js`:** the product chrome in the `app.example.js` shape — brand, primary navigation from confirmed Feature-scope items (specced → entry screen, unspecced → "coming soon"), account area, footer, "View as" personas (one per use-case actor and state), enum labels, date/number/money formatting, sign-in guard, `t()` when a requirement asks for several languages. Put here every piece of domain UI or logic more than one screen uses (a shared card, a calculation, a state change several flows make), plus a **lazy opener for every overlay screen other screens open** (`export const openX = async (ctx, …) => (await import("./<feature>/SCR-x.js")).open(ctx, …)`) and a `hostPage(ctx)` for overlay screens opened by URL. Each `export` gets a one-line `//` comment directly above it — the brief lists them, and turns each opener into a contract for the screen's writer. A big domain piece may go in a GENERATED helper module in the owning feature's folder; export it the same way.
4. **`test.spec.json`** (shape: `test.spec.example.json`): `entry` (the screen `/` opens), `samples` per screen (persona/params visits worth checking — each state, each persona that sees something different), and `walks`: one per FLOW happy path and one per BR reachable from the UI. The labels in walks are a contract — choose the wording the docs use for buttons and fields. Then `--screens` writes `screens.js` (features in Feature-scope order, entry feature first, samples, WALKS).
5. **Theme** in `app.css`: the token block, plus at most a few lines under "engagement touches" for what the kit lacks.
6. **Brief:** `--brief` → `prototype/.slices/_brief.md`: screen rules, `ctx` API, the `ui.js` and `app.js` export lists, personas, cross-screen contracts, and every walk/sample — the one file screen writers read.

Steps 1–6 can be chained once the hand-written files exist: `python .claude/references/scripts/protoflow_compile.py <project> --schema --seed --check-db --screens --brief`.

## Step 4 — One module per screen (parallel)

For each **new or stale** screen, write `prototype/<feature>/<SCR-id>.js` from its slice + the brief. Screens are independent once Step 3 is done, so parallelize by **screen**, not feature:
- ≤ 2 screens to write → write them yourself.
- More → batches of about 2 screens (balanced by size; keep a tiny overlay with the page that opens it), one subagent per batch, all in one message so they run in parallel, `model: "sonnet"`. The brief carries everything screen-specific (contracts, walk labels, samples), so the prompt is the same template for every batch — don't restate rules or contracts in it:

  > Write the ProtoFlow prototype screens `<SCR-a>`, `<SCR-b>` for project `<project>`. Read `protoflow/<project>/prototype/.slices/_brief.md` and your slices `.slices/<SCR-a>.json`, `.slices/<SCR-b>.json` (skim `app.js` / `ui.js` only for signatures). Write only `prototype/<feature>/<SCR-x>.js` for each, with the Write tool, then `node --check` each. Satisfy every contract and walk in the brief that names your screens. Reply with 2 lines per screen: page type + anything you couldn't do or assumed.

- Spot-check what comes back against the brief's rules before Step 5 (don't re-read every line).

**Design the page first, then wire it.** Pick one page type from prototype-ui.md (Landing, Dashboard, List, Detail, Form / wizard, Conversation, Decision dialog, Result, Back-office) from the SCR's Purpose, Fields, Actions, actor and flow, and lay it out the way a real product of that type would. The field list is the data the page shows, not the layout. A Purpose line is never a subtitle. **Simulated externals** (AI, payment, email, maps…): `ui.delay(500–1000)`, a busy/processing state, plausible output, `ctx.note("Simulated", …)`.

## Step 5 — Self-test, then a quick look

Start the server (`python protoflow/<project>/prototype/serve.py`, or the browser preview). In the page, run `await window.protoSelftest()` at desktop width, and again at 375px **unless** a `DECISION` says the prototype is desktop-only. It visits every screen sample and runs every walk, and reports: leaked spec ids/words, raw enum codes, `null`/`undefined`/`NaN`/`[object …]`, ISO timestamps, stray `0`/`true`/`false` text, sideways scroll, empty pages, render failures, console errors (overlays included), and `walkProblems` (the step that failed and why). Data is reset before and after. A full run takes well under a minute; if the browser tool times out, start it with `.then(r => window.__st = r)` and poll `window.__st`.

Fix every reported problem in the generated files (never in `docs/`). Re-check only what you fixed with `protoSelftest({ only: ["SCR-x", …] })`, then finish with one full run until `ok: true`. The walks replace manual click-through; what remains is judgement:
- open review mode once: screen list and notes visible, "show ids" tags heading, actions and rule messages;
- one or two screenshots for visual sanity (entry page + the busiest page).

Prefer `javascript_tool` / `get_page_text` over screenshots; screenshots can time out when the pane is hidden. If no browser is available, say so in the report and list the checklist as not verified.

## Step 6 — Manifest, registry, report

```bash
python .claude/references/scripts/protoflow_compile.py <project> --manifest --registry
```

This recompiles the model (features with a `prototype/<feature>/` folder are now `prototyped`), records sources and hashes for every GENERATED file in `.manifest.json`, and regenerates `docs/INDEX.md` + `docs/board.yml` exactly as `/protoflow-status` defines. Then tell the BA:

- files regenerated vs unchanged (from the Step 1 plan); screens per feature; rules enforced in-app (incl. app-level constraints from `schema.sql`);
- the step durations (Timing);
- how to open it: `python protoflow/<project>/prototype/serve.py` → <http://localhost:8000> (http, not `file://`; internet for the SQLite-WASM CDN on first load);
- the review panel (⋯ bottom-right or `` ` ``): review mode, show ids, "View as", reset data;
- the page type chosen for each screen, and which parts are simulated;
- `docs/spec.html` was regenerated (opens directly from disk);
- the assumptions, open questions and conflicts attached as review notes — the review agenda;
- the self-test result (samples + walks) at each width, or that it could not be run;
- next step: review with the customer. Changes → `/protoflow-spec <project> <feature>`, then re-run `/protoflow-prototype <project> <feature>` (only changed screens are rewritten). Sign-off → mark REQs `confirmed` (`Confirmed: <date> by <name>`) and run `/protoflow-handoff <project> <feature>`. Unspecced features → `/protoflow-spec <project> <next-feature>`.

## Customer change requests during review

When the customer asks for a change while clicking through: (1) say which items it affects ("this changes REQ-004 and BR-002"), (2) update the docs following the `/protoflow-spec` rules — a confirmed item gets a new proposed item alongside, not an edit; a new requirement is `Source: meeting <today>`, (3) re-run this skill; the plan will show only the affected screens as stale. **Never patch the prototype ahead of the docs.**

## Guardrails

- Never edit `docs/` to make the prototype easier; if the spec can't be rendered (e.g. a SCR with no fields), report the gap and render what exists.
- Never let the review layer leak into the customer view: no spec ids or spec words in visible text or toasts, no on-page "Open question" text, no screen list outside review mode (prototype-ui.md).
- Never invent features to make a page look complete. Navigation and cards show only confirmed Feature-scope items; unspecced ones show "coming soon".
- Never connect to or import from a customer production database; seed data only.
- Never copy personal data from `materials/` into `seed.sql`.
- Never hand-edit `product-model.json`, `spec.html`, `.slices/`, `notes.js`, `seed.sql`, `.manifest.json`, `schema.sql`, `screens.js` or the registry — re-run the script (edit `seed.spec.json` for seed changes).
