# Real estate deal notes

**One-line summary:** Organises a property deal file and computes stated formulas, with checks for missing, inconsistent and stale inputs, and never a recommendation.

## What it does

The skill gives an agent a fixed deal-notes contract: a `deal.json` with required fields, fixed units (annual money, rates as fractions, sqft or sqm) and a sourced, dated input for every key figure, plus a human notes file. A standard-library script computes gross yield, effective gross income, NOI, cap rate, debt service, cash flow before tax, cash-on-cash and DSCR from the stated formulas, and flags what is missing, inconsistent or stale. A due-diligence checklist assigns an owner and a date to each item, and a comparison procedure builds a side-by-side table without ranking. Every computed answer carries an "arithmetic, not advice; verify with a licensed professional" line.

## Capabilities

- `deal.json` and `deal_notes.md` templates; facts table with source, date and "seen or reported"
- `deal_check.py check`: nine metrics with their formulas, `not_computed` with the missing inputs, flags with severity, due-diligence counts, strict JSON
- `deal_check.py compare`: fixed-column table, currency, area-unit and date-spread guards, no ranking
- Flag table: unit slips (rate 6.5 instead of 0.065), expenses above income with no note, financing that does not add up, zero vacancy with no basis, figures older than 90 days, sources older than 180 days, overdue or ownerless checklist items

## When to use / when not to

Use for: turning an agent email, rent roll or seller statement into an organised deal file; computing the standard rental metrics with the formulas shown; building a due-diligence list with owner and date; comparing properties side by side.

Do not use for: whether to buy, sell, offer or refinance; valuation or rent estimates; market forecasts; tax, legal, lending or insurance guidance; listing copy; leases. Those need a licensed professional or a different skill.

How it differs from neighbours in this catalogue: `decision-evidence-ledger` records any decision and its evidence; this skill is specific to property inputs, units and formulas. `dataset-field-profiler` profiles generic data; this one validates a fixed deal contract.

## Requirements

Python 3.9 or newer, standard library only. No network. Tools tested: none yet beyond the script fixtures (see Evidence).

## Install

Copy the folder to `.claude/skills/real-estate-deal-notes/` or `.agents/skills/real-estate-deal-notes/`. Release pinning is not set up yet.

## Examples

**Prompt:** "Check deal.json for the duplex on Alder Court. Today is 2026-11-21."
**Command:** `python scripts/deal_check.py check evals/fixtures/good_deal.json --today 2026-11-21`
**Output (real fixture run, abridged):** status `ok`; gross_yield 0.09; effective_gross_income 35400.0; net_operating_income 23400.0; cap_rate 0.0585; total_cash_invested 120000; annual_debt_service 21583.82; cash_flow_before_tax 1816.18; cash_on_cash 0.0151; dscr 1.0841; flags none.

**Prompt:** "Run the numbers on the fourplex file."
**Command:** `python scripts/deal_check.py check evals/fixtures/bad_deal.json --today 2026-11-21`
**Output (real fixture run, abridged):** status `input_errors`, exit 1. Errors: `BAD_CURRENCY` (usd), `MISSING_FIELD` (operating expenses), `RATE_NOT_FRACTION` (6.5). Warnings include `STALE_AS_OF` (173 days), `VACANCY_ZERO`, `FINANCING_MISMATCH` (440,000 against 520,000), `DD_OVERDUE`, `DD_NO_OWNER`. Cap rate, DSCR and cash-on-cash are listed under `not_computed` with the inputs that are missing. Nothing is estimated.

## Limits

- Checks consistency, units and dates; cannot verify that a rent, price or expense is true.
- Thresholds are working values to catch input slips, not statements about normal properties.
- Debt service assumes a level-payment, fully amortising loan unless the lender's figure is supplied.
- Taxes, depreciation, reserves, management fees and appreciation are outside the formulas unless included in stated expenses.
- Not a licensed professional and not a substitute for one.

## Evidence

Script fixtures: 9 of 9 cases pass (see `VERIFICATION.md`). Not run: with-skill against baseline, trigger tests, any other tool, human review. Treat as a draft.

## Demo script (60 to 90 seconds)

1. Prompt: paste the agent email for 22 Cedar Lane and ask for a deal file.
2. The agent fills `deal.json`, converts $1,450 and $1,350 a month to 33,600 a year, and records sources and dates.
3. It runs the check: the numbers appear with their formulas; `VACANCY_ZERO` is raised because the seller's "no vacancy" claim has no document.
4. It asks three questions (vacancy basis, management fee, rental registration owner) and builds the checklist with owners and dates. It never says whether the deal is good.

## FAQ seeds

- Does it need network? No.
- Will it tell me whether to buy? No; it records and calculates and refers decisions to licensed professionals.
- Which currency does it use? Whatever you set, one per file; comparisons across currencies stop with an error.
- Does it work with monthly rent? Yes, once multiplied by 12 and noted in `income.note`.
- What if my lender defines DSCR differently? Use the lender's definition by hand; the reference lists common variants.
- Does anything leave my machine? No; it reads only the files you give it.
- How do I uninstall? Delete the folder.

## Changelog

0.1.0, 2026-11-21: first draft; script fixtures only.

## License and authorship

Apache-2.0, Global Media Holdings (skillalmanac.com). Drafted by claude-sonnet-5-5 with AI assistance; accountable publisher Global Media Holdings. No human review has been completed.
