# Unit Conversion Calculator

## One line

Exact conversions for length, mass, volume, temperature, area, speed and data size, with the factor printed next to each result.

## What it does

The skill takes a short list of requests, each written as a value, a source unit and a target unit. A stdlib-only Python script reads the list and converts each line with Python fractions, so no rounding happens until the final result is printed. Each result carries the factor used, so the arithmetic can be checked by hand. Temperature uses the affine formulas for Fahrenheit, Celsius and kelvin rather than a factor. Data sizes keep the decimal units (kB, MB, GB, TB) apart from the binary ones (KiB, MiB, GiB, TiB), so a gigabyte and a gibibyte never get mixed up. Requests that cross dimensions, such as cups to grams, are refused with a plain message instead of a guessed answer. The script never writes files and never touches the network.

## When to use

Use it for recipe scaling, home-improvement measurements, homework that asks for a unit change, and checking a conversion someone else already made. It suits a short list of conversions where each line must be traceable.

## When not to use

Do not use it for currency, time zones, or dry ingredients where the answer depends on density, such as flour cups to grams. Units outside the built-in table are not supported, and plural forms such as "cups" are reported as unknown rather than corrected.

## Requirements

Python 3.9 or newer. No third-party packages and no network access. The skill runs on any machine that has a Python interpreter.

## Example

Input file with four requests (smoke fixture), run with `python -I "<skill-folder>/scripts/convert.py" "<input-file>"`:

```
{"line":2,"status":"ok","value":"3.5","from":"mi","to":"km","dimension":"length","result":"5.632704","factor":"1.609344","method":"multiplicative","message":null}
{"line":3,"status":"ok","value":"350","from":"F","to":"C","dimension":"temperature","result":"176.666667","factor":null,"method":"affine","message":null}
{"line":4,"status":"ok","value":"2","from":"cup","to":"mL","dimension":"volume","result":"473.176473","factor":"236.5882365","method":"multiplicative","message":null}
{"line":5,"status":"refused","value":"2","from":"cup","to":"g","dimension":null,"result":null,"factor":null,"method":null,"message":"cannot convert volume to mass: different quantities"}
```

The script exits 1 for this input because one line is refused.

## Limits

Values are capped at an absolute value of 1e15 and a token length of 40 characters, both working values. Input files are capped at 2 MB. Each request must have exactly three fields. The unit table has 48 symbols; it does not cover fuel economy, pressure, energy or time. Results are rounded to at least six decimal places, with six significant digits for values below 1.

## Status

Provisional. Lint-clean, one smoke run. Not independently verified.
