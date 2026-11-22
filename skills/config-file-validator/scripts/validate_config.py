#!/usr/bin/env python3
"""Validate one or more hand-edited config files, optionally against a schema.

Usage:
    python validate_config.py [--schema SCHEMA.json] [--format FMT] [--env-file F.env]
                              [--check-paths] [--base-dir DIR] [--report OUT.json [--force]]
                              FILE [FILE ...]

Formats (chosen by extension, or --format json|toml|ini|env|yaml):
    json   standard library; line and column on failure; duplicate keys
    toml   tomllib (Python 3.11 or newer)
    ini    configparser (strict, no interpolation); also .cfg
    env    .env line grammar (KEY=value, export, quotes, inline comments)
    yaml   a documented SUBSET only (block mappings, block lists of scalars, flow lists
           of scalars, quoted and plain scalars, comments). Anything outside the subset
           (anchors, tags, block scalars, flow mappings, lists of mappings, multi-document)
           is reported as class "unsupported_yaml" and the file is not validated further.

Reads: the config files, the schema, the optional --env-file. Prints one JSON document to
stdout. Writes a file only when --report is given; the report path must not resolve to any
input (config, schema or env file) and --force does not change that. With --check-paths it
asks the filesystem whether named paths exist; it never opens them.
Never reads environment variables, never uses the network, never runs a subprocess.

Secrets: values that look like keys or tokens are never printed; messages and
masked_values show only the first two characters and the length.

Exit codes: 0 no errors (warnings allowed), 1 at least one error finding, 2 usage or I/O problem.
"""
import argparse
import difflib
import json
import os
import re
import sys

try:
    import tomllib
except ImportError:  # Python older than 3.11
    tomllib = None
import configparser

MAX_BYTES = 2_000_000          # refuse files that cannot be hand-edited configs
PORT_MIN, PORT_MAX = 1, 65535  # TCP/UDP port range; 0 is reserved, 65536 does not exist
SPEC_FIELDS = {"type", "required", "enum", "min", "max", "pattern", "items", "description"}
TYPES = {"string", "int", "float", "bool", "array", "object", "path", "datetime"}
BOOL_WORDS = {"true", "false", "1", "0", "yes", "no", "on", "off"}  # configparser / dotenv spellings
YAML11_BOOLS = {"yes", "no", "on", "off", "y", "n"}

SECRET_PATTERNS = [
    ("AWS access key id", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("private key block", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    ("sk- style API token", re.compile(r"\bsk-[A-Za-z0-9_-]{20,}")),
    ("GitHub token", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{36,}")),
    ("Slack token", re.compile(r"\bxox[abprs]-[A-Za-z0-9-]{10,}")),
    ("Google API key", re.compile(r"\bAIza[0-9A-Za-z_-]{35}\b")),
    ("JSON web token", re.compile(r"\beyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}")),
    ("password inside a URL", re.compile(r"[A-Za-z][A-Za-z0-9+.-]*://[^/\s:@]+:[^/\s@]+@")),
]
SECRET_KEY = re.compile(r"(password|passwd|secret|token|api[_-]?key|private[_-]?key|access[_-]?key|credential)", re.I)
SECRET_KEY_EXEMPT = re.compile(r"(_file|_path|_env|_var|_name|_ttl|_expiry|_url|_header|_ms|_seconds|_len|_length)$", re.I)
PH_BRACE = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)(:?[-=?+][^}]*)?\}")
PH_BARE = re.compile(r"^\$([A-Za-z_][A-Za-z0-9_]*)$")
PH_TEMPLATE = re.compile(r"\{\{[^}]*\}\}")
PH_ANGLE = re.compile(r"^<[^<>]+>$")
PH_LITERAL = re.compile(r"^(changeme|change[_-]?me|your[_ -].*|.*[_-]here|todo|tbd|replace[_-]?me|xxx+|\*{3,})$", re.I)
ENV_KEY = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


class Ctx:
    """State for one file: findings, line knowledge, masked values."""

    def __init__(self, path, fmt, text, env_vars, masked, base_dir, check_paths):
        self.path, self.fmt, self.lines = path, fmt, text.splitlines()
        self.findings, self.linemap = [], {}
        self.env_vars, self.masked = env_vars, masked
        self.base_dir, self.check_paths = base_dir, check_paths

    def add(self, cls, message, fix, line=None, col=None, key=None, severity="error"):
        self.findings.append({"line": line, "col": col, "class": cls, "severity": severity,
                              "key": key, "message": message, "fix": fix})

    def line_of(self, key):
        if key in self.linemap:
            return self.linemap[key]
        leaf = key.split(".")[-1]
        pat = re.compile(r'^\s*["\']?' + re.escape(leaf) + r'["\']?\s*[:=]')
        hits = [i for i, ln in enumerate(self.lines, 1) if pat.match(ln)]
        return hits[0] if len(hits) == 1 else None  # None = ambiguous, never guess


def mask(value):
    s = str(value)
    return s[:2] + "***(len %d)" % len(s)


def secret_reason(key, value):
    """Return (reason, strength) when the value looks like a secret, else None."""
    if not isinstance(value, str) or not value:
        return None
    for name, rx in SECRET_PATTERNS:
        if rx.search(value):
            return name, "error"
    leaf = (key or "").split(".")[-1]
    if SECRET_KEY.search(leaf) and not SECRET_KEY_EXEMPT.search(leaf):
        if len(value) >= 8 and not value.isdigit() and not is_placeholder(value):
            return "secret-like key name holding a literal value", "warning"
    return None


def is_placeholder(s):
    s = s.strip()
    return bool(PH_BRACE.search(s) or PH_BARE.match(s) or PH_TEMPLATE.search(s) or PH_ANGLE.match(s) or PH_LITERAL.match(s))


def show(ctx, key, value):
    """Printable form of a value for messages: masked if it could be a secret."""
    if secret_reason(key, value) or (isinstance(value, str) and SECRET_KEY.search((key or "").split(".")[-1])):
        ctx.masked.setdefault((ctx.path, key), {"file": ctx.path, "key": key, "line": ctx.line_of(key),
                                                "masked": mask(value), "reason": "shown masked in messages"})
        return mask(value)
    r = repr(value)
    return r if len(r) <= 40 else r[:37] + "..."


def tname(v):
    if v is None:
        return "null"
    if isinstance(v, bool):
        return "bool"
    if isinstance(v, int):
        return "int"
    if isinstance(v, float):
        return "float"
    if isinstance(v, str):
        return "string"
    if isinstance(v, list):
        return "array"
    if isinstance(v, dict):
        return "object"
    return "datetime"


def pos_to_linecol(text, pos):
    line = text.count("\n", 0, pos) + 1
    col = pos - (text.rfind("\n", 0, pos) + 1) + 1
    return line, col


# ---------------------------------------------------------------- parsers

MAX_NUMBER_DIGITS = 400  # a hand-edited config never needs a longer number; Python refuses int() past 4300 digits


class InvalidNumber(ValueError):
    """A number that cannot be held or is absurdly long; ends the run with error "invalid_number"."""


def guard_int(s):
    if len(s) > MAX_NUMBER_DIGITS:
        raise InvalidNumber("integer with %d characters (limit %d)" % (len(s), MAX_NUMBER_DIGITS))
    return int(s)


def guard_float(s):
    if len(s) > MAX_NUMBER_DIGITS:
        raise InvalidNumber("number with %d characters (limit %d)" % (len(s), MAX_NUMBER_DIGITS))
    v = float(s)
    if v in (float("inf"), float("-inf")):
        raise InvalidNumber("number %s is outside the float range" % s[:40])
    return v


def parse_json(text, ctx):
    dups = []

    def hook(pairs):
        seen = set()
        for k, _ in pairs:
            if k in seen and k not in dups:
                dups.append(k)
            seen.add(k)
        return dict(pairs)

    consts = []

    def const(c):
        consts.append(c)
        return 0.0

    try:
        data = json.loads(text, object_pairs_hook=hook, parse_constant=const,
                          parse_int=guard_int, parse_float=guard_float)
    except json.JSONDecodeError as e:
        pos = e.pos
        j = pos - 1
        while j >= 0 and text[j] in " \t\r\n":
            j -= 1
        if j >= 0 and text[j] == "," and text[pos:pos + 1] in ("}", "]"):
            ln, col = pos_to_linecol(text, j)
            ctx.add("syntax", "trailing comma before a closing bracket (JSON forbids it)",
                    "delete the comma on this line", ln, col)
        elif text[pos:pos + 2] in ("//", "/*") or text[pos:pos + 1] == "#":
            ctx.add("syntax", "comment in a JSON file (JSON has no comments)",
                    "delete the comment, or move the note into a documented key such as \"_comment\" if the consumer ignores unknown keys",
                    e.lineno, e.colno)
        elif text[pos:pos + 1] == "'":
            ctx.add("syntax", "single-quoted string (JSON needs double quotes)", "replace the single quotes with double quotes",
                    e.lineno, e.colno)
        else:
            ctx.add("syntax", "JSON parse error: " + e.msg, "fix the character at this position; look one line above if it looks fine (a missing comma or quote is reported at the next token)",
                    e.lineno, e.colno)
        return None
    for k in dups:
        hits = [i for i, ln in enumerate(ctx.lines, 1) if re.search(r'"' + re.escape(k) + r'"\s*:', ln)]
        ln = hits[1] if len(hits) > 1 else None
        ctx.add("duplicate_key", "key %r appears more than once in the same object; most parsers keep only the last value" % k,
                "keep one occurrence and decide which value is intended; do not assume the later one is the right one", ln, None, k)
    for c in consts:
        ctx.add("suspicious_value", "%s is not valid JSON (Python accepts it, other parsers reject it)" % c,
                "use null or a real number", None, None, None, "warning")
    if not isinstance(data, dict):
        ctx.add("wrong_type", "top level is %s, a config file is normally an object" % tname(data),
                "wrap the content in an object", 1, 1, None, "warning")
        return None
    return data


def parse_toml(text, ctx):
    if tomllib is None:
        ctx.add("unsupported", "TOML needs Python 3.11 or newer (tomllib)", "run the script with Python 3.11+", severity="error")
        return None
    try:
        return tomllib.loads(text)
    except tomllib.TOMLDecodeError as e:
        msg = str(e)
        m = re.search(r"\(at line (\d+), column (\d+)\)", msg)
        line = int(m.group(1)) if m else (len(ctx.lines) or 1)
        col = int(m.group(2)) if m else None
        base = re.sub(r"\s*\(at .*\)$", "", msg)
        if re.search(r"Cannot overwrite|Cannot declare|already|Duplicate", msg):
            ctx.add("duplicate_key", "TOML key or table defined twice: " + base,
                    "keep one definition; merge the two tables if both were intended", line, col)
        else:
            ctx.add("syntax", "TOML parse error: " + base, "fix the syntax at this position (strings need quotes, dates need the full form)", line, col)
        return None


def parse_ini(text, ctx):
    cp = configparser.ConfigParser(interpolation=None, strict=True)
    cp.optionxform = str  # keep key case
    try:
        cp.read_string(text)
    except configparser.DuplicateSectionError as e:
        ctx.add("duplicate_key", "section [%s] appears twice" % e.section, "merge the two sections", e.lineno, None, e.section)
        return None
    except configparser.DuplicateOptionError as e:
        ctx.add("duplicate_key", "key %r appears twice in [%s]" % (e.option, e.section), "keep one line; decide which value is intended",
                e.lineno, None, "%s.%s" % (e.section, e.option))
        return None
    except configparser.MissingSectionHeaderError as e:
        ctx.add("syntax", "key found before any [section] header", "add a [section] line above this key", e.lineno)
        return None
    except configparser.ParsingError as e:
        for ln, _ in e.errors:
            ctx.add("syntax", "line is neither a [section], a key = value pair nor a comment", "write it as key = value", ln)
        return None
    data, section = {}, None
    for i, raw in enumerate(ctx.lines, 1):
        s = raw.strip()
        if not s or s[0] in ";#":
            continue
        m = re.match(r"^\[(.+)\]$", s)
        if m and not raw[0].isspace():
            section = m.group(1)
            continue
        m = re.match(r"^([^=:\s][^=:]*?)\s*[=:]\s*(.*)$", raw) if not raw[0].isspace() else None
        if m and section is not None:
            path = "%s.%s" % (section, m.group(1))
            ctx.linemap[path] = i
            if re.search(r"\s[;#]", m.group(2)):
                ctx.add("suspicious_value", "text after ' ;' or ' #' is part of the value here, not a comment (configparser keeps it)",
                        "move the comment to its own line", i, None, path, "warning")
    for sec in cp.sections():
        data[sec] = dict(cp.items(sec))
    return data


def parse_env(text, ctx):
    data = {}
    for i, raw in enumerate(ctx.lines, 1):
        s = raw.strip()
        if not s or s.startswith("#"):
            continue
        if s.startswith("export ") or s.startswith("export\t"):
            s = s[7:].lstrip()
        m = re.match(r"^([^=\s]+)(\s*)=(\s*)(.*)$", s)
        if not m:
            ctx.add("syntax", "line has no '=' (expected KEY=value)", "write KEY=value, or start the line with # if it is a note", i)
            continue
        key, sp1, sp2, rest = m.groups()
        if not ENV_KEY.match(key):
            ctx.add("syntax", "invalid variable name %r (letters, digits and underscore; not starting with a digit)" % key,
                    "rename the key", i, None, key)
            continue
        if sp1 or sp2:
            ctx.add("syntax", "spaces around '=' (shells reject it, loaders disagree)", "write KEY=value with no spaces", i, None, key, "warning")
        value = rest
        if rest[:1] in ('"', "'"):
            q = rest[0]
            j, closed = 1, False
            while j < len(rest):
                if q == '"' and rest[j] == "\\":
                    j += 2
                    continue
                if rest[j] == q:
                    closed = True
                    break
                j += 1
            if not closed:
                ctx.add("syntax", "quoted value is never closed", "add the closing %s" % q, i, None, key)
                continue
            value = rest[1:j]
            tail = rest[j + 1:].strip()
            if tail and not tail.startswith("#"):
                ctx.add("syntax", "text after the closing quote", "remove it or put it inside the quotes", i, None, key, "warning")
        else:
            value = re.split(r"\s+#", rest, 1)[0].strip()
            if re.search(r"\s", value):
                ctx.add("suspicious_value", "unquoted value contains spaces (breaks when the file is sourced by a shell)",
                        "wrap the value in quotes", i, None, key, "warning")
        if key in data:
            ctx.add("duplicate_key", "%s is defined twice; the later line wins in most loaders" % key,
                    "keep one definition", i, None, key)
        data[key] = value
        ctx.linemap[key] = i
    return data


def strip_comment(s):
    q = None
    for i, c in enumerate(s):
        if q:
            if c == q:
                q = None
        elif c in "\"'":
            q = c
        elif c == "#" and (i == 0 or s[i - 1] in " \t"):
            return s[:i]
    return s


def yaml_scalar(tok, ctx, line, key):
    t = tok.strip()
    if t[:1] in ('"', "'") and len(t) >= 2 and t[-1] == t[0]:
        return t[1:-1]
    if t.startswith("["):
        if not t.endswith("]"):
            ctx.add("syntax", "flow list is not closed on the same line", "close the list with ] or use a block list", line, None, key)
            return None
        inner = t[1:-1].strip()
        return [yaml_scalar(p, ctx, line, key) for p in split_flow(inner)] if inner else []
    low = t.lower()
    if t in ("", "~") or low == "null":
        return None
    if low in ("true", "false"):
        return low == "true"
    if low in YAML11_BOOLS:
        ctx.add("suspicious_value", "%r is a boolean in YAML 1.1 loaders and a string in YAML 1.2 loaders" % t,
                "quote it if it is text (\"%s\"), or write true/false if it is a flag" % t, line, None, key, "warning")
        return t
    if re.match(r"^[+-]?(0|[1-9]\d*)$", t):
        return int(t)
    if re.match(r"^[+-]?\d+\.\d+([eE][+-]?\d+)?$", t):
        return float(t)
    return t


def split_flow(s):
    parts, cur, q = [], "", None
    for c in s:
        if q:
            cur += c
            if c == q:
                q = None
        elif c in "\"'":
            q = c
            cur += c
        elif c == ",":
            parts.append(cur)
            cur = ""
        else:
            cur += c
    parts.append(cur)
    return [p.strip() for p in parts]


YAML_KEY = re.compile(r"""^("[^"]*"|'[^']*'|[^\s:#'"\[\]{},&*!|>%@`-][^:]*?)\s*:(?:\s+(.*))?$""")


def parse_yaml(text, ctx):
    entries, seen_content = [], False
    for i, raw in enumerate(ctx.lines, 1):
        lead = raw[: len(raw) - len(raw.lstrip(" \t"))]
        body = strip_comment(raw).rstrip()
        if not body.strip():
            continue
        if "\t" in lead:
            ctx.add("syntax", "tab used for indentation (YAML allows spaces only)", "indent with spaces", i)
            return None
        t = body.strip()
        if t in ("---", "...") :
            if seen_content:
                ctx.add("unsupported_yaml", "multi-document file", "split it into one file per document, or use a full YAML parser", i)
                return None
            continue
        seen_content = True
        bad = None
        if re.search(r"(^|[\s:\-])[&*][A-Za-z0-9_]", t):
            bad = "anchor or alias (& or *)"
        elif re.search(r"(^|[\s:])![A-Za-z!]", t):
            bad = "tag (!)"
        elif re.search(r":\s+[|>][+-]?\d*$", t) or re.match(r"^-\s+[|>]", t):
            bad = "block scalar (| or >)"
        elif re.search(r":\s+\{", t) or t.startswith("{") or re.match(r"^-\s+\{", t):
            bad = "flow mapping ({...})"
        elif re.match(r"^-\s+\S.*:(\s|$)", t) and not re.match(r"^-\s+[\"'\[]", t):
            bad = "list of mappings"
        elif t.startswith("? "):
            bad = "complex key"
        if bad:
            ctx.add("unsupported_yaml", "outside the supported YAML subset: " + bad,
                    "validate this file with a full YAML parser; this script does not guess", i)
            return None
        entries.append((i, len(raw) - len(raw.lstrip(" ")), t))
    pos = [0]

    def block(indent, prefix):
        if pos[0] >= len(entries):
            return None
        if entries[pos[0]][2].startswith("-"):
            return parse_list(indent, prefix)
        return parse_map(indent, prefix)

    def parse_list(indent, prefix):
        out = []
        while pos[0] < len(entries) and entries[pos[0]][1] == indent and entries[pos[0]][2].startswith("-"):
            ln, _, t = entries[pos[0]]
            pos[0] += 1
            out.append(yaml_scalar(t[1:], ctx, ln, prefix.rstrip(".") or None))
        return out

    def parse_map(indent, prefix):
        out = {}
        while pos[0] < len(entries):
            ln, ind, t = entries[pos[0]]
            if ind < indent:
                break
            if ind > indent:
                ctx.add("syntax", "unexpected indentation", "align this line with its siblings", ln)
                raise ValueError
            m = YAML_KEY.match(t)
            if not m:
                ctx.add("syntax", "line is not a 'key: value' pair", "write key: value (a space is required after the colon)", ln)
                raise ValueError
            k = m.group(1)
            if k[:1] in "\"'":
                k = k[1:-1]
            path = prefix + k
            pos[0] += 1
            if k in out:
                ctx.add("duplicate_key", "key %r appears twice at this level; most loaders keep the last" % k,
                        "keep one occurrence", ln, None, path)
            ctx.linemap[path] = ln
            v = m.group(2)
            if v is None or v.strip() == "":
                if pos[0] < len(entries) and entries[pos[0]][1] > indent:
                    out[k] = block(entries[pos[0]][1], path + ".")
                elif pos[0] < len(entries) and entries[pos[0]][1] == indent and entries[pos[0]][2].startswith("-"):
                    out[k] = parse_list(indent, path + ".")
                else:
                    out[k] = None
            else:
                out[k] = yaml_scalar(v, ctx, ln, path)
        return out

    if not entries:
        return {}
    try:
        data = parse_map(entries[0][1], "")
    except ValueError:
        return None
    if pos[0] < len(entries):
        ctx.add("syntax", "unexpected content after the top-level mapping", "check indentation", entries[pos[0]][0])
        return None
    return data


# ---------------------------------------------------------------- schema

def load_schema(path):
    try:
        with open(path, encoding="utf-8-sig") as fh:
            sch = json.load(fh)
    except (OSError, ValueError) as e:
        raise SystemExit("schema %s: cannot read as JSON (%s)" % (path, e))
    if not isinstance(sch, dict) or not isinstance(sch.get("keys"), dict):
        raise SystemExit("schema %s: expected an object with a \"keys\" object" % path)
    extra = set(sch) - {"keys", "allow_unknown"}
    if extra:
        raise SystemExit("schema %s: unknown top-level field(s) %s (allowed: keys, allow_unknown)" % (path, sorted(extra)))
    for k, spec in sch["keys"].items():
        if not isinstance(spec, dict):
            raise SystemExit("schema key %r: spec must be an object" % k)
        bad = set(spec) - SPEC_FIELDS
        if bad:
            raise SystemExit("schema key %r: unknown field(s) %s (allowed: %s)" % (k, sorted(bad), sorted(SPEC_FIELDS)))
        if spec.get("type") not in TYPES:
            raise SystemExit("schema key %r: type must be one of %s" % (k, sorted(TYPES)))
        if "pattern" in spec:
            try:
                re.compile(spec["pattern"])
            except re.error as e:
                raise SystemExit("schema key %r: bad regex (%s)" % (k, e))
        if "enum" in spec and not isinstance(spec["enum"], list):
            raise SystemExit("schema key %r: enum must be a list" % k)
    return sch


def flatten(d, prefix=""):
    for k, v in d.items():
        p = prefix + str(k)
        if isinstance(v, dict) and v:
            yield from flatten(v, p + ".")
        else:
            yield p, v


def coerce(fmt, typ, v):
    """Return (ok, value). env/ini values are strings and are parsed to the wanted type."""
    if fmt in ("env", "ini") and isinstance(v, str):
        s = v.strip()
        if typ == "int":
            return (True, int(s)) if re.fullmatch(r"[+-]?\d+", s) else (False, v)
        if typ == "float":
            return (True, float(s)) if re.fullmatch(r"[+-]?\d+(\.\d+)?([eE][+-]?\d+)?", s) else (False, v)
        if typ == "bool":
            return (True, s.lower() in ("true", "1", "yes", "on")) if s.lower() in BOOL_WORDS else (False, v)
        if typ in ("string", "path"):
            return True, v
        return False, v
    got = tname(v)
    if typ == "float":
        return got in ("int", "float"), v
    if typ == "path":
        return got == "string", v
    return got == typ, v


def check_schema(ctx, data, schema):
    keys = schema["keys"]
    flat = dict(flatten(data))
    fmt = ctx.fmt
    for key, spec in keys.items():
        present = key in flat or (key in dict(_all_paths(data)))
        value = dict(_all_paths(data)).get(key)
        line = ctx.line_of(key)
        if not present:
            if spec.get("required"):
                ctx.add("missing_required", "required key %r is absent" % key,
                        "add it with a real value; a missing secret is never invented, ask the owner", None, None, key)
            continue
        empty = value is None or (isinstance(value, str) and not value.strip()) or value == [] or value == {}
        if empty:
            if spec.get("required"):
                ctx.add("empty_value", "required key %r is present but empty" % key,
                        "give it a value; do not guess a secret or an address", line, None, key)
            continue
        typ = spec["type"]
        ok, cv = coerce(fmt, typ, value)
        if not ok:
            fix = "use a value of type %s" % typ
            if fmt in ("json", "toml", "yaml") and isinstance(value, str):
                if typ == "bool" and value.lower() in ("true", "false"):
                    fix = "write %s without quotes" % value.lower()
                elif typ in ("int", "float") and re.fullmatch(r"[+-]?\d+(\.\d+)?", value.strip()):
                    fix = "write %s without quotes" % value.strip()
            ctx.add("wrong_type", "key %r should be %s but is %s (%s)" % (key, typ, tname(value), show(ctx, key, value)),
                    fix, line, None, key)
            continue
        if typ in ("int", "float"):
            if "min" in spec and cv < spec["min"]:
                ctx.add("out_of_range", "key %r is %s, below the minimum %s" % (key, cv, spec["min"]), "raise it to at least %s" % spec["min"], line, None, key)
            if "max" in spec and cv > spec["max"]:
                ctx.add("out_of_range", "key %r is %s, above the maximum %s" % (key, cv, spec["max"]), "lower it to at most %s" % spec["max"], line, None, key)
        if "enum" in spec and cv not in spec["enum"]:
            ctx.add("bad_enum", "key %r is %s, allowed: %s" % (key, show(ctx, key, cv), json.dumps(spec["enum"])),
                    "pick one of the allowed values (case matters)", line, None, key)
        if "pattern" in spec and isinstance(cv, str) and not re.fullmatch(spec["pattern"], cv):
            ctx.add("bad_pattern", "key %r does not match the pattern %s" % (key, spec["pattern"]), "change the value to match", line, None, key)
        if typ == "array" and "items" in spec:
            for n, item in enumerate(cv):
                if not coerce(fmt, spec["items"], item)[0]:
                    ctx.add("wrong_type", "key %r item %d should be %s" % (key, n, spec["items"]), "fix the item", line, None, key)
    if not schema.get("allow_unknown"):
        objs = [k for k, s in keys.items() if s["type"] in ("object", "array")]
        for path, _ in flatten(data):
            if path in keys or any(path == o or path.startswith(o + ".") for o in objs):
                continue
            near = difflib.get_close_matches(path, [k for k in keys if k not in flat], n=1, cutoff=0.55)
            fix = "remove it, or add it to the schema if it is intended"
            if near:
                fix = "probably a misspelling of %r; rename it" % near[0]
            ctx.add("unknown_key", "key %r is not in the schema" % path, fix, ctx.line_of(path), None, path, "warning")


def _all_paths(d, prefix=""):
    for k, v in d.items():
        p = prefix + str(k)
        yield p, v
        if isinstance(v, dict):
            yield from _all_paths(v, p + ".")


def generic_checks(ctx, data, schema):
    specs = schema["keys"] if schema else {}
    env_known = set(data) if ctx.fmt == "env" else set()
    for path, value in list(flatten(data)):
        items = [(path, v) for v in value] if isinstance(value, list) else [(path, value)]
        spec = specs.get(path, {})
        for p, v in items:
            line = ctx.line_of(path)
            leaf = path.split(".")[-1]
            if isinstance(v, str):
                for m in PH_BRACE.finditer(v):
                    name, dflt = m.group(1), m.group(2)
                    if dflt:
                        continue
                    if (name in env_known and name != leaf) or (ctx.env_vars is not None and name in ctx.env_vars):
                        continue
                    sev = "error" if ctx.env_vars is not None else "warning"
                    why = ("not defined in this file or the --env-file" if ctx.env_vars is not None
                           else "no --env-file was given, so it cannot be resolved here")
                    ctx.add("unresolved_placeholder", "placeholder ${%s} is unresolved (%s)" % (name, why),
                            "define %s in the environment or env file, or give it a default with ${%s:-default}" % (name, name),
                            line, None, path, sev)
                bm = PH_BARE.match(v.strip())
                if bm and bm.group(1) not in env_known and not (ctx.env_vars is not None and bm.group(1) in ctx.env_vars):
                    ctx.add("unresolved_placeholder", "$%s looks like an unexpanded variable" % bm.group(1),
                            "define it, or quote it differently if the dollar sign is literal", line, None, path, "warning")
                if PH_TEMPLATE.search(v) or PH_ANGLE.match(v.strip()) or PH_LITERAL.match(v.strip()):
                    ctx.add("unresolved_placeholder", "value looks like a template placeholder left unfilled",
                            "replace it with the real value; never invent one", line, None, path, "warning")
                hit = secret_reason(path, v)
                if hit:
                    reason, sev = hit
                    ctx.masked.setdefault((ctx.path, path), {"file": ctx.path, "key": path, "line": line, "masked": mask(v), "reason": reason})
                    ctx.add("secret_plaintext", "plain-text secret, %s (value masked as %s)" % (reason, mask(v)),
                            "move it to the environment or a secrets store and reference it, e.g. ${NAME}; rotate it if the file was ever committed",
                            line, None, path, sev)
                if ctx.fmt in ("json", "toml", "yaml") and v.lower() in ("true", "false") and spec.get("type") not in ("bool", "string"):
                    ctx.add("suspicious_value", "boolean written as a quoted string (%s)" % show(ctx, path, v),
                            "write %s without quotes if it is a flag" % v.lower(), line, None, path, "warning")
                if v != v.strip() and v.strip():
                    ctx.add("suspicious_value", "value has leading or trailing whitespace", "trim it", line, None, path, "warning")
                if ctx.check_paths and (spec.get("type") == "path" or re.search(r"_(path|file|dir|directory)$", leaf, re.I)) and v.strip():
                    if not is_placeholder(v) and not v.startswith("~"):
                        target = v if os.path.isabs(v) else os.path.join(ctx.base_dir, v)
                        if not os.path.exists(target):
                            sev = "error" if spec.get("type") == "path" else "warning"
                            ctx.add("path_missing", "path %s does not exist (checked relative to %s)" % (show(ctx, path, v), ctx.base_dir),
                                    "create it, correct the path, or run from the directory the app uses", line, None, path, sev)
        if re.search(r"(^|[_.-])port$", leaf, re.I) and "min" not in spec and "max" not in spec and not isinstance(value, (list, dict)):
            ok, pv = coerce(ctx.fmt, "int", value) if value not in (None, "") else (False, None)
            if ok and not isinstance(pv, bool) and not (PORT_MIN <= pv <= PORT_MAX):
                ctx.add("out_of_range", "port %s is outside %d to %d" % (pv, PORT_MIN, PORT_MAX),
                        "use a port between %d and %d" % (PORT_MIN, PORT_MAX), ctx.line_of(path), None, path)


# ---------------------------------------------------------------- driver

PARSERS = {"json": parse_json, "toml": parse_toml, "ini": parse_ini, "env": parse_env, "yaml": parse_yaml}


def detect(path):
    base = os.path.basename(path).lower()
    ext = os.path.splitext(base)[1]
    if base == ".env" or base.startswith(".env.") or ext == ".env":
        return "env"
    return {".json": "json", ".toml": "toml", ".ini": "ini", ".cfg": "ini", ".yaml": "yaml", ".yml": "yaml"}.get(ext)


def read_text(path):
    if os.path.getsize(path) > MAX_BYTES:
        raise SystemExit("%s: larger than %d bytes, not a hand-edited config" % (path, MAX_BYTES))
    with open(path, "rb") as fh:
        raw = fh.read()
    bom = raw.startswith(b"\xef\xbb\xbf")
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError as e:
        raise SystemExit("%s: not valid UTF-8 (%s); save the file as UTF-8" % (path, e))
    return text, bom


def validate_file(path, fmt, schema, env_vars, masked, base_dir, check_paths):
    text, bom = read_text(path)
    ctx = Ctx(path, fmt, text, env_vars, masked, base_dir or os.path.dirname(os.path.abspath(path)), check_paths)
    if bom:
        ctx.add("suspicious_value", "file starts with a UTF-8 byte order mark", "save without BOM; some parsers reject it", 1, 1, None, "warning")
    if not text.strip():
        ctx.add("syntax", "file is empty", "add content or remove the file", 1, 1)
        return ctx, False
    data = PARSERS[fmt](text, ctx)
    if data is None:
        return ctx, False
    generic_checks(ctx, data, schema)
    if schema:
        check_schema(ctx, data, schema)
    return ctx, True


def resolved(p):
    return os.path.normcase(os.path.realpath(p))


def main(argv=None):
    ap = argparse.ArgumentParser(description="Validate config files (JSON, TOML, INI, .env, YAML subset).")
    ap.add_argument("files", nargs="+")
    ap.add_argument("--schema")
    ap.add_argument("--format", choices=sorted(PARSERS))
    ap.add_argument("--env-file", dest="env_file")
    ap.add_argument("--check-paths", action="store_true")
    ap.add_argument("--base-dir", dest="base_dir")
    ap.add_argument("--report")
    ap.add_argument("--force", action="store_true")
    try:
        a = ap.parse_args(argv)
    except SystemExit as e:
        return 2 if e.code else 0
    current = [None]
    try:
        inputs = list(a.files) + [p for p in (a.schema, a.env_file) if p]
        for p in inputs:
            if not os.path.isfile(p):
                raise SystemExit("not a file: %s" % p)
        if a.report:
            rp = resolved(a.report)
            if any(rp == resolved(p) for p in inputs):
                raise SystemExit("refusing to write the report over an input file: %s" % a.report)
            if os.path.exists(a.report) and not a.force:
                raise SystemExit("report exists: %s (use --force to replace a non-input file)" % a.report)
        schema = load_schema(a.schema) if a.schema else None
        env_vars = None
        if a.env_file:
            ectx = Ctx(a.env_file, "env", "", None, {}, ".", False)
            etext, _ = read_text(a.env_file)
            ectx.lines = etext.splitlines()
            env_vars = set(parse_env(etext, ectx))
        masked, files, errs, warns = {}, [], 0, 0
        for path in a.files:
            current[0] = path
            fmt = a.format or detect(path)
            if not fmt:
                raise SystemExit("%s: cannot tell the format from the extension; pass --format" % path)
            ctx, parsed = validate_file(path, fmt, schema, env_vars, masked, a.base_dir, a.check_paths)
            ctx.findings.sort(key=lambda f: (f["line"] is None, f["line"] or 0, f["class"]))
            e = sum(1 for f in ctx.findings if f["severity"] == "error")
            errs += e
            warns += len(ctx.findings) - e
            files.append({"file": path, "format": fmt, "parsed": parsed, "errors": ctx.findings})
        out = {"tool": "validate_config", "schema_used": bool(schema), "files": files,
               "masked_values": sorted(masked.values(), key=lambda m: (m["file"], m["key"] or "")),
               "summary": {"files": len(files), "errors": errs, "warnings": warns},
               "not_checked": ["whether values are correct for the running system", "whether the application accepts the keys",
                               "any key the schema does not describe (types and ranges)"]}
        text = json.dumps(out, indent=2, ensure_ascii=False)
        if a.report:
            with open(a.report, "w", encoding="utf-8") as fh:
                fh.write(text + "\n")
        print(text)
        return 1 if errs else 0
    except (ValueError, RecursionError) as e:
        # Number too long or out of range, or nesting too deep: no finding list can be trusted.
        if isinstance(e, RecursionError):
            code, msg = "nesting_too_deep", "nesting is too deep to parse"
        elif isinstance(e, InvalidNumber) or "digits" in str(e):
            code, msg = "invalid_number", str(e)
        else:
            code, msg = "invalid_input", str(e)[:200]
        print(json.dumps({"tool": "validate_config", "error": code, "file": current[0], "message": msg}, indent=2))
        print("error: %s (%s)" % (code, current[0]), file=sys.stderr)
        return 2
    except SystemExit as e:
        if isinstance(e.code, str):
            print("error: " + e.code, file=sys.stderr)
            return 2
        return e.code or 0


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
