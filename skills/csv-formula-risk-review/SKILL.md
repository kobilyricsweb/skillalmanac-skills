---
name: csv-formula-risk-review
description: Review a UTF-8 CSV export for cells that could be interpreted as spreadsheet formulas before sharing or opening it in Excel or another spreadsheet app. Report exact record and column locations without editing data. Use for CSV export safety review, not general CSV validation or a guarantee of safe spreadsheet execution.
license: Apache-2.0
metadata:
  author: Global Media Holdings
  version: "0.1.0"
  network: none
  compatibility: Python 3.9 or newer, standard library only. No network or spreadsheet application required.
---

# CSV Formula Risk Review

Locate formula-like CSV cells before a business shares an export with customers, finance or operations. Flag candidates for review; do not execute formulas, open a spreadsheet application or silently rewrite business data.

## Review the export

Ask for the CSV path and delimiter if it is not a comma. The bundled read-only scanner accepts UTF-8 with or without a BOM, up to 2 MiB. It also inspects header cells: an unsafe header is still a spreadsheet cell.

Run from this skill's directory, using a quoted path:

```sh
python scripts/scan_csv.py "path/to/export.csv"
python scripts/scan_csv.py "path/to/export.csv" --delimiter ";"
```

Interpret the JSON and exit code together:

- `0`, `no_candidates`: none of this scanner's indicators were found. This is not a safety certification.
- `1`, `review_required`: review each reported cell. A negative number or a literal `@handle` can be a legitimate value; a match does not establish an exploit.
- `2`, `error`: stop. State the input problem; do not describe a failed scan as clean.

`record` is one-based and includes the header as record 1 and any blank rows yielded by the CSV parser. `physical_end_line` is the last text line of the CSV record, so quoted multiline cells can span earlier lines. `column` is one-based. Values are deliberately omitted from the JSON to avoid copying customer data into logs. Empty, BOM-only and blank-line-only files return an error because no cells were inspected. For tab-delimited data, `--delimiter "\t"` is accepted.

The scanner flags `=`, `+`, `-`, `@` and their full-width forms at the start of a cell after leading ASCII space, tab, CR or LF, and flags a cell beginning with tab, CR or LF. CSV quoting alone is not a cross-application guarantee: the scan examines parsed cells rather than raw line prefixes.

## Deliver a useful decision

Report the file, delimiter, records and cells inspected, then list candidates by record/column and indicator. Explain which locations need business review and which cannot be interpreted without context. Do not print full cell values unless the user asks and the data is appropriate to display.

For a flagged export, recommend retaining the original and testing a separate copy using the recipient's actual import method, with affected columns explicitly imported as text. Whether quoting, an apostrophe prefix or another transformation preserves values and prevents formula interpretation depends on the application and import path; do not label a universally “sanitized” CSV or apply bulk changes without agreement. A spreadsheet format with explicitly typed text cells may be preferable when the export system supports it.

If the user wants repair, first agree on the target application, import method, columns and acceptable value changes. This skill reviews only; it does not send exports or perform the repair.

## Limits

No formula execution, malware detection, workbook inspection, encoding autodetection or coverage of every Unicode/control-character trick. A clean result is limited to these explicit indicators. It does not check external links, workbook macros, recipient settings or the truth of the data. Cell boundaries follow Python's CSV parser; a recipient's parser or import settings may differ. For other encodings or files larger than the limit, request a suitable export; do not silently sample or transcode it.

## Basis for the review

- [OWASP CSV Injection](https://community.owasp.org/attacks/CSV_Injection): indicator characters and application-dependent mitigation limits.
- [LibreOffice Text Import](https://help.libreoffice.org/latest/en-GB/text/shared/00/00000208.html): quoted-field, formula-evaluation and column-type import options. Test the recipient's actual application and settings rather than assuming these options apply everywhere.
