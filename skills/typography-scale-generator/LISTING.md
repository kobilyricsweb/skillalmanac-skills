# Typography Scale Generator

## One line

Builds one geometric type scale from a base size and ratio and prints it as px and rem values, suggested line-heights, and a `:root` block of CSS custom properties.

## What it does

The skill takes a base size in pixels, a ratio (either a number between 1.05 and 2.0 or one of eight named ratios), and how many steps to produce below and above the base. The bundled script `scripts/type_scale.py` computes each step as base times ratio to the power of the step number, then reports the px size, the rem size, and a suggested line-height from a three-band rule (1.5 up to 20 px, 1.35 up to 32 px, 1.2 above that). It prints a table, a `:root` block with one size token and one line-height token per step, and a count of findings for any step that falls below 10 px or above 120 px. A config file or a flag set can supply the values, and an optional output file, which must be a new file, receives the CSS block only.

## When to use

Use it when a theme needs a consistent set of font sizes and the user wants the arithmetic done once and written out, for example when setting up heading and body tokens for a small web page, a style guide draft, or a document template. It also fits a request to compare two ratios, since the same base can be run twice with different values and the two tables read side by side.

## When not to use

Do not use it for choosing typefaces, for grid or layout CSS, for fluid sizes that scale with the viewport, or for sizes that follow no fixed ratio. The line-height bands are working values chosen for this package and are not a published standard, so they should be checked against the actual typeface before release.

## Requirements

Python 3.9 or newer, standard library only. No network access, no packages to install. Runs on any operating system with a Python interpreter.

## Example

The smoke run used base 16, ratio 1.25, two steps below and five above:

```
type scale: base 16px, ratio 1.25, root 16px
 step       px      rem line-height
   -2    10.24     0.64         1.5
   -1     12.8      0.8         1.5
    0       16        1         1.5
    1       20     1.25         1.5
    2       25   1.5625        1.35
    3    31.25   1.9531        1.35
    4    39.06   2.4414         1.2
    5    48.83   3.0518         1.2
:root {
  /* rem assumes html font-size = 16px (root); set it or use px */
  --type-step-n2: 0.64rem; /* 10.24px */
  --type-step-n1: 0.8rem; /* 12.8px */
  --type-step-0: 1rem; /* 16px */
  --type-step-1: 1.25rem; /* 20px */
  --type-step-2: 1.5625rem; /* 25px */
  --type-step-3: 1.9531rem; /* 31.25px */
  --type-step-4: 2.4414rem; /* 39.06px */
  --type-step-5: 3.0518rem; /* 48.83px */
  --type-line-n2: 1.5;
  --type-line-n1: 1.5;
  --type-line-0: 1.5;
  --type-line-1: 1.5;
  --type-line-2: 1.35;
  --type-line-3: 1.35;
  --type-line-4: 1.2;
  --type-line-5: 1.2;
}
findings: 0
```

## Limits

The script handles one scale per run and has no notion of a heading hierarchy, so the choice of which step becomes a heading is left to the reader. The rem values are measured against the root font size you pass with `--root` (default 16 px, the usual browser default), so a base of 18 px on a 16 px root gives 1.125rem at step 0. If your page sets a different html font-size, pass it as `--root`, or use the px values in the comments. The ratio names are a short working list, and the script does not accept arbitrary names. Line-height values are coarse bands rather than a fitted function of typeface metrics. Input files are capped at 2 MB and must hold scalar values only.

## Status

Provisional. Lint-clean, one smoke run. Not independently verified.
