---
name: protoflow-status
description: Scan a ProtoFlow engagement's feature docs and regenerate the derived docs/INDEX.md dashboard and docs/board.yml machine twin. Use to refresh the feature registry after editing discovery docs, to see project health, and to check handoff readiness. Read-only on docs/ (truth); writes only the two derived files.
---

# protoflow-status

Regenerate the feature registry from the docs. **The docs are the source of truth — you only READ them and only WRITE the two derived files (`docs/INDEX.md`, `docs/board.yml`). Never edit a feature doc to make a number come out; fix the doc, then re-run.**

## Read first

`.claude/references/registry.md` (registry format, status ladder, health gate) and `.claude/references/item-header.md` (how to read Status/Type). This skill implements the derivation `registry.md` defines.

## Input

The engagement id. Operate on `protoflow/<project>/`. If it doesn't exist, tell the BA to run `/protoflow-new <project>` first.

## Scan

For each feature folder under `protoflow/<project>/docs/features/*`, read `requirements.md`, `rules.md`, `flows.md`, `screens.md`, `acceptance.md` and count:

- **REQ** — number of `REQ-` items.
- **BR** — number of `BR-` items **defined** in this feature's `rules.md`. Defined = a `BR-` with a full item-header block (`Status:`/`Type:`/`Source:`). A bare `BR-nnn` mention pointing at `_global/rules.md` is a *reference*, not a definition — do not count it.
- **Open-Q** — number of items whose `Type:` is `UNKNOWN`.
- **Conflict** — number of items whose `Type:` is `CONFLICT`.
- **Confirmed reqs** — `REQ-` items whose `Status:` is `confirmed`.

Derive each feature's **status** on the fixed ladder (`grounded → explored → specced → prototyped → confirmed → handed-off`). Check the rules **in ladder order and take the highest stage whose condition holds** — a confirmed, prototyped feature is `confirmed`, not `specced`, even though the `specced` condition is also true:

- feature folder exists but `requirements.md` has no `REQ-` yet → `grounded`
- open questions raised (`UNKNOWN` items) but not yet a full req set → `explored`
- has requirements + rules + flows + screens → `specced`
- a prototype slice exists (`protoflow/<project>/prototype/<feature>` present) → `prototyped`
- every `REQ-` item is `Status: confirmed` → `confirmed`
- emitted to `handoff/<feature>/` → `handed-off`

## Health gate

A feature's **Handoff** is `blocked` when it has **any unresolved `CONFLICT` item**, or an **open question (`UNKNOWN`) attached to a `confirmed` requirement**. Attached = the `UNKNOWN` item cites that requirement's `REQ-` id in its body (the id-reference convention in `.claude/references/ids.md`). Otherwise `ready` once `specced`+, else `—`. Reflect the same verdict in both outputs — they are generated from this one scan so they never disagree.

## Write

Regenerate both derived files (overwrite; they are not hand-edited):

- **`docs/INDEX.md`** — from the `.claude/references/templates/INDEX.md` shape: the feature table (Feature, Status, REQ, BR, Open-Q, Conflict, Proto, Handoff), the health block (conflict total, open-question total, confirmed/total reqs), the global line (grounding present, glossary term count, entity count, ERD present), and the legend.
- **`docs/board.yml`** — from the `.claude/references/templates/board.yml` shape: one entry per feature under `features:` with `status`, `req`, `br`, `open_q`, `conflict`, `prototype`, `handoff`, plus the `health:` block.

**Assemble both by string composition in this prompt — no template engine, no code dependency.** Build the markdown table row by row and the YAML key by key.

## After

Print a one-line summary: features scanned, any `blocked` handoffs, total open questions — so the BA sees health at a glance during the meeting.

Then print **Next steps** — one line per feature, from its status and health (first matching rule wins), plus the project-level line when it applies:

| Situation | Suggest |
|-----------|---------|
| `interview.md` holds only template placeholders and `grounding.md` has no real facts | `/protoflow-interview <project>` (recommended first; with no customer materials it grounds the project) |
| `grounding.md` has no real facts yet and `materials/` is empty | drop the customer's files into `materials/` and run `/protoflow-ground <project>` — or, if there are none, `/protoflow-interview <project>` and answer *No materials* |
| `grounding.md` has no real facts yet | `/protoflow-ground <project>` |
| no `confirmed` item under `## Feature scope` | `/protoflow-explore <project>` (scope pass) |
| a confirmed Feature-scope item with no `docs/features/<f>/` folder | `/protoflow-explore <project> <f>` (deep-dive) |
| handoff `blocked` | resolve the blockers first — name each CONFLICT / attached UNKNOWN with its doc |
| `grounded` / `explored` | `/protoflow-spec <project> <f>` (if UNKNOWNs remain, say they'll carry into the spec) |
| `specced` | `/protoflow-prototype <project>` |
| `prototyped`, not every REQ confirmed | review with the customer, then mark the agreed REQs `confirmed` |
| `confirmed`, handoff `ready` | `/protoflow-handoff <project> <f>` |
| `handed-off` | none — copy `handoff/<f>/` into `devspec/changes/<f>/` if not done yet |

Project-level line, after the feature lines: when at least one feature is `specced` or beyond and `guides/` has no `library.html` or it is older than the newest file under `docs/`, suggest `/protoflow-guide <project>` (the flow library).

These are suggestions in the report only; nothing is written to `INDEX.md`/`board.yml` beyond the registry.
