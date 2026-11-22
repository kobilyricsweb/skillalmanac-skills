#!/usr/bin/env python3
"""Format reference entries from BibTeX or CSL-JSON into APA, MLA, Chicago or IEEE.

Usage:
    python format_refs.py format SOURCE --style apa|mla|chicago|ieee [--out references.txt] [--plain]
    python format_refs.py rules --style apa|mla|chicago|ieee

SOURCE is a .bib file (BibTeX) or a .json file (CSL-JSON: a list of items, or
{"items": [...]}). Reads only SOURCE. Writes only the file named by --out, and
only when --out is given; without it nothing is written (that is the dry run).
Prints one JSON report to stdout (UTF-8).

The script never looks anything up and never invents a value. A field that is
absent stays absent: the entry is marked "incomplete" and lists what is missing.
It does not know whether a source exists, and it does not read manuscripts.

Exit codes: 0 every entry complete, no duplicates; 1 at least one entry is
incomplete, unsupported or duplicated; 2 usage, unreadable or empty input.
"""
import argparse
import json
import os
import re
import sys
import unicodedata

STYLE_VERSIONS = {
    "apa": "APA 7th edition rules (2019 manual); AI-tool pattern follows the APA 7 software form",
    "mla": "MLA 9th edition rules (2021 handbook)",
    "chicago": "Chicago author-date, 17th edition rules; 18th edition differences are not implemented",
    "ieee": "IEEE reference guide form (2018 edition, numeric [n] order of input)",
}
TYPES = ("article", "book", "chapter", "web", "report", "software")

BIB_TYPES = {
    "article": "article", "book": "book", "incollection": "chapter", "inbook": "chapter",
    "online": "web", "electronic": "web", "misc": "web", "techreport": "report",
    "report": "report", "software": "software",
}
CSL_TYPES = {
    "article-journal": "article", "article": "article", "book": "book", "chapter": "chapter",
    "webpage": "web", "post-webpage": "web", "report": "report", "software": "software",
}

# Required fields per style and type. "author_or_publisher" means either one is enough;
# "author" is also met by editors for books. Anything missing here is reported, never filled.
REQUIRED = {
    "apa": {
        "article": ["author", "year", "title", "container", "volume"],
        "book": ["author", "year", "title", "publisher"],
        "chapter": ["author", "year", "title", "container", "publisher"],
        "web": ["title", "url"],
        "report": ["author_or_publisher", "year", "title"],
        "software": ["author_or_publisher", "year", "title", "url"],
    },
    "mla": {
        "article": ["author", "title", "container", "year"],
        "book": ["author", "title", "publisher", "year"],
        "chapter": ["author", "title", "container", "publisher", "year"],
        "web": ["title", "url"],
        "report": ["author_or_publisher", "title", "year"],
        "software": ["title", "description", "author_or_publisher", "year"],
    },
    "chicago": {
        "article": ["author", "year", "title", "container", "volume"],
        "book": ["author", "year", "title", "publisher"],
        "chapter": ["author", "year", "title", "container", "publisher"],
        "web": ["title", "url"],
        "report": ["author_or_publisher", "year", "title"],
        "software": ["author_or_publisher", "year", "title"],
    },
    "ieee": {
        "article": ["author", "title", "container", "year", "volume"],
        "book": ["author", "title", "publisher", "year"],
        "chapter": ["author", "title", "container", "publisher", "year"],
        "web": ["title", "url", "accessed"],
        "report": ["author_or_publisher", "title", "year"],
        "software": ["author_or_publisher", "title", "year", "url", "accessed"],
    },
}
# Recommended: absence is reported but does not make the entry incomplete.
RECOMMENDED = {
    "article": ["pages", "doi_or_url"],
    "book": [],
    "chapter": ["pages", "editor"],
    "web": ["author", "year"],
    "report": ["url"],
    "software": ["version"],
}
EXTRA_RECOMMENDED = {
    ("apa", "software"): ["genre"],
    ("mla", "software"): ["version", "url"],
    ("mla", "article"): ["volume"],
    ("chicago", "book"): ["place"],
    ("ieee", "book"): ["place"],
}

MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August",
          "September", "October", "November", "December"]
MLA_MONTHS = ["Jan.", "Feb.", "Mar.", "Apr.", "May", "June", "July", "Aug.", "Sept.", "Oct.", "Nov.", "Dec."]
IEEE_MONTHS = ["Jan.", "Feb.", "Mar.", "Apr.", "May", "Jun.", "Jul.", "Aug.", "Sep.", "Oct.", "Nov.", "Dec."]

# APA lists up to 20 authors; from 21 it lists 19, an ellipsis and the last author.
APA_MAX = 20
# Chicago lists up to 10 authors in the reference list, otherwise the first 7 plus et al.
CHICAGO_MAX, CHICAGO_KEEP = 10, 7
# IEEE lists up to 6 authors, otherwise the first author plus et al.
IEEE_MAX = 6
DOI_RE = re.compile(r"^10\.\d{4,9}/\S+$")
YEAR_MIN, YEAR_MAX = 1400, 2100  # outside this range a year is almost certainly a typo

COMBINING = {"'": "\u0301", "`": "\u0300", '"': "\u0308", "^": "\u0302", "~": "\u0303"}


# ---------------------------------------------------------------- parsing helpers
def clean(s):
    """Strip BibTeX braces and simple LaTeX accents; collapse whitespace."""
    if s is None:
        return ""
    s = re.sub(r"\\([`'\"^~])\{?\\?([A-Za-z])\}?",
               lambda m: unicodedata.normalize("NFC", m.group(2) + COMBINING[m.group(1)]), s)
    s = s.replace("\\&", "&").replace("\\_", "_").replace("\\%", "%")
    s = s.replace("{", "").replace("}", "")
    return re.sub(r"\s+", " ", s).strip()


def read_value(text, pos):
    parts = []
    while True:
        while pos < len(text) and text[pos] in " \t\r\n":
            pos += 1
        if pos >= len(text):
            break
        c = text[pos]
        if c == "{":
            depth, start = 1, pos + 1
            pos += 1
            while pos < len(text) and depth:
                depth += (text[pos] == "{") - (text[pos] == "}")
                pos += 1
            parts.append(text[start:pos - 1])
        elif c == '"':
            start, depth = pos + 1, 0
            pos += 1
            while pos < len(text) and not (text[pos] == '"' and depth == 0):
                depth += (text[pos] == "{") - (text[pos] == "}")
                pos += 1
            parts.append(text[start:pos])
            pos += 1
        else:
            m = re.compile(r"[^,}\s#]+").match(text, pos)
            if not m:
                break
            parts.append(m.group(0))
            pos = m.end()
        while pos < len(text) and text[pos] in " \t\r\n":
            pos += 1
        if pos < len(text) and text[pos] == "#":
            pos += 1
            continue
        break
    return "".join(parts), pos


def parse_bibtex(text):
    items = []
    pos = 0
    head = re.compile(r"@(\w+)\s*[{(]")
    while True:
        m = head.search(text, pos)
        if not m:
            break
        kind, j = m.group(1).lower(), m.end()
        if kind in ("comment", "preamble", "string"):
            depth, pos = 1, j
            while pos < len(text) and depth:
                depth += (text[pos] == "{") - (text[pos] == "}")
                pos += 1
            continue
        comma = text.find(",", j)
        if comma < 0:
            break
        key, pos, fields = text[j:comma].strip(), comma + 1, {}
        while pos < len(text):
            while pos < len(text) and text[pos] in " \t\r\n,":
                pos += 1
            if pos >= len(text) or text[pos] in "})":
                pos += 1
                break
            fm = re.compile(r"([A-Za-z_][\w\-]*)\s*=").match(text, pos)
            if not fm:
                pos += 1
                continue
            value, pos = read_value(text, fm.end())
            fields[fm.group(1).lower()] = value
        items.append({"_bib": kind, "id": key, "fields": fields})
    return items


def split_names(raw):
    """Split a BibTeX author string on top-level ' and '."""
    out, depth, cur, i = [], 0, "", 0
    while i < len(raw):
        c = raw[i]
        depth += (c == "{") - (c == "}")
        if depth == 0 and re.match(r"\s+and\s+", raw[i:], re.I) and cur.strip():
            out.append(cur.strip())
            i += re.match(r"\s+and\s+", raw[i:], re.I).end()
            cur = ""
            continue
        cur += c
        i += 1
    if cur.strip():
        out.append(cur.strip())
    return out


def parse_name(raw):
    raw = raw.strip()
    if raw.startswith("{") and raw.endswith("}") and "," not in raw[1:-1].split("{")[0] and raw.count("{") == 1:
        return {"literal": clean(raw)}
    flat = clean(raw)
    if "," in raw.replace("{", "").replace("}", ""):
        family, _, given = flat.partition(",")
        return {"family": family.strip(), "given": given.strip().lstrip(",").strip()}
    toks = flat.split()
    if len(toks) == 1:
        return {"literal": toks[0]}
    k = len(toks) - 1
    while k > 1 and toks[k - 1][:1].islower():
        k -= 1
    return {"family": " ".join(toks[k:]), "given": " ".join(toks[:k])}


def parse_date_text(s):
    s = (s or "").strip()
    m = re.match(r"^(\d{4})(?:-(\d{1,2}))?(?:-(\d{1,2}))?$", s)
    if m:
        return int(m.group(1)), int(m.group(2) or 0), int(m.group(3) or 0)
    return None


def month_num(v):
    v = (v or "").strip().lower()
    if v.isdigit() and 1 <= int(v) <= 12:
        return int(v)
    for i, name in enumerate(MONTHS):
        if v[:3] and name.lower().startswith(v[:3]):
            return i + 1
    return 0


def blank():
    return {"authors": [], "editors": [], "year": "", "month": 0, "day": 0, "title": "", "container": "",
            "volume": "", "issue": "", "pages": "", "edition": "", "publisher": "", "place": "",
            "doi": "", "url": "", "accessed": None, "number": "", "version": "", "genre": "",
            "description": ""}


def from_bib(item):
    f = {k: v for k, v in item["fields"].items()}
    e = blank()
    e["id"] = item["id"]
    e["type"] = BIB_TYPES.get(item["_bib"], "")
    e["raw_type"] = item["_bib"]
    e["authors"] = [parse_name(n) for n in split_names(f.get("author", ""))]
    e["editors"] = [parse_name(n) for n in split_names(f.get("editor", ""))]
    d = parse_date_text(f.get("date", ""))
    if d:
        e["year"], e["month"], e["day"] = str(d[0]), d[1], d[2]
    if f.get("year"):
        e["year"] = clean(f["year"])
    if f.get("month"):
        e["month"] = month_num(clean(f["month"])) or e["month"]
    if f.get("day"):
        e["day"] = int(f["day"]) if f["day"].strip().isdigit() else e["day"]
    e["title"] = clean(f.get("title"))
    e["container"] = clean(f.get("journal") or f.get("journaltitle") or f.get("booktitle")
                           or (f.get("website") or f.get("organization") if e["type"] == "web" else ""))
    for src, dst in (("volume", "volume"), ("pages", "pages"), ("edition", "edition"), ("publisher", "publisher"),
                     ("address", "place"), ("location", "place"), ("doi", "doi"), ("url", "url"),
                     ("version", "version"), ("genre", "genre"), ("description", "description"),
                     ("prompt", "description")):
        if f.get(src) and not e[dst]:
            e[dst] = clean(f[src])
    if e["type"] == "report" and not e["publisher"]:
        e["publisher"] = clean(f.get("institution"))
    if e["type"] == "article":
        e["issue"] = clean(f.get("number") or f.get("issue"))
    else:
        e["number"] = clean(f.get("number"))
        e["issue"] = clean(f.get("issue"))
    ua = parse_date_text(f.get("urldate") or f.get("accessed") or "")
    e["accessed"] = ua
    return e


def csl_date(v):
    if not isinstance(v, dict):
        return None
    dp = v.get("date-parts")
    if dp and dp[0] and str(dp[0][0]).isdigit():
        p = [int(x) for x in dp[0] if str(x).isdigit()]
        return (p[0], p[1] if len(p) > 1 else 0, p[2] if len(p) > 2 else 0)
    return parse_date_text(v.get("raw") or v.get("literal") or "")


def csl_names(lst):
    out = []
    for n in lst or []:
        if not isinstance(n, dict):
            continue
        if n.get("literal"):
            out.append({"literal": clean(n["literal"])})
        elif n.get("family"):
            out.append({"family": clean(n["family"]), "given": clean(n.get("given", ""))})
    return out


def from_csl(item):
    e = blank()
    e["id"] = str(item.get("id", ""))
    e["raw_type"] = str(item.get("type", ""))
    e["type"] = CSL_TYPES.get(e["raw_type"], "")
    e["authors"] = csl_names(item.get("author"))
    e["editors"] = csl_names(item.get("editor"))
    d = csl_date(item.get("issued"))
    if d:
        e["year"], e["month"], e["day"] = str(d[0]), d[1], d[2]
    e["accessed"] = csl_date(item.get("accessed"))
    for src, dst in (("title", "title"), ("container-title", "container"), ("volume", "volume"),
                     ("issue", "issue"), ("page", "pages"), ("edition", "edition"), ("publisher", "publisher"),
                     ("publisher-place", "place"), ("DOI", "doi"), ("URL", "url"), ("number", "number"),
                     ("version", "version"), ("genre", "genre"), ("note", "")):
        if dst and item.get(src) is not None:
            e[dst] = clean(str(item[src]))
    e["description"] = clean(str(item.get("description") or item.get("prompt") or ""))
    return e


def load(path):
    with open(path, "rb") as fh:
        raw = fh.read()
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise ValueError("file is not valid UTF-8; re-save it as UTF-8")
    if not text.strip():
        raise ValueError("file is empty")
    if path.lower().endswith(".json"):
        try:
            data = json.loads(text)
        except json.JSONDecodeError as exc:
            raise ValueError("invalid JSON: " + str(exc))
        if isinstance(data, dict):
            data = data.get("items", [])
        if not isinstance(data, list) or not data:
            raise ValueError("CSL-JSON must be a non-empty list of items (or an object with an items list)")
        return [from_csl(i) for i in data if isinstance(i, dict)]
    items = parse_bibtex(text)
    if not items:
        raise ValueError("no BibTeX entries found")
    return [from_bib(i) for i in items]


# ---------------------------------------------------------------- name and text helpers
def initials(given):
    out = []
    for tok in given.replace(".", ". ").split():
        parts = [p for p in tok.split("-") if p.strip(".")]
        if parts:
            out.append("-".join(p.strip(".")[0].upper() + "." for p in parts))
    return " ".join(out)


def inv(n, init):
    if n.get("literal"):
        return n["literal"]
    g = initials(n["given"]) if init else n["given"]
    return n["family"] + (", " + g if g else "")


def nat(n, init):
    if n.get("literal"):
        return n["literal"]
    g = initials(n["given"]) if init else n["given"]
    return (g + " " if g else "") + n["family"]


def fam(n):
    return n.get("literal") or n["family"]


def end(s):
    s = s.strip()
    return s if not s or s[-1] in ".?!" else s + "."


def endq(s):
    """A quoted title: period or the title's own ?/! goes inside the quotes."""
    s = s.strip()
    return '"' + (s if s[-1:] in ".?!" else s + ".") + '"'


def endq_comma(s):
    return '"' + s.strip() + ',"'


def ordinal(n):
    n = int(n)
    suf = "th" if 10 <= n % 100 <= 20 else {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suf}"


def edition_text(ed):
    ed = ed.strip()
    if not ed or ed == "1":
        return ""
    if ed.isdigit():
        return ordinal(ed) + " ed."
    ed = re.sub(r"\s*(ed\.?|edition)$", "", ed, flags=re.I)
    return ed + " ed."


def pages_norm(p):
    return re.sub(r"\s*(--|-|\u2014)\s*", "\u2013", p.strip())


def page_label(p, plural_prefix="pp. ", single_prefix="p. ", art_prefix=""):
    if not p:
        return ""
    if re.match(r"^[A-Za-z]+\d+$", p):  # article number such as e0234, not a page
        return art_prefix + p
    return (plural_prefix if "\u2013" in p else single_prefix) + p


def report_no(num, label):
    num = num.strip()
    if not num:
        return ""
    return f"{label} {num}" if num[0].isdigit() else num


def version_text(v):
    v = v.strip()
    if not v:
        return ""
    if re.match(r"^v?\d[\d.]*$", v):
        return "Version " + v.lstrip("vV")
    return v if v.lower().endswith("version") else v + " version"


def join_names(items, conj, comma2=False, serial=True):
    if len(items) == 1:
        return items[0]
    if len(items) == 2:
        return f"{items[0]}{',' if comma2 else ''} {conj} {items[1]}"
    return ", ".join(items[:-1]) + (", " if serial else " ") + f"{conj} {items[-1]}"


def link_of(e, mla=False):
    if e["doi"] and DOI_RE.match(e["doi"]):
        return "https://doi.org/" + e["doi"]
    if e["url"]:
        return re.sub(r"^https?://", "", e["url"]) if mla else e["url"]
    return ""


def norm_doi(d):
    d = d.strip()
    d = re.sub(r"^(https?://(dx\.)?doi\.org/|doi:\s*)", "", d, flags=re.I)
    return d


# ---------------------------------------------------------------- author strings per style
def apa_names(names):
    if not names:
        return ""
    items = [inv(n, True) for n in names]
    if len(items) > APA_MAX:
        return ", ".join(items[:19]) + ", . . . " + items[-1]
    if len(items) == 1:
        return items[0]
    return ", ".join(items[:-1]) + ", & " + items[-1]


def mla_names(names):
    if not names:
        return ""
    if len(names) >= 3:
        return inv(names[0], False) + ", et al."
    if len(names) == 1:
        return inv(names[0], False)
    return inv(names[0], False) + ", and " + nat(names[1], False)


def chicago_names(names):
    if not names:
        return ""
    more = len(names) > CHICAGO_MAX
    use = names[:CHICAGO_KEEP] if more else names
    items = [inv(use[0], False)] + [nat(n, False) for n in use[1:]]
    if more:
        return ", ".join(items) + ", et al."
    if len(items) == 1:
        return items[0]
    if len(items) == 2:
        return items[0] + (", and " if not use[0].get("literal") else " and ") + items[1]
    return ", ".join(items[:-1]) + ", and " + items[-1]


def ieee_names(names):
    if not names:
        return ""
    if len(names) > IEEE_MAX:
        return nat(names[0], True) + " et al."
    return join_names([nat(n, True) for n in names], "and")


def editors_text(style, eds):
    if not eds:
        return ""
    if style == "apa":
        s = join_names([nat(n, True) for n in eds], "&")
        return s + (" (Eds.)" if len(eds) > 1 else " (Ed.)")
    if style == "mla":
        if len(eds) >= 3:
            return "edited by " + nat(eds[0], False) + ", et al."
        return "edited by " + join_names([nat(n, False) for n in eds], "and")
    if style == "chicago":
        return "edited by " + join_names([nat(n, False) for n in eds], "and")
    return join_names([nat(n, True) for n in eds], "and") + (", Eds." if len(eds) > 1 else ", Ed.")


# ---------------------------------------------------------------- dates
def date_apa(e, full=True):
    y = e.get("year_s") or ("n.d." if e["type"] == "web" else "")
    if full and e["month"] and e["year"]:
        return f"{y}, {MONTHS[e['month'] - 1]}" + (f" {e['day']}" if e["day"] else "")
    return y


def date_mla(e):
    if not e["year"]:
        return ""
    parts = []
    if e["day"] and e["month"]:
        parts.append(str(e["day"]))
    if e["month"]:
        parts.append(MLA_MONTHS[e["month"] - 1])
    return " ".join(parts + [e["year"]])


def date_ieee(e):
    if not e["year"]:
        return ""
    return (IEEE_MONTHS[e["month"] - 1] + " " if e["month"] else "") + e["year"]


def acc_text(style, a):
    if not a:
        return ""
    y, m, d = a
    if style == "mla":
        return " ".join(([str(d)] if d and m else []) + ([MLA_MONTHS[m - 1]] if m else []) + [str(y)])
    if style == "ieee":
        return (IEEE_MONTHS[m - 1] + " " if m else "") + (f"{d}, " if d and m else "") + str(y)
    return (MONTHS[m - 1] + " " if m else "") + (f"{d}, " if d and m else "") + str(y)


# ---------------------------------------------------------------- formatters
def italic(s, plain):
    return s if plain or not s else "*" + s + "*"


def it_end(s, plain):
    return italic(s, plain) + ("" if s[-1:] in ".?!" else ".")


def fmt_apa(e, plain):
    t, ty = e["title"], e["type"]
    names = apa_names(e["authors"]) or (editors_text("apa", e["editors"]) if ty == "book" else "")
    y = date_apa(e, full=ty in ("web",))
    link = link_of(e)
    if ty == "software" and not names:
        names = e["publisher"]
    lead_date = f"({y})." if y else ""
    out = []
    if ty == "article":
        loc = [italic(e["container"], plain)] if e["container"] else []
        v = italic(e["volume"], plain) if e["volume"] else ""
        if e["issue"]:
            v += f"({e['issue']})"
        if v:
            loc.append(v)
        if e["pages"]:
            loc.append(e["pages"])
        out = [end(names), lead_date, end(t)] if names else [end(t), lead_date]
        out += [", ".join(loc) + "." if loc else "", link]
    elif ty == "book":
        ed = edition_text(e["edition"])
        title = (italic(t, plain) + f" ({ed}).") if ed else it_end(t, plain)
        out = ([end(names)] if names else [])
        out += [lead_date, title] if names else [title, lead_date]
        pub = e["publisher"] if e["publisher"] and e["publisher"] != names.rstrip(".") else ""
        out += [end(pub), link]
    elif ty == "chapter":
        parts = []
        if edition_text(e["edition"]):
            parts.append(edition_text(e["edition"]))
        if e["pages"]:
            parts.append(page_label(e["pages"]))
        eds = editors_text("apa", e["editors"])
        inpart = "In " + (eds + ", " if eds else "") + italic(e["container"], plain)
        inpart += (" (" + ", ".join(parts) + ")" if parts else "") + "."
        out = ([end(names), lead_date, end(t)] if names else [end(t), lead_date])
        out += [inpart, end(e["publisher"]), link]
    elif ty == "web":
        site = e["container"] if e["container"] and e["container"] != names.rstrip(".") else ""
        out = ([end(names), lead_date, it_end(t, plain)] if names else [it_end(t, plain), lead_date])
        out += [end(site)]
        if e["accessed"]:
            out += [f"Retrieved {acc_text('apa', e['accessed'])}, from {link}" if link else ""]
        else:
            out += [link]
    elif ty == "report":
        num = report_no(e["number"], "Report No.")
        title = italic(t, plain) + (f" ({num})." if num else ("" if t[-1:] in ".?!" else "."))
        pub = e["publisher"] if e["publisher"] and e["publisher"] != names.rstrip(".") else ""
        out = ([end(names), lead_date, title] if names else [title, lead_date]) + [end(pub), link]
    else:  # software, including AI tools
        v = version_text(e["version"])
        title = italic(t, plain) + (f" ({v})" if v else "") + (f" [{e['genre']}]" if e["genre"] else "") + "."
        out = ([end(names), lead_date, title] if names else [title, lead_date]) + [link]
    return " ".join(p for p in out if p)


def fmt_mla(e, plain):
    t, ty = e["title"], e["type"]
    names = mla_names(e["authors"]) or (mla_names(e["editors"]) if ty == "book" else "")
    link = link_of(e, mla=True)
    d = date_mla(e)
    head = [end(names)] if names else []
    if ty == "article":
        items = [italic(e["container"], plain), f"vol. {e['volume']}" if e["volume"] else "",
                 f"no. {e['issue']}" if e["issue"] else "", d, page_label(e["pages"]), link]
        return " ".join(head + [endq(t), end(", ".join(i for i in items if i))])
    if ty == "book":
        items = [edition_text(e["edition"]), e["publisher"], e["year"], link]
        return " ".join(head + [it_end(t, plain), end(", ".join(i for i in items if i))])
    if ty == "chapter":
        items = [italic(e["container"], plain), editors_text("mla", e["editors"]), edition_text(e["edition"]),
                 e["publisher"], e["year"], page_label(e["pages"]), link]
        return " ".join(head + [endq(t), end(", ".join(i for i in items if i))])
    if ty == "web":
        items = [italic(e["container"] or e["publisher"], plain), d, link]
        s = " ".join(head + [endq(t), end(", ".join(i for i in items if i))])
        if e["accessed"]:
            s += f" Accessed {acc_text('mla', e['accessed'])}."
        return s
    if ty == "report":
        items = [report_no(e["number"], "Report no."), e["publisher"] if e["publisher"] != names.rstrip(".") else "", e["year"], link]
        return " ".join(head + [it_end(t, plain), end(", ".join(i for i in items if i))])
    pub = e["publisher"] or mla_names(e["authors"])
    items = [italic(t, plain), version_text(e["version"]), pub, d, link]
    prompt = f'"{e["description"].rstrip(".")}" prompt.' if e["description"] else ""
    return " ".join(p for p in [prompt, end(", ".join(i for i in items if i))] if p)


def fmt_chicago(e, plain):
    t, ty = e["title"], e["type"]
    names = chicago_names(e["authors"]) or (chicago_names(e["editors"]) if ty == "book" else "")
    if ty == "software" and not names:
        names = e["publisher"]
    y = e.get("year_s") or ("n.d." if ty == "web" else "")
    link = link_of(e)
    link = end(link) if link else ""
    title_first = not names and ty in ("article", "chapter", "web")
    lead = ([end(names)] if names else []) + ([] if title_first or not y else [end(y)])
    pubplace = ": ".join(p for p in [e["place"], e["publisher"]] if p)
    if ty == "article":
        c = italic(e["container"], plain) + (" " + e["volume"] if e["volume"] else "")
        c += f" ({e['issue']})" if e["issue"] else ""
        c += f": {e['pages']}" if e["pages"] else ""
        return " ".join(lead + [endq(t)] + ([end(y)] if title_first and y else []) + [end(c) if e["container"] else "", link])
    if ty == "book":
        return " ".join(lead + [it_end(t, plain), end(edition_text(e["edition"])), end(pubplace), link])
    if ty == "chapter":
        inp = "In " + italic(e["container"], plain)
        extra = [editors_text("chicago", e["editors"]), e["pages"]]
        inp += ", " + ", ".join(x for x in extra if x) if any(extra) else ""
        return " ".join(lead + [endq(t)] + ([end(y)] if title_first and y else []) + [end(inp), end(pubplace), link])
    if ty == "web":
        acc = f"Accessed {acc_text('chicago', e['accessed'])}." if e["accessed"] else ""
        return " ".join(lead + [endq(t)] + ([end(y)] if title_first and y else []) + [end(e["container"]), acc, link])
    if ty == "report":
        pp = pubplace if e["publisher"] != names else ": ".join(p for p in [e["place"]] if p)
        return " ".join(lead + [it_end(t, plain), end(report_no(e["number"], "Report No.")), end(pp), link])
    return " ".join(lead + [it_end(t, plain), end(f"Version {e['version']}") if e["version"] else "",
                            end(e["publisher"]) if e["publisher"] and e["publisher"] != names else "", link])


def fmt_ieee(e, plain):
    t, ty = e["title"], e["type"]
    names = ieee_names(e["authors"]) or (ieee_names(e["editors"]) if ty == "book" else "")
    if ty == "software" and not names:
        names = e["publisher"]
    d = date_ieee(e)
    acc = acc_text("ieee", e["accessed"])
    url = e["url"]
    doi = "doi: " + e["doi"] if e["doi"] and DOI_RE.match(e["doi"]) else ""
    online = (f"Accessed: {acc}. " if acc else "") + (f"[Online]. Available: {url}" if url else "")
    head = names + "," if names else ""
    if ty == "article":
        items = [italic(e["container"], plain), f"vol. {e['volume']}" if e["volume"] else "",
                 f"no. {e['issue']}" if e["issue"] else "", page_label(e["pages"], art_prefix="Art. no. "), d, doi]
        s = " ".join(p for p in [head, endq_comma(t), end(", ".join(i for i in items if i))] if p)
        return s + (" " + online if url and not doi else "")
    if ty == "book":
        pp = f"{e['place']}: {e['publisher']}" if e["place"] else e["publisher"]
        ed = edition_text(e["edition"])
        return " ".join(p for p in [head, italic(t, plain) + ("," if ed else "."), ed,
                                    end(pp + (", " + e["year"] if e["year"] else ""))] if p)
    if ty == "chapter":
        pp = f"{e['place']}: {e['publisher']}" if e["place"] else e["publisher"]
        tail = ", ".join(x for x in [pp, e["year"], page_label(e["pages"])] if x)
        mid = ", ".join(x for x in [italic(e["container"], plain), editors_text("ieee", e["editors"])] if x)
        return " ".join(p for p in [head, endq_comma(t) + " in " + end(mid), end(tail)] if p)
    if ty == "web":
        return " ".join(p for p in [head, endq_comma(t), end(e["container"]), online] if p)
    if ty == "report":
        items = [e["publisher"] if e["publisher"] != names else "", e["place"], report_no(e["number"], "Rep."), e["year"]]
        return " ".join(p for p in [head, endq_comma(t), end(", ".join(i for i in items if i)), online] if p)
    v = version_text(e["version"])
    items = [v, e["publisher"] if e["publisher"] and e["publisher"] != names else "", e["year"]]
    return " ".join(p for p in [head, endq_comma(t), end(", ".join(i for i in items if i)), online] if p)


FORMATTERS = {"apa": fmt_apa, "mla": fmt_mla, "chicago": fmt_chicago, "ieee": fmt_ieee}


# ---------------------------------------------------------------- in-text strings
def short_title(t):
    w = t.split()
    return " ".join(w[:4]) + ("..." if len(w) > 4 else "")


def in_text(e, style, n):
    if style == "ieee":
        return f"[{n}]"
    names = e["authors"] or (e["editors"] if e["type"] == "book" else [])
    if style == "mla" and e["type"] == "software" and e["description"]:
        return f'("{short_title(e["description"])}")'
    fams = [fam(x) for x in names]
    y = e.get("year_s") or ("n.d." if e["type"] == "web" else "[year missing]")
    quoted = e["type"] in ("article", "chapter") or (e["type"] == "web" and style != "apa")
    if not fams:
        st = f'"{short_title(e["title"])}"' if quoted else short_title(e["title"])
        return f"({st}, {y})" if style == "apa" else (f"({st})" if style == "mla" else f"({st} {y})")
    if style == "apa":
        a = fams[0] if len(fams) == 1 else (f"{fams[0]} & {fams[1]}" if len(fams) == 2 else f"{fams[0]} et al.")
        return f"({a}, {y})"
    if style == "mla":
        a = fams[0] if len(fams) == 1 else (f"{fams[0]} and {fams[1]}" if len(fams) == 2 else f"{fams[0]} et al.")
        return f"({a})"
    if len(fams) == 1:
        a = fams[0]
    elif len(fams) == 2:
        a = f"{fams[0]} and {fams[1]}"
    elif len(fams) == 3:
        a = f"{fams[0]}, {fams[1]}, and {fams[2]}"
    else:
        a = f"{fams[0]} et al."
    return f"({a} {y})"


# ---------------------------------------------------------------- checks
def has(e, field):
    if field == "author":
        return bool(e["authors"] or (e["type"] == "book" and e["editors"]))
    if field == "editor":
        return bool(e["editors"])
    if field == "author_or_publisher":
        return bool(e["authors"] or e["publisher"])
    if field == "doi_or_url":
        return bool(e["doi"] or e["url"])
    if field == "accessed":
        return bool(e["accessed"])
    return bool(e.get(field))


def check(e, style):
    req = REQUIRED[style][e["type"]]
    missing = [f for f in req if not has(e, f)]
    rec = RECOMMENDED.get(e["type"], []) + EXTRA_RECOMMENDED.get((style, e["type"]), [])
    if e["type"] == "web" and style in ("mla", "ieee"):
        rec = [r for r in rec if r != "year" or style != "mla"]
    recommended = [f for f in dict.fromkeys(rec) if f not in missing and not has(e, f)]
    warnings = []
    e["pages"] = pages_norm(e["pages"])
    if e["doi"]:
        e["doi"] = norm_doi(e["doi"])
        if not DOI_RE.match(e["doi"]):
            warnings.append(f"invalid-doi: '{e['doi']}' does not match 10.NNNN/suffix; left out of the entry")
            e["doi"] = ""
    if e["year"]:
        if not re.match(r"^\d{4}$", e["year"]) or not YEAR_MIN <= int(e["year"]) <= YEAR_MAX:
            warnings.append(f"implausible-year: '{e['year']}'")
    for key in ("title", "container", "publisher"):
        if "\\" in e[key]:
            warnings.append(f"latex-residue: '{key}' still contains a backslash; fix the source")
    names = len(e["authors"])
    if style == "apa" and names > APA_MAX:
        warnings.append(f"apa-{names}-authors: first 19, ellipsis, last author listed")
    if style == "chicago" and names > CHICAGO_MAX:
        warnings.append(f"chicago-{names}-authors: first 7 then et al. applied")
    if style == "ieee" and names > IEEE_MAX:
        warnings.append(f"ieee-{names}-authors: first author then et al. applied")
    if e["type"] in ("web", "software") and not e["authors"] and e["title"]:
        warnings.append("no-author: title or publisher stands in the author position")
    if e["type"] == "web" and not e["year"] and style in ("apa", "chicago"):
        warnings.append("no-date: n.d. printed")
    if style == "apa" and e["title"] and e["type"] in ("article", "chapter"):
        w = [x for x in e["title"].split()[1:] if len(x) > 3]
        if len(w) >= 3 and sum(x[0].isupper() for x in w) / len(w) > 0.6:
            warnings.append("title-case: APA article and chapter titles use sentence case; script does not change case")
    if style == "mla" and re.match(r"^[A-Za-z]+\d+$", e["pages"]):
        warnings.append("article-number: printed bare in MLA; confirm how your instructor wants article numbers labelled")
    if style == "chicago" and e["type"] == "software":
        warnings.append("chicago-ai: guidance prefers citing generated text in running text or a note rather than the reference list; confirm")
    if style == "ieee" and e["type"] == "software":
        warnings.append("ieee-software: generic online-software pattern; confirm against your venue")
    if e["type"] == "software" and style == "mla" and e["year"] and not e["month"]:
        warnings.append("mla-ai-date: full date (day, month, year) of the generation is expected")
    return missing, recommended, warnings


def assign_suffixes(entries, style):
    groups = {}
    for e in entries:
        if e["type"] and e["year"] and (e["authors"] or e["editors"]):
            names = e["authors"] or e["editors"]
            groups.setdefault((tuple(fam(n).lower() for n in names), e["year"]), []).append(e)
    for g in groups.values():
        if len(g) > 1 and style in ("apa", "chicago"):
            for i, e in enumerate(sorted(g, key=lambda x: x["title"].lower())):
                e["year_s"] = e["year"] + chr(97 + i)
    for e in entries:
        e.setdefault("year_s", e["year"])


def sort_key(e):
    names = e["authors"] or (e["editors"] if e["type"] == "book" else [])
    lead = fam(names[0]).lower() if names else re.sub(r"^(a|an|the)\s+", "", e["title"].lower())
    return (lead, e.get("year_s", ""), e["title"].lower())


def title_norm(e):
    return re.sub(r"[^a-z0-9]", "", e["title"].lower())


def build(entries, style, plain):
    seen_doi, seen_key, dup_of, dups = {}, {}, {}, []
    for e in entries:
        if not e["type"]:
            continue
        k1 = norm_doi(e["doi"]).lower() if e["doi"] else ""
        names = e["authors"] or e["editors"]
        k2 = (fam(names[0]).lower() if names else "", e["year"], title_norm(e))
        first = seen_doi.get(k1) if k1 else None
        first = first or (seen_key.get(k2) if k2[2] else None)
        if first:
            dup_of[id(e)] = first
            dups.append({"id": e["id"], "duplicate_of": first})
        else:
            if k1:
                seen_doi[k1] = e["id"]
            if k2[2]:
                seen_key[k2] = e["id"]
    assign_suffixes([e for e in entries if e["type"] and id(e) not in dup_of], style)
    results = []
    for e in entries:
        res = {"id": e["id"], "type": e["type"] or None, "status": "ok", "formatted": "", "in_text": "",
               "missing_required": [], "missing_recommended": [], "warnings": []}
        if not e["type"]:
            res["status"] = "error"
            res["warnings"].append(f"unsupported-type: '{e.get('raw_type')}'; supported: article, book, chapter, web, report, software")
            results.append((e, res))
            continue
        e.setdefault("year_s", e["year"])
        miss, rec, warn = check(e, style)
        res["missing_required"], res["missing_recommended"], res["warnings"] = miss, rec, warn
        if miss:
            res["status"] = "incomplete"
        res["formatted"] = re.sub(r"\s+", " ", FORMATTERS[style](e, plain)).strip()
        if id(e) in dup_of:
            res["duplicate_of"] = dup_of[id(e)]
        results.append((e, res))
    return results, dups


def same_path(a, b):
    ra, rb = os.path.normcase(os.path.realpath(a)), os.path.normcase(os.path.realpath(b))
    if ra == rb:
        return True
    try:
        return os.path.samefile(a, b)
    except OSError:
        return False


def run_format(path, style, out, plain):
    if out and same_path(out, path):
        raise ValueError("refusing to write over the input file: --out must differ from SOURCE")
    entries = load(path)
    results, dups = build(entries, style, plain)
    live = [(e, r) for e, r in results if r["status"] != "error" and "duplicate_of" not in r]
    ordered = live if style == "ieee" else sorted(live, key=lambda p: sort_key(p[0]))
    lines = []
    for n, (e, r) in enumerate(ordered, 1):
        r["in_text"] = in_text(e, style, n)
        line = r["formatted"]
        if r["status"] == "incomplete":
            line = "[INCOMPLETE: missing " + ", ".join(r["missing_required"]) + "] " + line
        lines.append(f"[{n}] {line}" if style == "ieee" else line)
    for e, r in results:
        if "duplicate_of" in r:
            r["in_text"] = ""
    summary = {"total": len(results),
               "ok": sum(r["status"] == "ok" for _, r in results),
               "incomplete": sum(r["status"] == "incomplete" for _, r in results),
               "error": sum(r["status"] == "error" for _, r in results),
               "duplicates": len(dups), "warnings": sum(len(r["warnings"]) for _, r in results)}
    report = {"command": "format", "style": style, "style_version": STYLE_VERSIONS[style],
              "input": os.path.basename(path), "summary": summary,
              "ok": summary["incomplete"] == 0 and summary["error"] == 0 and not dups,
              "entries": [r for _, r in results], "duplicates": dups, "references": lines,
              "not_checked": ["existence of any source", "accuracy of any field value", "italics and hanging indent in the final document",
                              "whether the current manual has changed the rule"]}
    if out:
        with open(out, "w", encoding="utf-8", newline="\n") as fh:
            fh.write("\n".join(lines) + "\n")
        report["written"] = os.path.basename(out)
    return report


def run_rules(style):
    return {"command": "rules", "style": style, "style_version": STYLE_VERSIONS[style],
            "required": REQUIRED[style],
            "recommended": {t: RECOMMENDED.get(t, []) + EXTRA_RECOMMENDED.get((style, t), []) for t in TYPES},
            "author_limits": {"apa": f"all up to {APA_MAX}, else 19 + ellipsis + last",
                              "mla": "1 or 2 listed, 3 or more: first + et al.",
                              "chicago": f"all up to {CHICAGO_MAX}, else first {CHICAGO_KEEP} + et al.",
                              "ieee": f"all up to {IEEE_MAX}, else first + et al."}[style]}


def main(argv=None):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    f = sub.add_parser("format")
    f.add_argument("source")
    f.add_argument("--style", required=True, choices=list(FORMATTERS))
    f.add_argument("--out")
    f.add_argument("--plain", action="store_true", help="no markdown italics")
    r = sub.add_parser("rules")
    r.add_argument("--style", required=True, choices=list(FORMATTERS))
    try:
        a = ap.parse_args(argv)
    except SystemExit as exc:
        return 2 if exc.code else 0
    try:
        rep = run_format(a.source, a.style, a.out, a.plain) if a.cmd == "format" else run_rules(a.style)
    except (OSError, ValueError) as exc:
        print("error: " + str(exc), file=sys.stderr)
        return 2
    print(json.dumps(rep, indent=2, ensure_ascii=False))
    return 0 if rep.get("ok", True) else 1


if __name__ == "__main__":
    sys.exit(main())
