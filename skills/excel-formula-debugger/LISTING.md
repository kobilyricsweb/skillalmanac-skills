# excel-formula-debugger

**One-line summary:** audits an .xlsx for the cell that is really wrong: error values traced to their root, circular and broken references, overwritten and inconsistent formulas.

## What it does

The skill walks an agent through a fixed debugging procedure for spreadsheet formulas. A bundled Python script (standard library only, no network, read-only) opens the workbook as a zip of XML, reads every formula and its saved result, builds a dependency graph, and prints one strict JSON report. The report separates the root cause of an error from the cells that merely inherit it, finds loops by graph search and shows the path, and compares each formula with the pattern its column or row shares. A symptom table and two reference files (error causes, rewrite recipes) turn the findings into fixes and a fixed-format report.

## Capabilities

- Formula and error-cell counts per sheet; each error value marked as root cause or inherited, with the cells it came from.
- Missing sheets, `#REF!` inside formulas, links to other workbooks, references to empty cells and ranges, undefined names.
- Circular references with the cell path, including self-references, and a note when iterative calculation hides them.
- Hard-coded constants, volatile functions and how many cells depend on them, nested IF depth from 4, functions that need a newer version.
- Formulas that differ from their column or row, typed numbers inside a formula column, numbers stored as text.

## When to use / when not to

Use when a formula shows `#REF!`, `#N/A`, `#DIV/0!` or `#NAME?`, when Excel warns of a circular reference, when a total is off, when a workbook is slow, or before sending a workbook to someone.

Not for: analysing the data itself, charts, pivot tables, VBA, or writing a new formula with nothing to debug. The nearest existing skill is `spreadsheet-analysis`, which analyses what the data says; this one debugs how the formulas are built.

## Requirements

Python 3.9 or newer, standard library only. No network. Reads .xlsx and .xlsm; not .xls, .xlsb or password-protected files.

## Install

Copy the folder to `.claude/skills/excel-formula-debugger/` or `.agents/skills/excel-formula-debugger/`. Pin to a commit when the catalogue publishes one.

## Examples

Prompt: "The Orders sheet in broken.xlsx shows #DIV/0! in I2 and I3 and #N/A in I4. What is wrong?"

Real output of `python scripts/audit_workbook.py broken.xlsx` on the test workbook (trimmed to the relevant findings; 29 formulas, 24 findings):

```
error  error_value        Orders!I2  #DIV/0!: a divisor is zero or an empty cell ...   (root_cause: true, formula =B2/B9)
info   error_value        Orders!I3  #DIV/0! inherited from I2; fix those first
error  error_value        Orders!I4  #N/A: a lookup found no match ...                   (formula =VLOOKUP("zz",A2:B7,2,0))
warning empty_reference   Orders!I2  refers to B9, which holds nothing
error  circular_reference Orders!J2  circular chain of 2 cells: J2 -> J3 -> J2.
warning inconsistent_formula Orders!D4  differs from the pattern shared by 4 of 5 formulas in its column; that pattern would give =B4*C4
warning hardcoded_value_in_formula_column Orders!D6  typed number 250 sits between formulas that follow one pattern
```

The agent then reports: root cause I2 (empty divisor B9), I3 inherits it, I4 is a lookup for "zz" that is not in A2:A7; no IFERROR wrapper recommended.

A second prompt, "check clean.xlsx before I send it", returns `ok: true` with no findings; the closing SUM in D7 is recognised as a total row and not reported.

## Limits

Results are read as saved in the file; nothing is recalculated. Loops through INDIRECT, OFFSET, table references and 3D ranges are not seen. Consistency is checked along one column or row only. The script does not judge whether a formula is the right formula, and does not validate function names or argument counts. Thresholds are working values.

## Evidence

Static lint 0 FAIL / 0 WARN; 7 of 7 script fixtures pass (expected results worked out by hand). Not tested: efficacy against a baseline run, triggering in any tool, cross-tool installs, real Excel-written workbooks with shared formulas and tables beyond one fixture, human review. See VERIFICATION.md.

## Demo script (60 to 90 seconds)

1. Prompt: "My Orders sheet shows #DIV/0! and I can't see why. File attached."
2. The agent runs the audit and reads the JSON: six error cells, five root causes.
3. It points at I2 (`=B2/B9`, B9 empty) and says I3 only inherits it.
4. It explains #N/A in I4 as a missing lookup key and does not mask it.
5. Before/after: a re-run of the audit on the fixed copy shows the I-column findings gone.

## FAQ seeds

- Does it need network or Excel installed? No; it reads the file directly.
- Does it work on Google Sheets? Download the sheet as .xlsx and audit that copy.
- Does it recalculate my workbook? No; it reads the results saved in the file.
- Why does a file made by a script show no errors? Such files carry no saved results; open and save it in the app first.
- How is it different from spreadsheet-analysis? That one analyses data; this one debugs formulas.
- Will it change my file? No; the script is read-only and the agent works on a copy.
- Which files can it not read? .xls, .xlsb, password-protected and corrupt files.

## Changelog

0.1.0 (2026-11-21): first draft; static lint and script fixtures only.

## License and authorship

Apache-2.0, copyright Global Media Holdings (skillalmanac.com). Drafted with AI assistance (claude-sonnet-5-5); accountable publisher Global Media Holdings. No human review has taken place yet.
