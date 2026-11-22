Answer: spend per category so far this year (file runs 2026-01-08 to 2026-10-20), 37 amounts counted, extreme row kept:

| Category | Total spent | Entries counted |
|---|---|---|
| Office | 46,344.85 | 9 |
| Marketing | 6,085.00 | 7 |
| Travel | 2,966.90 | 7 |
| Software | 2,577.00 | 14 |
| All categories | 57,973.75 | 37 |

Office is inflated by one entry, 45,000 on 2026-04-16 (DeskDepot, file row 17), which looks like a typo. Without it Office is 1,344.85 and the overall total is 12,973.75. See "Figure both ways" below.

How the data was treated:
- Rows 14 and 27 ("Subtotal Q1" 5,121.20 and "Subtotal Q2" 47,397.30) are subtotal rows. They were left out of every figure and used only to reconcile.
- "Software" appears three ways: "Software", "software" (row 7) and "Software " (row 16). These were merged into one category.
- 4 amounts are stored as text and were read as numbers: "1,250.00" (row 5), "(120.00)" (row 19, read as -120, a refund), "1,100.00" (row 24) and "1,300.00" (row 41). A plain spreadsheet SUM skips these.
- Row 25 (Travel, Hotel Meridian, 2026-06-18, note "receipt missing") has a blank amount. It was left out, not treated as zero, so Travel is a floor.
- Dates come in two formats (YYYY-MM-DD and "Mon D, YYYY"), but both are unambiguous because months are named or year-first. I did not need to group by month.
- No exact duplicate rows.
- The 2026 total includes the -120 refund. Refunds were not excluded.

Problems to fix in the file (odd things flagged):
1. Row 17: Office 45,000 against a typical range of about 70 to 520. It is probably a typo (450 or 4,500). It is 78% of the overall total.
2. Row 25: blank amount with "receipt missing". Spend is understated by whatever that stay cost.
3. Rows 14 and 27: subtotals mixed into the data rows. Any SUM of the Amount column will double-count them. Q1 reconciles exactly (5,121.20). Q2 reconciles exactly (47,397.30) only because it includes the 45,000 and treats the blank as zero, so the Q2 subtotal carries the same possible typo.
4. Row 19: Software refund of -120 noted "refund for double charge". The regular Docubox charge is 240, so the refund is only half a charge, and I could not find a visible double charge in the file. Worth checking.
5. Spelling variants of Software (rows 7 and 16) and 4 text-formatted amounts (rows 5, 19, 24, 41), as described above.
6. Mixed date formats (6 rows use "Mon D, YYYY"). Harmless here, but they will sort and filter badly.

Figure both ways (extreme value):

| Category | With row 17 (used) | Without row 17 |
|---|---|---|
| Office | 46,344.85 | 1,344.85 |
| Marketing | 6,085.00 | 6,085.00 |
| Travel | 2,966.90 | 2,966.90 |
| Software | 2,577.00 | 2,577.00 |
| All | 57,973.75 | 12,973.75 |

Was the Office entry meant to be 45,000? If it was a typo, tell me the right value and I will update the figures.

Not checked: whether any amount is true, near-duplicates that differ by a typo, and what the Hotel Meridian amount in row 25 should be.
