"""Check furniture placement in a rectangular room against working-value clearances.

Usage:
    python -I clearance.py <input-file>

The input is one UTF-8 JSON object of at most 2 MB with keys "room", "items"
and "doors". Coordinates are in inches. The origin is the north-west corner of
the room; x grows east and y grows south. An item is given by its north-west
corner (x, y) and its size (w along x, d along y). Walls are north (y = 0),
south (y = length), west (x = 0) and east (x = width). A door offset is measured
from the start of its wall: from the west end for north and south walls, and
from the north end for east and west walls.

Standard output: one JSON object with status "ok" or "findings".
Standard error: one JSON object with status "error" for usage and input errors.
Exit codes: 0 no violations, 1 violations found, 2 usage or input error.

The script only reads the input file. It never writes files, opens sockets or
starts processes. The clearance values are working values, not a building code.
"""
import json
import math
import sys

MAX_BYTES = 2 * 1024 * 1024
MAX_ITEMS = 300
MAX_DOORS = 20
MAIN_PATH_IN = 36.0      # working value: clear width of a door's main path
SECONDARY_GAP_IN = 24.0  # working value: minimum gap between items off a main path
WALLS = ("north", "south", "east", "west")
SCOPE = "working-value layout check, not a building-code check"


class InputError(Exception):
    """Raised for any usage or input problem; the message is reported as JSON."""


def finite(value, label, positive=False, allow_negative=False):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise InputError(label + " must be a finite number")
    if positive and value <= 0:
        raise InputError(label + " must be greater than 0")
    if not allow_negative and value < 0:
        raise InputError(label + " must not be negative")
    return float(value)


def load_json(path):
    try:
        with open(path, "rb") as handle:
            raw = handle.read(MAX_BYTES + 1)
    except FileNotFoundError:
        raise InputError("input file not found")
    except OSError:
        raise InputError("input file cannot be read")
    if len(raw) > MAX_BYTES:
        raise InputError("input exceeds 2 MB")
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        raise InputError("input is not valid UTF-8")
    try:
        return json.loads(text)
    except ValueError:
        raise InputError("input is not valid JSON")


def parse_items(raw):
    if not isinstance(raw, list) or len(raw) > MAX_ITEMS:
        raise InputError("items must be a list of at most %d entries" % MAX_ITEMS)
    items = []
    for index, entry in enumerate(raw, start=1):
        if not isinstance(entry, dict):
            raise InputError("item %d must be an object" % index)
        name = entry.get("name")
        if not isinstance(name, str) or not 1 <= len(name) <= 80:
            raise InputError("item %d name must be 1 to 80 characters" % index)
        items.append({
            "name": name,
            "x": finite(entry.get("x"), "item %d x" % index, allow_negative=True),
            "y": finite(entry.get("y"), "item %d y" % index, allow_negative=True),
            "w": finite(entry.get("w"), "item %d w" % index, positive=True),
            "d": finite(entry.get("d"), "item %d d" % index, positive=True),
        })
    return items


def parse_doors(raw, width, length):
    if not isinstance(raw, list) or len(raw) > MAX_DOORS:
        raise InputError("doors must be a list of at most %d entries" % MAX_DOORS)
    doors = []
    for number, entry in enumerate(raw, start=1):
        if not isinstance(entry, dict):
            raise InputError("door %d must be an object" % number)
        wall = entry.get("wall")
        if wall not in WALLS:
            raise InputError("door %d wall must be north, south, east or west" % number)
        offset = finite(entry.get("offset"), "door %d offset" % number)
        size = finite(entry.get("width"), "door %d width" % number, positive=True)
        wall_length = width if wall in ("north", "south") else length
        if offset + size > wall_length:
            raise InputError("door %d does not fit on its %s wall" % (number, wall))
        doors.append({"wall": wall, "offset": offset, "width": size})
    return doors


def parse_input(data):
    if not isinstance(data, dict):
        raise InputError("top level must be a JSON object")
    room = data.get("room")
    if not isinstance(room, dict):
        raise InputError("room must be an object with width and length")
    width = finite(room.get("width"), "room width", positive=True)
    length = finite(room.get("length"), "room length", positive=True)
    items = parse_items(data.get("items"))
    doors = parse_doors(data.get("doors"), width, length)
    return width, length, items, doors


def overlap_extent(a1, a2, b1, b2):
    return min(a2, b2) - max(a1, b1)


def positive_overlap(r, s):
    return overlap_extent(r[0], r[2], s[0], s[2]) > 0 and overlap_extent(r[1], r[3], s[1], s[3]) > 0


def door_zones(door, width, length):
    """Return the swing zone and the 36 in main-path corridor of a door as rectangles."""
    wall, offset, size = door["wall"], door["offset"], door["width"]
    center = offset + size / 2.0
    half = MAIN_PATH_IN / 2.0
    if wall == "north":
        swing = (offset, 0.0, offset + size, size)
        corridor = (center - half, 0.0, center + half, length)
    elif wall == "south":
        swing = (offset, length - size, offset + size, length)
        corridor = (center - half, 0.0, center + half, length)
    elif wall == "west":
        swing = (0.0, offset, size, offset + size)
        corridor = (0.0, center - half, width, center + half)
    else:
        swing = (width - size, offset, width, offset + size)
        corridor = (0.0, center - half, width, center + half)
    return swing, corridor


def violation(code, items, door, distance, required, depth, message):
    return {
        "code": code,
        "items": items,
        "door": door,
        "distance_in": round(distance, 1),
        "required_in": required,
        "depth_in": None if depth is None else round(depth, 1),
        "message": message,
    }


def gap_between(ra, rb):
    """Return (vertical, gap_rect, gap) for two items that face each other, else None."""
    x_ext = overlap_extent(ra[0], ra[2], rb[0], rb[2])
    y_ext = overlap_extent(ra[1], ra[3], rb[1], rb[3])
    lo_x, hi_x = max(ra[0], rb[0]), min(ra[2], rb[2])
    lo_y, hi_y = max(ra[1], rb[1]), min(ra[3], rb[3])
    if x_ext > 0 and y_ext <= 0:
        if ra[3] <= rb[1]:
            return True, (lo_x, ra[3], hi_x, rb[1]), rb[1] - ra[3]
        return True, (lo_x, rb[3], hi_x, ra[1]), ra[1] - rb[3]
    if y_ext > 0 and x_ext <= 0:
        if ra[2] <= rb[0]:
            return False, (ra[2], lo_y, rb[0], hi_y), rb[0] - ra[2]
        return False, (rb[2], lo_y, ra[0], hi_y), ra[0] - rb[2]
    return None


def on_main_path(gap_rect, vertical, corridors):
    for corridor in corridors:
        x_ext = overlap_extent(gap_rect[0], gap_rect[2], corridor[0], corridor[2])
        y_ext = overlap_extent(gap_rect[1], gap_rect[3], corridor[1], corridor[3])
        if vertical and x_ext > 0 and y_ext >= 0:
            return True
        if not vertical and y_ext > 0 and x_ext >= 0:
            return True
    return False


def check(width, length, items, doors):
    rects = [(it["name"], (it["x"], it["y"], it["x"] + it["w"], it["y"] + it["d"])) for it in items]
    zones = [door_zones(door, width, length) for door in doors]
    found = []

    for name, r in rects:
        over = max(-r[0], -r[1], r[2] - width, r[3] - length, 0.0)
        if over > 0:
            found.append(violation("out_of_bounds", [name], None, over, 0.0, None,
                                   "%s extends %.1f in outside the room" % (name, over)))

    for i in range(len(rects)):
        for j in range(i + 1, len(rects)):
            (na, ra), (nb, rb) = rects[i], rects[j]
            if positive_overlap(ra, rb):
                depth = min(overlap_extent(ra[0], ra[2], rb[0], rb[2]),
                            overlap_extent(ra[1], ra[3], rb[1], rb[3]))
                found.append(violation("overlap", [na, nb], None, 0.0, 0.0, depth,
                                       "%s and %s overlap by %.1f in" % (na, nb, depth)))

    for number, (swing, _corridor) in enumerate(zones, start=1):
        for name, r in rects:
            if positive_overlap(r, swing):
                depth = min(overlap_extent(r[0], r[2], swing[0], swing[2]),
                            overlap_extent(r[1], r[3], swing[1], swing[3]))
                found.append(violation("door_swing_blocked", [name], number, 0.0, 0.0, depth,
                                       "%s sits in the swing zone of door %d" % (name, number)))

    for number, (_swing, corridor) in enumerate(zones, start=1):
        for name, r in rects:
            if positive_overlap(r, corridor):
                depth = min(overlap_extent(r[0], r[2], corridor[0], corridor[2]),
                            overlap_extent(r[1], r[3], corridor[1], corridor[3]))
                found.append(violation("main_path_blocked", [name], number, 0.0, MAIN_PATH_IN, depth,
                                       "%s intrudes %.1f in into the main path of door %d"
                                       % (name, depth, number)))

    corridors = [corridor for _swing, corridor in zones]
    for i in range(len(rects)):
        for j in range(i + 1, len(rects)):
            (na, ra), (nb, rb) = rects[i], rects[j]
            found_gap = gap_between(ra, rb)
            if found_gap is None:
                continue
            vertical, gap_rect, gap = found_gap
            gap = round(gap, 1)
            if on_main_path(gap_rect, vertical, corridors):
                if gap < MAIN_PATH_IN:
                    found.append(violation("main_path_narrow", [na, nb], None, gap, MAIN_PATH_IN, None,
                                           "%s and %s leave %.1f in on a main path (36 in needed)"
                                           % (na, nb, gap)))
            elif gap < SECONDARY_GAP_IN:
                found.append(violation("secondary_gap_narrow", [na, nb], None, gap, SECONDARY_GAP_IN, None,
                                       "%s and %s leave %.1f in between them (24 in needed)"
                                       % (na, nb, gap)))
    return found


def main(argv):
    if len(argv) != 2:
        sys.stderr.write(json.dumps({"status": "error", "error": "usage: clearance.py <input-file>"}) + "\n")
        return 2
    try:
        data = load_json(argv[1])
        width, length, items, doors = parse_input(data)
    except InputError as exc:
        sys.stderr.write(json.dumps({"status": "error", "error": str(exc)}) + "\n")
        return 2
    violations = check(width, length, items, doors)
    result = {
        "scope": SCOPE,
        "status": "findings" if violations else "ok",
        "room": {"width": width, "length": length},
        "violation_count": len(violations),
        "violations": violations,
    }
    sys.stdout.write(json.dumps(result, indent=2) + "\n")
    return 1 if violations else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
