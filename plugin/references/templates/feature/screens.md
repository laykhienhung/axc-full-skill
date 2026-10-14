# Screens — <feature>

_What the prototype renders for this feature. Each `SCR-` binds to entities and flows, and lists its states so the scaffolder and DevSpec `ui.md` know the shape. Source of truth._

### SCR-001 — <screen name>
- **Status:** proposed
- **Type:** INFERENCE | DECISION
- **Source:** screenshots/booking.png | AI-inferred
- **Confirmed:**

- **Purpose:** <what the user does here>
- **Fields:** <field> (bound to ENT-002.amount), <field> …
- **Actions:** <button/action> → FLOW-001
- **States:** empty | submitting | error | success
- **Flows:** FLOW-001
- **Entities:** ENT-002

```
┌─────────────────────┐
│ <screen sketch>     │
│ amount   [____]     │
│ [ Submit ]          │
└─────────────────────┘
```
