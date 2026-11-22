# Rights lists and finding codes

The lists live in `scripts/prompt_lint.py` as constants. They are examples chosen for frequency in prompts, not a legal register. This is not legal advice.

## Contents

- What the script treats as an error
- What it treats as a warning
- How to allow a term you own
- Finding codes
- Contradiction pairs

## What the script treats as an error

- `rights-living-artist`: about 30 working artists and filmmakers by name (illustrators, photographers, a street artist, animators, painters). Kim Jung Gi (died 2022) was removed from this list because it holds living artists only; his name, like any deceased artist's, is still caught as `possible-artist-name` after a style hook, and estates can hold rights.

Rights terms are scanned on every line outside the Negative field, including lines with an unrecognised label (such as `Prompt note:`) and bare prose lines that follow the Negative field; any hit makes the verdict `blocked`.
- `rights-real-person`: about 33 widely photographed public figures.
- `rights-trademark`: about 55 brands, studios and franchises (media companies, sportswear, drinks, cars, games, characters).
- `rights-likeness`: phrases that ask for a real person's face whatever the name: face swap, deepfake, "looks like" or "resembling" followed by a person category or a two-word proper name, "celebrity", "famous actor".

Matching is whole-word and case-insensitive for list terms. The negative field is not scanned, so "Negative: logo, watermark" is fine.

## What it treats as a warning

- `possible-artist-name`: a capitalised name after `in the style of`, `inspired by`, `painted by`, `photographed by`, `art by` and similar, that is not on a list and does not start with a movement, nation or period word (art deco, bauhaus, Japanese, Victorian, and so on). Describe the look instead.
- `rights-role-name`: a title and a name, such as a head of state or monarch followed by a surname.
- `possible-brand-mark`: the words logo, trademark, brand name, branded.

## How to allow a term you own

`python scripts/prompt_lint.py lint prompt.txt --allow "Acme Tea"` skips rights hits whose matched text is exactly that term, case-insensitively. Use it only for a brand, character or person the user owns or has written permission to depict, and say so in the report.

## Finding codes

| Code | Severity | Meaning |
|---|---|---|
| missing-field | error for required fields, warning for camera, palette, negative | the field is absent |
| aspect-invalid | error | zero side, a side over 32, or outside 1:4 to 4:1 |
| aspect-conflict | error | two different ratios stated |
| aspect-unparseable | error | an aspect field with no number |
| aspect-uncommon | warning | valid in range, not in the common set of 17 ratios |
| aspect-dimensions | warning | pixel size not a multiple of 8 |
| rights-living-artist, rights-real-person, rights-trademark, rights-likeness | error | see above; verdict becomes `blocked` |
| contradiction | error | two incompatible terms in the positive text |
| negative-overlap | warning | a term is both wanted and excluded |
| too-short, too-long | warning | under 12 or over 200 words of positive text |
| filler-token | warning | words such as masterpiece, 8k, stunning, award-winning |

Verdict: `blocked` if any rights error; otherwise `revise` if any error or score under 70; otherwise `pass`.

## Contradiction pairs

Sun position against flat light (golden hour with overcast or noon); day against night; photographic against drawn or painted; macro against wide framing; wide lens (8 to 28 mm, wide-angle, fisheye) against long lens (130 mm and longer, telephoto); shallow against deep focus (f/1 to f/2.8 against f/11 and smaller); long exposure against frozen motion; black and white against colourful; minimal against crowded; high-key against low-key; soft against hard light; clear against stormy weather. Clauses that start with no, not, without, avoid or never are ignored, so "golden hour, no overcast sky" passes.
