---
name: protoflow-ground
description: Read an engagement's customer materials and build/merge docs/_global/grounding.md (business context, facts, assumptions, open questions, contradictions, materials index), every item cited; seeds glossary.md and entities.md, cross-checks the BA's domain interview (interview.md) against the materials, and refreshes the project brief (interview.html + interview-tree.html). Use after /protoflow-interview once materials are dropped in, and again whenever new materials arrive. Not needed when the customer has no materials — /protoflow-interview grounds the project then. Read-only on materials/.
---

> **Pack root:** `${CLAUDE_PLUGIN_ROOT}`. In this pack's reference files, a path written as `<pack>/…` is under that root; project files (`devspec/`, `protoflow/`, `tests/`) stay relative to the working repo.

# protoflow-ground

Ground the AI in the customer's materials before any discussion or prototyping. **You READ `materials/` (never edit it) and WRITE only `docs/_global/grounding.md`, `glossary.md`, `entities.md`, the derived brief pages `docs/interview.html` and `docs/interview-tree.html`, and the one `Materials:` line of `interview.md`'s `## Source basis`. Every item you write is typed and cited — if you cannot cite it, you do not write it.** The prototype is downstream of understanding, never upstream.

## Read first

All `${CLAUDE_PLUGIN_ROOT}/references/…` paths are relative to the **repo root**. Read `${CLAUDE_PLUGIN_ROOT}/references/item-header.md` (the four-field header and the FACT…CONFLICT discipline), `${CLAUDE_PLUGIN_ROOT}/references/ids.md` (id allocation), `${CLAUDE_PLUGIN_ROOT}/references/truth-vs-derived.md`, `${CLAUDE_PLUGIN_ROOT}/references/interview-brief.md` (the brief you refresh), and the shapes you fill: `${CLAUDE_PLUGIN_ROOT}/references/templates/_global/grounding.md`, `glossary.md`, `entities.md`.

If `docs/_global/interview.md` holds real items (written by `/protoflow-interview`), read it too — it is your **reading lens**: its actors, process steps, terms and key data tell you what to look for; its `## Materials to expect` says what each file should settle; its open questions and assumptions are what the materials should confirm or refute. It is read-only here. No interview (or placeholders only) → proceed from the materials alone and suggest `/protoflow-interview <project>` in the report.

## Input

`<project-id> [file…]` from the command argument.

- No project id → ask the BA for one.
- `protoflow/<project>/` missing → STOP: "No engagement `<project>`. Run `/protoflow-new <project>` first."
- `materials/` empty (nothing but `.gitkeep`) → STOP and write nothing:
  - `interview.md` says `Materials: none` and `grounding.md` already holds facts → "This project is grounded from the BA interview — there are no materials to read. Next: `/protoflow-explore <project>`. If materials arrive later, drop them into `materials/` and re-run."
  - otherwise → "`materials/` is empty. Drop the customer's files into `protoflow/<project>/materials/`, then re-run — or, if the customer has no materials, run `/protoflow-interview <project>` and answer *No materials*; it grounds the project from the interview."
- Optional `file…` names (paths relative to `materials/`) force those files to be (re-)read even if already grounded.

## Step 1 — Inventory

List `materials/` recursively (ignore `.gitkeep`). Parse the `## Materials index` table in `grounding.md`. The **work set** is:

- every file with no index row, or whose row's `Read` is not `yes`, **plus**
- any file the BA named in the argument.

If the work set is empty, say "Nothing new to ground — all materials are indexed as read." and suggest `/protoflow-explore <project>`. Write nothing.

## Step 2 — Read each file by format

Read every page/sheet — do not skim. Keep a precise location for everything you extract.

| Format | How | Cite as |
|--------|-----|---------|
| `.pdf` | Read tool with `pages` — at most 20 pages per call; chunk long files (`1-20`, `21-40`, …) | `file.pdf p.12` |
| images (`.png` `.jpg` `.gif` `.webp`) | Read tool natively | `file.png (screenshot: <region/label>)` |
| `.md` `.txt` `.csv` `.json` `.eml` `.yml` | Read tool natively | `file.txt L12–20` · `file.csv row 7 col Status` |
| `.xlsx` `.xlsm` | Excel converter below | `file.xlsx Sheet1!A1:E20` |
| `.docx` `.pptx` | Office converter below | `file.docx §<heading>` · `file.pptx slide 4` |
| anything else / illegible | don't guess — record it | — |

**Converters write to a scratch folder, never inside `materials/`.** Use the session scratchpad directory if one exists, else `$TMP/protoflow-ground/<project>/`.

**Excel.** First check `python -c "import openpyxl"`. If it succeeds, dump every sheet with cell coordinates, then Read the dump:

```bash
python - "<materials/file.xlsx>" "<scratch>/file.xlsx.txt" <<'PY'
import sys, openpyxl
wb = openpyxl.load_workbook(sys.argv[1], data_only=True, read_only=True)
with open(sys.argv[2], "w", encoding="utf-8") as out:
    for ws in wb.worksheets:
        out.write(f"=== Sheet: {ws.title}\n")
        for row in ws.iter_rows():
            cells = [f"{c.coordinate}={c.value}" for c in row if c.value is not None]
            if cells:
                out.write(" | ".join(cells) + "\n")
PY
```

If the import fails: index the file `Read: no`, note `xlsx: no converter — CSV export requested`, and add an `UNKNOWN` under Open questions asking the BA to export each sheet as CSV into `materials/`.

**Word / PowerPoint.** Try `python-docx` / `python-pptx` (extract paragraphs with their headings, or text per slide). If those aren't importable, the files are zip archives: extract the text of `word/document.xml` or `ppt/slides/slide*.xml` with python's `zipfile` and strip the tags. If both fail, treat as unreadable (below) and ask for a PDF export.

**Unreadable or partly illegible** (scanned pages you can't make out, password-protected files, unknown formats): index `Read: partial` or `no` with a note saying which part and why. Never infer what the unreadable content "probably" says.

## Step 3 — Extract typed items

Every item is a `### <short label>` block with the four-line header from `item-header.md`, `Status: proposed`, `Confirmed:` blank. Labels are short and descriptive (`### Approval threshold`) — **do not invent id prefixes**; `ids.md` defines none for grounding items.

- **Business context** — 1–3 paragraphs of prose: the domain, the problem, the actors. Cite inline (`(customer-process.pdf p.2)`).
- **Known facts** — `Type: FACT`, only what a material states explicitly. `Source:` = exact location. A rule the materials state ("bookings over 10k need manager approval") is a FACT here — do **not** mint `BR-` ids: no features exist yet, so a rule's scope (local vs cross-cutting) is unknown. `/protoflow-spec` assigns `BR-` ids later.
- **Assumptions** — `Type: ASSUMPTION`, `Source: AI-inferred (from <file loc>)`. Only what you genuinely had to assume to make sense of the materials. Never phrase one as settled.
- **Open questions** — `Type: UNKNOWN`. Gaps a spec will need: missing limits/numbers, undefined statuses, actors without stated permissions, vague words ("quickly", "large"), referenced documents not provided. `Source:` = what raised it. Write the body as the question to put to the customer.
- **Contradictions** — `Type: CONFLICT`, `Source: <doc A loc> vs <doc B loc>`. Body: "Document A says X; document B says Y." **Never pick a side.**
- **Entities** → `entities.md`. A noun the business stores and acts on (customer, booking, invoice) becomes an `ENT-` item — `Type: FACT` if the materials define its fields (e.g. spreadsheet columns), else `INFERENCE`. Allocate ids per `ids.md`: scan all of `docs/` for the highest `ENT-` number, reserve the whole block up front, assign sequentially. If ≥2 entities have stated relationships, update the mermaid `erDiagram`; otherwise leave the ERD placeholder and say so in the report.
- **Glossary** → `glossary.md`. One table row per customer term with its customer-specific meaning and source. A term used two ways or never defined goes under "Disputed / ambiguous terms" as `UNKNOWN` or `CONFLICT`.

**Cross-check the interview** (only if `interview.md` has real items). For each interview item the materials speak to:

Link back with the interview item's exact `### <label>` (or the term, for a Key-terms row) — the brief reads these links to mark each point (`${CLAUDE_PLUGIN_ROOT}/references/interview-brief.md`):

- **Materials agree** → the grounding item is a normal `FACT` from the material; append `· matches BA interview › <label>` to its `Source:`.
- **Materials contradict** → add a `CONFLICT` under Contradictions, `Source: BA interview › <label> vs <file loc>`, body "The BA said X; <file> says Y." Never pick a side — the BA may know something newer than the document.
- **Materials answer an interview open question** → record the material's `FACT` as usual with `· answers BA interview › <label>` appended to its `Source:`; list it in the report so the BA can mark the interview question answered.
- Interview **key terms** that the materials use → glossary rows cite the material; terms only the BA mentioned stay out of the glossary (list them in the report).

Never copy an interview item into grounding without a material citation — interview content is the BA's, not the customer's documents'. (The exception is already done: when the customer had no materials, `/protoflow-interview` grounded the project from the interview — see Step 4.)

**Discipline:** never promote an `ASSUMPTION`/`INFERENCE` to `FACT`. Never write an item without a real `Source:`. Never write anything under `## Feature scope` — the feature spine belongs to `/protoflow-explore`'s scope pass.

## Step 4 — Merge, never clobber

`grounding.md` was seeded by `/protoflow-new` and may already hold human-confirmed work.

- **First run** (the file still has template placeholders — `<project>`, `<label>`, `<prose overview…>`, the `FACT-NOTE` example): replace the placeholder example blocks and the `<project>` token in `glossary.md`/`entities.md` the same way. Keep every section heading and its italic intro line. Leave `## Feature scope` exactly as it is.
- **Re-run:** before adding an item, compare it against existing items in the same section — same claim from the same source is a duplicate; skip it. Never edit, reword, or remove an item whose `Status:` is `confirmed` or whose `Confirmed:` line is filled. If new material contradicts a confirmed item, add a new `CONFLICT` citing both rather than touching the confirmed one. A new fact that sharpens a `proposed` item from the same source may update it; otherwise add alongside.
- **Materials index:** one row per file — `| File | What it is | Read | Notes |`, `Read` ∈ `yes` / `partial` / `no`. Update existing rows in place; add new ones.
- **Grounding built from the interview** (Materials index has the `| — | no customer materials | … |` row — the customer had none at interview time, and materials have now arrived):
  - replace that row with the real file rows;
  - when a material confirms an interview-sourced item (`Source: BA interview … › <label>`), append `· <file loc>` to its `Source:` instead of adding a duplicate FACT;
  - when a material contradicts one, leave the item and add a `CONFLICT` as in the cross-check;
  - in `interview.md`, set `## Source basis` → `Materials: available` (`Set: <today>`) — the only edit you make to that file.
- Once a doc holds human content, write with targeted Edits (insert under the right section), not a whole-file rewrite.

## Step 5 — Refresh the project brief

If `interview.md` holds real items, regenerate both brief pages (`docs/interview.html`, `docs/interview-tree.html`) exactly as `${CLAUDE_PLUGIN_ROOT}/references/interview-brief.md` defines, so each interview point now shows whether the materials matched it, contradicted it, or haven't covered it yet. If the basis was still `expected`, set it to `available` first (as above). No interview → skip.

## Step 6 — Report

Print a short summary for the BA:

- files read: N `yes`, N `partial`, N `no` (name the non-`yes` ones and why);
- items added: FACT / ASSUMPTION / UNKNOWN / CONFLICT counts; ENT ids minted; glossary rows added;
- interview cross-check (if any): N confirmed by materials, N contradicted (each is a CONFLICT), interview questions now answered, interview claims no material covered yet — and the refreshed brief `docs/interview.html` (tree view: `interview-tree.html`);
- the top open questions and every conflict — the agenda for the next customer conversation;
- next step: `/protoflow-explore <project>` (scope pass), or `/protoflow-status <project>` for the dashboard.
