---
name: protoflow-spec
description: Specification phase — author one feature's discovery docs (requirements, rules, use cases + flows, screens, acceptance) under docs/features/<feature>/ from the grounding and the deep-dive, minting stable REQ/BR/UC/FLOW/SCR/AC ids and citing every item. Use after /protoflow-explore <project> <feature>, and again to extend or revise a spec. Never invents requirements nobody agreed to; never edits confirmed items.
---

# protoflow-spec

Turn grounded understanding + the deep-dive into a structured, traceable specification for **one** feature — the step before prototyping. **You READ the docs (and `materials/` for citations); you WRITE only `docs/features/<feature>/*`, plus `_global/rules.md`, `_global/entities.md`, and `_global/db-design.md` when a rule or entity is shared. Capture, don't design solo: anything you fill in yourself is typed `INFERENCE`/`ASSUMPTION`, never `FACT`.**

## Read first

All `.claude/references/…` paths are relative to the **repo root**. Read `.claude/references/item-header.md`, `.claude/references/ids.md` (allocation + id-less items), `.claude/references/grouping.md` (rule scope (a)), and the shapes in `.claude/references/templates/feature/*`, `.claude/references/templates/_global/{rules,entities,db-design}.md`.

## Input

`<project-id> <feature>` from the command argument.

- Either missing → ask the BA.
- `protoflow/<project>/` missing → STOP, point to `/protoflow-new`.
- `<feature>` is not a `confirmed` item under `## Feature scope` in `grounding.md` → STOP: list the confirmed feature ids, or point to `/protoflow-explore <project>` for the scope pass.
- `docs/features/<feature>/` missing (no deep-dive yet) → warn: "No deep-dive for `<feature>` — the spec will rest on grounding alone and carry more assumptions." Continue only if the BA agrees; then create the folder as the deep-dive would (titles + intros only).

## Step 1 — Gather

Read:
- `grounding.md` — Business context; every fact, assumption, open question, and conflict that concerns this feature; the feature's Feature-scope item (its provenance).
- `docs/features/<feature>/*` — the deep-dive's id-less items (questions, answers as `DECISION`, assumptions) and any id'd items from a previous spec run.
- `_global/entities.md`, `_global/rules.md`, `_global/db-design.md`, `glossary.md`.
- Every other feature's `rules.md` — to spot a rule this feature shares with another (rule scope (a)).

## Step 2 — Allocate ids

Per `ids.md`: scan **all** of `protoflow/<project>/docs/` for the highest existing number of each type — `REQ`, `BR`, `UC`, `FLOW`, `SCR`, `AC`, `ENT` (rejected ones count). Draft the full item list first (Step 3), count how many of each type you need, then reserve the blocks and assign sequentially. Ids are project-global, zero-padded, never reused.

## Step 3 — Author

Write in this order, so every cross-reference points at an id that already exists:

1. **Rules (`BR-`) → `rules.md`.** One single testable statement each, `Applies to:` the REQ ids (fill after step 2). A rule another feature also needs → see Step 5.
2. **Requirements (`REQ-`) → `requirements.md`.** One behavior each: `SHALL:` (exactly one "The system SHALL …" sentence) and ≥1 `Scenario: WHEN … THEN …` (the main case first, then each alternate/error path from the deep-dive). `Rules:` and `Entities:` list ids. A requirement maps 1:1 onto a DevSpec requirement at handoff, so keep it small enough to test.
3. **Use cases (`UC-`) → `flows.md` `## Use cases`.** One per actor goal: Actor, Goal, Preconditions, Main path, `Requirements:` ids.
4. **Flows (`FLOW-`) → `flows.md` `## Flows`.** Trigger, numbered Steps (cite `BR-` where a rule is checked), `Rules:`, `Screens:`, and a mermaid `flowchart` matching the steps. Label every edge leaving a decision (`D -->|no| X`); the flow library draws its swimlane from this block.
5. **Screens (`SCR-`) → `screens.md`.** Purpose; `Fields:` bound to entity fields (`amount (ENT-002.amount)`); `Actions:` → `FLOW-`; `States:` (at least empty / error / success where they apply); `Flows:`, `Entities:`; an ASCII sketch. These are what `/protoflow-prototype` renders, so name every field and action.
6. **Acceptance (`AC-`) → `acceptance.md`.** Given / When / Then, observable outcome only; `Verifies:` REQ (and BR) ids. **At least one AC per REQ**, plus one per BR that can be violated.

Every item gets the four-line header, `Status: proposed`, `Confirmed:` blank.

## Step 4 — Type every item from its source

- A grounding `FACT` the item restates → `Type: FACT`, same `Source:` as the fact.
- A deep-dive answer (`DECISION`, `Source: meeting …`) → `Type: DECISION`, same `Source:`.
- A comparable-system baseline the customer confirmed in scope, detail not yet discussed → `Type: INFERENCE`, `Source: comparable: <system>`.
- Anything you fill in yourself → `Type: INFERENCE` (reasonable) or `ASSUMPTION` (a guess to confirm), `Source: AI-inferred (from <what>)`.
- **Never** type an item `FACT` unless a material states it.

**Open questions stay open.** A deep-dive `UNKNOWN` that is still unanswered stays an `UNKNOWN` item (keep its label; move it to the right doc if needed). If it bears on a specific requirement, add that `REQ-` id to the UNKNOWN's body ("Affects REQ-014.") — this is the attachment the `/protoflow-status` health gate checks. A `CONFLICT` stays a `CONFLICT`; write the REQ around the undisputed part and cite the REQ id in the conflict body.

## Step 5 — Rule scope (a) and shared entities

- A rule this feature shares with another feature: if it is already in `_global/rules.md`, reference its id under "Referenced cross-cutting rules" in this feature's `rules.md` — don't restate it. If it currently sits in the other feature's `rules.md`, **move** it to `_global/rules.md` keeping its id (`Spans features:` both), and replace the local block with a reference in both features. If the moved rule is `confirmed`, ask the BA before moving.
- A noun the feature stores that has no `ENT-` yet → add it to `entities.md` (`Type: INFERENCE` unless a material defines its fields), update the mermaid `erDiagram`, and add a matching `db-design.md` table (`Type: INFERENCE`, `Source: ENT-xxx`).

## Step 6 — Merge, never clobber

- On first run, the feature docs hold the deep-dive's id-less items. Convert each into id'd items: an answered question becomes part of a REQ/BR/SCR (its `Source: meeting …` carried over); an assumption becomes an `ASSUMPTION`-typed id'd item or part of one. Remove the id-less block once its content lives in an id'd item. Leave still-open `UNKNOWN`s and `CONFLICT`s as id-less items.
- On re-run: never edit, reword, or remove an item whose `Status:` is `confirmed` or whose `Confirmed:` is filled — propose a new item alongside and tell the BA. Never renumber. A dropped item becomes `Status: rejected` (id retired), not deleted. Write with targeted Edits once a doc holds human content.

## Step 7 — Check and report

Before finishing, verify:
- every `Rules:` / `Entities:` / `Screens:` / `Flows:` / `Verifies:` / `Requirements:` id exists;
- every REQ has ≥1 AC verifying it;
- no id was used twice across the project.

Then regenerate the registry the way `.claude/skills/protoflow-status/SKILL.md` defines (or tell the BA to run `/protoflow-status <project>`), and report: ids minted per type; items typed FACT / DECISION / INFERENCE / ASSUMPTION; open questions and conflicts still attached to REQs (the agenda for the customer); next step `/protoflow-prototype <project>` — and, if other confirmed features have no spec yet, `/protoflow-explore <project> <next-feature>` or `/protoflow-spec <project> <next-feature>`.
