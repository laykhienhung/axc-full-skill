# ProtoFlow — engagement folder layout

One customer engagement = one folder under `protoflow/` at the repo root (sibling to `devspec/`). The id is kebab-case.

```
protoflow/<project>/
├── materials/            raw customer uploads (PDF, xlsx, screenshots, manuals) — READ-ONLY, never edited
├── docs/                 SOURCE OF TRUTH — hand-editable markdown
│   ├── _global/          project-wide substrate, shared across every feature
│   │   ├── interview.md      BA domain interview + materials basis (typed, conversation-sourced); grounds the project when there are no materials
│   │   ├── grounding.md      facts / assumptions / open questions / conflicts / materials index
│   │   ├── glossary.md       term → definition (+ source)
│   │   ├── entities.md       data model + mermaid ERD (ENT- ids)
│   │   ├── architecture.md   modules + system diagram (the dev view)
│   │   ├── db-design.md      tables / columns / indexes derived from entities
│   │   └── rules.md          CROSS-CUTTING business rules only (BR- ids spanning ≥2 features)
│   ├── features/         one folder per feature (the BA/customer spine)
│   │   └── <feature>/
│   │       ├── requirements.md   REQ- items, SHALL + WHEN/THEN scenarios
│   │       ├── rules.md          BR- items local to this feature
│   │       ├── flows.md          FLOW- items, workflow steps + diagram
│   │       ├── screens.md        SCR- items, what the prototype renders
│   │       └── acceptance.md     AC- items, Given/When/Then
│   ├── INDEX.md          DERIVED dashboard of all features + health
│   ├── interview.html    DERIVED project brief, tabs view (written by /protoflow-interview and /protoflow-ground; see interview-brief.md)
│   ├── interview-tree.html  DERIVED project brief, tree view (same data, same writers)
│   ├── spec.html         DERIVED interactive spec dashboard (written by /protoflow-prototype)
│   └── board.yml         DERIVED machine twin of INDEX.md
├── product-model.json    DERIVED compiled model (see product-model.md; written by /protoflow-prototype and /protoflow-handoff)
├── prototype/            throwaway HTML/CSS/JS + SQLite-WASM (written by /protoflow-prototype)
├── handoff/<feature>/    DevSpec-native change artifacts + TestForge cases (written by /protoflow-handoff)
└── guides/               flow library: library.html + library.md (+ library.json) (written by /protoflow-guide; see user-guide.md)
```

`materials/` is read-only ground truth from the customer. `docs/` is where the BA and AI work. The four reserved slots (`product-model.json`, `prototype/`, `handoff/`, `guides/`) are created empty by `/protoflow-new` so the later lifecycle skills have a stable place to write.
