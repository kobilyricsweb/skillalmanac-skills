---
name: excel-formula-debugger
description: Finds why spreadsheet formulas break or give wrong numbers, by auditing an .xlsx for error values traced to their root cell, broken or empty references, circular references, volatile functions, deep nested IFs, hard-coded constants, overwritten cells and formulas that differ from their neighbours. Use when the user says a formula shows #REF!, #N/A, #DIV/0! or #NAME?, a circular reference warning, a total that is off, a sheet that is slow, or asks to check or fix Excel formulas. Do not use for data analysis or charts, pivot design, macros or VBA, or writing a formula from scratch with nothing to debug.
license: Apache-2.0
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  author_model: claude-sonnet-5-5
  version: "0.1.0"
  network: none
---

# Excel formula debugger

Debug formulas the way a reviewer would: find the one cell that is really wrong, say why, and change as little as possible. The script reads the saved file and reports structure; you supply the judgement about what the sheet is meant to do.

## Ask first

Get these before touching anything: the spreadsheet app and version (Excel desktop, Microsoft 365, Google Sheets, LibreOffice), the cell that looks wrong, what it should show, and the file or the exact formula text. Formulas typed with semicolons (many European locales) are stored with commas in the file; treat them as the same formula. For Google Sheets or LibreOffice, ask for File > Download > .xlsx and audit that copy.

## Workflow

```
- [ ] 1 Run the audit on a copy
- [ ] 2 Triage findings in the fixed order
- [ ] 3 Diagnose each root cause against the symptom table
- [ ] 4 Make the smallest fix, keep anchoring
- [ ] 5 Re-run and compare
- [ ] 6 Report
```

1. **Audit.** `python scripts/audit_workbook.py <file.xlsx>`. It prints one JSON document and changes nothing. Exit 0: no error-severity finding; 1: at least one; 2: the file could not be read as a workbook (`.xls`, `.xlsb`, password-protected, corrupt) and the message says what to do. Never edit the script to make a check pass. Without Python, read the formulas by hand against [references/error-causes.md](references/error-causes.md).
2. **Triage** in this order, because earlier items cause later ones: `error_value` with `root_cause: true`, `circular_reference`, `broken_reference` and `missing_sheet`, `external_link`, `inconsistent_formula` and `hardcoded_value_in_formula_column`, `number_stored_as_text`, `empty_reference`, then `hardcoded_constant`, `nested_if`, `volatile_function`, `newer_function`. An `error_value` with `root_cause: false` is inherited; do not touch it, fix its `inherited_from` cells.
3. **Diagnose** with the table below. Open the cell, step through it with Formulas > Evaluate Formula (Excel) or by editing a copy into pieces.
4. **Fix.** One cell at a time, filling down only after the first cell is right. Keep `$` anchors exactly as the neighbours have them. Rewrite recipes for nested IF, INDIRECT, OFFSET, circular loops and magic numbers are in [references/rewrites.md](references/rewrites.md); read only the section you need.
5. **Re-run** the audit on the fixed copy. The finding you fixed must be gone, and no new category may appear. Pick one result and recompute it by hand or with a calculator.
6. **Report** in the fixed shape below.

## Symptom table

| Symptom | First test | Most likely cause |
|---|---|---|
| `#DIV/0!` | Is the divisor cell empty, zero or text? | Blank input read as zero; fix the input or guard that one divisor |
| `#N/A` from a lookup | Compare the key and the lookup column with `=A2=D5`, and `=LEN()` on both | Trailing space, text-versus-number, wrong range, or exact match missing (last argument `0` or `FALSE`) |
| `#NAME?` | Does the name exist in Name Manager; is the function spelled right; does this version have it? | Typo, undefined name, text without quotes, or a function newer than the user's version |
| `#REF!` | Does the formula text contain `#REF!`? | A deleted row, column or sheet; rebuild the reference, do not mask it |
| `#VALUE!` | Evaluate the formula step by step | Text in arithmetic, a range where one value is expected, a date stored as text |
| Total too small | Are some numbers left-aligned or tagged "stored as text"? | `number_stored_as_text`; SUM ignores text in a range |
| Total unchanged after an edit | Is calculation set to Manual (Formulas > Calculation Options)? | Manual mode, or a typed number overwriting a formula |
| One row differs from its neighbours | `inconsistent_formula` expected text | Edited cell or broken fill-down; refill from a correct cell |
| Lookup returns a neighbour's value | Last argument of VLOOKUP or MATCH | Approximate match is the default for VLOOKUP when the argument is omitted |
| Slow after small edits | `volatile_cells` and `volatile_downstream_cells` | Every dependent of NOW, TODAY, RAND, OFFSET or INDIRECT recalculates on any change |
| Circular warning | `circular_reference.path` | A total includes its own cell, or two cells feed each other |

## Thresholds the script uses

- Nested IF: reported from depth 4 (three levels still read). From depth 8 the wording says so.
- Inconsistency: a column needs 4 or more formulas, and one pattern shared by at least 3 of them and 60% or more. Rows need 5 or more formulas and 80%. A final SUM, SUBTOTAL, AVERAGE, COUNT, MIN or MAX cell is treated as a total row and not reported.
- Hard-coded constants: 0, 1, 2 and 100 in arithmetic or as a bare argument, and 0 and 1 in comparisons, are ignored, as are small integers used as positions or digits (VLOOKUP column, ROUND digits). Other constants in arithmetic are warnings, in comparisons or arguments are info.
- Empty references: a single empty cell is a warning, an entirely empty range is info. Whole-column and whole-row references are skipped.

## Output contract

Strict JSON on stdout, ASCII only. Top level: `tool`, `version`, `file`, `ok` (no error-severity finding), `workbook` (`sheets`, `formula_cells`, `cached_values_present`, `iterative_calculation`, `defined_names`, `external_link_parts`, `volatile_cells`, `volatile_downstream_cells`), `sheets[]` (`name`, `state`, `formula_cells`, `value_cells`, `error_cells`, `volatile_cells`, `max_if_depth`, `cross_sheet_targets`, `used_range`), `counts_by_category`, `counts_by_severity`, `truncated_categories`, `findings[]`, `not_checked[]`. Each finding has `severity` (error, warning, info), `category`, `sheet`, `cell`, `message`, `suggestion`, and extras such as `formula`, `expected`, `path`, `cells`, `root_cause`. At most 200 findings are kept per category; `counts_by_category` always holds the true totals. Quote `not_checked` in your report.

## Report format

```
Root cause(s): <cell: what is wrong, one line each>
Changed: <cell: old formula -> new formula>
Left alone: <findings judged intentional or out of scope, with reason>
Re-run: <ok true or the findings that remain>
Not checked: <items from not_checked that matter here, and that results were not recalculated>
```

If nothing is wrong, say the audit found nothing and name what it cannot see; do not invent issues to look useful.

## Limits

- Cell results are read as saved in the file. Nothing is recalculated, so a file never calculated (for example written by a script) has no error values to find; `cached_values_present: false` says so.
- Dependencies through INDIRECT, OFFSET, structured table references (`Table1[Col]`) and 3D ranges are not followed, so loops through them are missed. Excel itself may also flag a loop that sits in an untaken IF branch; the script flags it too.
- Defined names are followed only when they are one plain reference.
- Consistency checks look along one column or one row. A formula that is wrong in the same way everywhere passes.
- The script does not judge whether a formula answers the question, and does not check function names or argument counts.
- `.xls`, `.xlsb`, encrypted workbooks and chart-only sheets are not read. Conditional-format and data-validation formulas are not read.
- The thresholds are working values, not measured optima. Newer-function version labels were written from general knowledge and should be confirmed for the user's build.
