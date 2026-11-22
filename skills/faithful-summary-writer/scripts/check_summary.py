#!/usr/bin/env python3
"""Check a summary against its single source and print strict JSON.

    python scripts/check_summary.py SOURCE.txt SUMMARY.txt [--target executive|standard|detailed|RATIO]
                                    [--tolerance 0.01]

Reads the two files (UTF-8). Writes nothing, uses no network. Exit codes:
0 = no mechanical failure found, 1 = at least one failure (see "ok"),
2 = usage problem (missing, unreadable or empty file, bad option).

What it finds (mechanical failures only; it cannot prove a summary faithful):
  - summary sentences with no supporting span in the source (token overlap),
  - numbers, percentages, currency amounts, years and capitalised names in the
    summary that are absent from the source,
  - numbers that are close to a source number but are not a legitimate rounding,
  - negation present in the summary but not in the matching source sentence
    (or the reverse), and hedges ("may", "suggests") dropped from it,
  - compression ratio against the target band,
  - coverage of source headings and of the most frequent source keywords,
  - runs of 16 or more consecutive words copied verbatim from the source.
"""
import argparse
import json
import math
import re
import sys

VERSION = "0.1.0"

# A summary sentence counts as supported when this share of its content words
# (stemmed, stop words removed) appears inside the best window of 1 to 3
# adjacent source sentences. 0.6 leaves room for paraphrase; below 0.4 almost
# nothing is shared. Working values, not measured optima.
SUPPORT_OK = 0.6
SUPPORT_WEAK = 0.4
# Longest source window (in sentences) a summary sentence may draw on.
MAX_WINDOW = 3
# Fewer content words than this and a sentence is a label or fragment: not scored.
MIN_CONTENT_WORDS = 3
# A well-overlapping sentence of at least this many content words that shares
# almost no adjacent word pairs with its window is downgraded to "weak": its
# words are scattered across the source rather than said there.
BIGRAM_FLOOR = 0.1
BIGRAM_MIN_WORDS = 6
# Verbatim copy: 16 or more consecutive words ("over 15").
COPY_MIN_WORDS = 16
# A summary number within this relative distance of a source number is treated
# as an alteration candidate rather than an invented figure. Years: 5 years.
ALTER_WINDOW = 0.25
# Rounding to fewer significant digits is only accepted from a source figure with at least this many.
ROUND_MIN_SOURCE_SIG = 3
# Score-like pairs ("5-4", "21:18"): the same two numbers in the opposite order are a flipped result.
PAIR_RE = re.compile(r"(?<![\d.,/:-])(\d+)\s*[-–—:]\s*(\d+)(?![\d]|\s*[-–—:]\s*\d)")
YEAR_WINDOW = 5
# Shared content words needed before a negation or hedge comparison is trusted.
MIN_SHARED_FOR_POLARITY = 3
# Coverage: number of keywords, minimum count, and the share of a heading's
# content words that must appear in the summary to call the heading covered.
KEYWORD_COUNT = 10
KEYWORD_MIN_FREQ = 2
HEADING_COVER = 0.5
# Sources shorter than this give unreliable ratio bands.
SHORT_SOURCE_WORDS = 300

# Target bands as (low, high) share of source words.
TARGETS = {
    "executive": (0.03, 0.07),
    "standard": (0.10, 0.15),
    "detailed": (0.20, 0.30),
}
NUMERIC_TARGET_SPREAD = 0.4  # a numeric target r means the band r*0.6 .. r*1.4

STOP = set("""a about above after again against all also am an and any are as at be because been before being
below between both but by can could did do does doing down during each few for from further had has have having
he her here hers him his how i if in into is it its itself just me more most my no nor not of off on once only or
other our out over own same she should so some such than that the their them then there these they this those
through to too under until up very was we were what when where which while who whom why will with would you your
said says say also one two""".split())

ABBR = {"mr", "mrs", "ms", "dr", "prof", "sr", "jr", "st", "vs", "etc", "inc", "ltd", "co", "corp", "no",
        "approx", "fig", "eg", "ie", "e.g", "i.e", "u.s", "u.k", "jan", "feb", "mar", "apr", "jun", "jul",
        "aug", "sep", "sept", "oct", "nov", "dec"}

MONTHS = {"january", "february", "march", "april", "may", "june", "july", "august", "september",
          "october", "november", "december", "jan", "feb", "mar", "apr", "jun", "jul", "aug", "sep",
          "sept", "oct", "nov", "dec"}
WEEKDAYS = {"monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"}

NEGATORS = {"not", "no", "never", "none", "neither", "nor", "cannot", "without"}
HEDGES = {"may", "might", "could", "possibly", "possible", "perhaps", "probably", "likely", "unlikely",
          "suggest", "suggests", "suggested", "appear", "appears", "appeared", "seem", "seems", "seemed",
          "seemingly", "reportedly", "allegedly", "approximately", "roughly", "estimated", "potentially",
          "tend", "tends", "probable"}

NUMBER_WORDS = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8,
                "nine": 9, "ten": 10, "eleven": 11, "twelve": 12, "thirteen": 13, "fourteen": 14,
                "fifteen": 15, "sixteen": 16, "seventeen": 17, "eighteen": 18, "nineteen": 19,
                "twenty": 20, "thirty": 30, "forty": 40, "fifty": 50, "sixty": 60, "seventy": 70,
                "eighty": 80, "ninety": 90, "hundred": 100}

MULTIPLIERS = {"thousand": 1e3, "k": 1e3, "million": 1e6, "m": 1e6, "billion": 1e9, "bn": 1e9,
               "trillion": 1e12}

TOKEN_RE = re.compile(r"\d+(?:[.,]\d+)*|[^\W_]+(?:['’][^\W_]+)*")
WORD_RE = re.compile(r"[^\W\d_][\w'’-]*")
NUM_RE = re.compile(
    r"(?<![A-Za-z0-9.,])(?P<cur>[$€£])?\s?"
    r"(?P<num>\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?)"
    r"(?P<suf>%|\s?(?:percent|per\s?cent|million|billion|trillion|thousand|bn)\b|[kKmM]\b)?",
    re.IGNORECASE)
BOUNDARY_RE = re.compile(r"[.!?]+[\"')\]”]*\s+")
BULLET_RE = re.compile(r"^\s*(?:[-*•]|\d+[.)])\s+")
HEADING_RE = re.compile(r"^\s{0,3}#{1,6}\s+")


class UsageError(Exception):
    pass


def read_text(path, label):
    try:
        with open(path, "rb") as fh:
            raw = fh.read()
    except OSError as exc:
        raise UsageError(f"cannot read {label} file '{path}': {exc.strerror or exc}")
    text = raw.decode("utf-8-sig", errors="replace")
    if not text.strip():
        raise UsageError(f"{label} file '{path}' is empty; put the text to check in it")
    return text


def clean_markup(line):
    return line.replace("**", "").replace("__", "").replace("`", "")


def to_units(text):
    """Split text into units (paragraphs, bullets, headings) with start line numbers."""
    units = []
    para = []
    para_line = 0

    def flush():
        nonlocal para
        if para:
            joined = " ".join(p.strip() for p in para)
            units.append({"line": para_line, "text": clean_markup(joined), "kind": "para", "raw": para[:]})
            para = []

    for n, line in enumerate(text.splitlines(), start=1):
        if not line.strip():
            flush()
        elif HEADING_RE.match(line):
            flush()
            units.append({"line": n, "text": clean_markup(HEADING_RE.sub("", line)).strip(), "kind": "heading", "raw": [line]})
        elif BULLET_RE.match(line):
            flush()
            units.append({"line": n, "text": clean_markup(BULLET_RE.sub("", line)).strip(), "kind": "bullet", "raw": [line]})
        else:
            if not para:
                para_line = n
            para.append(line)
    flush()
    return units


def split_sentences(text):
    out = []
    start = 0
    for m in BOUNDARY_RE.finditer(text):
        before = text[start:m.start()]
        if not before.strip():
            continue
        last = before.rsplit(None, 1)[-1].lstrip("\"'([“").lower()
        if last in ABBR or re.fullmatch(r"[a-z]", last) or re.fullmatch(r"(?:[a-z]\.)+[a-z]", last):
            continue
        nxt = text[m.end():m.end() + 1]
        if nxt and not (nxt.isupper() or nxt.isdigit() or nxt in "\"'([“"):
            continue
        out.append(text[start:m.end()].strip())
        start = m.end()
    tail = text[start:].strip()
    if tail:
        out.append(tail)
    return out


def tokens(text):
    return [t.lower() for t in TOKEN_RE.findall(text)]


def stem(word):
    w = word.lower().replace("’", "'")
    if w.endswith("'s"):
        w = w[:-2]
    if re.fullmatch(r"[\d.,]+", w):
        return w
    if w.endswith("ies") and len(w) > 4:
        return w[:-3] + "y"
    for suf in ("ing", "ed", "es", "s", "ly"):
        if w.endswith(suf) and len(w) - len(suf) >= 3:
            w = w[:-len(suf)]
            break
    if w.endswith("e") and len(w) > 3:
        w = w[:-1]
    return w


def content_seq(text):
    return [stem(t) for t in tokens(text) if t not in STOP]


def build_sentences(units, include_headings=False):
    sents = []
    for u in units:
        if u["kind"] == "heading" and not include_headings:
            continue
        for s in split_sentences(u["text"]):
            seq = content_seq(s)
            sents.append({
                "idx": len(sents) + 1, "line": u["line"], "text": s, "seq": seq,
                "set": frozenset(seq), "bigrams": frozenset(zip(seq, seq[1:])),
                "raw_tokens": tokens(s),
            })
    return sents


def extract_numbers(text):
    found = []
    for m in NUM_RE.finditer(text):
        num = m.group("num")
        suf = (m.group("suf") or "").strip().lower().replace(" ", "")
        cur = m.group("cur")
        value = float(num.replace(",", ""))
        kind = "number"
        if suf in ("%", "percent"):
            kind = "percent"
        elif suf in MULTIPLIERS:
            value *= MULTIPLIERS[suf]
        if cur:
            kind = "currency"
        elif kind == "number" and not suf and re.fullmatch(r"(19|20)\d\d", num):
            kind = "year"
        found.append({"text": m.group(0).strip(), "value": value, "kind": kind, "mantissa": num})
    return found


def sig_digits(mantissa):
    digits = mantissa.replace(",", "")
    if "." in digits:
        digits = digits.replace(".", "").lstrip("0")
    else:
        digits = digits.lstrip("0").rstrip("0")
    return max(1, len(digits))


def round_sig(value, k):
    if value == 0:
        return 0.0
    places = k - 1 - int(math.floor(math.log10(abs(value))))
    return round(value, places)


def same(a, b):
    return abs(a - b) <= 1e-9 * max(1.0, abs(b))


def source_number_pool(source_text):
    pool = extract_numbers(source_text)
    for tok in tokens(source_text):
        if tok in NUMBER_WORDS:
            v = float(NUMBER_WORDS[tok])
            pool.append({"text": tok, "value": v, "kind": "number", "mantissa": str(int(v))})
    return pool


def judge_number(item, pool, tolerance):
    """Return ('ok', None) | ('altered', src) | ('unsupported', None)."""
    s = item["value"]
    for n in pool:
        if same(s, n["value"]):
            return "ok", None
    k = sig_digits(item["mantissa"])
    for n in pool:
        nv = n["value"]
        if nv and abs(s - nv) / abs(nv) <= tolerance:
            return "ok", None
        # Rounding is only accepted for a source figure of the same kind with at least
        # ROUND_MIN_SOURCE_SIG significant digits, rounded to fewer digits (38,832 -> 39,000).
        # So 18 months never becomes "20 cities" and 5 never becomes "4".
        if (item["kind"] != "year" and n["kind"] == item["kind"] and k < sig_digits(n["mantissa"])
                and sig_digits(n["mantissa"]) >= ROUND_MIN_SOURCE_SIG and same(round_sig(nv, k), s)):
            return "ok", None
    best = None
    for n in pool:
        nv = n["value"]
        if item["kind"] == "year":
            if n["kind"] == "year" and abs(s - nv) <= YEAR_WINDOW:
                d = abs(s - nv)
                if best is None or d < best[0]:
                    best = (d, n)
        elif nv and abs(s - nv) / abs(nv) <= ALTER_WINDOW:
            d = abs(s - nv) / abs(nv)
            if best is None or d < best[0]:
                best = (d, n)
    if best:
        return "altered", best
    return "unsupported", None


def cap_phrases(sentence):
    """Yield (phrase_text, [tokens], at_start) for runs of capitalised words."""
    toks = [(m.group(0), m.start(), m.end()) for m in WORD_RE.finditer(sentence)]
    phrases = []
    cur = []
    for i, (w, s, e) in enumerate(toks):
        if w[0].isupper():
            if cur and sentence[cur[-1][2]:s] == " ":
                cur.append((w, s, e, i))
            else:
                if cur:
                    phrases.append(cur)
                cur = [(w, s, e, i)]
        else:
            if cur:
                phrases.append(cur)
            cur = []
    if cur:
        phrases.append(cur)
    result = []
    for ph in phrases:
        words = [p[0] for p in ph]
        result.append((" ".join(words), words, ph[0][3] == 0))
    return result


def name_checks(sentence, src_words, src_stems):
    """Return list of (kind, text) for capitalised names absent from the source."""
    out = []

    def present(w):
        lw = w.lower().replace("’", "'")
        if lw.endswith("'s"):
            lw = lw[:-2]
        return lw in src_words or stem(lw) in src_stems

    for text, words, at_start in cap_phrases(sentence):
        parts = words
        if at_start:
            first = parts[0]
            if len(parts) == 1:
                if not (first.isupper() and len(first) >= 2):
                    continue
            elif first.lower() in STOP or present(first):
                parts = parts[1:]
        missing = []
        for w in parts:
            if w.lower() in STOP:
                continue
            if not present(w):
                missing.append(w)
        if missing:
            kind = "date" if any(w.lower() in MONTHS or w.lower() in WEEKDAYS for w in missing) else "name"
            out.append((kind, text if len(parts) == len(words) else " ".join(parts)))
    return out


def find_window(sent, src):
    """Best window of 1..MAX_WINDOW adjacent source sentences; plus best single sentence."""
    S = sent["set"]
    B = sent["bigrams"]
    best = (-1.0, 0, 0, 0.0)  # score, start, size, bigram overlap
    single = (-1, 0, 0.0)     # shared count, index, score
    n = len(src)
    for i in range(n):
        u = set()
        ub = set()
        for w in range(1, MAX_WINDOW + 1):
            if i + w > n:
                break
            u |= src[i + w - 1]["set"]
            ub |= src[i + w - 1]["bigrams"]
            shared = len(S & u)
            score = shared / len(S)
            if w == 1 and shared > single[0]:
                single = (shared, i, score)
            if score > best[0] + 1e-12:
                bo = (len(B & ub) / len(B)) if B else 0.0
                best = (score, i, w, bo)
    return best, single


def copied_spans(src_tokens, sum_sentences):
    n = COPY_MIN_WORDS
    index = {}
    for i in range(len(src_tokens) - n + 1):
        index.setdefault(tuple(src_tokens[i:i + n]), []).append(i)
    spans = []
    for sent in sum_sentences:
        toks = sent["raw_tokens"]
        i = 0
        while i <= len(toks) - n:
            key = tuple(toks[i:i + n])
            starts = index.get(key)
            if not starts:
                i += 1
                continue
            best_len = 0
            for p in starts:
                length = n
                while i + length < len(toks) and p + length < len(src_tokens) and toks[i + length] == src_tokens[p + length]:
                    length += 1
                best_len = max(best_len, length)
            spans.append({"sentence": sent["idx"], "words": best_len, "text": " ".join(toks[i:i + best_len])})
            i += best_len
    return spans


def coverage(src_units, src_sents, summary_stems):
    heads = []
    for k, u in enumerate(src_units):
        is_head = u["kind"] == "heading"
        if not is_head and u["kind"] == "para" and len(u["raw"]) == 1:
            t = u["text"]
            wc = len(t.split())
            nxt_ok = k + 1 < len(src_units)
            if 1 <= wc <= 10 and not re.search(r"[.!?;,:]$", t) and (t[:1].isupper() or t[:1].isdigit()) and nxt_ok:
                is_head = True
        if is_head:
            heads.append(u["text"])
    missing_heads = []
    total_heads = 0
    for h in heads:
        stems = set(content_seq(h))
        if not stems:
            continue
        total_heads += 1
        if len(stems & summary_stems) / len(stems) < HEADING_COVER:
            missing_heads.append(h)
    counts = {}
    surface = {}
    for s in src_sents:
        for tok in tokens(s["text"]):
            if tok in STOP or re.search(r"\d", tok) or len(tok) < 4:
                continue
            st = stem(tok)
            counts[st] = counts.get(st, 0) + 1
            surface.setdefault(st, {}).setdefault(tok, 0)
            surface[st][tok] += 1
    ranked = sorted(((c, st) for st, c in counts.items() if c >= KEYWORD_MIN_FREQ), key=lambda x: (-x[0], x[1]))[:KEYWORD_COUNT]
    kw_missing = []
    for c, st in ranked:
        if st not in summary_stems:
            forms = surface[st]
            kw_missing.append(sorted(forms, key=lambda f: (-forms[f], f))[0])
    return {
        "headings_total": total_heads, "headings_covered": total_heads - len(missing_heads),
        "headings_missing": missing_heads,
        "keywords_total": len(ranked), "keywords_covered": len(ranked) - len(kw_missing),
        "keywords_missing": kw_missing,
        "keyword_coverage": round((len(ranked) - len(kw_missing)) / len(ranked), 3) if ranked else None,
    }


def trim(text, limit=240):
    return text if len(text) <= limit else text[:limit - 3] + "..."


def has_negation(sent):
    for t in sent["raw_tokens"]:
        if t in NEGATORS or t.endswith("n't") or t.endswith("n’t"):
            return True
    return False


def has_hedge(sent):
    return any(t in HEDGES for t in sent["raw_tokens"])


def resolve_target(value):
    if value in TARGETS:
        lo, hi = TARGETS[value]
        return value, lo, hi
    try:
        r = float(value)
    except ValueError:
        raise UsageError("--target must be executive, standard, detailed or a ratio such as 0.1")
    if not 0 < r < 1:
        raise UsageError("--target ratio must be between 0 and 1 (for example 0.1 for 10 percent)")
    return str(r), round(r * (1 - NUMERIC_TARGET_SPREAD), 4), round(r * (1 + NUMERIC_TARGET_SPREAD), 4)


def check(source_text, summary_text, target, tolerance):
    t_name, t_low, t_high = resolve_target(target)
    src_units = to_units(source_text)
    sum_units = to_units(summary_text)
    src = build_sentences(src_units)
    summ = build_sentences(sum_units)
    if not src:
        raise UsageError("source has no sentences to compare against")
    if not summ:
        raise UsageError("summary has no sentences; a heading-only summary cannot be checked")

    src_tokens = tokens(source_text)
    src_words = set(src_tokens)
    src_stems = {stem(t) for t in src_tokens}
    sum_stems = {stem(t) for t in tokens(summary_text)}
    pool = source_number_pool(source_text)

    source_words = len(src_tokens)
    summary_words = len(tokens(summary_text))
    ratio = round(summary_words / source_words, 4) if source_words else 0.0
    status = "within" if t_low <= ratio <= t_high else ("too_long" if ratio > t_high else "too_short")

    sent_flags = []
    counts = {"supported": 0, "weak": 0, "unsupported": 0}
    scored = 0
    negation_flips = []
    hedge_drops = []
    for s in summ:
        if len(s["set"]) < MIN_CONTENT_WORDS:
            continue
        scored += 1
        (score, start, size, bo), (shared, si, _) = find_window(s, src)
        state = "supported"
        if score < SUPPORT_WEAK:
            state = "unsupported"
        elif score < SUPPORT_OK:
            state = "weak"
        elif bo < BIGRAM_FLOOR and len(s["set"]) >= BIGRAM_MIN_WORDS:
            state = "weak"
        counts[state] += 1
        if state != "supported":
            sent_flags.append({"sentence": s["idx"], "status": state, "score": round(score, 3),
                               "text": trim(s["text"]), "best_source_line": src[start]["line"]})
        if shared >= MIN_SHARED_FOR_POLARITY:
            ref = src[si]
            if has_negation(s) != has_negation(ref):
                negation_flips.append({"sentence": s["idx"], "summary": trim(s["text"]),
                                       "summary_negated": has_negation(s), "source_line": ref["line"],
                                       "source": trim(ref["text"])})
            if has_hedge(ref) and not has_hedge(s):
                hedge_drops.append({"sentence": s["idx"], "summary": trim(s["text"]),
                                    "source_line": ref["line"], "source": trim(ref["text"])})

    src_pairs = {(m.group(1), m.group(2)) for m in PAIR_RE.finditer(source_text)}
    details = {}
    altered = []
    for s in summ:
        for item in extract_numbers(s["text"]):
            verdict, best = judge_number(item, pool, tolerance)
            if verdict == "unsupported":
                key = (item["kind"], item["text"])
                details.setdefault(key, {"kind": item["kind"], "text": item["text"], "sentence": s["idx"], "count": 0})["count"] += 1
            elif verdict == "altered":
                d, n = best
                altered.append({"sentence": s["idx"], "summary": item["text"], "source": n["text"],
                                "relative_difference": round(d, 4) if item["kind"] != "year" else None,
                                "difference": d if item["kind"] == "year" else None})
        for m in PAIR_RE.finditer(s["text"]):
            a, b = m.group(1), m.group(2)
            if a != b and (a, b) not in src_pairs and (b, a) in src_pairs:
                altered.append({"sentence": s["idx"], "summary": m.group(0).strip(), "source": f"{b}-{a}",
                                "relative_difference": None, "difference": None, "reason": "pair_order_reversed"})
        for kind, text in name_checks(s["text"], src_words, src_stems):
            key = (kind, text)
            details.setdefault(key, {"kind": kind, "text": text, "sentence": s["idx"], "count": 0})["count"] += 1

    spans = copied_spans(src_tokens, summ)
    cov = coverage(src_units, src, sum_stems)

    warnings = []
    if source_words < SHORT_SOURCE_WORDS:
        warnings.append(f"source is under {SHORT_SOURCE_WORDS} words; ratio bands are unreliable for short sources")
    if status != "within":
        warnings.append(f"ratio {ratio} is {status.replace('_', ' ')} for target {t_name} ({t_low} to {t_high})")
    if spans:
        warnings.append(f"{len(spans)} span(s) of {COPY_MIN_WORDS}+ words copied verbatim; paraphrase or quote and attribute")
    if hedge_drops:
        warnings.append(f"{len(hedge_drops)} sentence(s) dropped a hedge present in the matching source sentence")
    if counts["weak"]:
        warnings.append(f"{counts['weak']} sentence(s) only weakly supported; check each against the source by hand")

    ok = not (counts["unsupported"] or details or altered or negation_flips)
    return {
        "tool": "check_summary", "version": VERSION, "ok": ok,
        "source_words": source_words, "summary_words": summary_words, "ratio": ratio,
        "target": {"name": t_name, "low": t_low, "high": t_high, "status": status},
        "sentences": {"total": len(summ), "scored": scored, "supported": counts["supported"],
                      "weak": counts["weak"], "unsupported": counts["unsupported"]},
        "unsupported_sentences": sent_flags,
        "unsupported": list(details.values()),
        "altered_numbers": altered,
        "negation_flips": negation_flips,
        "hedge_drops": hedge_drops,
        "copied_spans": spans,
        "coverage": cov,
        "warnings": warnings,
        "limits": "Mechanical checks only: token overlap and surface forms. Passing does not prove the summary is faithful.",
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description="Check a summary against its source; prints JSON.")
    parser.add_argument("source")
    parser.add_argument("summary")
    parser.add_argument("--target", default="standard")
    parser.add_argument("--tolerance", type=float, default=0.01,
                        help="relative difference below which a changed number counts as rounding (default 0.01)")
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        return exc.code if isinstance(exc.code, int) else 2
    try:
        if not 0 <= args.tolerance < ALTER_WINDOW:
            raise UsageError(f"--tolerance must be at least 0 and below {ALTER_WINDOW}")
        report = check(read_text(args.source, "source"), read_text(args.summary, "summary"), args.target, args.tolerance)
    except UsageError as exc:
        print(f"check_summary: {exc}", file=sys.stderr)
        return 2
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except (OSError, ValueError):
            pass
    print(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
