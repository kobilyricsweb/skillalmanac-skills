#!/usr/bin/env python3
"""repair_ocr.py - repair OCR output with evidence from the document itself.

Usage:
    python repair_ocr.py INPUT [--doctype prose|table|form|receipt] [--lang en]
        [--out FILE] [--report FILE] [--force] [--dry-run]
        [--split-columns CHAR_INDEX] [--headers auto|on|off] [--no-unwrap]

What it reads: INPUT (UTF-8; falls back to cp1252 with a note). Newlines are
normalised to \\n and form feeds (\\f) are treated as page breaks and kept.
What it writes: the repaired text to --out (default: next to INPUT as
<name>.repaired<ext>) and, when --report is given, the JSON report. The JSON
report is always printed to stdout. --dry-run writes nothing.
It NEVER writes to INPUT: an --out or --report that resolves to the input
path is refused even with --force. An existing output needs --force.

Repairs (every one is logged with line and reason):
  ligature, invisible-char, quote-artefact (all doctypes except where noted),
  confusable (rn->m, vv->w, interior I->l/i, and digit-for-letter 0->o 1->l/i
  5->s in prose) only when the corrected word is attested elsewhere in the
  document, dehyphenate and unwrap (prose only), header-footer (prose, needs
  3 or more pages separated by form feeds), column-reflow (only with
  --split-columns).
Numbers and amounts are never altered. Damaged numbers (2O24, l00) are only
flagged. After the repairs the script compares the numbers in the input and
in the output; if they differ it refuses to write the repaired file.

Exit codes: 0 repaired (or nothing to repair); 1 number check failed, nothing
written; 2 usage or file error (message on stderr).
Standard library only. No network, no subprocess.
"""
import argparse
import json
import math
import os
import re
import sys
from collections import Counter

VERSION = "0.1.0"
DOCTYPES = ("prose", "table", "form", "receipt")

# --- thresholds. Each is a working value, not a measured optimum. ---
HF_EDGE = 2            # header/footer candidates: first and last 2 non-blank lines of a page
HF_MIN_PAGES = 3       # fewer pages cannot show a repeat pattern
HF_FRACTION = 0.6      # a line must repeat on 60% of pages (and at least 3) to count as header/footer
WRAP_FILL = 0.75       # a line shorter than 75% of the text width was not filled by wrapping
WRAP_FILL_AFTER_PUNCT = 0.90  # after a sentence end, require an almost full line before joining
WRAP_MAX_WIDTH = 120   # wider text is treated as already unwrapped paragraphs
WRAP_MIN_LINES = 6     # too few lines to judge the layout
WRAP_SHARE = 0.35      # at least 35% of lines near full width for the text to count as hard-wrapped
WIDTH_PERCENTILE = 0.90  # text width = 90th percentile of line lengths (ignores a few long outliers)
ATTEST_MIN = 2         # corrected word must occur at least twice elsewhere (rn/m, vv/w)
ATTEST_RATIO = 2       # ... and at least twice as often as the form being replaced
FLAG_ATTEST = 3        # suggestion-only pairs need the alternative 3 times
GUTTER_MIN_WIDTH = 3   # a column gutter is at least 3 blank character columns
GUTTER_MIN_LINES = 8   # lines needed on a page before a gutter is reported
GUTTER_SPACE_SHARE = 0.95
SPLIT_SHARE = 0.90     # share of long lines that must show blank space at the gutter to split a page
SPLIT_MIN_WIDE = 3
MAX_SUSPICIOUS = 300   # list cap; counts in stats stay exact

LIGATURES = {"\ufb00": "ff", "\ufb01": "fi", "\ufb02": "fl", "\ufb03": "ffi", "\ufb04": "ffl",
             "\ufb05": "st", "\ufb06": "st"}
INVISIBLES = "\u00ad\u200b\u2060"
HYPHENS = "-\u2010\u2011\u00ac"
# rn read for m, vv read for w: the only automatic word-level pairs. cl/d and li/h collide with real
# words (clog/dog, lie/he), so they are suggestions only.
AUTO_PAIRS = (("rn", "m"), ("vv", "w"))
FLAG_PAIRS = (("li", "h"), ("cl", "d"))
DIGIT_OPTIONS = {"0": ("o",), "1": ("l", "i"), "5": ("s",)}
KEEP_HYPHEN_PREFIXES = {"self", "ex", "vice", "well", "ill", "half", "cross"}  # English only

ALNUM = re.compile(r"[^\W_]+")
URLISH = re.compile(r"[@/\\]|www\.|https?:", re.I)
HYPH_END = re.compile("([^\\W\\d_]{2,})[" + re.escape(HYPHENS) + "]$")
NUM_RE = re.compile(r"(?<![^\W_])\d+(?:[.,:/]\d+)*(?![^\W_])")
ORDINAL = re.compile(r"^\d(st|nd|rd|th)$", re.I)
UNIT_PART = re.compile(r"^\d+(st|nd|rd|th|am|pm|kg|km|cm|mm|ml|mg|gb|mb|kb|tb|hz|khz|mhz|ghz|k|m|x|s|h|d|g|l)$", re.I)
LIST_RE = re.compile(r"^\s*(?:[-*\u2022\u00b7\u25aa\u2013\u2014]|\d{1,3}[.)]|[A-Za-z][.)]|\(\w{1,3}\))\s+")
TERMINAL_RE = re.compile(r"[.!?:][\"\u201d\u2019')\]]?$")
NUMBER_CONFUSABLE = re.compile(r"[0-9OoIl|.,]+")
STRAY_IN_WORD = re.compile(r"[^\W\d_][|\\\u00a6~^][^\W\d_]")
ISOLATED = re.compile(r"[|\\~^_\u00a6\u00ac\u00b0`\u00b4]{1,3}")
EDGE_PUNCT = "\"'.,;:!?()[]{}<>\u201c\u201d\u2018\u2019"


class UsageError(Exception):
    pass


def mk(line, line_end, cls, before, after, reason):
    return {"line": line, "line_end": line_end, "class": cls, "before": before, "after": after, "reason": reason}


# ---------------------------------------------------------------- file safety

def same_path(a, b):
    if os.path.normcase(os.path.realpath(a)) == os.path.normcase(os.path.realpath(b)):
        return True
    try:
        return os.path.samefile(a, b)
    except OSError:
        return False


def guard_outputs(inp, out, report, force):
    for label, p in (("--out", out), ("--report", report)):
        if not p:
            continue
        if same_path(inp, p):
            raise UsageError(f"{label} resolves to the input file; the input is never overwritten, even with --force. Choose another path.")
        if os.path.isdir(p):
            raise UsageError(f"{label} is a directory: {p}")
        parent = os.path.dirname(os.path.abspath(p))
        if not os.path.isdir(parent):
            raise UsageError(f"folder for {label} does not exist: {parent}")
        if os.path.exists(p) and not force:
            raise UsageError(f"{label} already exists: {p}. Use --force to replace it (never allowed for the input).")
    if out and report and same_path(out, report):
        raise UsageError("--out and --report resolve to the same file")


def read_text(path, notes):
    try:
        with open(path, "rb") as fh:
            data = fh.read()
    except OSError as exc:
        raise UsageError(f"cannot read {path}: {exc.strerror}")
    if not data.strip():
        raise UsageError("input is empty")
    try:
        text = data.decode("utf-8-sig")
    except UnicodeDecodeError:
        text = data.decode("cp1252", errors="replace")
        notes.append("input is not valid UTF-8; decoded as cp1252 (undecodable bytes became U+FFFD)")
    return text.replace("\r\n", "\n").replace("\r", "\n")


def write_text(path, text):
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)


# ---------------------------------------------------------------- tokens and counts

def line_tokens(line):
    """Yield (start, end, token) for alphanumeric runs, skipping URL- and e-mail-like chunks."""
    for m in re.finditer(r"\S+", line):
        chunk = m.group()
        if URLISH.search(chunk):
            continue
        for t in ALNUM.finditer(chunk):
            yield m.start() + t.start(), m.start() + t.end(), t.group()


def page_tokens(pg):
    """Per line: tokens plus a flag marking hyphen-break fragments (last token before a line-end
    hyphen, first token of the next line). Fragments are not whole words and are never counted
    or corrected on their own."""
    res = []
    prev = False
    for _no, text in pg:
        toks = list(line_tokens(text))
        frag_last = bool(HYPH_END.search(text.rstrip())) and bool(toks)
        flags = [False] * len(toks)
        if prev and toks:
            flags[0] = True
        if frag_last:
            flags[-1] = True
        res.append((toks, flags))
        prev = frag_last
    return res


class Counts:
    def __init__(self, pages):
        self.lower = Counter()   # exact lowercase alphabetic tokens
        self.anyc = Counter()    # all alphabetic tokens, lowercased
        self.hyph = Counter()    # in-line hyphenated compounds, lowercased
        for pg in pages:
            for (no, text), (toks, flags) in zip(pg, page_tokens(pg)):
                for (_s, _e, t), frag in zip(toks, flags):
                    if frag or not t.isalpha():
                        continue
                    self.anyc[t.lower()] += 1
                    if t.islower():
                        self.lower[t] += 1
                for m in re.finditer(r"([^\W\d_]+)-([^\W\d_]+)", text):
                    self.hyph[m.group(1).lower() + "-" + m.group(2).lower()] += 1


# ---------------------------------------------------------------- repair steps

def strip_headers(pages, mode, doctype, changes, notes):
    if mode == "off" or (mode == "auto" and doctype != "prose"):
        return pages
    filled = [pg for pg in pages if any(t.strip() for _n, t in pg)]
    if len(filled) < HF_MIN_PAGES:
        if mode == "on" or doctype == "prose":
            notes.append("header/footer removal skipped: fewer than 3 pages (pages are separated by form feed characters)")
        return pages
    keys_per_page = []
    for pg in pages:
        nz = [i for i, (_n, t) in enumerate(pg) if t.strip()]
        edge = set(nz[:HF_EDGE] + nz[-HF_EDGE:])
        keys = {}
        for i in edge:
            key = " ".join(re.sub(r"\d+", "#", pg[i][1].lower()).split())
            if key:
                keys[i] = key
        keys_per_page.append(keys)
    seen = Counter()
    for keys in keys_per_page:
        for key in set(keys.values()):
            seen[key] += 1
    need = max(HF_MIN_PAGES, math.ceil(HF_FRACTION * len(filled)))
    out = []
    for pg, keys in zip(pages, keys_per_page):
        kept = []
        for i, item in enumerate(pg):
            key = keys.get(i)
            if key is not None and seen[key] >= need:
                changes.append(mk(item[0], item[0], "header-footer", item[1].strip(), "",
                                  f"line repeats (digits ignored) on {seen[key]} of {len(filled)} pages at a page edge"))
            else:
                kept.append(item)
        out.append(kept)
    return out


def detect_gutter(pg):
    body = [t for _n, t in pg if t.strip()]
    if len(body) < GUTTER_MIN_LINES:
        return None
    maxlen = max(len(t) for t in body)
    good = []
    for c in range(int(0.3 * maxlen), int(0.7 * maxlen) + 1):
        longer = [t for t in body if len(t) > c + 3]
        if len(longer) >= 6 and sum(1 for t in longer if t[c] == " ") / len(longer) >= GUTTER_SPACE_SHARE:
            good.append(c)
    run = []
    for c in good:
        if run and c != run[-1] + 1:
            if len(run) >= GUTTER_MIN_WIDTH:
                break
            run = []
        run.append(c)
    if len(run) >= GUTTER_MIN_WIDTH:
        return run[0], run[-1] + 1
    return None


def split_columns(pages, gutter, changes, notes):
    out = []
    split_any = False
    for pi, pg in enumerate(pages, 1):
        wide = [(n, t) for n, t in pg if len(t) > gutter and t.strip()]
        if len(wide) < SPLIT_MIN_WIDE:
            out.append(pg)
            continue
        ok = sum(1 for _n, t in wide if t[gutter - 2:gutter].strip() == "")
        if ok < SPLIT_SHARE * len(wide):
            notes.append(f"page {pi} not split: gutter at character {gutter} is blank in only {ok} of {len(wide)} long lines")
            out.append(pg)
            continue
        split_any = True
        left = [[n, t[:gutter].rstrip()] for n, t in pg]
        right = [[n, t[gutter:].strip()] for n, t in pg]

        def tidy(rows):
            res = []
            for n, t in rows:
                if not t and (not res or not res[-1][1]):
                    continue
                res.append([n, t])
            while res and not res[-1][1]:
                res.pop()
            return res
        left, right = tidy(left), tidy(right)
        first = min(n for n, _t in wide)
        last = max(n for n, _t in wide)
        changes.append(mk(first, last, "column-reflow", f"two columns read across, gutter at character {gutter}",
                          "left column, blank line, right column",
                          f"blank gutter found in {ok} of {len(wide)} long lines on page {pi}"))
        trail = [[pg[-1][0], ""]] if not pg[-1][1].strip() else []  # keep the page's final newline
        out.append(left + [[right[0][0] if right else last, ""]] + right + trail)
    if not split_any:
        raise UsageError(f"--split-columns {gutter}: no page has a blank gutter at that character index; "
                         "run once without the option and read the column-layout hints in suspicious[]")
    return out


def char_repairs(pages, doctype, changes):
    lig_re = re.compile("\\S*[" + "".join(LIGATURES) + "]\\S*")
    inv_re = re.compile("\\S*[" + INVISIBLES + "]\\S*")
    quote_re = re.compile(r"\S*(?:``|'')\S*")
    tick_re = re.compile(r"\S*[^\W\d_][`\u00b4][^\W\d_]\S*")
    for pg in pages:
        for item in pg:
            no, text = item
            orig_line = text

            def log(cls, before, after, reason):
                changes.append(mk(no, no, cls, before, after, reason))

            def sub_lig(m):
                w = m.group()
                new = "".join(LIGATURES.get(c, c) for c in w)
                log("ligature", w, new, "ligature character expanded to plain letters")
                return new
            text = lig_re.sub(sub_lig, text)

            if doctype == "prose" and text.rstrip().endswith("\u00ad"):
                t2 = text.rstrip()
                text = t2[:-1] + "-" + text[len(t2):]
                log("invisible-char", "soft hyphen at line end", "-",
                    "shown as a hyphen so the line-break join can see it")

            def sub_inv(m):
                w = m.group()
                new = "".join(c for c in w if c not in INVISIBLES)
                log("invisible-char", w, new, "soft hyphen or zero-width character removed inside a word")
                return new
            text = inv_re.sub(sub_inv, text)

            if doctype == "prose":
                def sub_q(m):
                    w = m.group()
                    new = w.replace("``", '"').replace("''", '"')
                    log("quote-artefact", w, new, "doubled apostrophe or backtick pair is an OCR quote mark")
                    return new
                text = quote_re.sub(sub_q, text)

                def sub_t(m):
                    w = m.group()
                    new = w.replace("`", "'").replace("\u00b4", "'")
                    log("quote-artefact", w, new, "backtick or acute accent between letters is an apostrophe")
                    return new
                text = tick_re.sub(sub_t, text)
            if text != orig_line:
                item[1] = text


def decide(tok, counts, doctype):
    """Return ('fix', candidate, reason), ('flag', candidate, note) or None for one token."""
    low = counts.lower
    if tok.isalpha() and tok.islower():
        c0 = low.get(tok, 0)
        cands = set()
        for bad, good in AUTO_PAIRS:
            i = tok.find(bad)
            while i != -1:
                cands.add((tok[:i] + good + tok[i + len(bad):], bad + "->" + good))
                i = tok.find(bad, i + 1)
        scored = sorted(((low.get(c, 0), c, p) for c, p in cands), reverse=True)
        if scored and scored[0][0] > 0:
            top = scored[0]
            tied = len(scored) > 1 and scored[1][0] == top[0] and scored[1][1] != top[1]
            if tied:
                return ("flag", top[1], f"two corrections are equally attested ({top[1]}, {scored[1][1]})")
            if top[0] >= ATTEST_MIN and top[0] >= ATTEST_RATIO * c0:
                return ("fix", top[1], f"{top[2]}: '{top[1]}' appears {top[0]}x in the document, '{tok}' {c0}x")
            if c0 == 1:
                return ("flag", top[1], f"'{top[1]}' appears {top[0]}x; too little evidence to change '{tok}'")
        if len(tok) >= 3 and c0 == 1:
            for bad, good in FLAG_PAIRS:
                i = tok.find(bad)
                while i != -1:
                    c = tok[:i] + good + tok[i + len(bad):]
                    if low.get(c, 0) >= FLAG_ATTEST:
                        return ("flag", c, f"{bad}->{good} is a known confusion but also matches real words; '{c}' appears {low[c]}x")
                    i = tok.find(bad, i + 1)
        return None
    if re.fullmatch(r"[a-z]+I[a-z]+", tok):
        i = tok.index("I")
        opts = sorted(((low.get(tok[:i] + r + tok[i + 1:], 0), tok[:i] + r + tok[i + 1:]) for r in ("l", "i")), reverse=True)
        if opts[0][0] >= 1 and opts[0][0] > opts[1][0]:
            return ("fix", opts[0][1], f"capital I inside a lowercase word; '{opts[0][1]}' appears {opts[0][0]}x")
        return ("flag", opts[0][1], "capital I inside a lowercase word; no unique attested correction")
    if (doctype == "prose" and tok.isascii() and any(c.isdigit() for c in tok) and any(c.isalpha() for c in tok)
            and not ORDINAL.match(tok) and tok == tok.lower()):
        letters = sum(c.isalpha() for c in tok)
        runs = re.findall(r"\d+", tok)
        if letters >= 2 and all(len(r) == 1 and r in DIGIT_OPTIONS for r in runs) and len(runs) <= 2:
            parts = re.split(r"(\d)", tok)
            variants = [""]
            for p in parts:
                if p in DIGIT_OPTIONS:
                    variants = [v + o for v in variants for o in DIGIT_OPTIONS[p]]
                else:
                    variants = [v + p for v in variants]
            scored = sorted(((low.get(v, 0), v) for v in variants), reverse=True)
            if scored[0][0] >= 1:
                if len(scored) > 1 and scored[1][0] == scored[0][0]:
                    return ("flag", scored[0][1], "digit stands for a letter but two corrections are equally attested")
                return ("fix", scored[0][1], f"digit read for a letter; '{scored[0][1]}' appears {scored[0][0]}x in the document")
    return None


def fix_confusables(pages, counts, doctype, changes, hints):
    for pg in pages:
        info = page_tokens(pg)
        for li, (toks, flags) in enumerate(info):
            no, text = pg[li]
            edits = []
            for (s, e, t), frag in zip(toks, flags):
                if frag:
                    continue
                res = decide(t, counts, doctype)
                if not res:
                    continue
                if res[0] == "fix":
                    edits.append((s, e, t, res[1], res[2]))
                else:
                    hints.append({"original_line": no, "kind": "confusable-unconfirmed", "token": t,
                                  "suggestion": res[1], "note": res[2]})
            for s, e, t, cand, reason in reversed(edits):
                text = text[:s] + cand + text[e:]
            for s, e, t, cand, reason in edits:
                changes.append(mk(no, no, "confusable", t, cand, reason))
            pg[li][1] = text


class Para:
    def __init__(self, no, text):
        self.start = no
        self.last_no = no
        self.text = text
        self.last_len = len(text.rstrip())
        self.unwrapped = 0
        self.first = text.strip()


def emit(para, out, changes):
    if para.unwrapped:
        changes.append(mk(para.start, para.last_no, "unwrap", para.first[:60],
                          f"{para.unwrapped + 1} lines joined into 1",
                          "hard-wrapped lines (each filled most of the text width)"))
    out.append((para.start, para.last_no, para.text))


def try_dehyphen(cur, no, nxt, counts, lang, changes):
    t = cur.text.rstrip()
    m = HYPH_END.search(t)
    if not m:
        return False
    if m.start(1) > 0 and t[m.start(1) - 1].isdigit():
        return False
    n = nxt.lstrip()
    m2 = re.match(r"([^\W\d_]+)", n)
    if not m2 or not m2.group(1)[0].islower():
        return False
    left, first = m.group(1), m2.group(1)
    j = (left + first).lower()
    h = left.lower() + "-" + first.lower()
    c_join, c_h = counts.anyc.get(j, 0), counts.hyph.get(h, 0)
    if c_h and c_h >= c_join:
        keep, reason = True, f"hyphenated form '{h}' appears {c_h}x elsewhere in the document"
    elif c_join:
        keep, reason = False, f"joined form '{j}' appears {c_join}x elsewhere in the document"
    elif lang == "en" and left.lower() in KEEP_HYPHEN_PREFIXES and counts.anyc.get(first.lower(), 0) > 0:
        keep, reason = True, f"'{left.lower()}-' is a compound prefix and '{first.lower()}' is a word in the document"
    else:
        keep, reason = False, "no evidence in the document; default join of a line-end hyphen before a lowercase letter"
    break_line = cur.last_no
    cur.text = t[:m.start(1)] + left + ("-" if keep else "") + n
    cur.last_no = no
    cur.last_len = len(nxt.rstrip())
    changes.append(mk(break_line, no, "dehyphenate",
                      left + "-<NL>" + first, left + ("-" if keep else "") + first, reason))
    return True


def should_unwrap(cur, nxt, width):
    if re.match(r"\s{4,}|\t", nxt) or LIST_RE.match(nxt):
        return False
    if cur.last_len < WRAP_FILL * width:
        return False
    s = nxt.strip()
    if s.isupper() and sum(c.isalpha() for c in s) >= 3 and len(s) < 0.6 * width:
        return False
    if TERMINAL_RE.search(cur.text.rstrip()) and not s[:1].islower() and cur.last_len < WRAP_FILL_AFTER_PUNCT * width:
        return False
    return True


def measure_width(pages):
    lens = sorted(len(t.rstrip()) for pg in pages for _n, t in pg if t.strip())
    if len(lens) < WRAP_MIN_LINES:
        return None, False, "fewer than 6 non-blank lines; layout not judged"
    width = lens[int(WIDTH_PERCENTILE * (len(lens) - 1))]
    if width > WRAP_MAX_WIDTH:
        return width, False, f"text width {width} exceeds {WRAP_MAX_WIDTH}; looks like unwrapped paragraphs, lines not joined"
    near = sum(1 for n in lens if WRAP_FILL * width <= n <= width)
    if near / len(lens) < WRAP_SHARE:
        return width, False, f"only {near} of {len(lens)} lines are near full width; not treated as hard-wrapped"
    return width, True, f"hard-wrapped at about {width} characters"


def reflow(pages, counts, lang, do_unwrap, changes, stats):
    width, wrapped, note = measure_width(pages)
    stats["line_width"] = width
    stats["unwrap_applied"] = bool(do_unwrap and wrapped)
    stats["unwrap_note"] = note if do_unwrap else "disabled by --no-unwrap"
    out_pages = []
    for pg in pages:
        out = []
        cur = None
        for no, text in pg:
            if not text.strip():
                if cur:
                    emit(cur, out, changes)
                    cur = None
                out.append((no, no, text))
                continue
            if cur is None:
                cur = Para(no, text)
                continue
            if try_dehyphen(cur, no, text, counts, lang, changes):
                continue
            if do_unwrap and wrapped and should_unwrap(cur, text, width):
                cur.text = cur.text.rstrip() + " " + text.strip()
                cur.last_no = no
                cur.last_len = len(text.rstrip())
                cur.unwrapped += 1
                continue
            emit(cur, out, changes)
            cur = Para(no, text)
        if cur:
            emit(cur, out, changes)
        out_pages.append(out)
    return out_pages


# ---------------------------------------------------------------- residual scan

def suspicious_scan(final_pages):
    found = []
    base = 1
    for pg in final_pages:
        for k, (start, _end, text) in enumerate(pg):
            rep = base + k
            for chunk in text.split():
                core = chunk.strip(EDGE_PUNCT)
                if "\ufffd" in chunk:
                    found.append({"repaired_line": rep, "original_line": start, "kind": "replacement-char", "token": chunk,
                                  "suggestion": None, "note": "undecodable character; check the scan"})
                    continue
                if not core:
                    if ISOLATED.fullmatch(chunk):
                        found.append({"repaired_line": rep, "original_line": start, "kind": "isolated-symbol", "token": chunk,
                                      "suggestion": None, "note": "isolated symbol; likely scan noise"})
                    continue
                if ISOLATED.fullmatch(core):
                    found.append({"repaired_line": rep, "original_line": start, "kind": "isolated-symbol", "token": chunk,
                                  "suggestion": None, "note": "isolated symbol; likely scan noise"})
                    continue
                has_digit = any(c.isdigit() for c in core)
                if has_digit and NUMBER_CONFUSABLE.fullmatch(core) and re.search(r"[OoIl|]", core):
                    sug = core.replace("O", "0").replace("o", "0").replace("l", "1").replace("I", "1").replace("|", "1")
                    found.append({"repaired_line": rep, "original_line": start, "kind": "number-confusable", "token": chunk,
                                  "suggestion": sug, "note": "digits mixed with O/o/l/I/|; numbers are never changed automatically, check the scan"})
                    continue
                if STRAY_IN_WORD.search(core):
                    found.append({"repaired_line": rep, "original_line": start, "kind": "stray-symbol-in-word", "token": chunk,
                                  "suggestion": None, "note": "symbol between letters"})
                    continue
                if has_digit and any(c.isalpha() for c in core):
                    parts = [p for p in re.split(r"[-/_.,:]+", core) if p]
                    bad = [p for p in parts if any(c.isdigit() for c in p) and any(c.isalpha() for c in p)
                           and not UNIT_PART.match(p)]
                    if bad:
                        found.append({"repaired_line": rep, "original_line": start, "kind": "mixed-letters-digits", "token": chunk,
                                      "suggestion": None, "note": "letters and digits in one token; may be a code or a misread"})
        base += len(pg) - 1
    return found


def number_multiset(text):
    return Counter(NUM_RE.findall(text))


def render(final_pages):
    return "\f".join("\n".join(t for _s, _e, t in pg) for pg in final_pages)


# ---------------------------------------------------------------- driver

def repair(text, doctype, lang, split_col, headers, do_unwrap, notes):
    changes, hints = [], []
    raw_pages = text.split("\f")
    base = 1
    pages = []
    for pg in raw_pages:
        lines = pg.split("\n")
        pages.append([[base + i, ln] for i, ln in enumerate(lines)])
        base += len(lines) - 1
    if lang != "en":
        notes.append(f"language '{lang}': the confusion table is Latin-script only and the compound-prefix list is skipped")

    pages = strip_headers(pages, headers, doctype, changes, notes)
    if split_col:
        pages = split_columns(pages, split_col, changes, notes)
    else:
        for pi, pg in enumerate(pages, 1):
            g = detect_gutter(pg)
            if g:
                first = next((n for n, t in pg if t.strip()), pg[0][0])
                hints.append({"original_line": first, "kind": "column-layout", "token": "",
                              "suggestion": f"--split-columns {g[1]}",
                              "note": f"page {pi} has a blank gutter at characters {g[0]}-{g[1] - 1}; if it is a two-column page the lines are read across the columns"})
    char_repairs(pages, doctype, changes)
    counts = Counts(pages)
    fix_confusables(pages, counts, doctype, changes, hints)
    stats = {"word_types": len(counts.anyc)}
    suspect_columns = any(h["kind"] == "column-layout" for h in hints)
    if doctype == "prose" and not suspect_columns:
        final_pages = reflow(pages, counts, lang, do_unwrap, changes, stats)
    else:
        final_pages = [[(n, n, t) for n, t in pg] for pg in pages]
        why = (f"doctype {doctype}: lines are never joined" if doctype != "prose" else
               "two-column layout suspected: lines not joined until --split-columns is decided")
        stats.update({"line_width": None, "unwrap_applied": False, "unwrap_note": why})
    return changes, hints, final_pages, stats


def build_report(args, text, changes, hints, final_pages, stats, notes, out_path, repaired):
    removed = Counter()
    for c in changes:
        if c["class"] == "header-footer":
            removed.update(NUM_RE.findall(c["before"]))
    before = number_multiset(text) - removed
    after = number_multiset(repaired)
    missing = sorted((before - after).elements())
    added = sorted((after - before).elements())
    scan = suspicious_scan(final_pages)
    # map original line -> repaired line for the hints raised before reflow
    spans = []
    base = 1
    for pg in final_pages:
        for k, (s, e, _t) in enumerate(pg):
            spans.append((s, e, base + k))
        base += len(pg) - 1
    for h in hints:
        h["repaired_line"] = next((r for s, e, r in spans if s <= h["original_line"] <= e), None)
    keys = ("repaired_line", "original_line", "kind", "token", "suggestion", "note")
    suspicious = [{k: h.get(k) for k in keys} for h in hints + scan]
    suspicious.sort(key=lambda h: ((h["repaired_line"] or 0), h["kind"]))
    by_class = Counter(c["class"] for c in changes)
    changes.sort(key=lambda c: (c["line"], c["line_end"], c["class"]))
    by_kind = Counter(h["kind"] for h in suspicious)
    stats.update({
        "pages": len(final_pages),
        "lines_in": text.count("\n") + 1,
        "lines_out": repaired.count("\n") + 1,
        "changes_total": len(changes),
        "changes_by_class": dict(sorted(by_class.items())),
        "suspicious_total": len(suspicious),
        "suspicious_by_kind": dict(sorted(by_kind.items())),
        "suspicious_listed": min(len(suspicious), MAX_SUSPICIOUS),
        "numbers_unchanged": not missing and not added,
        "numbers_missing": missing,
        "numbers_added": added,
        "notes": notes,
    })
    return {
        "tool": "repair_ocr", "version": VERSION, "input": os.path.basename(args.input), "output": out_path,
        "doctype": args.doctype, "lang": args.lang,
        "changes": changes, "suspicious": suspicious[:MAX_SUSPICIOUS], "stats": stats,
    }


def main(argv=None):
    ap = argparse.ArgumentParser(description="Repair OCR text with evidence from the document itself; never overwrites the input.")
    ap.add_argument("input")
    ap.add_argument("--doctype", choices=DOCTYPES, default="prose")
    ap.add_argument("--lang", default="en")
    ap.add_argument("--out")
    ap.add_argument("--report")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--split-columns", type=int, default=0, metavar="CHAR_INDEX")
    ap.add_argument("--headers", choices=("auto", "on", "off"), default="auto")
    ap.add_argument("--no-unwrap", action="store_true")
    args = ap.parse_args(argv)
    try:
        if args.split_columns and args.split_columns < 3:
            raise UsageError("--split-columns must be at least 3")
        notes = []
        out_path = args.out
        if not out_path and not args.dry_run:
            root, ext = os.path.splitext(args.input)
            out_path = root + ".repaired" + (ext or ".txt")
        if not args.dry_run:
            guard_outputs(args.input, out_path, args.report, args.force)
        text = read_text(args.input, notes)
        changes, hints, final_pages, stats = repair(text, args.doctype, args.lang, args.split_columns,
                                                    args.headers, not args.no_unwrap, notes)
        repaired = render(final_pages)
        report = build_report(args, text, changes, hints, final_pages, stats, notes,
                              None if args.dry_run else (os.path.basename(out_path) if out_path else None), repaired)
    except UsageError as exc:
        sys.stderr.write(f"error: {exc}\n")
        return 2
    ok = report["stats"]["numbers_unchanged"]
    if not ok:
        report["output"] = None
        report["stats"]["notes"].append("number check failed; the repaired file was not written")
    payload = json.dumps(report, indent=2, ensure_ascii=True)
    if not args.dry_run and ok:
        write_text(out_path, repaired)
        if args.report:
            write_text(args.report, payload + "\n")
    sys.stdout.write(payload + "\n")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
