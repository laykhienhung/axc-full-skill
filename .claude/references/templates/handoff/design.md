# Design: <feature-id>

## Approach

<How the feature works end to end, from the use cases and flows. Name the module(s) from architecture.md. Note any existing-system constraints from architecture.md "Existing system notes".>

## Architecture

```
<actor> → <SCR-001 screen>
  → <service step from FLOW-001 step 1>
  → check <BR-002>
  → <persist to table>            (db.md)
  → <next screen / notification>
```

## Business rules

| Rule | Statement | Enforced at |
|------|-----------|-------------|
| BR-002 | <single testable statement> | <FLOW step / screen> |

## Impact Area

### Decision Defaults

| Gray area | Default decision | Fallback if default doesn't fit |
|-----------|------------------|---------------------------------|
| <from a DECISION or ASSUMPTION item> | <the decision / the assumption> | <what to do if it doesn't hold — "ask the BA" when none was discussed> |

### Blast Radius
- <module or area> (new/adjust) — safe/reversible   _(paths to confirm by dev — ProtoFlow does not read the codebase)_
- <table> (new) — safe/reversible (additive)

### Risk / reversibility
<Anything destructive or irreversible (data removal, security weakening) — or "None identified at discovery; additive only.">
