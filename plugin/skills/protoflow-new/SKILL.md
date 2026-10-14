---
name: protoflow-new
description: Scaffold a new ProtoFlow engagement folder from the shared templates. Use when a BA starts a customer discovery engagement — creates protoflow/<project>/ (materials, docs, reserved model/prototype/handoff slots) seeded from ${CLAUDE_PLUGIN_ROOT}/references/templates/.
---

> **Pack root:** `${CLAUDE_PLUGIN_ROOT}`. In this pack's reference files, a path written as `<pack>/…` is under that root; project files (`devspec/`, `protoflow/`, `tests/`) stay relative to the working repo.

# protoflow-new

Scaffold one customer engagement. **You create the folder skeleton and seed the global docs — you do NOT ground, spec, or prototype anything.** The BA fills materials and runs the lifecycle commands after.

## Read first

All `${CLAUDE_PLUGIN_ROOT}/references/…` paths are relative to the **repo root** (the command's working directory), not to this skill folder. Read `${CLAUDE_PLUGIN_ROOT}/references/layout.md` (the folder layout), `${CLAUDE_PLUGIN_ROOT}/references/truth-vs-derived.md`, and `${CLAUDE_PLUGIN_ROOT}/references/registry.md` (the registry format). This skill implements the layout `layout.md` defines.

## Input

The engagement id from the command argument: a kebab-case project name (e.g. `acme-booking`). If none was given, ask the BA for one.

## Guardrails (check before writing anything)

1. **Templates must exist.** If `${CLAUDE_PLUGIN_ROOT}/references/templates/` is missing, STOP immediately with:
   > ProtoFlow templates not found at `${CLAUDE_PLUGIN_ROOT}/references/templates/`. The ProtoFlow foundation is not installed correctly — reinstall it before creating an engagement.
   Create **no** folder — do not leave a partial tree.

2. **Never overwrite an existing engagement.** If `protoflow/<project>/` already exists, STOP with:
   > `protoflow/<project>/` already exists. Pick a new id, or run `/protoflow-status <project>` to work with the existing one.
   Do not touch the existing folder.

## What to create

Under `protoflow/<project>/`, build the layout from `${CLAUDE_PLUGIN_ROOT}/references/layout.md`:

```
protoflow/<project>/
├── materials/            (empty — BA drops raw uploads here)
├── docs/
│   ├── _global/          seeded from ${CLAUDE_PLUGIN_ROOT}/references/templates/_global/
│   │   ├── interview.md
│   │   ├── grounding.md
│   │   ├── glossary.md
│   │   ├── entities.md
│   │   ├── architecture.md
│   │   ├── db-design.md
│   │   └── rules.md
│   ├── features/         (empty — one folder per feature, created by the /protoflow-explore deep-dive)
│   ├── INDEX.md          seeded from ${CLAUDE_PLUGIN_ROOT}/references/templates/INDEX.md (empty-project state)
│   └── board.yml         seeded from ${CLAUDE_PLUGIN_ROOT}/references/templates/board.yml (empty-project state)
├── product-model.json    reserved slot — write `{}` (`/protoflow-prototype` compiles it later)
├── prototype/            reserved slot — empty (`/protoflow-prototype` fills it)
├── handoff/              reserved slot — empty (`/protoflow-handoff` fills it)
└── guides/               reserved slot — empty (`/protoflow-guide` fills it)
```

Copy each `${CLAUDE_PLUGIN_ROOT}/references/templates/_global/*.md` into `docs/_global/`, replacing the `<project>` placeholder wherever it appears with the real id. Seed `docs/INDEX.md` and `docs/board.yml` from `${CLAUDE_PLUGIN_ROOT}/references/templates/INDEX.md` / `${CLAUDE_PLUGIN_ROOT}/references/templates/board.yml` (the empty-project forms). Create the empty directories (`materials/`, `docs/features/`, `prototype/`, `handoff/`, `guides/`) and add a `.gitkeep` to each so it persists in git. Write `product-model.json` as `{}`.

## After scaffolding

Tell the BA what was created and the next step:

> Created `protoflow/<project>/`. Start with `/protoflow-interview <project>` to capture what you already know about the domain, then drop customer materials into `protoflow/<project>/materials/` and run `/protoflow-ground <project>` to build the grounding.
