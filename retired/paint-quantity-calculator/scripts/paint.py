"""paint-quantity-calculator: estimate wall paint for one room.

Usage:
    python -I scripts/paint.py <input-file>

The input file is one JSON object (UTF-8, at most 2 MB). The report is
written to stdout as plain text. Exit codes: 0 no findings, 1 findings
reported, 2 usage or input error. Errors are one JSON line on stderr:
{"error": "<CODE>", "detail": "<text>"}.

Read-only: writes no files, opens no network connections, starts no processes.
"""
import json
import math
import sys

VERSION = "0.1.0"
MAX_BYTES = 2 * 1024 * 1024
FT_PER_M = 3.28084
M_PER_FT = 0.3048

ALLOWED = {
    "units", "length", "width", "height", "doors", "door_area",
    "windows", "window_area", "coats", "coverage", "waste_percent", "rounding",
}
REQUIRED = {"units", "length", "width", "height", "doors", "windows", "coats"}

# Working values (not published specs). Feet and meter variants.
DEFAULTS = {
    "ft": {"door_area": 21.0, "window_area": 15.0, "coverage": 350.0},
    "m": {"door_area": 1.95, "window_area": 1.39, "coverage": 32.5},
}
WASTE_DEFAULT = 10.0
OPENINGS_LIMIT_SHARE = 0.50
HEIGHT_MIN_FT = 6.0
HEIGHT_MAX_FT = 20.0


class InputError(Exception):
    def __init__(self, code, detail):
        super().__init__(detail)
        self.code = code
        self.detail = detail


def fail(code, detail):
    raise InputError(code, detail)


def load(path):
    try:
        with open(path, "rb") as handle:
            raw = handle.read(MAX_BYTES + 1)
    except FileNotFoundError:
        fail("E_MISSING_FILE", "input file not found")
    except OSError:
        fail("E_READ", "input file could not be read")
    if len(raw) > MAX_BYTES:
        fail("E_TOO_LARGE", "input file is larger than 2 MB")
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        fail("E_INVALID_UTF8", "input file is not valid UTF-8")
    try:
        data = json.loads(text)
    except (ValueError, RecursionError):
        fail("E_INVALID_JSON", "input file is not valid JSON")
    if not isinstance(data, dict):
        fail("E_FIELD", "top-level JSON value must be an object")
    return data


def get_number(data, key, low, high):
    value = data[key]
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        fail("E_FIELD", f"{key} must be a number")
    if not math.isfinite(value) or not low <= value <= high:
        fail("E_FIELD", f"{key} must be between {low} and {high}")
    return float(value)


def get_int(data, key, low, high):
    value = data[key]
    if isinstance(value, bool) or not isinstance(value, int):
        fail("E_FIELD", f"{key} must be a whole number")
    if not low <= value <= high:
        fail("E_FIELD", f"{key} must be between {low} and {high}")
    return value


def optional_number(data, key, low, high, default, default_label):
    if key in data:
        return get_number(data, key, low, high), "user"
    return default, default_label


def run(path):
    data = load(path)
    unknown = sorted(set(data) - ALLOWED)
    if unknown:
        fail("E_FIELD", f"unknown field: {unknown[0]}")
    missing = sorted(REQUIRED - set(data))
    if missing:
        fail("E_FIELD", f"missing required field: {missing[0]}")

    units = data["units"]
    if units not in ("ft", "m"):
        fail("E_FIELD", "units must be ft or m")
    area_unit = "sq ft" if units == "ft" else "sq m"
    length_unit = units

    length = get_number(data, "length", 0.1, 200)
    width = get_number(data, "width", 0.1, 200)
    height = get_number(data, "height", 0.1, 200)
    doors = get_int(data, "doors", 0, 50)
    windows = get_int(data, "windows", 0, 50)
    coats = get_int(data, "coats", 1, 4)

    defaults = DEFAULTS[units]
    door_area, door_src = optional_number(
        data, "door_area", 0.1, 100, defaults["door_area"], "working default")
    window_area, window_src = optional_number(
        data, "window_area", 0.1, 100, defaults["window_area"], "working default")
    coverage, coverage_src = optional_number(
        data, "coverage", 1, 1000, defaults["coverage"], "working default")
    waste, waste_src = optional_number(
        data, "waste_percent", 0, 50, WASTE_DEFAULT, "working value")
    rounding = data.get("rounding", "half")
    if rounding not in ("half", "whole"):
        fail("E_FIELD", "rounding must be half or whole")

    gross = 2 * (length + width) * height
    door_total = doors * door_area
    window_total = windows * window_area
    openings = door_total + window_total
    if openings >= gross:
        fail("E_GEOMETRY", "openings meet or exceed the gross wall area")
    net = gross - openings
    coated = net * coats
    multiplier = 1 + waste / 100
    total = coated * multiplier
    raw = total / coverage
    if rounding == "half":
        buy = math.ceil(round(raw * 2, 6)) / 2
    else:
        buy = float(math.ceil(round(raw, 6)))

    findings = []
    share = openings / gross
    if share > OPENINGS_LIMIT_SHARE:
        findings.append(
            f"finding: F1 OPENINGS_OVER_HALF - openings are {share * 100:.1f} percent "
            f"of gross wall area (limit 50 percent, working value)")
    height_ft = height if units == "ft" else height * FT_PER_M
    if not HEIGHT_MIN_FT <= height_ft <= HEIGHT_MAX_FT:
        findings.append(
            f"finding: F2 HEIGHT_OUT_OF_RANGE - wall height {height:.2f} {length_unit} "
            f"is outside 6 to 20 ft (working range)")

    lines = [
        f"paint-quantity-calculator {VERSION}",
        f"units: {units}",
        f"gross_wall_area: 2 x ({length:.2f} + {width:.2f}) x {height:.2f} = {gross:.2f} {area_unit}",
        f"door_area_each: {door_area:.2f} {area_unit} ({door_src})",
        f"window_area_each: {window_area:.2f} {area_unit} ({window_src})",
        f"openings: doors {doors} x {door_area:.2f} = {door_total:.2f}; "
        f"windows {windows} x {window_area:.2f} = {window_total:.2f}; "
        f"total {openings:.2f} {area_unit}",
        f"net_wall_area: {gross:.2f} - {openings:.2f} = {net:.2f} {area_unit}",
        f"coats: {coats}",
        f"coated_area: {net:.2f} x {coats} = {coated:.2f} {area_unit}",
        f"waste: {waste:.2f} percent ({waste_src}); {coated:.2f} x {multiplier:.4f} = {total:.2f} {area_unit}",
        f"coverage: {coverage:.2f} {area_unit} per gallon ({coverage_src})",
        f"gallons_exact: {total:.2f} / {coverage:.2f} = {raw:.4f} gallons",
        f"gallons_to_buy: {buy:.2f} gallons (rounding: {rounding})",
    ]
    lines.extend(findings)
    if findings:
        lines.append(f"status: findings ({len(findings)})")
        exit_code = 1
    else:
        lines.append("status: ok")
        exit_code = 0
    return exit_code, "\n".join(lines) + "\n"


def print_error(code, detail):
    sys.stderr.write(json.dumps({"error": code, "detail": detail}) + "\n")


def main(argv):
    if len(argv) != 2:
        print_error("E_USAGE", "usage: python -I scripts/paint.py <input-file>")
        return 2
    try:
        exit_code, text = run(argv[1])
    except InputError as exc:
        print_error(exc.code, exc.detail)
        return 2
    sys.stdout.write(text)
    return exit_code


if __name__ == "__main__":
    sys.exit(main(sys.argv))
