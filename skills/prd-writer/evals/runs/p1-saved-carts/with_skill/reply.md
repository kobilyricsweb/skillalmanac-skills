I turned the notes into a PRD: prd.md in this folder. It is mostly decided on scope (logged-in users, web plus iOS, merge keeping the higher quantity) and open on several points the team still has to settle.

Decisions needed before build:
- Retention, 30 days (Leo) or 90 days (loyalty team via Marta). The call did not settle it, and no decider is named in the notes.
- Reminder emails in version one: the loyalty team says yes, Hana says no. No decider named.
- What "for the holidays" means as a date. The notes contain no date, so I wrote none.
- What happens to an item whose price changed or that is out of stock (Dev proposed an inline notice, Marta said it must be decided).

Marked as proposed or assumed: 2 lines. R6 (Dev's notice, [proposed]) and one assumption about the 23% baseline.

Left out on purpose: guest carts (Marta's constraint), the Android app, and reminder emails (the notes disagree, so they are neither a requirement nor a non-goal). Success targets are [needs data] because nobody named a number.

Check: PASS (prd_check.py with notes.md).
