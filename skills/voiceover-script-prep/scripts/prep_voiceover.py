#!/usr/bin/env python3
"""Prepare a written English script for text-to-speech or a voice actor.

Usage:
    python prep_voiceover.py SCRIPT --max-chars N [--wpm 155] [--lexicon FILE]
        [--max-sentence-words 35] [--comma-pause 0.2] [--sentence-pause 0.5]
        [--paragraph-pause 0.9] [--explicit-breaks] [--out-dir DIR]

Reads SCRIPT (UTF-8 text or simple Markdown) and an optional lexicon (JSON object
mapping a written form to a spoken form, or to {"say": ..., "ipa": ...}).
Prints ONE strict JSON report on stdout. Writes files only when --out-dir is given:
    spoken.txt     the spoken-form script, paragraphs separated by blank lines
    chunks.jsonl   one JSON object per chunk, each at most --max-chars characters
    spoken.ssml    an SSML-like marked version (paragraphs, sentences, spell-outs)
No audio is generated, nothing is sent anywhere, no network is used.

Exit codes: 0 verdict "ready"; 1 verdict "review" (a blocking list is not empty);
2 unreadable input or bad arguments (message on stderr).
"""
import argparse
import collections
import json
import os
import re
import sys
import unicodedata
from xml.sax.saxutils import escape

SCHEMA_VERSION = 1

# Typical narration speed for English prose is 140 to 170 words per minute; the
# estimate is also given at both ends of that band.
WPM_LOW, WPM_HIGH = 140, 170
# Below about 60 or above 300 wpm the number is almost certainly a typo.
WPM_MIN_ACCEPT, WPM_MAX_ACCEPT = 60, 300
# Longer sentences are hard to say in one breath and hard for TTS to phrase.
DEFAULT_MAX_SENTENCE_WORDS = 35
# Pause lengths in seconds (comma, sentence end, paragraph end).
DEFAULT_COMMA_PAUSE, DEFAULT_SENTENCE_PAUSE, DEFAULT_PARAGRAPH_PAUSE = 0.2, 0.5, 0.9
# Tongue-twister heuristic: this many words of one starting sound within a window.
TWISTER_WINDOW, TWISTER_MIN_HITS = 6, 4
# A chunk break is only taken at a clause boundary if it leaves at least this
# fraction of the limit in the first piece (avoids tiny fragments).
MIN_PIECE_FRACTION = 0.3

ONES = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten",
        "eleven", "twelve", "thirteen", "fourteen", "fifteen", "sixteen", "seventeen",
        "eighteen", "nineteen"]
TENS = ["", "", "twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety"]
SCALES = [(10 ** 12, "trillion"), (10 ** 9, "billion"), (10 ** 6, "million"), (1000, "thousand")]
ORD_IRREG = {"one": "first", "two": "second", "three": "third", "five": "fifth",
             "eight": "eighth", "nine": "ninth", "twelve": "twelfth"}
MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August",
          "September", "October", "November", "December"]
MONTH_RE = "(?:" + "|".join(MONTHS) + ")"
NUM = r"\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?"

CUR = {"$": ("dollar", "dollars", "cent", "cents"), "€": ("euro", "euros", "cent", "cents"),
       "£": ("pound", "pounds", "penny", "pence")}
SCALE_WORDS = {"k": "thousand", "m": "million", "bn": "billion", "b": "billion",
               "thousand": "thousand", "million": "million", "billion": "billion",
               "trillion": "trillion"}
UNITS = {
    "km/h": ("kilometer per hour", "kilometers per hour"), "kph": ("kilometer per hour", "kilometers per hour"),
    "mph": ("mile per hour", "miles per hour"), "km": ("kilometer", "kilometers"),
    "kg": ("kilogram", "kilograms"), "cm": ("centimeter", "centimeters"),
    "mm": ("millimeter", "millimeters"), "mi": ("mile", "miles"), "lbs": ("pound", "pounds"),
    "lb": ("pound", "pounds"), "oz": ("ounce", "ounces"), "ft": ("foot", "feet"),
    "GB": ("gigabyte", "gigabytes"), "MB": ("megabyte", "megabytes"), "KB": ("kilobyte", "kilobytes"),
    "TB": ("terabyte", "terabytes"), "kHz": ("kilohertz", "kilohertz"), "MHz": ("megahertz", "megahertz"),
    "GHz": ("gigahertz", "gigahertz"), "Hz": ("hertz", "hertz"), "ms": ("millisecond", "milliseconds"),
    "kW": ("kilowatt", "kilowatts"), "MW": ("megawatt", "megawatts"), "min": ("minute", "minutes"),
    "hrs": ("hour", "hours"), "hr": ("hour", "hours"), "sec": ("second", "seconds"),
    "°C": ("degree Celsius", "degrees Celsius"), "°F": ("degree Fahrenheit", "degrees Fahrenheit"),
}
UNIT_RE = "|".join(re.escape(u) for u in sorted(UNITS, key=len, reverse=True))

TITLES = {"Mr": "Mister", "Mrs": "Missus", "Ms": "Miz", "Prof": "Professor", "Sen": "Senator",
          "Rep": "Representative", "Gen": "General", "Capt": "Captain", "Col": "Colonel",
          "Lt": "Lieutenant", "Sgt": "Sergeant", "Rev": "Reverend"}
# (written form, spoken form, keep the full stop when a new sentence follows)
GENERAL_ABBR = [("e.g.", "for example", False), ("i.e.", "that is", False), ("etc.", "et cetera", True),
                ("vs.", "versus", False), ("approx.", "approximately", False), ("Inc.", "Incorporated", True),
                ("Ltd.", "Limited", True), ("Corp.", "Corporation", True), ("Co.", "Company", True),
                ("Ave.", "Avenue", True), ("Blvd.", "Boulevard", True), ("Rd.", "Road", True),
                ("Mt.", "Mount", False), ("Jr.", "Junior", True), ("Sr.", "Senior", True)]

# Acronyms read letter by letter, and acronyms read as words. Anything else in
# capitals is reported, never guessed.
SPELLED = set("""FBI CIA USA UK US EU UN AI TV CEO CFO CTO API URL HTML CSS SQL GPU CPU PDF USB SEO UI UX
DNA HR IT PR VR AR ID PC DIY VIP ATM GPS LED LCD HD NBA NFL BBC CNN HTTP HTTPS JSON XML IP VPN SMS""".split())
AS_WORDS = set("NASA NATO OK ASAP RAM LASER SCUBA RADAR UNESCO UNICEF COVID OPEC PIN AIDS ZIP".split())

SYMBOLS = set("&+=@#~%$€£°×÷<>^|\\/*_{}[]")
STOP_SHORT = {"the", "and", "for", "but", "not", "you", "are", "was", "his", "her", "its"}
# Words made by number expansion are not prose; they would trip the repeated-sound check.
NUMBER_WORDS = set(ONES) | {t for t in TENS if t} | {"hundred", "thousand", "million", "billion", "trillion", "minus", "point"}
SIBILANT_STARTS = {"s", "sh", "z", "ch"}

PUA_OPEN, PUA_CLOSE, PUA_BASE = "", "", 0xE100
PLACEHOLDER_RE = re.compile("(.)", re.S)
SPLIT_RE = re.compile(r'(?<!\b[A-Z])[.!?…]+["”’)\]]*(?:\s+|$)')
WORD_RE = re.compile(r"[^\W_]+(?:['’][^\W_]+)*")


def cardinal(n):
    if n < 0:
        return "minus " + cardinal(-n)
    if n < 20:
        return ONES[n]
    if n < 100:
        t, o = divmod(n, 10)
        return TENS[t] + ("-" + ONES[o] if o else "")
    if n < 1000:
        h, r = divmod(n, 100)
        return ONES[h] + " hundred" + (" " + cardinal(r) if r else "")
    for value, name in SCALES:
        if n >= value:
            q, r = divmod(n, value)
            return cardinal(q) + " " + name + (" " + cardinal(r) if r else "")
    return str(n)


def _ord_word(w):
    if w in ORD_IRREG:
        return ORD_IRREG[w]
    if w.endswith("y"):
        return w[:-1] + "ieth"
    return w + "th"


def ordinal(n):
    c = cardinal(n)
    head, sep, last = c.rpartition(" ")
    if "-" in last:
        a, b = last.split("-")
        last = a + "-" + _ord_word(b)
    else:
        last = _ord_word(last)
    return head + sep + last


def digits_spoken(s):
    return " ".join(ONES[int(c)] for c in s if c.isdigit())


def num_words(s):
    s = s.replace(",", "")
    if "." in s:
        i, f = s.split(".")
        return cardinal(int(i)) + " point " + digits_spoken(f)
    return cardinal(int(s))


def year_words(y):
    """Years are read as pairs: 1984 nineteen eighty-four, 2026 twenty twenty-six."""
    if y in (1000, 2000):
        return cardinal(y)
    if 2001 <= y <= 2009:
        return "two thousand " + cardinal(y - 2000)
    first, rest = divmod(y, 100)
    if rest == 0:
        return cardinal(first) + " hundred"
    if rest < 10:
        return cardinal(first) + " oh " + ONES[rest]
    return cardinal(first) + " " + cardinal(rest)


def decade_plural(n):
    w = cardinal(n)
    if w.endswith("y"):
        return w[:-1] + "ies"
    return w + "s"


class Normalizer:
    """Turns one paragraph of written text into spoken form."""

    def __init__(self, lexicon):
        self.lexicon = lexicon
        self.counts = collections.Counter()
        self.notes = []
        self.long_urls = []
        self.store = []
        self.line = 0

    # protected segments (lexicon hits, spelled acronyms, URLs) survive later passes
    def protect(self, plain, ssml):
        self.store.append((plain, ssml))
        return PUA_OPEN + chr(PUA_BASE + len(self.store) - 1) + PUA_CLOSE

    def resolve(self, text, mode):
        if mode == "ssml":
            text = escape(text)
        idx = 0 if mode == "plain" else 1
        return PLACEHOLDER_RE.sub(lambda m: self.store[ord(m.group(1)) - PUA_BASE][idx], text)

    def note(self, kind, detail):
        self.notes.append({"line": self.line, "kind": kind, "detail": detail})

    def _spell(self, letters, suffix=""):
        plain = " ".join(letters) + suffix
        ssml = '<say-as interpret-as="characters">' + letters + "</say-as>" + suffix
        return self.protect(plain, ssml)

    def normalize(self, text):
        self.store = []
        t = text
        # 1 lexicon
        for key in sorted(self.lexicon, key=len, reverse=True):
            entry = self.lexicon[key]
            say, ipa = entry.get("say"), entry.get("ipa")
            pat = re.compile(r"(?<![\w])" + re.escape(key) + r"(?![\w])")

            def lex(m, say=say, ipa=ipa, key=key):
                self.counts["lexicon"] += 1
                plain = say if say else key
                if ipa:
                    ssml = '<phoneme alphabet="ipa" ph="%s">%s</phoneme>' % (escape(ipa, {'"': "&quot;"}), escape(plain))
                else:
                    ssml = escape(plain)
                return self.protect(plain, ssml)
            t = pat.sub(lex, t)
        # 2 URLs and e-mail addresses
        t = re.sub(r"https?://[^\s<>\"')]+|www\.[^\s<>\"')]+", self._url, t)
        t = re.sub(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+", self._email, t)
        t = re.sub(r"(?<![\w@/.])[a-z0-9-]+(?:\.[a-z0-9-]+)*\.(?:com|org|net|io|co|ai|dev|app|gov|edu|uk|il)\b(?:/[^\s<>\"')]*)?",
                   self._url, t)
        # 3 dotted acronyms, titles and abbreviations
        t = re.sub(r"(?<![A-Za-z.])(?:[A-Z]\.){2,}", self._dotted, t)
        t = self._abbreviations(t)
        # 4 dates, times, phone numbers
        t = self._dates(t)
        t = self._times(t)
        t = re.sub(r"(?<!\d)(?:\+?1[-.\s])?\(?\d{3}\)?[-.\s]\d{3}[-.\s]\d{4}(?!\d)", self._phone, t)
        # seven-digit local numbers (555-0100) are read digit by digit; only a hyphen counts as the separator
        t = re.sub(r"(?<![\d.,$-])\d{3}-\d{4}(?![\d-])", self._phone, t)
        # version strings: v2.1.3 -> "version two point one point three"; bare x.y.z or x.y.z.w -> no "version"
        t = re.sub(r"(?<![\w.])([vV])?(\d+(?:\.\d+){1,3})(?!\w|\.\d)", self._version, t)
        # 5 money, percent, symbols that carry numbers
        t = re.sub(r"([$€£])\s?(" + NUM + r")(?:\s?(k|K|m|M|bn|B|thousand|million|billion|trillion)\b)?", self._currency, t)
        t = re.sub(r"(" + NUM + r")\s?%", lambda m: self._count("percent", num_words(m.group(1)) + " percent"), t)
        t = re.sub(r"(?<![\w.])-(?=\d)", "minus ", t)
        t = re.sub(r"#(?=\d)", "number ", t)
        t = re.sub(r"~(?=\d)", "about ", t)
        t = re.sub(r"\b24/7\b", lambda m: self._count("fraction", "twenty-four seven"), t)
        t = re.sub(r"(?<![\d/.])(\d{1,2})/(\d{1,2})(?![\d/])", self._fraction, t)
        # 6 ranges, units, ordinals, decades
        t = re.sub(r"(?<![\w/.])(" + NUM + r")[-–](" + NUM + r")(?![\w/])", self._range, t)
        t = re.sub(r"(?<![\w.])(" + NUM + r")\s?(" + UNIT_RE + r")(?![A-Za-z])", self._unit, t)
        t = re.sub(r"\b(\d{4})s\b", self._decade4, t)
        t = re.sub(r"['’]?\b(\d)0s\b", lambda m: self._count("decade", decade_plural(int(m.group(1)) * 10)), t)
        t = re.sub(r"\b(\d+)(?:st|nd|rd|th)\b", lambda m: self._count("ordinal", ordinal(int(m.group(1)))), t)
        # 7 plain symbols
        t = re.sub(r"(?<=\s)&(?=\s)|(?<=\w)&(?=\w)", " and ", t)
        t = re.sub(r"\band/or\b", "and or", t)
        t = re.sub(r"(?<=\s)\+(?=\s)", "plus", t)
        t = re.sub(r"(?<=\s)=(?=\s)", "equals", t)
        t = re.sub(r"×", " times ", t)
        t = re.sub(r"(?<![\w])@(\w+)", lambda m: "at " + m.group(1), t)
        t = re.sub(r"(?<![\w])#([A-Za-z]\w*)", lambda m: "hashtag " + m.group(1), t)
        # 8 remaining numbers
        t = re.sub(r"(?<![\w/])(" + NUM + r")(?![A-Za-z/\d])", self._number, t)
        # 9 acronyms in capitals
        t = re.sub(r"(?<![A-Za-z0-9])([A-Z]{2,6})(s|'s|’s)?(?![A-Za-z0-9])", self._acronym, t)
        t = re.sub(r"\s+", " ", t).strip()
        t = re.sub(r"\s+([,.;:!?])", r"\1", t)
        return t

    def _count(self, kind, text):
        self.counts[kind] += 1
        return text

    def _speak_url(self, s):
        out = []
        for ch in s:
            if ch.isdigit():
                out.append(" " + ONES[int(ch)] + " ")
            else:
                out.append({".": " dot ", "/": " slash ", "-": " dash ", "_": " underscore ", "?": " question mark ",
                            "=": " equals ", "&": " and ", "#": " hash ", ":": " colon ", "@": " at "}.get(ch, ch))
        return re.sub(r"\s+", " ", "".join(out)).strip()

    def _url(self, m):
        raw = m.group(0)
        trail = ""
        while raw and raw[-1] in ".,;:!?":
            trail = raw[-1] + trail
            raw = raw[:-1]
        shown = re.sub(r"^https?://", "", raw)
        shown = re.sub(r"^www\.", "", shown)
        path = shown.split("/", 1)[1] if "/" in shown else ""
        if len(path.strip("/").split("/")) > 2 or re.search(r"[?&#=]", shown) or len(shown) > 40:
            self.long_urls.append({"line": self.line, "url": raw})
        spoken = self._speak_url(shown)
        self.counts["url"] += 1
        return self.protect(spoken, escape(spoken)) + trail

    def _email(self, m):
        spoken = self._speak_url(m.group(0))
        self.counts["email"] += 1
        return self.protect(spoken, escape(spoken))

    def _dotted(self, m):
        letters = m.group(0).replace(".", "")
        self.counts["acronym_spelled"] += 1
        keep = "." if not m.string[m.end():].strip() else ""
        return self._spell(letters) + keep

    def _abbreviations(self, t):
        def dual(word, title, street):
            def fn(m):
                prev = m.string[:m.start()]
                nxt = m.string[m.end():]
                prev_cap = re.search(r"(?:[A-Z][a-z]+|\d+)\s*$", prev)
                next_cap = re.match(r"\s+[A-Z]", nxt)
                if prev_cap and not next_cap:
                    self.counts["abbreviation"] += 1
                    return street + ("." if not nxt.strip() else "")
                if prev_cap and next_cap:
                    self.note("ambiguous_abbreviation", "%s. read as '%s'; could be '%s'" % (word, title, street))
                self.counts["abbreviation"] += 1
                return title
            return fn
        t = re.sub(r"(?<![A-Za-z])Dr\.", dual("Dr", "Doctor", "Drive"), t)
        t = re.sub(r"(?<![A-Za-z])St\.", dual("St", "Saint", "Street"), t)
        t = re.sub(r"(?<![A-Za-z])(Mr|Mrs|Ms|Prof|Sen|Rep|Gen|Capt|Col|Lt|Sgt|Rev)\.(?=\s+[A-Z])",
                   lambda m: self._count("abbreviation", TITLES[m.group(1)]), t)
        t = re.sub(r"(?<![A-Za-z])No\.\s?(?=\d)", lambda m: self._count("abbreviation", "number "), t)
        for written, spoken, keep in GENERAL_ABBR:
            def fn(m, spoken=spoken, keep=keep):
                self.counts["abbreviation"] += 1
                nxt = m.string[m.end():]
                if keep and (not nxt.strip() or re.match(r"\s+[A-Z]", nxt)):
                    return spoken + "."
                return spoken
            t = re.sub(r"(?<![A-Za-z.])" + re.escape(written), fn, t)
        return t

    def _dates(self, t):
        def md_y(m):
            return self._count("date", "%s %s, %s" % (m.group(1), ordinal(int(m.group(2))), year_words(int(m.group(3)))))

        def d_m_y(m):
            return self._count("date", "the %s of %s, %s" % (ordinal(int(m.group(1))), m.group(2), year_words(int(m.group(3)))))

        def md(m):
            return self._count("date", "%s %s" % (m.group(1), ordinal(int(m.group(2)))))

        def d_m(m):
            return self._count("date", "the %s of %s" % (ordinal(int(m.group(1))), m.group(2)))

        def iso(m):
            mo = int(m.group(2))
            if not 1 <= mo <= 12:
                return m.group(0)
            return self._count("date", "%s %s, %s" % (MONTHS[mo - 1], ordinal(int(m.group(3))), year_words(int(m.group(1)))))
        sfx = r"(?:st|nd|rd|th)?"
        t = re.sub(r"\b(" + MONTH_RE + r")\s(\d{1,2})" + sfx + r",?\s(\d{4})\b", md_y, t)
        t = re.sub(r"\b(\d{1,2})" + sfx + r"\s(" + MONTH_RE + r"),?\s(\d{4})\b", d_m_y, t)
        t = re.sub(r"\b(\d{4})-(\d{2})-(\d{2})\b", iso, t)
        t = re.sub(r"\b(" + MONTH_RE + r")\s(\d{1,2})" + sfx + r"\b(?![,:]?\s?\d)", md, t)
        t = re.sub(r"\b(\d{1,2})" + sfx + r"\s(" + MONTH_RE + r")\b", d_m, t)
        return t

    def _times(self, t):
        def minutes(mm):
            if mm == 0:
                return ""
            return " oh " + ONES[mm] if mm < 10 else " " + cardinal(mm)

        def ampm(m):
            h, mm, ap = int(m.group(1)), int(m.group(2) or 0), m.group(3).upper()
            if not 0 <= h <= 24 or mm > 59:
                return m.group(0)
            self.counts["time"] += 1
            nxt = m.string[m.end():]
            # the full stop of "p.m." doubles as the sentence end when nothing or a new sentence follows
            keep = "." if m.group(4) and (not nxt.strip() or re.match(r"\s+[A-Z]", nxt)) else ""
            return cardinal(h) + minutes(mm) + " " + self._spell(ap + "M") + keep
        t = re.sub(r"\b(\d{1,2})(?::(\d{2}))?\s?([apAP])\.?[mM](\.?)(?![A-Za-z])", ampm, t)

        def clock(m):
            h, mm = int(m.group(1)), int(m.group(2))
            if h > 23 or mm > 59:
                return m.group(0)
            self.counts["time"] += 1
            if mm == 0:
                return cardinal(h) + (" hundred" if h >= 13 else " o'clock")
            return cardinal(h) + minutes(mm)
        return re.sub(r"(?<![\d:.])(\d{1,2}):(\d{2})(?![\d:])", clock, t)

    def _phone(self, m):
        groups = re.findall(r"\d+", m.group(0))
        spoken = ", ".join(digits_spoken(g) for g in groups)
        self.counts["phone"] += 1
        return self.protect(spoken, escape(spoken))

    def _version(self, m):
        prefix, body = m.group(1), m.group(2)
        parts = body.split(".")
        if not prefix and len(parts) < 3:
            return m.group(0)  # a plain decimal such as 2.5; the number rule reads it
        spoken = " point ".join(cardinal(int(p)) if p == "0" or not p.startswith("0") else digits_spoken(p)
                                for p in parts)
        if prefix:
            spoken = "version " + spoken
        self.counts["version"] += 1
        return self.protect(spoken, escape(spoken))

    def _currency(self, m):
        sym, num, scale = m.groups()
        u1, up, c1, cp = CUR[sym]
        raw = num.replace(",", "")
        self.counts["currency"] += 1
        if scale:
            return num_words(num) + " " + SCALE_WORDS[scale.lower()] + " " + up
        if "." in raw:
            whole_s, frac = raw.split(".")
            if len(frac) <= 2:
                whole, cents = int(whole_s), int((frac + "0")[:2])
                if whole == 0 and cents:
                    return cardinal(cents) + " " + (c1 if cents == 1 else cp)
                s = cardinal(whole) + " " + (u1 if whole == 1 else up)
                if cents:
                    s += " and " + cardinal(cents) + " " + (c1 if cents == 1 else cp)
                return s
            return num_words(raw) + " " + up
        n = int(raw)
        return cardinal(n) + " " + (u1 if n == 1 else up)

    def _fraction(self, m):
        a, b = int(m.group(1)), int(m.group(2))
        if not 2 <= b <= 10 or a == 0:
            return m.group(0)
        den = {2: "half", 4: "quarter"}.get(b) or ordinal(b)
        if a > 1:
            den = "halves" if b == 2 else den + "s"
        return self._count("fraction", cardinal(a) + " " + den)

    def _range(self, m):
        a, b = m.group(1), m.group(2)
        if any(len(x) > 1 and x.startswith("0") and not x.startswith("0.") for x in (a, b)):
            return m.group(0)
        try:
            av, bv = float(a.replace(",", "")), float(b.replace(",", ""))
        except ValueError:
            return m.group(0)
        if av >= bv:
            return m.group(0)
        self.counts["range"] += 1
        if re.fullmatch(r"\d{4}", a) and re.fullmatch(r"\d{4}", b) and 1001 <= int(a) <= 2099 and 1001 <= int(b) <= 2099:
            return year_words(int(a)) + " to " + year_words(int(b))
        return a + " to " + b

    def _unit(self, m):
        num, unit = m.group(1), m.group(2)
        one, many = UNITS[unit]
        self.counts["unit"] += 1
        return num_words(num) + " " + (one if num == "1" else many)

    def _decade4(self, m):
        y = int(m.group(1))
        self.counts["decade"] += 1
        if y == 2000:
            return "two thousands"
        if y % 100 == 0:
            return cardinal(y // 100) + " hundreds"
        return cardinal(y // 100) + " " + decade_plural(y % 100)

    def _number(self, m):
        raw = m.group(1)
        plain = raw.replace(",", "")
        before = m.string[:m.start()]
        if "." in plain:
            self.counts["number"] += 1
            return num_words(raw)
        if len(plain) > 1 and plain.startswith("0"):
            self.counts["number"] += 1
            return digits_spoken(plain)
        if len(plain) > 15:
            return raw
        if "," not in raw and len(plain) >= 10:
            self.note("long_digit_string", "%s read digit by digit" % plain)
            self.counts["number"] += 1
            return digits_spoken(plain)
        if "," not in raw and len(plain) == 4 and 1000 <= int(plain) <= 2099:
            ctx = re.search(r"(?:\b(?:in|since|by|until|till|from|before|after|during|year|circa|of|early|late|mid)|\b"
                            + MONTH_RE + r"|\()\s*$", before, re.I)
            if ctx:
                self.counts["year"] += 1
                return year_words(int(plain))
            if int(plain) >= 1100:
                self.note("ambiguous_year_or_count", "%s read as a count: %s" % (plain, cardinal(int(plain))))
        self.counts["number"] += 1
        return cardinal(int(plain))

    def _acronym(self, m):
        letters, suffix = m.group(1), m.group(2) or ""
        if letters in AS_WORDS:
            return m.group(0)
        if letters in SPELLED:
            self.counts["acronym_spelled"] += 1
            return self._spell(letters, "s" if suffix else "")
        return m.group(0)


def sound_class(word):
    w = word.lower()
    for dg, k in (("sh", "sh"), ("ch", "ch"), ("th", "th"), ("ph", "f"), ("wh", "w"), ("kn", "n"), ("wr", "r")):
        if w.startswith(dg):
            return "sibilant" if k in SIBILANT_STARTS else k
    c = w[0]
    if c in "aeiou":
        return None
    if c == "c":
        return "sibilant" if len(w) > 1 and w[1] in "eiy" else "k"
    if c in "kq":
        return "k"
    if c in "sz":
        return "sibilant"
    return c


def find_twisters(words):
    hits, i = [], 0
    while i + TWISTER_WINDOW <= len(words):
        window = words[i:i + TWISTER_WINDOW]
        classes = collections.Counter()
        for w in window:
            if len(w) > 2 and w.lower() not in STOP_SHORT and w.lower() not in NUMBER_WORDS:
                k = sound_class(w)
                if k:
                    classes[k] += 1
        if classes:
            k, n = classes.most_common(1)[0]
            if n >= TWISTER_MIN_HITS:
                hits.append((k, " ".join(window)))
                i += TWISTER_WINDOW
                continue
        i += 1
    return hits


def split_sentences(t):
    out, start = [], 0
    for m in SPLIT_RE.finditer(t):
        seg = t[start:m.end()].strip()
        if seg:
            out.append(seg)
        start = m.end()
    rest = t[start:].strip()
    if rest:
        out.append(rest)
    return out


def split_long(text, limit):
    pieces = []
    while len(text) > limit:
        window = text[:limit + 1]
        cut = -1
        for pat in (r"[;:]\s", r",\s", r"\s(?=(?:and|but|or|so|because|which|that)\s)", r"\s"):
            ends = [m.end() for m in re.finditer(pat, window) if limit * MIN_PIECE_FRACTION <= m.end() <= limit]
            if ends:
                cut = ends[-1]
                break
        if cut <= 0:
            cut = limit
        pieces.append(text[:cut].rstrip())
        text = text[cut:].lstrip()
    if text:
        pieces.append(text)
    return pieces


def count_words(plain):
    return len(WORD_RE.findall(plain))


def count_commas(plain):
    return len(re.findall(r"[,;:—–]", plain))


def timecode(sec):
    sec = int(round(sec))
    return "%d:%02d" % (sec // 60, sec % 60)


def read_paragraphs(raw):
    """Return [(first_line_number, text)]. Headings and bullets are their own paragraphs."""
    paras, cur, cur_line = [], [], 0

    def flush():
        nonlocal cur
        if cur:
            paras.append((cur_line, " ".join(cur)))
            cur = []
    for no, line in enumerate(raw.splitlines(), 1):
        s = line.strip()
        if not s:
            flush()
            continue
        heading = re.match(r"#{1,6}\s+(.*)", s)
        bullet = re.match(r"[-*+]\s+(.*)", s)
        if heading or bullet:
            flush()
            body = (heading or bullet).group(1)
            paras.append((no, body if re.search(r"[.!?:]$", body) else body + "."))
            continue
        if not cur:
            cur_line = no
        cur.append(s)
    flush()
    cleaned = []
    for no, text in paras:
        text = re.sub(r"\[([^\]]+)\]\((?:[^)]*)\)", r"\1", text)
        text = re.sub(r"(\*\*|__|\*|_)(?=\S)(.+?)(?<=\S)\1", r"\2", text)
        text = text.replace("`", "")
        cleaned.append((no, text))
    return cleaned


def load_lexicon(path):
    try:
        with open(path, encoding="utf-8-sig") as f:
            data = json.load(f)
    except (OSError, ValueError) as exc:
        raise ValueError("cannot read lexicon %s: %s" % (path, exc))
    if not isinstance(data, dict):
        raise ValueError("lexicon must be a JSON object mapping written form to spoken form")
    lex = {}
    for key, val in data.items():
        if not key.strip():
            raise ValueError("lexicon has an empty key")
        if isinstance(val, str):
            val = {"say": val}
        if not isinstance(val, dict) or not (val.get("say") or val.get("ipa")):
            raise ValueError("lexicon entry %r needs a string or an object with 'say' and/or 'ipa'" % key)
        lex[key] = {"say": val.get("say"), "ipa": val.get("ipa")}
    return lex


def check_delimiters(text):
    found = []
    straight = len(re.findall(r'(?<!\d)"', text))
    if straight % 2:
        found.append(("double_quote", "%d straight double quotes (odd count)" % straight))
    lo, lc = text.count("“"), text.count("”")
    if lo != lc:
        found.append(("curly_quote", "%d opening and %d closing curly quotes" % (lo, lc)))
    if text.count("(") != text.count(")"):
        found.append(("parenthesis", "%d '(' and %d ')'" % (text.count("("), text.count(")"))))
    if text.count("[") != text.count("]"):
        found.append(("bracket", "%d '[' and %d ']'" % (text.count("["), text.count("]"))))
    return found


def scripts_in(text):
    counts = collections.Counter()
    for ch in text:
        if ch.isalpha():
            name = unicodedata.name(ch, "").split(" ")[0] or "UNKNOWN"
            if name != "LATIN":
                counts[name] += 1
    return dict(counts)


def edge_strip(tok):
    return tok.strip(".,;:!?()\"'“”‘’")


def scan_unexpanded(text, line, found):
    """text has protected segments blanked out."""
    for m in re.finditer(r"\S+", text):
        tok = edge_strip(m.group(0))
        if not tok:
            continue
        kinds = []
        if re.search(r"\d", tok):
            kinds.append("digits")
        if any(c in SYMBOLS for c in tok):
            kinds.append("symbol")
        if not re.search(r"\d", tok) and re.search(r"(?<![A-Za-z])[A-Z]{2,}(?![a-z])", tok) and tok not in AS_WORDS:
            kinds.append("all_caps")
        for kind in kinds:
            key = (tok, kind)
            if key in found:
                found[key]["count"] += 1
            else:
                found[key] = {"token": tok, "kind": kind, "line": line, "count": 1}


def build(args, raw, lexicon):
    norm = Normalizer(lexicon)
    paragraphs = read_paragraphs(raw)
    sentences = []
    unexpanded = {}
    camel = {}
    delimiters, mixed, long_sentences, twisters = [], [], [], []
    ssml_paras = []
    plain_paras = []
    for pi, (line, text) in enumerate(paragraphs):
        norm.line = line
        for kind, detail in check_delimiters(text):
            delimiters.append({"line": line, "kind": kind, "detail": detail})
        sc = scripts_in(text)
        if sc:
            mixed.append({"line": line, "scripts": sc})
        spoken = norm.normalize(text)
        scan_unexpanded(PLACEHOLDER_RE.sub(" ", spoken), line, unexpanded)
        for m in re.finditer(r"\b[a-z]+[A-Z][A-Za-z]*\b", PLACEHOLDER_RE.sub(" ", spoken)):
            camel.setdefault(m.group(0), {"token": m.group(0), "kind": "mixed_case", "line": line})
        sents = split_sentences(spoken)
        plain_paras.append(norm.resolve(spoken, "plain"))
        ss = []
        for si, s in enumerate(sents):
            plain = norm.resolve(s, "plain")
            ssml = norm.resolve(s, "ssml")
            words = count_words(plain)
            if words > args.max_sentence_words:
                long_sentences.append({"line": line, "words": words, "starts": " ".join(plain.split()[:8])})
            # URLs, lexicon hits and spelled acronyms are skipped: "slash" and "dot" are not prose
            for segment in PLACEHOLDER_RE.split(s)[::2]:
                for sound, snippet in find_twisters(re.findall(r"[A-Za-z']+", segment)):
                    twisters.append({"line": line, "sound": sound, "text": snippet})
            sentences.append({"plain": plain, "words": words, "commas": count_commas(plain),
                              "para_end": si == len(sents) - 1, "line": line})
            ss.append(ssml)
        ssml_paras.append(ss)
    return norm, paragraphs, sentences, unexpanded, camel, delimiters, mixed, long_sentences, twisters, ssml_paras, plain_paras


def make_chunks(sentences, args):
    units = []
    for s in sentences:
        pieces = split_long(s["plain"], args.max_chars)
        for k, p in enumerate(pieces):
            last = k == len(pieces) - 1
            w = count_words(p)
            units.append({"text": p, "words": w, "commas": count_commas(p),
                          "pause": (args.paragraph_pause if s["para_end"] else args.sentence_pause) if last else 0.0,
                          "para_end": s["para_end"] and last, "ends_mid": not last, "starts_mid": k > 0})
    chunks, cur = [], None

    def close():
        nonlocal cur
        if cur:
            chunks.append(cur)
            cur = None
    for u in units:
        if cur is not None:
            sep = "\n\n" if cur["last_para_end"] else " "
            if len(cur["text"]) + len(sep) + len(u["text"]) > args.max_chars or cur["ends_mid"]:
                close()
        if cur is None:
            cur = {"text": u["text"], "units": [u], "last_para_end": u["para_end"], "ends_mid": u["ends_mid"],
                   "starts_mid": u["starts_mid"]}
        else:
            sep = "\n\n" if cur["last_para_end"] else " "
            cur["text"] += sep + u["text"]
            cur["units"].append(u)
            cur["last_para_end"] = u["para_end"]
            cur["ends_mid"] = u["ends_mid"]
    close()
    out = []
    for i, c in enumerate(chunks, 1):
        words = sum(u["words"] for u in c["units"])
        sec = words / args.wpm * 60 + sum(u["commas"] * args.comma_pause + u["pause"] for u in c["units"])
        out.append({"id": i, "text": c["text"], "chars": len(c["text"]), "words": words,
                    "est_seconds": round(sec, 2), "starts_mid_sentence": c["starts_mid"],
                    "ends_mid_sentence": c["ends_mid"]})
    return out, units


def add_comma_breaks(ssml, ms):
    parts = re.split(r"(<[^>]+>)", ssml)
    return "".join(p if p.startswith("<") else re.sub(r"([,;:])", r'\1<break time="%dms"/>' % ms, p) for p in parts)


def build_ssml(ssml_paras, args):
    lines = ["<speak>"]
    for pi, ss in enumerate(ssml_paras):
        bits = []
        for si, s in enumerate(ss):
            if args.explicit_breaks:
                s = add_comma_breaks(s, int(round(args.comma_pause * 1000)))
            bits.append("<s>" + s + "</s>")
            if args.explicit_breaks and si < len(ss) - 1:
                bits.append('<break time="%dms"/>' % int(round(args.sentence_pause * 1000)))
        lines.append("<p>" + " ".join(bits) + "</p>")
        if pi < len(ssml_paras) - 1:
            lines.append('<break time="%dms"/>' % int(round(args.paragraph_pause * 1000)))
    lines.append("</speak>")
    return "\n".join(lines) + "\n"


def main(argv=None):
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
            sys.stderr.reconfigure(encoding="utf-8")
        except (OSError, ValueError):
            pass
    ap = argparse.ArgumentParser(description="Prepare an English script for text-to-speech or narration.")
    ap.add_argument("script")
    ap.add_argument("--max-chars", type=int, required=True, help="the target tool's per-request character limit")
    ap.add_argument("--wpm", type=float, default=155.0)
    ap.add_argument("--lexicon")
    ap.add_argument("--max-sentence-words", type=int, default=DEFAULT_MAX_SENTENCE_WORDS)
    ap.add_argument("--comma-pause", type=float, default=DEFAULT_COMMA_PAUSE)
    ap.add_argument("--sentence-pause", type=float, default=DEFAULT_SENTENCE_PAUSE)
    ap.add_argument("--paragraph-pause", type=float, default=DEFAULT_PARAGRAPH_PAUSE)
    ap.add_argument("--explicit-breaks", action="store_true", help="write comma and sentence breaks into the SSML")
    ap.add_argument("--out-dir")
    args = ap.parse_args(argv)
    if not WPM_MIN_ACCEPT <= args.wpm <= WPM_MAX_ACCEPT:
        print("error: --wpm must be between %d and %d" % (WPM_MIN_ACCEPT, WPM_MAX_ACCEPT), file=sys.stderr)
        return 2
    if args.max_chars < 50:
        print("error: --max-chars must be at least 50", file=sys.stderr)
        return 2
    try:
        with open(args.script, encoding="utf-8-sig") as f:
            raw = f.read()
    except (OSError, UnicodeDecodeError) as exc:
        print("error: cannot read %s as UTF-8 text: %s" % (args.script, exc), file=sys.stderr)
        return 2
    if not raw.strip():
        print("error: %s is empty" % args.script, file=sys.stderr)
        return 2
    try:
        lexicon = load_lexicon(args.lexicon) if args.lexicon else {}
    except ValueError as exc:
        print("error: %s" % exc, file=sys.stderr)
        return 2

    (norm, paragraphs, sentences, unexpanded, camel, delimiters, mixed, long_sentences, twisters,
     ssml_paras, plain_paras) = build(args, raw, lexicon)
    chunks, units = make_chunks(sentences, args)

    total_words = sum(c["words"] for c in chunks)
    pauses = sum(u["commas"] * args.comma_pause + u["pause"] for u in units)
    est = sum(c["est_seconds"] for c in chunks)
    over = [c["id"] for c in chunks if c["chars"] > args.max_chars]
    mid = [c["id"] for c in chunks if c["ends_mid_sentence"]]
    unexp_list = sorted(unexpanded.values(), key=lambda d: (d["line"], d["token"], d["kind"]))
    advisories = []
    if not WPM_LOW <= args.wpm <= WPM_HIGH:
        advisories.append("wpm_outside_140_170")
    blockers = [name for name, lst in (("unexpanded", unexp_list), ("mixed_script", mixed),
                                       ("unmatched_delimiters", delimiters), ("chunks_over_limit", over),
                                       ("mid_sentence_breaks", mid)) if lst]
    for name, lst in (("long_sentences", long_sentences), ("tongue_twisters", twisters),
                      ("long_urls", norm.long_urls), ("notes", norm.notes),
                      ("mixed_case_tokens", list(camel.values()))):
        if lst:
            advisories.append(name)
    report = {
        "schema_version": SCHEMA_VERSION,
        "tool": "prep_voiceover",
        "input": os.path.basename(args.script),
        "settings": {"wpm": args.wpm, "max_chars": args.max_chars, "max_sentence_words": args.max_sentence_words,
                     "comma_pause": args.comma_pause, "sentence_pause": args.sentence_pause,
                     "paragraph_pause": args.paragraph_pause, "lexicon_entries": len(lexicon)},
        "verdict": "review" if blockers else "ready",
        "blockers": blockers,
        "advisories": advisories,
        "totals": {"paragraphs": len(paragraphs), "sentences": len(sentences), "words": total_words,
                   "spoken_chars": sum(len(p) for p in plain_paras), "chunks": len(chunks),
                   "est_seconds": round(est, 2), "est_timecode": timecode(est),
                   "est_seconds_at_140_wpm": round(total_words / WPM_LOW * 60 + pauses, 2),
                   "est_seconds_at_170_wpm": round(total_words / WPM_HIGH * 60 + pauses, 2)},
        "expansions": dict(sorted(norm.counts.items())),
        "chunks": [{k: v for k, v in c.items() if k != "text"} for c in chunks],
        "unexpanded": unexp_list,
        "mixed_script": mixed,
        "unmatched_delimiters": delimiters,
        "chunks_over_limit": over,
        "mid_sentence_breaks": mid,
        "long_sentences": long_sentences,
        "tongue_twisters": twisters,
        "long_urls": norm.long_urls,
        "mixed_case_tokens": sorted(camel.values(), key=lambda d: (d["line"], d["token"])),
        "notes": norm.notes,
    }
    if args.out_dir:
        try:
            os.makedirs(args.out_dir, exist_ok=True)
            with open(os.path.join(args.out_dir, "spoken.txt"), "w", encoding="utf-8", newline="\n") as f:
                f.write("\n\n".join(plain_paras) + "\n")
            with open(os.path.join(args.out_dir, "chunks.jsonl"), "w", encoding="utf-8", newline="\n") as f:
                for c in chunks:
                    f.write(json.dumps(c, ensure_ascii=False) + "\n")
            with open(os.path.join(args.out_dir, "spoken.ssml"), "w", encoding="utf-8", newline="\n") as f:
                f.write(build_ssml(ssml_paras, args))
        except OSError as exc:
            print("error: cannot write to %s: %s" % (args.out_dir, exc), file=sys.stderr)
            return 2
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 1 if blockers else 0


if __name__ == "__main__":
    sys.exit(main())
