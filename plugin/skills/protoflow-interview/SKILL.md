---
name: protoflow-interview
description: Interview the BA about the customer's domain — a guided Q&A (actors, current process, pain points, goals, scope, rules, volumes, outputs, existing systems, terms, data, constraints, risks, materials) captured as typed, conversation-sourced items in docs/_global/interview.md, plus a project brief docs/interview.html (tabs) and docs/interview-tree.html (tree). First asks whether customer materials exist — with none, it grounds the project itself (writes grounding, glossary, entities); with materials, it is the domain summary /protoflow-ground cross-checks. Use right after /protoflow-new; re-run to continue. Never reads materials/.
---

> **Pack root:** `${CLAUDE_PLUGIN_ROOT}`. In this pack's reference files, a path written as `<pack>/…` is under that root; project files (`devspec/`, `protoflow/`, `tests/`) stay relative to the working repo.

# protoflow-interview

Capture what the BA knows about the customer's domain **before** anyone reads the materials. The interview works in one of two modes, set by the BA's answer in Step 1:

- **Materials available or expected** → the interview is the **domain summary** that supports `/protoflow-ground`: a lens to read the materials through and a list of claims to check. You WRITE only `docs/_global/interview.md` and the brief pages `docs/interview.html` and `docs/interview-tree.html`.
- **No materials** → the interview is the project's **only source**, so it **covers grounding** too: after the Q&A you also WRITE `docs/_global/grounding.md`, `glossary.md`, and `entities.md` from the answers (Step 6), so `/protoflow-explore` and everything after it work as usual.

**You never read `materials/`.** Everything you record is what the BA said — conversation-derived, never a customer-confirmed fact.

Each session is self-contained: all state lives in the docs, never in conversation memory. A re-run resumes from them.

## Read first

All `${CLAUDE_PLUGIN_ROOT}/references/…` paths are relative to the **repo root**. Read `${CLAUDE_PLUGIN_ROOT}/references/item-header.md` (the four-field header), `${CLAUDE_PLUGIN_ROOT}/references/ids.md` (allocation + "Id-less items"), `${CLAUDE_PLUGIN_ROOT}/references/truth-vs-derived.md`, `${CLAUDE_PLUGIN_ROOT}/references/interview-brief.md` (the brief you render), and the shape you fill: `${CLAUDE_PLUGIN_ROOT}/references/templates/_global/interview.md`. In no-materials mode also read `${CLAUDE_PLUGIN_ROOT}/skills/protoflow-ground/SKILL.md` Steps 3–4 (the grounding item shapes and merge rules you reuse) and `${CLAUDE_PLUGIN_ROOT}/references/templates/_global/grounding.md`, `glossary.md`, `entities.md`.

## Input

`<project-id>` from the command argument.

- No project id → ask the BA for one.
- `protoflow/<project>/` missing → STOP: "No engagement `<project>`. Run `/protoflow-new <project>` first."
- `docs/_global/interview.md` missing (engagement created before this skill existed) → create it from `${CLAUDE_PLUGIN_ROOT}/references/templates/_global/interview.md`, replacing `<project>`.
- `grounding.md` already holds facts from materials (Materials index has a `yes`/`partial` row) → warn once: "Materials are already grounded — the interview is meant to come first. Continuing; re-run `/protoflow-ground <project>` afterwards so it cross-checks the interview." Then proceed in materials mode.

## Step 1 — Open the session

1. Ask the BA's name (needed for `Source:`), unless the `## Sessions` table already names one — then confirm it's the same person.
2. **Materials basis.** Ask with `AskUserQuestion`: *Has the customer provided materials (documents, spreadsheets, screenshots, manuals)?*
   - **Received** — files are (or will shortly be) in `materials/` → `Materials: available`.
   - **Expected later** — promised but not yet sent → `Materials: expected`.
   - **No materials** — the interview is the only source → `Materials: none`.

   Write it under `## Source basis` (`Materials:`, `Set: <today> by <BA>`, `Note:` with anything the BA adds). On a re-run, show the current basis and ask only whether it changed. A change from `none` to `available`/`expected` switches to materials mode; grounding already written from the interview stays — `/protoflow-ground` will cross-check it.
3. **Resume or start.** If `interview.md` already has real items (not template placeholders), this is a follow-up: show which topics are covered and how many open questions remain, then ask with `AskUserQuestion` (multiSelect) which topics to continue. Never re-ask a question already recorded — answered or not — unless the BA asks to revisit it.
4. Tell the BA in one line how it works: a topic at a time, a few questions each, answer in your own words, "skip" or "don't know" are fine answers. In no-materials mode add: "this is the only source, so the more precise, the better the spec."

## Step 2 — Interview, one topic at a time

Walk these topics in order (skip ones the BA chose not to cover). Per turn ask **2–4 questions on one topic** in plain chat and wait for the answer; use `AskUserQuestion` only where the answer is a choice (industry, in/out of scope, how sure they are). Never ask more than one topic per turn.

| # | Topic | Ask about | Writes to |
|---|-------|-----------|-----------|
| 1 | Domain & customer | industry, who the customer is (size, sites, market), the problem in one sentence, why now | `## Domain at a glance` |
| 2 | Stakeholders & actors | who uses it, who decides/pays, who is affected, external parties; rough headcount | `## Stakeholders & actors` |
| 3 | Current process | how the work happens today, step by step: who does what, with which tool | `## Current process (as-is)` |
| 4 | Pain points | what goes wrong, for whom, how often, what it costs | `## Pain points` |
| 5 | Goals & success | what "better" means; any number or deadline the customer uses to judge it | `## Goals & success measures` |
| 6 | Scope boundaries | what's clearly in, clearly out, unsure | `## Scope boundaries` |
| 7 | Business rules & limits | thresholds, approvals, deadlines, quotas, who may override, what is forbidden | `## Business rules & limits` |
| 8 | Volumes & frequency | number of users, transactions per day/month, peaks, history to keep | `## Volumes & frequency` |
| 9 | Outputs & notifications | reports, documents, exports; who is told what, when, by which channel | `## Outputs & notifications` |
| 10 | Existing systems & screens | software, spreadsheets, paper forms in use; what they show; replace, keep, or integrate | `## Existing systems & screens` |
| 11 | Key terms | words the customer uses with a special meaning, abbreviations | `## Key terms` |
| 12 | Key data | what they record and track; important fields, statuses, relationships | `## Key data` |
| 13 | Constraints | regulation, login/SSO, devices, languages, budget, deadline | `## Constraints` |
| 14 | Risks & sensitivities | politics, resistance, sensitive data, dependencies on other teams | `## Risks & sensitivities` |
| 15 | Materials | what the customer has sent or will send, and what each should settle (materials mode only) | `## Materials to expect` |

**Interviewing discipline:**

- **Follow up on vague words.** "Quickly", "a lot", "the manager", "usually" → ask for the number, the role, the exception. One follow-up per vague answer, then move on.
- **Use the BA's words.** Record terms as the BA says them; don't translate to generic vocabulary.
- **"It's in the documents."** In materials mode, don't press — record an `UNKNOWN` and add a "look for …" line to that material's row in `## Materials to expect`.
- **You may offer options, never answers.** When a question is a choice, the options may come from general knowledge of the domain (e.g. typical approval models) — but nothing is recorded unless the BA picks or states it. Never fill a gap from your own knowledge.
- **Don't spec.** This is domain understanding, not requirements: no screens to build, no field validation, no feature list. If the BA drifts into solution detail, note it in one line under the relevant topic and steer back.
- **Keep it moving.** Aim for the whole interview in about 15–20 turns. If the BA wants to stop early, stop — write what you have.

## Step 3 — Type every answer

Every captured point is an id-less `### <short label>` item with the four-line header (`Key terms` and `Materials to expect` are table rows instead). Labels are unique across `interview.md` — `/protoflow-ground` links back to them.

- **Status:** `proposed` — always. Only the customer or the materials can confirm it.
- **Type** — from how sure the BA is:
  - `FACT` — the BA states it as known ("they have three sites").
  - `ASSUMPTION` — the BA believes or guesses it ("I think only vehicles need approval"). Ask "are you sure, or is that your impression?" when it's unclear.
  - `UNKNOWN` — the BA doesn't know. Also add it to `## Open questions`, phrased as the question to answer.
  - Never `DECISION` (nothing has been agreed with the customer) or `CONFLICT` (unless the BA reports two sources disagreeing — then `CONFLICT`, "X says …; Y says …", never pick a side).
- **Source:** `BA interview <today> (<BA name>)`. If the BA cites where they learned it, append it: `BA interview 2026-10-08 (Jane) — from kickoff call`.
- **Confirmed:** blank.

## Step 4 — Play back and correct

Before writing, show the BA a compact recap — one line per item grouped by topic, with its type — and ask with `AskUserQuestion`: *looks right* / *fix something* / *add something*. Apply corrections (wording, type, removal) and repeat once if needed. This fixes what you heard; it does not confirm the facts.

## Step 5 — Write `interview.md` (merge, never clobber)

- **First run** (template placeholders still present): replace the placeholder blocks and `<…>` tokens with the real content. Keep every section heading and its italic intro line. Empty topics keep their heading with a one-line `_Not covered yet._` in place of the placeholder. In no-materials mode, `## Materials to expect` gets `_No customer materials — see Source basis._`.
- **Re-run:** add new items under the right section with targeted Edits. Skip duplicates (same claim). Never edit an item whose `Status:` is `confirmed` or whose `Confirmed:` is filled. A BA correction to a `proposed` item may update it in place. A new answer to an existing `## Open questions` item: add the answer as a new item in its topic section and mark the question `Status: rejected` with a last line `Answered: see <section> › <label>` — never delete it.
- Add one row to `## Sessions` per session: date, BA, topics covered.

## Step 6 — Ground from the interview (no-materials mode only)

Skip this step unless `## Source basis` says `Materials: none`. Here the interview stands in for the materials: apply `/protoflow-ground`'s item shapes and merge rules (its Steps 3–4) with the interview as the source instead of files.

- **`grounding.md`**
  - `## Business context` ← Domain at a glance, plus one short paragraph each on the actors and the current process, cited `(BA interview <date>)`.
  - `## Known facts` ← every interview `FACT` from the topic sections (actors, process steps, pains, goals, scope, rules, volumes, outputs, systems, constraints, risks). `## Assumptions` ← every `ASSUMPTION`. `## Open questions` ← every open `UNKNOWN` (not `rejected`). `## Contradictions` ← every `CONFLICT`. Copy each with its label, `Type:`, body, `Status: proposed`, and `Source: BA interview <date> (<BA>) › <label>` so the link back stays explicit. A business rule stays a FACT/ASSUMPTION — **never mint `BR-` ids**.
  - `## Materials index` ← one row: `| — | no customer materials | n/a | grounded from BA interview <date> |` (replace the template's example rows on first run).
  - **Never** write `## Feature scope` — that is `/protoflow-explore`.
- **`glossary.md`** ← one row per Key-terms row, `Source: BA interview <date>`. A term the BA marked `UNKNOWN`, or used two ways, goes under "Disputed / ambiguous terms".
- **`entities.md`** ← one `ENT-` item per Key-data item: `Type: FACT` if the BA named its fields, else `INFERENCE`; `Source: BA interview <date> › <label>`. Allocate ids exactly as `${CLAUDE_PLUGIN_ROOT}/references/ids.md` says (scan all of `docs/`, reserve the block up front). Update the mermaid `erDiagram` when ≥2 entities have stated relationships; otherwise leave the placeholder.
- **Merge:** on a re-run add only interview items not yet in grounding (match on the `› <label>` link); never touch a `confirmed` item; write with targeted Edits once a doc holds human content.

## Step 7 — Render the project brief

Regenerate both brief pages, `docs/interview.html` and `docs/interview-tree.html`, exactly as `${CLAUDE_PLUGIN_ROOT}/references/interview-brief.md` defines — from the whole `interview.md` (not just this session), with `basis` and each item's `check` derived from `grounding.md`. Never hand-edit it.

## Step 8 — Report

Print a short summary for the BA:

- materials basis; topics covered / skipped; items added by type (FACT / ASSUMPTION / UNKNOWN);
- the top open questions and the riskiest assumptions;
- no-materials mode: what was grounded (facts / assumptions / open questions copied, glossary rows, `ENT-` ids minted);
- materials mode: the reading guide — materials expected and not yet received, and what each should settle;
- the brief: `protoflow/<project>/docs/interview.html` (tabs view; its top bar links to the tree view `interview-tree.html`; both open straight from disk; print saves a PDF for the customer kickoff);
- next step by basis:
  - `none` → `/protoflow-explore <project>` (scope pass). If materials turn up later, drop them into `materials/` and run `/protoflow-ground <project>` — it cross-checks everything the interview grounded.
  - `expected` → when the files arrive, drop them into `materials/` and run `/protoflow-ground <project>`.
  - `available` → `/protoflow-ground <project>`.
  - Any basis: `/protoflow-interview <project>` again to cover skipped topics.

## Guardrails

- Never read `materials/`. If the BA pastes material content into the chat, record what they say about it, `Source: BA interview …`, and suggest dropping the file into `materials/` for grounding.
- Write `grounding.md`, `glossary.md`, `entities.md` and mint `ENT-` ids **only** in no-materials mode (Step 6). In materials mode those belong to `/protoflow-ground`.
- Never promote a BA statement to customer truth: every item stays `proposed`, never `DECISION`.
- Never invent: no answer → `UNKNOWN`, not your best guess.
- Never mint REQ/BR/FLOW/SCR/AC/UC ids; never write `## Feature scope`.
