---
name: pdf-extraction-and-forms
description: Extracts text and tables from PDF files and fills PDF form fields without silent errors. Use when the user wants data out of a PDF, a scanned PDF read, a table to CSV, or a form filled. A script triages the file (pages, text layer or scan, form field names, encryption), a decision table picks direct extraction or OCR, table checks test row counts and sums, and a mapping contract plus read-back check proves what was filled. Do not use for creating, merging or redesigning PDFs, e-signing, or removing passwords.
license: Apache-2.0
compatibility: The three scripts need Python 3.9 or newer, standard library only, no network. OCR, table and form-writing tools are named options the user installs; this skill never installs anything. Without Python, follow the manual fallback in each step.
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  author_model: claude-sonnet-5-5
  version: "0.1.0"
  network: none
---

# PDF extraction and forms

PDF is a drawing format, not a data format. The common failures are silent: a scan "extracts" as an empty string, a table loses a row at a page break, a form value is written but never shows. This skill makes each of those loud.

## Scripts (run them; do not edit them to make a check pass)

| Script | Job | Exit |
|---|---|---|
| `scripts/pdf_inspect.py file.pdf` | Byte-level triage, strict JSON | 0 inspected, 2 error or not a PDF |
| `scripts/table_check.py table.csv [--rows N] [--cols N] [--sum COL=VALUE] [--total-row] [--decimal comma]` | Validates an extracted table | 0 pass, 1 fail, 2 usage |
| `scripts/form_verify.py mapping.json out_inspect.json [--original blank_inspect.json]` | Compares the mapping with values read back from the filled PDF | 0 pass, 1 fail, 2 usage |

`pdf_inspect.py` is a byte scan, not a parser. Its fields: `page_count`, `page_count_confident`, `text_layer` (`text_layer_likely`, `ocr_layer_likely`, `image_only_likely`, `mixed`, `unknown`), `pages_with_text_operators`, `image_objects`, `type0_fonts_without_tounicode`, `encryption.encrypted`, `form.fields[]` (`name`, `type`, `value`, `required`, `read_only`, `on_states`), `form.xfa`, `warnings[]`. Read `warnings` every time.

## Workflow

```
- [ ] 1 Triage the file
- [ ] 2 Choose the route from the decision table
- [ ] 3 Extract (text or table) or map (form)
- [ ] 4 Validate with the checks
- [ ] 5 Re-read the saved output and verify
- [ ] 6 Report
```

1. **Triage.** `python scripts/pdf_inspect.py file.pdf`. Never extract before this. No Python: open the file, try to select text on two pages, note the page count and whether form fields highlight.
2. **Route** by `text_layer` and `warnings`:

| Result | Meaning | Route |
|---|---|---|
| `text_layer_likely`, no warnings | Real text on every page | Extract directly with a layout-aware text tool |
| `ocr_layer_likely` | Scan with an invisible OCR layer: text exists but carries OCR errors | Extract, then spot-check 5 numbers and 5 names per document against the page image |
| `image_only_likely` | Scan, no text at all | OCR needed. Ask the user which OCR tool they have or want; list options from `references/tools.md`; never install anything. Rasterise at 300 dpi |
| `mixed` | Some pages text, some images | Route per page. Keep a page-to-method list in the report |
| `type0_fonts_without_tounicode` above 0 | Text layer may paste as garbage | Extract one page; if it is garbled, treat as `image_only_likely` |
| `unknown` | Content in compressed object streams or an unsupported filter | Try a real extraction tool on page 1; if it returns text, proceed; if empty, treat as a scan |
| `encryption.encrypted` true | Content cannot be read by the script | Ask the user for the password. Do not guess, bypass or strip it |
| `form.xfa` true | Dynamic XFA form; AcroForm fillers will not work | Stop; tell the user to use a viewer with XFA support or request a static version |

3. **Extract.** Text: keep page numbers; one output file per document with a `--- page N ---` marker. Tables: one CSV per table (UTF-8, header row first) plus the page it came from. Tools that find tables by ruling lines fail on borderless tables; tools that guess from whitespace invent columns. State which kind was used.
4. **Validate tables** with `table_check.py`, against numbers that come from the PDF, not from the extraction:
   - `--rows N`: N is counted independently (an "N items" line, a visible row count, line numbers printed in the table). No independent count: report "row count unverified".
   - `--sum COL=VALUE` takes the printed column total; `--total-row` is for a last row that is the printed total.
   - Default tolerance is 0.01 (one cent). A printed total that disagrees with its own rows by more than that is a finding about the PDF too: report it, do not adjust cells.
   - Traps the script names: a header repeated at every page break (`repeated_header_rows`), a wrapped cell split into an extra row (`ragged_rows`), `O` for 0 and `l` for 1 (`numeric_cells_parse`). Also watch footnote marks glued to numbers, `(1,234)` negatives, trailing minus, and `1.234,56` decimals (`--decimal comma`).
   - Any failed check: fix the extraction (another table method, a page range) and re-run. Never edit cells by hand to make a sum match.
5. **Forms** follow the contract below.
6. **Re-read** the saved output, not the working variable: reopen the CSV or text file, or inspect the filled PDF again, and run the checks on that.
7. **Report** in the fixed shape at the end.

## Form-field mapping contract

Write `mapping.json` before touching the PDF. Strict shape:

```json
{
  "form": "blank.pdf",
  "output": "filled.pdf",
  "fields": [
    {"pdf_field": "form1.Name", "value": "Jane Doe", "source": "where this value came from", "type": "text", "required": false}
  ],
  "unfilled_on_purpose": [{"pdf_field": "Signature", "reason": "user signs by hand"}]
}
```

Rules:
1. `pdf_field` is copied exactly from `form.fields[].name`. Names are often opaque (`f1_3[0]`): match by the label printed beside the field on the page, and ask the user when two readings are possible. Never guess between "Home" and "Mailing" address.
2. `source` is required and must be the user, a named file or a named page of the PDF. A value without a source is not filled.
3. Checkbox and radio values are an entry of that field's `on_states` (often `Yes`, but not always `1`, `On` or `Y`), never `true`.
4. Fields of `type` `signature` and any `read_only` field are never filled; list them under `unfilled_on_purpose`.
5. Every `required: true` field is either in `fields` or in `unfilled_on_purpose` with a reason.
6. Dropdown and list values must be one of the form's own options. The script does not list options: check them in the viewer or with the form tool's own listing before writing.
7. Write to a new file. Never overwrite the blank form. The form-writing library is one the user has installed (see `references/tools.md`); do not install one.
8. Identity numbers, bank details and health data: use only what the user supplied for this form, do not repeat the values in the report, name the fields only.

Form verification: `pdf_inspect.py filled.pdf > out.json`, then `form_verify.py mapping.json out.json --original blank.json` (blank.json is the inspect report of the blank form). Statuses: `ok`, `missing_in_output`, `empty_in_output`, `value_mismatch`, `unexpected_value`, `required_empty_not_declared`, `unreadable`. Exit 0 is required. `unreadable` is not a pass: fields inside compressed object streams or an encrypted output cannot be read back by the script, so reopen the file in a form-aware reader, compare by eye, and say so. Last, view the page: some fillers store the value but no appearance, so the box looks empty. If it does, report it; do not claim success.

## Report (fixed shape)

```
File: <name>, <page_count> pages, text_layer <value>, route <chosen route>
Output: <files written, with page or table counts>
Checks: <each script check and result; tables: rows found vs expected, sums vs printed totals>
Unverified: <what had no independent check, e.g. "row count: no printed count">
Needs the user: <ambiguous fields, missing password, tools to install, OCR spot-check results>
```

## Limits

- `pdf_inspect.py` does not follow the cross-reference table or read compressed object streams, so many modern files give `unknown` or a null page count; encrypted files give nothing beyond the encryption header.
- A text layer found is not proof the text is correct or in reading order; a scan is detected only by the absence of text operators.
- Page and field counts rely on plain objects; incremental saves can leave deleted pages visible (a warning is given when counts disagree).
- `table_check.py` cannot detect a wrong cell that still sums correctly, and cannot verify a row count it is not given.
- `form_verify.py` reads stored field values, not what a viewer renders.
- Not covered: PDF creation, merging, redaction, signatures, XFA, password removal, layout reconstruction, handwriting.
- Manual fallback for every script: select text on sample pages, count rows and sum columns by hand or in a spreadsheet, open the filled form in a viewer and read each mapped field.

Read [references/tools.md](references/tools.md) only when a route needs a tool the user lacks: it lists open-source options, what each is for and its licence note.
