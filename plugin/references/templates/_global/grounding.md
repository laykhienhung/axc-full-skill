# Grounding — <project>

_The first output of discovery. The map of what is known, assumed, unknown, and contradictory across all provided materials. Source of truth; hand-edited by BA + AI._

## Business context

<prose overview of the domain and the problem, cited to materials>

## Feature scope

_The feature spine — the customer-recognizable capabilities discovery will cover, written by `/protoflow-explore` (scope pass) and agreed with the customer before any deep-dive. Proposed from two sources: the materials, and web research on comparable real systems in the domain. Each stays `proposed` until the customer signs off, then `confirmed`. A confirmed feature is what a per-feature deep-dive and, later, one `docs/features/<feature>/` folder + one DevSpec change map to._

### <feature-id — e.g. booking-approval>
- **Status:** proposed
- **Type:** DECISION
- **Source:** <material: file p.N | comparable: name the reference system | both>
- **Confirmed:**

<one line: what this feature is, in the customer's terms; note if it's an industry-standard baseline the materials didn't mention>

## Known facts

### FACT-NOTE
_Facts are captured as typed items so they trace. Use the ENT-/BR- ids where an item is really an entity or rule; keep free-standing facts here._

### <FACT id or short label>
- **Status:** proposed
- **Type:** FACT
- **Source:** <file p.N | meeting date>
- **Confirmed:**

<the fact>

## Assumptions

### <label>
- **Status:** proposed
- **Type:** ASSUMPTION
- **Source:** AI-inferred
- **Confirmed:**

<assumption made to keep exploring — must be confirmed or dropped>

## Open questions

### <label>
- **Status:** proposed
- **Type:** UNKNOWN
- **Source:** <what raised it>
- **Confirmed:**

<the question to put to the BA/customer>

## Contradictions

### <label>
- **Status:** proposed
- **Type:** CONFLICT
- **Source:** <doc A p.N vs doc B p.M>
- **Confirmed:**

<"Document A says X; document B says Y." Blocks handoff until resolved.>

## Materials index

| File | What it is | Read | Notes |
|------|------------|------|-------|
| customer-process.pdf | process description | yes | |
| booking.xlsx | booking register | no | xlsx: no converter — CSV export requested |

_`Read` is `yes` / `partial` / `no`; Notes says why when it isn't `yes`. `/protoflow-ground` re-reads only files not yet `yes`._
