---
description: Convert one sheet of a manual QA checklist workbook into the common TestCase template (.xlsx)
argument-hint: "<checklist.xlsx> [--sheet NAME] [--out path]"
---

Invoke the `testforge-convert` skill for: $ARGUMENTS

Follow the skill: pick one sheet, extract it with extract_manual.py, show the gate table
(groups / ABBR / prefix / repo path / output) and STOP for confirmation, rewrite each case per
references/conversion-rules.md (parallel chunk agents for > 40 cases), then write and validate
with write_template.py and report totals plus the Manual cases.
