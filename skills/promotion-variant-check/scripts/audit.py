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
    def err(code, message):
        return {"code": code, "message": message}
    observed_count = len(data["variants"]) if isinstance(data, dict) and isinstance(data.get("variants"), list) else 0
    base_result = {"ok": False, "input_error": True, "errors": [], "variant_count": observed_count, "findings": []}
    if not isinstance(data, dict) or set(data) != {"baseline", "variants", "changed_field"}:
        base_result["errors"] = [err("TOP_LEVEL_SCHEMA", "top-level keys are exactly baseline, variants, changed_field")]
        return base_result
    baseline = data["baseline"]
    changed = data["changed_field"]
    variants = data["variants"]
    errors = []
    if not isinstance(baseline, dict) or not 1 <= len(baseline) <= 200:
        errors.append(err("BASELINE_TYPE_OR_LIMIT", "baseline must be a nonempty object of at most 200 fields"))
        baseline = {}
    else:
        for key, value in baseline.items():
            if not isinstance(key, str) or not key or len(key) > 200 or not isinstance(value, str) or len(value) > 2000:
                errors.append(err("BASELINE_FIELD_TYPE", "baseline keys and values have invalid types or lengths"))
    if not isinstance(changed, str) or not changed or changed not in baseline:
        errors.append(err("CHANGED_FIELD", "changed_field must name a baseline field"))
    if not isinstance(variants, list) or not 1 <= len(variants) <= 200:
        errors.append(err("VARIANT_TYPE_OR_LIMIT", "variants must contain 1 to 200 objects"))
        variants = []
    ids = set()
    for variant in variants:
        if not isinstance(variant, dict) or set(variant) != {"id", "fields"}:
            errors.append(err("VARIANT_SCHEMA", "each variant has exactly id and fields"))
            continue
        ident, fields = variant["id"], variant["fields"]
        if not isinstance(ident, str) or not ident or len(ident) > 200 or ident in ids:
            errors.append(err("VARIANT_ID", "variant IDs must be unique nonempty strings"))
        if isinstance(ident, str) and ident and len(ident) <= 200:
            ids.add(ident)
        if not isinstance(fields, dict) or set(fields) != set(baseline):
            errors.append(err("FIELD_KEY_SET", "variant fields must exactly match baseline keys"))
            continue
        for key, value in fields.items():
            if not isinstance(value, str) or len(value) > 2000:
                errors.append(err("VARIANT_VALUE_TYPE", "variant field values must be bounded strings"))
    if errors:
        base_result["errors"] = errors
        base_result["variant_count"] = observed_count
        return base_result
    findings = []
    for variant in variants:
        ident, fields = variant["id"], variant["fields"]
        changed_fields = sorted([key for key in baseline if fields[key] != baseline[key]])
        codes = []
        if not changed_fields:
            codes.append("NO_CHANGE")
        if len(changed_fields) > 1:
            codes.append("MORE_THAN_ONE_CHANGED")
        if changed_fields != [changed]:
            codes.append("CHANGED_FIELD_MISMATCH")
        if codes:
            findings.append({"variant": ident, "codes": codes, "changed_fields": changed_fields})
    return {"ok": not findings, "errors": [], "variant_count": len(variants), "findings": findings}

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
