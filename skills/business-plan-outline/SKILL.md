---
name: business-plan-outline
description: Writes a one-page business plan outline from founder-supplied inputs, tagging every number as GIVEN or ASSUMPTION and naming the five assumptions that most change the outcome, each with a test. Use when a founder asks for a one-page business plan, a plan outline with stated assumptions, or a plan for a new product, service or local business whose numbers must be labeled. Do not use for full financial models, investor pitch decks, revenue forecasts without user-supplied inputs, or legal, tax or regulatory advice.
license: Apache-2.0
compatibility: Requires none beyond a text-capable agent (type B).
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  author_model: claude-haiku-5-5
  version: "0.1.0"
  network: none
---

# Business plan outline

This skill produces one outline in a fixed eight-section format. Every number carries a tag. The skill never invents an input: a number the user did not give or estimate is not written into the plan.

## Definitions

- GIVEN: a price, cost or fact the user states as known, such as a quote, a price list or a signed contract.
- ASSUMPTION: any estimate, including volumes and costs the user estimated. Tag it ASSUMPTION even when the user sounds confident.
- Working value: a threshold in this skill that is not a published standard. Label it "working value" wherever it appears in the output.
- Amounts are in the user's currency. Examples use US dollars.

## Workflow

1. Intake. Check the eight intake items: problem, customer segment, offer, unit price, sales channel, revenue model, cost lines, start month. Output: a checklist marking each item present, missing or estimated.
2. Stop check. Apply the decision table below. Output: one status value and, if needed, the question list.
3. Tag numbers. Attach GIVEN or ASSUMPTION to every number. Output: a list of number, tag and the user sentence it came from.
4. Revenue. Compute revenue only when a unit price is GIVEN and a volume exists as GIVEN or ASSUMPTION. Output: the formula units x unit price per month, with its tag.
5. Unit economics. Variable cost per unit is the sum of per-unit costs. Contribution per unit is unit price minus variable cost per unit. Break-even units per month is fixed cost per month divided by contribution per unit, rounded up to a whole unit. Output: the three values and any flag.
6. Milestones. Write exactly four milestone rows at months 1, 3, 6 and 12. Output: the table in section 7.
7. Assumptions. For each ASSUMPTION, recompute month-12 profit with the value at minus 20 percent and at plus 20 percent. Rank by the absolute change at minus 20 percent and keep the top five. Output: the table in section 8.
8. Self-check. Recompute every total. Confirm eight sections, four milestone rows and five assumption rows. Output: "pass" or a list of fixes made.

## Decision table

| Condition | Action | Status |
|---|---|---|
| Problem, customer, unit price or sales channel is missing | Stop. Return a numbered question list of at most 6 questions. Write no plan. | needs_input |
| No unit price is given | Write "Revenue not forecast: no price input" in section 5. Return the question list. | needs_input |
| Unit price is GIVEN but no volume estimate exists | Leave section 5 revenue cells blank. Write "Revenue not forecast: no volume input" and ask one question. | partial |
| Start month or cost lines are missing | Set start month to month 1 and fill missing cost lines as ASSUMPTION "not given". Continue. | partial |
| Contribution per unit is zero or below | Continue. Write "negative unit contribution" in section 5. | partial |
| Break-even units above 3 times the month-12 units (working value) | Continue. Write "break-even far above target" in section 7. | partial |
| All intake items present or estimated, no flags | Write the full outline. | complete |

Use "refused" for requests listed under Refuse / stop when.

## Assumption tests (working values)

| Assumption type | Test | Pass if |
|---|---|---|
| Units per month | 14-day waitlist or pre-booking test | At least half of the month-3 unit target is booked (working value) |
| Variable cost per unit | Time or quote five real jobs | Average is at or below the stated figure |
| Fixed cost line | Two written quotes | Lower quote is at or below the stated figure |
| Marketing spend | 14-day test capped at the stated monthly amount | Cost per booking is at or below one-third of unit price (working value) |
| Customer reach | Ten customer interviews | Seven of ten say they would pay the unit price (working value) |

## Output contract

Use these headings in this order and no others:

- Title line: "# Business plan outline: " followed by the business name.
- "Status:" line with one value: complete, partial, needs_input or refused.
- "Notes:" line listing each partial reason, or "none".
- "## 1. Problem" through "## 4. Channel": short prose, one paragraph each.
- "## 5. Revenue model": a table with columns Line, Formula, Value, Tag. Then lines for contribution per unit, break-even units per month and any flag.
- "## 6. Cost lines": a table with columns Line, Amount per month, Tag. End with a total row.
- "## 7. 12-month milestones": a table with columns Month, Units, Revenue, Variable cost, Fixed cost, Profit. Rows are months 1, 3, 6 and 12. Profit equals revenue minus variable cost minus fixed cost.
- "## 8. Assumptions to test": a table with columns Rank, Assumption, Value, Profit change at minus 20 percent, Profit change at plus 20 percent, Test, Pass if. Five rows, ranked 1 to 5.

## Output rules

- Amounts are whole currency units with a thousands separator, such as 8,400. Do not show cents.
- Put the tag in its own column or at the end of the line, never only in prose.
- Profit changes in section 8 are shown with a sign: -840 or +840.
- Units and money are never mixed in one cell. Units go in the Units column only.
- Revenue equals units times unit price. Recompute it in the table; do not copy it from elsewhere.
- Fixed cost in section 7 equals the total of section 6 for every month, unless the user gave a month-specific cost, which must be tagged GIVEN or ASSUMPTION in section 6.
- Do not add a section, a milestone row or an assumption row beyond the counts in this file.
- Use US English spelling and plain sentences. Avoid the word "guaranteed" and any claim of certainty about future sales.
- If the Notes line says "none", the Status line must say complete.
- A plan with status partial must name every partial reason in the Notes line, one reason per clause.

## Refuse / stop when

- The request asks for a success probability, a funding amount or an investor valuation. Status: refused.
- No unit price is given. Refuse the revenue forecast and return the question list.
- A critical intake item is missing (see decision table). Return the question list and write no plan.
- The request asks for legal, tax or regulatory advice. Decline that part and continue the outline.
- The user asks to label an ASSUMPTION as GIVEN. Keep the tag and say why in the Notes line.

## Files

- [License](LICENSE.txt): Apache-2.0 text for this skill.
