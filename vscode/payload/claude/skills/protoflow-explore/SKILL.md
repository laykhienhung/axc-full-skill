---
name: protoflow-explore
description: Exploration phase, in two passes. Scope pass (no feature) proposes the feature spine from grounding.md plus web research on comparable real systems, provenance-tagged, and records the customer's sign-off under ## Feature scope. Deep-dive (feature id) explores one confirmed feature — scenarios, rules, edge cases, open questions — into its docs/features/<feature>/ folder as a resumable session. Use after /protoflow-ground and before /protoflow-spec. Never writes requirements ids or touches the prototype.
---

# protoflow-explore

The discussion step between grounding and specification, run **breadth then depth** so intent is clarified before anything is committed as a requirement. **You READ `materials/` and the docs; you WRITE only `docs/_global/grounding.md` (`## Feature scope`) and, in a deep-dive, that one feature's folder. You never mint REQ/BR/FLOW/SCR/AC ids (that is `/protoflow-spec`) and never touch `prototype/`.**

Each session is self-contained: all state lives in the docs, never in conversation memory. A deep-dive can run in its own session, in any order, and be resumed later — read the docs, work, write back.

## Read first

All `.claude/references/…` paths are relative to the **repo root**. Read `.claude/references/item-header.md` (the FACT…CONFLICT discipline), `.claude/references/ids.md` (incl. "Id-less items"), `.claude/references/grouping.md` (what a feature is), and `.claude/references/templates/feature/*` (the folder a deep-dive creates).

## Input

`<project-id> [feature]` from the command argument. **No feature → scope pass. A feature id → deep-dive that feature.**

- No project id → ask the BA for one.
- `protoflow/<project>/` missing → STOP: "No engagement `<project>`. Run `/protoflow-new <project>` first."
- `grounding.md` still holds only template placeholders (`<prose overview…>`, `<label>`) and no real facts → STOP: "Nothing grounded yet. Run `/protoflow-ground <project>` first." (Thin grounding is fine — research then carries more weight — but empty grounding means there is no domain to research.)

## Scope pass (no feature argument)

1. **Read** `grounding.md` (Business context, facts, assumptions, open questions, existing `## Feature scope` items), `glossary.md`, `entities.md`, and `interview.md` if it has real items (goals, pain points, scope boundaries).
2. **Candidates from the materials.** Group the facts into customer-recognizable capabilities (a verb the customer would say: "request a booking", "approve a booking"). Each candidate cites the facts it came from (`customer-process.pdf p.4`). Interview goals and pain points may suggest candidates too (provenance `interview: <label>`); anything the interview lists as **out of scope** is not proposed — mention it in the report instead. Give each a kebab-case feature id (`booking-request`) — this id becomes the feature folder name and the DevSpec change id, so keep it short and stable.
3. **Real-world research.** Load `WebSearch` / `WebFetch` (via ToolSearch if deferred). From the Business context, name the domain and search for 2–4 established systems in it (e.g. for a booking product: OpenTable, Calendly, Booking.com extranet). Read their product/feature pages; extract the capabilities they have in common — the baseline the customer may not have written down but will expect. Keep the URL for each.
   - If research yields nothing solid, say so and continue from the materials only. **Never invent a comparable system or a feature it "probably" has.**
   - If web tools are unavailable, say so and continue from the materials only.
4. **Merge** into one table for the BA, one row per candidate: feature id · one-line description in customer terms · provenance (`material: <file loc>` / `interview: <label>` / `comparable: <system> (<url>)` / `both`). Drop near-duplicates; existing `## Feature scope` items are shown with their current status and are not re-proposed.
5. **Confirm with the BA/customer.** Use `AskUserQuestion` (multiSelect, ≤4 options per question, as many questions as needed) to mark each new candidate *confirm* / *defer* / *reject*. Do not decide for them.
6. **Write** each candidate under `## Feature scope` in `grounding.md` as:

   ```
   ### <feature-id>
   - **Status:** confirmed | proposed | rejected
   - **Type:** DECISION
   - **Source:** material: customer-process.pdf p.4 | comparable: OpenTable (https://…) | both: …
   - **Confirmed:** <today> by <BA name>      (only when confirmed)

   <one line in the customer's terms; for a comparable-only feature add: "Industry baseline — not in the customer's materials.">
   ```

   Confirmed → `Status: confirmed` + `Confirmed:` filled. Deferred → `proposed`. Rejected → `rejected` (kept so it is not proposed again). On first run, replace the template's `### <feature-id — …>` placeholder block; keep the heading and italic intro.
7. **Merge, never clobber** (same rules as `/protoflow-ground` Step 4): never edit an item whose `Status:` is `confirmed` or whose `Confirmed:` is filled; a duplicate id is skipped; write with targeted Edits.
8. **Report:** features confirmed / deferred / rejected, which came only from research, and the next step: `/protoflow-explore <project> <feature>` for each confirmed feature.

**Research is a candidate, not a fact.** A comparable-only feature is never presented as something the customer asked for; it becomes part of scope only through the customer's confirmation.

## Deep-dive (feature argument)

1. **Scope gate.** The feature must be a `### <feature>` item under `## Feature scope` with `Status: confirmed`. Not found → STOP and list the confirmed ids. Found but `proposed` → STOP: "`<feature>` is not confirmed yet — confirm it in the scope pass first."
2. **Resume or create.** If `docs/features/<feature>/` exists, read all five docs — this session adds to them and does not repeat questions already there (answered or not). Otherwise create the folder with the five docs from `.claude/references/templates/feature/*`, keeping only the `# <Doc> — <feature>` title (placeholder replaced) and the italic intro line — **no example items**. (Creating the folder is what moves the feature to `explored` on `/protoflow-status`.)
3. **Gather what is known** about the feature: grounding facts/assumptions/unknowns/conflicts that concern it, the entities it touches, its glossary terms, and the Feature-scope provenance (for a comparable-only feature, what the reference systems do).
4. **Walk the feature systematically**, one lens at a time:
   - actors and their permissions;
   - the main scenario, end to end;
   - alternate and error paths (invalid input, rejection, cancel, retry, timeout);
   - states and transitions of the main entity;
   - data: which `ENT-` entities and fields, what is required, what is unique;
   - business rules and limits (thresholds, deadlines, quotas, who may override);
   - notifications and who receives them;
   - edge cases: concurrency (two users at once), partial completion, history/audit, deletion;
   - non-functional notes the customer raised (volume, response time, language, devices).

   For every gap write one typed id-less item (`### <short label>`, four-line header, `Status: proposed`):
   - `UNKNOWN` — body is the question to put to the customer;
   - `ASSUMPTION` — what you had to assume to keep going, `Source: AI-inferred (from <loc>)`;
   - `CONFLICT` — "Document A says X; document B says Y." Never pick a side;
   - `FACT` — only when re-stating a grounding fact this feature depends on, with the original `Source:`.

   Place each in the doc it will later inform: rule/limit questions → `rules.md`; screen/field/UX questions → `screens.md`; workflow-order questions → `flows.md`; test-condition questions → `acceptance.md`; everything else → `requirements.md`.
5. **Discuss live.** Put the most important questions to the BA with `AskUserQuestion` (≤4 per call; offer realistic options from the materials/research; the BA can always answer "Other" or "don't know yet"). Each answered question: set the item's `Type: DECISION`, `Source: meeting <today>`, `Status: confirmed`, `Confirmed: <today> by <BA name>`, and rewrite the body as the answer (keep the original question as a first line `Q: …`). "Don't know yet" stays `UNKNOWN`.
6. **No silent scope creep.** A new capability that surfaces (e.g. "they also want a waiting list") is appended to `## Feature scope` in `grounding.md` as a `proposed` DECISION with `Source: meeting <today>` — never explored in this session.
7. **Report:** questions raised, answered, still open; assumptions made; any new scope proposed; next step `/protoflow-spec <project> <feature>` (or `/protoflow-explore <project> <other-feature>`). Suggest `/protoflow-status <project>` to refresh the board.

## Guardrails

- Distinguish epistemic types explicitly; never silently turn an assumption into a requirement.
- Cite real references, don't invent them. If research yields nothing solid, fall back to the materials.
- Scope first, sign-off, then loop: never deep-dive a feature that isn't `confirmed`.
- Never mint REQ/BR/FLOW/SCR/AC/UC ids — id-less `### <label>` items only; `/protoflow-spec` mints ids.
- Read-only on `materials/`; discussion only — never scaffold or change `prototype/`.
