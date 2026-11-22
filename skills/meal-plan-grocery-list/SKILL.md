---
name: meal-plan-grocery-list
description: Builds a dinner plan and a merged grocery list for a household within a user-set budget. Use when a user gives household size, a number of dinners, diet rules, a budget and their own prices, and wants repeats limited, ingredient quantities summed across dishes and pantry items subtracted. Do not use for medical diet advice, calorie or macro targets, allergy safety certification, or prices the user has not supplied.
license: Apache-2.0
compatibility: Works with none beyond a text-capable agent (type B).
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  author_model: claude-haiku-5-5
  version: "0.1.0"
  network: none
---

# Meal plan and grocery list

This skill turns a household's intake facts into a fixed set of dinners, one scaled ingredient list, a pantry-adjusted purchase list and a budget check. Every price comes from the user's price list. Every quantity comes from the user's recipes or from recipes drafted and marked as drafted.

Ships with: [LICENSE.txt](LICENSE.txt).

## Workflow

1. **Intake check.** Collect these facts:
   - adults (integer, 1 or more); children (integer, 0 or more; default 0)
   - dinners (integer, 1 to 14)
   - diet: `none`, `vegetarian`, `vegan`, or a list of excluded foods
   - budget in US dollars (a number above 0)
   - recipes: name, base servings, and ingredient lines (amount, unit, ingredient)
   - price list: ingredient, package size, package price in US dollars
   - pantry: ingredient, amount, unit (optional; default none)

   Output: a fact table with each value or `missing`. If adults, dinners, budget or recipes are missing, stop and return the numbered question list described under "Refuse / stop when" with status `needs-input`. If only dish names are given, draft ingredient lines at a base of 4 servings, mark each recipe `drafted`, and cap the status at `partial`. Missing prices or pantry do not stop the run.

2. **Diet filter and dinner slate.** Apply the diet table below to every ingredient line. Remove any dish that breaks the rule and replace it with another dish from the user's list. Then build the dinner order.

   | Diet | Excluded |
   |---|---|
   | `vegetarian` | meat, poultry, fish, shellfish, gelatin, animal stock |
   | `vegan` | everything in `vegetarian`, plus eggs, dairy, honey |
   | `none` | nothing added by this skill |

   Repeats: a dinner that matches an earlier dinner counts as a repeat. A plan may contain at most 2 repeats. If the plan would need more than 2, replace the extra repeats with new dishes before continuing.

   Output: the dinner list in day order, with `Repeat of day` filled for each repeat.

3. **Scale each dinner.** Servings needed = adults + 0.5 x children (working value). Scale factor = servings needed / base servings, rounded to 2 decimals. Multiply each ingredient line by the scale factor. Do not round yet.

   Output: one scaled line per dinner per ingredient.

4. **Merge and subtract pantry.** Convert every unit to its base unit, then sum all scaled lines that share an ingredient name and unit family.

   | Unit family | Accepted units | Base unit | Conversion (fixed) |
   |---|---|---|---|
   | mass | g, kg, oz, lb | g | kg = 1000 g; oz = 28 g; lb = 454 g |
   | volume | mL, L, tsp, tbsp, cup, fl oz | mL | L = 1000 mL; tsp = 5 mL; tbsp = 15 mL; cup = 240 mL; fl oz = 30 mL |
   | count | each, clove | each | 1 clove = 1 each (only for garlic lines) |

   Rounding happens after the sum. Count items round up to a whole `each`. Mass and volume round up to the nearest 5 g or 5 mL. If one ingredient name appears in two unit families, keep two lines and add a note under "Unpriced or unverified".

   Pantry: to buy = max(0, total needed - pantry amount), in the base unit. A pantry entry with no unit does not subtract; list it under "Unpriced or unverified".

   The `Pantry` column in the output shows the pantry amount on hand, even when it is larger than the amount needed.

   Output: one row per merged ingredient with needed, pantry and to-buy amounts.

5. **Price and budget check.** Packages to buy = ceiling(to buy / package size), with both in the same base unit. A line with to buy = 0 has 0 packages and a $0.00 line total. Line total = packages x package price. Use only the user's price list. A to-buy line with no price gets `price missing`, is excluded from the total, and sets the status to `partial`.

   Budget result, with priced total T and budget B (working values):

   | Condition | Result |
   |---|---|
   | T <= 0.90 x B | `under budget` |
   | 0.90 x B < T <= B | `within budget, tight` |
   | T > B | `over budget` |

   If the status is `partial`, the result still applies to the priced total and must say "priced lines only".

6. **Assemble the output.** Write the six sections in the order given in the output contract. Round money to 2 decimals and show dollars with a `$` sign.

## Decision and threshold table

| Item | Value | Rule |
|---|---|---|
| Dinners | 1 to 14 | Outside this range: `needs-input` |
| Repeats per plan | 0 to 2 | More than 2: replace repeats before output |
| Child serving weight | 0.5 | Working value |
| Mass rounding | nearest 5 g, up | Applied after summing |
| Volume rounding | nearest 5 mL, up | Applied after summing |
| Count rounding | whole each, up | Applied after summing |
| Tight budget band | 90% of budget | Working value |
| Status values | `complete`, `over budget`, `partial`, `needs-input`, `refused` | Exactly one per run |

Status meaning: `complete` means all lines priced, no drafted recipes, and the result is `under budget` or `within budget, tight`. `over budget` means all lines priced and the result is `over budget`. `partial` means any line is `price missing` or any recipe is `drafted`. `needs-input` means step 1 stopped the run. `refused` means a request fell under the refusal list.

## Output contract

Return Markdown with exactly these six level-2 headings, in this order:

1. `## Summary`: a 2-column table with rows Household, Dinners, Diet, Budget (USD), Status.
2. `## Dinner plan`: a table with columns Day | Dinner | Repeat of day | Scale factor.
3. `## Grocery list`: a table with columns Ingredient | Needed | Pantry | To buy | Package | Packages | Package price | Line total. Sort rows by ingredient name, A to Z.
4. `## Budget check`: a 2-column table with rows Priced total, Budget, Remaining, Result. Remaining = Budget - Priced total, and it can be negative.
5. `## Unpriced or unverified`: a bullet list. Write `None.` if nothing applies.
6. `## Assumptions`: a bullet list of every default used (pantry none, child weight, drafted recipes, unit conversions).

## Refuse / stop when

- Adults is 0, dinners is outside 1 to 14, budget is missing or not above 0, or recipes are missing. Stop with status `needs-input` and return a numbered question list. Ask one question per missing fact, and ask no more than 6 questions.
- The request asks for a medical or therapeutic diet claim (for example, a claim that a dish lowers blood sugar or treats a condition). Refuse that claim with status `refused`. The plan may still list the diet label the user stated.
- The request asks for calorie, macro, or weight targets. Refuse with status `refused`.
- The request asks you to certify allergen safety or cross-contact. Refuse with status `refused` and say the user must check product labels.
- A price is needed and the user did not supply it. Do not estimate it. Mark it `price missing` and set status `partial`.
- The plan would exceed 2 repeats and no replacement dish is available. Stop with status `needs-input`.
