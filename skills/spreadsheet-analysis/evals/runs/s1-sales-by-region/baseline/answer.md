# Q3 2026 sales by region

| Region | Total sales | Orders |
|---|---|---|
| North | $24,700 | 10 |
| South | $22,575 | 10 |
| East | $17,275 | 9 |
| West | $13,550 | 6 |
| **All regions** | **$78,100** | **35 priced (36 unique orders)** |

**North was the biggest region**, about $2,125 ahead of South.

Cleaning applied:
- Region names normalised ("north ", "NORTH", " North" counted as North).
- Amounts like "$2,725.00" converted to numbers.
- Duplicate rows removed: SO-1009 ($325, North) and SO-1023 ($3,175, East) each appear twice; counted once.
- SO-1013 (North, Devon, 2026-09-07) has no amount, so it is counted as 0. North's true total is higher, so the ranking cannot change.
- The file's own "Total" row ($66,925) is not used; it does not match the data (it appears to skip the amounts stored as text and does not remove duplicates).

If you do not remove duplicates, North is $25,025, East $20,450 and the order is unchanged.
