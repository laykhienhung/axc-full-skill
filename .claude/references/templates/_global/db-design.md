# DB design — <project>

_Tables / columns / indexes derived from the entities (ENT-). Feeds the prototype's local DB and the DevSpec `db.md` at handoff. Source of truth for the data shape; keep aligned with entities.md._

## Tables

### <table_name>  (from ENT-001)
- **Status:** proposed
- **Type:** INFERENCE | DECISION
- **Source:** ENT-001 | booking.xlsx
- **Confirmed:**

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| code | text | PK, unique | |
| name | text | not null | |
| credit_limit | numeric | default 0 | |
| status | text | check in (ACTIVE,INACTIVE) | |

- **Indexes:** `idx_<table>_status` on (status)
- **Relationships:** FK to <table> (from ENT relationship)

## Notes

- Prototype DB is throwaway seed data only — never connected to a customer production database.
