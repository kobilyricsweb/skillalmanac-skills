#!/usr/bin/env python3
"""Lint a prompt file for six structural defects and print one strict JSON object.

    python prompt_lint.py lint <prompt-file>

Reads the one file it is given (UTF-8, a BOM is accepted). Writes nothing, no network.
Standard output is always exactly one JSON document (ASCII only, no NaN), also on error.

Exit codes
    0  every applicable check passed
    1  at least one check failed
    2  usage error, missing file, unreadable file, or empty file (JSON {"error": ...})

JSON contract (schema_version 1)
    {"schema_version": 1, "command": "lint", "file": <base name>, "words": int,
     "lines": int, "placeholders": [str], "has_numeric_length_bound": bool,
     "checks": [{"id": str, "status": "pass" | "fail" | "na",
                 "findings": [{"line": int | null, "rule": str, "match": str,
                               "detail": str}]}],
     "passed": int, "applicable": int, "score": int (0-100), "verdict": "pass" | "fail"}
    Check ids, in this order: output_contract, contradictions, unbounded_length,
    undefined_placeholders, vague_phrasing, untrusted_input_boundary.
    score = round(100 * passed / applicable). "na" checks are left out of both counts.
    Text inside fenced code blocks is ignored by every check except output_contract
    and undefined_placeholders (a schema or a template legitimately lives in a fence).

What it cannot do: it matches surface wording. It does not know whether the prompt is
good, only whether these defects are visible. A pass is not a quality verdict.
"""
import json
import os
import re
import sys

SCHEMA_VERSION = 1

# Words after which a placeholder name suggests text that came from outside the prompt
# author's control. Used only to decide whether the injection-boundary check applies.
UNTRUSTED_NAME_WORDS = (
    "user", "input", "document", "text", "email", "message", "content", "query",
    "ticket", "review", "comment", "transcript", "page", "article", "question",
    "request", "body", "data", "file", "reply", "post", "feedback", "note",
)

UNITS = r"(words?|sentences?|items?|bullets?|bullet points?|characters?|chars|paragraphs?|lines?|tokens?|points?|steps?)"

OUTPUT_CONTRACT_RE = re.compile(
    r"output\s+(?:format|contract|schema|structure)|response\s+(?:format|schema|structure)|"
    r"return\s+format|expected\s+output|"
    r"\b(?:respond|reply|answer)\s+(?:only\s+)?(?:with|in|using)\b|"
    r"\breturn\s+(?:only\s+)?(?:a|an|the|valid|exactly|one)\b|"
    r"\boutput\s+(?:only|exactly|a|an|the\s+following)\b|"
    r"\bjson\s+schema\b|\bvalid\s+json\b|^\s*#+\s*(?:output|response|format)\b",
    re.IGNORECASE | re.MULTILINE,
)

# (label, regex A, regex B): both present in prose lines means the prompt pulls two ways.
CONTRADICTION_PAIRS = (
    ("concise-vs-detailed",
     re.compile(r"\b(?:be\s+(?:concise|brief|short|terse)|keep\s+it\s+(?:short|brief)|as\s+brief\s+as)", re.I),
     re.compile(r"\b(?:be\s+(?:as\s+)?(?:detailed|thorough|comprehensive|exhaustive)|in\s+(?:great\s+|full\s+)?detail|as\s+detailed\s+as)", re.I)),
    ("json-only-vs-explanation",
     re.compile(r"\b(?:only|just)\s+(?:valid\s+)?json\b|\bjson\s+only\b|\bnothing\s+(?:else\s+)?but\s+json|\bno\s+(?:other\s+|extra\s+)?text\b", re.I),
     re.compile(r"\b(?:include|add|provide|give|write)\s+(?:a\s+|an\s+|your\s+|the\s+)?(?:brief\s+|short\s+)?(?:explanation|reasoning|rationale|justification|commentary)\b|\bexplain\s+(?:your|the|why)\b", re.I)),
    ("no-questions-vs-ask",
     re.compile(r"\b(?:do\s+not|don't|never)\s+ask\s+(?:the\s+user\s+)?(?:any\s+)?(?:clarifying\s+)?questions?", re.I),
     re.compile(r"\bask\s+(?:the\s+user\s+)?(?:a\s+|one\s+)?(?:clarifying\s+)?questions?\b|\bask\s+for\s+clarification\b", re.I)),
    ("formal-vs-casual",
     re.compile(r"\b(?:formal|professional)\s+(?:tone|register|style|language)\b|\bwrite\s+formally\b", re.I),
     re.compile(r"\b(?:casual|informal|playful|chatty)\b", re.I)),
)

ALWAYS_RE = re.compile(r"\balways\s+([a-z']+(?:\s+[a-z']+){0,3})", re.I)
NEVER_RE = re.compile(r"\b(?:never|do\s+not|don't|must\s+not|mustn't|should\s+not|shouldn't)\s+([a-z']+(?:\s+[a-z']+){0,3})", re.I)
DETERMINERS = {"the", "a", "an", "any", "your", "its", "their", "this", "that", "these", "those", "my", "our", "to", "in", "of", "or", "and", "all", "every", "each", "some", "it", "them", "be"}

MAX_RE = re.compile(r"\b(?:at\s+most|no\s+more\s+than|under|fewer\s+than|up\s+to|maximum\s+of|max(?:imum)?|limited\s+to|within)\s+(\d+)\s+" + UNITS, re.I)
MIN_RE = re.compile(r"\b(?:at\s+least|no\s+fewer\s+than|no\s+less\s+than|minimum\s+of|min(?:imum)?(?:\s+of)?)\s+(\d+)\s+" + UNITS, re.I)

NUMERIC_BOUND_RE = re.compile(r"\b\d+\s*(?:-|to)?\s*\d*\s*" + UNITS + r"\b|\b(?:one|single|two|three)\s+(?:sentence|paragraph|line|word)s?\b", re.I)

UNBOUNDED_RULES = (
    ("as-needed", re.compile(r"\bas\s+(?:long|detailed|thorough|comprehensive|verbose|extensive)\s+as\s+(?:needed|necessary|possible|you\s+(?:like|want|can|need))", re.I)),
    ("as-much-as", re.compile(r"\bas\s+(?:much|many)\s+(?:\w+\s+)?as\s+(?:needed|necessary|possible|you\s+(?:like|want|can|need))", re.I)),
    ("exhaustive", re.compile(r"\b(?:be\s+|in\s+an?\s+)?(?:exhaustive|comprehensive|in[- ]depth)\b", re.I)),
    ("no-limit", re.compile(r"\bno\s+(?:length\s+|word\s+|token\s+)?(?:limit|cap|maximum)\b|\b(?:don't|do\s+not)\s+worry\s+about\s+(?:the\s+)?(?:length|brevity)\b|\bany\s+length\b", re.I)),
    ("long-form", re.compile(r"\b(?:write|produce|give)\s+(?:a\s+|an\s+)?(?:long|lengthy|very\s+detailed|extremely\s+detailed)\b", re.I)),
)

VAGUE_RULES = (
    ("try-to", re.compile(r"\b(?:try|trying|tries)\s+to\b", re.I)),
    ("attempt-to", re.compile(r"\battempt(?:ing)?\s+to\b", re.I)),
    ("should-probably", re.compile(r"\bshould\s+probably\b|\bprobably\s+should\b", re.I)),
    ("if-possible", re.compile(r"\bif\s+possible\b|\bwhere\s+possible\b|\bwhen\s+possible\b", re.I)),
    ("ideally", re.compile(r"\bideally\b|\bhopefully\b", re.I)),
    ("might-want", re.compile(r"\byou\s+(?:might|may)\s+want\s+to\b|\bfeel\s+free\s+to\b|\bit\s+would\s+be\s+(?:nice|good|great|helpful)\b", re.I)),
    ("best-effort", re.compile(r"\bdo\s+your\s+best\b|\bas\s+best\s+(?:as\s+)?you\s+can\b|\bbest\s+effort\b", re.I)),
)

PLACEHOLDER_RE = re.compile(r"\{\{\s*([A-Za-z_][\w.\-]*)\s*\}\}")

BOUNDARY_RE = re.compile(
    r"untrusted|\bnot\s+(?:as\s+)?(?:instructions|commands)\b|\bas\s+data\b|"
    r"\bdata,?\s+(?:and\s+)?not\s+(?:instructions|commands)\b|"
    r"\b(?:never|do\s+not|don't)\s+(?:follow|obey|execute|act\s+on)\s+(?:any\s+)?(?:instructions|commands|requests)\s+(?:found\s+)?(?:in|inside|within)\b|"
    r"\bignore\s+(?:any\s+)?(?:instructions|commands)\s+(?:found\s+)?(?:in|inside|within)\b",
    re.IGNORECASE,
)


def fail(message):
    sys.stdout.write(json.dumps({"schema_version": SCHEMA_VERSION, "error": message}, ensure_ascii=True) + "\n")
    return 2


def split_lines(text):
    """Return (all_lines, prose) where prose is [(line_number, text)] outside fenced code."""
    lines = text.splitlines()
    prose = []
    in_fence = False
    for number, line in enumerate(lines, start=1):
        if re.match(r"^\s*(?:```|~~~)", line):
            in_fence = not in_fence
            continue
        if not in_fence:
            prose.append((number, line))
    return lines, prose


def clip(value, size=80):
    value = " ".join(value.split())
    return value if len(value) <= size else value[: size - 3] + "..."


def finding(line, rule, match, detail):
    return {"line": line, "rule": rule, "match": clip(match), "detail": detail}


def check_output_contract(text):
    if OUTPUT_CONTRACT_RE.search(text):
        return []
    return [finding(None, "no-output-contract", "",
                    "no statement of the output format found (say what to return: format, fields, length, what to do when the answer is unknown)")]


def object_key(rest):
    tokens = re.findall(r"[a-z']+", rest.lower())
    if not tokens:
        return None
    verb = tokens[0]
    for token in tokens[1:]:
        if token not in DETERMINERS:
            return verb + " " + token
    return None


def singular(unit):
    unit = unit.lower()
    if unit == "chars":
        return "character"
    return unit[:-1] if unit.endswith("s") else unit


def check_contradictions(prose):
    found = []
    for label, re_a, re_b in CONTRADICTION_PAIRS:
        line_a = next(((n, m.group(0)) for n, t in prose for m in [re_a.search(t)] if m), None)
        line_b = next(((n, m.group(0)) for n, t in prose for m in [re_b.search(t)] if m), None)
        if line_a and line_b:
            found.append(finding(line_b[0], label, line_b[1],
                                 "conflicts with line %d (%s)" % (line_a[0], clip(line_a[1], 40))))
    always, never = {}, {}
    for number, line in prose:
        for m in ALWAYS_RE.finditer(line):
            key = object_key(m.group(1))
            if key:
                always.setdefault(key, (number, m.group(0)))
        for m in NEVER_RE.finditer(line):
            key = object_key(m.group(1))
            if key:
                never.setdefault(key, (number, m.group(0)))
    for key in sorted(set(always) & set(never)):
        found.append(finding(never[key][0], "always-vs-never", never[key][1],
                             "'always %s' on line %d and a prohibition on the same action here" % (key, always[key][0])))
    maxima, minima = {}, {}
    for number, line in prose:
        for m in MAX_RE.finditer(line):
            maxima.setdefault(singular(m.group(2)), []).append((int(m.group(1)), number, m.group(0)))
        for m in MIN_RE.finditer(line):
            minima.setdefault(singular(m.group(2)), []).append((int(m.group(1)), number, m.group(0)))
    for unit in sorted(set(maxima) & set(minima)):
        top = min(maxima[unit])
        low = max(minima[unit])
        if low[0] > top[0]:
            found.append(finding(low[1], "min-above-max", low[2],
                                 "minimum %d on line %d exceeds maximum %d on line %d (unit: %s)" % (low[0], low[1], top[0], top[1], unit)))
    found.sort(key=lambda f: (f["line"] or 0, f["rule"]))
    return found


def check_unbounded(prose):
    found = []
    for number, line in prose:
        for rule, regex in UNBOUNDED_RULES:
            for m in regex.finditer(line):
                found.append(finding(number, rule, m.group(0), "no measurable length limit; give a number and a unit"))
    return found


def placeholder_defined(lines, name):
    escaped = re.escape(name)
    definition = re.compile(
        r"^\s*(?:[-*+]\s+|\|\s*)?(?:`|\*\*)?\{\{\s*" + escaped + r"\s*\}\}(?:`|\*\*)?\s*(?::|-|–|—|=|\||\bis\b|\bmeans\b|\bholds\b|\bcontains\b)",
        re.IGNORECASE,
    )
    words = re.compile(r"\b" + r"[ _\-]".join(re.escape(p) for p in re.split(r"[_\-]", name)) + r"\b", re.IGNORECASE)
    for line in lines:
        if definition.search(line):
            return "defined"
    for line in lines:
        stripped = PLACEHOLDER_RE.sub(" ", line)
        if words.search(stripped):
            return "mentioned"
    return None


def check_placeholders(lines, text):
    names = []
    first_line = {}
    for number, line in enumerate(lines, start=1):
        for m in PLACEHOLDER_RE.finditer(line):
            name = m.group(1)
            if name not in first_line:
                first_line[name] = (number, m.group(0))
                names.append(name)
    found = []
    for name in names:
        if placeholder_defined(lines, name) is None:
            number, token = first_line[name]
            found.append(finding(number, "undefined-placeholder", token,
                                 "the prompt never says what '%s' holds (add a line like '%s: <what it is, format, may it be empty>')" % (name, token)))
    return sorted(names), found


def check_vague(prose):
    found = []
    for number, line in prose:
        for rule, regex in VAGUE_RULES:
            for m in regex.finditer(line):
                found.append(finding(number, rule, m.group(0), "hedged instruction; state the required behaviour or the exact fallback"))
    found.sort(key=lambda f: (f["line"], f["rule"]))
    return found


def check_boundary(prose, names):
    untrusted = [n for n in names if any(w in n.lower() for w in UNTRUSTED_NAME_WORDS)]
    if not untrusted:
        return "na", []
    if any(BOUNDARY_RE.search(t) for _, t in prose):
        return "pass", []
    return "fail", [finding(None, "no-untrusted-input-rule", ", ".join("{{%s}}" % n for n in untrusted),
                            "placeholders likely to carry outside text, but no line says to treat it as data and not as instructions")]


def lint_text(text, filename):
    lines, prose = split_lines(text)
    names, undefined = check_placeholders(lines, text)
    boundary_status, boundary_findings = check_boundary(prose, names)
    results = [
        ("output_contract", check_output_contract(text), None),
        ("contradictions", check_contradictions(prose), None),
        ("unbounded_length", check_unbounded(prose), None),
        ("undefined_placeholders", undefined, "na" if not names else None),
        ("vague_phrasing", check_vague(prose), None),
        ("untrusted_input_boundary", boundary_findings, boundary_status if boundary_status == "na" else None),
    ]
    checks, passed, applicable = [], 0, 0
    for check_id, findings, forced in results:
        status = forced or ("fail" if findings else "pass")
        if status != "na":
            applicable += 1
            passed += status == "pass"
        checks.append({"id": check_id, "status": status, "findings": findings})
    score = int(round(100.0 * passed / applicable)) if applicable else 100
    return {
        "schema_version": SCHEMA_VERSION,
        "command": "lint",
        "file": os.path.basename(filename),
        "words": len(text.split()),
        "lines": len(lines),
        "placeholders": names,
        "has_numeric_length_bound": bool(NUMERIC_BOUND_RE.search("\n".join(t for _, t in prose))),
        "checks": checks,
        "passed": passed,
        "applicable": applicable,
        "score": score,
        "verdict": "pass" if passed == applicable else "fail",
    }


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) != 2 or argv[0] != "lint":
        return fail("usage: prompt_lint.py lint <prompt-file>")
    path = argv[1]
    if not os.path.isfile(path):
        return fail("file not found: " + os.path.basename(path))
    try:
        with open(path, "r", encoding="utf-8-sig") as handle:
            text = handle.read()
    except (OSError, UnicodeDecodeError) as exc:
        return fail("cannot read file as UTF-8 text: %s" % type(exc).__name__)
    if not text.strip():
        return fail("file is empty: " + os.path.basename(path))
    report = lint_text(text, path)
    sys.stdout.write(json.dumps(report, ensure_ascii=True, allow_nan=False, indent=2) + "\n")
    return 0 if report["verdict"] == "pass" else 1


if __name__ == "__main__":
    sys.exit(main())
