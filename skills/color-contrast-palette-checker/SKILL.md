---
name: color-contrast-palette-checker
description: Checks foreground and background colour pairs against WCAG 2.x contrast thresholds and suggests the nearest passing foreground for each failing pair. Use when a palette, text colour, button colour or UI token needs a pass or fail check at the 4.5, 3 or 7 ratio levels from a list of hex pairs. Do not use for colour-blindness simulation, APCA scoring, contrast of photos or images, or choosing brand colours by taste.
license: Apache-2.0
compatibility: Python 3.9+ stdlib only, no network (type A)
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  author_model: claude-haiku-5-5
  version: "0.1.0"
  network: none
---

# Color contrast palette checker

Use this skill to turn a list of colour pairs into a pass or fail table. The script
computes the WCAG 2.x contrast ratio for each pair and reports four checks. It does
not judge whether a colour looks good; it only measures the ratio.

Script: `scripts/contrast_check.py` (run from the skill folder). Licence: `LICENSE.txt`.
Sample inputs: `fixtures/pairs_valid.txt` (five pairs, two fail normal text) and
`fixtures/pairs_invalid_hex.txt` (one bad hex value, used to test the error path).

## Input format

One pair per line:

    foreground,background[,label]

- Colours are hex with a leading `#`, either `#rgb` or `#rrggbb`. Case does not matter.
- `label` is optional, up to 80 characters, no control characters. Without a label the
  script writes `pair N`, where N is the count of pairs read so far.
- Blank lines are skipped. A comma inside the label is allowed; the label is everything
  after the second comma.
- Limits: 2 MB file size, 500 pairs, UTF-8 encoding (a byte-order mark is accepted).

## Workflow

1. **Validate the input file.** Check that every non-blank line has two hex values and
   that no value is missing its `#`. Output: the number of pairs you expect to see
   (non-blank lines). Do not fix values silently; report them.
2. **Run the script.** Command:

       python -I scripts/contrast_check.py <input-file>

   Output: the JSON report on stdout (keys in the contract below), and the exit code.
3. **Read the exit code.** Use the table in the Script contract. Exit 2 means stop: report
   the `message` and `line` keys from the error line and ask for a corrected file. Do not
   produce a palette verdict from a failed run.
4. **Build the pair table.** One row per pair, using the columns in the output contract.
   Show the ratio with two decimals, exactly as printed. Take every pass or fail decision
   from the boolean fields. The script decides on the unrounded ratio, so a displayed
   value near 4.5 can disagree with the rounded number; the boolean is the answer.
5. **List the fixes.** For each pair with `aa_normal` false, quote the `suggestion` and
   `suggestion_ratio`. Mark a pair as "no suggestion" when `suggestion` is null: no
   lightness value on that hue reaches 4.5.
6. **Write the verdict line.** Use the exact sentence in the output contract.

## Threshold table

| Check key | Ratio needed | Where it applies (WCAG 2.x) |
|-----------|--------------|------------------------------|
| `aa_normal` | 4.5 or more | Text below 18 pt, or below 14 pt bold (level AA) |
| `aa_large` | 3 or more | Text at 18 pt or larger, or 14 pt bold or larger (level AA) |
| `ui_component` | 3 or more | Borders, icons and states of UI components (level AA) |
| `aaa_normal` | 7 or more | Normal text, stricter level AAA |

A pair with `aa_normal` false is a finding. Exit code 1 means at least one finding.

Suggestion search (working value, not a published spec): HSL lightness moves in steps of
0.002 from the original foreground, keeping hue and saturation. The search runs toward
darker when the background is at least as light as the foreground, and lighter otherwise,
and also tries the opposite direction. The nearest passing colour in lightness wins.

## Output contract

The JSON report has these top-level keys, in this order: `status` (always `ok` on exit
0 or 1), `thresholds` (object with `aa_normal`, `aa_large`, `ui_component`, `aaa_normal`),
`pairs` (list), `summary` (object with `pairs`, `fail_aa_normal`, `pass_aa_normal`).

Each entry in `pairs` has these keys: `line`, `label`, `foreground`, `background`,
`ratio`, `aa_normal`, `aa_large`, `ui_component`, `aaa_normal`, `suggestion`,
`suggestion_ratio`. `suggestion` and `suggestion_ratio` are null when the pair passes
normal text.

The reply you write for the user uses these headings in this order:

1. `## Summary`: pairs checked, pairs failing normal text, exit code.
2. `## Pairs`: a table with the columns Label, Foreground, Background, Ratio, AA normal,
   AA large, UI, AAA, Suggestion. Use yes or no in the check columns.
3. `## Suggested fixes`: one bullet per failing pair in the form
   `label: foreground #xxxxxx -> #yyyyyy (ratio z.zz)`, or `no suggestion` when null.
4. `## Not checked`: the list of out-of-scope items named in Refuse / stop when.
5. A final line exactly: `Verdict: N of M pairs pass AA normal text.`

## Script contract

Arguments: one positional argument, the input file path. No options.

Exit codes:

| Code | Meaning |
|------|---------|
| 0 | All pairs pass AA normal text |
| 1 | At least one pair fails AA normal text (JSON report still printed) |
| 2 | Usage error, missing or unreadable file, bad hex, bad line, limit exceeded |

Error output is one JSON line on stdout: `{"status": "error", "message": "...", "line": N}`.
The `line` key is present only when a specific line is at fault. Usage errors from the
argument parser go to stderr with exit code 2.

The script opens the input read-only and writes nothing to disk.

## Refuse / stop when

- The request is for colour-blindness simulation (protanopia, deuteranopia and similar).
  The script does not implement it. Say so and stop that part.
- The request is for APCA or any contrast model other than WCAG 2.x. Stop and say the
  script only computes WCAG 2.x ratios.
- The input is a photo, screenshot or image file. The script reads only text lines of hex
  pairs; ask the user to list the colours they sampled.
- The input has more than 500 pairs or exceeds 2 MB. Split the file, then run once per part.
- The input has any invalid hex value. Stop with the exit 2 message; do not guess the
  intended colour.
- The user asks which colour is best for the brand. Report the ratios and stop there.
