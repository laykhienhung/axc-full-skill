# Playwright Live Capture — discovering real selectors

Load this when a step's selector is unknown and you must drive the live app to find it.

## Why capture at all

Never guess selectors from a test-case description. A step like "Click [Add New] button"
may render as a button labeled `Add` (not `Add New`). Capture the real DOM, then encode it.

## The loop (per unknown step)

1. `browser_navigate` to the app.
2. `browser_snapshot` for small pages. For large apps the full snapshot overflows —
   use `browser_find` with a regex instead (`/add new|save|search/i`) to locate an element
   + its `ref` cheaply.
3. Act via the returned `ref` (`browser_click`, `browser_fill_form`).
4. Re-`find` to confirm the next state before scripting it.

## Token discipline (this is a hard rule, not a suggestion)

- `browser_snapshot` on a real enterprise page can be 140k+ chars — it WILL overflow.
  Reach for `browser_find` (regex, returns snippets) or a scoped
  `browser_snapshot({target: ref})` on a subtree instead.
- Prefer `browser_evaluate` / `browser_run_code_unsafe` returning a SMALL structured object
  (the fields you need) over dumping DOM. One targeted evaluate beats five snapshots.
- Do NOT read the saved `page-*.yml` snapshot files back in full. Query for what you need.

## Role/label selectors first, coordinates last

Prefer, in order: `getByRole` → `getByLabel` → `getByPlaceholder` → `getByText` →
`data-*` attribute → CSS class → coordinate click. Coordinates only when the widget has no
addressable element (see custom-grids.md).

## Stale-tab / SPA hazard

Enterprise SPAs (mantine tabs, keep-alive panels) leave multiple hidden copies of a panel
in the DOM after navigation. When several elements match:
- Filter to the VISIBLE one: bounding box has width/height > 0 and
  `visibility !== 'hidden'` and `display !== 'none'`.
- Click "the first visible match", not `.first()` (which may be a hidden stale copy).
- If tab state is corrupted mid-session, a fresh `browser_navigate` + re-open is cheaper
  than fighting stale nodes.

## Confirm before you script

After each captured action, verify the observable result (row count changed, cell text set,
URL changed). A step that "ran" without a confirmed effect is not captured — it's assumed.
