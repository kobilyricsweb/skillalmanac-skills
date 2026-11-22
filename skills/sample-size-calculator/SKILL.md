---
name: sample-size-calculator
description: Computes the minimum number of subjects per group for a planned comparison of two proportions, two means, or one mean, using the normal approximation in a stdlib Python script. Use when a researcher needs n before collecting data, already has alpha, power and an effect size (p1 and p2, or delta and sd), and wants a reproducible number with its assumptions and warnings printed. Do not use for post-hoc power of a finished study, for survival or time-to-event designs, for clustered, stepped-wedge or repeated-measures designs, or for choosing an effect size to reach a wanted n.
license: Apache-2.0
compatibility: Python 3.9+ stdlib only, no network (type A).
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  author_model: claude-haiku-5-5
  version: "0.1.0"
  network: none
---

# Sample size calculator

Computes the minimum n per group for a planned two-group or one-group comparison. The script does the arithmetic. The agent picks the design, checks inputs against the ranges below, runs the script once, and reports the result together with its assumptions and warnings. The agent never adjusts the script's output by hand.

## Workflow

1. Identify the design with the design table. Output: the design name and the list of inputs it needs.
2. Collect inputs. Ask only for values that are missing. Output: an inputs table with each value and its source ("given by user" or "working value").
3. Check every value against the input range table. Output: "inputs valid", or the first failing field with its rule. If a field fails, stop.
4. Run the script once with the command in the Script contract. Output: the raw JSON line and the exit code.
5. Act on the exit code: 0 means report the result; 1 means report the result and copy every entry of `warnings`; 2 means report the `error` string and do not invent a value.
6. Write the report in the output contract below. Output: the report only, with no extra sections.

## Design table

| design | required inputs | groups | formula in the script |
|---|---|---|---|
| two-proportions | p1, p2 | 2 | pbar = (p1+p2)/2; n = (za*sqrt(2*pbar*(1-pbar)) + zb*sqrt(p1*(1-p1)+p2*(1-p2)))^2 / (p1-p2)^2 |
| two-means | delta, sd | 2 | n = 2*((za+zb)*sd/delta)^2 |
| one-mean | delta, sd | 1 | n = ((za+zb)*sd/delta)^2 |

za is the inverse normal of 1 - alpha/tails. zb is the inverse normal of power. Use two-means only when both groups share one standard deviation. Unequal group sizes and unequal standard deviations are outside this skill.

## Input range table

| input | allowed | value used when omitted |
|---|---|---|
| alpha | 0 < alpha < 0.5 | 0.05 (common working value) |
| power | 0.5 <= power < 1 | 0.80 (common working value) |
| tails | 1 or 2 | 2 |
| p1, p2 | 0 < value < 1, and p1 != p2 | none, required |
| delta | nonzero; sign is ignored | none, required |
| sd | greater than 0 | none, required |

Keys that the chosen design does not use are errors, not ignored. Name the common defaults as working values in the report; they are not industry mandates.

## Warning and limit table

| condition | script behaviour | exit code |
|---|---|---|
| proportions: n_per_group times the smallest of p1, 1-p1, p2, 1-p2 is below 5 | result printed, warning added | 1 |
| n_per_group above 1000000000 | refused | 2 |
| input file over 2 MB, nesting deeper than 8, invalid UTF-8, invalid JSON | refused | 2 |

## Script contract

Path: `scripts/sample_size.py`, run from the skill folder.

Exact command for the standard two-proportion case:

    python -I scripts/sample_size.py --design two-proportions --p1 0.30 --p2 0.40 --alpha 0.05 --power 0.80

Arguments: `--input PATH` (JSON object file, read only), `--design`, `--alpha`, `--power`, `--tails`, `--p1`, `--p2`, `--delta`, `--sd`. Flags override values read from `--input`.

Stdout is one JSON line with sorted keys: `alpha`, `assumptions`, `design`, `groups`, `inputs`, `method`, `n_per_group`, `n_total`, `power`, `smallest_expected_count`, `tails`, `unrounded_per_group`, `warnings`, `z_alpha`, `z_beta`. On error stdout is `{"error": "<message>"}`.

Exit codes: 0 computed, no warnings. 1 computed, at least one warning (result still printed). 2 usage or input error.

## Output contract

Use these headings in this order, and nothing else:

### Result
- Design: <design>
- Groups: <groups>
- Required n per group: <n_per_group> (unrounded <unrounded_per_group>)
- Total: <n_total>

### Inputs
A table with columns: name | value | source.

### Assumptions
The `assumptions` array copied unchanged, one bullet per entry.

### Warnings
The `warnings` array copied unchanged, or the single word "None".

### Not covered
Dropout allowance, multiple comparisons, clustering, unequal allocation. State each as not included.

## Refuse / stop when

- The user wants post-hoc power for a finished study, or a sample size picked to reach a p-value.
- The user asks you to invent p1, p2, delta or sd so that a wanted n comes out. Ask for the effect size instead.
- The design is clustered, stepped-wedge, repeated-measures, survival or time-to-event.
- Group sizes must be unequal, or the two groups have different standard deviations.
- Any input fails the range table, or a key is unknown (exit 2).
- Exit 1 with a small-count warning: report the number, but label it unreliable and recommend an exact method. Do not present it as final.
- The script reports an error for n above 1000000000: say the effect size is implausibly small and ask the user to confirm it.

## Files

- `SKILL.md`: this file.
- `LICENSE.txt`: Apache-2.0 text.
- `scripts/sample_size.py`: the calculator described above.
- `fixtures/proportions_smoke.json`, `fixtures/means_smoke.json`, `fixtures/small_counts.json`, `fixtures/bad_unknown_key.json`: input files used in verification.
