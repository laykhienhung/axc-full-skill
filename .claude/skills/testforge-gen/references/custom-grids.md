# Editable data grids that resist normal Playwright

Load this ONLY when a target is an editable grid/table whose cells have no per-cell
`<input>` in the DOM (custom canvas-like grids: CyberLogitec "IB", ag-Grid, some MUI).

## How to detect one

`browser_evaluate` a quick probe:
```js
() => ({
  ag: !!document.querySelector('.ag-root'),
  rdg: !!document.querySelector('.rdg'),
  mui: !!document.querySelector('.MuiDataGrid-root'),
  cellHasInput: !!document.querySelector('td [contenteditable], td input'),
  tableClass: document.querySelector('table')?.className,
})
```
No cell inputs + a proprietary table class = custom grid. Editing is a single hidden textbox
activated by clicking a cell.

## The contract that actually works (learned from CyberLogitec IB grid)

1. **Edit = click cell → type → commit.** A cell click focuses one hidden `<input>`.
   Type, then `Tab` (moves right / commits) or `Enter`.
2. **Fill a whole row with ONE click + a Tab-chain.** Click the first editable cell, type,
   then `press('Tab'); type(next); ...` across columns in visual order. Do NOT re-locate the
   cell between columns.
3. **Why re-locating breaks:** editing often auto-appends a trailing empty row, so `.last()`
   and "last data cell" drift to the wrong row mid-fill and your values scatter. The Tab-chain
   from a single anchor avoids this entirely.
4. **Column keys are class suffixes, and the prefix is dynamic.** Cells look like
   `HideCol2pckUtCd` one render and `HideCol1pckUtCd` the next. Target by suffix
   (`td[class*="pckUtCd"]`), never the full class.
5. **Booleans (Use Y/N) are not checkboxes.** They render as an element whose class encodes
   state (`IBBool0` off / `IBBool1` on). Click the cell to toggle; assert on the class, not
   `isChecked()`.
6. **Read-back by value, not by index.** To verify, find the row whose code cell text equals
   what you typed, then read its sibling cells. Row indices move.

## Encode it in the Page Object, not the spec

Wrap all of the above (coordinate click, Tab-chain fill, boolean toggle, value read-back)
as methods on the grid's Page Object. The spec should say `addRow(data)` / `setUseYN(code)` /
`rowByCode(code)` — never contain a coordinate or a class suffix. See the CARISDO-TC-1
`PackageCodePage` in `tests/pages/` for a working reference implementation.

## Confirmation dialogs may not exist

Test cases often say "Click [OK] on the confirmation dialog". Many grids commit on Save with
NO dialog. Capture first: click Save, then `browser_find` for a dialog. If none appears,
drop the dialog step and note the deviation to the user — do not invent a `.click('OK')`
that will hang.
