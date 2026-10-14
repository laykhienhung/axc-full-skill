---
description: Generate a verified Playwright E2E test (POM + fixture + spec) from a test case
argument-hint: <path/to/cases.csv|.xlsx (multi-sheet → looped) | pasted steps>
---

Invoke the `testforge-gen` skill to generate a verified Playwright test for: $ARGUMENTS

Follow the skill workflow: load the case, read repo basecode, confirm the plan, capture real
selectors from the live app, generate Page Object + fixture + spec, and run the spec until it
passes. Report files created, the pass/fail result, and any deviations from the written case.

A multi-sheet `.xlsx` (one sheet per screen) runs in workbook loop mode: one plan table and a
single confirmation for the whole workbook, then every screen in turn in the visible browser
(at most 3 attempts per case), and a final full run with a per-case report.
