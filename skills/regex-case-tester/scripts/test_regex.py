#!/usr/bin/env python3
"""Run a table of must-match and must-not-match cases against a regex, with Python re.

Usage:
    python test_regex.py SPEC.json [--no-probe]
    python test_regex.py -            (read the spec from standard input)

SPEC.json is an object:
    pattern    string, required
    flavour    "python" (default), or "js", "pcre", "re2", "java", "dotnet", "go", "other"
    mode       "fullmatch" (default) or "search"
    flags      list drawn from "i" "m" "s" "x" "a" (optional)
    match      list of strings that must match
    no_match   list of strings that must not match

Reads the spec file only. Writes nothing; the JSON report goes to standard output.
No network, no subprocess, no signals.

Time guard. Python's re cannot be interrupted, so the guard is a length cap, not a clock:
a case longer than MAX_CASE_LEN is skipped, and when the static scan finds a high-severity
risk the cap drops to RISKY_CASE_LEN. The growth probe runs short strings of increasing
length and stops as soon as one run is slow. A catastrophic pattern the static scan misses,
combined with a long input, can still hang; see Limits in SKILL.md.

Exit codes: 0 verdict "pass"; 1 any other verdict; 2 the spec file is missing, unreadable
or malformed.
"""
import json
import re
import sys
import time

try:
    import re._parser as _parser  # Python 3.11 and newer
except ImportError:
    try:
        import sre_parse as _parser  # older Pythons
    except ImportError:
        _parser = None

MAX_PATTERN_LEN = 2000   # a longer pattern is almost certainly not a field validator
MAX_CASE_LEN = 2000      # ordinary cap on one input, so one big string cannot stall a run
RISKY_CASE_LEN = 16      # 2**16 backtracking steps is still instant; 2**30 is not
MIN_CASES_EACH = 3       # the brief asks for at least three of each kind
PROBE_STOP_SECONDS = 0.05    # stop growing the probe after one run this slow
PROBE_EXP_SIZES = (6, 8, 10, 12, 14, 16, 18, 20, 22)   # exponential shapes double per extra char
PROBE_POLY_SIZES = (50, 100, 200, 400)                 # polynomial shapes are probed by doubling
EXP_RATIO = 2.5          # time ratio for +2 characters that marks exponential growth (4 is ideal)
POLY_RATIO = 3.0         # time ratio for doubling length that marks at least quadratic growth
PROBE_MIN_MS = 1.0       # ignore growth between runs too fast to time reliably

FLAG_MAP = {"i": re.IGNORECASE, "m": re.MULTILINE, "s": re.DOTALL, "x": re.VERBOSE, "a": re.ASCII}
FLAVOURS = {"python", "js", "pcre", "re2", "java", "dotnet", "go", "other"}

# A small probe alphabet stands in for "any character" when two sets are compared.
ALPHABET = frozenset([chr(i) for i in range(128)] + ["é", "٣", "３", " ", "я", "中"])
CATEGORY_RE = {
    "CATEGORY_DIGIT": re.compile(r"\d"), "CATEGORY_NOT_DIGIT": re.compile(r"\D"),
    "CATEGORY_SPACE": re.compile(r"\s"), "CATEGORY_NOT_SPACE": re.compile(r"\S"),
    "CATEGORY_WORD": re.compile(r"\w"), "CATEGORY_NOT_WORD": re.compile(r"\W"),
}
BACKTRACKING_REPEATS = ("MAX_REPEAT", "MIN_REPEAT")
ALL_REPEATS = BACKTRACKING_REPEATS + ("POSSESSIVE_REPEAT",)


# ---------------------------------------------------------------- pattern tree helpers

def items_of(sub):
    data = getattr(sub, "data", None)
    return list(data) if data is not None else list(sub)


def lit_set(code, ci):
    ch = chr(code)
    out = {ch}
    if ci:
        out |= {ch.lower(), ch.upper()}
    return out


def in_set(av, ci):
    negate, pos = False, set()
    for op, arg in av:
        name = str(op)
        if name == "NEGATE":
            negate = True
        elif name == "LITERAL":
            pos |= lit_set(arg, ci)
        elif name == "RANGE":
            lo, hi = arg
            pos |= {c for c in ALPHABET if lo <= ord(c) <= hi}
        elif name == "CATEGORY":
            rx = CATEGORY_RE.get(str(arg))
            pos |= {c for c in ALPHABET if rx is None or rx.match(c)}
        else:
            pos |= set(ALPHABET)
    return set(ALPHABET) - pos if negate else pos


def node_first(op, av, ci, dotall, reverse):
    """Return (chars the node can consume first, whether it can match empty)."""
    name = str(op)
    if name == "LITERAL":
        return lit_set(av, ci), False
    if name == "NOT_LITERAL":
        return set(ALPHABET) - lit_set(av, ci), False
    if name == "ANY":
        return (set(ALPHABET) if dotall else set(ALPHABET) - {"\n"}), False
    if name == "IN":
        return in_set(av, ci), False
    if name == "SUBPATTERN":
        add = av[1] or 0
        return seq_first(items_of(av[3]), ci or bool(add & re.IGNORECASE), dotall or bool(add & re.DOTALL), reverse)
    if name == "BRANCH":
        out, nullable = set(), False
        for alt in av[1]:
            s, n = seq_first(items_of(alt), ci, dotall, reverse)
            out |= s
            nullable = nullable or n
        return out, nullable
    if name in ALL_REPEATS:
        s, n = seq_first(items_of(av[2]), ci, dotall, reverse)
        return s, n or av[0] == 0
    if name == "ATOMIC_GROUP":
        return seq_first(items_of(av), ci, dotall, reverse)
    if name in ("AT", "ASSERT", "ASSERT_NOT"):
        return set(), True
    if name == "GROUPREF_EXISTS":
        s1, _ = seq_first(items_of(av[1]), ci, dotall, reverse)
        s2, _ = seq_first(items_of(av[2]) if av[2] is not None else [], ci, dotall, reverse)
        return s1 | s2, True
    return set(ALPHABET), True  # GROUPREF and anything unknown: assume the worst


def seq_first(items, ci, dotall, reverse=False):
    out = set()
    for op, av in (reversed(items) if reverse else items):
        s, nullable = node_first(op, av, ci, dotall, reverse)
        out |= s
        if not nullable:
            return out, False
    return out, True


def contains_unbounded(items):
    for op, av in items:
        name = str(op)
        if name in BACKTRACKING_REPEATS:
            if av[1] == _parser.MAXREPEAT or contains_unbounded(items_of(av[2])):
                return True
        elif name == "SUBPATTERN" and contains_unbounded(items_of(av[3])):
            return True
        elif name == "BRANCH" and any(contains_unbounded(items_of(a)) for a in av[1]):
            return True
    return False


def edge_unbounded(items, ci, dotall, reverse):
    """Characters consumed by unbounded repeats sitting at the start (or end) of a sequence."""
    out = set()
    for op, av in (list(reversed(items)) if reverse else items):
        name = str(op)
        if name in BACKTRACKING_REPEATS and av[1] == _parser.MAXREPEAT:
            s, _ = seq_first(items_of(av[2]), ci, dotall, reverse)
            out |= s
        elif name == "SUBPATTERN":
            out |= edge_unbounded(items_of(av[3]), ci, dotall, reverse)
        elif name == "BRANCH":
            for alt in av[1]:
                out |= edge_unbounded(items_of(alt), ci, dotall, reverse)
        _, nullable = node_first(op, av, ci, dotall, reverse)
        if not nullable:
            break
    return out


def find_branches(items):
    """BRANCH nodes reachable from a repeat body without crossing another repeat."""
    out = []
    for op, av in items:
        name = str(op)
        if name == "BRANCH":
            out.append(av[1])
            for alt in av[1]:
                out += find_branches(items_of(alt))
        elif name == "SUBPATTERN":
            out += find_branches(items_of(av[3]))
    return out


def pick_char(chars, avoid=()):
    pool = sorted(c for c in chars if c.isprintable() and c not in avoid and ord(c) < 128)
    for preferred in ("a", "0", "1", " ", "x"):
        if preferred in pool:
            return preferred
    return pool[0] if pool else "a"


def pick_breaker(chars):
    for cand in ("!", "#", "~", "@", "\n", "\x01"):
        if cand not in chars:
            return cand
    return "\x01"


class Flags:
    def __init__(self):
        self.items = []

    def add(self, fid, severity, message, sample=None, kind=None, breaker="!"):
        entry = {"id": fid, "severity": severity, "message": message}
        if sample is not None:
            entry["probe"] = {"char": sample, "breaker": breaker, "kind": kind}
        self.items.append(entry)


def analyze(items, ci, dotall, out):
    prev = None  # previous item if it was an unbounded backtracking repeat
    dot_repeats = 0
    for op, av in items:
        name = str(op)
        unbounded = name in BACKTRACKING_REPEATS and av[1] == _parser.MAXREPEAT
        if unbounded:
            body = items_of(av[2])
            first, nullable = seq_first(body, ci, dotall)
            last, _ = seq_first(body, ci, dotall, True)
            inner = contains_unbounded(body)
            if nullable:
                out.add("nested_quantifier" if inner else "nullable_repeat_body", "high",
                        "an unbounded repeat whose body can match the empty string"
                        + (" and holds another unbounded repeat" if inner else ""),
                        pick_char(first or {"a"}), "exp", pick_breaker(first))
            elif inner:
                tail = edge_unbounded(body, ci, dotall, True)
                head = edge_unbounded(body, ci, dotall, False)
                clash = (tail & first) | (head & last)
                if clash:
                    out.add("nested_quantifier", "high",
                            "an unbounded repeat around a body that ends or starts with an unbounded repeat over the same characters",
                            pick_char(clash), "exp", pick_breaker(clash))
                else:
                    out.add("nested_quantifier_delimited", "medium",
                            "an unbounded repeat around a body with an inner unbounded repeat; a mandatory delimiter probably keeps it safe, confirm with the probe",
                            pick_char(first), "exp", pick_breaker(first))
            for alts in find_branches(body):
                sets = [seq_first(items_of(a), ci, dotall) for a in alts]
                singles = [len(items_of(a)) == 1 for a in alts]
                empties = [len(items_of(a)) == 0 for a in alts]
                if all(empties):
                    out.add("overlapping_alternation", "high", "alternatives inside an unbounded repeat are identical",
                            pick_char(first or {"a"}), "exp", pick_breaker(first))
                elif any(empties):
                    out.add("overlapping_alternation_prefix", "medium",
                            "alternatives inside an unbounded repeat share a leading part, so one is a prefix of another",
                            pick_char(first or {"a"}), "exp", pick_breaker(first))
                else:
                    for i in range(len(alts)):
                        for j in range(i + 1, len(alts)):
                            both = sets[i][0] & sets[j][0]
                            if both:
                                sev = "high" if singles[i] and singles[j] else "medium"
                                out.add("overlapping_alternation", sev,
                                        "two alternatives inside an unbounded repeat can start with the same character",
                                        pick_char(both), "exp", pick_breaker(both))
                                break
            if prev is not None:
                shared = seq_first(items_of(prev[2]), ci, dotall)[0] & first
                if shared:
                    out.add("adjacent_overlapping_repeats", "medium",
                            "two unbounded repeats in a row can claim the same characters; time grows as a power of the input length",
                            pick_char(shared), "poly", pick_breaker(shared))
            if len(first) > 100 and len(body) == 1:
                dot_repeats += 1
            analyze(body, ci, dotall, out)
            prev = av
            continue
        prev = None
        if name in ALL_REPEATS:
            analyze(items_of(av[2]), ci, dotall, out)
        elif name == "SUBPATTERN":
            add = av[1] or 0
            analyze(items_of(av[3]), ci or bool(add & re.IGNORECASE), dotall or bool(add & re.DOTALL), out)
        elif name == "BRANCH":
            for alt in av[1]:
                analyze(items_of(alt), ci, dotall, out)
        elif name in ("ATOMIC_GROUP",):
            analyze(items_of(av), ci, dotall, out)
        elif name in ("ASSERT", "ASSERT_NOT"):
            analyze(items_of(av[1]), ci, dotall, out)
    if dot_repeats >= 2:
        out.add("multiple_dot_repeats", "low", "two or more unbounded any-character repeats in one sequence; slow on long non-matching input")


def pitfall_flags(items, mode, out):
    """Flags that are about correctness, not speed."""
    top_names = [str(op) for op, _ in items]
    has_start = any(str(op) == "AT" and str(av) in ("AT_BEGINNING", "AT_BEGINNING_STRING") for op, av in items)
    has_end = any(str(op) == "AT" and str(av) in ("AT_END", "AT_END_STRING") for op, av in items)
    if mode == "search" and not (has_start and has_end):
        out.add("unanchored_in_search_mode", "medium",
                "search mode with no anchor at "
                + ("either end" if not (has_start or has_end) else "one end")
                + ": a valid substring inside a bad value will pass")

    def walk(seq):
        for idx, (op, av) in enumerate(seq):
            name = str(op)
            if name == "AT" and str(av) == "AT_END" and mode == "search":
                out.add("dollar_allows_trailing_newline", "medium",
                        "$ also matches just before a final newline; \\Z is the strict end in Python")
            if name == "IN":
                lits = [a for o, a in av if str(o) == "LITERAL"]
                if any(str(o) == "RANGE" and a == (65, 122) for o, a in av):
                    out.add("range_A_to_z", "medium", "[A-z] also matches [ \\ ] ^ _ and a backtick; write A-Za-z")
                if 124 in lits and len(lits) >= 3 and not any(str(o) == "NEGATE" for o, _ in av):
                    out.add("pipe_in_class", "low", "a | inside [...] is a literal pipe, not alternation")
            if name == "ANY" and 0 < idx < len(seq) - 1:
                left, right = str(seq[idx - 1][0]), str(seq[idx + 1][0])
                if left in ("LITERAL", "IN") and right in ("LITERAL", "IN"):
                    out.add("single_dot_between_tokens", "low", "an unescaped . between two tokens matches any character; use \\. for a literal dot")
            if name == "SUBPATTERN":
                walk(items_of(av[3]))
            elif name in ALL_REPEATS:
                walk(items_of(av[2]))
            elif name == "BRANCH":
                for alt in av[1]:
                    walk(items_of(alt))
            elif name == "ATOMIC_GROUP":
                walk(items_of(av))
            elif name in ("ASSERT", "ASSERT_NOT"):
                walk(items_of(av[1]))

    walk(items)
    return top_names


def static_scan(pattern, flags, mode):
    flags_obj = Flags()
    if _parser is None:
        return [], "static analysis unavailable: no regex parser module in this Python"
    try:
        tree = _parser.parse(pattern, flags)
    except Exception as exc:  # compile errors are reported elsewhere
        return [], "static analysis skipped: " + str(exc)
    items = items_of(tree)
    analyze(items, bool(flags & re.IGNORECASE), bool(flags & re.DOTALL), flags_obj)
    pitfall_flags(items, mode, flags_obj)
    seen, unique = set(), []
    for entry in flags_obj.items:
        key = (entry["id"], entry["message"])
        if key not in seen:
            seen.add(key)
            unique.append(entry)
    return unique, None


# ---------------------------------------------------------------- constructs Python re cannot test

def untestable_constructs(pattern):
    found, seen = [], set()

    def add(cid, note):
        if cid not in seen:
            seen.add(cid)
            found.append({"id": cid, "note": note})

    modern = sys.version_info >= (3, 11)
    i, n, in_class = 0, len(pattern), False
    while i < n:
        c = pattern[i]
        nxt = pattern[i + 1] if i + 1 < n else ""
        if c == "\\":
            if nxt in ("p", "P"):
                add("unicode_property", "\\p{...} is not in Python re; use a character range or verify in the target engine")
            elif nxt in ("h", "H", "K", "G", "R", "X", "Q", "E"):
                add("escape_" + nxt, "\\" + nxt + " is not in Python re")
            elif nxt == "z":
                add("escape_z", "\\z is not in Python re before 3.14 (verify (unconfirmed)); Python's strict end is \\Z")
            i += 2
            continue
        if in_class:
            if c == "[" and nxt == ":":
                add("posix_class", "[[:alpha:]] POSIX classes are not in Python re")
            if c == "]":
                in_class = False
            i += 1
            continue
        if c == "[":
            in_class = True
            if nxt == "^" and i + 2 < n and pattern[i + 2] == "]":
                i += 3
            elif nxt == "]":
                i += 2
            else:
                i += 1
            continue
        if c == "(":
            rest = pattern[i + 1:i + 4]
            if rest.startswith("?<") and not rest.startswith(("?<=", "?<!")):
                add("named_group_angle", "(?<name>...) is not Python syntax; Python needs (?P<name>...)")
            elif rest.startswith("?'"):
                add("named_group_quote", "(?'name'...) is not Python syntax")
            elif rest.startswith("?>") and not modern:
                add("atomic_group", "(?>...) needs Python 3.11 or newer")
            elif rest.startswith(("?R", "?&", "?+", "?-")) or (rest[:1] == "?" and rest[1:2].isdigit()):
                add("recursion", "recursion or relative group calls are not in Python re")
            elif rest[:1] == "*":
                add("backtracking_verb", "(*VERB) control verbs are not in Python re")
        if c in "*+?}" and nxt == "+" and not modern:
            add("possessive_quantifier", "possessive quantifiers need Python 3.11 or newer")
        i += 1
    return found


# ---------------------------------------------------------------- running cases

def match_once(rx, text, mode):
    start = time.perf_counter()
    m = rx.fullmatch(text) if mode == "fullmatch" else rx.search(text)
    return m, (time.perf_counter() - start) * 1000.0


def run_case(rx, text, mode, expected, kind, cap, suspect=False, note=None):
    case = {"input": text, "kind": kind, "expected": expected}
    if len(text) > cap:
        case.update(actual="skipped", verdict="skipped", ms=0.0,
                    note="longer than the %d-character cap for this pattern" % cap)
        return case
    m, ms = match_once(rx, text, mode)
    other = "search" if mode == "fullmatch" else "fullmatch"
    alt, _ = match_once(rx, text, other)
    case["actual"] = "match" if m else "no_match"
    case["ms"] = round(ms, 3)
    case["groups"] = list(m.groups()) if m else None
    case["named"] = m.groupdict() if m else None
    case["span"] = list(m.span()) if m else None
    case["alt_semantics"] = {"mode": other, "actual": "match" if alt else "no_match"}
    if expected is None:
        case["verdict"] = "review" if (m and suspect) else "observed"
    else:
        case["verdict"] = "pass" if case["actual"] == expected else "fail"
    notes = []
    if note:
        notes.append(note)
    if expected == "match" and case["verdict"] == "pass" and mode == "search" and not alt:
        notes.append("passes only because search mode accepts a substring; fullmatch would reject it")
    if expected == "no_match" and case["verdict"] == "pass" and mode == "fullmatch" and alt:
        notes.append("rejected only because fullmatch requires the whole string; search would accept it")
    if notes:
        case["note"] = "; ".join(notes)
    return case


def adversarial_inputs(match_cases, mode, known):
    base = match_cases[0] if match_cases else None
    out = [("empty", "", True, "the empty string matched")]
    if base is not None:
        out += [
            ("trailing_newline", base + "\n", True, "a value with a trailing newline matched"),
            ("leading_space", " " + base, True, "a value with a leading space matched"),
            ("trailing_space", base + " ", True, "a value with a trailing space matched"),
        ]
        if any(ch.isdigit() for ch in base):
            swapped = "".join(chr(0x660 + int(ch)) if ch in "0123456789" else ch for ch in base)
            out.append(("arabic_indic_digits", swapped, True, "non-ASCII digits matched; \\d is Unicode-aware in Python str patterns, use [0-9] or re.ASCII"))
        if base != base.swapcase():
            out.append(("case_flipped", base.swapcase(), False, None))
        if mode == "search":
            out.append(("junk_suffix", base + "#junk", True, "text after a valid value still matched"))
            out.append(("junk_prefix", "junk#" + base, True, "text before a valid value still matched"))
    out.append(("non_ascii_letter", "é", True, "a non-ASCII letter matched"))
    seen, result = set(), []
    for label, text, suspect, note in out:
        if text in known or text in seen:
            continue
        seen.add(text)
        result.append((label, text, suspect, note))
    return result


def probe(rx, mode, entries):
    results = []
    # Exponential probes first. A polynomial probe uses long strings (50 and up), which would
    # hang on a pattern that is also exponential, so it only runs when no exponential risk is
    # present or seen.
    entries = sorted(entries, key=lambda e: e["probe"]["kind"] != "exp")
    exp_risk = False
    for entry in entries:
        info = entry["probe"]
        if info["kind"] == "poly" and exp_risk:
            results.append({"flag_id": entry["id"], "char": info["char"], "breaker": info["breaker"], "runs": [],
                            "verdict": "not_run_exponential_risk",
                            "detail": "skipped: another flag on this pattern points to exponential time, and long probe strings could hang"})
            continue
        if info["kind"] == "exp" and entry["severity"] == "high":
            exp_risk = True
        char, breaker = info["char"], info["breaker"]
        sizes = PROBE_EXP_SIZES if info["kind"] == "exp" else PROBE_POLY_SIZES
        runs = []
        for size in sizes:
            text = char * size + breaker
            m, ms = match_once(rx, text, mode)
            runs.append({"n": size, "ms": round(ms, 3)})
            if ms / 1000.0 > PROBE_STOP_SECONDS:
                break
        verdict, detail = "no_blowup_seen", "no super-linear growth within the probe sizes; this does not prove the pattern safe"
        timed = [r for r in runs if r["ms"] >= PROBE_MIN_MS]
        if len(timed) >= 2:
            prev, last = timed[-2], timed[-1]
            ratio = last["ms"] / prev["ms"] if prev["ms"] else 0
            step = last["n"] - prev["n"]
            if info["kind"] == "exp" and step == 2 and ratio >= EXP_RATIO:
                verdict, detail = "exponential_growth_seen", "time grew %.1fx for 2 more characters" % ratio
            elif info["kind"] == "poly" and last["n"] == 2 * prev["n"] and ratio >= POLY_RATIO:
                verdict, detail = "polynomial_growth_seen", "time grew %.1fx when the input length doubled" % ratio
        if info["kind"] == "exp" and verdict != "no_blowup_seen":
            exp_risk = True
        results.append({"flag_id": entry["id"], "char": char, "breaker": breaker, "runs": runs,
                        "verdict": verdict, "detail": detail})
    return results


# ---------------------------------------------------------------- spec and report

class SpecError(Exception):
    pass


def load_spec(path):
    try:
        if path == "-":
            raw = sys.stdin.read()
        else:
            with open(path, encoding="utf-8-sig") as fh:
                raw = fh.read()
    except OSError as exc:
        raise SpecError("cannot read spec file: %s" % exc)
    if not raw.strip():
        raise SpecError("spec file is empty")
    try:
        spec = json.loads(raw)
    except ValueError as exc:
        raise SpecError("spec is not valid JSON: %s" % exc)
    if not isinstance(spec, dict):
        raise SpecError("spec must be a JSON object")
    if not isinstance(spec.get("pattern"), str) or not spec["pattern"]:
        raise SpecError("spec.pattern must be a non-empty string")
    if len(spec["pattern"]) > MAX_PATTERN_LEN:
        raise SpecError("spec.pattern is longer than %d characters" % MAX_PATTERN_LEN)
    flavour = spec.get("flavour", "python")
    if flavour not in FLAVOURS:
        raise SpecError("spec.flavour must be one of " + ", ".join(sorted(FLAVOURS)))
    mode = spec.get("mode", "fullmatch")
    if mode not in ("fullmatch", "search"):
        raise SpecError('spec.mode must be "fullmatch" or "search"')
    flag_names = spec.get("flags", [])
    if not isinstance(flag_names, list) or any(f not in FLAG_MAP for f in flag_names):
        raise SpecError('spec.flags must be a list drawn from "i" "m" "s" "x" "a"')
    for key in ("match", "no_match"):
        value = spec.get(key, [])
        if not isinstance(value, list) or any(not isinstance(v, str) for v in value):
            raise SpecError("spec.%s must be a list of strings" % key)
    return spec, flavour, mode, flag_names


def build_report(spec, flavour, mode, flag_names, do_probe):
    pattern = spec["pattern"]
    flags = 0
    for name in flag_names:
        flags |= FLAG_MAP[name]
    must, mustnt = spec.get("match", []), spec.get("no_match", [])
    report = {"pattern": pattern, "flavour": flavour, "mode": mode, "flags": flag_names,
              "python_version": "%d.%d.%d" % sys.version_info[:3]}
    warnings = []
    untestable = untestable_constructs(pattern)
    report["untestable_constructs"] = untestable
    if flavour != "python":
        warnings.append("flavour is %s: Python re is a stand-in, so results are indicative only and never a pass" % flavour)
    if len(must) < MIN_CASES_EACH or len(mustnt) < MIN_CASES_EACH:
        warnings.append("fewer than %d must-match or %d must-not-match cases; the table is too thin to prove anything"
                        % (MIN_CASES_EACH, MIN_CASES_EACH))
    if "mode" not in spec:
        warnings.append('mode was not stated; defaulted to "fullmatch"')
    try:
        rx = re.compile(pattern, flags)
    except re.error as exc:
        report["compile"] = {"ok": False, "error": exc.msg, "position": exc.pos,
                             "line": getattr(exc, "lineno", None), "column": getattr(exc, "colno", None)}
        report.update(cases=[], static_flags=[], probe=[], warnings=warnings)
        if flavour != "python" or untestable:
            warnings.append("Python re cannot parse this pattern; it may still be valid in the target flavour")
            report["verdict"] = "untestable"
        else:
            report["verdict"] = "invalid_pattern"
        return report
    report["compile"] = {"ok": True, "groups": rx.groups, "group_names": sorted(rx.groupindex)}
    static, static_note = static_scan(pattern, flags, mode)
    if static_note:
        warnings.append(static_note)
    risky_high = any(f["severity"] == "high" for f in static)
    cap = RISKY_CASE_LEN if risky_high else MAX_CASE_LEN
    if risky_high:
        warnings.append("high-severity backtracking risk: inputs longer than %d characters were not run" % RISKY_CASE_LEN)
    cases = [run_case(rx, t, mode, "match", "user", cap) for t in must]
    cases += [run_case(rx, t, mode, "no_match", "user", cap) for t in mustnt]
    known = set(must) | set(mustnt)
    for label, text, suspect, note in adversarial_inputs(must, mode, known):
        case = run_case(rx, text, mode, None, "adversarial:" + label, cap, suspect, note)
        if case["verdict"] == "observed":
            case.pop("note", None)
        cases.append(case)
    probe_results = []
    if do_probe:
        probe_results = probe(rx, mode, [f for f in static if "probe" in f][:3])
    for entry in static:
        entry.pop("probe", None)
    report.update(cases=cases, static_flags=static, probe=probe_results, warnings=warnings)
    user = [c for c in cases if c["kind"] == "user"]
    counts = {v: sum(1 for c in cases if c["verdict"] == v) for v in ("pass", "fail", "skipped", "review", "observed")}
    report["summary"] = counts
    grown = any(p["verdict"].endswith("_growth_seen") for p in probe_results)
    thin = len(must) < MIN_CASES_EACH or len(mustnt) < MIN_CASES_EACH
    if any(c["verdict"] == "fail" for c in user):
        verdict = "fail"
    elif any(c["verdict"] == "skipped" for c in user) or thin:
        verdict = "incomplete"
    elif risky_high or grown:
        verdict = "risky"
    elif flavour != "python" or untestable:
        verdict = "indicative_only"
    else:
        verdict = "pass"
    report["verdict"] = verdict
    return report


def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    do_probe = "--no-probe" not in args
    args = [a for a in args if a != "--no-probe"]
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if len(args) != 1 or args[0] in ("-h", "--help"):
        sys.stderr.write("usage: test_regex.py SPEC.json [--no-probe]   (SPEC.json may be - for stdin)\n")
        return 2
    try:
        spec, flavour, mode, flag_names = load_spec(args[0])
    except SpecError as exc:
        sys.stderr.write("error: %s\n" % exc)
        return 2
    report = build_report(spec, flavour, mode, flag_names, do_probe)
    sys.stdout.write(json.dumps(report, indent=2, ensure_ascii=True) + "\n")
    return 0 if report["verdict"] == "pass" else 1


if __name__ == "__main__":
    sys.exit(main())
