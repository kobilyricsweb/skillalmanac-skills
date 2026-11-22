## Comparison procedure

Purpose: put two or more deals side by side so differences in inputs are visible, without ranking them.

1. **Prepare each deal first.** Each deal has its own `deal.json` that has been checked with `check`. A deal with an `error` flag is fixed or left out of the table; say which.
2. **Like-for-like test.** Run `python scripts/deal_check.py compare a.json b.json ...`. Read `table_flags`:
   - `CURRENCY_MIXED` (error): stop. Do not convert currencies on your own. Ask the user for one currency and the rate and date they accept, and record both.
   - `AS_OF_SPREAD` (warn): figures are more than 30 days apart. Either refresh the older deal or print the dates as a column and say the rows are not same-date.
   - `AREA_UNIT_MIXED` (warn): do not show any per-area figure across units without converting by hand and noting the factor.
   - `CELL_NOT_COMPUTED` (warn): leave the cell as "not computed" and list the missing input under the table.
3. **Fixed columns, in this order:** address, as_of, purchase price, gross yield, cap rate, cash-on-cash, DSCR, error count, warning count, open due-diligence items. Add user-requested input columns (units, area, year built) after them. Do not add a "score", "rank", "best" or colour for better or worse.
4. **Row order** is the order the user listed the deals. Do not sort by any metric unless the user asks for a sort by a named column, and then state "sorted by cap rate, descending; ordering is not a recommendation".
5. **Notes under the table**, one line per row, limited to: inputs that differ in kind (a cash purchase versus a financed one, an owner-paid utility), flags still open, and the as_of date. No adjectives about quality.
6. **Cash purchases and zero debt service.** DSCR is not computed when debt service is 0, and cash-on-cash then equals NOI over cash invested. Mark these rows so a reader does not compare them with financed rows unaware.
7. **Close with:** the arithmetic line from SKILL.md, and one sentence listing what a licensed professional should verify before any decision (the source documents behind each row, the financing terms, local taxes and rules).

Example shape:

| Address | As of | Price | Gross yield | Cap rate | Cash-on-cash | DSCR | Errors | Warnings | Open DD |
|---|---|---|---|---|---|---|---|---|---|
| 14 Alder Court | 2026-11-01 | 400,000 | 0.0900 | 0.0585 | 0.0151 | 1.0841 | 0 | 0 | 2 |
| 27 Birch Row | 2026-10-25 | 310,000 | 0.0871 | 0.0512 | -0.0503 | 0.8227 | 0 | 0 | 1 |

Negative cash-on-cash and DSCR below 1 are displayed as numbers with their formulas. They are not described as good or bad here.
