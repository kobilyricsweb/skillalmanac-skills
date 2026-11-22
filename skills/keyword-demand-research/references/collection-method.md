# Collecting keyword data from the user's own API account

Read this before writing collection code. It applies to any paid keyword-data API. Endpoint names differ by provider; the method does not.

## Before the first paid call

1. **Credentials.** Read them at run time from an environment variable or a config file the user names. Never print them, never put them in the script, a log, a saved response or the report. If the user pastes a key into the chat, tell them to rotate it and move it to their environment.
2. **Balance and price list.** Call the provider's free account endpoint. Record the balance and the unit price of each endpoint to be used.
3. **Spend cap.** Agree a cap with the user. Default when they give none: the lower of a fixed amount they name and 50% of the current balance. The collection code checks the running total before every paid call and stops at the cap.
4. **Dry cost estimate.** Calls x unit price, per round. Show it and get a yes before spending.

## Collection rules

- **Save every raw response** to a file named after the call, before parsing. Re-runs read the saved file instead of paying again.
- **Keep a ledger**: one line per call with time, endpoint, file name, cost and status. The report's spend figure is the sum of this ledger and is checked against the balance difference.
- **Retry transient errors** (rate limit, server error, a payment error while the balance is positive) a few times with a pause. Keep failed responses under a different file name; do not parse them.
- **Record what each number means**: the endpoint, the location and language parameters, the date range, and whether the provider buckets or models the value.

## Rounds

| Round | What to pull | Why |
|---|---|---|
| 1 | Suggestions for 20 to 50 seeds: the head term, its singular and plural, the product names, the user's own phrasing | The core of the list |
| 2 | Next pages for seeds that hit the page limit; modifier seeds (best, vs, how to, price, near me, for X); related-keyword and keyword-idea endpoints for the heads | Width |
| 3 | Bare ambiguous heads filtered by a pattern that keeps only the intended meaning; the ranking keywords of the main competitor sites | What seeds cannot reach |
| Volume pass | Authoritative monthly volumes for the kept list, in the target market, with at least 13 months (15 if a year-on-year three-month window is wanted) | One consistent source for the totals |

## When to stop

After each round, count the keywords first seen in that round and their volume. Stop when a round's new volume is mostly close variants of terms already held, or under about 15% of what the list already holds. Write the per-round numbers in the report; they are the evidence that the list is saturated. The list is still a lower bound.

## Classification pass

1. Write word rules (regular expressions) for each group: the target meaning, brand-navigational, adjacent topics, other meanings to drop.
2. Run the rules, then read the top few hundred keywords by volume and fix the rules.
3. Keep an "ambiguous" group for keywords that probably belong but cannot be proven from the text, and report it separately.
4. Keywords the volume endpoint rejects (odd characters) or returns empty are counted and listed under "not obtained".

## Cross-checks worth their cost

- A second volume source (for example a clickstream model) on the top 100 only, shown next to the first where they differ.
- A live results page for the 20 to 30 largest heads: who ranks, whether an AI answer block appears.
- Keyword difficulty from the provider, named as that provider's metric.
