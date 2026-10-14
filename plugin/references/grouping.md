# ProtoFlow — grouping: feature-first with a global substrate

Discovery groups by **feature** — a capability the customer recognizes (e.g. `booking-approval`), because a feature maps 1:1 to a downstream DevSpec change and to a demo-able prototype slice.

- **Feature** is the folder and the spine. Requirements, local rules, flows, screens, and acceptance for one capability live in `features/<feature>/`.
- **A requirement is the atom of traceability**, not a folder — it lives as a `REQ-` item inside `requirements.md`.
- **A module is dev-side language** — it appears only in `_global/architecture.md`, never as a discovery folder.
- Truly shared concepts (entities/ERD, glossary, architecture, db-design) live in `_global/` so they are not duplicated across features.

## Cross-feature rule scope — rule (a)

- A rule scoped to **one** feature lives in that feature's `rules.md`.
- A rule spanning **two or more** features lives in `_global/rules.md`, and each feature that relies on it **references its `BR-` id** rather than restating it.

This keeps local rules local and shared rules single-sourced.
