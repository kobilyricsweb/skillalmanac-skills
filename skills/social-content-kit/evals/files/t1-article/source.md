# What we learned timing 40 invoice runs

Published 24 November 2026 by the Harbor Ledger finance team. Full write-up: https://harborledger.example/invoice-timing

For six weeks in the autumn we timed every month-end invoice run in our own accounts team. There were 40 runs in total, across 4 people. The median close time before we changed anything was 52 minutes. After we removed one manual approval step, the median fell to 31 minutes.

The slow step was a spreadsheet export that someone had to email to a second person. It cost 21 minutes on average and nobody had noticed because it was always done "while doing something else".

We made three mistakes while measuring. First, we timed from the moment the run started, not from the moment the invoices were ready, which skewed the baseline by about 6 minutes. Second, we included 3 runs that were interrupted by a system outage and discarded them only later. Third, we asked people to time themselves, which meant the fast ones forgot to start the clock.

"The number that surprised us was not the 21 minutes. It was that four people had all assumed somebody else owned that step," said finance lead Dana Okafor.

We are not claiming the 31-minute figure will hold for other teams. Our runs are small, with a median of 180 invoices. We plan to repeat the test in the first quarter of 2027 with a second team.
