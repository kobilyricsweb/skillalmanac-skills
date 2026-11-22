---
name: real-estate-deal-notes
description: Organises a property deal file for small investors and agents. Use when the user says deal notes, deal file, cap rate, cash on cash, DSCR, rental property numbers, compare properties or due diligence checklist. Gives a deal-notes contract (facts, sources, dates), stated-formula arithmetic, a checklist with owner and date, a comparison table, and a script that flags missing, inconsistent or stale inputs. Do not use for advice on whether to buy, sell, price or finance, valuation, tax, legal or lending guidance, or market forecasts.
license: Apache-2.0
compatibility: The script needs Python 3.9 or newer, standard library only. No network access is used. Without Python, follow the manual formulas in references/formulas.md and the flag rules in step 4.
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  author_model: claude-sonnet-5-5
  version: "0.1.0"
  network: none
---

# Real estate deal notes

Turn a pile of listing details, rent rolls, quotes and emails into one organised deal file. You record, compute stated formulas and flag gaps. You do not judge the deal.

## Arithmetic-only rule

Every reply that contains a computed figure carries this line, word for word: `Arithmetic on the supplied inputs only, not advice. Verify every figure and decision with a licensed professional.`

Never write or imply: that a deal is good, bad, a bargain, overpriced, safe or risky; that the user should buy, sell, offer, hold, refinance or walk away; a value estimate, a rent estimate, an appreciation or market forecast; a tax, legal, lending or insurance opinion. If asked, say this skill only records and calculates, restate the numbers with their formulas, name the licensed professional type that would answer (agent, appraiser, lender, attorney, tax adviser), and offer the checklist item that would put the question to them. A number is described by what it equals ("cap rate 5.85 percent on the stated inputs"), never by what it means.

Never invent an input. A missing figure stays missing and is reported; do not estimate vacancy, expenses or rate "to fill the sheet".

## Deal-notes contract

One folder per deal, two files. Start from `assets/deal_template.json` and `assets/deal_notes_template.md`.

1. `deal.json` holds machine-checked inputs. Required: `property.address`, `property.type`, `currency` (3 uppercase letters), `as_of` (YYYY-MM-DD, the date the figures describe), `purchase_price`, `income.gross_scheduled_rent_annual`, `income.vacancy_rate`, `expenses.operating_expenses_annual`. Optional: `income.other_income_annual`, `closing_costs`, `renovation_cost`, `financing.{down_payment, loan_amount, interest_rate, term_years, annual_debt_service, note}`, `property.{units, area_value, area_unit (sqft or sqm), year_built}`, `income.note`, `expenses.note`, `sources`, `due_diligence`.
2. Units are fixed so nothing needs guessing: money is a plain number in the file currency, all income and expense figures are per year, rates are fractions (0.065, not 6.5), areas are in `sqft` or `sqm`. Monthly figures are multiplied by 12 by the user or by you, and the multiplication is written in `income.note`.
3. Every key input (price, rent, operating expenses) has an entry in `sources`: `{"field", "source", "date"}`. Who said it and when, for example "seller rent roll, 2026-10-20". A figure from conversation with no document is recorded as such ("seller verbal"), not upgraded.
4. `deal_notes.md` is the human file: facts table (each fact, value, source, date), open questions, decisions the user made and their date (recorded in the user's words), and the due-diligence list. Separate what a document says from what someone told the user.

## Workflow

```
- [ ] 1 Collect and structure facts
- [ ] 2 Fill deal.json (no guesses)
- [ ] 3 Run the check
- [ ] 4 Resolve flags with the user
- [ ] 5 Build the due-diligence list
- [ ] 6 Comparison table (only if two or more deals)
- [ ] 7 Report
```

1. **Collect.** Extract property facts from what the user pasted into the facts table with source and date per row. Quote ambiguous items instead of interpreting them.
2. **Fill `deal.json`.** Use exactly the keys above. Ask the user only for the missing required inputs, in one message, listing each field and its unit.
3. **Run** `python scripts/deal_check.py check deal.json`. Add `--today YYYY-MM-DD` only to reproduce an earlier run. Output is strict JSON: `results` (formulas listed under `formulas`), `not_computed` with the missing inputs per metric, `flags`, `due_diligence` counts, `counts`, `disclaimer`. Exit 0 means no input errors, 1 means at least one `error` flag, 2 means a usage or file problem. Do not edit the script to make a check pass.
4. **Resolve flags.** Flag meaning and the action:

| Flag | Meaning | Action |
|---|---|---|
| `MISSING_FIELD`, `NOT_A_NUMBER`, `BAD_CURRENCY`, `BAD_DATE` | Required input absent or malformed | Ask the user; do not compute around it |
| `RATE_NOT_FRACTION` | A rate above 1 | Convert only after the user confirms the unit |
| `OUT_OF_RANGE`, `LOAN_EXCEEDS_PRICE` | Negative or impossible value | Ask |
| `EXPENSES_EXCEED_INCOME` | Operating expenses above effective gross income and no `expenses.note` | Ask for the reason; record the answer in `expenses.note` |
| `OPEX_RATIO_LOW` | Expenses under 10 percent of income, no note | Ask which categories are included (tax, insurance, repairs, management, utilities) |
| `VACANCY_ZERO` | Vacancy 0 and no `income.note` | Ask for the basis; record it |
| `FINANCING_MISMATCH` | Down payment plus loan differs from price by over 1 percent, no `financing.note` | Ask (seller credit, cash purchase, second loan); record it |
| `DEBT_SERVICE_MISMATCH`, `FINANCING_INCOMPLETE` | Override or partial loan terms disagree with the amortised figure | Ask which is right |
| `RESULT_OUTSIDE_USUAL_RANGE` | Gross yield outside 1 to 30 percent or cap rate outside 0 to 25 percent | Treat as a likely unit slip (monthly entered as annual, percent as fraction); ask. If confirmed correct, say so in a note; the number is still reported |
| `STALE_AS_OF`, `STALE_SOURCE`, `FUTURE_DATE` | Figures older than 90 days, sources older than 180 days, or dated after today | Ask for a refresh or record that the user accepts the age |
| `NO_SOURCE`, `SOURCE_NO_DATE`, `DEFAULTED_TO_ZERO` | Unsourced key input, undated source, or an omitted cost treated as 0 | Ask; a defaulted closing or renovation cost raises cash-on-cash |
| `DD_NO_OWNER`, `DD_NO_DATE`, `DD_OVERDUE` | Open checklist item lacking owner or date, or past due | Assign or reschedule with the user |

   After answers, update `deal.json` and re-run. A flag the user decides to keep is written into the relevant `note` field, not deleted from the report.
5. **Due diligence.** Read [references/due_diligence_checklist.md](references/due_diligence_checklist.md) and copy only the items that apply to the property type. Each item gets `owner` (a named person or role, never "TBD"), `due` (a date), `status` (`open`, `done`, `blocked`, `na`), and for `done` a one-line result with the document it came from. Do not mark an item `done` on the user's word without writing that it is self-reported.
6. **Compare.** For two or more deals run `python scripts/deal_check.py compare a.json b.json ...`. Follow the procedure in [references/comparison_procedure.md](references/comparison_procedure.md): same currency, as_of within 30 days, same formula definitions, rows in the order given, no ranking, no "best" column, one sentence per row stating only differences in inputs.
7. **Report** in this fixed shape, after the arithmetic line:

```
Deal: <address>, figures as of <as_of>
Results: <the metrics with their formulas, each shown with its inputs>
Not computed: <metric: missing inputs>
Flags: <count by severity; each warn/error with the user's answer or "open">
Due diligence: <open / blocked / overdue counts; items missing an owner or date>
Not checked: <e.g. every figure against its source document; zoning, title, condition, market rents>
```

Formula definitions and the traps behind each one (what the cap rate excludes, which denominator cash-on-cash uses, the lender's DSCR variant) are in [references/formulas.md](references/formulas.md). Read it before explaining a result or when the user's lender or agent quotes a different definition.

## Files

- `scripts/deal_check.py`: run it, do not read it unless a result is disputed. `check` for one deal, `compare` for several. Reads only the given files and writes nothing.
- `assets/deal_template.json`: copy and fill. `assets/deal_notes_template.md`: copy and fill.
- `references/formulas.md`, `references/due_diligence_checklist.md`, `references/comparison_procedure.md`: read the one the current step names.

If Python is not available: compute by hand from `references/formulas.md`, show each formula with its numbers substituted, and apply the flag table above by eye. Say in the report that the script was not run.

## Limits

- The script checks internal consistency, units and dates. It cannot tell whether a rent, price or expense is true; that needs the source documents and a licensed professional.
- Thresholds (90 and 180 days, 1 percent financing gap, 10 percent expense ratio, the yield and cap ranges) are working values to catch input slips. They are not statements about what a normal property looks like.
- The debt-service figure assumes a level-payment, fully amortising loan with monthly payments. Interest-only, balloon, variable-rate and fee-bearing loans need `financing.annual_debt_service` supplied from the lender's own schedule.
- Taxes, depreciation, capital reserves, management fees and appreciation are outside the formulas unless the user includes them in the stated expenses.
- Formula conventions vary by market and lender; the script uses the definitions in `references/formulas.md` and says so in its output.
- The skill is not a licensed professional and does not replace one.
