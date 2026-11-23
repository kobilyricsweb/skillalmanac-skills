# Unique customers and monthly revenue by plan

## Unique customers: 50
The sheet has 55 data rows, but 5 are duplicates. Matching on email (ignoring case and spaces): jon.hale9 (exact duplicate row), and DEV.JAIN3, rae.brooks17 (trailing space), Chloe.Evans28 and PIA.DIAZ41 (different capitalisation). So the unique count is 50.

## Monthly revenue by plan (current MRR, unique customers)
| Plan | Customers | Fee | Monthly revenue |
|---|---|---|---|
| Pro | 30 | $29 | $870 |
| Team | 7 | $79 | $553 |
| Basic | 13 | $9 | $117 |
| **Total** | **50** | | **$1,540** |

## Month by month (cumulative MRR by signup month)
The file has no cancellation or billing history, so this assumes everyone is still active and pays from their signup month.

| Month | Basic | Pro | Team | Total MRR |
|---|---|---|---|---|
| Jan | $9 | $116 | $79 | $204 |
| Feb | $27 | $232 | $158 | $417 |
| Mar | $36 | $406 | $158 | $600 |
| Apr | $45 | $406 | $237 | $688 |
| May | $63 | $435 | $316 | $814 |
| Jun | $72 | $493 | $316 | $881 |
| Jul | $72 | $551 | $474 | $1,097 |
| Aug | $90 | $696 | $474 | $1,260 |
| Sep | $99 | $783 | $474 | $1,356 |
| Oct | $117 | $870 | $553 | $1,540 |

## Cleaning notes
- Plan names normalised ("basic", "BASIC ", "PRO " etc.). Fees stored as text ("$29") converted; fees are consistent per plan (Basic 9, Pro 29, Team 79).
- The "Grand Total" row (1,453) was excluded; it does not match the data (1,715 if duplicates were counted, 1,540 after removing them).
- Signups run through 2026-10-21; the export is dated 2026-11-18, so November signups are not in the file.
