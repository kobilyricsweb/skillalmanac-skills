## Contents

- Nested IF
- INDIRECT and OFFSET
- Lookups
- Magic numbers
- Breaking a circular reference
- Whole-column references
- Fill-down and anchoring
- Errors: guard or fix

# Rewrite recipes

Read only the section that matches the finding. Each recipe says when it applies and what it costs.

## Nested IF

Depth 4 or more.

| Situation | Rewrite | Needs |
|---|---|---|
| Bands on one number (grade, tax tier) | A small table of lower bounds with `XLOOKUP(x,bounds,labels,,-1)`, or `LOOKUP(x,bounds,labels)` with bounds sorted ascending | LOOKUP works everywhere; XLOOKUP needs a newer version |
| Equality tests against one cell | `SWITCH(x,"a",1,"b",2,0)` | Excel 2019 and later |
| Several independent conditions | `IFS(c1,r1,c2,r2,TRUE,default)` | Excel 2019 and later |
| Older versions must open the file | Helper columns, one test per column, or `CHOOSE(MATCH(...),...)` | Any |
Put the thresholds in cells, not in the formula, so a rate change is one edit.

## INDIRECT and OFFSET

Both are volatile and hide their dependencies.

- `OFFSET(A1,n,0)` with a fixed shape becomes `INDEX(A:A,1+n)` (or `INDEX(A1:A100,n+1)`). INDEX is not volatile.
- A moving range `SUM(OFFSET(A1,0,0,n,1))` becomes `SUM(A1:INDEX(A:A,n))`.
- `INDIRECT("Sheet"&n&"!A1")` to pick a sheet: replace with CHOOSE over direct references, or consolidate the sheets into one table and use SUMIFS. Keep INDIRECT only when the sheet name truly comes from user input, and say what depends on it.

## Lookups

- Default to exact match. VLOOKUP: fourth argument `FALSE` or `0`. MATCH: third argument `0`.
- Left-looking lookup: `INDEX(ret,MATCH(key,keycol,0))` works in every version; XLOOKUP is shorter but newer.
- A key with stray spaces: `TRIM` and `SUBSTITUTE(x,CHAR(160)," ")` on both sides, in a helper column, not inside every lookup.
- Several criteria: `SUMIFS` for numbers; for text results, a helper key column `=A2&"|"&B2`.
- Use `IFERROR(lookup,"not found")` only on a lookup whose missing key is an expected case, and use `IFNA` when only #N/A should be caught, so other errors stay visible.

## Magic numbers

A constant inside a formula (`*1.17`, `>500`) hides a business rule. Move it to a labelled input cell, anchor it (`$B$1`) or give it a name, and refer to it. Leave 0, 1, 2 and 100 alone when they are structural. When the same constant appears in many formulas, change them all in one pass and re-run the audit to confirm none remain.

## Breaking a circular reference

First find the path (`circular_reference.path`). Then choose:

1. **Total includes itself** (`=SUM(B2:B10)` placed in B10): shrink the range to B2:B9.
2. **Two cells feed each other** (price from cost, cost from price): decide which is the input and type it; compute the other.
3. **Running balance** that reads its own previous result in the same cell: move the previous value to its own column or row.
4. **Intended iteration** (interest on an average balance): keep, but turn Iterative calculation on knowingly, set a maximum change (for example 0.001) and a cap of iterations, and document it in a visible note. Warn the user that Excel then stops flagging accidental loops.
Do not "fix" a loop by wrapping it in IFERROR; the result is still circular.

## Whole-column references

`SUM(A:A)` is fine and fast. Whole-column references inside array formulas, SUMPRODUCT, or many volatile formulas multiply the work; use a bounded range or a Table column. A whole-column reference that includes the formula's own column is a circular reference.

## Fill-down and anchoring

A fill-down shifts every reference without `$`. Anchor what must not move: the rate cell (`$B$1`), the lookup table (`$F$2:$G$20`), the header row of a two-way lookup (`B$1`). Check the first and the last filled cell, not only the first. A mixed pair such as `$A2` locks the column and lets the row move.

## Errors: guard or fix

Fix the cause when the error means bad input or a broken reference. Guard only when a missing result is a normal state, and then return something visible ("" or "n/a"), never 0 that a SUM would count.
