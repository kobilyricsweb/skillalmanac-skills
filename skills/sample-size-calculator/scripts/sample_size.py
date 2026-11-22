"""Sample size calculator for two proportions, two means, or one mean.

Uses the normal approximation with statistics.NormalDist from the standard
library. Inputs come from command-line flags, from a JSON object file given
with --input (read only), or from both; flags override file values. Prints one
JSON object on stdout with sorted keys.

Exit codes: 0 result computed with no warnings, 1 result computed with at
least one warning, 2 usage or input error (one-line JSON error on stdout).
"""

import argparse
import json
import math
import os
import sys
from statistics import NormalDist

MAX_INPUT_BYTES = 2 * 1024 * 1024
MAX_NESTING = 8
MAX_N_PER_GROUP = 1000000000
MIN_EXPECTED_COUNT = 5
DESIGNS = ("two-proportions", "two-means", "one-mean")
DESIGN_KEYS = {
    "two-proportions": {"p1", "p2"},
    "two-means": {"delta", "sd"},
    "one-mean": {"delta", "sd"},
}
GROUPS = {"two-proportions": 2, "two-means": 2, "one-mean": 1}
COMMON_KEYS = {"design", "alpha", "power", "tails"}
ALL_KEYS = COMMON_KEYS | {"p1", "p2", "delta", "sd"}
FLAG_KEYS = ("design", "alpha", "power", "tails", "p1", "p2", "delta", "sd")


def fail(message):
    sys.stdout.write(json.dumps({"error": message}) + "\n")
    sys.exit(2)


class Parser(argparse.ArgumentParser):
    def error(self, message):
        fail("usage: " + message)


def nesting_depth(value):
    depth = 0
    stack = [(value, 1)]
    while stack:
        item, level = stack.pop()
        if level > depth:
            depth = level
        if isinstance(item, dict):
            stack.extend((child, level + 1) for child in item.values())
        elif isinstance(item, list):
            stack.extend((child, level + 1) for child in item)
    return depth


def read_input(path):
    try:
        size = os.path.getsize(path)
    except OSError:
        fail("input file not found or unreadable")
    if size > MAX_INPUT_BYTES:
        fail("input file exceeds 2 MB limit")
    try:
        with open(path, "rb") as handle:
            raw = handle.read(MAX_INPUT_BYTES + 1)
    except OSError:
        fail("input file not found or unreadable")
    if len(raw) > MAX_INPUT_BYTES:
        fail("input file exceeds 2 MB limit")
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        fail("input file is not valid UTF-8")
    try:
        data = json.loads(text)
    except (ValueError, RecursionError, MemoryError):
        fail("input file is not valid JSON")
    if not isinstance(data, dict):
        fail("input JSON must be an object")
    if nesting_depth(data) > MAX_NESTING:
        fail("input JSON nesting exceeds limit of 8")
    return data


def as_number(name, value):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        fail(name + " must be a number")
    number = float(value)
    if not math.isfinite(number):
        fail(name + " must be finite")
    return number


def validate(config):
    unknown = sorted(set(config) - ALL_KEYS)
    if unknown:
        fail("unknown key: " + str(unknown[0]))
    design = config.get("design")
    if not isinstance(design, str) or design not in DESIGNS:
        fail("design must be one of two-proportions, two-means, one-mean")
    needed = DESIGN_KEYS[design]
    for key in sorted(needed):
        if key not in config:
            fail("missing " + key + " for design " + design)
    other_keys = (DESIGN_KEYS["two-proportions"] | DESIGN_KEYS["two-means"]) - needed
    for key in sorted(other_keys):
        if key in config:
            fail(key + " is not used by design " + design)

    alpha = as_number("alpha", config.get("alpha", 0.05))
    if not 0 < alpha < 0.5:
        fail("alpha must satisfy 0 < alpha < 0.5")
    power = as_number("power", config.get("power", 0.80))
    if not 0.5 <= power < 1:
        fail("power must satisfy 0.5 <= power < 1")
    tails = as_number("tails", config.get("tails", 2))
    if tails not in (1.0, 2.0):
        fail("tails must be 1 or 2")
    tails = int(tails)

    values = {"alpha": alpha, "power": power, "tails": tails}
    if design == "two-proportions":
        p1 = as_number("p1", config["p1"])
        p2 = as_number("p2", config["p2"])
        if not (0 < p1 < 1 and 0 < p2 < 1):
            fail("p1 and p2 must satisfy 0 < value < 1")
        if p1 == p2:
            fail("p1 and p2 must differ")
        values["p1"] = p1
        values["p2"] = p2
    else:
        delta = abs(as_number("delta", config["delta"]))
        sd = as_number("sd", config["sd"])
        if delta == 0:
            fail("delta must be nonzero")
        if sd <= 0:
            fail("sd must be greater than 0")
        values["delta"] = delta
        values["sd"] = sd
    return design, values


def compute(design, values):
    norm = NormalDist()
    z_alpha = norm.inv_cdf(1 - values["alpha"] / values["tails"])
    z_beta = norm.inv_cdf(values["power"])
    if design == "two-proportions":
        p1, p2 = values["p1"], values["p2"]
        pbar = (p1 + p2) / 2
        numerator = (z_alpha * math.sqrt(2 * pbar * (1 - pbar))
                     + z_beta * math.sqrt(p1 * (1 - p1) + p2 * (1 - p2)))
        exact = (numerator / abs(p1 - p2)) ** 2
    elif design == "two-means":
        exact = 2 * ((z_alpha + z_beta) * values["sd"] / values["delta"]) ** 2
    else:
        exact = ((z_alpha + z_beta) * values["sd"] / values["delta"]) ** 2
    if not math.isfinite(exact) or exact > MAX_N_PER_GROUP:
        fail("required sample size exceeds 1000000000 per group")
    n_per_group = math.ceil(round(exact, 9))
    return z_alpha, z_beta, exact, n_per_group


def build_result(design, values):
    z_alpha, z_beta, exact, n_per_group = compute(design, values)
    groups = GROUPS[design]
    warnings = []
    smallest = None
    if design == "two-proportions":
        cell = min(values["p1"], 1 - values["p1"], values["p2"], 1 - values["p2"])
        smallest = round(n_per_group * cell, 2)
        if smallest < MIN_EXPECTED_COUNT:
            warnings.append(
                "smallest expected count per group is " + str(smallest)
                + " (below 5): the normal approximation is unreliable here; "
                "use an exact method such as Fisher exact test and review with a statistician")
    assumptions = [
        "Normal approximation; z quantiles from statistics.NormalDist.",
        "Normal approximation is poor when expected counts per group are below 5.",
        "Two-sided test." if values["tails"] == 2 else "One-sided test (tails 1).",
        "Result is the minimum per group; no dropout allowance is included.",
    ]
    if design == "two-proportions":
        assumptions.append("Independent groups with equal allocation (same n in each group).")
    elif design == "two-means":
        assumptions.append("Equal standard deviation in both groups and equal allocation.")
    else:
        assumptions.append("One group compared with a fixed reference value; sd is known or well estimated.")
    inputs = {key: values[key] for key in sorted(DESIGN_KEYS[design])}
    return {
        "design": design,
        "method": "normal approximation",
        "alpha": values["alpha"],
        "tails": values["tails"],
        "power": values["power"],
        "inputs": inputs,
        "z_alpha": round(z_alpha, 4),
        "z_beta": round(z_beta, 4),
        "groups": groups,
        "unrounded_per_group": round(exact, 4),
        "n_per_group": n_per_group,
        "n_total": n_per_group * groups,
        "smallest_expected_count": smallest,
        "assumptions": assumptions,
        "warnings": warnings,
    }


def main(argv):
    parser = Parser(description="Required sample size for two proportions, two means, or one mean.")
    parser.add_argument("--input", help="JSON object file, read only, 2 MB max")
    parser.add_argument("--design", help="two-proportions, two-means or one-mean")
    parser.add_argument("--alpha", type=float, help="significance level, default 0.05")
    parser.add_argument("--power", type=float, help="power, default 0.80")
    parser.add_argument("--tails", type=float, help="1 or 2, default 2")
    parser.add_argument("--p1", type=float, help="baseline proportion")
    parser.add_argument("--p2", type=float, help="alternative proportion")
    parser.add_argument("--delta", type=float, help="difference in means (sign ignored)")
    parser.add_argument("--sd", type=float, help="standard deviation")
    args = parser.parse_args(argv)

    config = read_input(args.input) if args.input is not None else {}
    for key in FLAG_KEYS:
        value = getattr(args, key)
        if value is not None:
            config[key] = value
    design, values = validate(config)
    result = build_result(design, values)
    sys.stdout.write(json.dumps(result, sort_keys=True) + "\n")
    return 1 if result["warnings"] else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
