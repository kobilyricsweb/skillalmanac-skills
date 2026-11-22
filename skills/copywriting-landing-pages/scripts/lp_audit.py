#!/usr/bin/env python3
"""Audit a landing-page draft (Markdown or HTML) against the section contract.

Usage:
    python lp_audit.py <file> [--format auto|markdown|html]
                       [--optional proof,objections] [--strict]

Reads one file; writes nothing; no network. Prints one JSON object (strict JSON,
no NaN) to stdout. Exit codes: 0 = no errors (warnings allowed unless --strict),
1 = at least one error (or warning with --strict), 2 = usage or file problem
(a plain message goes to stderr).

Checks: section presence and order, hero length, block length limits,
unsupported numeric claims, banned phrases, CTA count, grammar and consistency,
and a reading-level proxy (Flesch-Kincaid grade).

Markdown conventions: a link with the title "cta" ([Text](url "cta")) is
forced to count as a CTA. In HTML, <button> and <a class="...btn|button|cta...">
count as CTAs. Fenced code and YAML front matter are ignored.
"""
import json
import os
import re
import sys
from html.parser import HTMLParser

# ---- thresholds (working values; the reason for each is in references/rules.md)
HEADLINE_MAX_WARN = 12      # words; a headline longer than this is read as a sentence, not a promise
HEADLINE_MAX_ERROR = 14
HEADLINE_MIN = 3            # under three words is almost always a slogan with no promise
HERO_SUPPORT_MAX_WARN = 30  # words of sub-headline text under the H1, CTA excluded
HERO_SUPPORT_MAX_ERROR = 45
SECTION_HEADING_MAX = 10    # words
PARAGRAPH_MAX = 50          # words per paragraph or list item
SECTION_WORDS_MAX = {"default": 150, "how": 180, "objections": 300, "proof": 150, "cta": 60}
SUBHEADS_MAX = 4            # H3s in a section that is not how/objections; more means several messages
CTA_LABEL_MIN, CTA_LABEL_MAX = 2, 5
CTA_TOTAL_MAX = 4           # primary CTAs on the whole page
CTA_PER_SECTION_MAX = 2
CTA_LABEL_VARIANTS_MAX = 2
FK_WARN, FK_ERROR = 8.0, 10.0   # Flesch-Kincaid grade proxy
FK_MIN_WORDS = 40               # below this the grade is too noisy to report
LONG_SENTENCE = 25              # words
LONG_SENTENCE_REPORT_MAX = 5
TEXT_SNIPPET = 120

ROLE_ORDER = ["hero", "proof", "how", "objections", "cta"]
ROLE_HEADING = [
    ("objections", re.compile(r"\b(faq|frequently asked|questions|objections?|concerns?|worried|doubts?|pricing|guarantee|risk|what if|before you (buy|sign|start))\b", re.I)),
    ("how", re.compile(r"\b(how (it|this|\w+) works?|how to|steps?|process|what happens|get (set up|going)|setup|set up|workflow)\b", re.I)),
    ("proof", re.compile(r"\b(proof|trusted|customers?|testimonials?|results?|case stud(y|ies)|reviews?|who (uses|is using)|in numbers|by the numbers|stories|love|loved)\b", re.I)),
    ("cta", re.compile(r"\b(get started|start|try|sign up|book|ready|join|request|download|contact|talk to|begin)\b", re.I)),
]

# verbs that mark a link as a call to action
CTA_VERBS = {"get", "start", "try", "book", "request", "join", "sign", "download", "buy", "subscribe",
             "create", "schedule", "claim", "talk", "contact", "shop", "order", "add", "begin", "open",
             "build", "launch", "install", "apply", "reserve", "register", "send", "speak"}
# verbs a CTA label may start with (adds secondary-action verbs)
LABEL_VERBS = CTA_VERBS | {"see", "watch", "view", "compare", "check", "browse", "choose", "pick", "use",
                           "take", "make", "run", "save", "learn", "read", "click", "submit"}
VAGUE_LABEL = re.compile(r"^(submit|click here|here|learn more|read more|more info|more|go|continue|send|ok|enter)$", re.I)
ARTICLES = {"a", "an", "the", "your", "my", "our"}

# ---- numeric claim patterns
NUM = r"\d[\d,]*(?:\.\d+)?"
CLAIM_PATTERNS = [
    ("percent", re.compile(NUM + r"\s?%")),
    ("multiplier", re.compile(r"\b" + NUM + r"\s?[x\u00d7](?![\w])|\b" + NUM + r"\s+times\s+(?:faster|more|as|better|cheaper)", re.I)),
    ("money", re.compile(r"[$\u20ac\u00a3]\s?" + NUM + r"\s?[kKmMbB]?\b")),
    ("count", re.compile(r"\b" + NUM + r"\+?\s+(?:[a-z]+\s+)?(?:customers|users|teams|companies|businesses|brands|founders|marketers|developers|agencies|stores|sites|reviews|ratings|downloads|projects|clients|members|subscribers|people|professionals|employees|firms|practices|inspectors|freelancers|owners|shops|clinics|schools|startups|creators|accountants)\b", re.I)),
    ("time", re.compile(r"\b(?:in|within|under|less than|saves?|saved|cuts?|reduc(?:e|es|ed)|saving)\s+(?:up to\s+|about\s+|over\s+|more than\s+)?" + NUM + r"\s?(?:seconds?|minutes?|mins?|hours?|hrs?|days?|weeks?|months?)\b|\b" + NUM + r"\s?(?:seconds?|minutes?|hours?|days?|weeks?)\s+(?:faster|sooner|less|saved|a week|per week|a day|per day)\b", re.I)),
    ("change", re.compile(r"\bfrom\s+" + NUM + r"\s?(?:seconds?|minutes?|hours?|days?|weeks?|months?|%|x)?\s+to\s+" + NUM, re.I)),
    ("rating", re.compile(r"\b\d(?:\.\d)?\s?(?:/|out of)\s?5\b|\b\d(?:\.\d)?\s?(?:stars?|\u2605)|(?:#|\bNo\.\s?)1\b|\btop\s+\d+\b", re.I)),
]
PRICE_AFTER = re.compile(r"^\s*(?:/|per\s)\s*(?:mo|month|yr|year|user|seat|member|week)", re.I)
PRICE_BEFORE = re.compile(r"(?:from|starting at|starts at|only|costs?|priced at|pricing|for|plans?)\s*$", re.I)
VAGUE_QUANTITY = re.compile(r"\b(thousands of|millions of|hundreds of|countless|numerous|a growing number of|many (?:companies|teams|customers|businesses|brands)|trusted by (?:many|leading|top|the best))\b", re.I)

# ---- support markers
LINK_RE = re.compile(r"\[([^\]]*)\]\(([^)\s]*)(?:\s+\"([^\"]*)\")?\)")
SUPPORT_TEXT = [
    re.compile(r"\bsources?\s*:", re.I),
    re.compile(r"\baccording to\b", re.I),
    re.compile(r"\[\^[\w-]+\]"),
    re.compile(r"\((?:[A-Z][\w&.\- ]+),?\s+(?:19|20)\d\d\)"),
    re.compile(r"\bas of\s+(?:[A-Za-z]+\s+)?(?:19|20)\d\d\b", re.I),
    re.compile(r"\bn\s?=\s?\d+"),
]
FOOTNOTE_DEF = re.compile(r"^\s*\[\^?([\w-]+)\]:\s*\S")
SOURCE_START = re.compile(r"^\s*(?:sources?\s*:|according to|\[\^?[\w-]+\]:)", re.I)
ATTRIBUTION = re.compile(r"^\s*(?:\u2014|\u2013|--|-)\s*[A-Z]")

# ---- banned phrases: (regex, severity, hint)
BANNED = [
    (r"revolutioni[sz]\w*|revolutionary", "warn", "say what changes, concretely"),
    (r"game[- ]chang\w*", "warn", "name the change"),
    (r"cutting[- ]edge|state[- ]of[- ]the[- ]art|next[- ]gen(?:eration)?|world[- ]class|best[- ]in[- ]class", "warn", "drop it or give the spec that earns it"),
    (r"groundbreaking|unparalleled|unrivall?ed|unmatched|industry[- ]leading|market[- ]leading", "warn", "comparison needs a named benchmark"),
    (r"seamless(?:ly)?|effortless(?:ly)?|frictionless", "warn", "describe the steps instead"),
    (r"robust|powerful|innovative|disruptive|holistic|synerg\w+", "warn", "show what it does"),
    (r"supercharg\w*|turbocharg\w*|skyrocket\w*|unleash\w*|unlock(?:s|ed|ing)? (?:the )?(?:full )?(?:power|potential)", "warn", "state the measured outcome or cut"),
    (r"take your \w+(?: \w+)? to the next level|next level", "warn", "say which level, measured how"),
    (r"in today'?s (?:fast[- ]paced|digital|competitive|ever[- ]changing)\b[\w -]*", "warn", "start with the reader's problem"),
    (r"\b(?:elevate|empower|leverage)s?\b", "warn", "use help, let, use"),
    (r"all[- ]in[- ]one (?:solution|platform)|one[- ]stop[- ]shop|end[- ]to[- ]end solution", "warn", "list the three things it covers"),
    (r"no[- ]brainer", "warn", "let the reader decide"),
    (r"the best\b|best (?:\w+ )?(?:on the market|in the world|ever)|number one", "error", "superlative needs a named ranking and date, or cut"),
    (r"guarantee[sd]? (?:results|success|growth|roi|to)\b|guaranteed", "error", "a guarantee needs written terms; state them or cut"),
    (r"risk[- ]free|100% (?:satisfaction|safe|secure|accurate)|zero risk", "error", "state the actual refund or cancellation term"),
    (r"act now|limited[- ]time|don'?t miss out|last chance|hurry|while (?:stocks|supplies) last|only \d+ (?:spots|seats|left)", "warn", "pressure is allowed only with a real, dated deadline"),
    (r"click here|\bsimply\b|\bjust\b(?= (?:click|add|sign|enter|connect))", "warn", "name the action; drop the minimiser"),
    (r"many (?:users|people|businesses) (?:love|trust)|loved by (?:many|thousands)", "error", "give the count and the source, or cut"),
]
BANNED_RE = [(re.compile(p, re.I), sev, hint) for p, sev, hint in BANNED]


def snippet(text, n=TEXT_SNIPPET):
    text = " ".join(text.split())
    return text if len(text) <= n else text[: n - 3] + "..."


def words_of(text):
    text = LINK_RE.sub(lambda m: m.group(1), text)
    text = re.sub(r"[*_`>#]", " ", text)
    return re.findall(r"[A-Za-z0-9][A-Za-z0-9'\u2019$%.,/+-]*", text)


def plain(text):
    text = LINK_RE.sub(lambda m: m.group(1), text)
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"[*_`]", "", text).strip()


# ---------------------------------------------------------------- parsing
def parse_markdown(text):
    lines = text.splitlines()
    i = 0
    if lines and lines[0].strip() == "---":
        for j in range(1, len(lines)):
            if lines[j].strip() == "---":
                i = j + 1
                break
    blocks, defs = [], {}
    para, para_line, in_code = [], 0, False

    def flush():
        nonlocal para
        if para:
            blocks.append({"kind": "para", "level": 0, "text": " ".join(para), "line": para_line})
            para = []

    for n in range(i, len(lines)):
        raw, line = lines[n], lines[n].rstrip()
        s = line.strip()
        if s.startswith("```") or s.startswith("~~~"):
            flush()
            in_code = not in_code
            continue
        if in_code:
            continue
        if not s:
            flush()
            continue
        m = FOOTNOTE_DEF.match(line)
        if m:
            flush()
            defs[m.group(1)] = n + 1
            blocks.append({"kind": "footnote", "level": 0, "text": s, "line": n + 1})
            continue
        m = re.match(r"^(#{1,6})\s+(.*?)\s*#*\s*$", s)
        if m:
            flush()
            blocks.append({"kind": "heading", "level": len(m.group(1)), "text": m.group(2), "line": n + 1})
            continue
        if re.match(r"^(?:[-*_]\s*){3,}$", s):
            flush()
            continue
        m = re.match(r"^(?:[-*+]|\d+[.)])\s+(.*)$", s)
        if m:
            flush()
            blocks.append({"kind": "item", "level": 0, "text": m.group(1), "line": n + 1})
            continue
        if s.startswith("|"):
            flush()
            if re.match(r"^\|?[\s:|-]+\|?$", s):
                continue
            blocks.append({"kind": "item", "level": 0, "text": " | ".join(c.strip() for c in s.strip("|").split("|")), "line": n + 1})
            continue
        if s.startswith(">"):
            flush()
            q = s.lstrip("> ").strip()
            if q:
                blocks.append({"kind": "para", "level": 0, "text": q, "line": n + 1, "quote": True})
            continue
        if s.startswith("<"):
            stripped = re.sub(r"<[^>]+>", " ", s).strip()
            if not stripped:
                continue
            s = stripped
        if not para:
            para_line = n + 1
        para.append(s)
    flush()
    return blocks, defs


class HtmlBlocks(HTMLParser):
    BLOCK = {"p", "li", "div", "section", "header", "footer", "ul", "ol", "br", "tr", "td", "th",
             "blockquote", "article", "main", "nav", "form", "aside", "figure", "figcaption", "table"}
    SKIP = {"script", "style", "noscript", "svg", "template", "head"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.blocks, self.defs = [], {}
        self.buf, self.kind, self.level, self.line = [], "para", 0, 1
        self.skip = 0
        self.in_quote = 0
        self.link_stack = []

    def flush(self):
        text = " ".join("".join(self.buf).split())
        if text:
            b = {"kind": self.kind, "level": self.level, "text": text, "line": self.line}
            if self.in_quote:
                b["quote"] = True
            self.blocks.append(b)
        self.buf, self.kind, self.level = [], "para", 0

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag in self.SKIP:
            self.skip += 1
            return
        if self.skip:
            return
        if re.fullmatch(r"h[1-6]", tag):
            self.flush()
            self.kind, self.level, self.line = "heading", int(tag[1]), self.getpos()[0]
        elif tag in self.BLOCK:
            self.flush()
            self.line = self.getpos()[0]
            if tag == "li":
                self.kind = "item"
            if tag == "blockquote":
                self.in_quote += 1
        elif tag == "a":
            cls = (a.get("class") or "").lower()
            title = "cta" if re.search(r"\b(btn|button|cta)\b", cls) else ""
            self.link_stack.append((a.get("href") or "", title))
            self.buf.append("[")
        elif tag == "button":
            self.link_stack.append(("#button", "cta"))
            self.buf.append("[")

    def handle_endtag(self, tag):
        if tag in self.SKIP:
            self.skip = max(0, self.skip - 1)
            return
        if self.skip:
            return
        if re.fullmatch(r"h[1-6]", tag) or tag in self.BLOCK:
            if tag == "blockquote":
                self.flush()
                self.in_quote = max(0, self.in_quote - 1)
            else:
                self.flush()
        elif tag in ("a", "button") and self.link_stack:
            href, title = self.link_stack.pop()
            self.buf.append("](%s%s)" % (href or "#", ' "cta"' if title else ""))

    def handle_data(self, data):
        if self.skip:
            return
        self.buf.append(data)

    def close(self):
        super().close()
        self.flush()


def parse_html(text):
    p = HtmlBlocks()
    p.feed(text)
    p.close()
    return p.blocks, p.defs


# ------------------------------------------------------------ structure
def build_sections(blocks, findings, optional):
    sections, preface, cur = [], [], None
    seen_h1 = 0
    for b in blocks:
        if b["kind"] == "heading" and b["level"] <= 2:
            if b["level"] == 1:
                seen_h1 += 1
                if seen_h1 > 1:
                    findings.append(finding("sections", "warn", b["line"], "multiple-h1", b["text"], "one H1 per page; use H2 for later sections"))
            cur = {"heading": b["text"], "line": b["line"], "level": b["level"], "blocks": [], "role": None}
            sections.append(cur)
        elif cur is None:
            preface.append(b)
        else:
            cur["blocks"].append(b)
    return sections, preface


def classify(sections):
    last = len(sections) - 1
    for idx, s in enumerate(sections):
        if idx == 0 and s["level"] == 1:
            s["role"] = "hero"
            continue
        role = "other"
        for name, rx in ROLE_HEADING:
            if rx.search(s["heading"]):
                role = name
                break
        if role == "other" and idx == last and idx > 0:
            n = sum(len(words_of(b["text"])) for b in s["blocks"])
            if n <= 60 and any(LINK_RE.search(b["text"]) for b in s["blocks"]):
                role = "cta"
        s["role"] = role


def finding(check, severity, line, rule, text, fix):
    return {"check": check, "severity": severity, "line": line, "rule": rule, "text": snippet(text), "fix": fix}


# ---------------------------------------------------------------- checks
def check_sections(sections, findings, optional):
    roles = [s["role"] for s in sections]
    if not sections or sections[0]["role"] != "hero":
        findings.append(finding("sections", "error", sections[0]["line"] if sections else 1, "no-h1", sections[0]["heading"] if sections else "", "start with one H1 that states the promise"))
    first = {}
    for idx, r in enumerate(roles):
        first.setdefault(r, idx)
    for role in ROLE_ORDER[1:]:
        if role not in first:
            sev = "warn" if role in optional else "error"
            findings.append(finding("sections", sev, 1, "missing-" + role, role, "add a %s section, or pass --optional %s if the page deliberately omits it" % (role, role)))
    present = [r for r in ROLE_ORDER if r in first]
    for a, b in zip(present, present[1:]):
        if first[a] > first[b]:
            line = sections[first[a]]["line"]
            findings.append(finding("sections", "warn", line, "order", "%s comes after %s" % (a, b), "order is hero, proof, how, objections, cta"))
    for s in sections:
        if len(words_of(s["heading"])) > SECTION_HEADING_MAX and s["role"] != "hero":
            findings.append(finding("blocks", "warn", s["line"], "heading-length", s["heading"], "section headings: %d words at most" % SECTION_HEADING_MAX))


def hero_section(sections):
    return sections[0] if sections and sections[0]["role"] == "hero" else None


def check_hero(sections, ctas, findings, stats):
    h = hero_section(sections)
    if not h:
        return
    hw = len(words_of(h["heading"]))
    stats["hero_headline_words"] = hw
    if hw > HEADLINE_MAX_ERROR:
        findings.append(finding("hero", "error", h["line"], "headline-long", h["heading"], "headline over %d words; one promise in %d or fewer" % (HEADLINE_MAX_ERROR, HEADLINE_MAX_WARN)))
    elif hw > HEADLINE_MAX_WARN:
        findings.append(finding("hero", "warn", h["line"], "headline-long", h["heading"], "headline over %d words; tighten" % HEADLINE_MAX_WARN))
    elif hw < HEADLINE_MIN:
        findings.append(finding("hero", "warn", h["line"], "headline-short", h["heading"], "under %d words rarely carries a promise" % HEADLINE_MIN))
    if re.search(r"(?:\band\b|&|\+|;|\bplus\b)", h["heading"], re.I):
        findings.append(finding("hero", "warn", h["line"], "two-promises", h["heading"], "headline joins two ideas; keep one and move the other to a section"))
    support = 0
    for b in h["blocks"]:
        if b["kind"] in ("para", "item") and not is_cta_block(b):
            support += len(words_of(b["text"]))
    stats["hero_support_words"] = support
    if support > HERO_SUPPORT_MAX_ERROR:
        findings.append(finding("hero", "error", h["line"], "support-long", "%d words under the headline" % support, "sub-headline text: %d words at most" % HERO_SUPPORT_MAX_WARN))
    elif support > HERO_SUPPORT_MAX_WARN:
        findings.append(finding("hero", "warn", h["line"], "support-long", "%d words under the headline" % support, "sub-headline text: %d words at most" % HERO_SUPPORT_MAX_WARN))
    if not any(c["section"] == 0 for c in ctas):
        findings.append(finding("cta", "error", h["line"], "hero-no-cta", h["heading"], "the hero needs the primary CTA"))


def check_blocks(sections, findings):
    for s in sections:
        total = 0
        subheads = 0
        for b in s["blocks"]:
            if b["kind"] == "heading":
                subheads += 1
                continue
            if b["kind"] == "footnote":
                continue
            n = len(words_of(b["text"]))
            total += n
            if n > PARAGRAPH_MAX and not is_cta_block(b):
                findings.append(finding("blocks", "warn", b["line"], "paragraph-long", b["text"], "%d words; limit %d per paragraph or item" % (n, PARAGRAPH_MAX)))
        limit = SECTION_WORDS_MAX.get(s["role"], SECTION_WORDS_MAX["default"])
        if s["role"] != "hero" and total > limit:
            findings.append(finding("blocks", "warn", s["line"], "section-long", s["heading"], "%d words; limit %d for a %s section (one message per section)" % (total, limit, s["role"])))
        if s["role"] not in ("how", "objections", "hero") and subheads > SUBHEADS_MAX:
            findings.append(finding("blocks", "warn", s["line"], "too-many-subheads", s["heading"], "%d sub-headings; more than %d usually means several messages" % (subheads, SUBHEADS_MAX)))


def split_sentences(text):
    parts = re.split(r"(?<=[.!?])[*_\"\u201d']*\s+(?=[A-Z0-9\"\u201c\[$#*_])", text.strip())
    return [p for p in parts if p]


def sentence_claims(sentence):
    clean = LINK_RE.sub(lambda m: m.group(1), sentence)
    clean = re.sub(r"[*_`]", "", clean)
    hits = []
    for name, rx in CLAIM_PATTERNS:
        for m in rx.finditer(clean):
            if name == "money":
                after = clean[m.end(): m.end() + 14]
                before = clean[max(0, m.start() - 20): m.start()]
                if PRICE_AFTER.match(after) or PRICE_BEFORE.search(before):
                    continue
            near = clean[max(0, m.start() - 40): m.end() + 40]
            if name in ("time", "money", "percent") and re.search(r"\b(trial|refund|money-back|guarantee|cancel)\b", near, re.I):
                continue  # offer terms (trial length, refund window) are commitments, not performance claims
            if re.match(r"\s*step\s+\d", clean, re.I) and name == "count":
                continue
            hits.append((name, m.group(0)))
    return hits


def has_support(sentence, defs):
    for m in LINK_RE.finditer(sentence):
        text, href, title = m.group(1), m.group(2), m.group(3)
        first = text.strip().split(" ")[0].lower() if text.strip() else ""
        if title == "cta" or first in CTA_VERBS:
            continue
        if re.match(r"https?://", href):
            return True
        if re.fullmatch(r"\d+", text.strip()) and href.startswith("#"):
            return True
    for rx in SUPPORT_TEXT:
        m = rx.search(sentence)
        if m:
            fm = re.search(r"\[\^([\w-]+)\]", m.group(0))
            if fm and fm.group(1) not in defs:
                return False
            return True
    return False


def check_claims(blocks, defs, findings, stats):
    count = 0
    for idx, b in enumerate(blocks):
        if b["kind"] == "footnote":
            continue
        text = b["text"]
        if VAGUE_QUANTITY.search(text) and not has_support(text, defs):
            m = VAGUE_QUANTITY.search(text)
            findings.append(finding("claims", "error", b["line"], "vague-quantity", m.group(0), "replace with the exact count and its source, or remove the claim"))
            count += 1
        block_supported = any(is_source_sentence(s) for s in split_sentences(text)[1:])
        nxt = blocks[idx + 1] if idx + 1 < len(blocks) else None
        next_supports = bool(nxt and (SOURCE_START.match(nxt["text"]) or (b.get("quote") and ATTRIBUTION.match(nxt["text"]))))
        quote_attr = b.get("quote") and ATTRIBUTION.search(text)
        for sentence in split_sentences(text):
            hits = sentence_claims(sentence)
            if not hits:
                continue
            if block_supported or next_supports or quote_attr or has_support(sentence, defs):
                continue
            kind, frag = hits[0]
            findings.append(finding("claims", "error", b["line"], "unsupported-number", sentence, "add a source in the same sentence (link, 'Source: ...', footnote) or remove the number [%s: %s]" % (kind, frag.strip())))
            count += 1
    stats["unsupported_claims"] = count


def is_source_sentence(sentence):
    """A trailing sentence that is itself a citation: 'Source: ...' or a lone external link."""
    flat = LINK_RE.sub(lambda m: m.group(1), sentence)
    if SOURCE_START.match(flat.strip()):
        return True
    m = LINK_RE.fullmatch(sentence.strip())
    return bool(m and re.match(r"https?://", m.group(2)) and m.group(3) != "cta")


def strip_urls(text):
    text = LINK_RE.sub(lambda m: m.group(1), text)
    return re.sub(r"https?://\S+", " ", text)


def check_banned(blocks, findings, stats):
    count = 0
    for b in blocks:
        if b["kind"] == "footnote":
            continue
        text = strip_urls(b["text"])
        for rx, sev, hint in BANNED_RE:
            for m in rx.finditer(text):
                phrase = m.group(0)
                if re.search(r"act now|limited|hurry|last chance|miss out|supplies|stocks|spots|seats", phrase, re.I) and re.search(r"\b(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?\s+\d{1,2}\b|\b\d{4}-\d{2}-\d{2}\b", text, re.I):
                    continue
                findings.append(finding("banned", sev, b["line"], "banned-phrase", phrase, hint))
                count += 1
    stats["banned_hits"] = count


def is_cta_block(b):
    return b["kind"] in ("para", "item") and len(find_ctas_in_block(b)) > 0 and len(words_of(LINK_RE.sub("", b["text"]))) <= 3


def find_ctas_in_block(b):
    out = []
    if b["kind"] == "heading" or b["kind"] == "footnote":
        return out
    whole = re.sub(r"[*_>\s-]", "", b["text"])
    for m in LINK_RE.finditer(b["text"]):
        text, href, title = m.group(1).strip(), m.group(2), m.group(3)
        label = re.sub(r"[*_`]", "", text).strip()
        first = re.sub(r"[^a-z]", "", label.split(" ")[0].lower()) if label else ""
        alone = re.sub(r"[*_>\s-]", "", m.group(0)) == whole
        if title == "cta" or first in CTA_VERBS or VAGUE_LABEL.match(label) or (alone and not href.startswith("#") and 1 <= len(label.split()) <= 6):
            if re.match(r"https?://", href) and title != "cta" and first not in CTA_VERBS and not alone and not VAGUE_LABEL.match(label):
                continue
            out.append({"label": label, "href": href})
    return out


def norm_label(label):
    ws = [w for w in re.sub(r"[^a-z0-9 ]", "", label.lower()).split() if w not in ARTICLES]
    return " ".join(ws)


def gather_ctas(sections, preface):
    ctas = []
    for si, s in enumerate(sections):
        for b in s["blocks"]:
            for c in find_ctas_in_block(b):
                c.update({"line": b["line"], "section": si})
                ctas.append(c)
    for b in preface:
        for c in find_ctas_in_block(b):
            c.update({"line": b["line"], "section": 0})
            ctas.append(c)
    return ctas


def check_ctas(ctas, sections, findings, stats):
    primary = [c for c in ctas if not c["href"].startswith("#") or c["href"] == "#button"]
    stats["cta_count"] = len(primary)
    if not primary and not ctas:
        findings.append(finding("cta", "error", 1, "no-cta", "no call to action found", "add one primary CTA link or button with a verb and an object"))
        return
    for c in ctas:
        label = c["label"]
        n = len(label.split())
        problems = []
        if VAGUE_LABEL.match(label):
            problems.append("vague label")
        else:
            first = re.sub(r"[^a-z]", "", label.split(" ")[0].lower()) if label else ""
            if first not in LABEL_VERBS:
                problems.append("does not start with a verb")
            if n < CTA_LABEL_MIN or n > CTA_LABEL_MAX:
                problems.append("%d words, want %d to %d" % (n, CTA_LABEL_MIN, CTA_LABEL_MAX))
        if label.endswith("!") or label.endswith("..."):
            problems.append("trailing punctuation")
        if len(label) > 3 and label.upper() == label:
            problems.append("all caps")
        if problems:
            findings.append(finding("cta", "warn", c["line"], "cta-grammar", label, "; ".join(problems) + "; use verb + object, e.g. 'Start the free trial'"))
    dests = sorted({c["href"] for c in primary if c["href"] != "#button" and c["href"]})
    if len(dests) > 1:
        findings.append(finding("cta", "error", primary[0]["line"], "cta-destination-split", ", ".join(dests), "all primary CTAs go to one destination"))
    labels = sorted({norm_label(c["label"]) for c in primary})
    if len(labels) > CTA_LABEL_VARIANTS_MAX:
        findings.append(finding("cta", "warn", primary[0]["line"], "cta-label-variants", "; ".join(labels), "at most %d wordings of the one action" % CTA_LABEL_VARIANTS_MAX))
    if len(primary) > CTA_TOTAL_MAX:
        findings.append(finding("cta", "warn", primary[-1]["line"], "cta-count", "%d primary CTAs" % len(primary), "at most %d on the page" % CTA_TOTAL_MAX))
    per = {}
    for c in primary:
        per[c["section"]] = per.get(c["section"], 0) + 1
    for si, n in per.items():
        if n > CTA_PER_SECTION_MAX:
            findings.append(finding("cta", "warn", sections[si]["line"], "cta-per-section", sections[si]["heading"], "%d CTAs in one section; at most %d" % (n, CTA_PER_SECTION_MAX)))
    last = sections[-1] if sections else None
    if last is not None and len(sections) > 1 and not any(c["section"] == len(sections) - 1 for c in ctas):
        findings.append(finding("cta", "error", last["line"], "final-no-cta", last["heading"], "end the page with the primary CTA"))


def syllables(word):
    w = re.sub(r"[^a-z]", "", word.lower())
    if not w:
        return 0
    n = len(re.findall(r"[aeiouy]+", w))
    if w.endswith("e") and not w.endswith(("le", "ee", "ye")) and n > 1:
        n -= 1
    return max(1, n)


def check_reading(blocks, findings, stats):
    sentences = []
    for b in blocks:
        if b["kind"] in ("para", "item") and not is_cta_block(b):
            text = plain(b["text"])
            parts = split_sentences(text) or [text]
            for p in parts:
                if words_of(p):
                    sentences.append((b["line"], p))
    all_words = [w for _, p in sentences for w in words_of(p)]
    stats["words"] = len(all_words)
    stats["sentences"] = len(sentences)
    stats["fk_grade"] = None
    stats["avg_sentence_words"] = None
    if not sentences:
        return
    stats["avg_sentence_words"] = round(len(all_words) / len(sentences), 2)
    if len(all_words) < FK_MIN_WORDS:
        return
    syl = sum(syllables(w) for w in all_words)
    grade = 0.39 * len(all_words) / len(sentences) + 11.8 * syl / len(all_words) - 15.59
    stats["fk_grade"] = round(grade, 2)
    if grade > FK_ERROR:
        findings.append(finding("reading", "error", 1, "grade-high", "grade %.1f" % grade, "aim for grade %d or lower: shorter sentences, plainer words" % FK_WARN))
    elif grade > FK_WARN:
        findings.append(finding("reading", "warn", 1, "grade-high", "grade %.1f" % grade, "aim for grade %d or lower" % FK_WARN))
    reported = 0
    for line, p in sentences:
        n = len(words_of(p))
        if n > LONG_SENTENCE and reported < LONG_SENTENCE_REPORT_MAX:
            findings.append(finding("reading", "warn", line, "sentence-long", p, "%d words; split it (limit %d)" % (n, LONG_SENTENCE)))
            reported += 1


# ------------------------------------------------------------------ main
def audit(text, fmt, optional, path):
    blocks, defs = parse_html(text) if fmt == "html" else parse_markdown(text)
    findings, stats = [], {}
    sections, preface = build_sections(blocks, findings, optional)
    classify(sections)
    ctas = gather_ctas(sections, preface)
    check_sections(sections, findings, optional)
    check_hero(sections, ctas, findings, stats)
    check_blocks(sections, findings)
    check_claims(blocks, defs, findings, stats)
    check_banned(blocks, findings, stats)
    check_ctas(ctas, sections, findings, stats)
    check_reading(blocks, findings, stats)
    stats.setdefault("hero_headline_words", None)
    stats.setdefault("hero_support_words", None)
    findings.sort(key=lambda f: (f["line"], f["check"], f["rule"]))
    errors = sum(1 for f in findings if f["severity"] == "error")
    warns = len(findings) - errors
    return {
        "tool": "lp_audit", "schema": 1, "file": os.path.basename(path), "format": fmt,
        "verdict": "fix" if errors else "pass", "counts": {"error": errors, "warn": warns},
        "stats": stats,
        "sections": [{"role": s["role"], "heading": snippet(s["heading"], 80), "line": s["line"],
                      "words": sum(len(words_of(b["text"])) for b in s["blocks"] if b["kind"] != "heading")} for s in sections],
        "findings": findings,
    }


def main(argv):
    args, fmt, optional, strict, path = list(argv), "auto", set(), False, None
    while args:
        a = args.pop(0)
        if a == "--format" and args:
            fmt = args.pop(0)
        elif a == "--optional" and args:
            optional = {x.strip() for x in args.pop(0).split(",") if x.strip()}
        elif a == "--strict":
            strict = True
        elif a.startswith("--") or path is not None:
            sys.stderr.write("usage: lp_audit.py <file> [--format auto|markdown|html] [--optional proof,objections] [--strict]\n")
            return 2
        else:
            path = a
    if path is None or fmt not in ("auto", "markdown", "html") or not optional <= set(ROLE_ORDER[1:]):
        sys.stderr.write("usage: lp_audit.py <file> [--format auto|markdown|html] [--optional proof,how,objections,cta] [--strict]\n")
        return 2
    try:
        with open(path, "rb") as fh:
            data = fh.read()
    except OSError as exc:
        sys.stderr.write("cannot read %s: %s\n" % (path, exc.strerror))
        return 2
    text = data.decode("utf-8", errors="replace").lstrip("\ufeff")
    if not text.strip():
        sys.stderr.write("%s is empty; paste the draft into a file first\n" % path)
        return 2
    if fmt == "auto":
        head = text[:2000].lower()
        fmt = "html" if path.lower().endswith((".html", ".htm")) or "<!doctype html" in head or "<html" in head or "<h1" in head else "markdown"
    report = audit(text, fmt, optional, path)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    sys.stdout.write(json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False) + "\n")
    bad = report["counts"]["error"] or (strict and report["counts"]["warn"])
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
