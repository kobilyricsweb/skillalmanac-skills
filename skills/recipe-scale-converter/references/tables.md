## Contents

- Unit constants
- Bundled density table
- Matching rules and traps
- Your own density file
- Sources

## Unit constants

Defined exactly in the script (US customary):

| Unit | Value |
|---|---|
| 1 US fluid ounce | 29.5735295625 ml |
| 1 tsp | 1/6 fl oz = 4.92892159375 ml |
| 1 tbsp | 1/2 fl oz = 14.78676478125 ml |
| 1 cup | 8 fl oz = 236.5882365 ml |
| 1 pint, quart, gallon | 16, 32, 128 fl oz |
| 1 ounce (weight) | 28.349523125 g |
| 1 pound | 453.59237 g |
| 1 butter stick | 4 fl oz volume (1/2 cup, 8 tbsp) |

`--system metric` swaps only tsp, tbsp and cup to 5, 15 and 250 ml. Fluid ounce, pint, quart and gallon stay US.

## Bundled density table

Grams per US cup (236.588 ml). Approximate working values rounded to whole grams; real products differ by brand, moisture and how the cup is filled. Replace any of them with `--density`.

| Ingredient | g per cup | Matches (confidence) |
|---|---|---|
| all-purpose flour | 120 | all-purpose, plain, ap flour (high); flour (medium) |
| bread flour | 127 | bread flour |
| whole wheat flour | 120 | whole wheat, wholemeal |
| granulated sugar | 200 | granulated, white sugar (high); sugar (medium) |
| brown sugar | 213 | brown sugar, firmly packed |
| powdered sugar | 120 | powdered, confectioners, icing |
| butter | 227 | butter (high); margarine (medium) |
| milk | 245 | milk |
| water | 237 | water |
| honey | 340 | honey |
| vegetable oil | 218 | vegetable, canola, sunflower oil (high); oil (medium) |
| olive oil | 216 | olive oil |
| rolled oats | 90 | rolled oats, old-fashioned oats, oats |
| cocoa powder | 85 | cocoa, cocoa powder |
| cornstarch | 128 | cornstarch, corn starch (high); cornflour (medium) |
| table salt | 288 | table salt (high); salt (medium) |
| white rice (uncooked) | 185 | white rice (high); rice (medium) |
| heavy cream | 238 | heavy, whipping, double cream (high); cream (medium) |
| yogurt | 245 | yogurt, yoghurt |
| maple syrup | 315 | maple syrup |
| peanut butter | 258 | peanut butter |

## Matching rules and traps

- The longest matching phrase wins, so "peanut butter" never falls through to "butter".
- A one-word phrase matches only when every word before it is a plain descriptor (sifted, unsalted, large, packed, whole and similar). "almond flour", "coconut milk" and "ice cream" therefore get no density instead of a wrong one.
- Salt is refused when the line says kosher, flaky, sea, coarse, pink or Himalayan: crystal size changes grams per cup several-fold.
- "Cream" is refused before cheese or tartar.
- A medium-confidence match (a generic word such as "flour") lowers the line's confidence and says which entry was used.
- Two lines for the same ingredient in different units are flagged; the script does not add them together.
- Volume to weight for a liquid and weight to volume for a dry good use the same single number; that is why the numbers are approximate.

## Your own density file

CSV, one ingredient per line: `ingredient,g_per_cup`. A header row, blank lines and lines starting with `#` are allowed. Values must be grams per US cup between 20 and 600; anything else stops the run with the line number. Phrases are matched as whole words anywhere in the ingredient name, longest first, before the bundled table, and count as high confidence.

## Sources

- NIST Special Publication 811, guide for the use of the International System of Units, appendix B conversion factors (exact values for the fluid ounce, ounce and pound): https://www.nist.gov/pml/special-publication-811
- The grams-per-cup values are not taken from one source. They are rounded working values in the range commonly quoted in kitchen conversion practice, and the script labels them approximate on every line that uses them.
