# Recipe scale converter

**One line:** Scale a recipe by servings, factor or pan size and convert between cups, grams and ounces, with warnings where linear scaling misleads.

## What it does

The skill turns an ingredient list into a scaled and optionally converted list. A Python script reads one ingredient per line (mixed numbers, fractions, Unicode fractions, ranges, bracketed pack sizes), multiplies with exact fractions, converts volume to weight only through a density table (a bundled approximate list or the user's own CSV), and rounds once to kitchen-friendly measures. Every line carries a note and a confidence. Leavening, salt, strong spices and simmering liquid get a "taste or test" note when the factor is 2 or more, or 0.5 or less; cook time is never computed, only warned about.

## Capabilities

- Factor, servings-to-servings and pan-to-pan scaling (rectangle, square, round, inches or centimetres) with the formula stated.
- Metric to US and US to metric, in the same family or across volume and weight with a density.
- Rounding tables per unit and a unit ladder (for example 4 tbsp becomes 1/4 cup when rounding loses 3 percent or less).
- Checks: no quantity, number written as a word, unknown unit, ambiguous `oz` and `stick`, pack sizes, same ingredient in two units, fractional eggs, factor above 4 or below 0.25.
- Strict JSON output, or a plain text list.

## When to use

Doubling, halving or resizing a recipe; changing pans; converting a recipe between metric and US; preparing a recipe for a bake sale or a small kitchen.

## When not to use

Nutrition, calories, allergens, food safety, canning or curing ratios, meal plans, shopping lists, writing recipes, cook times and temperatures, or normalising unit columns in a dataset (a different job).

## Requirements

Python 3.9 or newer, standard library only. No network access. Tested only on the fixtures listed in VERIFICATION.md.

## Example 1: cookies for a sale, in grams

Prompt: "This cookie recipe makes 24. I need 60 and I want grams where possible."

Command: `python scripts/scale_recipe.py evals/files/t1-cookies/recipe.txt --from-servings 24 --to-servings 60 --units metric --basis mass --format text`

Output (saved fixture run):

```
680 g all-purpose flour
2 1/2 tsp baking soda
15 g salt
570 g butter, softened
380 g granulated sugar
400 g brown sugar
5 large eggs
5 tsp vanilla extract
5 cups chocolate chips

factor: 2.5 (servings 24 to 60)
warning: cook time and temperature are not computed; they do not scale with the factor, so go by the recipe's own doneness test
```

The JSON form adds, for the baking soda and salt lines, the note that the amount is linear and should be added in steps and tasted, and for the chocolate chips a `no_density` flag.

## Example 2: a different pan

Command: `python scripts/scale_recipe.py evals/files/t2-cake-pan/recipe.txt --from-pan round:9 --to-pan 9x13 --format text`

Output (saved fixture run): factor 1.8391 and `2 3/4 cups all-purpose flour`, `1 7/8 cups sugar`, `14 1/2 tbsp milk`, `3 1/2 large eggs`, `1 1/4 tbsp baking powder`, `7/8 tsp salt`, plus a warning that the pan factor assumes the same batter depth.

## Limits

Densities are approximate and rounded. Cup sizes differ by country (US and a 250 ml metric cup are supported). Non-linear rules are working heuristics. Pans are compared by area only. No nutrition, safety, time or temperature advice. English only.

## Evidence

Static lint passes with 0 FAIL and 0 WARN; 16 of 16 script and write-safety checks pass on hand-checked fixtures. Not tested: with and without efficacy, trigger rate, native discovery, any tool other than direct script runs, human review. See VERIFICATION.md.

## Difference from nearby skills

unit-normalization-plan (reserved) specifies unit normalisation for dataset fields; this skill scales and converts real recipe quantities with a density table and kitchen rounding. spreadsheet-analysis and travel-planner do not scale ingredient lists.

## Demo storyboard (60 to 90 seconds)

1. Prompt: the 24-cookie recipe and "I need 60, in grams".
2. The agent saves the list to a file and runs the script.
3. Show the JSON warnings and the notes on salt and baking soda.
4. Show the final list in grams, with chocolate chips left in cups because there was no density.
5. Before and after: the user's list against the scaled list.

## FAQ seeds

- Does it need the internet? No.
- Where do the densities come from? Approximate rounded working values, listed in references/tables.md; override with your own CSV.
- Why are chocolate chips still in cups? There is no bundled density for them, and the script does not guess.
- Why does the cooking time not change? It does not scale with the factor, so the script only warns.
- Can it give calories? No.
- How is it different from a dataset unit tool? It reads recipe lines and rounds to kitchen measures.
- How do I uninstall it? Delete the skill folder.

## Changelog

0.1.0, 2026-11-21: first draft; script fixtures only.

## License and authorship

Apache-2.0, copyright Global Media Holdings (skillalmanac.com). Drafted with AI assistance (claude-sonnet-5-5); accountable publisher Global Media Holdings. No human review has taken place yet.
