# Color contrast palette checker

## One line

Checks a list of foreground and background hex pairs against the WCAG 2.x contrast levels and suggests the nearest passing text colour for each failing pair.

## What it does

The skill runs a small Python script over a plain text file. Each line holds one pair, written as a foreground colour, a background colour and an optional label. The script converts each hex value to relative luminance, computes the WCAG 2.x contrast ratio, and reports four yes or no checks: normal text at 4.5, large text at 3, UI components at 3, and stricter normal text at 7.

For every pair that fails normal text, the script searches for the nearest foreground colour that passes. It keeps the hue and saturation of the original colour and moves only its HSL lightness, in small steps, toward darker or lighter. The first passing value in either direction is the suggestion, and its ratio is printed next to it. When no lightness on that hue reaches 4.5, the suggestion is null, and the report says so by leaving the field empty.

The output is one JSON report with a summary, so an agent can build a table or a short list of fixes without parsing free text. Invalid input stops the run with a single error line and exit code 2, so a typo in one hex value cannot silently change the result.

## When to use

Use it when a set of colours is about to ship as text on a background, such as a button palette, a set of tags or a dark-mode theme, and someone needs the ratios written down before a review. It also fits a short audit of a design token list, where the input is simply the pairs already in use.

## When not to use

Do not use it to simulate colour blindness, to score contrast with APCA, or to check photographs and screenshots. It does not pick brand colours and it does not judge whether a palette looks good. Its suggestions move lightness only, so a suggested colour should be looked at by a person before it replaces a brand colour.

## Requirements

Python 3.9 or newer, standard library only. No network access, no packages to install. The script reads one file of at most 2 MB and at most 500 pairs. The input must be UTF-8.

## Example

Command run on the bundled sample file `fixtures/pairs_valid.txt`:

    python -I scripts/contrast_check.py fixtures/pairs_valid.txt

Output, pasted verbatim from the smoke run (exit code 1):

```json
{
  "status": "ok",
  "thresholds": {
    "aa_normal": 4.5,
    "aa_large": 3.0,
    "ui_component": 3.0,
    "aaa_normal": 7.0
  },
  "pairs": [
    {
      "line": 1,
      "label": "grey body text on white",
      "foreground": "#777777",
      "background": "#ffffff",
      "ratio": 4.48,
      "aa_normal": false,
      "aa_large": true,
      "ui_component": true,
      "aaa_normal": false,
      "suggestion": "#767676",
      "suggestion_ratio": 4.54
    },
    {
      "line": 2,
      "label": "black on white",
      "foreground": "#000000",
      "background": "#ffffff",
      "ratio": 21.0,
      "aa_normal": true,
      "aa_large": true,
      "ui_component": true,
      "aaa_normal": true,
      "suggestion": null,
      "suggestion_ratio": null
    },
    {
      "line": 3,
      "label": "brand blue on white",
      "foreground": "#1a5fb4",
      "background": "#ffffff",
      "ratio": 6.29,
      "aa_normal": true,
      "aa_large": true,
      "ui_component": true,
      "aaa_normal": false,
      "suggestion": null,
      "suggestion_ratio": null
    },
    {
      "line": 4,
      "label": "white on navy button",
      "foreground": "#ffffff",
      "background": "#0b3d91",
      "ratio": 10.04,
      "aa_normal": true,
      "aa_large": true,
      "ui_component": true,
      "aaa_normal": true,
      "suggestion": null,
      "suggestion_ratio": null
    },
    {
      "line": 5,
      "label": "pink tag on charcoal",
      "foreground": "#ff00aa",
      "background": "#222222",
      "ratio": 4.42,
      "aa_normal": false,
      "aa_large": true,
      "ui_component": true,
      "aaa_normal": false,
      "suggestion": "#ff10af",
      "suggestion_ratio": 4.5
    }
  ],
  "summary": {
    "pairs": 5,
    "fail_aa_normal": 2,
    "pass_aa_normal": 3
  }
}
```

The grey pair fails normal text at 4.48 and the suggested #767676 reaches 4.54. The file also contains a bad value; running `fixtures/pairs_invalid_hex.txt` prints `{"status": "error", "message": "invalid hex colour: '#00g' (use #rgb or #rrggbb)", "line": 2}` and exits 2.

## Limits

The suggestion search is a working value, not a published rule. It uses lightness steps of 0.002 and tries both directions, so it can return a colour that is far from the brand hue. Ratios are shown with two decimals, while the pass or fail flag uses the unrounded value. The script knows only WCAG 2.x. It does not check colour-blindness, APCA, gradients, transparency or text over images, and it cannot tell which pairs will really appear together on a page.

## Status

Provisional. Lint-clean, one smoke run. Not independently verified.
