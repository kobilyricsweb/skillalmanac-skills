---
name: unit-conversion-calculator
description: Converts values between common units of length, mass, volume, temperature, area, speed and data size using exact arithmetic, and shows the factor used. Use when a recipe, DIY project or homework problem needs a unit change such as miles to kilometers, Fahrenheit to Celsius or cups to milliliters, or when a conversion must be checked line by line. Do not use for currency, dry-ingredient weight from volume (no density data), time zones, or unit names outside the built-in table.
license: Apache-2.0
compatibility: Python 3.9+ stdlib only, no network (type A).
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  author_model: claude-haiku-5-5
  version: "0.1.0"
  network: none
---

# Unit Conversion Calculator

Convert each requested value with exact fractions, then show the result, the factor and the method. The script [scripts/convert.py](scripts/convert.py) does the arithmetic. The agent collects the requests, maps units to the table below, runs the script and checks the output.

## Workflow

1. **Collect the requests.** Output: a numbered list of requests, each as `<value> <from-unit> <to-unit>`. Turn sentences such as "how many ml in two cups" into one line each (`2 cup mL`).
2. **Map every unit to a symbol in the table below.** Output: the mapping, one line per request. Singular symbols only: "cups" becomes `cup`, "Mb" is not in the table and is reported as unknown.
3. **Write the requests to `<input-file>`.** Output: the path of a UTF-8 text file with one request per line. Use the user's file if they gave one; otherwise create the file in the user's working folder and state its path.
4. **Run the script on `<input-file>`.** Output: the exact command line and the exit code (see the script contract).
5. **Parse the JSON Lines.** Output: the results table defined in the output contract.
6. **Check every `ok` row.** For `multiplicative` rows, multiply the value by the printed factor and confirm it equals `result` after the rounding rule. For `affine` (temperature) rows, apply the formula once by hand: F to C is (F - 32) x 5 / 9; C to F is C x 9 / 5 + 32; K is C + 273.15. Output: "checked" or the row that failed.
7. **Report refusals and errors.** Output: each non-`ok` line with its status and message, plus the action taken.

## Units and factors

| Dimension | Symbols | Base unit for factors |
|---|---|---|
| length | m, cm, mm, km, in, ft, yd, mi | m |
| mass | g, mg, kg, t (metric tonne), oz (avoirdupois), lb | g |
| volume (US customary and metric) | mL, L, tsp, tbsp, floz, cup, pt, qt, gal | mL |
| area | m2, cm2, in2, ft2, yd2, ac, ha, km2, mi2 | m2 |
| speed | m/s, km/h, mph, kn | m/s |
| data, decimal (1000 per step) | B, kB, MB, GB, TB | B |
| data, binary (1024 per step) | KiB, MiB, GiB, TiB | B |
| temperature (affine, no factor) | C, F, K | not applicable |

A `cup` is 236.5882365 mL, a US customary value. The decimal data symbols (kB, MB, GB, TB) and the binary symbols (KiB, MiB, GiB, TiB) are never interchangeable: `1 MB` is 1000000 B and `1 MiB` is 1048576 B.

## Thresholds (working values)

| Check | Working value | What happens when exceeded |
|---|---|---|
| Input file size | 2 MB (2097152 bytes) | error code `input_too_large`, exit 2 |
| Value token length | 40 characters | status `bad_value` |
| Absolute value | 1e15 | status `bad_value` |
| Fields per request | exactly 3 | status `bad_format` |
| Result precision | at least 6 decimal places; 6 significant digits when the result is below 1 | rounding rule, not an error |
| Kelvin floor | 0 K (input below -273.15 C or -459.67 F, or negative kelvin) | status `refused`, message "below absolute zero" |

## Output contract

The script prints one JSON object per request. The agent turns them into this table for the user, in the same order:

| Line | Request | Result | Factor | Method | Status |
|---|---|---|---|---|---|

- `Line` is the `line` key (1-based line number in the input file).
- `Request` is `value from-unit to-unit` as typed.
- `Result` is the `result` key with the to-unit appended, for example `5.632704 km`. Empty when the status is not `ok`.
- `Factor` is the `factor` key, or `not applicable` for `affine` rows.
- `Method` is `multiplicative` or `affine`.
- `Status` is the `status` key.

Status values:

| status | Meaning | Script exit code |
|---|---|---|
| `ok` | converted | 0 when every line is `ok` |
| `refused` | units measure different quantities, or the value is below absolute zero | 1 |
| `unknown_unit` | a unit symbol is not in the table | 1 |
| `bad_value` | value is not a finite number within the thresholds, or has underscores | 1 |
| `bad_format` | the line does not have exactly three fields | 1 |

Error object (stdout, one line, exit 2): `{"status":"error","code":...,"message":...}` where `code` is one of `usage`, `missing_file`, `not_a_file`, `unreadable_file`, `input_too_large`, `invalid_utf8`, `empty_input`.

## Refuse or stop when

- A pair crosses dimensions, such as cups to grams, miles to seconds or Celsius to meters. Report `refused`; never convert through density or an assumed ingredient weight.
- The user wants dry-ingredient weight from a volume (flour cups to grams). The table has no density data. Refuse and say so.
- A unit is not in the table, such as `cups`, `Mb` or `pounds`. Stop for that line, report `unknown_unit` and name the closest table symbol. Do not guess a factor.
- The script exits 2. Stop, report the `code` and the `message`, and do not retry with a guessed path.
- A value is outside the thresholds. Report `bad_value`; do not round or truncate it yourself.
- The request is for currency, time zones or any quantity not in the table.

## Script contract

- File: `scripts/convert.py`, relative to the skill folder.
- Arguments: exactly one, `<input-file>`, a UTF-8 text file (a leading byte order mark is accepted).
- Exact command line: `python -I "<skill-folder>/scripts/convert.py" "<input-file>"`
- Output on stdout: JSON Lines with the keys `line`, `status`, `value`, `from`, `to`, `dimension`, `result`, `factor`, `method`, `message`. Unused keys are `null`.
- Exit 0: every request is `ok`. Exit 1: at least one request is `refused`, `unknown_unit`, `bad_value` or `bad_format`. Exit 2: usage or file error; one-line JSON error object.
- Read-only. The script never writes files, uses the network or runs subprocesses.

## Shipped files

- [scripts/convert.py](scripts/convert.py): the converter.
- [fixtures/smoke_requests.txt](fixtures/smoke_requests.txt): four requests, three `ok` and one `refused`, for a quick check.
- [fixtures/edge_requests.txt](fixtures/edge_requests.txt): one line per error path (`refused`, `bad_value`, `unknown_unit`, `bad_format`, identity conversion).
- [LICENSE.txt](LICENSE.txt): Apache-2.0 license text.
