# ProtoFlow — ID scheme

Every important item carries a stable, typed id so it can be traced from a source document through to a downstream test.

| Prefix   | Item                | Lives in                         |
|----------|---------------------|----------------------------------|
| `REQ-`   | Requirement         | `features/<f>/requirements.md`   |
| `BR-`    | Business rule       | `features/<f>/rules.md` or `_global/rules.md` |
| `ENT-`   | Entity              | `_global/entities.md`            |
| `UC-`    | Use case            | `features/<f>/flows.md` (`## Use cases`) |
| `FLOW-`  | Workflow            | `features/<f>/flows.md`          |
| `SCR-`   | Screen              | `features/<f>/screens.md`        |
| `AC-`    | Acceptance criterion| `features/<f>/acceptance.md`     |

Rules:

- Ids are a **zero-padded, per-project sequence within a type**: `REQ-001`, `REQ-002`, …, `BR-001`, `ENT-001`. The sequence is global to the project, not restarted per feature — `REQ-014` is unique across the whole engagement.
- An id is **never renumbered or reused** once assigned. If an item is dropped, its id is retired (mark it `Status: rejected`), never handed to a different item. This keeps every downstream reference stable.
- Downstream artifacts reference ids, never titles: a requirement cites `Rules: BR-003`, an acceptance criterion cites `Verifies: REQ-005`.

## Allocating a new id (single authority)

There is **no central counter file** — the docs themselves are the ledger, so allocation can never drift from reality. Any skill that mints an id (`protoflow-ground`, `protoflow-spec`, and any other skill that adds items) allocates the same way:

1. Scan every doc in `protoflow/<project>/docs/` for existing ids of the target type (including `Status: rejected` retired ones — they still count).
2. The next id = **highest existing number of that type + 1**, zero-padded.
3. Assign, then write. When adding several at once, reserve the block up front so two new items never collide.

This rule is authoritative for all skills; none keeps its own private counter.

## Id-less items

Items written before `/protoflow-spec` runs — grounding items, and the questions/assumptions a `/protoflow-explore` deep-dive drops into a feature folder — use a short `### <label>` heading with no id. `/protoflow-spec` mints ids when it turns them into REQ/BR/FLOW/SCR/AC items. Never invent other prefixes.
