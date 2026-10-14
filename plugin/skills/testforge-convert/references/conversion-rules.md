# Conversion rules: manual checklist case → common TestCase template

The input is one extracted case (`extract_manual.py` output). The output is one JSON object:

```json
{"key": "R4", "type": "Auto", "type_reason": "", "summary": "Verify ...", "priority": "High",
 "pre": "1. ...", "action": "1. ...\n2. ...", "input": "1. -\n2. ...",
 "checkpoint": "1. ...\n2. ...", "expected": "1. ...\n2. ..."}
```

Do not write a TC #, Test Repository Path or Regression value. `write_template.py` fills those in.

## Iron rule: never invent

Every value, account, code, message text and number must come from the source case: its
`desc`, `pre`, `section_pre`, `steps`, `expected` or `path`. If a step needs a value the source
doesn't give, write `TBD` in Input Data. Don't guess it. Do rephrase, split and reorder, but
don't add behaviour that the source doesn't state.

One narrow exception: **suggested synthetic input**. When the step's own wording fixes the
*shape* of a value (a length, a character class, an invalid format, a page size named in the
source), you may write a sample value in Input Data and end it with ` [suggested]`. Rules:
- Values the source actually gives are copied verbatim with **no** tag.
- `[suggested]` appears only in `input`, never in `pre`, `action`, `checkpoint` or `expected`.
- Business data is never guessed: existing or unused codes, names, accounts, B/L / booking
  numbers stay `TBD`. You may add a format hint, still tagged:
  `Code = TBD (unused Commodity Code; e.g. ZZZ999) [suggested]`.
- Message texts, expected values and counts are never suggested.

## Suggested values

| Source wording | Input Data |
|---|---|
| "longer than N characters" | `Field = A×(N+1) [suggested]` |
| "max length N" / "exactly N characters" | `Field = A×N [suggested]` |
| "long data" (no N given) | `Field = A×TBD (longer than the field limit) [suggested]` |
| "a-z A-Z 0-9, special characters and space" / "special characters" | `Field = aZ09 !@#$% [suggested]` |
| "only spaces" / "leading and trailing spaces" | `Field = "   " [suggested]` / `Field = "  abc  " [suggested]` |
| "Input language", languages named in the source (English, Vietnamese, Chinese, Japanese) | one sample per named language only: `Field = abc; Tiếng Việt; 中文; 日本語 [suggested]` |
| "invalid data" in a code field | `Field = @@@ [suggested]` |
| "page size greater than total rows" | the largest page size the source names, e.g. `Page size = 2000 [suggested]`; otherwise `TBD` |
| "change the page size" (options named in the source) | one of those options, e.g. `Page size = 50 [suggested]` |
| "a keyword" / "partial value" / "valid data" | `Field = TBD (e.g. first 3 chars of an existing value) [suggested]` |
| "paste data" | the same value as the typed step, with ` (paste)`: `Field = A×101 (paste) [suggested]` |

`A×101` means the letter `A` repeated 101 times. Write the notation, not the literal string.

## Fields

| Field | Rule |
|---|---|
| `summary` | One sentence that starts with `Verify`. Keep the source `desc` meaning. If the desc is only a label (e.g. "Popup Name"), expand it from the steps and expected result: `Verify the Commodity Search pop-up name follows the common UI rules`. |
| `pre` | A numbered list built from `section_pre`, then the case's `pre`, then `<screen> screen is opened` when the first step opens the screen. Leave it empty (`""`) when there is nothing to say. |
| `action` | Numbered, imperative, **one line per step and one action per step**. Buttons and keys go in `[Brackets]`. Keep menu paths as written (`Open Ocean Export > Master B/L > OEM B/L List`). Split a source step that does two things into two steps. A pure "check / observe X" step becomes `Observe X`. |
| `input` | The **same numbering as `action`**. Write `Field = value` and use `-` when a step takes no input. Join several values in one step with `; `. A suggested value ends with ` [suggested]`, one tag per value (see **Suggested values**). |
| `checkpoint` | The **same numbering**. Each line is a short noun phrase saying what is checked at that step (`Default focus field`, `[Search] button visibility`). |
| `expected` | The **same numbering**. Each line is the observable result of that step, rewritten from the source's bullets. The source's `Point N:` blocks map to step N. A step the source gives no result for gets the state it leads to (`The pop-up is displayed`), still drawn from the source. Put a step's several bullets on its one line, separated by `; `. |
| `priority` | Copy the source priority as `High`, `Medium` or `Low`. If it's blank, use `Medium`. |
| `type` | `Auto` or `Manual`. See below. |
| `type_reason` | Empty for `Auto`. For `Manual`, give a short reason (`visual CSS check`). |

Each of `action`, `input`, `checkpoint` and `expected` is a numbered list `1. … n.` with the
**same n**. Write one line per number with no continuation lines. That way `read_cases.py` (testforge-gen) gives every
step its expected result.

## Type: Auto vs Manual

Choose **Manual** when the check can't be asserted from the DOM in one browser session:
- visual style: font, colour, size, padding, alignment, hover cursor, CSS, spelling or wording review, "Misspelling", layout at a given screen resolution
- moving or dragging a pop-up by eye, or "observe" checks with no concrete expected value
- more than one actor or session (e.g. "the super admin changes the user's permission" while the user stays logged in), or a logout and login as a different role
- other browsers (Firefox, Safari), printing, a physical email or fax, a downloaded file opened in another app
- a percentage or a sampled checklist ("Execute 30% of the UI common checklist")

Everything else is **Auto**: navigation, input, buttons, grid data, validation messages,
pop-up open and close, keyboard ([Tab], [Enter], shortcuts) focus order, sort and pagination, and permission visibility for the logged-in user.

The source Status (Passed / Failed / Pending / Blocked), Remark and bug IDs are **not**
carried over, and they do not decide the Type.

## Example

Source:
```
desc: Verify user cannot use some buttons without permission
pre:  User doesn't have permission to use button:\n- [Search]\n- [Save]\n- [+ Add New]
steps: 1. Open Ocean Export > Master B/L > OEM B/L List\n2. Click on and observe display button on UI
expected: User cannot search data, add a new OEM B/L Entry, or save ...\n- [Search] button is hidden\n- [Save] button is hidden\n- [+ Add New] button is hidden\n- Remaining buttons are displayed
priority: High
```

Output:
```json
{"key": "R9", "type": "Auto", "type_reason": "", "priority": "High",
 "summary": "Verify user without [Search], [Save] and [+ Add New] permission cannot see those buttons on OEM B/L List",
 "pre": "1. User doesn't have permission to use buttons [Search], [Save], [+ Add New]",
 "action": "1. Open Ocean Export > Master B/L > OEM B/L List\n2. Observe the buttons displayed on the UI",
 "input": "1. -\n2. -",
 "checkpoint": "1. OEM B/L List screen opens\n2. Visibility of [Search], [Save], [+ Add New] and the remaining buttons",
 "expected": "1. OEM B/L List screen is displayed\n2. [Search], [Save] and [+ Add New] buttons are hidden; the remaining buttons are displayed; the user cannot search, add a new OEM B/L Entry, or save"}
```

### Example with suggested input

Source (shortened):
```
desc: Verify the data validation of the Commodity Name field
steps: 1. Check max length\n2. Check input data\n3. Input language\n4. Search by invalid data\n5. Search by valid data
expected: Point 1: Data layout: Free text (max length = 100); the user cannot input long data
          Point 2: Free input: az - AZ, 0 - 9, special character, space; Auto-upcase
          Point 3: Allow: English, Vietnamese, Chinese, Japanese
          Point 4: Display an empty table with the message "No Data Found"
          Point 5: Display list results match the search conditions
```

Input Data (the max length of 100 and the language list come from the source; the existing
commodity name is business data, so it stays `TBD`):
```
1. Commodity Name = A×101 [suggested]
2. Commodity Name = aZ09 !@#$% [suggested]
3. Commodity Name = abc; Tiếng Việt; 中文; 日本語 [suggested]
4. Commodity Name = @@@ [suggested]
5. Commodity Name = TBD (e.g. first 3 chars of an existing commodity name) [suggested]
```
