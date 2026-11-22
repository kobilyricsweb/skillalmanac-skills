#!/usr/bin/env python3
"""Scan a text for machine-written prose patterns, and check that an edit kept the facts.

    python prose_scan.py scan <file>              # pattern report as JSON
    python prose_scan.py facts <original> <edit>  # fact-preservation report as JSON

Reads the files it is given. Writes nothing. Prints one JSON object to stdout.
Errors go to stderr as a plain sentence.

Exit codes
    scan:   0 = verdict clean or light, 1 = verdict heavy
    facts:  0 = nothing missing or added, 1 = a number, name, URL, quote or code
            item differs between the two files
    both:   2 = usage error, unreadable file, or empty file

JSON contract for `scan` (schema_version 1)
    {"schema_version": 1, "command": "scan", "file": str, "words": int,
     "sentences": int, "findings": [{"line": int, "category": str, "rule": str,
     "match": str}], "counts_by_category": {category: int},
     "per_100_words": float, "verdict": "clean" | "light" | "heavy"}
    Findings are sorted by line, then rule. Text inside fenced code blocks is ignored.

JSON contract for `facts` (schema_version 1)
    {"schema_version": 1, "command": "facts", "original": str, "edit": str,
     "missing": {kind: [str]}, "added": {kind: [str]}, "ok": bool}
    kinds: numbers, urls, quotes, code, names. Lists are sorted and de-duplicated.

The scan matches surface patterns only. It cannot tell whether a flagged phrase is
wrong in context; a human or the agent decides. The facts check compares surface
forms; it cannot tell whether a claim was reworded into a different claim.
"""
import json
import re
import statistics
import sys

SCHEMA_VERSION = 1

# Findings per 100 words. Chosen so that ordinary careful prose (a few stock phrases
# in a long text) stays "clean" and a text built from stock phrases is "heavy".
LIGHT_FROM = 1.0
HEAVY_FROM = 3.0
# Three consecutive sentences opening with the same word read as a template.
PARALLEL_RUN = 3
# Hedge words in one sentence at or above this count read as stacked hedging.
HEDGE_STACK = 2
# Em dashes are flagged only when frequent: three or more AND this many per 100 words.
EM_DASH_PER_100 = 1.0
EM_DASH_MIN = 3
# Sentence lengths this uniform (population stdev, in words) over at least
# UNIFORM_MIN_SENTENCES sentences read as a metronome.
UNIFORM_STDEV = 3.0
UNIFORM_MIN_SENTENCES = 8

FENCE = re.compile(r"```.*?```", re.S)
WORD = re.compile(r"[A-Za-z0-9][A-Za-z0-9'_-]*")
SENTENCE = re.compile(r"\S.*?(?:[.!?]+(?=\s|$)|$)", re.S)

# (rule id, category, regex). All case-insensitive. One finding per match.
PATTERNS = [
    # Stock vocabulary that models overuse.
    ("stock-verb", "vocabulary", r"\b(delve[sd]?|delving|underscor(?:e|es|ed|ing)|showcas(?:e|es|ed|ing)|foster(?:s|ed|ing)?|leverag(?:e|es|ed|ing)|harness(?:es|ed|ing)?|unlock(?:s|ed|ing)?|elevat(?:e|es|ed|ing)|streamlin(?:e|es|ed|ing))\b"),
    ("stock-adjective", "vocabulary", r"\b(pivotal|multifaceted|seamless(?:ly)?|robust|holistic|vibrant|bustling|intricate|myriad|transformative|cutting-edge|groundbreaking|game-chang(?:er|ing)|paramount|invaluable)\b"),
    ("stock-noun", "vocabulary", r"\b(tapestry|realm|landscape|testament|beacon|cornerstone|synergy|paradigm|journey)\b"),
    # Claims of importance with no content.
    ("significance", "inflation", r"\b(stands? as a testament|plays? a (?:crucial|vital|pivotal|key|significant) role|is a (?:testament|reminder) to|marks? a (?:significant|pivotal|turning) (?:moment|point|shift)|rich (?:history|tapestry)|ever-evolving|ever-changing)\b"),
    ("era-opener", "inflation", r"\bin (?:today's|the modern|an increasingly) (?:fast-paced|digital|interconnected|ever-changing)[a-z -]*(?:world|landscape|era|age)\b"),
    # Padding that frames content instead of giving it.
    ("signpost", "filler", r"\b(it(?:'s| is) (?:important|crucial|essential) to (?:note|mention|remember|understand)(?: that)?|it(?:'s| is) worth (?:noting|mentioning|remembering)(?: that)?|it should be noted that|needless to say|at the end of the day|when it comes to|in conclusion|in summary|to summari[sz]e|overall,)"),
    ("announce", "filler", r"\b(let(?:'s| us) (?:dive|delve|explore|take a (?:closer )?look)|in this (?:article|post|section|guide), we(?: will| 'll)?|here(?:'s| is) the (?:thing|kicker|catch|truth|deal)|(?:here(?:'s| is) )?what you need to know)\b"),
    ("wordy-phrase", "filler", r"\b(in order to|due to the fact that|in the event that|a (?:wide )?(?:variety|range|number) of|the fact that|has the ability to|is able to|at this point in time)\b"),
    # Chat residue that should never reach a document.
    ("chat-residue", "residue", r"\b(as an ai(?: language model)?|i hope this (?:helps|finds you)|feel free to|great question|certainly!|absolutely!|happy to help|let me know if)\b"),
    # Hedging as a reflex.
    ("hedge-pair", "hedging", r"\b(may|might|could|can) (?:potentially|possibly|perhaps|arguably)\b|\b(?:potentially|possibly|arguably) (?:may|might|could)\b|\bit (?:could|can|may) be argued\b|\bseems? to (?:suggest|indicate)\b"),
    # Contrast templates and trailing participle phrases.
    ("negative-parallel", "parallelism", r"\bnot (?:just|only|merely|simply) [^.;:!?]{1,80}?,? but (?:also )?|\bit(?:'s| is) not (?:about )?[^.;:!?]{1,60}?[,;] it(?:'s| is)\b|\bmore than just\b"),
    ("participle-tail", "parallelism", r", (?:highlighting|underscoring|showcasing|reflecting|emphasi[sz]ing|demonstrating|ensuring|fostering|contributing to) (?:the|its|their|a|an|how|that)\b"),
    ("vague-authority", "vagueness", r"\b(experts (?:say|agree|believe)|studies (?:show|suggest|have shown)|research (?:shows|suggests)|many (?:people|experts) (?:believe|say)|industry (?:leaders|experts))\b"),
]
COMPILED = [(rid, cat, re.compile(rx, re.I)) for rid, cat, rx in PATTERNS]

# Single hedge words counted per sentence for the stacked-hedge rule.
HEDGES = re.compile(r"\b(may|might|could|perhaps|possibly|potentially|arguably|somewhat|relatively|fairly|generally|typically|tends? to|appears? to|seems? to|in some cases|to some extent)\b", re.I)


def read_text(path):
    try:
        with open(path, encoding="utf-8", errors="replace") as handle:
            text = handle.read()
    except OSError as exc:
        print(f"cannot read {path}: {exc}", file=sys.stderr)
        raise SystemExit(2)
    if not text.strip():
        print(f"{path} is empty; give it a text with at least one sentence", file=sys.stderr)
        raise SystemExit(2)
    return text


def blank_code(text):
    """Replace fenced code with spaces, keeping newlines so line numbers stay true."""
    return FENCE.sub(lambda m: re.sub(r"[^\n]", " ", m.group(0)), text)


def line_of(text, offset):
    return text.count("\n", 0, offset) + 1


def snippet(value, limit=80):
    value = re.sub(r"\s+", " ", value.strip())
    return value if len(value) <= limit else value[: limit - 3] + "..."


def sentences_with_offsets(text):
    return [(m.start(), m.group(0)) for m in SENTENCE.finditer(text) if WORD.search(m.group(0))]


def scan_text(text):
    clean = blank_code(text)
    findings = []
    for rid, cat, rx in COMPILED:
        for m in rx.finditer(clean):
            findings.append({"line": line_of(clean, m.start()), "category": cat, "rule": rid, "match": snippet(m.group(0))})

    sents = sentences_with_offsets(clean)
    words = len(WORD.findall(clean))

    # Stacked hedges inside one sentence.
    for start, sent in sents:
        hits = HEDGES.findall(sent)
        if len(hits) >= HEDGE_STACK:
            findings.append({"line": line_of(clean, start), "category": "hedging", "rule": "hedge-stack", "match": snippet(sent)})

    # Runs of sentences that open with the same word, within one paragraph.
    run_start, run_word, run_len, prev_end = None, None, 0, 0
    for start, sent in sents:
        first = WORD.search(sent).group(0).lower()
        same_paragraph = "\n\n" not in clean[prev_end:start]
        if first == run_word and same_paragraph:
            run_len += 1
        else:
            run_start, run_word, run_len = start, first, 1
        if run_len == PARALLEL_RUN:
            findings.append({"line": line_of(clean, run_start), "category": "parallelism", "rule": "same-opener-run", "match": f"{PARALLEL_RUN}+ sentences start with '{first}'"})
        prev_end = start + len(sent)

    # Uniform sentence length.
    lengths = [len(WORD.findall(s)) for _, s in sents]
    if len(lengths) >= UNIFORM_MIN_SENTENCES and statistics.pstdev(lengths) < UNIFORM_STDEV and statistics.mean(lengths) >= 10:
        findings.append({"line": 1, "category": "rhythm", "rule": "uniform-length", "match": f"{len(lengths)} sentences, mean {statistics.mean(lengths):.1f} words, stdev {statistics.pstdev(lengths):.1f}"})

    # Frequent em dashes.
    dashes = [m.start() for m in re.finditer("—", clean)]
    if len(dashes) >= EM_DASH_MIN and words and len(dashes) * 100.0 / words >= EM_DASH_PER_100:
        for pos in dashes:
            findings.append({"line": line_of(clean, pos), "category": "punctuation", "rule": "em-dash-density", "match": "—"})

    findings.sort(key=lambda f: (f["line"], f["rule"], f["match"]))
    return findings, words, len(sents)


def verdict_for(density):
    if density >= HEAVY_FROM:
        return "heavy"
    if density >= LIGHT_FROM:
        return "light"
    return "clean"


def cmd_scan(path):
    text = read_text(path)
    findings, words, nsent = scan_text(text)
    counts = {}
    for f in findings:
        counts[f["category"]] = counts.get(f["category"], 0) + 1
    density = round(len(findings) * 100.0 / words, 2) if words else 0.0
    verdict = verdict_for(density)
    report = {
        "schema_version": SCHEMA_VERSION, "command": "scan", "file": path, "words": words,
        "sentences": nsent, "findings": findings, "counts_by_category": dict(sorted(counts.items())),
        "per_100_words": density, "verdict": verdict,
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 1 if verdict == "heavy" else 0


# ---- facts ----------------------------------------------------------------

NUMBER = re.compile(r"[$€£]?\d[\d,]*(?:\.\d+)?%?")
URL = re.compile(r"https?://[^\s)>\]\"']+")
QUOTE = re.compile(r"\"([^\"\n]{1,300})\"|“([^”\n]{1,300})”")
CODE = re.compile(r"`([^`\n]+)`")
CAP = re.compile(r"\b[A-Z][A-Za-z0-9'-]*\b")
TITLE_BEFORE = re.compile(r"\b(?:Dr|Mr|Mrs|Ms|Mx|Prof|Sen|Rep|Gen|Capt|Sgt|Rev|St|Sr|Jr)\.\s+$")
SENTENCE_START = re.compile(r"(?:^|[.!?]\s+|\n\s*(?:[-*>]\s+|\d+[.)]\s+)?)$")


def facts_of(text):
    no_fence = text
    urls = {u.rstrip(".,;:") for u in URL.findall(no_fence)}
    code = {c.strip() for c in CODE.findall(no_fence)}
    quotes = {(a or b).strip() for a, b in QUOTE.findall(no_fence)}
    stripped = URL.sub(" ", CODE.sub(" ", no_fence))
    numbers = {n.rstrip(",") for n in NUMBER.findall(stripped)}
    inner, initial = set(), set()
    for m in CAP.finditer(stripped):
        token = m.group(0)
        if token == "I":
            continue
        before = stripped[: m.start()]
        # A name right after a title ("Dr. Lee") is a name, not a sentence start.
        is_initial = SENTENCE_START.search(before) and not TITLE_BEFORE.search(before)
        (initial if is_initial else inner).add(token)
    return {"numbers": numbers, "urls": urls, "quotes": quotes, "code": code, "names": inner}, initial


def cmd_facts(orig_path, edit_path):
    orig_text, edit_text = read_text(orig_path), read_text(edit_path)
    a, a_initial = facts_of(orig_text)
    b, b_initial = facts_of(edit_text)
    missing, added = {}, {}
    for kind in ("numbers", "urls", "quotes", "code", "names"):
        if kind == "names":
            # A name that moved to or from a sentence start is not a change.
            missing[kind] = sorted(a[kind] - (b[kind] | b_initial))
            added[kind] = sorted(b[kind] - (a[kind] | a_initial))
        else:
            missing[kind] = sorted(a[kind] - b[kind])
            added[kind] = sorted(b[kind] - a[kind])
    ok = not any(missing.values()) and not any(added.values())
    report = {"schema_version": SCHEMA_VERSION, "command": "facts", "original": orig_path, "edit": edit_path, "missing": missing, "added": added, "ok": ok}
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if ok else 1


def main(argv):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    usage = "usage: prose_scan.py scan <file> | prose_scan.py facts <original> <edit>"
    if len(argv) == 2 and argv[0] == "scan":
        return cmd_scan(argv[1])
    if len(argv) == 3 and argv[0] == "facts":
        return cmd_facts(argv[1], argv[2])
    print(usage, file=sys.stderr)
    return 2


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except SystemExit as exc:
        sys.exit(exc.code)
