## Contents

1. Definitions used by the script
2. Worked example
3. Traps and variant definitions
4. Wording for results

## 1. Definitions used by the script

All money is annual and in the file currency. Rates are fractions.

| Metric | Formula | Notes |
|---|---|---|
| Gross yield | gross_scheduled_rent_annual / purchase_price | Before vacancy and expenses; price only, no closing or renovation cost in the denominator |
| Effective gross income (EGI) | gross_scheduled_rent_annual x (1 - vacancy_rate) + other_income_annual | Vacancy applies to rent, not to other income |
| Net operating income (NOI) | EGI - operating_expenses_annual | Debt service, depreciation, income tax and capital spending are not operating expenses here |
| Cap rate | NOI / purchase_price | Uses the price, not an appraised value, because the file has no appraisal |
| Annual debt service | 12 x level monthly payment, where payment = L x r / (1 - (1 + r)^-n), r = interest_rate / 12, n = term_years x 12; if r is 0, payment = L / n | Or `financing.annual_debt_service` as supplied |
| Cash flow before tax | NOI - annual debt service | Not income tax; not after reserves unless reserves sit in operating expenses |
| Total cash invested | down_payment + closing_costs + renovation_cost | Excludes the loan |
| Cash-on-cash | cash flow before tax / total cash invested | Year-one style snapshot from the stated inputs; not an annualised return over a hold |
| DSCR | NOI / annual debt service | Undefined when debt service is 0 |

## 2. Worked example

Price 400,000; rent 36,000; vacancy 0.05; other income 1,200; operating expenses 12,000; closing 8,000; renovation 12,000; down payment 100,000; loan 300,000 at 0.06 over 30 years.

- Gross yield 36,000 / 400,000 = 0.0900
- EGI 36,000 x 0.95 + 1,200 = 35,400
- NOI 35,400 - 12,000 = 23,400; cap rate 23,400 / 400,000 = 0.0585
- Monthly payment 1,798.65; annual debt service 21,583.82
- Cash flow before tax 23,400 - 21,583.82 = 1,816.18
- Total cash invested 100,000 + 8,000 + 12,000 = 120,000; cash-on-cash 1,816.18 / 120,000 = 0.0151
- DSCR 23,400 / 21,583.82 = 1.0841

## 3. Traps and variant definitions

- **Expenses that sneak into NOI.** Mortgage interest and principal are financing, not operating. A "total expenses" figure from a seller statement often includes them; subtracting debt service again counts it twice. Ask which lines the figure contains.
- **Expenses left out.** Seller statements commonly omit management, vacancy, repairs reserve or the buyer's own insurance quote. The script flags an expense ratio under 10 percent for this reason; it cannot say what is missing.
- **Gross rent multiplier.** Price divided by gross rent is the reciprocal of gross yield. If a source quotes a multiplier, convert and state both.
- **Cap rate on value or price.** Agents may quote cap rate on list price, offer price or appraised value. Write which one in the notes. The script uses the purchase price entered.
- **Cash-on-cash denominator.** Some people leave out closing costs or renovation spend. The script includes them because they are cash the investor puts in; if the user prefers another convention, say so in the report and compute by hand, labelled.
- **DSCR variants.** Lenders may use NOI after a reserve, a stressed rate, or a minimum lease-up income. The script's DSCR uses NOI as stated. A lender's own figure is the one that matters for a loan decision; ask the lender for its definition.
- **Rates in percent.** 6.5 entered for a rate is a unit slip; the script rejects any rate above 1 rather than convert.
- **Monthly versus annual.** Rent entered monthly gives a gross yield near 0.007 to 0.01. The script flags a gross yield below 0.01 as a likely slip.
- **Currency and area.** Never convert currency or area silently. Mixed currencies make a comparison invalid; the compare command stops with an error.
- **Rounding.** Ratios are shown to 4 decimals and money to 2. Round only at display.

These are conventions of the arithmetic, not statements about any market. Figures about local taxes, rents or lending terms must come from documents or a licensed professional.

## 4. Wording for results

Use: "On the stated inputs the cap rate is 5.85 percent (NOI 23,400 / price 400,000)." Do not use: "a solid 5.85 percent", "below market", "healthy coverage", "thin margin". A DSCR of 1.08 is "NOI is 1.08 times the stated annual debt service"; whether a lender accepts it is a question for the lender.
