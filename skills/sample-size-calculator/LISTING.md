# Sample size calculator

## One line

Computes the minimum subjects per group for a planned comparison of two proportions, two means, or one mean, with its assumptions printed.

## What it does

The skill gives an agent a fixed procedure for sizing a study before data collection. The agent identifies the design (two proportions, two means with a shared standard deviation, or one mean against a reference value), checks alpha, power, tails and the effect inputs against written ranges, and runs a Python script that uses the normal approximation. The script rounds the unrounded requirement up to a whole number per group and reports the total. It also prints the assumptions behind the number, and when the smallest expected cell count per group falls below 5 it returns a warning and exit code 1, because the normal approximation is weak at that size.

Inputs can come from flags, from a JSON object file, or from both, with flags taking precedence. Unknown keys, keys that the chosen design does not use, out-of-range values, non-finite numbers, oversized or deeply nested files and invalid UTF-8 all stop the run with a one-line JSON error and exit code 2.

## When to use

Use it when a researcher or analyst has an effect size in hand, for example a baseline conversion rate and the rate they hope to detect, or a mean difference with a known standard deviation, and needs the group size before fieldwork starts. It suits planning memos where the reader wants the arithmetic reproducible.

## When not to use

Do not use it for power of a finished study, for choosing an effect size until a target n appears, for clustered or repeated-measures designs, for survival endpoints, or for small-count exact tests. The skill refuses those cases in its own refusal list.

## Requirements

Python 3.9 or later, standard library only (argparse, json, math, os, sys and statistics). No network access, no packages to install, no write access to the input files.

## Example

Command run from the skill folder:

    python -I scripts/sample_size.py --design two-proportions --p1 0.30 --p2 0.40 --alpha 0.05 --power 0.80

Output, verbatim from the smoke run:

    {"alpha": 0.05, "assumptions": ["Normal approximation; z quantiles from statistics.NormalDist.", "Normal approximation is poor when expected counts per group are below 5.", "Two-sided test.", "Result is the minimum per group; no dropout allowance is included.", "Independent groups with equal allocation (same n in each group)."], "design": "two-proportions", "groups": 2, "inputs": {"p1": 0.3, "p2": 0.4}, "method": "normal approximation", "n_per_group": 356, "n_total": 712, "power": 0.8, "smallest_expected_count": 106.8, "tails": 2, "unrounded_per_group": 355.9428, "warnings": [], "z_alpha": 1.96, "z_beta": 0.8416}

Exit code 0. The unrounded value 355.9428 rounds up to 356 per group.

## Limits

The normal approximation is a planning estimate. It is weak when expected counts are small, and the script only flags that for proportion designs. It assumes independent observations, equal allocation and, for means, one common standard deviation. It does not add a dropout allowance, adjust for multiple comparisons, or handle clustering. Alpha and power defaults (0.05 and 0.80) are working values that the user must confirm. The script refuses required sizes above 1000000000 per group.

## Status

Provisional. Lint-clean, one smoke run. Not independently verified.
