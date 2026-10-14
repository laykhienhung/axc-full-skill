---
description: Batch-generate verified Playwright specs from a multi-screen Excel workbook with parallel per-screen agents
argument-hint: "<workbook.xlsx> [--concurrency N]"
---

Invoke the `testforge-batch` skill for: $ARGUMENTS

Follow the skill: read every sheet (one sheet = one screen), build the plan with plan_batch.py,
show the single plan table and STOP for confirmation, then run the testforge-batch Workflow
(one agent per screen, capped at --concurrency, default 5), merge fixtures, run the full
regression, and report per-screen / per-case status with deviations.
