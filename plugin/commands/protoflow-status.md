---
description: Scan an engagement's feature docs and regenerate INDEX.md + board.yml
argument-hint: <project-id>
---

Invoke the `protoflow-status` skill. Input: `$ARGUMENTS` (the engagement id).

Scan `protoflow/<project>/docs/features/*`, recount items, derive each feature's status and health, and regenerate the derived `docs/INDEX.md` and `docs/board.yml`.
