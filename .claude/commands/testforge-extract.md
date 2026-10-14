---
description: Find repeated page actions across Page Objects and hoist them into a shared helper
argument-hint: "[pages_dir] (default: tests/pages)"
---

Run Step 7 (Evolve) of the `testforge-gen` skill against: ${ARGUMENTS:-tests/pages}

Run scripts/extract_common_actions.py to report repeated action sequences, present the
candidates, and — only for candidates the user picks — hoist them into a shared actions helper
and re-run affected specs to confirm they stay green. Do not refactor without confirmation.
