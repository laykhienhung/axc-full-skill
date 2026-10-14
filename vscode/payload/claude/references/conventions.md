# ProtoFlow — shared conventions

ProtoFlow is a BA-led product-discovery and rapid-prototyping system run inside Claude Code. The AI is the runtime — there is no application code, no server, no build step. Everything is markdown the BA and customer can read.

The contract is split into focused reference files in this `.claude/references/` folder (at the repo root). A command loads **only** the sections it needs, not this whole file:

| Reference | Covers |
|-----------|--------|
| [layout.md](layout.md) | §1 engagement folder layout |
| [ids.md](ids.md) | §2 ID scheme + traceability |
| [item-header.md](item-header.md) | §3 universal item header (Status/Type/Source/Confirmed, the FACT…CONFLICT discipline) |
| [truth-vs-derived.md](truth-vs-derived.md) | §4 truth vs derived, data-flow direction |
| [grouping.md](grouping.md) | §5 feature-first grouping + cross-feature rule scope (a) |
| [interview-brief.md](interview-brief.md) | the project brief `docs/interview.html` + `docs/interview-tree.html`: `BRIEF` shape, materials basis, matched/contradicted checks |
| [registry.md](registry.md) | §6 `INDEX.md` / `board.yml` format, status ladder, health gate |
| [user-guide.md](user-guide.md) | the flow library `guides/`: feature statuses, `LIBRARY` shape, draft heuristics, validation, rendering |

Scaffold shapes the skills seed engagements from live in [templates/](templates/).

Each skill's "Read first" line points at the specific reference(s) above. Read this index only when you need the whole contract.
