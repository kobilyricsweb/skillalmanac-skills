---
name: recipe-scale-converter
description: Scales recipe ingredient lists by servings, a factor or pan size and converts cups, spoons, grams and ounces. Use when the user says double this recipe, halve it, scale to 12 servings, my pan is smaller, convert cups to grams, or metric to US. A script parses lines like 1 1/2 cups flour, changes volume to weight only through a density table, rounds to kitchen measures and flags items that do not scale linearly (leavening, salt, spices, simmering liquid, cook time). Do not use for nutrition, calories, allergens, food safety, canning, meal plans, shopping lists or writing new recipes.
license: Apache-2.0
compatibility: The script needs Python 3.9 or newer, standard library only. No network access is used. Without Python, follow the manual method in steps 2 to 5.
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  author_model: claude-sonnet-5-5
  version: "0.1.0"
  network: none
---

# Recipe scale converter

Arithmetic and unit conversion on an ingredient list, nothing else. The script does the sums exactly (fractions, not floats) and rounds once at the end. Amounts for leavening, salt, spice and cook time are shown with a warning, never presented as settled.

## Workflow

```
- [ ] 1 Get the list and the target
- [ ] 2 Write the list as one ingredient per line
- [ ] 3 Run scripts/scale_recipe.py
- [ ] 4 Read warnings, notes and unparsed lines
- [ ] 5 Report in the fixed shape
```

1. **Collect** the ingredient list and exactly one target: a factor (2, 1.5, 3/2), servings (from and to) or pans (from and to). If the user gives a yield without the original yield, ask for it. Ask which cup they mean when the recipe is not American (see Limits). Ask for conversion needs: keep units, metric, US, and whether weight or volume is wanted.
2. **Format** each ingredient on its own line, no bullets: `1 1/2 cups flour`, `2-3 tbsp oil`, `200 g sugar`, `1 cup (227 g) butter`, `1 (14 oz) can tomatoes`, `3 large eggs`. Mixed numbers, fractions, decimals, Unicode fractions and ranges (`2-3`, `2 to 3`) are read. Compound quantities of one kind (`1 cup + 2 tbsp`, `1 lb 4 oz`) are summed into the first unit before scaling; a second quantity in a different kind of unit (`1 cup + 3 oz`) or combined with a range is not scaled: the line is kept as written with flag `unparsed_compound` and confidence low, so rewrite it as one quantity. Method text does not belong in the file.
3. **Run** (do not edit the script to make a result come out differently):

```bash
python scripts/scale_recipe.py recipe.txt --from-servings 4 --to-servings 10
python scripts/scale_recipe.py recipe.txt --factor 1.5 --units metric --basis mass
python scripts/scale_recipe.py recipe.txt --from-pan 9x13 --to-pan 8x8 --format text
```

   Options: `--units keep|metric|us`, `--basis keep|mass|volume`, `--system us|metric` (what tsp, tbsp and cup mean in the input), `--density file.csv` (your own `ingredient,g_per_cup` lines, checked before the bundled table), `--format json|text`, `--out file` (add `--force` to replace an existing file; the script never writes over the recipe or density file).
4. **Read the result**: `warnings[]` first, then each line's `note` and `confidence`, then `unparsed[]`. Fix unparsed lines in the file (words as numbers such as "one cup", a zero denominator, a backwards range) and run again. Exit code 1 means some lines were not parsed; 2 means a usage or file problem.
5. **Report** in this shape, with the scaled list first:

```
Scaled list: <the scaled_list lines, converted where a conversion was asked>
Factor: <value and how it was derived>
Check before cooking: <non-linear notes, pan and time warnings, ambiguous units>
Densities used: <ingredient and g per US cup, bundled approximate or user>
Not converted: <lines left in original units and why>
Not covered: <cook time, temperature, method; no nutrition or safety guidance>
```

## Formulas

- Servings: factor = target / original. Pans: factor = area(new) / area(old), where rectangle = a x b, round = pi x (d/2)^2, square = a x a, and centimetres are divided by 2.54 first. The pan factor assumes the same batter depth.
- Volume to weight: grams = millilitres x (g per US cup / 236.588). Weight to volume is the inverse. A conversion without a matching density is refused, never guessed.
- Exact unit constants: 1 US fl oz = 29.5735295625 ml; tsp = 1/6 fl oz; tbsp = 1/2 fl oz; US cup = 8 fl oz; 1 oz = 28.349523125 g; 1 lb = 453.59237 g; one butter stick = 4 fl oz volume (1/2 cup).

## Rounding to practical measures

| Unit | Rounded to | Notes |
|---|---|---|
| tsp | 1/8 below 1 tsp, then 1/4 | |
| tbsp | 1/4 below 4 tbsp, then 1/2 | |
| cup | nearest of 0, 1/8, 1/4, 1/3, 3/8, 1/2, 5/8, 2/3, 3/4, 7/8 | |
| g | 0.5 below 5, 1 below 20, 5 below 200, then 10 | kg to 0.05 |
| ml | 0.5 below 10, 5 below 100, then 10 | l to 0.05 |
| oz | 1/4 below 4, then 1/2 | lb to 1/4 |
| counts, packs | 1/2 below 10, then 1 | eggs flagged when fractional |

Unit ladder when the unit stays in the same system: cup from 1/4 cup, tbsp from 1 tbsp, tsp below that (kg from 1000 g, l from 1000 ml, lb from 16 oz), taking the larger unit only if rounding to it moves the value by 3 percent or less. A line whose rounding moves the value by more than 10 percent is flagged `rounding_large`.

## Non-linear items (documented heuristics, not measured laws)

Applied when the factor is 2 or more, or 0.5 or less:

| Class | Matches | Note given |
|---|---|---|
| leavening | baking powder, baking soda, yeast, cream of tartar | test a small batch or use the source's own scaled version |
| salt | salt | add in steps and taste; the number is an upper bound |
| strong flavour | cayenne, chili, cinnamon, cumin, garlic, extract and similar | add in steps and taste |
| simmering liquid | stock, broth, wine | evaporation does not scale with volume |

Always: cook time and temperature are not computed (`COOK_TIME`); a factor above 4 or below 0.25 adds a pan, batch or measuring warning; a pan change adds a depth warning. Curing salt, pectin and pickling lime are flagged ratio-critical: scale only from a tested source.

## Line checks

- No quantity ("salt to taste") is kept as written. A number written as a word is reported as unparsed.
- `oz` is read as weight; next to a liquid it is flagged ambiguous (fl oz intended?). `stick` is a butter stick only for butter or margarine.
- Unknown unit before "of" (for example "2 sacks of potatoes") is scaled linearly and flagged.
- Pack sizes in brackets, as in `1 (14 oz) can`, are not scaled; only the count is.
- The same ingredient in two different units gets `unit_mismatch`.
- Densities (g per US cup) are approximate: [references/tables.md](references/tables.md) lists every bundled value, matching rules, known traps and sources. Read it when a conversion note appears or the user asks which density was used.

## Output contract

`scale_recipe.py` prints strict JSON: `tool`, `version`, `factor{value, exact, basis}`, `settings{}`, `summary{lines, unparsed, converted, with_notes}`, `lines[]` (`line_no`, `original`, `scaled`, `converted` or null, `note`, `confidence` high, medium, low or n/a, `flags[]`, `rounding_error_pct`, `density` or null), `unparsed[]` (`line_no`, `original`, `reason`), `warnings[]` (`code`, `message`) and `scaled_list[]` (the converted line when present, else the scaled line).

## Boundaries

No nutrition, calorie, allergen, dietary or food-safety statements, and no times or temperatures. Do not scale canning, preserving or curing recipes with this skill's output; take those ratios from a tested source. Quantities are as the user supplied them; the script does not check that a recipe is sensible.

## Limits

- The bundled densities are approximate and rounded; flour in particular varies by scoop method. Give your own with `--density` for anything that matters. Salt crystal size changes density a lot, so kosher and sea salt are not matched.
- Cup sizes differ by country. `--system us` (default) and `--system metric` (cup 250 ml, tbsp 15 ml, tsp 5 ml) are supported; a 20 ml Australian tablespoon is not.
- Non-linear rules are working values from kitchen practice, not tested thresholds, and the script cannot know how the user's recipe behaves.
- "1-1/2" is read as one and a half, not a range; write ranges as "1 to 1 1/2".
- Pan factors treat all pans as the same depth; loaf and bundt pans need a volume-based judgement the script cannot make.
- Text is English only. Without Python, apply the formulas and tables by hand and say the result was computed by hand.
