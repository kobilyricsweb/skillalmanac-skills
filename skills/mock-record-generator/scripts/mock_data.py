#!/usr/bin/env python3
"""Generate seeded mock records from a JSON field list or a simple TypeScript interface.

Command line:
  python scripts/mock_data.py <spec-file> --count N --seed S --format {csv,json} --out <new-file> [--interface NAME]

Reads the spec file only and writes exactly one new output file. The output path must not exist.
Standard library only. Makes no network calls and starts no other programs.

Exit codes: 0 ok, 1 findings (unsupported fields were skipped; output was still written), 2 usage or input error.
Errors are printed as one JSON line on stderr. The report is one JSON line on stdout.
"""

import argparse
import csv
import datetime
import io
import json
import os
import random
import re
import sys

MAX_INPUT_BYTES = 2 * 1024 * 1024
MAX_ROWS = 10000
MAX_FIELDS = 100
MAX_WORDS = 20

FIRST_NAMES = ["Ada", "Ben", "Carla", "Dev", "Elena", "Farid", "Grace", "Hiro", "Ines", "Jomo", "Kai", "Lena"]
LAST_NAMES = ["Alvarez", "Brooks", "Chen", "Dubois", "Evans", "Fischer", "Garcia", "Haddad", "Ito", "Jensen", "Khan", "Lopez"]
WORDS = ["amber", "brisk", "cedar", "delta", "ember", "fjord", "glade", "harbor", "iris", "juniper",
         "kettle", "lumen", "maple", "nimbus", "orbit", "prism", "quill", "river", "sable", "tundra"]
ALNUM = "abcdefghijklmnopqrstuvwxyz0123456789"
JSON_TYPES = ("int", "float", "bool", "date", "enum", "uuid", "name", "email", "text")

NAME_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]{0,63}")
HEADER_RE = re.compile(r"(?:export\s+)?interface\s+([A-Za-z_][A-Za-z0-9_]*)\s*\{$")
FIELD_RE = re.compile(r"(?:readonly\s+)?([A-Za-z_][A-Za-z0-9_]*)(\?)?\s*:\s*(.+?)\s*;?$")
LITERAL = r"(?:\"[^\"\\]*\"|'[^'\\]*')"
UNION_RE = re.compile(r"^" + LITERAL + r"(?:\s*\|\s*" + LITERAL + r")*$")
VALUE_RE = re.compile(r"\"([^\"\\]*)\"|'([^'\\]*)'")


class InputError(Exception):
    def __init__(self, code, message):
        Exception.__init__(self, message)
        self.code = code
        self.message = message


def emit_error(code, message):
    sys.stderr.write(json.dumps({"status": "error", "code": code, "message": message}) + "\n")
    sys.exit(2)


class OneLineParser(argparse.ArgumentParser):
    def error(self, message):
        emit_error("usage_error", message)


def pick(rng, items):
    return items[int(rng.random() * len(items))]


def make_field(name, gen, decimals=None, optional=False):
    return {"name": name, "gen": gen, "decimals": decimals, "optional": optional}


def is_number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def check_order(index, low, high):
    if low > high:
        raise InputError("invalid_spec", "field %d: min is greater than max" % index)


def parse_date(index, value):
    try:
        return datetime.date.fromisoformat(value)
    except (TypeError, ValueError):
        raise InputError("invalid_spec", "field %d: date must be YYYY-MM-DD" % index)


def build_json_field(index, name, ftype, item):
    def need_int(key, default):
        value = item.get(key, default)
        if type(value) is not int:
            raise InputError("invalid_spec", "field %d: %s must be an integer" % (index, key))
        return value

    if ftype == "int":
        low, high = need_int("min", 0), need_int("max", 100)
        check_order(index, low, high)
        return make_field(name, lambda rng: low + int(rng.random() * (high - low + 1)))

    if ftype == "float":
        low, high = item.get("min", 0.0), item.get("max", 1.0)
        if not is_number(low) or not is_number(high):
            raise InputError("invalid_spec", "field %d: min and max must be numbers" % index)
        decimals = need_int("decimals", 2)
        if not 0 <= decimals <= 6:
            raise InputError("invalid_spec", "field %d: decimals must be 0 to 6" % index)
        check_order(index, low, high)
        low_f, high_f = float(low), float(high)

        def gen_float(rng):
            value = round(low_f + rng.random() * (high_f - low_f), decimals)
            return min(max(value, low_f), high_f)

        return make_field(name, gen_float, decimals)

    if ftype == "bool":
        return make_field(name, lambda rng: rng.random() < 0.5)

    if ftype == "date":
        start = parse_date(index, item.get("from", "2000-01-01"))
        end = parse_date(index, item.get("to", "2030-12-31"))
        if start > end:
            raise InputError("invalid_spec", "field %d: from is after to" % index)
        span = (end - start).days

        def gen_date(rng):
            return (start + datetime.timedelta(days=int(rng.random() * (span + 1)))).isoformat()

        return make_field(name, gen_date)

    if ftype == "enum":
        values = item.get("values")
        if (not isinstance(values, list) or not values
                or not all(isinstance(v, str) and v for v in values)
                or len(set(values)) != len(values)):
            raise InputError("invalid_spec", "field %d: values must be distinct non-empty strings" % index)
        choices = list(values)
        return make_field(name, lambda rng: pick(rng, choices))

    if ftype == "uuid":
        def gen_uuid(rng):
            raw = [int(rng.random() * 256) for _ in range(16)]
            raw[6] = (raw[6] & 0x0F) | 0x40
            raw[8] = (raw[8] & 0x3F) | 0x80
            text = bytes(raw).hex()
            return "%s-%s-%s-%s-%s" % (text[0:8], text[8:12], text[12:16], text[16:20], text[20:32])

        return make_field(name, gen_uuid)

    if ftype == "name":
        return make_field(name, lambda rng: pick(rng, FIRST_NAMES) + " " + pick(rng, LAST_NAMES))

    if ftype == "email":
        def gen_email(rng):
            first = pick(rng, FIRST_NAMES).lower()
            last = pick(rng, LAST_NAMES).lower()
            return "%s.%s%d@example.com" % (first, last, 100 + int(rng.random() * 900))

        return make_field(name, gen_email)

    # ftype == "text"
    words = need_int("words", 5)
    if not 1 <= words <= MAX_WORDS:
        raise InputError("invalid_spec", "field %d: words must be 1 to 20" % index)

    def gen_text(rng):
        sentence = " ".join(pick(rng, WORDS) for _ in range(words))
        return sentence[0].upper() + sentence[1:] + "."

    return make_field(name, gen_text)


def parse_json(text):
    try:
        doc = json.loads(text)
    except (ValueError, RecursionError):
        raise InputError("invalid_json", "spec is not valid JSON")
    items = doc.get("fields") if isinstance(doc, dict) else None
    if not isinstance(items, list) or not items:
        raise InputError("invalid_spec", "spec must be an object with a non-empty fields list")
    fields, unsupported, seen = [], [], set()
    for index, item in enumerate(items):
        if not isinstance(item, dict):
            raise InputError("invalid_spec", "field %d is not an object" % index)
        name = item.get("name")
        if not isinstance(name, str) or not NAME_RE.fullmatch(name):
            raise InputError("invalid_spec", "field %d has a missing or invalid name" % index)
        if name in seen:
            raise InputError("invalid_spec", "field %d repeats a field name" % index)
        seen.add(name)
        ftype = item.get("type")
        if not isinstance(ftype, str):
            raise InputError("invalid_spec", "field %d has no type" % index)
        if ftype not in JSON_TYPES:
            unsupported.append({"field": name, "line": None, "type": ftype, "reason": "unsupported_type"})
            continue
        fields.append(build_json_field(index, name, ftype, item))
    return fields, unsupported


def ts_field(name, optional, expr):
    if expr == "string":
        gen, decimals = (lambda rng: "".join(pick(rng, ALNUM) for _ in range(8))), None
    elif expr == "number":
        gen, decimals = (lambda rng: round(rng.random() * 1000, 2)), 2
    elif expr == "boolean":
        gen, decimals = (lambda rng: rng.random() < 0.5), None
    elif UNION_RE.match(expr):
        values = []
        for double_quoted, single_quoted in VALUE_RE.findall(expr):
            value = double_quoted or single_quoted
            if value not in values:
                values.append(value)
        gen, decimals = (lambda rng: pick(rng, values)), None
    else:
        return None
    return make_field(name, gen, decimals, optional)


def parse_ts(text, wanted):
    lines = text.splitlines()
    start = None
    for number, line in enumerate(lines):
        match = HEADER_RE.match(line.strip())
        if match and (wanted is None or match.group(1) == wanted):
            start = number
            break
    if start is None:
        raise InputError("interface_not_found", "no matching interface header ending in an opening brace")
    fields, unsupported, seen = [], [], set()
    depth = 1
    for number in range(start + 1, len(lines)):
        line = lines[number].strip()
        if not line or line.startswith("//"):
            continue
        line_no = number + 1
        if depth == 1 and not line.startswith("}"):
            match = FIELD_RE.match(line)
            if match is None:
                unsupported.append({"field": None, "line": line_no, "type": None, "reason": "unsupported_syntax"})
            else:
                name, mark, expr = match.group(1), match.group(2), match.group(3)
                if name in seen:
                    raise InputError("invalid_spec", "line %d repeats a field name" % line_no)
                seen.add(name)
                built = ts_field(name, mark is not None, expr)
                if built is None:
                    unsupported.append({"field": name, "line": line_no, "type": expr, "reason": "unsupported_type"})
                else:
                    fields.append(built)
        depth += line.count("{") - line.count("}")
        if depth <= 0:
            break
    if depth > 0:
        raise InputError("invalid_spec", "interface body is not closed")
    return fields, unsupported


def read_spec(path):
    try:
        if os.path.getsize(path) > MAX_INPUT_BYTES:
            raise InputError("input_too_large", "spec is larger than 2 MB")
        with open(path, "rb") as handle:
            raw = handle.read(MAX_INPUT_BYTES + 1)
    except OSError:
        raise InputError("input_not_found", "spec file cannot be read")
    if len(raw) > MAX_INPUT_BYTES:
        raise InputError("input_too_large", "spec is larger than 2 MB")
    try:
        return raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise InputError("invalid_utf8", "spec is not valid UTF-8")


def check_output(spec_path, out_path):
    if os.path.normcase(os.path.abspath(out_path)) == os.path.normcase(os.path.abspath(spec_path)):
        raise InputError("output_is_input", "output path must not be the spec file")
    if not os.path.isdir(os.path.dirname(os.path.abspath(out_path))):
        raise InputError("output_dir_missing", "output folder does not exist")
    if os.path.exists(out_path):
        raise InputError("output_exists", "output file already exists; choose a new file name")


def generate(fields, count, seed):
    rng = random.Random(seed)
    rows = []
    for _ in range(count):
        row = {}
        for spec in fields:
            if spec["optional"] and rng.random() < 0.5:
                row[spec["name"]] = None
            else:
                row[spec["name"]] = spec["gen"](rng)
        rows.append(row)
    return rows


def csv_cell(value, decimals):
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, float) and decimals is not None:
        return "%.*f" % (decimals, value)
    return str(value)


def render(rows, fields, fmt):
    names = [spec["name"] for spec in fields]
    if fmt == "json":
        return json.dumps([{n: row[n] for n in names} for row in rows], indent=2, ensure_ascii=False) + "\n"
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(names)
    for row in rows:
        writer.writerow([csv_cell(row[spec["name"]], spec["decimals"]) for spec in fields])
    return buffer.getvalue()


def write_new(path, text):
    try:
        with open(path, "x", encoding="utf-8", newline="") as handle:
            handle.write(text)
    except FileExistsError:
        raise InputError("output_exists", "output file already exists; choose a new file name")
    except OSError:
        raise InputError("output_not_writable", "output file cannot be created")


def main(argv=None):
    parser = OneLineParser(description="Generate seeded mock records as CSV or JSON.")
    parser.add_argument("spec", help="JSON field list (.json) or TypeScript interface (.ts)")
    parser.add_argument("--count", type=int, required=True, help="rows, 1 to 10000")
    parser.add_argument("--seed", type=int, default=0, help="integer seed; same seed and spec give the same rows")
    parser.add_argument("--format", choices=("csv", "json"), required=True)
    parser.add_argument("--out", required=True, help="new output file; must not exist")
    parser.add_argument("--interface", default=None, help="interface name when the .ts file has several")
    args = parser.parse_args(argv)
    rows = []
    try:
        if not 1 <= args.count <= MAX_ROWS:
            raise InputError("usage_error", "count must be between 1 and 10000")
        ext = os.path.splitext(args.spec)[1].lower()
        if ext not in (".json", ".ts"):
            raise InputError("unsupported_spec_file", "spec must end in .json or .ts")
        check_output(args.spec, args.out)
        text = read_spec(args.spec)
        if ext == ".json":
            fields, unsupported = parse_json(text)
        else:
            fields, unsupported = parse_ts(text, args.interface)
        if not fields:
            raise InputError("no_supported_fields", "no supported fields in spec")
        if len(fields) > MAX_FIELDS:
            raise InputError("too_many_fields", "spec has more than 100 supported fields")
        rows = generate(fields, args.count, args.seed)
        write_new(args.out, render(rows, fields, args.format))
    except InputError as exc:
        emit_error(exc.code, exc.message)
    report = {
        "status": "partial" if unsupported else "ok",
        "rows": len(rows),
        "format": args.format,
        "out": args.out,
        "fields": [spec["name"] for spec in fields],
        "unsupported": unsupported,
    }
    sys.stdout.write(json.dumps(report) + "\n")
    return 1 if unsupported else 0


if __name__ == "__main__":
    sys.exit(main())
