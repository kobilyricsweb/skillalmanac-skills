# meal-plan-grocery-list

## One line

Builds a dinner plan and a merged grocery list for a household within a budget the user sets, using the user's own recipes and prices.

## What it does

The skill takes a short intake: number of adults and children, number of dinners, a diet rule, a budget in US dollars, recipes with base servings, a price list and an optional pantry. It checks the intake first and stops with a numbered question list if a required fact is missing.

It then removes dishes that break the diet rule, limits repeated dinners to two, and scales each recipe to the household size. Ingredient lines are converted to a base unit, summed across all dinners, and rounded after the sum. Pantry amounts on hand are subtracted, and purchase quantities are rounded up to whole packages from the user's price list.

The output has six fixed sections: a summary, the dinner order, a grocery table with package counts and line totals, a budget check with a three-band result, a list of unpriced or unverified items, and a list of assumptions. Lines without a user price are marked and excluded from the total, which changes the status to partial. The skill does not invent prices or nutrition facts.

## When to use

- A household wants one to fourteen dinners planned in one pass with a fixed budget.
- The user already has recipes and prices, and wants the same ingredient used across several dishes counted once on the shopping list.
- The user wants a pantry subtracted before shopping, with package rounding applied.
- The user wants repeated dinners capped, for example at most two in a week.

## When not to use

- The user asks for a medical diet, a calorie or macro target, or a weight goal. The skill refuses those.
- The user needs allergen safety certified or cross-contact guaranteed.
- The user wants current store prices. The skill uses only the prices the user typed in.
- The user wants recipes invented from scratch with no review. Drafted recipes are allowed but capped at partial status and listed for review.

## Requirements

No tools, network access or files beyond a text-capable agent. The user supplies the intake facts in the conversation. The skill runs in any agent that can follow a numbered procedure and produce Markdown tables.

## Example

Input in short form: two adults, no children, five dinners, vegetarian, a $60.00 budget, four-serving recipes, a price list for 16 ingredients, and a pantry with 500 mL of olive oil and 1 onion. Lentil soup is repeated on day 5, which counts as one repeat.

### Summary

| Item | Value |
|---|---|
| Household | 2 adults, 0 children |
| Dinners | 5 |
| Diet | vegetarian |
| Budget (USD) | $60.00 |
| Status | complete |

### Dinner plan

| Day | Dinner | Repeat of day | Scale factor |
|---|---|---|---|
| 1 | Lentil soup | | 0.50 |
| 2 | Black bean tacos | | 0.50 |
| 3 | Vegetable fried rice | | 0.50 |
| 4 | Tomato and spinach pasta | | 0.50 |
| 5 | Lentil soup | 1 | 0.50 |

### Grocery list

| Ingredient | Needed | Pantry | To buy | Package | Packages | Package price | Line total |
|---|---|---|---|---|---|---|---|
| Avocado | 1 each | 0 each | 1 each | Single avocado, 1 each | 1 | $0.79 | $0.79 |
| Black bean (canned) | 400 g | 0 g | 400 g | Can 425 g | 1 | $0.99 | $0.99 |
| Carrot | 3 each | 0 each | 3 each | Bag of 4 each | 1 | $1.49 | $1.49 |
| Corn tortilla | 6 each | 0 each | 6 each | Pack of 30 each | 1 | $2.99 | $2.99 |
| Crushed tomato | 400 g | 0 g | 400 g | Can 800 g | 1 | $1.79 | $1.79 |
| Dried lentil | 500 g | 0 g | 500 g | Bag 1000 g | 1 | $2.49 | $2.49 |
| Egg | 2 each | 0 each | 2 each | Carton of 12 each | 1 | $3.49 | $3.49 |
| Frozen pea | 150 g | 0 g | 150 g | Bag 450 g | 1 | $1.79 | $1.79 |
| Garlic | 2 each | 0 each | 2 each | Bulb of 10 each | 1 | $0.69 | $0.69 |
| Lime | 1 each | 0 each | 1 each | Single lime, 1 each | 1 | $0.50 | $0.50 |
| Long-grain rice | 200 g | 0 g | 200 g | Bag 1000 g | 1 | $2.19 | $2.19 |
| Olive oil | 45 mL | 500 mL | 0 mL | Bottle 500 mL | 0 | $4.99 | $0.00 |
| Onion | 2 each | 1 each | 1 each | Bag of 3 each | 1 | $1.29 | $1.29 |
| Pasta | 250 g | 0 g | 250 g | Box 500 g | 1 | $1.29 | $1.29 |
| Spinach | 75 g | 0 g | 75 g | Bag 300 g | 1 | $2.49 | $2.49 |
| Vegetable broth | 1000 mL | 0 mL | 1000 mL | Carton 1000 mL | 1 | $2.29 | $2.29 |

### Budget check

| Item | Value |
|---|---|
| Priced total | $26.56 |
| Budget | $60.00 |
| Remaining | $33.44 |
| Result | under budget |

### Unpriced or unverified

None.

### Assumptions

- Pantry is exactly as the user listed it. No other pantry items were assumed.
- Child serving weight is not used, because the household has no children.
- Scale factor is 2 servings needed divided by the 4-serving base, which gives 0.50 for each dinner.
- Recipes are user-supplied, not drafted, so no recipe is marked drafted.
- Unit conversions are the fixed values in the skill: 1 cup = 240 mL, 1 oz = 28 g, 1 lb = 454 g.
- Budget bands are working values. The total of $26.56 is at or below 90% of the budget ($54.00), so the result is under budget.

## Limits

- Prices, package sizes and recipe amounts are only as accurate as the user's input. The skill does not check them against any store.
- The rounding rules (whole each for counts, nearest 5 g or 5 mL for mass and volume) can leave small surplus amounts on the list.
- Repeat cap, child serving weight and budget bands are working values, not published standards.
- The skill makes no nutrition, medical or allergen claims, and it refuses requests for them.
- Cooking times, shopping order and store layout are outside its scope.

## Status

Provisional. Lint-clean, one smoke run. Not independently verified.
