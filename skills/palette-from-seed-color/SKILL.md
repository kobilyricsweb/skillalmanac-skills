---
name: palette-from-seed-color
description: Builds a seven-color palette from one hex seed color, keeping the seed hue and saturation across five lightness steps plus a complement and an analogous color, and reports WCAG contrast of each color against white and black. Use when a designer or developer needs accessible tints, shades, or harmony colors from one brand color, or needs to know which text color passes 4.5:1 or 7:1 on each swatch. Do not use for picking brand colors, judging aesthetics, reading colors from images or screenshots, or exporting full design-system tokens.
license: Apache-2.0
compatibility: Python 3.9+ stdlib only, no network (type A).
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  author_model: claude-haiku-5-5
  version: "0.1.0"
  network: none
---

# Palette from seed color

This skill runs [scripts/palette.py](scripts/palette.py) on one hex seed and reports the palette as a table or JSON. The script only reads its input and prints to stdout. It never writes files.

## Workflow

1. **Get the seed.** Accept 6 hex digits with an optional leading `#`, in any letter case. Output: the seed as `#rrggbb`. Reject 3-digit shorthand, named colors, and rgb() notation; ask the user for the 6-digit hex.
2. **Run the script** with the seed as an argument, or with `--seed-file` pointing at a text file whose first non-empty line is the seed. Use the command lines in the Script contract below. Output: stdout table or JSON, plus an exit code.
3. **Branch on the exit code.** 0 means every color has a pairing at or above `--min-ratio`. 1 means at least one color is a finding; list the finding names. 2 means usage or input error; report the `code` from stderr and stop.
4. **Label each contrast value** with the threshold table below. Do not recompute ratios by hand; quote the script values.
5. **Write the reply** in the Output contract. Keep the script output verbatim in a fenced block, then add the labeled summary.

## Threshold and palette tables

| Contrast ratio | Label | Permitted use |
|---|---|---|
| 7.0 or more | AAA | Text at any size |
| 4.5 to under 7.0 | AA | Body text |
| 3.0 to under 4.5 | AA-large | Large text only (18 pt regular or 14 pt bold) |
| under 3.0 | fail | Not for text |

The four labels follow the published WCAG 2.x thresholds.

| Palette role | HSL lightness | Hue and saturation source |
|---|---|---|
| step-15 | 15% | Seed hue and saturation |
| step-30 | 30% | Seed hue and saturation |
| step-50 | 50% | Seed hue and saturation |
| step-70 | 70% | Seed hue and saturation |
| step-90 | 90% | Seed hue and saturation |
| complement | Seed lightness | Seed hue plus 180 degrees |
| analogous-30 | Seed lightness | Seed hue plus 30 degrees |

The five step lightness values are working values, not a published standard.

| Finding setting | Value | Status |
|---|---|---|
| `--min-ratio` default | 7.0 | Working value; a color with no pairing at 7.0 or more is a finding |
| `--min-ratio` allowed range | 1 to 21 | Fixed by the script; outside it the script exits 2 |

Under the fixed formula the better of white or black never falls below 4.58, so `--min-ratio 4.5` cannot produce a finding. Use 7.0 when the question is whether any text pairing is strong.

## Output contract

Table output (default) has this shape:

```
seed #rrggbb  min-ratio 7.00
name           hex       white label      black label     best
<7 data rows, one per palette role>
findings: none            (or: findings: <comma-separated names>)
```

Columns: `name`, `hex`, `white` (ratio), `label`, `black` (ratio), `label`, `best` (`white` or `black`).

JSON output (`--format json`) has these keys:
- top level: `seed`, `min_ratio`, `colors`, `findings`
- each entry of `colors`: `name`, `hex`, `white_ratio`, `white_label`, `black_ratio`, `black_label`, `best_text`, `best_ratio`
- `findings`: list of color names below the threshold; empty when none

Error output goes to stderr as one line of JSON: `{"error": "<message>", "code": "<CODE>"}`.

| Code | Exit | Meaning |
|---|---|---|
| E_USAGE | 2 | Arguments invalid, both or neither seed given, or `--min-ratio` out of range |
| E_BAD_HEX | 2 | Seed is not 6 hex digits |
| E_FILE_NOT_FOUND | 2 | `--seed-file` path does not exist |
| E_FILE_READ | 2 | `--seed-file` path exists but cannot be read (for example a directory) |
| E_FILE_TOO_LARGE | 2 | `--seed-file` is over 2 MB |
| E_FILE_ENCODING | 2 | `--seed-file` is not valid UTF-8 |
| E_FILE_EMPTY | 2 | `--seed-file` has no non-empty line |

## Script contract

- Script: `scripts/palette.py`. Python 3.9+, standard library only, no network, no subprocess, read-only.
- Arguments: exactly one of `<hex-seed>` (positional) or `--seed-file <input-file>`; optional `--format table|json` (default `table`); optional `--min-ratio <number>` (default 7.0).
- Exit codes: 0 ok, 1 findings, 2 usage or input error.
- Command, seed inline: `python -I scripts/palette.py <hex-seed> --format json`
- Command, seed from file: `python -I scripts/palette.py --seed-file <input-file> --min-ratio 7.0`
- Fixtures for a smoke run: `fixtures/seed_valid.txt` (expected exit 1 at the default threshold) and `fixtures/seed_bad.txt` (expected exit 2, E_BAD_HEX).

## Refuse or stop when

- The seed is not 6 hex digits, or the file is over 2 MB, not UTF-8, or empty. Stop, report the error code, and ask for a corrected seed.
- The user supplies an image, a screenshot, or a color name and asks for its hex. Stop and ask for the hex value.
- The user asks which brand color to choose, whether the palette looks good, or for a full token export such as CSS variables for a whole product. Refuse; this skill covers the palette and contrast values only.
- The user asks for a `--min-ratio` outside 1 to 21. Stop and report E_USAGE.
- The user asks for contrast numbers that the script did not produce. Run the script first, or say the value is not available.

## Shipped files

- `scripts/palette.py`: the palette and contrast script described above.
- `fixtures/seed_valid.txt`: a valid seed file for a smoke run.
- `fixtures/seed_bad.txt`: an invalid seed file for an error-path run.
- `LICENSE.txt`: Apache License 2.0 text.
