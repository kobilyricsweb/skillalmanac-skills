#!/usr/bin/env python3
"""Validate a batch of model outputs against a JSON Schema subset and tally failures.

Usage:
    python validate_outputs.py --schema schema.json --input outputs.jsonl
    python validate_outputs.py --example example.json --input ./outputs_dir --allow none
    python validate_outputs.py --schema s.json --input o.jsonl --allow fence,prose,trailing_commas \
        --report report.json --log per_record.jsonl --retry-out retries.jsonl

Reads: the schema (or example object) and the outputs (a JSONL file, or a folder of
.txt/.json/.md/.out files, one record per file). Never calls a model, never uses the network.
Writes: only the optional --report, --log and --retry-out files. Each of those refuses a path
that resolves to any input (schema, example, outputs file, a file inside the outputs folder, or the
outputs folder itself), even with --force. An existing output file needs --force to be replaced.
Prints one strict JSON report on stdout.

Exit codes: 0 every record valid; 1 at least one record invalid; 2 usage, input, or schema
problem (including schema keywords this script cannot check, unless --allow-unsupported).

The repair ladder (cheapest first; each rung that changes text is logged per record):
    fence, prose            extraction rungs, on by default
    trailing_commas, comments, python_literals, single_quotes
                            syntax rungs, off by default, enable with --allow
Truncated output is never repaired: closing brackets would invent data.
"""
import argparse
import json
import math
import os
import re
import sys

VERSION = "0.1.0"

# Rungs in the order they are tried. The first two only extract text; the rest rewrite syntax.
EXTRACTION_RUNGS = ("fence", "prose")
SYNTAX_RUNGS = ("trailing_commas", "comments", "python_literals", "single_quotes")
ALL_RUNGS = EXTRACTION_RUNGS + SYNTAX_RUNGS
DEFAULT_ALLOW = ("fence", "prose")

SUPPORTED = {"type", "properties", "required", "additionalProperties", "enum", "const",
             "minimum", "maximum", "items", "minItems", "maxItems", "minLength", "maxLength",
             "pattern"}
# Keywords that carry no validation meaning; skipping them is not "silently ignoring a rule".
ANNOTATIONS = {"$schema", "$id", "$comment", "title", "description", "default", "examples",
               "deprecated", "readOnly", "writeOnly"}
TYPE_NAMES = {"string", "number", "integer", "boolean", "null", "object", "array"}

MAX_START_CANDIDATES = 6      # first JSON-looking openers tried per text; stops cost on bracket-heavy prose
MAX_RETRY_LINES = 8           # a retry message lists at most this many problems; longer lists confuse the model
MAX_MSG_CHARS = 160           # one problem line stays short
EXCERPT_CHARS = 100
WILSON_Z = 1.96               # 95% interval

START_RE = re.compile(r"[\{\[]\s*(?:[\"\{\[\]\}\d-]|')")
NUMERIC_STRING_RE = re.compile(r"^\s*-?\d+(\.\d+)?([eE][+-]?\d+)?\s*$")
FENCE_OPEN_RE = re.compile(r"```[A-Za-z0-9_+-]*[ \t]*\r?\n")
FENCE_JSON_OPEN_RE = re.compile(r"```[A-Za-z0-9_+-]*[ \t]*\r?\n[ \t]*[\{\[]")
SECOND_CANDIDATE_RE = re.compile(r"[\{\[]\s*[\"\{\[]")
INPUT_SUFFIXES = {".txt", ".json", ".md", ".out"}


class UsageError(Exception):
    pass


# ---------------------------------------------------------------- strict parsing

def strict_parse(text):
    """Parse with the standard library, rejecting NaN/Infinity and recording duplicate keys."""
    dups = []

    def hook(pairs):
        obj = {}
        for key, val in pairs:
            if key in obj:
                dups.append(key)
            obj[key] = val
        return obj

    def bad_constant(name):
        raise ValueError("non-standard constant " + name)

    try:
        value = json.loads(text, object_pairs_hook=hook, parse_constant=bad_constant)
    except json.JSONDecodeError as exc:
        return False, None, dups, "%s at line %d column %d" % (exc.msg, exc.lineno, exc.colno)
    except ValueError as exc:
        return False, None, dups, str(exc)
    return True, value, dups, ""


# ---------------------------------------------------------------- repair ladder

def balanced_end(text, start, quotes):
    """Index of the bracket that closes the one at text[start], or None if the text ends first."""
    depth = 0
    i = start
    n = len(text)
    while i < n:
        c = text[i]
        if c in quotes:
            q = c
            i += 1
            while i < n and text[i] != q:
                if text[i] == "\\":
                    i += 1
                i += 1
            i += 1
            continue
        if c in "{[":
            depth += 1
        elif c in "}]":
            depth -= 1
            if depth == 0:
                return i
        i += 1
    return None


def repair_syntax(text, enabled):
    """Apply the enabled syntax rungs outside of strings. Returns (new_text, set_of_rungs_that_changed_text)."""
    out = []
    applied = set()
    i = 0
    n = len(text)
    literals = {"True": "true", "False": "false", "None": "null"}
    while i < n:
        c = text[i]
        if c == '"':
            j = i + 1
            while j < n:
                if text[j] == "\\":
                    j += 2
                    continue
                if text[j] == '"':
                    break
                j += 1
            out.append(text[i:j + 1])
            i = j + 1
            continue
        if c == "'" and "single_quotes" in enabled:
            j = i + 1
            buf = []
            while j < n and text[j] != "'":
                if text[j] == "\\" and j + 1 < n:
                    buf.append("'" if text[j + 1] == "'" else text[j:j + 2])
                    j += 2
                    continue
                buf.append('\\"' if text[j] == '"' else text[j])
                j += 1
            out.append('"' + "".join(buf) + '"')
            applied.add("single_quotes")
            i = j + 1
            continue
        if "comments" in enabled and text.startswith("//", i):
            j = text.find("\n", i)
            i = n if j < 0 else j
            applied.add("comments")
            continue
        if "comments" in enabled and text.startswith("/*", i):
            j = text.find("*/", i + 2)
            i = n if j < 0 else j + 2
            applied.add("comments")
            continue
        if c == "," and "trailing_commas" in enabled:
            k = i + 1
            while k < n and text[k] in " \t\r\n":
                k += 1
            if k < n and text[k] in "}]":
                applied.add("trailing_commas")
                i += 1
                continue
        if "python_literals" in enabled and (c.isalpha() or c == "_"):
            word = re.match(r"[A-Za-z_]+", text[i:]).group(0)
            if word in literals:
                out.append(literals[word])
                applied.add("python_literals")
            else:
                out.append(word)
            i += len(word)
            continue
        out.append(c)
        i += 1
    return "".join(out), applied


def fence_block(text):
    """Content of the first fenced block that starts with { or [ (closed or cut off), plus a multi flag."""
    for m in FENCE_OPEN_RE.finditer(text):
        rest = text[m.end():]
        if not rest.lstrip().startswith(("{", "[")):
            continue
        end = rest.find("```")
        block = rest if end < 0 else rest[:end]
        return block, len(FENCE_JSON_OPEN_RE.findall(text)) > 1
    return None


def attempt(text, allowed):
    """Try to get one JSON value out of text using only the allowed rungs.

    Returns a dict with status ok | empty | no_json_found | truncated | invalid_syntax.
    """
    t = text.lstrip(chr(0xFEFF))
    s = t.strip()
    if not s:
        return {"status": "empty"}
    syntax_allowed = set(allowed) & set(SYNTAX_RUNGS)
    ok, val, dups, err = strict_parse(s)
    if ok:
        return {"status": "ok", "value": val, "dups": dups, "repairs": [], "notes": []}

    candidates = []
    notes = []
    if "fence" in allowed:
        fb = fence_block(t)
        if fb:
            candidates.append((["fence"], fb[0].strip()))
            if fb[1]:
                notes.append("multiple_fenced_blocks")
    candidates.append(([], s))

    had_truncation = False
    balanced_but_bad = False
    parse_error = err
    for labels, cand in candidates:
        # Whole candidate, with syntax rungs only.
        fixed, applied = repair_syntax(cand, syntax_allowed)
        ok, val, dups, e = strict_parse(fixed)
        if ok:
            return {"status": "ok", "value": val, "dups": dups, "notes": notes,
                    "repairs": _ordered(labels, applied)}
        parse_error = e or parse_error
        if "prose" not in allowed:
            continue
        starts = [m.start() for m in START_RE.finditer(cand)][:MAX_START_CANDIDATES]
        skip_until = -1   # a value that failed to parse must not be re-tried through its own inner arrays
        for st in starts:
            if st <= skip_until:
                continue
            modes = ['"', "\"'"] if "single_quotes" in syntax_allowed else ['"']
            ends_seen = []
            for quotes in modes:
                end = balanced_end(cand, st, quotes)
                if end is None:
                    had_truncation = True
                    continue
                ends_seen.append(end)
                piece = cand[st:end + 1]
                fixed, applied = repair_syntax(piece, syntax_allowed)
                ok, val, dups, e = strict_parse(fixed)
                if ok:
                    extra = list(labels)
                    if cand[st:end + 1] != cand:
                        extra.append("prose")
                    if SECOND_CANDIDATE_RE.search(cand[end + 1:]):
                        notes.append("second_json_candidate_after_first")
                    return {"status": "ok", "value": val, "dups": dups, "notes": notes,
                            "repairs": _ordered(extra, applied)}
                parse_error = e or parse_error
                balanced_but_bad = True
            skip_until = max(ends_seen) if ends_seen else len(cand)
    if not START_RE.search(s):
        return {"status": "no_json_found", "error": "no { or [ that starts a JSON value"}
    if balanced_but_bad or not had_truncation:
        return {"status": "invalid_syntax", "error": parse_error}
    return {"status": "truncated", "error": "an opening bracket has no matching close (cut off?)"}


def _ordered(labels, applied):
    rank = {name: i for i, name in enumerate(ALL_RUNGS)}
    return sorted(set(labels) | set(applied), key=lambda x: rank[x])


def process_text(text, allowed):
    """attempt() plus the diagnosis of which disallowed rungs would have rescued a failed record."""
    res = attempt(text, allowed)
    if res["status"] == "ok":
        return res
    full = attempt(text, ALL_RUNGS)
    if full["status"] == "ok":
        res["status"] = "invalid_syntax"
        res["fixable_by"] = [r for r in full["repairs"] if r not in allowed]
        if not res.get("error"):
            res["error"] = "not a single strict JSON value"
    else:
        res["status"] = full["status"] if full["status"] != "ok" else res["status"]
        res["error"] = full.get("error", res.get("error", ""))
    return res


# ---------------------------------------------------------------- schema subset

def json_type(v):
    if v is None:
        return "null"
    if isinstance(v, bool):
        return "boolean"
    if isinstance(v, int):
        return "integer"
    if isinstance(v, float):
        return "number"
    if isinstance(v, str):
        return "string"
    if isinstance(v, list):
        return "array"
    return "object"


def type_ok(v, t):
    if t == "null":
        return v is None
    if t == "boolean":
        return isinstance(v, bool)
    if t == "integer":
        return (isinstance(v, int) and not isinstance(v, bool)) or (isinstance(v, float) and v.is_integer())
    if t == "number":
        return isinstance(v, (int, float)) and not isinstance(v, bool)
    if t == "string":
        return isinstance(v, str)
    if t == "array":
        return isinstance(v, list)
    return isinstance(v, dict)


def jeq(a, b):
    """JSON equality: true is not 1."""
    if isinstance(a, bool) or isinstance(b, bool):
        return isinstance(a, bool) and isinstance(b, bool) and a == b
    if isinstance(a, list) and isinstance(b, list):
        return len(a) == len(b) and all(jeq(x, y) for x, y in zip(a, b))
    if isinstance(a, dict) and isinstance(b, dict):
        return a.keys() == b.keys() and all(jeq(a[k], b[k]) for k in a)
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return a == b
    return type(a) == type(b) and a == b


def check_schema(schema, path, unsupported, errors):
    """Walk the schema once. Fills unsupported (keywords this script cannot check) and errors (schema is malformed)."""
    if not isinstance(schema, dict):
        errors.append("%s: a schema must be an object" % path)
        return
    for key, val in schema.items():
        if key in ANNOTATIONS:
            continue
        if key not in SUPPORTED:
            unsupported.append({"path": path, "keyword": key})
            continue
        if key == "type":
            names = val if isinstance(val, list) else [val]
            if not names or not all(isinstance(x, str) and x in TYPE_NAMES for x in names):
                errors.append("%s: type must be one of %s or a list of them" % (path, sorted(TYPE_NAMES)))
        elif key == "properties":
            if not isinstance(val, dict):
                errors.append("%s: properties must be an object" % path)
            else:
                for name, sub in val.items():
                    check_schema(sub, path + "." + name, unsupported, errors)
        elif key == "required":
            if not isinstance(val, list) or not all(isinstance(x, str) for x in val):
                errors.append("%s: required must be a list of strings" % path)
        elif key == "additionalProperties":
            if not isinstance(val, bool):
                unsupported.append({"path": path, "keyword": "additionalProperties (schema value)"})
        elif key == "enum":
            if not isinstance(val, list) or not val:
                errors.append("%s: enum must be a non-empty list" % path)
        elif key in ("minimum", "maximum"):
            if isinstance(val, bool) or not isinstance(val, (int, float)):
                errors.append("%s: %s must be a number" % (path, key))
        elif key == "items":
            if isinstance(val, dict):
                check_schema(val, path + "[]", unsupported, errors)
            else:
                unsupported.append({"path": path, "keyword": "items (tuple form)"})
        elif key in ("minItems", "maxItems", "minLength", "maxLength"):
            if isinstance(val, bool) or not isinstance(val, int) or val < 0:
                errors.append("%s: %s must be a non-negative integer" % (path, key))
        elif key == "pattern":
            try:
                re.compile(val)
            except (re.error, TypeError) as exc:
                errors.append("%s: pattern does not compile (%s)" % (path, exc))


def infer_schema(example):
    """Schema from an example object: types from values, every key required, no extra keys."""
    t = json_type(example)
    if t == "object":
        return {"type": "object", "properties": {k: infer_schema(v) for k, v in example.items()},
                "required": list(example.keys()), "additionalProperties": False}
    if t == "array":
        s = {"type": "array"}
        if example:
            s["items"] = infer_schema(example[0])
        return s
    return {"type": t}


def short(v):
    r = json.dumps(v, ensure_ascii=False)
    return r if len(r) <= 40 else r[:37] + "..."


def validate(value, schema, path, out):
    """Append (class, path, message) tuples for every violation under this node."""
    if "type" in schema:
        names = schema["type"] if isinstance(schema["type"], list) else [schema["type"]]
        if not any(type_ok(value, t) for t in names):
            numeric_expected = any(t in ("number", "integer") for t in names)
            if numeric_expected and isinstance(value, str) and NUMERIC_STRING_RE.match(value):
                out.append(("number_as_string", path,
                            "%s is the string %s, expected %s" % (path, short(value), "/".join(names))))
            else:
                out.append(("wrong_type", path,
                            "%s is %s, expected %s" % (path, json_type(value), "/".join(names))))
            return
    if isinstance(value, dict):
        props = schema.get("properties", {})
        for name in schema.get("required", []):
            if name not in value:
                out.append(("missing_field", path + "." + name, "%s.%s is required but missing" % (path, name)))
        for name, sub in props.items():
            if name in value:
                validate(value[name], sub, path + "." + name, out)
        if schema.get("additionalProperties") is False:
            for name in value:
                if name not in props:
                    out.append(("extra_field", path + "." + name, "%s.%s is not allowed" % (path, name)))
    if isinstance(value, list):
        n = len(value)
        if "minItems" in schema and n < schema["minItems"]:
            if n == 0:
                out.append(("empty_array", path, "%s is empty, expected at least %d item(s)" % (path, schema["minItems"])))
            else:
                out.append(("array_size", path, "%s has %d item(s), expected at least %d" % (path, n, schema["minItems"])))
        if "maxItems" in schema and n > schema["maxItems"]:
            out.append(("array_size", path, "%s has %d item(s), expected at most %d" % (path, n, schema["maxItems"])))
        if isinstance(schema.get("items"), dict):
            for i, item in enumerate(value):
                validate(item, schema["items"], "%s[%d]" % (path, i), out)
    if isinstance(value, bool):
        pass
    elif isinstance(value, (int, float)):
        if "minimum" in schema and value < schema["minimum"]:
            out.append(("out_of_range", path, "%s is %s, minimum is %s" % (path, short(value), schema["minimum"])))
        if "maximum" in schema and value > schema["maximum"]:
            out.append(("out_of_range", path, "%s is %s, maximum is %s" % (path, short(value), schema["maximum"])))
    if isinstance(value, str):
        if "minLength" in schema and len(value) < schema["minLength"]:
            out.append(("length_violation", path, "%s has %d character(s), minimum is %d" % (path, len(value), schema["minLength"])))
        if "maxLength" in schema and len(value) > schema["maxLength"]:
            out.append(("length_violation", path, "%s has %d character(s), maximum is %d" % (path, len(value), schema["maxLength"])))
        if "pattern" in schema and not re.search(schema["pattern"], value):
            out.append(("pattern_mismatch", path, "%s value %s does not match pattern %s" % (path, short(value), schema["pattern"])))
    if "enum" in schema and not any(jeq(value, e) for e in schema["enum"]):
        out.append(("enum_violation", path, "%s is %s, allowed: %s" % (path, short(value), short(schema["enum"]))))
    if "const" in schema and not jeq(value, schema["const"]):
        out.append(("enum_violation", path, "%s is %s, must be %s" % (path, short(value), short(schema["const"]))))


def norm_field(path):
    return re.sub(r"\[\d+\]", "[]", path)


# ---------------------------------------------------------------- records

def read_records(path, fmt, field):
    """Yield (record_id, text). Returns (records, blank_lines_skipped, input_files)."""
    records = []
    blanks = 0
    files = []
    if os.path.isdir(path):
        if fmt == "jsonl":
            raise UsageError("--format jsonl needs a file, but %s is a folder" % path)
        for name in sorted(os.listdir(path)):
            full = os.path.join(path, name)
            if os.path.isfile(full) and os.path.splitext(name)[1].lower() in INPUT_SUFFIXES:
                with open(full, "rb") as fh:
                    records.append((name, fh.read().decode("utf-8", errors="replace")))
                files.append(full)
        return records, blanks, files
    if not os.path.isfile(path):
        raise UsageError("input not found: %s" % path)
    if fmt == "files":
        raise UsageError("--format files needs a folder, but %s is a file" % path)
    with open(path, "rb") as fh:
        raw = fh.read().decode("utf-8", errors="replace")
    files.append(path)
    for lineno, line in enumerate(raw.splitlines(), 1):
        if not line.strip():
            blanks += 1
            continue
        text = line
        try:
            obj = json.loads(line)
        except ValueError:
            obj = None
        if isinstance(obj, str):
            text = obj
        elif isinstance(obj, dict) and isinstance(obj.get(field), str):
            text = obj[field]
        records.append(("line %d" % lineno, text))
    return records, blanks, files


def wilson(k, n):
    if n == 0:
        return [0.0, 0.0]
    p = k / n
    z2 = WILSON_Z ** 2
    centre = (p + z2 / (2 * n)) / (1 + z2 / n)
    half = WILSON_Z * math.sqrt(p * (1 - p) / n + z2 / (4 * n * n)) / (1 + z2 / n)
    return [round(max(0.0, centre - half), 4), round(min(1.0, centre + half), 4)]


def evaluate(text, schema, allowed):
    """Run one record. Returns dict(failures=[(class, path, message)], repairs, notes)."""
    res = process_text(text, allowed)
    failures = []
    if res["status"] == "ok":
        for key in res["dups"]:
            failures.append(("duplicate_key", "$.." + key, "key %s appears more than once in an object" % short(key)))
        validate(res["value"], schema, "$", failures)
        return {"failures": failures, "repairs": res["repairs"], "notes": res["notes"]}
    status = res["status"]
    if status == "empty":
        failures.append(("empty_output", "$", "the reply was empty"))
    elif status == "no_json_found":
        failures.append(("no_json_found", "$", "the reply contains no JSON value"))
    elif status == "truncated":
        failures.append(("truncated", "$", "the JSON is cut off before it closes"))
    else:
        msg = "not valid JSON: %s" % res.get("error", "")
        if res.get("fixable_by"):
            msg += " (would parse with rung: %s)" % ", ".join(res["fixable_by"])
        failures.append(("invalid_syntax", "$", msg))
    return {"failures": failures, "repairs": [], "notes": res.get("notes", [])}


def retry_message(failures):
    lines = []
    for _cls, _path, msg in failures[:MAX_RETRY_LINES]:
        lines.append("- " + msg[:MAX_MSG_CHARS])
    if len(failures) > MAX_RETRY_LINES:
        lines.append("- and %d more problem(s) of the same kinds" % (len(failures) - MAX_RETRY_LINES))
    return ("Your previous reply was rejected by the program that parses it.\n"
            "Problems found:\n" + "\n".join(lines) + "\n"
            "Reply again with exactly one JSON value that satisfies the schema. Put nothing before or after "
            "it: no code fences, no comments, no explanation. Keep every value that was not listed as a "
            "problem unchanged.")


def same_path(a, b):
    return os.path.normcase(os.path.realpath(a)) == os.path.normcase(os.path.realpath(b))


def guard_output(path, protected, other_outputs, force):
    for p in protected:
        if same_path(path, p):
            raise UsageError("refusing to write %s: it is an input (%s)" % (path, p))
    parent = os.path.dirname(os.path.abspath(path))
    for p in protected:
        if os.path.isdir(p) and same_path(parent, p):
            raise UsageError("refusing to write %s: it is inside the input folder" % path)
    for o in other_outputs:
        if o and same_path(path, o):
            raise UsageError("report, log and retry paths must differ from each other")
    if os.path.exists(path) and not force:
        raise UsageError("%s exists; pass --force to replace it" % path)


def run(args):
    allow_arg = args.allow.strip().lower()
    if allow_arg == "none":
        allowed = ()
    elif allow_arg == "all":
        allowed = ALL_RUNGS
    else:
        allowed = tuple(x.strip() for x in allow_arg.split(",") if x.strip())
        bad = [x for x in allowed if x not in ALL_RUNGS]
        if bad:
            raise UsageError("unknown rung(s) %s; choose from %s, or none, or all" % (bad, ", ".join(ALL_RUNGS)))

    protected = [args.input]
    if args.schema:
        protected.append(args.schema)
    if args.example:
        protected.append(args.example)
    records, blanks, files = read_records(args.input, args.format, args.field)
    protected.extend(files)
    outs = [args.report, args.log, args.retry_out]
    for p in outs:
        if p:
            guard_output(p, protected, [o for o in outs if o is not p], args.force)

    try:
        with open(args.schema or args.example, "rb") as fh:
            source = json.loads(fh.read().decode("utf-8-sig"))
    except (OSError, ValueError) as exc:
        raise UsageError("cannot read %s as JSON: %s" % (args.schema or args.example, exc))
    schema = source if args.schema else infer_schema(source)
    unsupported, schema_errors = [], []
    check_schema(schema, "$", unsupported, schema_errors)
    if schema_errors:
        raise UsageError("schema problem: " + "; ".join(schema_errors))
    if unsupported and not args.allow_unsupported:
        raise UsageError("schema uses keywords this script cannot check: %s. Rewrite the schema without "
                         "them, or pass --allow-unsupported to validate the rest and keep them listed in "
                         "the report." % ", ".join("%s at %s" % (u["keyword"], u["path"]) for u in unsupported))
    if not records:
        raise UsageError("no records found in %s" % args.input)

    by_class, by_field, repairs_count, notes_count = {}, {}, {}, {}
    examples, seen_examples = [], set()
    log_rows, retry_rows = [], []
    valid = clean_valid = 0
    for rec_id, text in records:
        ev = evaluate(text, schema, allowed)
        fails = ev["failures"]
        for r in ev["repairs"]:
            repairs_count[r] = repairs_count.get(r, 0) + 1
        for note in set(ev["notes"]):
            notes_count[note] = notes_count.get(note, 0) + 1
        if not fails:
            valid += 1
            if not ev["repairs"]:
                clean_valid += 1
        classes = set()
        fields = set()
        for cls, path, msg in fails:
            classes.add(cls)
            fields.add(norm_field(path))
            key = (cls, norm_field(path))
            if key not in seen_examples and len(examples) < args.max_examples:
                seen_examples.add(key)
                examples.append({"record": rec_id, "class": cls, "field": norm_field(path), "message": msg,
                                 "excerpt": re.sub(r"\s+", " ", text.strip())[:EXCERPT_CHARS]})
        for cls in classes:
            by_class[cls] = by_class.get(cls, 0) + 1
        for fld in fields:
            by_field[fld] = by_field.get(fld, 0) + 1
        log_rows.append({"record": rec_id, "valid": not fails, "repairs": ev["repairs"], "notes": ev["notes"],
                         "failures": [{"class": c, "field": norm_field(p), "message": m} for c, p, m in fails]})
        if fails:
            retry_rows.append({"record": rec_id, "failure_classes": sorted(classes), "retry_message": retry_message(fails)})

    n = len(records)
    report = {
        "tool": "validate_outputs.py", "version": VERSION,
        "schema_source": "schema" if args.schema else "inferred_from_example",
        "allowed_repairs": list(allowed),
        "n": n, "valid": valid, "rate": round(valid / n, 4), "rate_ci95": wilson(valid, n),
        "clean_valid": clean_valid, "valid_after_repair": valid - clean_valid,
        "repairs_applied": dict(sorted(repairs_count.items())),
        "failures_by_class": dict(sorted(by_class.items(), key=lambda kv: (-kv[1], kv[0]))),
        "failures_by_field": dict(sorted(by_field.items(), key=lambda kv: (-kv[1], kv[0]))),
        "notes": dict(sorted(notes_count.items())),
        "blank_lines_skipped": blanks,
        "unsupported_keywords": unsupported,
        "examples": examples,
    }
    if args.report:
        write_text(args.report, json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    if args.log:
        write_text(args.log, "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in log_rows))
    if args.retry_out:
        write_text(args.retry_out, "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in retry_rows))
    return report, (0 if valid == n else 1)


def write_text(path, text):
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)


def build_parser():
    p = argparse.ArgumentParser(description="Validate model outputs against a JSON Schema subset.")
    src = p.add_mutually_exclusive_group(required=True)
    src.add_argument("--schema", help="JSON Schema file (supported subset only)")
    src.add_argument("--example", help="an example object; a schema is inferred from it")
    p.add_argument("--input", required=True, help="JSONL file or folder of text files")
    p.add_argument("--format", choices=("auto", "jsonl", "files"), default="auto")
    p.add_argument("--field", default="output", help="JSONL object key holding the model text (default: output)")
    p.add_argument("--allow", default=",".join(DEFAULT_ALLOW),
                   help="repair rungs to allow: comma list of %s, or none, or all (default: fence,prose)" % ",".join(ALL_RUNGS))
    p.add_argument("--allow-unsupported", action="store_true", help="validate with the supported keywords and list the rest")
    p.add_argument("--max-examples", type=int, default=5)
    p.add_argument("--report", help="also write the JSON report to this new file")
    p.add_argument("--log", help="write one JSONL row per record, with the repairs applied")
    p.add_argument("--retry-out", help="write one retry message per failed record (JSONL)")
    p.add_argument("--force", action="store_true", help="replace an existing output file (never an input)")
    return p


def main(argv=None):
    args = build_parser().parse_args(argv)
    try:
        report, code = run(args)
    except UsageError as exc:
        sys.stderr.write("error: %s\n" % exc)
        return 2
    sys.stdout.write(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    return code


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except (AttributeError, OSError):
        pass
    sys.exit(main())
