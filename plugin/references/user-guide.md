# ProtoFlow — the flow library (`guides/`)

`/protoflow-guide` is the final, project-wide stage. It turns the engagement into one **flow library**: a browsable site of every feature's process flows. Each flow page shows:

- **Steps** (default): the flow as numbered plain-language steps, each tagged with who acts (a person lane or the System), its screen and platform. A run of questions the same lane asks in a row reads as one "Checks" step; each branch that leaves the main path is spelled out ("no → … The flow ends here", "Go to step 8", "Back to step 2"), with error branches highlighted;
- **Diagram** (a toggle beside Steps, remembered per browser): the swimlane with zoom;
- short cards: what it uses (inputs), what it produces (outputs), states (the lifecycle) and the words used (terms);
- the feature's open questions folded at the bottom, and links to the previous / next flow of the feature.

The same file serves two readers:

| View | Reader | Shows |
|------|--------|-------|
| **Reader view** (default) | the customer, end users, anyone new | the flows in the customer's words: no ProtoFlow ids, item types, sources or statuses inside the diagrams and tables |
| **Team view** (toggle in the header, remembered per browser) | developers, testers, BAs | the same pages plus flow and node ids, the blockers of a blocked feature, and each flow's REQ / BR / AC copied verbatim with ids and draft chips |

Everything in `guides/` is **derived** (see [truth-vs-derived.md](truth-vs-derived.md)). To change the library, edit the docs and re-run `/protoflow-guide`. The one exception is `guides/library.json`, which is the refined working copy the skill keeps between runs; it is still never hand-edited by the BA.

| File | Written by | What |
|------|-----------|------|
| `guides/library.json` | `--library-draft` (first run) then the skill's refinement step | the `LIBRARY` object below |
| `guides/.library.draft.json` | `--library-draft` when `library.json` exists | the fresh deterministic draft to merge from |
| `guides/.library.prev.json` | the script | the draft the current `library.json` was refined from (the diff baseline) |
| `guides/library.html` | `--library` | the template with `LIBRARY` embedded. One self-contained file with hash routing; it opens from disk, deep-links and prints |
| `guides/library.md` | `--library` | the same content as Markdown, with mermaid diagrams |

## Which features are listed

Every feature that has a `docs/features/<f>/` folder or is a `confirmed` Feature-scope item, in Feature-scope order, each with a status:

| Status | Rule (from the `/protoflow-status` scan) |
|--------|-------------------------------------------|
| `final` | `confirmed` or `handed-off`, handoff not `blocked` |
| `blocked` | handoff `blocked`: an unresolved CONFLICT, or an UNKNOWN attached to a confirmed REQ. `blockers` names each one |
| `in-review` | `specced` or `prototyped`: flows exist but are not signed off |
| `no-flow` | `grounded` / `explored`, or a confirmed scope item with no folder yet: listed, with no flow pages |

Inside a feature, `Status: rejected` FLOWs are skipped. A `proposed` FLOW is still drawn; Team view marks it draft.

## `LIBRARY` shape

```
{ project, product, generated, language: "en" | "vi",
  modules:    [{ id, name, features: [featureId] }],
  features:   [{ id, title, module, status, summary, blockers: [text], flows: [FLOW] }],
  glossary:   [{ term, def }],
  lifecycles: [{ id: "<table>.<column>", entity, states: [code], transitions: [{ from, to, label }], flows?: [FLOW-id] }] }

FLOW = { id, title, summary, draft, view?: "lifecycle",
  lanes:   [{ id, name, kind: "input" | "actor" | "system" | "output" }],
  nodes:   [{ id, label, kind: "start" | "end" | "step" | "decision" | "state", lane, platform, screen, ref, phase?: "exception" }],
  edges:   [{ from, to, label }],
  inputs:  [{ no, input, type, goesTo, node }],          // type: "Master data" | "Record" | "Document" | …
  steps:   [{ step, role, screen }],
  outputs: [{ no, output, when, node }],
  terms:   [glossary term], lifecycle: lifecycle id | null,
  team:    { reqs: [{ id, title, text, draft }], rules: [...], acceptance: [...] } }
```

- **Lanes:** one `input` lane, one `actor` lane per role that acts in the flow (name it the way the customer names the role, e.g. "Mod / Admin"), one `system` lane, one `output` lane. Inputs and outputs are drawn as data shapes in their lanes, beside the node they feed (`inputs[].node`) or come from (`outputs[].node`).
- **Nodes:**
  - A `step` has a `platform` tag ("Web", "Mobile", "System (auto)", "Master data", "Email", …). An actor step also has the `screen` it happens on, using the screen's title.
  - A `decision` is a question; every outgoing edge is labelled with its answer.
  - `phase: "exception"` marks nodes reached only through an error / rejection branch. They are drawn dashed red.
- **`view: "lifecycle"`** — a FLOW that is a state machine (lifecycle-titled, no decisions) is drawn as a state diagram. Its nodes are `state`s and it has no start/end.
- `ref` and `id` fields may hold spec ids. Every other string is **reader text**.

## How the draft is built (`--library-draft`, deterministic)

- **Nodes and edges** come from each FLOW's ```` ```mermaid flowchart ```` (`flow.graph` in the model). A FLOW without one becomes a straight chain of its Steps.
- **Labels** that cite another item ("Post – FLOW-001") read as that item's title; `(BR-…)` references are dropped.
- **Lanes:**
  - The actor is the best-matching use case's actor.
  - The first node is the actor's trigger.
  - A step whose label starts with a system verb goes to System.
  - A decision goes to System unless it reads as the actor's choice ("which…?", "confirm?").
- **Exception phase:** nodes reachable from Start only through a `no` / `invalid` / `cancel` / … edge.
- **Inputs:** entities the flow's screens bind to, those the flow names first, at most three. **Outputs:** the flow's end points with the label of the branch that reaches them.
- **Lifecycles:**
  - States come from `db-design.md` `status` / `state` columns with `check in (…)`.
  - Transitions come from lifecycle-titled FLOW graphs.
  - A flow links to a lifecycle when it drew it or names its entity.
- **Team detail:** the rules the FLOW cites, the REQs governed by them, and the ACs verifying those REQs.

The draft is a starting point. The refinement step fixes what a heuristic can't know:
- which role does each step;
- system vs. actor;
- platforms;
- input types (master data vs. records);
- titles and one-sentence summaries.

It never invents steps, branches or messages the docs don't have.

## Validation (`--library`)

The render refuses (exit 1, JSON list of errors) when:

- a node's lane doesn't exist or its kind is unknown; an edge, input or output points at a missing node; a flow links to an unknown lifecycle;
- a decision has fewer than two outgoing branches, or an unlabelled one;
- a swimlane flow has no start or no end, or a start never reaches an end (state diagrams are exempt);
- **reader text contains a spec id** (`REQ-`, `BR-`, `UC-`, `FLOW-`, `SCR-`, `AC-`, `ENT-`): titles, summaries, node labels / screens / platforms, edge labels, inputs, outputs, steps, glossary;
- `language` is not `en` / `vi`, or a module lists an unknown feature.

## Rendering

- **HTML:**
  - The script copies `<pack>/references/templates/library.html` and replaces only the `LIBRARY` data block (`</script` escaped). It also sets `<title>`.
  - Fix view bugs in the template, never in the copy.
  - Routes: `#/` (index: "N of M features ready" bar, search, status filter, module filter when there is more than one module, one card per feature with its flows), `#/f/<feature>` (a feature with several flows), `#/f/<feature>/<FLOW-id>` (a flow page: Steps / Diagram).
  - Reader labels: `final` shows as "Ready", `blocked` as "Waiting on answers" (with "N open questions before this is final"), `in-review` "In review", `no-flow` "No flow yet". Blockers show to readers without their doc name and bookkeeping notes; Team view shows them verbatim.
  - The Steps view is built in the page from `nodes` / `edges` / `phase`. It needs no extra `LIBRARY` field, so a decision's edge labels and node labels are what the reader reads: keep them plain (Step 4).
  - Chrome: Diagram zoom (− / + / Fit width / Fit view / Full screen, Ctrl+wheel, drag to pan), Copy for AI (the flow as Markdown), theme (auto / dark / light), Print (prints the current view).
  - Interface strings come from built-in English and Vietnamese tables, picked by `language`. That is the docs' language, detected from grounding.
- **Markdown:** the index, then per flow a `flowchart TD` with one subgraph per lane (a `stateDiagram-v2` for state flows), the tables, the lifecycle, and the team detail in a `<details>` block.
