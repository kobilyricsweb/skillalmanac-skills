#!/usr/bin/env python3
"""Check a Markdown manuscript against a BibTeX or CSL-JSON source file.

Usage:
    python manuscript_check.py MANUSCRIPT.md SOURCES.bib|SOURCES.json [options]

Options:
    --window-after N     sentences after a numeric sentence that may carry its
                         citation (default 1)
    --window-before N    sentences before it that may carry the citation (default 0)
    --skip-sections RE   case-insensitive regex; headings matching it (and
                         everything under them) are not scanned for uncited
                         numbers (default: own-data sections such as methods and
                         results, plus references)
    --all-sections       scan every section for uncited numbers

Reads the two files you name. Writes nothing. No network. Prints ONE JSON
object to stdout (UTF-8), also on errors.

Exit codes: 0 no findings, 1 findings in at least one category,
2 input problem (missing or unreadable file, unparseable source file).

Checks: unresolved citation keys, sources never cited, duplicate keys, missing
required fields per entry type, placeholder or suspect field values, and
sentences with numbers but no citation nearby.
It cannot tell whether a source really says what the sentence claims, and it
cannot tell whether a source exists.
"""
import argparse
import json
import re
import sys

VERSION = 1

# Pandoc citation key: starts with a letter, digit or underscore; may contain
# internal punctuation; must not end in punctuation (so "@smith2020." works).
KEY_RE = re.compile(r"(?<![\w@\\])@\{?([A-Za-z0-9_](?:[\w:.#$%&+?<>~/-]*\w)?)\}?")
LATEX_CITE_RE = re.compile(
    r"\\(?:cite|citep|citet|citealp|citealt|citeauthor|citeyear|parencite|textcite|"
    r"autocite|footcite|nocite)\*?(?:\[[^\]]*\]){0,2}\{([^}]*)\}")
BRACKET_RE = re.compile(r"\[[^\[\]]*\]")
FENCE_RE = re.compile(r"^(\s*)(`{3,}|~{3,})")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$")
LIST_MARKER_RE = re.compile(r"^(\s*(?:[-*+]|\d+[.)])\s+|\s*>\s?)+")

# Sections whose numbers are the author's own data or machinery, not borrowed
# claims. Reason: Methods and Results report what the author did and found;
# demanding a citation for every figure there would bury real problems.
DEFAULT_SKIP_SECTIONS = (
    r"^(?:\d+[.)]?\s*)?(?:materials?\s+and\s+methods?|methods?|methodology|"
    r"materials?|participants?|procedure|results?|findings|appendix|appendices|"
    r"acknowledge?ments?|references|bibliography|works\s+cited|data\s+availability)\b")

ABBREVIATIONS = {
    "e.g", "i.e", "et al", "al", "fig", "figs", "eq", "eqs", "vs", "cf", "approx",
    "no", "dr", "prof", "mr", "mrs", "ms", "etc", "ca", "pp", "p", "vol", "ed",
    "eds", "resp", "inc", "st", "sec", "ch", "viz", "ibid", "op", "cit",
}
REF_LABEL_RE = re.compile(
    r"\b(?:Fig(?:ure)?s?|Tables?|Tab|Sections?|Sec|Eq(?:uation)?s?|Chapters?|Ch|"
    r"Appendix|Panels?|Steps?|Pages?|pp?|Lines?|Theorems?|Lemmas?|Hypothesis|H)"
    r"\.?\s*[\dA-Z][\w.\-]*")
ORDINAL_RE = re.compile(r"\b\d+(?:st|nd|rd|th)\b")
NUMBER_RE = re.compile(r"(?<![A-Za-z_])(?<![A-Za-z]-)(\d(?:[\d,]*\d)?(?:\.\d+)?)(%?)")

PLACEHOLDER_RE = re.compile(
    r"^\s*(?:todo|tbd|tba|unknown|xx+|\?+|n/?a|none|anonymous|fill\s*in|"
    r"placeholder|lorem.*|\.\.\.|-+)\s*$|\b(?:TODO|FIXME|XXX)\b", re.I)

# --- required fields -------------------------------------------------------
# A tuple means "any one of these". BibTeX lists follow the classic entry-type
# definitions; misc, online and unknown types use house rules (title and a date),
# because classic BibTeX requires nothing for misc and that hides bad entries.
YEAR = ("year", "date")
BIBTEX_REQUIRED = {
    "article": ["author", "title", ("journal", "journaltitle"), YEAR],
    "book": [("author", "editor"), "title", "publisher", YEAR],
    "booklet": ["title"],
    "inbook": [("author", "editor"), "title", ("chapter", "pages"), "publisher", YEAR],
    "incollection": ["author", "title", "booktitle", "publisher", YEAR],
    "inproceedings": ["author", "title", "booktitle", YEAR],
    "conference": ["author", "title", "booktitle", YEAR],
    "manual": ["title"],
    "mastersthesis": ["author", "title", ("school", "institution"), YEAR],
    "phdthesis": ["author", "title", ("school", "institution"), YEAR],
    "thesis": ["author", "title", ("school", "institution"), YEAR],
    "techreport": ["author", "title", "institution", YEAR],
    "report": ["author", "title", "institution", YEAR],
    "unpublished": ["author", "title", "note"],
    "proceedings": ["title", YEAR],
    "misc": ["title", YEAR],
    "online": ["title", ("author", "editor", "organization"), YEAR, ("url", "doi")],
}
BIBTEX_DEFAULT = ["title", YEAR]
CSL_REQUIRED = {
    "article-journal": ["author", "title", "container-title", "issued"],
    "article-magazine": ["author", "title", "container-title", "issued"],
    "article-newspaper": ["title", "container-title", "issued"],
    "article": ["author", "title", "issued"],
    "book": [("author", "editor"), "title", "publisher", "issued"],
    "chapter": ["author", "title", "container-title", "publisher", "issued"],
    "paper-conference": ["author", "title", "container-title", "issued"],
    "thesis": ["author", "title", "publisher", "issued"],
    "report": ["author", "title", "publisher", "issued"],
    "webpage": ["title", ("author", "container-title", "publisher"), "issued", "url"],
    "dataset": ["title", "author", "issued"],
}
CSL_DEFAULT = ["title", "issued"]


class InputError(Exception):
    pass


# --- source file parsing ---------------------------------------------------
def _skip_ws(s, i):
    while i < len(s) and s[i].isspace():
        i += 1
    return i


def _read_balanced(s, i, open_c="{", close_c="}"):
    """s[i] is open_c; return (inner text, index after the closing char) or None."""
    depth = 0
    j = i
    while j < len(s):
        c = s[j]
        if c == "\\":
            j += 2
            continue
        if c == open_c:
            depth += 1
        elif c == close_c:
            depth -= 1
            if depth == 0:
                return s[i + 1:j], j + 1
        j += 1
    return None


def _read_value(s, i):
    """Read a BibTeX field value (parts joined by #). Return (text, next index)."""
    parts = []
    while True:
        i = _skip_ws(s, i)
        if i >= len(s):
            return "".join(parts), i
        c = s[i]
        if c == "{":
            r = _read_balanced(s, i)
            if r is None:
                raise ValueError("unbalanced braces in a field value")
            parts.append(r[0])
            i = r[1]
        elif c == '"':
            j, depth = i + 1, 0
            while j < len(s):
                if s[j] == "\\":
                    j += 2
                    continue
                if s[j] == "{":
                    depth += 1
                elif s[j] == "}":
                    depth -= 1
                elif s[j] == '"' and depth == 0:
                    break
                j += 1
            if j >= len(s):
                raise ValueError("unterminated quoted value")
            parts.append(s[i + 1:j])
            i = j + 1
        else:
            m = re.match(r"[^\s,#}]+", s[i:])
            if not m:
                raise ValueError("missing field value")
            parts.append(m.group(0))
            i += m.end()
        i = _skip_ws(s, i)
        if i < len(s) and s[i] == "#":
            i += 1
            continue
        return "".join(parts), i


def parse_bibtex(text):
    """Return (entries, parse_errors). Entry: dict(key, type, fields, line)."""
    entries, errors = [], []
    i = 0
    while True:
        i = text.find("@", i)
        if i < 0:
            break
        line = text.count("\n", 0, i) + 1
        m = re.match(r"@\s*([A-Za-z]+)\s*([{(])", text[i:])
        if not m:
            i += 1
            continue
        etype = m.group(1).lower()
        close_c = "}" if m.group(2) == "{" else ")"
        body_start = i + m.end() - 1
        block = _read_balanced(text, body_start, m.group(2), close_c)
        if block is None:
            errors.append({"line": line, "error": "entry is not closed"})
            i += 1
            continue
        inner, after = block
        i = after
        if etype in ("comment", "preamble", "string"):
            continue
        km = re.match(r"\s*([^\s,{}]+)\s*,?", inner)
        if not km:
            errors.append({"line": line, "error": "entry has no citation key"})
            continue
        key = km.group(1)
        fields = {}
        pos = km.end()
        try:
            while True:
                pos = _skip_ws(inner, pos)
                while pos < len(inner) and inner[pos] == ",":
                    pos = _skip_ws(inner, pos + 1)
                if pos >= len(inner):
                    break
                fm = re.match(r"([^\s=,{}]+)\s*=", inner[pos:])
                if not fm:
                    raise ValueError("expected 'field = value'")
                name = fm.group(1).lower()
                value, pos = _read_value(inner, pos + fm.end())
                fields[name] = value.strip()
        except ValueError as exc:
            errors.append({"line": line, "key": key, "error": str(exc)})
        entries.append({"key": key, "type": etype, "fields": fields, "line": line})
    return entries, errors


def parse_csl(text):
    try:
        data = json.loads(text)
    except ValueError as exc:
        raise InputError(f"source file is not valid JSON: {exc}")
    if isinstance(data, dict) and isinstance(data.get("items"), list):
        data = data["items"]
    if not isinstance(data, list):
        raise InputError("CSL-JSON must be a list of items (or an object with an 'items' list)")
    entries, errors = [], []
    for idx, item in enumerate(data, 1):
        if not isinstance(item, dict) or item.get("id") in (None, ""):
            errors.append({"line": idx, "error": f"item {idx} has no 'id'"})
            continue
        fields = {str(k).lower(): v for k, v in item.items()}
        entries.append({"key": str(item["id"]), "type": str(item.get("type", "")).lower(),
                        "fields": fields, "line": idx})
    return entries, errors


def is_empty(value):
    if value is None:
        return True
    if isinstance(value, str):
        return not value.strip()
    if isinstance(value, dict):
        parts = value.get("date-parts")
        if parts is not None:
            return not any(x not in (None, "", []) for p in parts for x in (p if isinstance(p, list) else [p]))
        return all(is_empty(v) for v in value.values())
    if isinstance(value, list):
        return not value or all(is_empty(v) for v in value)
    return False


def missing_fields(entry, fmt):
    table, default = (BIBTEX_REQUIRED, BIBTEX_DEFAULT) if fmt == "bibtex" else (CSL_REQUIRED, CSL_DEFAULT)
    required = table.get(entry["type"], default)
    out = []
    for req in required:
        names = req if isinstance(req, tuple) else (req,)
        if all(is_empty(entry["fields"].get(n)) for n in names):
            out.append("|".join(names))
    return out


def suspect_fields(entry, fmt):
    out = []
    for name, value in entry["fields"].items():
        if isinstance(value, str) and PLACEHOLDER_RE.search(value):
            out.append({"field": name, "value": value, "reason": "placeholder text"})
    if fmt == "bibtex":
        year = entry["fields"].get("year", "")
        if year and not re.fullmatch(r"\d{4}[a-z]?", year.strip()):
            out.append({"field": "year", "value": year, "reason": "not a four-digit year"})
    else:
        issued = entry["fields"].get("issued")
        if isinstance(issued, dict) and isinstance(issued.get("date-parts"), list):
            try:
                y = issued["date-parts"][0][0]
                if y is not None and not re.fullmatch(r"\d{4}", str(y)):
                    out.append({"field": "issued", "value": str(y), "reason": "not a four-digit year"})
            except (IndexError, TypeError):
                pass
    return out


# --- manuscript masking and citation extraction ----------------------------
def mask(text, start, end, keep_newlines=True):
    seg = text[start:end]
    return text[:start] + "".join("\n" if (c == "\n" and keep_newlines) else " " for c in seg) + text[end:]


def mask_by_regex(text, pattern, flags=0):
    for m in list(re.finditer(pattern, text, flags)):
        text = mask(text, m.start(), m.end())
    return text


def strip_non_prose(raw):
    """Length-preserving mask of front matter, code, comments and math."""
    text = raw
    fm = re.match(r"\A---\s*\n.*?\n(?:---|\.\.\.)\s*(?:\n|\Z)", text, re.S)
    if fm:
        text = mask(text, 0, fm.end())
    lines = text.split("\n")
    out, fence = [], None
    for ln in lines:
        m = FENCE_RE.match(ln)
        if fence is None and m:
            fence = m.group(2)[0]
            out.append(" " * len(ln))
        elif fence is not None:
            out.append(" " * len(ln))
            if m and m.group(2)[0] == fence:
                fence = None
        else:
            out.append(ln)
    text = "\n".join(out)
    text = mask_by_regex(text, r"<!--.*?-->", re.S)
    text = mask_by_regex(text, r"`[^`\n]+`")
    text = mask_by_regex(text, r"\$\$.+?\$\$", re.S)
    text = mask_by_regex(text, r"(?<![\\$])\$(?=\S)[^$\n]+?(?<=\S)\$(?!\d)")
    return text, (raw[:fm.end()] if fm else "")


def find_citations(text):
    """Return list of (key, offset_start, offset_end_of_whole_citation_span)."""
    found = []  # (key, span_start, span_end)
    for m in LATEX_CITE_RE.finditer(text):
        for k in m.group(1).split(","):
            k = k.strip()
            if k:
                found.append((k, m.start(), m.end()))
    masked = text
    for m in LATEX_CITE_RE.finditer(text):
        masked = mask(masked, m.start(), m.end())
    for m in BRACKET_RE.finditer(masked):
        keys = [k.group(1) for k in KEY_RE.finditer(m.group(0))]
        for k in keys:
            found.append((k, m.start(), m.end()))
        if keys:
            masked = mask(masked, m.start(), m.end())
    for m in KEY_RE.finditer(masked):
        found.append((m.group(1), m.start(), m.end()))
    return found


def blank_citations(text):
    """Replace every citation span by a token of the same length."""
    spans = []
    for m in LATEX_CITE_RE.finditer(text):
        spans.append((m.start(), m.end()))
    tmp = text
    for s, e in spans:
        tmp = mask(tmp, s, e)
    for m in BRACKET_RE.finditer(tmp):
        if KEY_RE.search(m.group(0)):
            spans.append((m.start(), m.end()))
            tmp = mask(tmp, m.start(), m.end())
    for m in KEY_RE.finditer(tmp):
        spans.append((m.start(), m.end()))
    for s, e in sorted(spans):
        n = e - s
        token = "\u27e6" + "C" * max(n - 2, 0) + "\u27e7" if n >= 2 else "C"
        text = text[:s] + token + text[e:]
    return text


def nocite_keys(frontmatter, text):
    keys, wildcard = set(), False
    for m in re.finditer(r"^nocite:\s*(.*(?:\n[ \t]+.*)*)", frontmatter, re.M):
        block = m.group(1)
        if "@*" in block:
            wildcard = True
        keys.update(k.group(1) for k in KEY_RE.finditer(block))
    for m in re.finditer(r"\\nocite\{([^}]*)\}", text):
        for k in m.group(1).split(","):
            k = k.strip()
            if k == "*":
                wildcard = True
            elif k:
                keys.add(k)
    return keys, wildcard


# --- sentences and numbers -------------------------------------------------
BOUNDARY_RE = re.compile(r"(?<=[.!?])[\"')\]\u201d\u2019]*\s+(?=[\"'(\[\u201c\u2018]*[A-Z0-9\u27e6])")


def split_sentences(par, base):
    """par: paragraph text; base: offset of par in the document. -> [(start, end)]"""
    cuts = [0]
    for m in BOUNDARY_RE.finditer(par):
        before = par[:m.start()]
        wm = re.search(r"([A-Za-z.]+)$", before)
        word = wm.group(1).lower().rstrip(".") if wm else ""
        if word in ABBREVIATIONS or (len(word) == 1 and word.isalpha()
                                     and before[-2:-1] in (" ", "", "(")):
            continue
        cuts.append(m.end())
    cuts.append(len(par))
    return [(base + a, base + b) for a, b in zip(cuts, cuts[1:]) if par[a:b].strip()]


def numbers_in(sentence):
    s = REF_LABEL_RE.sub(" ", sentence)
    s = ORDINAL_RE.sub(" ", s)
    s = re.sub(r"\[\^[^\]]*\]", " ", s)
    found = []
    for m in NUMBER_RE.finditer(s):
        digits, pct = m.group(1), m.group(2)
        if pct or "." in digits or "," in digits or len(digits) >= 2:
            found.append(digits + pct)
    return found


def prepare_claim_text(text):
    """Mask links, URLs and list markers (length preserving) after citations are blanked."""
    text = mask_by_regex(text, r"(?<=\])\([^)\s]*\)")  # link targets
    text = mask_by_regex(text, r"!\[[^\]]*\]")
    text = mask_by_regex(text, r"https?://[^\s)>\]]+")
    return text


def scan_claims(clean, skip_re, window_before, window_after, all_sections, covered):
    lines = clean.split("\n")
    offsets, pos = [], 0
    for ln in lines:
        offsets.append(pos)
        pos += len(ln) + 1
    stack = []  # (level, title)
    skipped = []
    results, checked = [], 0
    par = []  # list of line indexes

    def flush():
        nonlocal checked
        if not par:
            return
        a = offsets[par[0]]
        b = offsets[par[-1]] + len(lines[par[-1]])
        ptext = clean[a:b]
        sents = split_sentences(ptext, a)
        words_ok = [len(re.findall(r"[A-Za-z]{2,}", clean[s:e])) >= 2 for s, e in sents]
        has_cite = ["\u27e6" in clean[s:e] for s, e in sents]
        for i, (s, e) in enumerate(sents):
            if not words_ok[i] or has_cite[i]:
                continue
            nums = numbers_in(clean[s:e])
            if not nums:
                continue
            checked += 1
            lo, hi = max(0, i - window_before), min(len(sents), i + window_after + 1)
            first = s
            while first < e and clean[first].isspace():
                first += 1
            item = {
                "line": clean.count("\n", 0, first) + 1,
                "section": stack[-1][1] if stack else "",
                "numbers": nums,
                "sentence": re.sub(r"\s+", " ", clean[s:e]).strip().replace("\u27e6", "[").replace("\u27e7", "]"),
            }
            if any(has_cite[lo:hi]):
                covered.append(item)
                continue
            results.append(item)
        par.clear()

    skipping = False
    for idx, ln in enumerate(lines):
        hm = HEADING_RE.match(ln)
        if hm:
            flush()
            level = len(hm.group(1))
            while stack and stack[-1][0] >= level:
                stack.pop()
            stack.append((level, hm.group(2)))
            skipping = (not all_sections) and any(skip_re.search(t) for _, t in stack)
            if skipping and skip_re.search(hm.group(2)):
                skipped.append(hm.group(2))
            continue
        if not ln.strip():
            flush()
            continue
        if skipping or ln.lstrip().startswith("|") or re.match(r"^\s*[-=|:\s]{3,}$", ln):
            flush()
            continue
        marker = LIST_MARKER_RE.match(ln)
        if marker:
            flush()
            m_end = marker.end()
            lines[idx] = " " * m_end + ln[m_end:]
            clean = clean[:offsets[idx]] + lines[idx] + clean[offsets[idx] + len(ln):]
        par.append(idx)
    flush()
    return results, checked, skipped


# --- main ------------------------------------------------------------------
def read_text(path, what):
    try:
        with open(path, "rb") as fh:
            data = fh.read()
    except OSError as exc:
        raise InputError(f"cannot read {what} '{path}': {exc.strerror or exc}")
    if not data.strip():
        raise InputError(f"{what} '{path}' is empty")
    try:
        return data.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise InputError(f"{what} '{path}' is not UTF-8; re-save it as UTF-8")


def analyse(manuscript_path, sources_path, window_before=0, window_after=1,
            skip_sections=DEFAULT_SKIP_SECTIONS, all_sections=False):
    raw = read_text(manuscript_path, "manuscript")
    src = read_text(sources_path, "sources file")
    stripped = src.lstrip()
    fmt = "csl-json" if stripped[:1] in "[{" else "bibtex"
    entries, parse_errors = parse_csl(src) if fmt == "csl-json" else parse_bibtex(src)
    kind = "csl" if fmt == "csl-json" else "bibtex"
    if not entries and not parse_errors:
        raise InputError("sources file holds no entries; is it BibTeX (.bib) or CSL-JSON?")

    text, frontmatter = strip_non_prose(raw)
    cites = find_citations(text)
    nokeys, wildcard = nocite_keys(frontmatter, text)

    # duplicates (case-insensitive: BibTeX treats keys that way)
    groups = {}
    for e in entries:
        groups.setdefault(e["key"].lower(), []).append(e)
    duplicates = [{"key": g[0]["key"], "count": len(g), "locations": [e["line"] for e in g]}
                  for g in groups.values() if len(g) > 1]
    duplicates.sort(key=lambda d: d["key"].lower())

    known = {e["key"] for e in entries}
    known_lower = {}
    for e in entries:
        known_lower.setdefault(e["key"].lower(), e["key"])

    cited_lines = {}
    for key, s, _e in cites:
        cited_lines.setdefault(key, []).append(text.count("\n", 0, s) + 1)
    unresolved = []
    for key in sorted(cited_lines):
        if key in known:
            continue
        item = {"key": key, "lines": sorted(set(cited_lines[key]))}
        if key.lower() in known_lower:
            item["hint"] = f"differs only in letter case from '{known_lower[key.lower()]}'"
        unresolved.append(item)

    cited = set(cited_lines) | nokeys
    uncited = [] if wildcard else sorted(known - cited, key=str.lower)

    missing, suspect = [], []
    for e in entries:
        miss = missing_fields(e, kind)
        if miss:
            missing.append({"key": e["key"], "type": e["type"], "missing": miss})
        for s in suspect_fields(e, kind):
            suspect.append({"key": e["key"], **s})
    table = BIBTEX_REQUIRED if kind == "bibtex" else CSL_REQUIRED
    unknown_types = sorted({e["type"] for e in entries if e["type"] not in table})

    clean = prepare_claim_text(blank_citations(text))
    covered = []
    claims, checked, skipped = scan_claims(
        clean, re.compile(skip_sections, re.I), window_before, window_after, all_sections, covered)

    counts = {
        "entries": len(entries),
        "citation_occurrences": len(cites),
        "distinct_keys_cited": len(cited_lines),
        "numeric_sentences_checked": checked,
    }
    problems = {
        "unresolved_keys": len(unresolved),
        "uncited_sources": len(uncited),
        "duplicate_keys": len(duplicates),
        "missing_fields": len(missing),
        "suspect_fields": len(suspect),
        "uncited_numeric_claims": len(claims),
        "parse_errors": len(parse_errors),
    }
    notes = []
    if wildcard:
        notes.append("nocite wildcard found: the uncited-sources check was skipped")
    if unknown_types:
        notes.append("entry types without a rule use the default (title and date): " + ", ".join(unknown_types))
    return {
        "tool": "manuscript_check",
        "version": VERSION,
        "ok": sum(problems.values()) == 0,
        "manuscript": manuscript_path,
        "sources": sources_path,
        "source_format": fmt,
        "counts": counts,
        "problems": problems,
        "unresolved_keys": unresolved,
        "uncited_sources": uncited,
        "duplicate_keys": duplicates,
        "missing_fields": missing,
        "suspect_fields": suspect,
        "uncited_numeric_claims": claims,
        "numeric_claims_covered_by_neighbour": covered,
        "parse_errors": parse_errors,
        "skipped_sections": skipped,
        "notes": notes,
    }


def emit(obj):
    sys.stdout.buffer.write((json.dumps(obj, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))


def main(argv=None):
    ap = argparse.ArgumentParser(description="Check a Markdown manuscript against BibTeX or CSL-JSON.")
    ap.add_argument("manuscript")
    ap.add_argument("sources")
    ap.add_argument("--window-after", type=int, default=1)
    ap.add_argument("--window-before", type=int, default=0)
    ap.add_argument("--skip-sections", default=DEFAULT_SKIP_SECTIONS)
    ap.add_argument("--all-sections", action="store_true")
    try:
        args = ap.parse_args(argv)
    except SystemExit as exc:
        if exc.code not in (0, None):
            emit({"tool": "manuscript_check", "version": VERSION, "ok": False,
                  "error": "bad arguments; run with --help"})
        return 2 if exc.code else 0
    try:
        re.compile(args.skip_sections)
        report = analyse(args.manuscript, args.sources, max(0, args.window_before),
                         max(0, args.window_after), args.skip_sections, args.all_sections)
    except re.error as exc:
        emit({"tool": "manuscript_check", "version": VERSION, "ok": False, "error": f"bad --skip-sections regex: {exc}"})
        return 2
    except InputError as exc:
        emit({"tool": "manuscript_check", "version": VERSION, "ok": False, "error": str(exc)})
        return 2
    emit(report)
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
