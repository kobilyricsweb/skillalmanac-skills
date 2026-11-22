"""Generate a modular type scale as CSS custom properties.

Stdlib only. No network, no subprocess, no eval or exec. Inputs are read only.

Usage:
    python -I scripts/type_scale.py --base 16 --ratio 1.25 --below 2 --above 5
    python -I scripts/type_scale.py --config fixtures/scale_basic.json --out type-scale.css

Inputs: optional --config JSON object with keys base, ratio, below, above.
Scalar values only, file at most 2 MB. Command-line flags override config keys.
Output: a text table, a :root CSS block and a findings count on stdout.
With --out, only the :root block is written to that file; --out must be a new
file (an existing path is refused) and may not resolve to the config file.

Exit codes: 0 ok, 1 findings (a step is below 10 px or above 120 px),
2 usage or input error. Input errors print one JSON line to stderr.
"""

import argparse
import json
import math
import os
import sys
from pathlib import Path

MAX_BYTES = 2 * 1024 * 1024
MIN_PX = 10.0
MAX_PX = 120.0
DEFAULTS = {"base": "16", "ratio": "1.25", "below": "2", "above": "5", "root": "16"}
CONFIG_KEYS = ("base", "ratio", "below", "above", "root")
NAMED_RATIOS = {
    "minor-second": 1.067,
    "major-second": 1.125,
    "minor-third": 1.2,
    "major-third": 1.25,
    "perfect-fourth": 1.333,
    "augmented-fourth": 1.414,
    "perfect-fifth": 1.5,
    "golden": 1.618,
}
EXIT_OK = 0
EXIT_FINDINGS = 1
EXIT_ERROR = 2


class InputError(Exception):
    """A usage or input problem that is reported as one JSON line."""


def to_number(value, name, lo, hi):
    if isinstance(value, bool) or not isinstance(value, (int, float, str)):
        raise InputError(name + " must be a number")
    try:
        x = float(value)
    except (ValueError, OverflowError):
        raise InputError(name + " must be a number")
    if not math.isfinite(x) or x < lo or x > hi:
        raise InputError("%s must be between %s and %s" % (name, lo, hi))
    return x


def to_int(value, name, lo, hi):
    x = to_number(value, name, lo, hi)
    if not x.is_integer():
        raise InputError(name + " must be a whole number")
    return int(x)


def to_ratio(value):
    if isinstance(value, str) and value.strip().lower() in NAMED_RATIOS:
        return NAMED_RATIOS[value.strip().lower()]
    try:
        return to_number(value, "ratio", 1.05, 2.0)
    except InputError:
        raise InputError("ratio must be a number from 1.05 to 2.0 or a known name")


def read_config(path):
    p = Path(path)
    try:
        if p.stat().st_size > MAX_BYTES:
            raise InputError("config file is larger than 2 MB")
        raw = p.read_bytes()
    except OSError:
        raise InputError("config file cannot be read")
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        raise InputError("config file is not valid UTF-8")
    try:
        data = json.loads(text)
    except (ValueError, RecursionError, MemoryError):
        raise InputError("config file is not valid JSON")
    if not isinstance(data, dict):
        raise InputError("config must be a JSON object")
    for key, value in data.items():
        if key not in CONFIG_KEYS:
            raise InputError("unknown config key: " + str(key)[:40])
        if isinstance(value, (dict, list)):
            raise InputError("config values must be scalars, nesting is not allowed")
    return data


def check_out(out, config):
    resolved = Path(out).resolve()
    if config is not None:
        cfg = Path(config).resolve()
        same = resolved == cfg
        if not same and cfg.exists() and resolved.exists():
            same = os.path.samefile(str(resolved), str(cfg))
        if same:
            raise InputError("--out must not be the config file")
    if resolved.is_dir():
        raise InputError("--out is a directory")
    if resolved.exists():
        raise InputError("--out file already exists; choose a new file name")
    if not resolved.parent.is_dir():
        raise InputError("--out parent directory does not exist")
    return resolved


def line_height(px):
    if px <= 20.0:
        return 1.5
    if px <= 32.0:
        return 1.35
    return 1.2


def fmt(x, places):
    s = "%.*f" % (places, x)
    if "." in s:
        s = s.rstrip("0").rstrip(".")
    return s if s not in ("", "-0") else "0"


def tag(n):
    return "n%d" % -n if n < 0 else "%d" % n


def build_rows(base, ratio, below, above, root):
    rows = []
    for n in range(-below, above + 1):
        factor = ratio ** n
        px = base * factor
        rows.append({"step": n, "px": px, "rem": px / root, "lh": line_height(px)})
    return rows


def table_lines(base, ratio, rows, root):
    lines = ["type scale: base %spx, ratio %s, root %spx" % (fmt(base, 2), fmt(ratio, 4), fmt(root, 2))]
    lines.append("{:>5} {:>8} {:>8} {:>11}".format("step", "px", "rem", "line-height"))
    for r in rows:
        lines.append("{:>5} {:>8} {:>8} {:>11}".format(
            r["step"], fmt(r["px"], 2), fmt(r["rem"], 4), fmt(r["lh"], 2)))
    return lines


def css_block(rows, root):
    out = [":root {"]
    out.append("  /* rem assumes html font-size = %spx (root); set it or use px */" % fmt(root, 2))
    for r in rows:
        out.append("  --type-step-%s: %srem; /* %spx */" % (
            tag(r["step"]), fmt(r["rem"], 4), fmt(r["px"], 2)))
    for r in rows:
        out.append("  --type-line-%s: %s;" % (tag(r["step"]), fmt(r["lh"], 2)))
    out.append("}")
    return "\n".join(out)


def find_problems(rows):
    found = []
    for r in rows:
        if r["px"] < MIN_PX or r["px"] > MAX_PX:
            found.append("finding: step %d is %spx, outside %s to %s px" % (
                r["step"], fmt(r["px"], 2), fmt(MIN_PX, 0), fmt(MAX_PX, 0)))
    return found


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Generate a modular type scale as CSS custom properties.")
    parser.add_argument("--config", help="JSON object with keys base, ratio, below, above")
    parser.add_argument("--base", help="base size in px, 8 to 48")
    parser.add_argument("--ratio", help="number 1.05 to 2.0 or a name such as major-third")
    parser.add_argument("--below", help="steps below 0, whole number 0 to 6")
    parser.add_argument("--above", help="steps above 0, whole number 0 to 12")
    parser.add_argument("--root", help="html root font size in px that rem is measured against, 8 to 32 (default 16)")
    parser.add_argument("--out", help="write the :root block to this file")
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        return EXIT_OK if exc.code == 0 else EXIT_ERROR

    try:
        cfg = read_config(args.config) if args.config else {}
        cli = {"base": args.base, "ratio": args.ratio, "below": args.below, "above": args.above,
               "root": args.root}
        values = {}
        for key in CONFIG_KEYS:
            values[key] = cli[key] if cli[key] is not None else cfg.get(key, DEFAULTS[key])
        base = to_number(values["base"], "base", 8, 48)
        ratio = to_ratio(values["ratio"])
        below = to_int(values["below"], "below", 0, 6)
        above = to_int(values["above"], "above", 0, 12)
        root = to_number(values["root"], "root", 8, 32)
        out_path = check_out(args.out, args.config) if args.out else None
    except InputError as exc:
        sys.stderr.write(json.dumps({"error": str(exc)}) + "\n")
        return EXIT_ERROR

    rows = build_rows(base, ratio, below, above, root)
    css = css_block(rows, root)
    problems = find_problems(rows)

    if out_path is not None:
        try:
            with open(str(out_path), "x", encoding="utf-8", newline="\n") as fh:
                fh.write(css + "\n")
        except OSError:
            sys.stderr.write(json.dumps({"error": "cannot write the --out file"}) + "\n")
            return EXIT_ERROR

    lines = table_lines(base, ratio, rows, root)
    lines.append(css)
    lines.extend(problems)
    lines.append("findings: %d" % len(problems))
    sys.stdout.write("\n".join(lines) + "\n")
    return EXIT_FINDINGS if problems else EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
