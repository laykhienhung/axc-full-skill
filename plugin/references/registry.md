# ProtoFlow — feature registry: `docs/INDEX.md` and `docs/board.yml`

Both are derived (see [truth-vs-derived.md](truth-vs-derived.md)), regenerated together by `/protoflow-status` from a single scan of `docs/features/*` so they never disagree.

## `INDEX.md` — the human dashboard

Shape:

- A title + phase line marked "derived, do not hand-edit".
- A **feature table** with one row per feature and these columns:
  `Feature | Status | REQ | BR | Open-Q | Conflict | Proto | Handoff`
  (REQ/BR = counts; Open-Q = count of `UNKNOWN` items; Conflict = count of `CONFLICT` items; Proto = whether a prototype slice exists; Handoff = `ready` / `blocked` / `—`.)
- A **health block** listing handoff blockers: unresolved conflicts, open-question totals, confirmed-vs-total requirement counts.
- A **global line**: grounding present, glossary term count, entity count, ERD present.
- A **status legend** (see below).

## `board.yml` — the machine twin

One entry per feature with its status and the same counts, marked derived / not hand-editable:

```yaml
# DERIVED by /protoflow-status — do not hand-edit
features:
  booking:
    status: specced
    req: 8
    br: 5
    open_q: 2
    conflict: 1
    prototype: false
    handoff: blocked
```

## Feature status ladder (fixed vocabulary)

```
grounded → explored → specced → prototyped → confirmed → handed-off
```

- `grounded` — entities/context extracted, no requirements yet.
- `explored` — deep-dived; the feature folder exists (created by `/protoflow-explore <project> <feature>`) and holds open questions, but not yet a full req set.
- `specced` — requirements / rules / flows / screens written.
- `prototyped` — a prototype slice exists and is viewable.
- `confirmed` — the customer has signed off.
- `handed-off` — emitted to DevSpec.

## Health gate

A feature's `Handoff` is **blocked** when it has any unresolved `CONFLICT` item, or an open question (`UNKNOWN`) attached to a `confirmed` requirement. `/protoflow-status` reflects this in both `INDEX.md` (health block) and `board.yml` (`handoff: blocked`).
