#!/usr/bin/env python3
"""Compare a source locale file with a target locale file and print strict JSON.

Usage:
    python locale_check.py SOURCE TARGET [--glossary FILE] [--limits FILE]
                           [--no-ratio] [--min-chars N] [--strict]

SOURCE and TARGET are .json (nested objects and arrays are flattened to
dotted keys such as "nav.items[0]") or .properties (Java style: key=value,
key:value, # and ! comments, backslash continuation, \\uXXXX escapes).
The two files may differ in format; only keys and values are compared.

Reads the files given and nothing else. Writes JSON to stdout only. No network.

Glossary file (JSON):
    {"terms": {"Dashboard": "Tableau de bord", "Invoice": ["Facture", "Facturation"]},
     "do_not_translate": ["Acme Cloud", "OAuth"],
     "allow_identical": ["OK", "Email"],
     "allow_identical_keys": ["brand.name"]}
Limits file (JSON): {"key": max_characters_in_target, ...}

Exit codes: 0 no error-level issue; 1 at least one error-level issue (or any
issue with --strict); 2 usage problem, unreadable or invalid file.
"""
import argparse
import json
import re
import sys

# Length ratio ceilings by source length: (max source chars, max target/source).
# Working values from the common rule of thumb that short strings grow more
# than long ones when English is translated into German, French or Finnish.
RATIO_BANDS = [(10, 3.0), (20, 2.0), (30, 1.7), (50, 1.5), (70, 1.4)]
RATIO_LONG = 1.3  # every source longer than the last band
MIN_RATIO_SRC_LEN = 20  # below this, a very short target is normal (CJK, "OK")
TOO_SHORT_RATIO = 0.3  # target under 30% of a 20+ char source suggests truncation
DEFAULT_MIN_CHARS = 4  # identical values shorter than this are ignored ("OK", "ID")
SNIP = 120  # characters of a value echoed in an issue
PLURAL_TYPES = ("plural", "select", "selectordinal")

ERROR_TYPES = {
    "missing_key", "extra_key", "empty_target", "placeholder_mismatch",
    "icu_missing_other", "icu_branch_mismatch", "unbalanced_braces",
    "tag_mismatch", "glossary_term_missing", "do_not_translate_altered",
    "hard_limit_exceeded",
}
WARNING_TYPES = {
    "untranslated_identical", "length_ratio_exceeded", "target_too_short",
    "bidi_control_chars", "duplicate_key",
}

RE_MUSTACHE = re.compile(r"\{\{\s*[\w.\-]+\s*\}\}")
RE_DOLLAR = re.compile(r"\$\{[^}]*\}")
RE_I18NEXT = re.compile(r"\$t\([^)]+\)")
RE_PRINTF = re.compile(r"%(?:\((\w+)\))?(?:(\d+)\$)?[-+0#]*\d*(?:\.\d+)?([sdifuxXoeEgGcr])")
RE_TAG = re.compile(r"<(/?)([A-Za-z][\w-]*|\d+)\b[^>]*?(/?)>")
# Characters that are not letters: Latin, Greek/Cyrillic/Arabic/Hebrew/Indic..., kana, CJK
# are counted as letters (ranges built from code points to keep the file ASCII).
RE_NOT_LETTER = re.compile("[^A-Za-z%s-%s%s-%s%s-%s]" % tuple(chr(c) for c in (0xC0, 0x24F, 0x370, 0x1FFF, 0x3040, 0x9FFF)))
RE_BIDI = re.compile("[" + chr(0x202A) + "-" + chr(0x202E) + "]")


class Fail(Exception):
    """Raised for a file problem; the message says what to fix."""


def read_text(path):
    try:
        with open(path, "rb") as fh:
            raw = fh.read()
    except OSError as exc:
        raise Fail("cannot read %s: %s" % (path, exc.strerror or exc))
    if not raw.strip():
        raise Fail("%s is empty" % path)
    for enc in ("utf-8-sig", "latin-1"):
        try:
            return raw.decode(enc), enc
        except UnicodeDecodeError:
            continue
    raise Fail("cannot decode %s" % path)


def flatten(node, prefix, out):
    if isinstance(node, dict):
        for k, v in node.items():
            flatten(v, "%s.%s" % (prefix, k) if prefix else str(k), out)
    elif isinstance(node, list):
        for i, v in enumerate(node):
            flatten(v, "%s[%d]" % (prefix, i), out)
    elif isinstance(node, str):
        out[prefix] = node


def load_json(text, path):
    dups = []

    def hook(pairs):
        seen = set()
        for k, _ in pairs:
            if k in seen:
                dups.append(k)
            seen.add(k)
        return dict(pairs)

    try:
        data = json.loads(text, object_pairs_hook=hook)
    except ValueError as exc:
        raise Fail("%s is not valid JSON: %s" % (path, exc))
    out = {}
    flatten(data, "", out)
    return out, sorted(set(dups))


def unescape_prop(s):
    def sub(m):
        c = m.group(1)
        if c.startswith("u"):
            try:
                return chr(int(c[1:], 16))
            except ValueError:
                return m.group(0)
        return {"n": "\n", "t": "\t", "r": "\r", "f": "\f"}.get(c, c)
    return re.sub(r"\\(u[0-9a-fA-F]{4}|.)", sub, s)


def load_properties(text):
    out, dups = {}, []
    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    i = 0
    while i < len(lines):
        line = lines[i].lstrip()
        i += 1
        if not line or line[0] in "#!":
            continue
        while re.search(r"(?<!\\)(?:\\\\)*\\$", line) and i < len(lines):
            line = line[:-1] + lines[i].lstrip()
            i += 1
        m = re.match(r"((?:[^\s=:\\]|\\.)+)\s*(?:[=:]\s*|\s+)(.*)$", line, re.S)
        if m:
            key, val = m.group(1), m.group(2)
        else:
            key, val = line, ""
        key = unescape_prop(key)
        if key in out:
            dups.append(key)
        out[key] = unescape_prop(val)
    return out, sorted(set(dups))


def load_locale(path):
    text, enc = read_text(path)
    if path.lower().endswith(".properties"):
        data, dups = load_properties(text)
        fmt = "properties"
    elif path.lower().endswith(".json"):
        data, dups = load_json(text, path)
        fmt = "json"
    else:
        raise Fail("%s: extension must be .json or .properties" % path)
    return {"data": data, "dups": dups, "format": fmt, "encoding": enc}


def load_json_file(path, what):
    text, _ = read_text(path)
    try:
        obj = json.loads(text)
    except ValueError as exc:
        raise Fail("%s file %s is not valid JSON: %s" % (what, path, exc))
    if not isinstance(obj, dict):
        raise Fail("%s file %s must be a JSON object" % (what, path))
    return obj


# ---------------------------------------------------------------- placeholders

def _skip_quoted(s, i):
    """ICU apostrophe quoting: '' is a literal apostrophe; '{' starts a quote."""
    if i + 1 < len(s) and s[i + 1] == "'":
        return i + 2
    if i + 1 < len(s) and s[i + 1] in "{}":
        j = s.find("'", i + 2)
        return len(s) if j < 0 else j + 1
    return i + 1


def _match_brace(s, i):
    """Index of the } closing the { at s[i], or -1."""
    depth, j = 0, i
    while j < len(s):
        c = s[j]
        if c == "'":
            j = _skip_quoted(s, j)
            continue
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return j
        j += 1
    return -1


def _split_commas(inner, limit):
    parts, depth, cur, j = [], 0, [], 0
    while j < len(inner):
        c = inner[j]
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
        if c == "," and depth == 0 and len(parts) < limit:
            parts.append("".join(cur))
            cur = []
        else:
            cur.append(c)
        j += 1
    parts.append("".join(cur))
    return parts


def scan_icu(s, tokens, structs, problems):
    """Collect {name} tokens; record plural/select structure; note bad braces."""
    i = 0
    while i < len(s):
        c = s[i]
        if c == "'":
            i = _skip_quoted(s, i)
            continue
        if c == "}":
            problems.append("unmatched }")
            i += 1
            continue
        if c != "{":
            i += 1
            continue
        j = _match_brace(s, i)
        if j < 0:
            problems.append("unclosed {")
            return
        inner = s[i + 1:j]
        parts = _split_commas(inner, 2)
        name = parts[0].strip()
        if not name:
            problems.append("empty {}")
        elif len(parts) >= 3 and parts[1].strip() in PLURAL_TYPES:
            ptype = parts[1].strip()
            branches, k, body = {}, 0, parts[2]
            while k < len(body):
                while k < len(body) and body[k].isspace():
                    k += 1
                st = k
                while k < len(body) and not body[k].isspace() and body[k] != "{":
                    k += 1
                selector = body[st:k]
                while k < len(body) and body[k].isspace():
                    k += 1
                if k >= len(body) or body[k] != "{":
                    break
                e = _match_brace(body, k)
                if e < 0:
                    problems.append("unclosed branch")
                    break
                if not selector.startswith("offset:"):
                    branches[selector] = body[k + 1:e]
                    scan_icu(body[k + 1:e], tokens, structs, problems)
                k = e + 1
            structs.append((name, ptype, sorted(branches)))
            tokens.append("{%s,%s}" % (name, ptype))
        else:
            tokens.append("{%s}" % name)
        i = j + 1


def extract(s):
    """Return (tokens, structs, tags, problems) for one string value."""
    tokens, structs, problems = [], [], []
    work = s
    for rx in (RE_MUSTACHE, RE_DOLLAR, RE_I18NEXT):
        for m in rx.finditer(work):
            tokens.append(re.sub(r"\s+", "", m.group(0)))
        work = rx.sub(" ", work)
    work = work.replace("%%", "  ")
    printf = []
    for m in RE_PRINTF.finditer(work):
        printf.append((m.group(1), m.group(2), m.group(3)))
    work = RE_PRINTF.sub(" ", work)
    tags = []
    for m in RE_TAG.finditer(work):
        tags.append(("/" if m.group(1) else "") + m.group(2) + ("/" if m.group(3) else ""))
    work = RE_TAG.sub(" ", work)
    if "{" in work or "}" in work:
        scan_icu(work, tokens, structs, problems)
    return tokens, printf, structs, tags, problems


def printf_signature(items):
    named = sorted("%%(%s)%s" % (n, c) for n, p, c in items if n)
    rest = [(p, c) for n, p, c in items if not n]
    # Position numbers (%1$s) are dropped so a reordered translation is fine;
    # only the conversion types and their count are compared.
    return named + sorted("%" + c for _, c in rest)


def multiset_diff(a, b):
    """Items of a not matched in b (as a sorted list)."""
    left = list(b)
    out = []
    for x in a:
        if x in left:
            left.remove(x)
        else:
            out.append(x)
    return sorted(out)


# ------------------------------------------------------------------- checks

def ratio_limit(n):
    for upto, lim in RATIO_BANDS:
        if n <= upto:
            return lim
    return RATIO_LONG


def snip(s):
    return s if len(s) <= SNIP else s[:SNIP - 3] + "..."


def term_in(text, term):
    return re.search(r"(?<!\w)%s(?!\w)" % re.escape(term), text, re.I) is not None


def issue(kind, key, **extra):
    d = {"type": kind, "severity": "error" if kind in ERROR_TYPES else "warning", "key": key}
    d.update(extra)
    return d


def compare(src, tgt, gloss, limits, ratio_on, min_chars):
    issues = []
    sd, td = src["data"], tgt["data"]
    for k in sorted(set(sd) - set(td)):
        issues.append(issue("missing_key", k, source=snip(sd[k])))
    for k in sorted(set(td) - set(sd)):
        issues.append(issue("extra_key", k, target=snip(td[k])))
    for side, name in ((src, "source"), (tgt, "target")):
        for k in side["dups"]:
            issues.append(issue("duplicate_key", k, file=name))

    terms = gloss.get("terms", {}) if gloss else {}
    dnt = gloss.get("do_not_translate", []) if gloss else []
    allow_vals = {v.strip().casefold() for v in gloss.get("allow_identical", [])} if gloss else set()
    allow_keys = set(gloss.get("allow_identical_keys", [])) if gloss else set()

    for k in sorted(set(sd) & set(td)):
        s, t = sd[k], td[k]
        if s.strip() and not t.strip():
            issues.append(issue("empty_target", k, source=snip(s)))
            continue
        st, sp, ss, stags, sprob = extract(s)
        tt, tp, ts, ttags, tprob = extract(t)

        for p in tprob:
            issues.append(issue("unbalanced_braces", k, detail=p, target=snip(t)))
        if not tprob:
            miss = multiset_diff(st, tt) + [x for x in multiset_diff(printf_signature(sp), printf_signature(tp))]
            extra = multiset_diff(tt, st) + [x for x in multiset_diff(printf_signature(tp), printf_signature(sp))]
            if miss or extra:
                issues.append(issue("placeholder_mismatch", k, missing_in_target=miss,
                                    added_in_target=extra, source=snip(s), target=snip(t)))
            sdict = {(n, ty): b for n, ty, b in ss}
            for n, ty, b in ts:
                if "other" not in b:
                    issues.append(issue("icu_missing_other", k, argument=n, target=snip(t)))
            for (n, ty), b in sdict.items():
                if ty in ("select",):
                    tb = next((bb for nn, tty, bb in ts if nn == n and tty == ty), None)
                    if tb is not None and sorted(tb) != sorted(b):
                        issues.append(issue("icu_branch_mismatch", k, argument=n,
                                            source_branches=b, target_branches=tb))
        tag_miss = multiset_diff(stags, ttags)
        tag_extra = multiset_diff(ttags, stags)
        if tag_miss or tag_extra:
            issues.append(issue("tag_mismatch", k, missing_in_target=tag_miss,
                                added_in_target=tag_extra, source=snip(s), target=snip(t)))

        # Untranslated: identical, has letters, long enough, not allowed.
        letters = re.sub(RE_NOT_LETTER, "", re.sub(
            r"\{[^}]*\}|%\w|<[^>]*>", "", s))
        if (s.strip() == t.strip() and len(letters) >= min_chars and k not in allow_keys
                and s.strip().casefold() not in allow_vals
                and not any(s.strip() == d for d in dnt)):
            issues.append(issue("untranslated_identical", k, source=snip(s)))

        # Length: hard limit first, then ratio.
        if k in limits and len(t) > limits[k]:
            issues.append(issue("hard_limit_exceeded", k, limit=limits[k], length=len(t), target=snip(t)))
        if ratio_on and s.strip() and s != t:
            r = len(t) / len(s)
            lim = ratio_limit(len(s))
            if r > lim:
                issues.append(issue("length_ratio_exceeded", k, ratio=round(r, 2), limit=lim,
                                    source_chars=len(s), target_chars=len(t)))
            elif len(s) >= MIN_RATIO_SRC_LEN and r < TOO_SHORT_RATIO:
                issues.append(issue("target_too_short", k, ratio=round(r, 2),
                                    source_chars=len(s), target_chars=len(t)))

        if RE_BIDI.search(t) and not RE_BIDI.search(s):
            issues.append(issue("bidi_control_chars", k, target=snip(t)))

        # Glossary and do-not-translate (checked against the source text).
        for term, want in terms.items():
            if term_in(s, term):
                opts = want if isinstance(want, list) else [want]
                if not any(o.casefold() in t.casefold() for o in opts):
                    issues.append(issue("glossary_term_missing", k, term=term, expected=opts, target=snip(t)))
        for term in dnt:
            if term in s and term not in t:
                issues.append(issue("do_not_translate_altered", k, term=term, target=snip(t)))
    return issues


def build_report(args):
    src = load_locale(args.source)
    tgt = load_locale(args.target)
    gloss = load_json_file(args.glossary, "glossary") if args.glossary else None
    limits = load_json_file(args.limits, "limits") if args.limits else {}
    for k, v in limits.items():
        if not isinstance(v, int) or isinstance(v, bool) or v < 1:
            raise Fail("limits file: %r must map to a positive integer" % k)
    if gloss is not None:
        terms = gloss.get("terms", {})
        if not isinstance(terms, dict) or not all(
                isinstance(v, str) or (isinstance(v, list) and v and all(isinstance(x, str) for x in v))
                for v in terms.values()):
            raise Fail("glossary 'terms' must map a source term to a string or a non-empty list of strings")
        for field in ("do_not_translate", "allow_identical", "allow_identical_keys"):
            if not isinstance(gloss.get(field, []), list):
                raise Fail("glossary '%s' must be a list" % field)
    issues = compare(src, tgt, gloss, limits, not args.no_ratio, args.min_chars)
    counts = {}
    for it in issues:
        counts[it["type"]] = counts.get(it["type"], 0) + 1
    errors = sum(1 for i in issues if i["severity"] == "error")
    warnings = len(issues) - errors
    ok = errors == 0 and (not args.strict or warnings == 0)
    return {
        "tool": "locale_check",
        "version": 1,
        "source": {"path": args.source, "format": src["format"], "encoding": src["encoding"], "keys": len(src["data"])},
        "target": {"path": args.target, "format": tgt["format"], "encoding": tgt["encoding"], "keys": len(tgt["data"])},
        "options": {"glossary": bool(gloss), "limits": len(limits), "ratio_check": not args.no_ratio,
                    "min_chars": args.min_chars, "strict": args.strict},
        "ok": ok,
        "errors": errors,
        "warnings": warnings,
        "counts_by_type": dict(sorted(counts.items())),
        "issues": issues,
    }


def main(argv=None):
    ap = argparse.ArgumentParser(description="Compare a source and a target locale file.")
    ap.add_argument("source")
    ap.add_argument("target")
    ap.add_argument("--glossary")
    ap.add_argument("--limits")
    ap.add_argument("--no-ratio", action="store_true", help="skip the length ratio check")
    ap.add_argument("--min-chars", type=int, default=DEFAULT_MIN_CHARS)
    ap.add_argument("--strict", action="store_true", help="warnings also fail")
    try:
        args = ap.parse_args(argv)
    except SystemExit as exc:
        return 2 if exc.code else 0
    try:
        report = build_report(args)
    except Fail as exc:
        sys.stderr.write("error: %s\n" % exc)
        return 2
    sys.stdout.write(json.dumps(report, ensure_ascii=True, indent=2, allow_nan=False) + "\n")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
