#!/usr/bin/env python3
"""Turn a resource file into a pseudo-locale sibling and report what it found.

Usage:
    python pseudo_localize.py SOURCE [--format auto|json|properties|po]
        [--level 1|2|3|4] [--expansion 0.30|tiered] [--no-short-boost]
        [--limits LIMITS.json] [--scan-dir DIR]
        [--output PATH] [--report PATH] [--force] [--dry-run]

Reads:  SOURCE (JSON key-value, .properties or gettext .po), optionally a limits
        file (JSON object key -> max characters) and a source directory to scan
        for hard-coded UI text.
Writes: the pseudo-locale file (default: SOURCE with ".pseudo" before the
        extension) and, if --report is given, the JSON report. Nothing else.
        The script refuses any output or report path that resolves to an input
        (source, limits file, or anything under --scan-dir), even with --force.
        Without --force an existing output file is not replaced.
        --dry-run writes nothing and only prints the report.
Stdout: one strict JSON report (ASCII-escaped). Errors go to stderr.
Exit:   0 finished and every placeholder survived the round trip
        1 finished but a placeholder mismatch or round-trip failure was found
        2 usage or input error (nothing written)

It does not translate. Standard library only; no network.
"""
import argparse
import json
import math
import os
import re
import sys

PSEUDO_TAG = "en-XA"  # tag written into a .po header; any private pseudo tag works

# Plain accent transform: one visually similar accented letter per ASCII letter.
# Chosen so English text stays readable to a tester while no character is ASCII.
ACCENT_LOWER = "\u00e1\u0180\u00e7\u00f0\u00e9\u0192\u011f\u0125\u00ed\u0135\u0137\u013c\u0271\u00f1\u00f6\u00fe\u02e0\u0155\u0161\u0163\u00fc\u1e7d\u0175\u1e8b\u00fd\u017e"
ACCENT_UPPER = "\u00c1\u0181\u00c7\u00d0\u00c9\u0191\u011e\u0124\u00cd\u0134\u0136\u013b\u1e40\u00d1\u00d6\u00de\u01ea\u0154\u0160\u0162\u00dc\u1e7c\u0174\u1e8a\u00dd\u017d"
assert len(ACCENT_LOWER) == 26 and len(ACCENT_UPPER) == 26
ACCENT_TABLE = str.maketrans(
    "abcdefghijklmnopqrstuvwxyz" + "ABCDEFGHIJKLMNOPQRSTUVWXYZ", ACCENT_LOWER + ACCENT_UPPER)

EXPANSION_DEFAULT = 0.30  # typical growth of English into most European languages
EXPANSION_SHORT = 0.50    # short strings grow proportionally more
SHORT_LEN = 10            # strings of this many characters or fewer count as short
# Approximate tiers (upper length bound, growth) for --expansion tiered; midpoints of the
# commonly cited ranges, so treat them as a rough planning aid, not a measurement.
EXPANSION_TIERS = [(10, 1.5), (20, 0.9), (30, 0.7), (50, 0.5), (70, 0.35)]
PAD_CHAR = "~"            # visible padding that cannot be mistaken for text
RLE, PDF = "\u202b", "\u202c"  # right-to-left embedding start / pop directional formatting
MAX_SCAN_FILES = 5000
MAX_SCAN_BYTES = 1000000
MAX_HARDCODED = 500
SCAN_EXT = {".html", ".htm", ".jsx", ".tsx", ".vue", ".svelte"}
SKIP_DIRS = {"node_modules", ".git", "dist", "build", "__pycache__", ".next", "vendor"}

RE_ICU_HEAD = re.compile(r"\s*[\w.\-]+\s*,\s*(?:plural|selectordinal|select)\s*,")
RE_ICU_SELECTOR = re.compile(r"(?:\s*offset:\d+)?\s*[^\s{}]+\s*")
RE_OTHER = re.compile(
    r"</?[A-Za-z][^<>]*>|<!--.*?-->"
    r"|&(?:#\d+|#[xX][0-9a-fA-F]+|[A-Za-z][A-Za-z0-9]{1,31});"
    r"|%\([^)]+\)[-+#0 ]*\d*(?:\.\d+)?[sdifuxXoeEgGcr]"
    r"|%%"
    r"|%(?:\d+\$)?[-+#0]*(?:\d+|\*)?(?:\.(?:\d+|\*))?(?:hh|h|ll|l|L|z|j|t)?[sdifuxXoeEgGcpb@]",
    re.S)
RE_UNNAMED_PRINTF = re.compile(r"^%(?!%)(?!\d+\$)(?!\()")
FRAG_KEY_WORDS = {"prefix", "suffix", "postfix", "before", "after", "pre", "part", "joiner",
                  "connector", "fragment"}
RE_END_FUNCTION_WORD = re.compile(r"(?i)\b(?:of|the|a|an|and|or|with|from)\s*$")
RE_PLURAL_HACK = re.compile(r"[A-Za-z]\((?:s|es)\)")
MONTHS = (r"(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|"
          r"Aug(?:ust)?|Sep(?:t(?:ember)?)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)")
BAKED = [
    ("date", re.compile(r"\b\d{1,4}[/.\-]\d{1,2}[/.\-]\d{1,4}\b|\b" + MONTHS + r"\.?\s+\d{1,2}\b")),
    ("time", re.compile(r"\b\d{1,2}:\d{2}\b")),
    ("currency", re.compile("[$\u20ac\u00a3\u00a5\u20aa]\\s?\\d|\\d\\s?[$\u20ac\u00a3\u00a5\u20aa]")),
    ("number", re.compile(r"\b\d+(?:[.,]\d+)*\b")),
]


class Fail(Exception):
    """Input or usage problem: message goes to stderr, exit 2."""


# ---------------------------------------------------------------- tokenizer

def match_brace(s, i):
    """Index of the } closing the { at s[i], or -1."""
    depth = 0
    for j in range(i, len(s)):
        if s[j] == "{":
            depth += 1
        elif s[j] == "}":
            depth -= 1
            if depth == 0:
                return j
    return -1


def parse_branches(rest, warn):
    toks, i, n = [], 0, len(rest)
    while i < n:
        if rest[i:].strip() == "":
            toks.append(("prot", rest[i:]))
            break
        m = RE_ICU_SELECTOR.match(rest, i)
        if not m or m.end() >= n or rest[m.end()] != "{":
            toks.append(("prot", rest[i:]))
            warn.append("malformed ICU branches kept untouched: " + rest[i:i + 40])
            break
        k = match_brace(rest, m.end())
        if k < 0:
            toks.append(("prot", rest[i:]))
            warn.append("unbalanced ICU branch kept untouched: " + rest[i:i + 40])
            break
        toks.append(("prot", m.group() + "{"))
        toks.extend(tokenize(rest[m.end() + 1:k], warn, True))
        toks.append(("prot", "}"))
        i = k + 1
    return toks


def tokenize(s, warn, in_plural=False):
    """Split a string into ('lit', text) runs that may be altered and ('prot', text) tokens
    that must come out byte-identical. ICU plural/select branches keep their keywords and
    selectors protected and expose only the branch text as literal."""
    toks, buf, i, n = [], [], 0, len(s)

    def flush():
        if buf:
            toks.append(("lit", "".join(buf)))
            buf.clear()

    while i < n:
        c = s[i]
        brace = -1
        if c == "$" and i + 1 < n and s[i + 1] == "{":
            brace = i + 1
        elif c == "{":
            brace = i
        if brace >= 0:
            j = match_brace(s, brace)
            if j < 0:
                warn.append("unbalanced { treated as text: " + s[i:i + 30])
                buf.append(c)
                i += 1
                continue
            flush()
            inner = s[brace + 1:j]
            m = RE_ICU_HEAD.match(inner) if c == "{" else None
            if m:
                toks.append(("prot", "{" + inner[:m.end()]))
                toks.extend(parse_branches(inner[m.end():], warn))
                toks.append(("prot", "}"))
            else:
                toks.append(("prot", s[i:j + 1]))
            i = j + 1
            continue
        if in_plural and c == "#":
            flush()
            toks.append(("prot", "#"))
            i += 1
            continue
        m = RE_OTHER.match(s, i)
        if m:
            flush()
            toks.append(("prot", m.group()))
            i = m.end()
            continue
        buf.append(c)
        i += 1
    flush()
    return toks


def placeholders(s):
    return [t for k, t in tokenize(s, []) if k == "prot"]


def has_letters(toks):
    return any(k == "lit" and any(ch.isalpha() for ch in t) for k, t in toks)


# ---------------------------------------------------------------- transform

def growth_for(n, mode, short_boost):
    if mode == "tiered":
        for bound, ratio in EXPANSION_TIERS:
            if n <= bound:
                return ratio
        return EXPANSION_DEFAULT
    ratio = float(mode)
    if short_boost and n <= SHORT_LEN:
        ratio = max(ratio, EXPANSION_SHORT)
    return ratio


def pseudo(s, level, mode, short_boost):
    """Return (pseudo string, transformed?). Strings with no letters come back unchanged."""
    toks = tokenize(s, [])
    if not has_letters(toks):
        return s, False
    out = "".join(t if k == "prot" else t.translate(ACCENT_TABLE) for k, t in toks)
    brackets = level >= 2
    if level >= 3:
        added = int(math.floor(len(s) * growth_for(len(s), mode, short_boost) + 0.5))
        out += PAD_CHAR * max(0, added - (2 if brackets else 0))
    if brackets:
        out = "[" + out + "]"
    if level >= 4:
        out = RLE + out + PDF
    return out, True


def visible_len(s):
    return len(s.replace(RLE, "").replace(PDF, ""))


# ---------------------------------------------------------------- formats

def detect_format(path, requested):
    if requested != "auto":
        return requested
    ext = os.path.splitext(path)[1].lower()
    return {".json": "json", ".properties": "properties", ".po": "po", ".pot": "po"}.get(ext) or _bad_ext(ext)


def _bad_ext(ext):
    raise Fail("cannot tell the format from extension '%s'; pass --format json|properties|po" % ext)


def read_text(path, warnings):
    data = open(path, "rb").read()
    if not data.strip():
        raise Fail("source file is empty: " + path)
    try:
        return data.decode("utf-8-sig")
    except UnicodeDecodeError:
        warnings.append("source is not UTF-8; read as ISO-8859-1 (legacy .properties encoding)")
        return data.decode("latin-1")


# --- JSON

def json_walk(node, path, fn):
    if isinstance(node, dict):
        return {k: json_walk(v, path + [str(k)], fn) for k, v in node.items()}
    if isinstance(node, list):
        return [json_walk(v, path + [str(i)], fn) for i, v in enumerate(node)]
    if isinstance(node, str):
        return fn(".".join(path), node)
    return node


def json_strings(data):
    found = []
    json_walk(data, [], lambda k, v: found.append((k, v)) or v)
    return found


# --- .properties

def prop_unescape(v):
    def rep(m):
        if m.group(1):
            return chr(int(m.group(1), 16))
        return {"n": "\n", "t": "\t", "r": "\r", "f": "\f"}.get(m.group(2), m.group(2))
    s = re.sub(r"\\u([0-9a-fA-F]{4})|\\(.)", rep, v, flags=re.S)
    try:
        return s.encode("utf-16", "surrogatepass").decode("utf-16")
    except UnicodeError:
        return s


def prop_escape(v):
    out = []
    for ch in v:
        o = ord(ch)
        if ch == "\\":
            out.append("\\\\")
        elif ch == "\n":
            out.append("\\n")
        elif ch == "\r":
            out.append("\\r")
        elif ch == "\t":
            out.append("\\t")
        elif ch == "\f":
            out.append("\\f")
        elif o > 126 or o < 32:
            if o > 0xFFFF:
                o -= 0x10000
                out.append("\\u%04x\\u%04x" % (0xD800 + (o >> 10), 0xDC00 + (o & 0x3FF)))
            else:
                out.append("\\u%04x" % o)
        else:
            out.append(ch)
    s = "".join(out)
    return "\\ " + s[1:] if s.startswith(" ") else s


def parse_properties(text):
    lines = text.splitlines()
    items, i = [], 0
    while i < len(lines):
        raw = lines[i]
        logical = raw.lstrip()
        if logical == "" or logical[0] in "#!":
            items.append(("raw", raw))
            i += 1
            continue
        while (len(logical) - len(logical.rstrip("\\"))) % 2 == 1 and i + 1 < len(lines):
            logical = logical[:-1] + lines[i + 1].lstrip()
            i += 1
        i += 1
        j = 0
        while j < len(logical) and logical[j] not in "=: \t\f":
            j += 2 if logical[j] == "\\" else 1
        key_raw = logical[:j]
        m = re.match(r"[ \t\f]*[=:]?[ \t\f]*", logical[j:])
        sep = m.group() or "="
        items.append(("kv", key_raw, sep, prop_unescape(logical[j + m.end():])))
    return items


# --- gettext .po

def po_unescape(v):
    return re.sub(r"\\(.)", lambda m: {"n": "\n", "t": "\t", "r": "\r", '"': '"', "\\": "\\"}.get(
        m.group(1), "\\" + m.group(1)), v)


def po_escape(v):
    return (v.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")
            .replace("\t", "\\t").replace("\r", "\\r"))


def parse_po(text):
    entries, cur, last = [], None, None

    def new():
        return {"comments": [], "ctxt": None, "id": None, "plural": None, "strs": {}}

    def finish():
        nonlocal cur
        if cur is not None and cur["id"] is not None:
            entries.append(cur)
        cur = None

    for no, line in enumerate(text.splitlines(), 1):
        line = line.rstrip()
        if line.strip() == "":
            finish()
            continue
        if cur is None:
            cur = new()
        if line.startswith("#"):
            if cur["strs"]:
                finish()
                cur = new()
            cur["comments"].append(line)
            continue
        m = re.match(r'(msgctxt|msgid_plural|msgid|msgstr(?:\[(\d+)\])?)\s+"(.*)"$', line)
        if m:
            word, idx, val = m.group(1), m.group(2), po_unescape(m.group(3))
            if word == "msgctxt" or (word == "msgid" and cur["id"] is not None and cur["strs"]):
                if cur["id"] is not None:
                    finish()
                    cur = new()
            if word == "msgctxt":
                cur["ctxt"], last = val, ("ctxt", None)
            elif word == "msgid":
                cur["id"], last = val, ("id", None)
            elif word == "msgid_plural":
                cur["plural"], last = val, ("plural", None)
            else:
                n = int(idx) if idx is not None else 0
                cur["strs"][n], last = val, ("str", n)
            continue
        m = re.match(r'"(.*)"$', line.strip())
        if m and last:
            val = po_unescape(m.group(1))
            if last[0] == "str":
                cur["strs"][last[1]] += val
            else:
                key = {"ctxt": "ctxt", "id": "id", "plural": "plural"}[last[0]]
                cur[key] += val
            continue
        raise Fail("line %d is not valid .po syntax: %s" % (no, line[:60]))
    finish()
    return entries


def po_key(e):
    return (e["ctxt"] + "|" if e["ctxt"] is not None else "") + e["id"]


def po_nplurals(entries):
    for e in entries:
        if e["id"] == "" and e["ctxt"] is None:
            m = re.search(r"nplurals\s*=\s*(\d+)", e["strs"].get(0, ""))
            if m:
                return max(1, int(m.group(1)))
    return 2


def po_header_text(entries):
    for e in entries:
        if e["id"] == "" and e["ctxt"] is None:
            return e["strs"].get(0, "")
    return None


def po_pseudo_header(h):
    if h is None:
        return ("Content-Type: text/plain; charset=UTF-8\nLanguage: %s\n"
                "Plural-Forms: nplurals=2; plural=(n != 1);\n" % PSEUDO_TAG)
    if re.search(r"charset=", h):
        h = re.sub(r"charset=[^\s;\\]+", "charset=UTF-8", h)
    else:
        h = (h if h == "" or h.endswith("\n") else h + "\n") + "Content-Type: text/plain; charset=UTF-8\n"
    if re.search(r"(?m)^Language:.*$", h):
        return re.sub(r"(?m)^Language:.*$", "Language: " + PSEUDO_TAG, h)
    return (h if h == "" or h.endswith("\n") else h + "\n") + "Language: %s\n" % PSEUDO_TAG


def po_source_strings(entries):
    out = []
    for e in entries:
        if e["id"] == "" and e["ctxt"] is None:
            continue
        out.append((po_key(e), e["id"]))
        if e["plural"] is not None:
            out.append((po_key(e) + " [plural]", e["plural"]))
    return out


# ---------------------------------------------------------------- analysis

def analyze(key, text, leaf, use_key_names, found):
    tok_warn = []
    toks = tokenize(text, tok_warn)
    found["warnings"].extend("%s: %s" % (key, w) for w in tok_warn)
    lit = " ".join(t for k, t in toks if k == "lit")
    prots = [t for k, t in toks if k == "prot"]
    if not has_letters(toks):
        found["no_letters"].append(key)
        return

    def frag(reason, conf):
        found["fragments"].append({"key": key, "reason": reason, "confidence": conf, "value": text})

    if use_key_names and leaf:
        words = re.split(r"[._\-\s]+|(?<=[a-z0-9])(?=[A-Z])", leaf)
        hit = [w for w in (re.sub(r"\d+$", "", w.lower()) for w in words) if w in FRAG_KEY_WORDS]
        if hit:
            frag("key name suggests a sentence piece: " + hit[0], "medium")
    if text != text.strip():
        frag("leading or trailing space: joined to neighbouring strings in code", "high")
    stripped = text.strip()
    if stripped.endswith(",") or RE_END_FUNCTION_WORD.search(stripped):
        frag("ends mid-sentence (comma or function word)", "medium")
    words = stripped.split()
    if (len(words) >= 2 and stripped[:1].islower() and stripped[-1:] not in ".!?:\u2026"):
        frag("starts lowercase, several words, no final punctuation", "low")
    if RE_PLURAL_HACK.search(text):
        frag("plural written as word(s): needs a real plural form", "medium")
    if prots and not re.sub(r"[\W_\d]+", "", lit):
        frag("only placeholders and punctuation: sentence assembled elsewhere", "low")
    tags = [t for t in prots if t.startswith("<") and not t.startswith("<!--")]
    if tags:
        found["html_inside"].append({"key": key, "tags": tags})
    unnamed = [t for t in prots if RE_UNNAMED_PRINTF.match(t) or t == "{}"]
    if len(unnamed) >= 2:
        found["repeated_unnamed"].append({"key": key, "count": len(unnamed), "tokens": unnamed})
    for kind, rx in BAKED:  # first kind that matches wins: date, time, currency, number
        ms = [m.group(0) for m in rx.finditer(lit)]
        if ms:
            found["baked_values"].append({"key": key, "kind": kind, "matches": ms[:5]})
            break


def scan_hardcoded(root, value_to_key, warnings):
    results, files = [], 0
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(d for d in dirnames if d not in SKIP_DIRS)
        for name in sorted(filenames):
            if os.path.splitext(name)[1].lower() not in SCAN_EXT:
                continue
            path = os.path.join(dirpath, name)
            try:
                if os.path.getsize(path) > MAX_SCAN_BYTES:
                    warnings.append("scan skipped large file: " + path)
                    continue
                body = open(path, "rb").read().decode("utf-8", errors="replace")
            except OSError:
                continue
            files += 1
            if files > MAX_SCAN_FILES:
                warnings.append("scan stopped after %d files" % MAX_SCAN_FILES)
                return results
            if os.path.splitext(name)[1].lower() in (".html", ".htm", ".vue", ".svelte"):
                body = re.sub(r"(?is)<(script|style)\b.*?</\1>",
                              lambda m: "\n" * m.group(0).count("\n"), body)
            rel = os.path.relpath(path, root).replace(os.sep, "/")
            for no, line in enumerate(body.splitlines(), 1):
                cands = [("text", m.group(1)) for m in re.finditer(r">\s*([^<>{}]+?)\s*<", line)]
                cands += [("attribute:" + m.group(1).lower(), m.group(2)) for m in re.finditer(
                    r"""\b(placeholder|title|alt|aria-label|label)\s*=\s*["']([^"'{}<>]+)["']""",
                    line, re.I)]
                for kind, txt in cands:
                    txt = re.sub(r"&nbsp;|&amp;", " ", txt).strip()
                    if not re.search(r"[A-Za-z]{3,}", txt) or re.search(r"=>|;|&&|\|\||://", txt):
                        continue
                    if len(txt.split()) < 2 and not txt[:1].isupper():
                        continue
                    results.append({"file": rel, "line": no, "kind": kind, "text": txt,
                                    "matches_key": value_to_key.get(" ".join(txt.split()))})
                    if len(results) >= MAX_HARDCODED:
                        warnings.append("hard-coded list truncated at %d" % MAX_HARDCODED)
                        return results
    return results


# ---------------------------------------------------------------- paths

def norm(p):
    return os.path.normcase(os.path.realpath(p))


def is_input(path, inputs, scan_dir):
    p = norm(path)
    if p in [norm(i) for i in inputs]:
        return True
    try:
        if any(os.path.exists(i) and os.path.exists(path) and os.path.samefile(i, path) for i in inputs):
            return True
    except OSError:
        pass
    if scan_dir:
        base = norm(scan_dir)
        if p == base or p.startswith(base + os.sep):
            return True
    return False


# ---------------------------------------------------------------- main

def build_parser():
    ap = argparse.ArgumentParser(description="Create a pseudo-locale file and report problems.")
    ap.add_argument("source")
    ap.add_argument("--format", default="auto", choices=["auto", "json", "properties", "po"])
    ap.add_argument("--level", type=int, default=3, choices=[1, 2, 3, 4],
                    help="1 accents, 2 +brackets, 3 +expansion (default), 4 +right-to-left wrap")
    ap.add_argument("--expansion", default=str(EXPANSION_DEFAULT),
                    help="growth fraction (default 0.30) or 'tiered'")
    ap.add_argument("--no-short-boost", action="store_true")
    ap.add_argument("--limits")
    ap.add_argument("--scan-dir")
    ap.add_argument("--output")
    ap.add_argument("--report")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    return ap


def run(args):
    warnings = []
    src = args.source
    if not os.path.isfile(src):
        raise Fail("source file not found: " + src)
    if args.expansion != "tiered":
        try:
            if not 0 <= float(args.expansion) <= 5:
                raise ValueError
        except ValueError:
            raise Fail("--expansion must be a number from 0 to 5, or 'tiered'")
    fmt = detect_format(src, args.format)
    text = read_text(src, warnings)

    limits = {}
    if args.limits:
        try:
            limits = json.load(open(args.limits, encoding="utf-8-sig"))
            if not isinstance(limits, dict) or not all(isinstance(v, int) and v > 0 for v in limits.values()):
                raise ValueError
        except (OSError, ValueError):
            raise Fail("--limits must be a JSON object mapping keys to positive integers: " + args.limits)
    if args.scan_dir and not os.path.isdir(args.scan_dir):
        raise Fail("--scan-dir is not a directory: " + args.scan_dir)

    root, ext = os.path.splitext(src)
    output = args.output or (root + ".pseudo" + ext)
    inputs = [src] + ([args.limits] if args.limits else [])
    for label, p in (("output", output), ("report", args.report)):
        if p and is_input(p, inputs, args.scan_dir):
            raise Fail("refusing: %s path resolves to an input (%s)" % (label, p))
    if args.report and norm(args.report) == norm(output):
        raise Fail("refusing: report path equals output path")
    if not args.dry_run:
        for p in (output, args.report):
            if p and os.path.isdir(p):
                raise Fail("path is a directory: " + p)
        for p in (output, args.report):
            if p and os.path.exists(p) and not args.force:
                raise Fail("file exists (use --force to replace it): " + p)

    def fn(s):
        return pseudo(s, args.level, args.expansion, not args.no_short_boost)

    counts = {"total": 0, "transformed": 0}
    pairs = []  # (key, source string, pseudo string)

    def conv(key, s):
        out, changed = fn(s)
        counts["total"] += 1
        counts["transformed"] += int(changed)
        pairs.append((key, s, out))
        return out

    mismatches, rt_ok, rt_detail = [], True, "ok"

    def compare(key, s, o):
        a, b = placeholders(s), placeholders(o)
        if a != b:
            mismatches.append({"key": key, "source": a, "output": b})
        return len(a)

    ph_total = 0
    if fmt == "json":
        try:
            data = json.loads(text)
        except ValueError as exc:
            raise Fail("source is not valid JSON: %s" % exc)
        if not isinstance(data, (dict, list)):
            raise Fail("JSON source must be an object or an array")
        src_strings = json_strings(data)
        new = json_walk(data, [], conv)
        out_text = json.dumps(new, ensure_ascii=False, indent=2) + "\n"
        try:
            back = json.loads(out_text)
            strip = lambda d: json_walk(d, [], lambda k, v: None)
            if strip(back) != strip(data):
                rt_ok, rt_detail = False, "key structure changed"
            out_strings = json_strings(back)
            if [k for k, _ in out_strings] != [k for k, _ in src_strings]:
                rt_ok, rt_detail = False, "string keys differ after round trip"
            else:
                for (k, s), (_, o) in zip(src_strings, out_strings):
                    ph_total += compare(k, s, o)
        except ValueError as exc:
            rt_ok, rt_detail = False, "output is not valid JSON: %s" % exc
        use_key_names = True
    elif fmt == "properties":
        items = parse_properties(text)
        src_strings = [(prop_unescape(i[1]), i[3]) for i in items if i[0] == "kv"]
        lines = []
        for it in items:
            if it[0] == "raw":
                lines.append(it[1])
            else:
                lines.append(it[1] + it[2] + prop_escape(conv(prop_unescape(it[1]), it[3])))
        out_text = "\n".join(lines) + "\n"
        back = [(prop_unescape(i[1]), i[3]) for i in parse_properties(out_text) if i[0] == "kv"]
        if [k for k, _ in back] != [k for k, _ in src_strings]:
            rt_ok, rt_detail = False, "keys differ after round trip"
        else:
            for (k, s), (_, o) in zip(src_strings, back):
                ph_total += compare(k, s, o)
        use_key_names = True
    else:
        entries = parse_po(text)
        src_strings = po_source_strings(entries)
        nplural = po_nplurals(entries)
        header = po_header_text(entries)
        chunks = ['msgid ""', 'msgstr "%s"' % po_escape(po_pseudo_header(header))]
        out_lines = list(chunks)
        out_lines.append("")
        for e in entries:
            if e["id"] == "" and e["ctxt"] is None:
                continue
            out_lines.extend(e["comments"])
            if e["ctxt"] is not None:
                out_lines.append('msgctxt "%s"' % po_escape(e["ctxt"]))
            out_lines.append('msgid "%s"' % po_escape(e["id"]))
            key = po_key(e)
            if e["plural"] is not None:
                out_lines.append('msgid_plural "%s"' % po_escape(e["plural"]))
                for n in range(nplural):
                    if n == 0:
                        val = conv(key, e["id"])
                    else:
                        val = conv(key + " [plural]", e["plural"]) if n == 1 else fn(e["plural"])[0]
                    out_lines.append('msgstr[%d] "%s"' % (n, po_escape(val)))
            else:
                out_lines.append('msgstr "%s"' % po_escape(conv(key, e["id"])))
            out_lines.append("")
        out_text = "\n".join(out_lines)
        back = parse_po(out_text)
        body = [e for e in entries if not (e["id"] == "" and e["ctxt"] is None)]
        back_body = [e for e in back if not (e["id"] == "" and e["ctxt"] is None)]
        if [(e["ctxt"], e["id"], e["plural"]) for e in body] != [(e["ctxt"], e["id"], e["plural"]) for e in back_body]:
            rt_ok, rt_detail = False, "entries differ after round trip"
        else:
            for e, b in zip(body, back_body):
                for n, o in sorted(b["strs"].items()):
                    s = e["id"] if (n == 0 or e["plural"] is None) else e["plural"]
                    k = po_key(e) + ("" if n == 0 or e["plural"] is None else " [plural]")
                    ph_total += compare(k, s, o)
        use_key_names = False

    found = {"no_letters": [], "fragments": [], "html_inside": [], "repeated_unnamed": [], "baked_values": [],
             "warnings": []}
    seen_keys = set()
    for key, s in src_strings:
        if key in seen_keys:
            warnings.append("duplicate key: " + key)
        seen_keys.add(key)
        analyze(key, s, re.split(r"[.|]", key)[-1], use_key_names, found)

    warnings.extend(found["warnings"])
    overflow = []
    pair_map = {k: (s, o) for k, s, o in pairs}
    for key, limit in sorted(limits.items()):
        if key not in pair_map:
            warnings.append("limit key not found in source: " + key)
            continue
        s, o = pair_map[key]
        sl, ol = visible_len(s), visible_len(o)
        if sl > limit:
            cls = "source_over_limit"
        elif ol > limit:
            cls = "pseudo_exceeds_limit"
        else:
            continue
        overflow.append({"key": key, "limit": limit, "source_len": sl, "pseudo_len": ol, "class": cls,
                         "headroom_pct": int(math.floor((limit / sl - 1) * 100)) if sl else None})

    hard = None
    if args.scan_dir:
        v2k = {}
        for k, s in src_strings:
            v2k.setdefault(" ".join(s.split()), k)
        hard = scan_hardcoded(args.scan_dir, v2k, warnings)

    written = False
    if not args.dry_run:
        mode = "w" if args.force else "x"
        with open(output, mode, encoding="utf-8", newline="\n") as fh:
            fh.write(out_text)
        written = True

    report = {
        "tool": "pseudo_localize", "source_file": src, "format": fmt, "level": args.level,
        "expansion": args.expansion, "strings_total": counts["total"], "transformed": counts["transformed"],
        "placeholders_checked": ph_total, "placeholder_mismatches": mismatches,
        "round_trip_ok": rt_ok, "round_trip_detail": rt_detail, "overflow_risk": overflow,
        "fragments": found["fragments"], "html_inside": found["html_inside"],
        "repeated_unnamed": found["repeated_unnamed"], "baked_values": found["baked_values"],
        "no_letters": found["no_letters"], "hardcoded_candidates": hard, "warnings": warnings,
        "output_file": None if args.dry_run else output, "written": written,
        "ok": rt_ok and not mismatches,
    }
    if args.report and not args.dry_run:
        mode = "w" if args.force else "x"
        try:
            with open(args.report, mode, encoding="utf-8", newline="\n") as fh:
                fh.write(json.dumps(report, indent=2, ensure_ascii=True) + "\n")
        except FileExistsError:
            raise Fail("report exists (use --force to replace it): " + args.report)
    return report


def main(argv=None):
    args = build_parser().parse_args(argv)
    try:
        report = run(args)
    except Fail as exc:
        sys.stderr.write("error: %s\n" % exc)
        return 2
    sys.stdout.write(json.dumps(report, indent=2, ensure_ascii=True) + "\n")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
