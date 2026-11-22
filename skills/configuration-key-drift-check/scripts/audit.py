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
    if not isinstance(data, dict):
        return {"ok": False, "input_error": True, "errors": [err("TOP_LEVEL_TYPE", "input must be an object")], "configuration_count": 0, "findings": []}
    if set(data) != {"required_keys", "optional_keys", "configurations"}:
        observed_count = len(data["configurations"]) if isinstance(data.get("configurations"), list) else 0
        return {"ok": False, "input_error": True, "errors": [err("UNKNOWN_OR_MISSING_KEY", "top-level keys are exactly required_keys, optional_keys, configurations")], "configuration_count": observed_count, "findings": []}
    errors = []
    def decl(name):
        value = data[name]
        if not isinstance(value, list) or len(value) > 200:
            errors.append(err("DECLARATION_TYPE_OR_LIMIT", name + " must be an array of at most 200 strings"))
            return []
        seen = set()
        for item in value:
            if not isinstance(item, str) or not item or len(item) > 200:
                errors.append(err("KEY_TYPE", name + " contains an invalid key"))
            elif item in seen:
                errors.append(err("DUPLICATE_DECLARED_KEY", name + " contains a duplicate key"))
            if isinstance(item, str) and item and len(item) <= 200:
                seen.add(item)
        return [item for item in value if isinstance(item, str) and item and len(item) <= 200]
    required = decl("required_keys")
    optional = decl("optional_keys")
    if set(required) & set(optional):
        errors.append(err("REQUIRED_OPTIONAL_OVERLAP", "required and optional keys overlap"))
    configs = data["configurations"]
    observed_count = len(configs) if isinstance(configs, list) else 0
    if not isinstance(configs, list) or not 1 <= len(configs) <= 100:
        errors.append(err("CONFIGURATION_TYPE_OR_LIMIT", "configurations must contain 1 to 100 objects"))
        configs = []
    names = set()
    for cfg in configs:
        if not isinstance(cfg, dict) or set(cfg) != {"name", "keys"}:
            errors.append(err("CONFIGURATION_SCHEMA", "each configuration has exactly name and keys"))
            continue
        name, keys = cfg["name"], cfg["keys"]
        if not isinstance(name, str) or not name or len(name) > 200 or name in names:
            errors.append(err("CONFIGURATION_NAME", "configuration names must be unique nonempty strings"))
        if isinstance(name, str) and name and len(name) <= 200:
            names.add(name)
        if not isinstance(keys, list) or len(keys) > 500:
            errors.append(err("CONFIGURATION_KEYS_TYPE_OR_LIMIT", "configuration keys must be an array of at most 500 strings"))
        elif any(not isinstance(k, str) or not k or len(k) > 200 for k in keys):
            errors.append(err("CONFIGURATION_KEY_TYPE", "configuration keys must be nonempty strings of at most 200 characters"))
    if errors:
        return {"ok": False, "input_error": True, "errors": errors, "configuration_count": observed_count, "findings": []}
    findings = []
    required_set, allowed = set(required), set(required) | set(optional)
    for cfg in configs:
        name, keys = cfg["name"], cfg["keys"]
        counts = Counter(keys)
        duplicate = sorted([k for k, count in counts.items() if count > 1])
        missing = sorted(required_set - set(keys))
        unexpected = sorted(set(keys) - allowed)
        if duplicate:
            findings.append({"configuration": name, "code": "DUPLICATE_CONFIG_KEY", "keys": duplicate})
        if missing:
            findings.append({"configuration": name, "code": "MISSING_REQUIRED_KEY", "keys": missing})
        if unexpected:
            findings.append({"configuration": name, "code": "UNEXPECTED_KEY", "keys": unexpected})
    return {"ok": not findings, "errors": [], "configuration_count": observed_count, "findings": findings}

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
