# Listing page content: founder-operating-kit

**One line:** Gives an agent a weekly operating cadence for early-stage founders, with burn and runway arithmetic and a review checker.

## What it does

The skill sets up five files: a monthly metrics CSV, a weekly review, a decision log, hiring scorecards and a monthly investor update, each with a template. A script computes gross and net burn, runway under three burn assumptions, month-over-month and 3-month compound growth, and flags months where the cash balance does not reconcile. A second command checks a weekly review file for missing sections, a missing north-star number, and decisions without a named owner or a valid due date. The formulas are stated in the skill and in the JSON output. The agent never recommends raising, cutting or hiring; it does arithmetic on the founder's own figures.

## Capabilities

- `scripts/founder_ops.py metrics <csv>`: strict JSON with burn, runway (last month, 3-month average, worst of 3), cash-zero month, growth, reconciliation gaps, flags, formulas
- `scripts/founder_ops.py review <md>`: strict JSON listing errors and warnings by code and line
- Templates: metrics sheet, weekly review, decision log, hiring scorecard, investor update
- A reference with metric definitions, a north-star selection test and a worked runway example

## When to use

A founder says weekly review, operating cadence, how many months of runway, burn rate, decision log, hiring scorecard or investor update, and has monthly figures in a file.

## When not to use

Fundraising strategy, valuation, tax, legal or accounting advice, full financial models (cohorts, scenarios, three statements), cap tables. Differences from neighbours: `meeting-notes-and-actions` (batch_01) turns a meeting into actions but has no metrics or runway arithmetic; `decision-evidence-ledger` (batch_03) records evidence for one decision, while this skill keeps an append-only log inside a weekly cadence; `spreadsheet-analysis` (batch_01) is general analysis, not a fixed contract.

## Requirements

Python 3.9 or newer, standard library only. Network: none. Tested: Windows 11, Python 3.11 (see VERIFICATION.md).

## Install

Not yet published. Copy the folder to `.claude/skills/founder-operating-kit/` or `.agents/skills/founder-operating-kit/`.

## Examples

**1. Runway from a CSV.** Prompt: "Here is our monthly cash CSV. How many months of runway do we have?" Real output of `python scripts/founder_ops.py metrics evals/files/t1-runway/monthly.csv` (abridged):

```
"burn": {"net_burn_latest": 42800.0, "net_burn_avg_last_3": 43433.33, "net_burn_worst_of_last_3": 44500.0},
"runway_months": {"last_month": 0.83, "avg_last_3": 0.82, "worst_of_last_3": 0.8},
"cash_zero_month_at_avg_burn": "2026-11",
"growth": {"mom_latest": 0.1, "cmgr_3m": 0.1362},
"flags": ["runway_under_6_months"]
```

**2. Review check.** Prompt: "Finish this week's review so it passes." Real output of `python scripts/founder_ops.py review evals/fixtures/team_owner_review.md`: `ok: false`, error codes `north_star_missing`, `decision_no_owner` ("the team" is not a person), `decision_bad_due` ("next Friday"), `decision_no_due`; warning `too_many_priorities` (4 listed, limit 3). The agent then asks the founder for these values instead of inventing them.

## Limits

Arithmetic only, not financial or legal advice, no forecasting. Cash basis. Runway assumes flat burn. The 6-month flag and 3-month window are working values. The review check tests structure, not quality. A scorecard does not remove bias.

## Evidence

Script fixtures: 9 of 9 cases pass (Windows 11, Python 3.11, 2026-11-21). Trigger tests, with-and-without evals, cross-tool runs and human review have not been run. See VERIFICATION.md.

## Demo script (60 to 90 seconds)

1. Founder: "Run my Monday review." Agent runs the metrics command on the CSV.
2. Agent shows runway 0.82 months, range 0.80 to 0.83, net burn 43,433, with the formula, and no advice.
3. Agent asks for the north-star number and the decisions; the founder dictates two.
4. Agent writes the review, runs the check, fixes a missing due date, re-runs: ok true. Decisions go to the log.

## FAQ seeds

- Does it need network? No.
- Does it tell me whether to raise money? No; it computes runway and stops.
- Can it send the investor update? No; it drafts, you send.
- Why three runway numbers? One lumpy month should not hide the range.
- What if I raised money this month? The reconciliation warning fires; note it in the review, leave revenue alone.
- Does it work in tool X? Only Windows with Python 3.11 was run so far.
- How do I uninstall? Delete the folder.

## Changelog

0.1.0, 2026-11-21: first draft, script fixtures only.

## License and authorship

Apache-2.0, Copyright 2026 Global Media Holdings (skillalmanac.com). Drafted by claude-sonnet-5-5; accountable publisher Global Media Holdings. No human review has taken place yet.
