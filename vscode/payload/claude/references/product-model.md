# ProtoFlow — `product-model.json` (compiled model)

`protoflow/<project>/product-model.json` is the docs compiled into one JSON object. It is **derived** (see [truth-vs-derived.md](truth-vs-derived.md)): regenerated in full from `docs/` by `/protoflow-prototype`, `/protoflow-handoff` and `/protoflow-guide` via `.claude/references/scripts/protoflow_compile.py`, never hand-edited. The same object is embedded in `docs/spec.html` as `const MODEL = …;`, so its shape is exactly what [templates/spec.html](templates/spec.html) reads — the demo `MODEL` in that file is a worked example.

## Shape

```jsonc
{
  "project":   "acme-booking",            // engagement id
  "generated": "2026-09-26",              // compile date
  "context":   "…",                       // grounding.md ## Business context, prose, citations stripped
  "modules": [                            // _global/architecture.md ## Modules
    { "name": "Booking", "description": "<Responsibility>", "dependsOn": ["<module>"] }
  ],
  "flowE2E": [                            // end-to-end journey across features, in order
    { "step": "Customer submits a booking", "module": "Booking", "feature": "booking-request" }
  ],
  "global": {
    "entities": [                         // _global/entities.md
      { "id": "ENT-001", "name": "Booking", "note": "<one line>",
        "fields":    [ { "name": "id", "type": "uuid", "key": "PK" } ],     // key: PK | FK | omitted
        "relations": [ { "to": "Resource", "card": "}o--||", "label": "for" } ] }  // card = mermaid erDiagram cardinality
    ],
    "dbDesign": [                         // _global/db-design.md ## Tables
      { "table": "bookings", "entity": "ENT-001",
        "columns": [ { "name": "id", "type": "uuid", "key": "PK", "note": "" } ],
        "indexes": [ "idx_bookings_status" ] }
    ],
    "glossary": [ { "term": "Hold", "def": "…", "source": "customer-process.pdf p.4" } ]
  },
  "features": [ /* one per docs/features/<feature>/, see below */ ]
}
```

### Feature

```jsonc
{
  "id": "booking-request",                // folder name = Feature-scope id
  "title": "Booking request",             // humanized id, or the first line of the Feature-scope item
  "module": "Booking",                    // the architecture module whose "Features it serves" lists it; else "Ungrouped"
  "status": "specced",                    // derived exactly as /protoflow-status does (registry.md ladder)
  "provenance": "material: customer-process.pdf p.4",   // the Feature-scope item's Source:
  "entities": ["ENT-001"],                // union of Entities: across its REQ and SCR items
  "useCases":     [ { "id": "UC-001", "title": "…", "actor": "…", "goal": "…",
                      "pre": ["…"], "main": ["…"], "reqs": ["REQ-001"] } ],
  "requirements": [ /* item + "rules": ["BR-001"], "entities": ["ENT-001"] */ ],
  "rules":        [ /* item + "scope": "local" | "global", "appliesTo": ["REQ-001"], "spans": ["<feature>"] */ ],
  "flows":        [ /* item + "trigger": "…", "steps": ["…"], "rules": [], "screens": [],
                       "graph": { "nodes": [ { "id": "A", "label": "…", "kind": "step" | "decision" | "terminal" } ],
                                  "edges": [ { "from": "A", "to": "B", "label": "yes" } ] } | null */ ],
  "screens":      [ /* item + "purpose": "…", "statesDetail": [...], "elements": ["<field or action>"], "fields": [...], "actions": [...], "states": [...], "flows": [], "entities": [], "sketch": "<ascii>" */ ],
  "acceptance":   [ /* item + "verifies": "REQ-001", "verifiesAll": ["REQ-001", "BR-002"], "gherkin": "Given …\nWhen …\nThen …" */ ]
}
```

### Item (common fields)

Every item block in a doc compiles to:

```jsonc
{ "id": "REQ-001",            // "" for an id-less ### <label> item (grounding-style questions/assumptions)
  "title": "Submit a booking",
  "status": "proposed",       // proposed | confirmed | rejected
  "type": "FACT",             // FACT | INFERENCE | ASSUMPTION | UNKNOWN | DECISION | CONFLICT
  "source": "customer-process.pdf p.6",
  "confirmed": "",            // the Confirmed: line, "" when blank
  "text": "…" }               // REQ: "SHALL …\nWHEN … THEN …" lines; BR: the Rule:; UNKNOWN/CONFLICT/other: the body
```

## Compile rules

- **Full regeneration**, never a patch: read every doc, write the whole file.
- Id-less items (open questions, assumptions, conflicts left by a deep-dive) are compiled into the array of the doc they sit in, with `"id": ""`, so `spec.html` and the health counts see them.
- `Status: rejected` items are kept (the dashboard shows them struck through); consumers that emit downstream artifacts skip them.
- A cross-cutting rule (`_global/rules.md`) is compiled into **every** feature listed in its `Spans features:`, with `"scope": "global"`.
- `screens[].elements` = the SCR's `Fields:` names followed by its `Actions:` labels (what `spec.html` lists); the structured `fields`/`actions`/`states` are what the prototype scaffolder reads:
  - `fields`: `[ { "label": "Amount", "bind": "ENT-002.amount" } ]`
  - `actions`: `[ { "label": "Submit", "flow": "FLOW-001" } ]`
  - `states`: `["empty", "submitting", "error", "success"]`
- `flowE2E`: the confirmed features' main FLOW steps chained in Feature-scope order, each step tagged with its feature's module. Omit (empty array) when only one feature is specced.
- `acceptance[].verifies`: the first REQ id in `Verifies:` (the dashboard groups AC under it); keep the full list in `verifiesAll`.
- `useCases[].main`: one entry per step. A main path written inline ("1. Opens … 2. Chooses …") is split at the numbers.
- `flows[].graph`: the FLOW's first ```` ```mermaid flowchart ```` block parsed into nodes and edges (`A -->|label| B`, `A -- label --> B`, chains). `{…}` is a decision; `(…)`, `([…])` and `((…))` are terminals; anything else is a step. `null` when the FLOW has no mermaid block. The flow library (`/protoflow-guide`) draws its swimlanes from it.
- Strings are plain text: strip markdown emphasis, keep line breaks as `\n`.
