"""Convert values between common units with exact arithmetic (stdlib only).

Usage: python -I scripts/convert.py <input-file>

<input-file> is a UTF-8 text file with one request per line:
    <value> <from-unit> <to-unit>
Blank lines are skipped. A line whose first non-space character is # is a comment.
Each request prints one JSON object on stdout (JSON Lines).

Exit codes: 0 every request ok; 1 at least one request refused, unknown or invalid;
2 usage or file error (a one-line JSON error object is printed instead).
The script only reads its input. It never writes files and never uses the network.
"""
import json
import os
import sys
from decimal import Decimal, ROUND_HALF_EVEN, localcontext
from fractions import Fraction

MAX_INPUT_BYTES = 2 * 1024 * 1024
MAX_ABS_VALUE = Decimal("1e15")
MAX_VALUE_TOKEN = 40
KELVIN_OFFSET = Fraction("273.15")

# symbol -> (dimension, exact factor to the base unit of the dimension)
# Base units: length m, mass g, volume mL, area m2, speed m/s, data B.
FACTORS = {
    "m": ("length", "1"), "cm": ("length", "0.01"), "mm": ("length", "0.001"),
    "km": ("length", "1000"), "in": ("length", "0.0254"), "ft": ("length", "0.3048"),
    "yd": ("length", "0.9144"), "mi": ("length", "1609.344"),
    "g": ("mass", "1"), "mg": ("mass", "0.001"), "kg": ("mass", "1000"),
    "t": ("mass", "1000000"), "oz": ("mass", "28.349523125"), "lb": ("mass", "453.59237"),
    "mL": ("volume", "1"), "L": ("volume", "1000"), "tsp": ("volume", "4.92892159375"),
    "tbsp": ("volume", "14.78676478125"), "floz": ("volume", "29.5735295625"),
    "cup": ("volume", "236.5882365"), "pt": ("volume", "473.176473"),
    "qt": ("volume", "946.352946"), "gal": ("volume", "3785.411784"),
    "m2": ("area", "1"), "cm2": ("area", "0.0001"), "in2": ("area", "0.00064516"),
    "ft2": ("area", "0.09290304"), "yd2": ("area", "0.83612736"),
    "ac": ("area", "4046.8564224"), "ha": ("area", "10000"), "km2": ("area", "1000000"),
    "mi2": ("area", "2589988.110336"),
    "m/s": ("speed", "1"), "km/h": ("speed", "1000/3600"), "mph": ("speed", "0.44704"),
    "kn": ("speed", "1852/3600"),
    "B": ("data", "1"), "kB": ("data", "1000"), "MB": ("data", "1000000"),
    "GB": ("data", "1000000000"), "TB": ("data", "1000000000000"),
    "KiB": ("data", "1024"), "MiB": ("data", "1048576"), "GiB": ("data", "1073741824"),
    "TiB": ("data", "1099511627776"),
}
TEMPERATURE_UNITS = {"C", "F", "K"}

FACTOR_VALUES = {symbol: Fraction(text) for symbol, (_, text) in FACTORS.items()}
ALL_UNITS = {symbol: dim for symbol, (dim, _) in FACTORS.items()}
ALL_UNITS.update({symbol: "temperature" for symbol in TEMPERATURE_UNITS})


class InputProblem(Exception):
    """File-level problem; the script stops with exit code 2."""

    def __init__(self, code, message):
        super().__init__(message)
        self.code = code


def parse_value(text):
    if not text or len(text) > MAX_VALUE_TOKEN or "_" in text:
        raise ValueError("value")
    number = Decimal(text)
    if not number.is_finite() or abs(number) > MAX_ABS_VALUE:
        raise ValueError("value")
    return Fraction(number)


def to_kelvin(x, unit):
    if unit == "C":
        return x + KELVIN_OFFSET
    if unit == "F":
        return (x - 32) * Fraction(5, 9) + KELVIN_OFFSET
    return x


def from_kelvin(k, unit):
    if unit == "C":
        return k - KELVIN_OFFSET
    if unit == "F":
        return (k - KELVIN_OFFSET) * Fraction(9, 5) + 32
    return k


def format_result(fr):
    """Round to at least 6 decimal places, with 6 significant digits below 1."""
    if fr == 0:
        return "0"
    with localcontext() as ctx:
        ctx.prec = 60
        exact = Decimal(fr.numerator) / Decimal(fr.denominator)
        places = max(6, 6 - exact.adjusted())
        quantized = exact.quantize(Decimal(1).scaleb(-places), rounding=ROUND_HALF_EVEN)
        text = format(quantized, "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text


def format_factor(fr):
    """Exact decimal when the denominator has only 2 and 5 as prime factors, else n/d."""
    denominator = fr.denominator
    for prime in (2, 5):
        while denominator % prime == 0:
            denominator //= prime
    if denominator != 1:
        return "%d/%d" % (fr.numerator, fr.denominator)
    with localcontext() as ctx:
        ctx.prec = 80
        return format((Decimal(fr.numerator) / Decimal(fr.denominator)).normalize(), "f")


def make_record(number, status, parts, dimension=None, result=None, factor=None,
                method=None, message=None):
    def token(index):
        return parts[index][:MAX_VALUE_TOKEN] if len(parts) > index else None
    return {
        "line": number, "status": status, "value": token(0), "from": token(1),
        "to": token(2), "dimension": dimension, "result": result, "factor": factor,
        "method": method, "message": message,
    }


def convert_line(number, text):
    parts = text.split()
    if len(parts) != 3:
        return make_record(number, "bad_format", parts,
                           message="expected three fields: value from-unit to-unit")
    value_text, src, dst = parts
    try:
        x = parse_value(value_text)
    except (ValueError, ArithmeticError):
        return make_record(number, "bad_value", parts,
                           message="value must be a finite number, |value| <= 1e15, no underscores")
    for symbol in (src, dst):
        if symbol not in ALL_UNITS:
            return make_record(number, "unknown_unit", parts,
                               message="unknown unit: " + symbol[:MAX_VALUE_TOKEN])
    src_dim, dst_dim = ALL_UNITS[src], ALL_UNITS[dst]
    if src_dim != dst_dim:
        return make_record(number, "refused", parts,
                           message="cannot convert %s to %s: different quantities"
                           % (src_dim, dst_dim))
    if src_dim == "temperature":
        kelvin = to_kelvin(x, src)
        if kelvin < 0:
            return make_record(number, "refused", parts, dimension=src_dim,
                               message="below absolute zero")
        result = from_kelvin(kelvin, dst)
        return make_record(number, "ok", parts, dimension=src_dim,
                           result=format_result(result), method="affine")
    factor = FACTOR_VALUES[src] / FACTOR_VALUES[dst]
    result = x * factor
    return make_record(number, "ok", parts, dimension=src_dim,
                       result=format_result(result), factor=format_factor(factor),
                       method="multiplicative")


def read_lines(path):
    if not os.path.exists(path):
        raise InputProblem("missing_file", "input file does not exist")
    if not os.path.isfile(path):
        raise InputProblem("not_a_file", "input path is not a regular file")
    try:
        if os.path.getsize(path) > MAX_INPUT_BYTES:
            raise InputProblem("input_too_large", "input file exceeds 2 MB")
        with open(path, "rb") as handle:
            raw = handle.read(MAX_INPUT_BYTES + 1)
    except OSError:
        raise InputProblem("unreadable_file", "input file cannot be read")
    if len(raw) > MAX_INPUT_BYTES:
        raise InputProblem("input_too_large", "input file exceeds 2 MB")
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise InputProblem("invalid_utf8", "input file is not valid UTF-8")
    return text.splitlines()


def fail(code, message):
    print(json.dumps({"status": "error", "code": code, "message": message},
                     separators=(",", ":")))
    return 2


def main(argv):
    if len(argv) != 2:
        return fail("usage", "usage: python -I scripts/convert.py <input-file>")
    try:
        lines = read_lines(argv[1])
    except InputProblem as problem:
        return fail(problem.code, str(problem))
    records = []
    for number, line in enumerate(lines, start=1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        records.append(convert_line(number, stripped))
    if not records:
        return fail("empty_input", "no conversion requests found in input file")
    findings = 0
    for record in records:
        print(json.dumps(record, separators=(",", ":")))
        if record["status"] != "ok":
            findings += 1
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
