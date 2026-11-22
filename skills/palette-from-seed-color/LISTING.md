# Palette from seed color

## One line

Turns one hex seed color into seven palette colors and reports the WCAG contrast of each against white and black.

## What it does

The skill takes one six-digit hex seed such as `#2a6fdb`. It converts the seed to HSL, keeps its hue and saturation, and produces five lightness steps at 15, 30, 50, 70 and 90 percent. It then adds two harmony colors: a complement at the seed hue plus 180 degrees, and an analogous color at the seed hue plus 30 degrees. Both harmony colors keep the seed's own lightness. For each of the seven colors, the script computes the WCAG 2.x contrast ratio against white and against black, labels each ratio as AAA, AA, AA-large or fail, and names the better text color. A color is listed as a finding when neither text color reaches the threshold, which defaults to 7.0 and can be changed with `--min-ratio`. The output is a fixed-width table or JSON. Invalid seeds, missing files, oversized files and bad encodings stop the run with one line of JSON on stderr and exit code 2.

## When to use

Use this skill when a designer or developer has one brand color and needs a small set of tints, shades and harmony colors that are already checked for text contrast. It fits a quick check of a new accent, a set of button or badge backgrounds, or a question such as whether a mid-lightness blue can carry white text. The output names exact hex values and ratios, so a reviewer can paste the table into a design note without retyping numbers.

## When not to use

Do not use this skill to choose a brand color, judge whether a palette looks good, or read colors from an image. It does not produce full design-system tokens, does not handle dark-mode pairs separately, and does not check colors used as borders, icons or chart series. The five lightness steps are fixed working values, so a seed whose best tint needs a different lightness will not get one.

## Requirements

Python 3.9 or later with the standard library. No network access and no third-party packages. The script reads one seed from the command line or from a text file and writes to stdout. It does not write files.

## Example

Command run on the smoke seed, with the default threshold:

```
python -I scripts/palette.py 2a6fdb
```

Verbatim output (exit code 1, because step-50 has no text pairing at 7.0):

```
seed #2a6fdb  min-ratio 7.00
name           hex       white label      black label     best  
step-15        #0b2041   16.19 AAA         1.30 fail      white 
step-30        #164183    9.92 AAA         2.12 fail      white 
step-50        #256cda    4.96 AA          4.24 AA-large  white 
step-70        #7ca7e9    2.45 fail        8.56 AAA       black 
step-90        #d3e2f8    1.31 fail       16.00 AAA       black 
complement     #db962a    2.50 fail        8.41 AAA       black 
analogous-30   #3e2adb    8.21 AAA         2.56 fail      white 
findings: step-50
```

## Limits

The lightness steps and the default 7.0 finding threshold are working values. The script checks only text contrast on the seven generated swatches and on white and black. It assumes sRGB input and does not model color blindness, print output or display calibration. It accepts only six-digit hex, so shorthand such as `#2af` fails with E_BAD_HEX. Seed files are capped at 2 MB, and only the first non-empty line is read.

## Status

Provisional. Lint-clean, one smoke run. Not independently verified.
