"""Estimate floor tile count, order count, box count and leftover tiles.

Usage:
    python -I scripts/tiles.py <input-file>

<input-file> is a UTF-8 JSON object of at most 2 MB with these keys:
    room_length_ft   number, greater than 0
    room_width_ft    number, greater than 0
    tile_length_in   number, greater than 0
    tile_width_in    number, greater than 0
    layout           "straight" or "diagonal"
    tiles_per_box    integer, 1 or more
    gap_in           number, 0 or more (optional, default 0)
    waste_pct        number, 0 to 100 (optional, default 10 straight, 15 diagonal)

Output: one JSON object on stdout.
Exit codes: 0 no findings, 1 findings, 2 usage or input error.
Error on exit 2: one line of JSON on stderr, {"error": "..."}.
The input file is read only. Nothing is written. No network, no subprocess.
"""

import json
import math
import sys
from fractions import Fraction

MAX_BYTES = 2 * 1024 * 1024
REQUIRED = {"room_length_ft", "room_width_ft", "tile_length_in",
            "tile_width_in", "layout", "tiles_per_box"}
OPTIONAL = {"gap_in", "waste_pct"}
# Minimum waste percent per layout, working values (not a published spec).
# The same numbers are the defaults when waste_pct is omitted.
LAYOUT_WASTE = {"straight": 10, "diagonal": 15}


def fail(message):
    sys.stderr.write(json.dumps({"error": message}) + "\n")
    sys.exit(2)


def reject_constant(name):
    raise ValueError(name)


def to_fraction(key, value):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        fail(key + " must be a number")
    if isinstance(value, float) and not math.isfinite(value):
        fail(key + " must be a finite number")
    return Fraction(str(value))


def positive(data, key):
    value = to_fraction(key, data[key])
    if value <= 0:
        fail(key + " must be greater than 0")
    return value


def load(path):
    try:
        with open(path, "rb") as handle:
            raw = handle.read(MAX_BYTES + 1)
    except OSError:
        fail("input file cannot be read")
    if len(raw) > MAX_BYTES:
        fail("input file exceeds 2 MB")
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        fail("input file is not valid UTF-8")
    try:
        data = json.loads(text, parse_constant=reject_constant)
    except (ValueError, RecursionError):
        fail("input file is not valid JSON")
    if not isinstance(data, dict):
        fail("input must be a JSON object")
    return data


def parse(data):
    missing = sorted(REQUIRED - set(data))
    if missing:
        fail("missing keys: " + ", ".join(missing))
    if any(key not in REQUIRED and key not in OPTIONAL for key in data):
        fail("unknown key in input")
    layout = data["layout"]
    if not isinstance(layout, str) or layout not in LAYOUT_WASTE:
        fail('layout must be "straight" or "diagonal"')
    tiles_per_box = data["tiles_per_box"]
    if (isinstance(tiles_per_box, bool) or not isinstance(tiles_per_box, int)
            or tiles_per_box < 1):
        fail("tiles_per_box must be an integer of 1 or more")
    gap = to_fraction("gap_in", data.get("gap_in", 0))
    if gap < 0:
        fail("gap_in must be 0 or more")
    if "waste_pct" in data:
        waste = to_fraction("waste_pct", data["waste_pct"])
        if waste < 0 or waste > 100:
            fail("waste_pct must be from 0 to 100")
    else:
        waste = Fraction(LAYOUT_WASTE[layout])
    return {
        "length_ft": positive(data, "room_length_ft"),
        "width_ft": positive(data, "room_width_ft"),
        "tile_l": positive(data, "tile_length_in"),
        "tile_w": positive(data, "tile_width_in"),
        "gap": gap,
        "waste": waste,
        "tiles_per_box": tiles_per_box,
        "layout": layout,
    }


def show(value):
    value = Fraction(value)
    if value.denominator == 1:
        return str(value.numerator)
    return "%g" % float(value)


def estimate(p):
    length_in = p["length_ft"] * 12
    width_in = p["width_ft"] * 12
    gap = p["gap"]
    cols = math.ceil((length_in + gap) / (p["tile_l"] + gap))
    rows = math.ceil((width_in + gap) / (p["tile_w"] + gap))
    base = cols * rows
    waste_tiles = math.ceil(base * p["waste"] / 100)
    order = base + waste_tiles
    tpb = p["tiles_per_box"]
    boxes = math.ceil(Fraction(order, tpb))
    leftover = boxes * tpb - order
    arithmetic = [
        "Room %s ft = %s in long; %s ft = %s in wide"
        % (show(p["length_ft"]), show(length_in), show(p["width_ft"]), show(width_in)),
        "Columns = ceil((%s + %s) / (%s + %s)) = %d"
        % (show(length_in), show(gap), show(p["tile_l"]), show(gap), cols),
        "Rows = ceil((%s + %s) / (%s + %s)) = %d"
        % (show(width_in), show(gap), show(p["tile_w"]), show(gap), rows),
        "Base tiles = %d x %d = %d" % (cols, rows, base),
        "Waste tiles = ceil(%d x %s / 100) = %d" % (base, show(p["waste"]), waste_tiles),
        "Order tiles = %d + %d = %d" % (base, waste_tiles, order),
        "Boxes = ceil(%d / %d) = %d" % (order, tpb, boxes),
        "Leftover tiles = %d x %d - %d = %d" % (boxes, tpb, order, leftover),
    ]
    findings = []
    minimum = LAYOUT_WASTE[p["layout"]]
    if p["waste"] < minimum:
        findings.append({
            "code": "WASTE_BELOW_MINIMUM",
            "detail": "waste %s percent is below the %s minimum of %d percent"
                      % (show(p["waste"]), p["layout"], minimum),
        })
    return {
        "status": "findings" if findings else "ok",
        "layout": p["layout"],
        "columns": cols,
        "rows": rows,
        "base_tiles": base,
        "waste_pct": show(p["waste"]),
        "waste_tiles": waste_tiles,
        "order_tiles": order,
        "tiles_per_box": tpb,
        "boxes": boxes,
        "leftover_tiles": leftover,
        "arithmetic": arithmetic,
        "findings": findings,
    }


def main(argv):
    if len(argv) != 2:
        fail("usage: python -I scripts/tiles.py <input-file>")
    result = estimate(parse(load(argv[1])))
    print(json.dumps(result, indent=2))
    return 1 if result["findings"] else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
