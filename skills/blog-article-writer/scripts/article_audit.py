#!/usr/bin/env python3
"""Audit a Markdown blog article, or the brief it was written from.

    python article_audit.py audit <article.md> [--site-host example.com]
                            [--min-internal-links N] [--brief brief.md]
    python article_audit.py brief <brief.md>

Reads the files it is given. Writes nothing. Prints exactly one JSON object to
stdout and nothing else. Errors are also JSON (an "error" key) plus one plain
sentence on stderr.

Exit codes
    0  verdict "pass" or "review" (no error-level finding)
    1  verdict "fix" (at least one error-level finding)
    2  usage error, unreadable file, or empty file

JSON contract, `audit` (schema_version 1; every key is always present)
    {"schema_version": 1, "command": "audit", "file": str, "words": int,
     "title": str|null, "h2_count": int, "intro_words": int,
     "sections": [{"heading": str, "line": int, "words": int,
                   "example_signals": [str]}],
     "reading": {"sentences": int, "mean_words": float, "median_words": float,
                 "p90_words": float, "stdev_words": float,
                 "share_over_30": float, "share_under_9": float,
                 "grade_proxy": float},
     "links": {"internal": int, "external": int, "internal_required": int},
     "brief_checked": bool,
     "findings": [{"severity": "error"|"warning", "rule": str, "line": int,
                   "message": str, "match": str}],
     "counts": {"error": int, "warning": int},
     "verdict": "pass" | "review" | "fix"}

JSON contract, `brief` (schema_version 1)
    {"schema_version": 1, "command": "brief", "file": str,
     "fields": {"audience": int, "promise": int, "angle": int,
                "not_covered": int},          # word counts, 0 = missing
     "claim_rows": int, "claim_rows_with_url": int,
     "findings": [...same shape as above...], "counts": {...}, "verdict": str}

Everything here is a surface measurement. Thresholds are working values chosen
for blog articles of roughly 800 to 2,500 words; they are not measured optima.
The script cannot judge whether a claim is true or an example is good.
"""
import json
import math
import re
import statistics
import sys

SCHEMA_VERSION = 1

# --- thresholds (working values; each has a reason) ---------------------------
INTRO_MAX_WORDS = 120      # reader decides to stay within the first screen
SECTION_MIN_WORDS = 80     # below this an H2 is a label, not a section
SECTION_MAX_WORDS = 450    # above this an H2 almost always holds two ideas
H2_MIN, H2_MAX = 3, 10     # fewer: not an article; more: a list in disguise
H1_MAX_CHARS = 70          # longer titles are cut in search results
MEAN_SENTENCE_MAX = 22     # mean words per sentence above this tires readers
SHARE_OVER_30_MAX = 0.10   # more than 10% very long sentences
STDEV_MIN = 5.0            # below this with 12+ sentences the rhythm is monotone
MIN_SENTENCES_FOR_RHYTHM = 12
GRADE_MAX = 12.0           # grade proxy above this is hard for a general audience
INTERNAL_PER_WORDS = 500   # one internal link per 500 words ...
INTERNAL_FLOOR = 2         # ... and never fewer than 2
BRIEF_MIN_CLAIM_ROWS = 3
BRIEF_PROMISE_WORDS = (8, 35)
BRIEF_MIN_WORDS = {"audience": 5, "angle": 8, "not_covered": 3}

# --- patterns -------------------------------------------------------------------
OPENER_RULES = [
    ("era-opener", r"\bin today'?s (?:fast[- ]paced|digital|modern|ever[- ]changing|competitive|connected|world|age|landscape|society|business)"),
    ("ever-evolving", r"\bin (?:the|an) (?:ever[- ](?:changing|evolving)|digital age|age of|era of|modern world)"),
    ("realm-of", r"\bin the (?:realm|world|landscape|field) of\b"),
    ("dawn-of-time", r"\b(?:since|from) the dawn of\b"),
    ("rhetorical-wonder", r"\bhave you ever (?:wondered|asked yourself|thought about|noticed)\b"),
    ("are-you-looking", r"\bare you (?:looking|struggling|tired|ready|wondering|searching)\b"),
    ("when-it-comes-to", r"\bwhen it comes to\b"),
    ("this-article-will", r"\b(?:in this|this) (?:article|post|blog post|guide),? (?:we|i|you)(?:'ll| will| are going to|'re going to)?\b"),
    ("welcome-to", r"\bwelcome to\b"),
    ("lets-dive", r"\blet'?s (?:dive|delve|explore|jump|unpack|take a (?:look|closer look))\b"),
    ("goes-without-saying", r"\bit goes without saying\b"),
    ("whether-you-are", r"\bwhether you(?:'re| are) an? [^,.]{1,40}? or an?\b"),
    ("in-recent-years", r"\bin recent years\b"),
    ("more-than-ever", r"\bmore (?:important|relevant|crucial|popular) than ever\b"),
    ("unlock-power", r"\bunlock(?:ing)? the (?:power|secrets?|potential)\b"),
    ("stock-phrase", r"\b(?:game[- ]changer|rich tapestry|delve into|ultimate guide to|navigate the (?:complex|complexities))\b"),
]
CLOSER_RULES = [
    ("closer", r"\b(?:in conclusion|to sum up|to summari[sz]e|all in all|at the end of the day)\b"),
]
GENERIC_H2 = {"introduction", "intro", "overview", "conclusion", "final thoughts",
              "summary", "wrapping up", "getting started", "background", "faq"}
EXAMPLE_PHRASES = ["for example", "for instance", "e.g.", "such as", "imagine ",
                   "say you", "suppose ", "consider ", "in one case", "one team",
                   "one client", "step 1", "here is what", "here's what"]
UNIT_WORDS = (r"ms|seconds?|minutes?|hours?|days?|weeks?|months?|years?|kb|mb|gb|"
              r"people|users?|customers?|companies|respondents|studies|participants|"
              r"employees|pages|sites|words|times|fold|x")
NUMBER_CLAIM = re.compile(
    r"(?:[$€£]\s?\d[\d,]*(?:\.\d+)?(?:\s?(?:k|m|bn|million|billion))?)"
    r"|(?:\b\d[\d,]*(?:\.\d+)?\s?(?:%|percent\b))"
    r"|(?:\b\d+(?:\.\d+)?\s?(?:million|billion|thousand)\b)"
    r"|(?:\b\d{1,3}(?:,\d{3})+\b)"
    r"|(?:\b\d+\s+(?:out of|in)\s+\d+\b)"
    r"|(?:\b\d+(?:\.\d+)?\s?(?:" + UNIT_WORDS + r")\b)",
    re.IGNORECASE)
LINK_RE = re.compile(r"(?<!!)\[([^\]]*)\]\(([^)\s]+)[^)]*\)")
FOOTNOTE_RE = re.compile(r"\[\^[^\]]+\]|\[\d{1,3}\]")
ABBREV = ["e.g.", "i.e.", "vs.", "etc.", "dr.", "mr.", "mrs.", "ms.", "st.", "no.", "approx."]
PLACEHOLDER_RE = re.compile(r"\b(?:tbd|todo|lorem ipsum|fill in|xxx)\b|<[^>]*>|\.\.\.$", re.IGNORECASE)


def die(command, message, file=None):
    sys.stderr.write(message + "\n")
    print(json.dumps({"schema_version": SCHEMA_VERSION, "command": command,
                      "file": file, "error": message}, ensure_ascii=False))
    sys.exit(2)


def read_text(command, path):
    try:
        with open(path, "r", encoding="utf-8-sig") as fh:
            text = fh.read()
    except (OSError, UnicodeDecodeError) as exc:
        die(command, "Cannot read '%s' as UTF-8 text (%s). Check the path and encoding." % (path, exc.__class__.__name__), path)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    if not text.strip():
        die(command, "File '%s' is empty. Give it the article or brief text." % path, path)
    return text


def blank_comments(text):
    return re.sub(r"<!--.*?-->", lambda m: re.sub(r"[^\n]", "", m.group(0)), text, flags=re.DOTALL)


def split_front_matter(text):
    """Return (front_matter_dict_of_title, body_text, line_offset)."""
    lines = text.split("\n")
    if lines and lines[0].strip() == "---":
        for i in range(1, len(lines)):
            if lines[i].strip() == "---":
                title = None
                for fl in lines[1:i]:
                    m = re.match(r"\s*title\s*:\s*(.+?)\s*$", fl, re.IGNORECASE)
                    if m:
                        title = m.group(1).strip("\"'")
                return title, "\n".join([""] * (i + 1) + lines[i + 1:]), 0
    return None, text, 0


def plain(text):
    text = re.sub(r"!\[[^\]]*\]\([^)]*\)", " ", text)
    text = LINK_RE.sub(lambda m: m.group(1), text)
    text = re.sub(r"https?://\S+", " ", text)
    text = re.sub(r"[`*_>#|]", " ", text)
    return text


def words_of(text):
    return re.findall(r"[A-Za-z0-9][A-Za-z0-9'\u2019\-]*", plain(text))


def sentences_of(text):
    t = text
    for ab in ABBREV:
        t = re.sub(re.escape(ab), ab.replace(".", "\u0001"), t, flags=re.IGNORECASE)
    parts = re.split(r"(?<=[.!?])[\"')\]]*\s+(?=[A-Z0-9\"\u201c\u2018(\[])", t)
    return [p.replace("\u0001", ".").strip() for p in parts if p.strip()]


def syllables(word):
    w = re.sub(r"[^a-z]", "", word.lower())
    if not w:
        return 1
    groups = re.findall(r"[aeiouy]+", w)
    n = len(groups)
    if w.endswith("e") and not w.endswith(("le", "ee")) and n > 1:
        n -= 1
    return max(n, 1)


def percentile(values, p):
    if not values:
        return 0.0
    s = sorted(values)
    k = (len(s) - 1) * p
    lo, hi = math.floor(k), math.ceil(k)
    return s[lo] + (s[hi] - s[lo]) * (k - lo)


def parse_units(text):
    """Split into headings and text units with line numbers and a kind."""
    units, fence, para = [], None, None
    lines = text.split("\n")

    def flush():
        nonlocal para
        if para:
            units.append(para)
            para = None

    for idx, raw in enumerate(lines, 1):
        line = raw.rstrip()
        fm = re.match(r"^\s*(```|~~~)", line)
        if fence:
            if fm and fm.group(1) == fence:
                fence = None
            continue
        if fm:
            flush()
            fence = fm.group(1)
            units.append({"kind": "code", "line": idx, "text": ""})
            continue
        if not line.strip():
            flush()
            continue
        hm = re.match(r"^(#{1,6})\s+(.*?)\s*#*\s*$", line)
        if hm:
            flush()
            units.append({"kind": "heading", "line": idx, "level": len(hm.group(1)), "text": hm.group(2)})
            continue
        if re.match(r"^\s*\|", line):
            flush()
            if re.match(r"^\s*\|?[\s:\-|]+\|?\s*$", line):
                continue
            units.append({"kind": "table", "line": idx, "text": line})
            continue
        if re.match(r"^\s*(?:[-*+]|\d+[.)])\s+", line):
            flush()
            para = {"kind": "list", "line": idx, "text": re.sub(r"^\s*(?:[-*+]|\d+[.)])\s+", "", line)}
            continue
        if line.lstrip().startswith(">"):
            flush()
            units.append({"kind": "quote", "line": idx, "text": line.lstrip("> ")})
            continue
        if para:
            para["text"] += " " + line.strip()
        else:
            para = {"kind": "para", "line": idx, "text": line.strip()}
    flush()
    return units


def finding(findings, severity, rule, line, message, match=""):
    findings.append({"severity": severity, "rule": rule, "line": line,
                     "message": message, "match": match[:160]})


def finish(command, path, findings, extra):
    findings.sort(key=lambda f: (f["line"], f["rule"], f["match"]))
    counts = {"error": sum(f["severity"] == "error" for f in findings),
              "warning": sum(f["severity"] == "warning" for f in findings)}
    verdict = "fix" if counts["error"] else ("review" if counts["warning"] else "pass")
    out = {"schema_version": SCHEMA_VERSION, "command": command, "file": path}
    out.update(extra)
    out.update({"findings": findings, "counts": counts, "verdict": verdict})
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 1 if verdict == "fix" else 0


def is_internal(target, site_host):
    if target.startswith("#") or target.startswith("mailto:"):
        return False
    m = re.match(r"^[a-z][a-z0-9+.\-]*://([^/:?#]+)", target, re.IGNORECASE)
    if not m:
        return True  # relative or root-relative path
    host = m.group(1).lower()
    host = host[4:] if host.startswith("www.") else host
    return bool(site_host) and host == site_host


def audit(path, site_host, min_internal, brief_path):
    raw = read_text("audit", path)
    title_fm, body, _ = split_front_matter(blank_comments(raw))
    units = parse_units(body)
    findings = []

    # --- headings ---
    headings = [u for u in units if u["kind"] == "heading"]
    h1s = [h for h in headings if h["level"] == 1]
    title = h1s[0]["text"] if h1s else title_fm
    if len(h1s) + (1 if title_fm and not h1s else 0) != 1:
        finding(findings, "error", "h1-count", h1s[1]["line"] if len(h1s) > 1 else 1,
                "The article needs exactly one H1 (or a front-matter title); found %d." % len(h1s))
    if title and len(title) > H1_MAX_CHARS:
        finding(findings, "warning", "title-long", h1s[0]["line"] if h1s else 1,
                "Title is %d characters; keep it at or under %d." % (len(title), H1_MAX_CHARS), title)
    prev = 0
    seen = {}
    for h in headings:
        if prev and h["level"] > prev + 1:
            finding(findings, "error", "heading-skip", h["line"],
                    "Heading jumps from H%d to H%d; add the missing level." % (prev, h["level"]), h["text"])
        prev = h["level"]
        if not h["text"].strip():
            finding(findings, "error", "heading-empty", h["line"], "Empty heading.")
        if h["level"] == 2:
            key = h["text"].strip().lower()
            if key in GENERIC_H2:
                finding(findings, "warning", "heading-generic", h["line"],
                        "Generic H2 '%s' tells the reader nothing; name the idea." % h["text"], h["text"])
            if re.search(r"(?:\s(?:and|&)\s|;)", h["text"]):
                finding(findings, "warning", "heading-two-ideas", h["line"],
                        "H2 joins two things with 'and', '&' or ';'; one idea per H2 means one subject.", h["text"])
            if key in seen:
                finding(findings, "warning", "heading-duplicate", h["line"],
                        "Same H2 text as line %d." % seen[key], h["text"])
            seen.setdefault(key, h["line"])
    h2s = [h for h in headings if h["level"] == 2]
    if len(h2s) < H2_MIN:
        finding(findings, "error", "h2-too-few", h2s[0]["line"] if h2s else 1,
                "Found %d H2 sections; an article needs at least %d." % (len(h2s), H2_MIN))
    elif len(h2s) > H2_MAX:
        finding(findings, "warning", "h2-too-many", h2s[H2_MAX]["line"],
                "Found %d H2 sections; more than %d usually means a list, not an article." % (len(h2s), H2_MAX))

    # --- sections ---
    intro_units, sections, current = [], [], None
    for u in units:
        if u["kind"] == "heading" and u["level"] == 2:
            current = {"heading": u["text"], "line": u["line"], "units": []}
            sections.append(current)
        elif u["kind"] == "heading" and u["level"] == 1:
            continue
        elif current is None:
            intro_units.append(u)
        else:
            current["units"].append(u)
    intro_words = sum(len(words_of(u["text"])) for u in intro_units if u["kind"] != "heading")
    if intro_words == 0:
        finding(findings, "error", "intro-missing", 1, "No text between the title and the first H2.")
    elif intro_words > INTRO_MAX_WORDS:
        finding(findings, "error", "intro-long", intro_units[0]["line"] if intro_units else 1,
                "Intro is %d words; the limit is %d." % (intro_words, INTRO_MAX_WORDS))

    section_out = []
    for s in sections:
        wc = sum(len(words_of(u["text"])) for u in s["units"] if u["kind"] != "code")
        signals = set()
        low = " ".join(u["text"] for u in s["units"]).lower()
        for ph in EXAMPLE_PHRASES:
            if ph in low:
                signals.add("phrase:" + ph.strip())
        for u in s["units"]:
            if u["kind"] == "code":
                signals.add("code-block")
            elif u["kind"] == "table":
                signals.add("table")
            elif u["kind"] == "quote":
                signals.add("quote")
            if u["kind"] != "code" and re.search(r"!\[", u["text"]):
                signals.add("image")
            if u["kind"] != "code" and NUMBER_CLAIM.search(u["text"]):
                signals.add("figure")
        section_out.append({"heading": s["heading"], "line": s["line"], "words": wc,
                            "example_signals": sorted(signals)})
        if wc < SECTION_MIN_WORDS:
            finding(findings, "warning", "section-thin", s["line"],
                    "Section has %d words; under %d it reads as a label." % (wc, SECTION_MIN_WORDS), s["heading"])
        elif wc > SECTION_MAX_WORDS:
            finding(findings, "warning", "section-long", s["line"],
                    "Section has %d words; over %d it usually holds two ideas. Split or cut." % (wc, SECTION_MAX_WORDS), s["heading"])
        if not signals:
            finding(findings, "warning", "section-no-example", s["line"],
                    "No example signal (phrase like 'for example', code, table, quote, image or a figure).", s["heading"])

    # --- generic openers ---
    first_units = {id(intro_units[0])} if intro_units else set()
    for s in sections:
        body_units = [u for u in s["units"] if u["kind"] in ("para", "list")]
        if body_units:
            first_units.add(id(body_units[0]))
    for u in intro_units + [x for s in sections for x in s["units"]]:
        if u["kind"] not in ("para", "list", "quote"):
            continue
        for rule, pat in OPENER_RULES + CLOSER_RULES:
            m = re.search(pat, u["text"], re.IGNORECASE)
            if m:
                high = rule != "closer" and (id(u) in first_units or any(u is x for x in intro_units))
                finding(findings, "error" if high else "warning", "generic-" + rule, u["line"],
                        "Stock phrase%s; say the specific thing instead." % (" in an opening paragraph" if high else ""), m.group(0))

    # --- sentences, reading level, uncited numeric claims ---
    lengths, syl, wtot = [], 0, 0
    claim_hits = []
    for u in units:
        if u["kind"] not in ("para", "list", "quote", "table"):
            continue
        if u["kind"] == "table":
            sents = [u["text"]]
        else:
            sents = sentences_of(u["text"])
        for i, s in enumerate(sents):
            ws = words_of(s)
            if u["kind"] != "table" and ws:
                lengths.append(len(ws))
                wtot += len(ws)
                syl += sum(syllables(w) for w in ws)
            cleaned = re.sub(r"https?://\S+", " ", LINK_RE.sub(lambda m: m.group(1), s))
            m = NUMBER_CLAIM.search(cleaned)
            if not m:
                continue
            nxt = sents[i + 1] if i + 1 < len(sents) else ""
            cited = any(LINK_RE.search(x) or FOOTNOTE_RE.search(x) or re.search(r"https?://", x) for x in (s, nxt))
            if not cited:
                finding(findings, "error", "uncited-number", u["line"],
                        "Numeric claim with no link or footnote in this or the next sentence.", m.group(0))
            claim_hits.append((u["line"], m.group(0)))
    nsent = len(lengths)
    mean = statistics.mean(lengths) if lengths else 0.0
    stdev = statistics.pstdev(lengths) if lengths else 0.0
    over30 = sum(1 for n in lengths if n > 30) / nsent if nsent else 0.0
    under9 = sum(1 for n in lengths if n < 9) / nsent if nsent else 0.0
    grade = (0.39 * (wtot / nsent) + 11.8 * (syl / wtot) - 15.59) if nsent and wtot else 0.0
    if mean > MEAN_SENTENCE_MAX:
        finding(findings, "warning", "sentences-long", 1, "Mean sentence is %.1f words; keep it at or under %d." % (mean, MEAN_SENTENCE_MAX))
    if nsent and over30 > SHARE_OVER_30_MAX:
        finding(findings, "warning", "sentences-very-long", 1, "%.0f%% of sentences exceed 30 words; keep it at or under %.0f%%." % (over30 * 100, SHARE_OVER_30_MAX * 100))
    if nsent >= MIN_SENTENCES_FOR_RHYTHM and stdev < STDEV_MIN:
        finding(findings, "warning", "rhythm-monotone", 1, "Sentence-length spread is %.1f words; below %.0f the rhythm reads as machine-regular." % (stdev, STDEV_MIN))
    if grade > GRADE_MAX:
        finding(findings, "warning", "grade-high", 1, "Reading-grade proxy is %.1f; above %.0f is hard for a general audience." % (grade, GRADE_MAX))

    # --- links ---
    internal = external = 0
    for m in LINK_RE.finditer("\n".join(u["text"] for u in units if u["kind"] != "code")):
        target = m.group(2)
        if target.startswith("#") or target.startswith("mailto:"):
            continue
        if is_internal(target, site_host):
            internal += 1
        else:
            external += 1
    total_words = sum(len(words_of(u["text"])) for u in units if u["kind"] not in ("heading", "code"))
    required = min_internal if min_internal is not None else max(INTERNAL_FLOOR, total_words // INTERNAL_PER_WORDS)
    if internal < required:
        finding(findings, "warning", "internal-links-low", 1,
                "Found %d internal links; need %d (one per %d words, at least %d)." % (internal, required, INTERNAL_PER_WORDS, INTERNAL_FLOOR))

    # --- optional cross-check against the brief ---
    brief_checked = False
    if brief_path:
        brief_checked = True
        brief_text = read_text("audit", brief_path)
        brief_digits = re.sub(r"[,\s]", "", brief_text)
        for line, match in claim_hits:
            digits = re.sub(r"[^\d.]", "", match).strip(".")
            if digits and digits not in brief_digits:
                finding(findings, "warning", "number-not-in-brief", line,
                        "Figure does not appear in the brief's claim table; add a row with its source or cut it.", match)

    extra = {"words": total_words, "title": title, "h2_count": len(h2s), "intro_words": intro_words,
             "sections": section_out,
             "reading": {"sentences": nsent, "mean_words": round(mean, 1),
                         "median_words": round(statistics.median(lengths), 1) if lengths else 0.0,
                         "p90_words": round(percentile(lengths, 0.9), 1),
                         "stdev_words": round(stdev, 1), "share_over_30": round(over30, 3),
                         "share_under_9": round(under9, 3), "grade_proxy": round(grade, 1)},
             "links": {"internal": internal, "external": external, "internal_required": required},
             "brief_checked": brief_checked}
    return finish("audit", path, findings, extra)


def split_row(line):
    cells = [c.strip() for c in line.strip().strip("|").split("|")]
    return cells


def brief(path):
    text = blank_comments(read_text("brief", path))
    findings = []
    values = {}
    keys = {"audience": "audience", "promise": "promise", "angle": "angle",
            "not covered": "not_covered", "not-covered": "not_covered", "out of scope": "not_covered"}
    for idx, line in enumerate(text.split("\n"), 1):
        m = re.match(r"^\s*(?:[-*]\s*)?\**\s*([A-Za-z \-]+?)\s*:?\**\s*:\s*(.*)$", line)
        if not m:
            continue
        key = keys.get(m.group(1).strip().lower())
        if key and key not in values:
            values[key] = (idx, m.group(2).strip().strip("*").strip())
    counts = {}
    for key in ("audience", "promise", "angle", "not_covered"):
        idx, val = values.get(key, (1, ""))
        n = len(words_of(val))
        counts[key] = n
        label = key.replace("_", " ")
        if n == 0:
            finding(findings, "error", "brief-field-missing", idx, "Field '%s' is missing or empty." % label)
            continue
        if PLACEHOLDER_RE.search(val):
            finding(findings, "error", "brief-placeholder", idx, "Field '%s' still holds a placeholder." % label, val)
        if key == "promise":
            lo, hi = BRIEF_PROMISE_WORDS
            if not lo <= n <= hi:
                finding(findings, "error", "brief-promise-length", idx, "Promise is %d words; write one sentence of %d to %d words." % (n, lo, hi), val)
        elif n < BRIEF_MIN_WORDS[key]:
            finding(findings, "error", "brief-field-thin", idx, "Field '%s' has %d words; at least %d." % (label, n, BRIEF_MIN_WORDS[key]), val)

    rows, with_url = 0, 0
    blocks, cur = [], []
    for idx, line in enumerate(text.split("\n"), 1):
        if re.match(r"^\s*\|", line):
            cur.append((idx, line))
        elif cur:
            blocks.append(cur)
            cur = []
    if cur:
        blocks.append(cur)
    table = None
    for blk in blocks:
        low = [c.lower() for c in split_row(blk[0][1])]
        if any("claim" in c for c in low) and any("source" in c for c in low):
            table = (blk, low)
            break
    if table is None:
        finding(findings, "error", "brief-claim-table-missing", 1, "No claim table found; it needs a header with 'Claim' and 'Source' columns.")
    else:
        blk, low = table
        claim_i = next(i for i, c in enumerate(low) if "claim" in c)
        source_i = next(i for i, c in enumerate(low) if "source" in c)
        checked_i = next((i for i, c in enumerate(low) if "check" in c), None)
        if checked_i is None:
            finding(findings, "warning", "brief-no-checked-column", blk[0][0], "Claim table has no 'Checked' column; record the date each source was read.")
        for idx, line in blk[1:]:
            if re.match(r"^\s*\|?[\s:\-|]+\|?\s*$", line):
                continue
            cells = split_row(line)
            rows += 1
            claim = cells[claim_i] if claim_i < len(cells) else ""
            source = cells[source_i] if source_i < len(cells) else ""
            if len(words_of(claim)) < 3:
                finding(findings, "error", "brief-claim-thin", idx, "Claim cell is empty or under 3 words.", claim)
            um = re.search(r"https?://[^\s)|]+", source)
            if um:
                with_url += 1
                if re.match(r"^https?://[^/]+/?$", um.group(0)):
                    finding(findings, "warning", "brief-homepage-source", idx, "Source is a site homepage; link the page that holds the claim.", um.group(0))
            else:
                finding(findings, "error", "brief-claim-no-url", idx, "Claim has no source URL; cite it or cut the claim.", claim)
            if checked_i is not None and not re.search(r"\d{4}-\d{2}-\d{2}", cells[checked_i] if checked_i < len(cells) else ""):
                finding(findings, "warning", "brief-no-check-date", idx, "No YYYY-MM-DD date in the Checked cell.", claim)
        if rows < BRIEF_MIN_CLAIM_ROWS:
            finding(findings, "error", "brief-claim-rows", blk[0][0], "Claim table has %d rows; at least %d." % (rows, BRIEF_MIN_CLAIM_ROWS))
    extra = {"fields": counts, "claim_rows": rows, "claim_rows_with_url": with_url}
    return finish("brief", path, findings, extra)


def parse_args(argv):
    if len(argv) < 2 or argv[0] not in ("audit", "brief"):
        die("usage", "Usage: article_audit.py audit <article.md> [--site-host H] [--min-internal-links N] [--brief brief.md] | brief <brief.md>")
    cmd, rest = argv[0], argv[1:]
    path, opts, i = None, {"site_host": "", "min_internal": None, "brief": None}, 0
    while i < len(rest):
        a = rest[i]
        if a in ("--site-host", "--min-internal-links", "--brief") and cmd == "audit":
            if i + 1 >= len(rest):
                die(cmd, "Option %s needs a value." % a)
            v = rest[i + 1]
            if a == "--site-host":
                h = re.sub(r"^https?://", "", v.strip().lower()).split("/")[0]
                opts["site_host"] = h[4:] if h.startswith("www.") else h
            elif a == "--brief":
                opts["brief"] = v
            else:
                if not v.isdigit():
                    die(cmd, "--min-internal-links needs a whole number.")
                opts["min_internal"] = int(v)
            i += 2
        elif a.startswith("--") or path is not None:
            die(cmd, "Unexpected argument '%s'." % a)
        else:
            path = a
            i += 1
    if path is None:
        die(cmd, "Give the path of the Markdown file to check.")
    return cmd, path, opts


def main(argv=None):
    cmd, path, opts = parse_args(sys.argv[1:] if argv is None else argv)
    if cmd == "audit":
        return audit(path, opts["site_host"], opts["min_internal"], opts["brief"])
    return brief(path)


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except AttributeError:
        pass
    sys.exit(main())
