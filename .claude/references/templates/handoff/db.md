# DB: <feature-id>

**Source**: file-derived (ProtoFlow `docs/_global/db-design.md`, discovery — not a live schema; check against the real database before migrating)
**Dialect**: <dialect from db-design.md / architecture.md, else "unspecified">

## Tables touched
### <table>  (new)
| col | type | null | default | note |
|-----|------|------|---------|------|
| id | uuid | no | — | PK |
| <col> | <type> | yes | — | **add** · FK → <table>.id · from ENT-001.<field> |

## Impact
- <which other features' entities/tables share this table (cross-cutting ENT-)>
- **Migration**: <additive only / note anything that alters existing data>

## Open questions
- <db-related UNKNOWN items still open, or "None.">
