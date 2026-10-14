# ProtoFlow — universal item header

Every item block — in every template, every doc — carries the same four-field header directly under its `### <ID> — <title>` heading:

```
### REQ-005 — Credit check on booking
- **Status:** proposed | confirmed | rejected
- **Type:** FACT | INFERENCE | ASSUMPTION | UNKNOWN | DECISION | CONFLICT
- **Source:** customer-process.pdf p.12   (or: meeting 2026-09-26, or: AI-inferred)
- **Confirmed:** 2026-09-26 by <name>     (blank until confirmed)
```

Field meanings:

- **Status** — lifecycle of the item. `proposed` (drafted, not yet agreed), `confirmed` (BA/customer signed off), `rejected` (dropped; id retired).
- **Type** — epistemic status, the core discipline of ProtoFlow. The AI must never silently promote an `ASSUMPTION` to a `FACT` or a requirement:
  - `FACT` — stated explicitly in provided materials.
  - `INFERENCE` — reasonably inferred, not explicitly documented.
  - `ASSUMPTION` — temporarily assumed to keep exploring; must be confirmed or dropped.
  - `UNKNOWN` — an open question needing clarification. Counts against handoff readiness.
  - `DECISION` — a choice confirmed by the BA or customer.
  - `CONFLICT` — two sources disagree. Blocks handoff until resolved.
- **Source** — where it came from: a document + location, a meeting date, or `AI-inferred`. Distinguishes document-derived / conversation-derived / AI-inferred / customer-confirmed.
- **Confirmed** — date + who, once a human signs off. Blank means not yet confirmed.
