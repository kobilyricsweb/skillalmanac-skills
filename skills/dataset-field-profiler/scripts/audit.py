"""Offline JSON utility. Reads one explicit input, prints JSON, writes no files.
Exit 0 modeled pass; 1 findings; 2 invalid input. No network.
"""
import json
import sys
from pathlib import Path
from decimal import Decimal, InvalidOperation
from fractions import Fraction
from collections import Counter, defaultdict, deque

MAX_BYTES = 2_000_000

def number(value):
    if isinstance(value, bool) or not isinstance(value, (int, Decimal)):
        raise ValueError("expected a finite JSON number; strings and booleans are not numbers")
    try:
        result = Decimal(str(value))
    except InvalidOperation as exc:
        raise ValueError("expected a finite decimal number") from exc
    if not result.is_finite():
        raise ValueError("number must be finite")
    parts = result.as_tuple()
    if len(parts.digits) > 1000 or abs(parts.exponent) > 1000 or abs(result.adjusted()) > 1000:
        raise ValueError("number exceeds coefficient-digit or exponent limit (1000)")
    return Fraction(result)

class InvalidNumber(ValueError):
    """A numeric JSON token rejected before any domain audit."""


def bounded_decimal(token):
    # Bound token allocation before Decimal conversion; the semantic limit remains1000.
    if len(token) > 2100:
        raise InvalidNumber("number exceeds coefficient-digit or exponent limit (1000)")
    try:
        value = Decimal(token)
        number(value)
        return value
    except (InvalidOperation, OverflowError, ValueError) as exc:
        raise InvalidNumber(str(exc) if isinstance(exc, ValueError) else "invalid decimal number") from exc

def require(condition, message):
    if not condition:
        raise ValueError(message)

def reject_constant(value):
    raise InvalidNumber("non-finite JSON number")

def unique_object(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, "duplicate JSON object key")
        result[key] = value
    return result

def audit(data):
    require(isinstance(data, dict), "input must be an object")
    require(set(data) == {"records"}, "unknown or missing top-level key")
    records = data["records"]
    require(isinstance(records, list), "records must be an array")
    require(len(records) <= 10000, "records exceeds 10000")
    names = set()
    for record in records:
        require(isinstance(record, dict), "every record must be an object")
        require(len(record) <= 1000, "record exceeds 1000 fields")
        names.update(record.keys())
        require(len(names) <= 1000, "field union exceeds 1000")
    fields = []
    total = len(records)
    for name in sorted(names):
        item = {"name": name, "present": 0, "missing": 0, "null": 0,
                "string": 0, "boolean": 0, "integer": 0, "number": 0,
                "array": 0, "object": 0}
        for record in records:
            if name not in record:
                item["missing"] += 1
                continue
            item["present"] += 1
            value = record[name]
            if value is None:
                item["null"] += 1
            elif isinstance(value, bool):
                item["boolean"] += 1
            elif isinstance(value, str):
                item["string"] += 1
            elif isinstance(value, (int, Decimal)) and not isinstance(value, bool):
                exact = number(value)
                if exact.denominator == 1:
                    item["integer"] += 1
                else:
                    item["number"] += 1
            elif isinstance(value, list):
                item["array"] += 1
            elif isinstance(value, dict):
                item["object"] += 1
            else:
                require(False, "unsupported JSON value")
        require(item["present"] + item["missing"] == total, "internal count error")
        fields.append(item)
    return {"ok": True, "errors": [], "row_count": total,
            "field_count": len(fields), "fields": fields}

def main():
    try:
        require(len(sys.argv) == 2, "usage: python audit.py input.json")
        path = Path(sys.argv[1])
        require(path.stat().st_size <= MAX_BYTES, "input exceeds 2000000 bytes")
        data = json.loads(path.read_text(encoding="utf-8-sig"), parse_float=bounded_decimal, parse_int=bounded_decimal,
                          parse_constant=reject_constant, object_pairs_hook=unique_object)
        result = audit(data)
        require(isinstance(result, dict) and isinstance(result.get("ok"), bool), "invalid checker result")
        print(json.dumps(result, ensure_ascii=True, sort_keys=True))
        return 2 if result.get("input_error") else 0 if result["ok"] else 1
    except (ValueError, TypeError, KeyError, OSError, UnicodeError, RecursionError, OverflowError) as exc:
        report = {"ok": False, "input_error": True, "message": str(exc), "errors": []}
        if isinstance(exc, InvalidNumber):
            report["code"] = "invalid_number"
        print(json.dumps(report))
        return 2

if __name__ == "__main__":
    raise SystemExit(main())
