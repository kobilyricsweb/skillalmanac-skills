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
    require(set(data) == {"nodes"}, "unknown or missing top-level key")
    nodes = data["nodes"]
    require(isinstance(nodes, list), "nodes must be an array")
    require(len(nodes) <= 10000, "nodes exceeds 10000")
    parents = {}
    for node in nodes:
        require(isinstance(node, dict), "every node must be an object")
        require(set(node) == {"id", "parent_id"}, "node keys must be id and parent_id")
        ident = node["id"]
        parent = node["parent_id"]
        require(isinstance(ident, str) and len(ident) > 0, "id must be a nonempty string")
        require(parent is None or isinstance(parent, str), "parent_id must be string or null")
        require(ident not in parents, "duplicate id")
        parents[ident] = parent
    ids = set(parents)
    roots = sorted(ident for ident, parent in parents.items() if parent is None)
    orphans = sorted([{"id": ident, "parent_id": parent}
                      for ident, parent in parents.items()
                      if parent is not None and parent not in ids],
                     key=lambda item: (item["id"], item["parent_id"]))
    self_parenting = sorted(ident for ident, parent in parents.items() if parent == ident)
    state = {}
    cycles = []
    for start in sorted(ids):
        if state.get(start, 0) != 0:
            continue
        path = []
        position = {}
        current = start
        while current in ids and state.get(current, 0) == 0:
            state[current] = 1
            position[current] = len(path)
            path.append(current)
            current = parents[current]
            if current in position:
                cycles.append(path[position[current]:])
                break
        for ident in path:
            state[ident] = 2
    cycles.sort(key=lambda cycle: tuple(cycle))
    errors = []
    if orphans:
        errors.append({"code": "ORPHAN_REFERENCE", "count": len(orphans)})
    if self_parenting:
        errors.append({"code": "SELF_PARENTING", "count": len(self_parenting)})
    if cycles:
        errors.append({"code": "CYCLE", "count": len(cycles)})
    return {"ok": not errors, "errors": errors, "node_count": len(nodes),
            "roots": roots, "orphan_references": orphans,
            "self_parenting": self_parenting, "cycles": cycles}

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
