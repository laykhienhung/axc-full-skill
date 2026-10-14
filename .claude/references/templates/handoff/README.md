# Handoff templates — DevSpec change shapes

Shapes `/protoflow-handoff` emits into `protoflow/<project>/handoff/<feature>/`, so the folder drops straight into `devspec/changes/<feature>/`. Copied from CLT-DevSpec, which defines them inside its skills (no template files there):

| File | DevSpec source of the shape |
|------|-----------------------------|
| `proposal.md`, `design.md`, `spec.md`, `tasks.md` | `clt-devspec/skills/devspec-capture/SKILL.md` |
| `design.md` → `## Impact Area` | `clt-devspec/references/impact-area.md` |
| `tasks.md` `[req-N]` coverage | `clt-devspec/references/req-coverage.md` |
| `db.md` | `clt-devspec/skills/devspec-db-design/SKILL.md` |
| `ui.md` + `mockups/<screen>.html` | `clt-devspec/skills/devspec-ui-mockup/SKILL.md` |
| `testforge/<feature>-cases.csv` | `clt-testforge/.claude/skills/testforge-gen/scripts/read_cases.py` (header aliases) |
| `TRACE.md` | ProtoFlow-only: ProtoFlow id → DevSpec / TestForge ref |

Worked example of a real change: `clt-testforge/devspec/archive/test-evidence-capture/`.

**Re-sync these when DevSpec or TestForge change their format.** No file carries YAML frontmatter. `<…>` marks a value to fill; `(REQ-005)`-style suffixes keep ProtoFlow ids visible across the boundary.
