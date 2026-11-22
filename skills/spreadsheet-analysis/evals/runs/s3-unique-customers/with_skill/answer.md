Answer: you have 50 unique customers, and monthly recurring revenue is 1,540 per month.

| Plan | Customers | Monthly revenue |
|---|---|---|
| Pro | 30 | 870 |
| Team | 7 | 553 |
| Basic | 13 | 117 |
| Total | 50 | 1,540 |

"Monthly revenue by plan" is read as the sum of the Monthly fee column for each plan, one row per customer. The file has no billing history by month, so I cannot give revenue month by month. If you meant that, I need a payments table. Fees by plan are Basic 9, Pro 29, Team 79.

How the data was treated:
- The file has 55 customer rows. Row 57 ("Grand Total", 1,453) is a total row and was left out of every figure.
- Customers are identified by Email, compared after trimming spaces and ignoring case. 5 customers appear twice, 55 rows becoming 50 customers:
  - dev.jain3@example.com: rows 5 and 53 (the second is in capitals)
  - jon.hale9@example.com: rows 11 and 27 (exact duplicate)
  - rae.brooks17@example.com: rows 19 and 54 (the second has a trailing space)
  - chloe.evans28@example.com: rows 31 and 55 (different capitalisation)
  - pia.diaz41@example.com: rows 44 and 56 (the second is in capitals)
  In every case the name, plan, signup date and fee are identical, so the first row of each was kept and the repeat dropped. Nothing needed a judgement call about which version is current.
- Plan has spelling variants ("Pro" / "PRO ", "basic" / "Basic" / "BASIC "). They were merged into Basic, Pro and Team.
- 8 fees are stored as text (for example "$29" in rows 4, 10, 22, 29, 35, 41 and "$9" in row 16, "$79" in row 47). They were read as numbers.
- No blank fees. All signup dates are year-first (YYYY-MM-DD), so no date ambiguity.
- The "Notes" sheet only says "Exported from billing on 2026-11-18". It has no data.

Problems to fix in the file:
- Raw Email count is 54 distinct as typed, 53 if only exact duplicate rows are removed, and 50 after ignoring case and spaces. 50 is the real number.
- Rows 27 and 54 are exact or near-exact duplicates, and rows 53, 55 and 56 are repeat entries that differ only by capitals. Rows 27, 53, 54, 55 and 56 overstate revenue by 87 in Pro (rows 53, 55, 56) plus 9 in Basic (row 54) plus 79 in Team (row 27), 175 in total.
- The file's own Grand Total of 1,453 is wrong in two ways. It skips the 8 text fees (262) and still counts the 5 repeat rows. Raw sum 1,715 minus 262 gives exactly 1,453.
- Mixed text and number fees mean a plain SUM undercounts. Plan names with stray capitals or spaces split any pivot table.

Figure both ways (duplicate handling):

| Basis | Customers | Basic | Pro | Team | Total |
|---|---|---|---|---|---|
| One row per customer, used | 50 | 117 | 870 | 553 | 1,540 |
| Only exact duplicate rows removed (2 rows) | 53 | 117 | 957 | 553 | 1,627 |
| Nothing removed | 55 | 126 | 957 | 632 | 1,715 |

The middle row is shown only for comparison. Because the extra rows are the same person with different capitals or spaces, 50 is the right customer count.

Not checked: whether any customer is cancelled or inactive (the file has no status column, so all 50 are counted as current), whether the fees match your price list, and near-duplicates that differ by a typo in the email.
