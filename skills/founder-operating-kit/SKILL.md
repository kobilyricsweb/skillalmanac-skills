---
name: founder-operating-kit
description: Runs an early-stage founder's weekly operating cadence from files, with a metrics-sheet contract, a weekly review, a decision log with owners and dates, a hiring scorecard, an investor update, and a script that computes burn, runway and growth from a monthly CSV and checks a review file, in strict JSON. Use when a founder says weekly review, operating cadence, how many months of runway, burn rate, decision log, hiring scorecard, or investor update. Do not use for fundraising strategy, valuation, tax, legal or accounting advice, or full financial models.
license: Apache-2.0
compatibility: The script needs Python 3.9 or newer, standard library only. No network access is used. Without Python, use the formulas in this file by hand.
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  author_model: claude-sonnet-5-5
  version: "0.1.0"
  network: none
---

# Founder operating kit

A weekly cadence for a team of 1 to 15: one metrics sheet, one review file per week, one decision log, one monthly investor update. The agent does the arithmetic and the bookkeeping; the founder makes every decision. Figures come only from the founder's files: never estimate, never fill a missing number, never say what the founder should raise, spend or pay.

## Files the cadence uses

| File | Template | Rule |
|---|---|---|
| `metrics/monthly.csv` | `assets/metrics_sheet.csv` | one row per month, oldest first, no gaps |
| `reviews/YYYY-MM-DD.md` | `assets/weekly_review.md` | named for the Monday of the week |
| `decisions.md` | `assets/decision_log.md` | append-only |
| `hiring/<role>-<candidate-id>.md` | `assets/hiring_scorecard.md` | one per interviewer per candidate |
| `investors/YYYY-MM.md` | `assets/investor_update.md` | sent only by the founder |

Copy a template only when the file does not exist yet. Read [references/definitions.md](references/definitions.md) before choosing the north star or writing any number into an update; it holds the definitions the checks assume.

## Metrics sheet contract

Input CSV, UTF-8, header exactly `month,revenue,cash_out,cash_balance`. `month` is YYYY-MM. `revenue` is cash received from customers in the month. `cash_out` is all cash paid out in the month, as a positive number. `cash_balance` is the bank balance at month end. One currency, plain numbers. Output is the JSON printed by the script (below). The north star is one number, defined in one sentence, recorded in the review's Metrics section as `North star: <name> = <number>`; changing its definition is a decision-log entry.

## Weekly review procedure (30 minutes)

```
- [ ] 1 Update monthly.csv if a month closed; run the metrics command
- [ ] 2 Create reviews/<Monday>.md from the template
- [ ] 3 Fill Metrics from the JSON, never from memory
- [ ] 4 List Wins, Misses (max 3 each), Risks
- [ ] 5 Write every decision as: - <verb first> | owner: <person> | due: YYYY-MM-DD
- [ ] 6 Pick at most 3 priorities for next week
- [ ] 7 Run the review check; fix until ok is true
- [ ] 8 Append each decision to decisions.md
- [ ] 9 Report
```

1. Run `python scripts/founder_ops.py metrics metrics/monthly.csv`. If `ok` is false, fix the listed lines with the founder; do not guess a value. Treat each `warnings` entry as a question to ask.
2. Ask the founder for what the files cannot give: the north star number, wins, misses, decisions made. A decision is something the founder says was decided. Do not invent decisions from notes.
3. An owner is one named person, not "team" or "TBD". A due date is a calendar date on or after the Monday of the week.
4. Run `python scripts/founder_ops.py review reviews/<Monday>.md`. Fix every entry in `errors`; mention each entry in `warnings`.
5. Report in this shape: `Runway: x.x months (avg of last 3) | Net burn | Growth | Decisions logged: n | Review check: ok | Open questions for the founder | Not checked`.

## Arithmetic (state these formulas whenever you quote a figure)

- Gross burn = cash_out in the month. Net burn = cash_out minus revenue.
- Runway (months) = latest cash_balance divided by net burn. Quote three: last month, average of last 3 months, worst of last 3. Lead with the average and show the range. If net burn is zero or negative, runway is undefined: say "cash-flow positive over the window".
- Month-over-month growth = revenue this month divided by revenue last month, minus 1. Three-month compound growth = (revenue now / revenue 3 months ago) to the power 1/3, minus 1.
- The script flags runway under 6 months and any month where the balance differs from the prior balance minus net burn by more than 1% of the prior balance. A flagged gap is a question (funding, loan, data error), never a conclusion.
- Say what the numbers are, not what to do. Never recommend raising, cutting, hiring or pricing; show the arithmetic of an option only if asked, labelled as arithmetic.

## Hiring scorecard

Use `assets/hiring_scorecard.md`. Fix criteria and weights (sum 100) before the first interview, score 1 to 4 against the written anchors, and require evidence text for every score. Criteria must be job-related; refuse criteria about protected characteristics, age, family plans, health or nationality, and say why. Compute the weighted score (sum of weight x score / 100) and show the arithmetic. Interviewers score before seeing each other's cards. A scorecard supports a human decision; it does not make one.

## Investor update

Use `assets/investor_update.md`, monthly, within 10 days of month end. Every number must be traceable to the metrics sheet or a named source; mark unaudited figures as management figures. Misses are mandatory. Forward-looking statements are intentions with a date, never a forecast of revenue or valuation. Give the draft to the founder; never send it.

## Script

`scripts/founder_ops.py` (run it, do not edit it to make a check pass):

- `metrics <csv>` prints JSON with keys `ok, errors, warnings, burn, runway_months, cash_zero_month_at_avg_burn, growth, flags, reconciliation_gaps, formulas`. Input error codes: `missing_columns, bad_month, bad_number, negative_value, duplicate_month, not_sorted, month_gap, no_rows`.
- `review <md>` prints JSON with keys `ok, errors, warnings, sections_found, decisions_counted`. Error codes: `missing_section, empty_section, week_missing, bad_week_date, north_star_missing, decisions_not_listed, decision_no_owner, decision_no_due, decision_bad_due, decision_due_before_week`. Required sections: Metrics, Wins, Misses, Decisions, Risks, Priorities (`Next week priorities` also accepted).
- Exit 0 ok, 1 problems listed in the JSON, 2 unreadable file. Output is strict JSON.

If Python is unavailable, compute the formulas above by hand, show each step, and check the review manually against the required sections and the decision pattern.

## Limits

- Arithmetic only. It is not financial, tax, legal, accounting or investment advice, and it does not forecast.
- Runway assumes burn stays at the stated level; real burn changes with hiring, revenue and one-off payments. The 6-month flag and the 3-month window are working values, not measured optima.
- Cash basis only: no accruals, deferred revenue, debt schedules or currency conversion.
- The review check tests structure, owners and dates, not whether decisions are good or the north star is the right one.
- A scorecard cannot remove bias; it only makes the evidence visible.
