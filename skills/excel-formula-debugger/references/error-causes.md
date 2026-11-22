## Contents

- Reading an error value
- Causes in the order to test them
- Silent wrong numbers (no error shown)
- Calculation settings that fool you
- Sources

# Error causes and tests

Use this when the script cannot run, or when a finding needs a deeper look. Read only the block for the error in front of you.

## Reading an error value

An error spreads: every formula that reads an error cell shows an error too. The cell to fix is the first one in the chain, whose own inputs are all clean. Click the error cell, use Formulas > Trace Precedents, and walk back until a cell has no error among its inputs.

## Causes in the order to test them

### #DIV/0!
1. The divisor refers to an empty cell (empty counts as zero).
2. The divisor is a formula that returns 0 for the first rows of data (a running average divided by a count that starts at zero).
3. The divisor is text that cannot be read as a number (such as "-"): that gives #VALUE!, not #DIV/0!. Text that looks like zero ("0") is converted and gives #DIV/0!.
Fix the source. Guard with `IF(B2=0,"",A2/B2)` only when "no answer" is a legitimate result for that row.

### #N/A
1. Exact match asked, key truly absent: confirm in the source list.
2. Key has a trailing or non-breaking space: `=LEN(A2)` against what you see; `CHAR(160)` survives TRIM, so use `SUBSTITUTE(A2,CHAR(160)," ")` first.
3. Number in one list, text in the other: left-aligned digits, or `=ISTEXT(A2)`.
4. Lookup range does not start at the key column (VLOOKUP looks only at the first column of the range).
5. Range moved down by one row when the formula was filled without `$` anchors.
6. The formula contains `NA()` on purpose, for charts that skip points.

### #NAME?
1. Function misspelled, or name typed without a defined target.
2. Text not in double quotes, or smart quotes pasted from a web page or document instead of straight quotes.
3. Range typed with a missing colon, such as `A1A5`.
4. The workbook was saved by a newer version: functions stored with an `_xlfn.` prefix in the file (XLOOKUP, FILTER, LET, TEXTSPLIT and others) show #NAME? in older versions.
5. A function that exists only in another app (Excel and Google Sheets each have functions the other lacks).

### #REF!
1. A row, column or sheet used by the formula was deleted: the formula text itself contains `#REF!`.
2. VLOOKUP column index larger than the number of columns in the range.
3. A formula copied to a place where its relative reference would fall off the sheet.
4. A reference to a closed workbook that moved.
Rebuild the reference; undo the deletion first if it was recent.

### #VALUE!
1. Arithmetic on text (a cell holding "n/a" or "12 kg").
2. A range given where one value is expected, in a version without dynamic arrays.
3. A date stored as text: `=ISNUMBER(A2)` is FALSE.
4. TEXT or DATEVALUE given a format the user's locale does not use.
5. Array formula needing Ctrl+Shift+Enter in a version before dynamic arrays.

### #NUM!
Invalid number for the function (square root of a negative, a result beyond about 1E+308, a date before 1900), or an iterative function (IRR, RATE) that did not converge: give it a guess argument.

### #NULL!
A space between two references is the intersection operator. If the ranges do not overlap it fails. A comma or colon was meant.

### #SPILL!
A dynamic array formula needs empty cells below or beside it and cannot spill into merged cells or inside a table. Clear the blocking cells, or move the formula.

## Silent wrong numbers (no error shown)

| Cause | How to see it |
|---|---|
| Number stored as text | Left-aligned, green corner, `=ISTEXT(cell)` |
| Typed number over a formula | `inconsistent_formula` or `hardcoded_value_in_formula_column`; F2 on the cell shows no `=` |
| Range stops one row short | Compare the range end with the last data row; use a Table or a range that includes a spare row |
| SUM includes its own subtotals | Subtotals inside the range double-count; use SUBTOTAL(9,...) or exclude them |
| Rounding shown, not stored | Format shows 2 decimals but the cell holds more; sums look 0.01 off |
| Approximate-match lookup | VLOOKUP and HLOOKUP default to approximate; needs sorted keys, otherwise returns a wrong neighbour |
| Hidden or filtered rows | SUM counts hidden rows; SUBTOTAL(109,...) skips manually hidden ones |
| Dates as text or wrong locale | Day and month swapped when the text was converted |
| Floating-point residue | `=0.1+0.2-0.3` is not exactly zero; compare with ROUND |

## Calculation settings that fool you

- Calculation mode Manual: results stay frozen until F9. Check Formulas > Calculation Options.
- Iterative calculation on: a circular reference stops warning and settles on a number. The script reports `iterative_calculation` for this reason.
- "Precision as displayed" on: stored values are permanently rounded to the displayed format.
- 1904 date system: dates differ by 1,462 days between workbooks.

## Sources

Facts here are general spreadsheet behaviour, restated in original words. Not re-fetched in the authoring session; confirm before quoting a version number.

- Excel recalculation and volatile functions: https://learn.microsoft.com/en-us/office/client-developer/excel/excel-recalculation
- Open file format specification (formula and cell storage): https://ecma-international.org/publications-and-standards/standards/ecma-376/
