#!/usr/bin/env python3
"""Format IEEE numbered references from structured data, and verify a pasted IEEE list.

Usage:
    python ieee_format.py format INPUT.json [--ascii] [--text-out LIST.txt] [--output REPORT.json]
    python ieee_format.py verify LIST.txt [--manuscript TEXT.txt] [--output REPORT.json]

format  reads one JSON file with "entries" (the sources) and "citations" (the in-text
        citations in the order they appear in the manuscript). It numbers the sources in
        order of first citation, writes each in-text citation, and builds the reference list.
        Journal and conference name abbreviations are never invented: the script prints the
        abbreviation you supply, or the full name with a warning when none is supplied.
verify  reads a pasted reference list ("[1] ..." lines) and optionally the manuscript text,
        and reports every rule it can check by pattern.

Writes: strict JSON to stdout; with --output a new file (mode "x") with the same JSON;
with --text-out a new file with the numbered list (format only). It refuses a path that
is an existing file or the input file. Standard library only, no network, no clock.

Exit codes: 0 no error-level finding; 1 at least one error-level finding; 2 usage or
input problem (one-line JSON error on stdout).

Rules come from the IEEE Reference Guide V 3.28.2025; see references/ in the skill.
"""
import argparse
import calendar
import json
import os
import re
import sys

SCHEMA_VERSION = 1
MAX_BYTES = 2_000_000
MAX_DEPTH = 12
MAX_STR = 5000
MAX_ENTRIES = 2000

MONTH_ABBR = {1: "Jan.", 2: "Feb.", 3: "Mar.", 4: "Apr.", 5: "May", 6: "Jun.",
              7: "Jul.", 8: "Aug.", 9: "Sep.", 10: "Oct.", 11: "Nov.", 12: "Dec."}
MONTH_NAMES = ["january", "february", "march", "april", "may", "june", "july",
               "august", "september", "october", "november", "december"]
MONTH_LOOKUP = {}
for _i, _n in enumerate(MONTH_NAMES, 1):
    MONTH_LOOKUP[_n] = _i
    MONTH_LOOKUP[_n[:3]] = _i
MONTH_LOOKUP["sept"] = 9
ABBR_SET = set(MONTH_ABBR.values())
FULL_MONTH_RE = r"(?:January|February|March|April|June|July|August|September|October|November|December|Sept)"
SHORT_MONTH_RE = r"(?:Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|Oct|Nov|Dec)"
US_NAMES = {"usa", "us", "u.s.", "u.s.a.", "u.s.a", "united states", "united states of america"}
SUFFIXES = {"jr": "Jr.", "sr": "Sr.", "ii": "II", "iii": "III", "iv": "IV"}
TYPES = ("journal", "book", "chapter", "conference", "web")
ORDINAL_WORDS = ("first", "second", "third", "fourth", "fifth", "sixth", "seventh",
                 "eighth", "ninth", "tenth")
CONF_FULL_WORDS = ("Proceedings", "International", "Conference", "Symposium", "Annual",
                   "Technical Digest")
DASH = "–"


class InputError(Exception):
    """A problem with the input file or options; reported with exit code 2."""


def fail(msg):
    raise InputError(msg)


def finding(sev, code, message, ref=None):
    return {"severity": sev, "code": code, "ref": ref, "message": message}


# ---------------------------------------------------------------- safe file I/O

def _bad_int(s):
    if len(s) > 15:
        raise ValueError("integer with more than 15 digits")
    return int(s)


def _bad_float(s):
    raise ValueError("non-integer number %s: write it as a string" % s[:20])


def _bad_const(s):
    raise ValueError("%s is not allowed in JSON" % s)


def read_text(path):
    if not os.path.exists(path):
        fail("input file not found")
    if not os.path.isfile(path):
        fail("input path is not a file")
    if os.path.getsize(path) > MAX_BYTES:
        fail("input larger than 2 MB")
    with open(path, "rb") as fh:
        data = fh.read(MAX_BYTES + 1)
    if not data.strip():
        fail("input file is empty")
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        fail("input is not valid UTF-8")
    if text.startswith("\ufeff"):
        text = text[1:]
    return text


def depth_ok(obj):
    stack = [(obj, 1)]
    while stack:
        cur, d = stack.pop()
        if d > MAX_DEPTH:
            return False
        if isinstance(cur, dict):
            stack.extend((v, d + 1) for v in cur.values())
        elif isinstance(cur, list):
            stack.extend((v, d + 1) for v in cur)
    return True


def load_json(path):
    text = read_text(path)
    try:
        doc = json.loads(text, parse_int=_bad_int, parse_float=_bad_float,
                         parse_constant=_bad_const)
    except RecursionError:
        fail("JSON nested too deeply")
    except ValueError as exc:
        fail("invalid JSON: %s" % str(exc)[:120])
    if not depth_ok(doc):
        fail("JSON nested more than %d levels" % MAX_DEPTH)
    return doc


def out_path_ok(out, input_path):
    if out is None:
        return
    if os.path.exists(out) or os.path.islink(out):
        fail("output path already exists: %s" % os.path.basename(out))
    if os.path.realpath(out) == os.path.realpath(input_path):
        fail("output path is the input file")


def write_new(path, text):
    try:
        with open(path, "x", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
    except FileExistsError:
        fail("output path already exists: %s" % os.path.basename(path))
    except OSError as exc:
        fail("cannot write output: %s" % exc.strerror)


# ---------------------------------------------------------------- field helpers

def clean(value):
    """Return a whitespace-collapsed string for str or int, else None."""
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, int):
        return str(value)
    if isinstance(value, str):
        s = " ".join(value.split())
        if len(s) > MAX_STR:
            fail("a field is longer than %d characters" % MAX_STR)
        return s or None
    fail("fields must be strings or whole numbers")


def ordinal(n):
    if 10 <= n % 100 <= 20:
        suf = "th"
    else:
        suf = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return "%d%s" % (n, suf)


def parse_month(value):
    """Return (display string or None, error text or None). Accepts one month or two."""
    s = clean(value)
    if s is None:
        return None, None
    parts = [p for p in re.split(r"\s*[/–—-]\s*", s) if p]
    if not 1 <= len(parts) <= 2:
        return None, "month %r not understood" % s[:20]
    shown = []
    for p in parts:
        p2 = p.rstrip(".").lower()
        if p2.isdigit():
            num = int(p2)
        else:
            num = MONTH_LOOKUP.get(p2)
        if num is None or not 1 <= num <= 12:
            return None, "month %r not understood" % p[:20]
        shown.append(num)
    return "/".join(MONTH_ABBR[n] for n in shown), None


def month_num(value):
    s = clean(value)
    if s is None:
        return None
    p = s.rstrip(".").lower()
    if p.isdigit():
        return int(p) if 1 <= int(p) <= 12 else None
    return MONTH_LOOKUP.get(p)


def build_date(e, ref, issues, need_day=False, allow_days=False):
    """Month/day/year text such as 'Aug. 30, 2024'. Returns '' when nothing is given."""
    month, err = parse_month(e.get("month"))
    if err:
        issues.append(finding("error", "bad_month", err, ref))
    year = clean(e.get("year"))
    day = clean(e.get("day"))
    days = clean(e.get("days")) if allow_days else None
    if year is not None and not re.fullmatch(r"\d{4}", year):
        issues.append(finding("error", "bad_year", "year must be four digits", ref))
    if day is not None:
        if not day.isdigit() or not 1 <= int(day) <= 31:
            issues.append(finding("error", "bad_date", "day %r is not 1-31" % day[:6], ref))
            day = None
        elif month and "/" not in month and year and re.fullmatch(r"\d{4}", year):
            mn = month_num(e.get("month"))
            if mn and int(day) > calendar.monthrange(int(year), mn)[1]:
                issues.append(finding("error", "bad_date",
                                      "%s %s does not exist in %s" % (month, day, year), ref))
    if days is not None:
        m = re.fullmatch(r"(\d{1,2})\s*(?:[–—-]+\s*(\d{1,2}))?", days)
        if not m or not all(1 <= int(g) <= 31 for g in m.groups() if g):
            issues.append(finding("error", "bad_date", "days %r not understood" % days[:12], ref))
            days = None
        else:
            days = m.group(1) if not m.group(2) else "%s%s%s" % (m.group(1), "@@", m.group(2))
        if days and not month:
            issues.append(finding("error", "bad_date", "days given without a month", ref))
    if need_day and (month is None or day is None or year is None):
        issues.append(finding("error", "missing_field", "month, day and year are all required", ref))
    out = month or ""
    if day:
        out = (out + " " + day).strip()
    elif days:
        out = (out + " " + days).strip()
    if year:
        out = (out + ", " + year) if (day or days) else (out + " " + year).strip()
    return out


def pages_text(e, ref, issues, ascii_mode):
    """Return (kind, text): kind is 'pp', 'p', 'artno' or None."""
    raw = clean(e.get("pages"))
    art = clean(e.get("article_number"))
    if raw is None:
        return ("artno", art) if art else (None, None)
    m = re.fullmatch(r"\s*(\d+)\s*(?:[–—-]+\s*(\d+))?\s*", raw)
    if m:
        first, last = m.group(1), m.group(2)
        if last is None or last == first:
            return "p", first
        if int(last) < int(first) or len(last) < len(first):
            issues.append(finding("error", "elided_pages",
                                  "page range %r is shortened; write both numbers in full" % raw[:20], ref))
            return None, None
        return "pp", first + ("-" if ascii_mode else DASH) + last
    if re.fullmatch(r"[A-Za-z]+\d+", raw) and not art:
        issues.append(finding("warning", "article_id_moved",
                              "%r looks like an article number, so it is printed as Art. no., not as a page" % raw[:20], ref))
        return "artno", raw
    issues.append(finding("error", "bad_pages", "pages %r not understood" % raw[:20], ref))
    return None, None


def doi_text(e, ref, issues):
    d = clean(e.get("doi"))
    if d is None:
        return None
    d = re.sub(r"^(?:https?://(?:dx\.)?doi\.org/|doi:\s*)", "", d, flags=re.I)
    if not re.fullmatch(r"10\.\d{4,9}/\S+", d):
        issues.append(finding("error", "bad_doi", "DOI must look like 10.xxxx/suffix", ref))
        return None
    return d


# ---------------------------------------------------------------- names

def initials(given, ref, issues):
    out = []
    for tok in [t for t in re.split(r"[\s.]+", given) if t]:
        parts = [p for p in tok.split("-") if p]
        if len(parts) > 1:
            issues.append(finding("warning", "hyphenated_given_name",
                                  "the guide gives no rule for %r; initials printed as %s" % (
                                      tok[:20], "-".join(p[0].upper() + "." for p in parts)), ref))
            out.append("-".join(p[0].upper() + "." for p in parts))
        elif parts:
            out.append(parts[0][0].upper() + ".")
    return " ".join(out)


def person(p, ref, issues):
    """Return (display name, surname, has_suffix) for one person or organization."""
    if isinstance(p, str):
        fail("authors must be objects with family and given, or org")
    if not isinstance(p, dict):
        fail("each author must be an object")
    org = clean(p.get("org"))
    if org:
        return org, org, False
    family = clean(p.get("family"))
    if not family:
        fail("every author needs family or org")
    given = clean(p.get("given"))
    suffix = clean(p.get("suffix"))
    name = family
    if given:
        name = initials(given, ref, issues) + " " + family
    else:
        issues.append(finding("warning", "author_given_name_missing",
                              "no given name for %s" % family[:40], ref))
    sfx = None
    if suffix:
        sfx = SUFFIXES.get(suffix.rstrip(".").lower(), suffix)
        name += " " + sfx
    return name, family, bool(sfx)


def people(lst, ref, issues, label="authors"):
    if not isinstance(lst, list) or not lst:
        return None
    people_ = [person(p, ref, issues) for p in lst]
    n = len(people_)
    if n > 6:
        return people_[0][0] + " et al.", people_, True
    names = [p[0] for p in people_]
    if n == 1:
        return names[0], people_, False
    if n == 2:
        sep = ", and " if people_[0][2] else " and "
        return names[0] + sep + names[1], people_, False
    return ", ".join(names[:-1]) + ", and " + names[-1], people_, False


# ---------------------------------------------------------------- reference builders

def place(e):
    city, state, country = clean(e.get("city")), clean(e.get("state")), clean(e.get("country"))
    us = country is not None and country.lower() in US_NAMES
    bits = []
    if city:
        bits.append(city)
    if us:
        if state:
            bits.append(state)
        bits.append("USA")
    else:
        if country:
            bits.append(country)
    return bits, us, bool(city), bool(state)


def check_place(e, ref, issues, need):
    bits, us, has_city, has_state = place(e)
    if need and not bits:
        issues.append(finding("warning", "missing_location",
                              "no city or country; the guide's form includes the place of publication", ref))
    if us and not has_state:
        issues.append(finding("warning", "us_state_missing",
                              "U.S. location without a state; the guide prints city, state, USA", ref))
    if not us and clean(e.get("state")):
        issues.append(finding("warning", "state_ignored",
                              "state is printed only for U.S. places and was left out", ref))
    return bits


def check_conf_name(name, ref, issues):
    hit = [w for w in CONF_FULL_WORDS if re.search(r"\b%s\b" % w, name)]
    if hit:
        issues.append(finding("warning", "conference_name_unabbreviated",
                              "supply the abbreviated name (the guide abbreviates %s)" % ", ".join(hit), ref))
    if re.search(r"\b(?:%s)\b" % "|".join(ORDINAL_WORDS), name, re.I):
        issues.append(finding("warning", "ordinal_not_numeric",
                              "the guide writes ordinals as numerals, such as 4th", ref))


def need(e, keys, ref, issues):
    ok = True
    for k in keys:
        if k == "authors":
            if not isinstance(e.get("authors"), list) or not e.get("authors"):
                issues.append(finding("error", "missing_field", "authors is required", ref))
                ok = False
        elif clean(e.get(k)) is None:
            issues.append(finding("error", "missing_field", "%s is required" % k, ref))
            ok = False
    return ok


def build_reference(e, ref, issues, ascii_mode):
    lq, rq = ('"', '"') if ascii_mode else ("“", "”")
    typ = clean(e.get("type"))
    if typ not in TYPES:
        fail("entry %s: type must be one of %s" % (ref, ", ".join(TYPES)))
    auth = people(e.get("authors"), ref, issues)
    a_txt = auth[0] if auth else None
    title = clean(e.get("title"))
    status = clean(e.get("status"))
    doi = doi_text(e, ref, issues)
    url = clean(e.get("url"))
    if url and not re.fullmatch(r"(?:https?://|www\.)\S+", url):
        issues.append(finding("error", "bad_url", "url must start with http://, https:// or www.", ref))
        url = None

    def finish(body):
        return body + "."

    if typ == "journal":
        keys = ["authors", "title"] + ([] if status else ["year"])
        need(e, keys, ref, issues)
        jfull, jabbr = clean(e.get("journal")), clean(e.get("journal_abbrev"))
        if not jfull and not jabbr:
            issues.append(finding("error", "missing_field", "journal or journal_abbrev is required", ref))
        if jfull and " " not in jfull:
            jname = jfull
        elif jabbr:
            jname = jabbr
        else:
            jname = jfull
            if jname:
                issues.append(finding("warning", "journal_abbreviation_missing",
                                      "no journal_abbrev supplied; the full title is printed unabbreviated", ref))
        head = "%s, %s%s,%s" % (a_txt or "", lq, title or "", rq)
        if status == "submitted":
            return finish(head + " submitted for publication")
        body = head + " " + (jname or "")
        if status == "to_be_published":
            return finish(body + ", to be published")
        if status:
            fail("entry %s: status must be to_be_published or submitted" % ref)
        if e.get("early_access") is True:
            body += ", early access, " + build_date(e, ref, issues, need_day=True)
            if doi:
                body += ", doi: " + doi
            return finish(body)
        vol, no = clean(e.get("volume")), clean(e.get("issue"))
        if vol:
            body += ", vol. " + vol
        else:
            issues.append(finding("warning", "missing_volume", "no volume given", ref))
        if no:
            body += ", no. " + no
        kind, ptxt = pages_text(e, ref, issues, ascii_mode)
        if kind in ("p", "pp"):
            body += ", %s. %s" % (kind, ptxt)
        d = build_date(e, ref, issues) or "(n.d.)"
        body += ", " + d
        if kind == "artno":
            body += ", Art. no. " + ptxt
        if doi:
            body += ", doi: " + doi
            if url:
                issues.append(finding("warning", "url_dropped", "DOI present, so the URL was not printed", ref))
            return finish(body)
        if url:
            return body + ". [Online]. Available: " + url
        return finish(body)

    if typ == "book":
        need(e, ["authors", "title", "publisher", "year"], ref, issues)
        bits = check_place(e, ref, issues, True)
        ed = clean(e.get("edition"))
        body = "%s, %s" % (a_txt or "", title or "")
        if ed:
            m = re.fullmatch(r"(\d{1,2})(?:st|nd|rd|th)?(?:\s+ed\.?)?", ed, re.I)
            if not m:
                issues.append(finding("error", "bad_edition", "edition must be a number such as 2 or 2nd", ref))
            else:
                body += ", %s ed" % ordinal(int(m.group(1)))
        body += ". "
        loc = ", ".join(bits)
        pub = clean(e.get("publisher")) or ""
        if re.search(r"\bUniversity\b", pub):
            issues.append(finding("warning", "publisher_unabbreviated",
                                  "the guide abbreviates University as Univ. in publisher names", ref))
        body += ("%s: %s" % (loc, pub)) if loc else pub
        d = build_date(e, ref, issues) or "(n.d.)"
        body += ", " + d
        pg = clean(e.get("pages"))
        if clean(e.get("chapter_number")):
            body += ", ch. " + clean(e.get("chapter_number"))
        if pg:
            kind, ptxt = pages_text(e, ref, issues, ascii_mode)
            if kind in ("p", "pp"):
                body += ", %s. %s" % (kind, ptxt)
        if doi:
            body += ", doi: " + doi
        return finish(body)

    if typ == "chapter":
        need(e, ["authors", "title", "book_title", "publisher", "year"], ref, issues)
        bits = check_place(e, ref, issues, True)
        if clean(e.get("edition")):
            issues.append(finding("warning", "edition_ignored",
                                  "the guide shows no edition form for a chapter; edition not printed", ref))
        body = "%s, %s%s,%s in %s" % (a_txt or "", lq, title or "", rq, clean(e.get("book_title")) or "")
        eds = people(e.get("editors"), ref, issues, "editors")
        if eds:
            n_eds = len(eds[1]) if not eds[2] else 7
            body += ", %s, %s" % (eds[0], "Ed." if n_eds == 1 else "Eds.")
        loc = ", ".join(bits)
        pub = clean(e.get("publisher")) or ""
        if re.search(r"\bUniversity\b", pub):
            issues.append(finding("warning", "publisher_unabbreviated",
                                  "the guide abbreviates University as Univ. in publisher names", ref))
        body += ", " + (("%s: %s" % (loc, pub)) if loc else pub)
        body += ", " + (build_date(e, ref, issues) or "(n.d.)")
        if clean(e.get("chapter_number")):
            body += ", ch. " + clean(e.get("chapter_number"))
        kind, ptxt = pages_text(e, ref, issues, ascii_mode)
        if kind in ("p", "pp"):
            body += ", %s. %s" % (kind, ptxt)
        if doi:
            body += ", doi: " + doi
        return finish(body)

    if typ == "conference":
        need(e, ["authors", "title", "conference", "year"], ref, issues)
        conf = clean(e.get("conference")) or ""
        check_conf_name(conf, ref, issues)
        bits = check_place(e, ref, issues, False)
        d = build_date(e, ref, issues, allow_days=True).replace("@@", DASH if not ascii_mode else "-")
        presented = e.get("presented") is True
        head = "%s, %s%s,%s " % (a_txt or "", lq, title or "", rq)
        body = head + ("presented at the " if presented else "in ") + conf
        if bits:
            body += ", " + ", ".join(bits)
        if d:
            body += ", " + d
        if clean(e.get("paper")):
            body += ", Paper " + clean(e.get("paper"))
        if not presented:
            kind, ptxt = pages_text(e, ref, issues, ascii_mode)
            if kind in ("p", "pp"):
                body += ", %s. %s" % (kind, ptxt)
            if doi:
                body += ", doi: " + doi
        elif clean(e.get("pages")) or doi:
            issues.append(finding("warning", "fields_ignored",
                                  "pages and DOI are not printed for a paper that was presented only", ref))
        return finish(body)

    # web
    need(e, ["title", "website", "url"], ref, issues)
    if clean(e.get("doi")):
        issues.append(finding("warning", "doi_ignored", "DOI is not used on web items", ref))
    acc = None
    if e.get("accessed") is not None:
        acc_e = {"month": e["accessed"].get("month"), "day": e["accessed"].get("day"),
                 "year": e["accessed"].get("year")} if isinstance(e.get("accessed"), dict) else None
        if acc_e is None:
            fail("entry %s: accessed must be an object with month, day, year" % ref)
        acc = build_date(acc_e, ref, issues, need_day=True)
    pub_date = build_date(e, ref, issues)
    if not acc and not pub_date:
        issues.append(finding("error", "missing_field", "accessed date or publication date is required", ref))
    lead = ""
    if a_txt:
        lead = a_txt + ", "
    body = "%s%s%s,%s %s" % (lead, lq, title or "", rq, clean(e.get("website")) or "")
    if pub_date:
        body += ", " + pub_date + "."
    else:
        body += "."
    if acc:
        body += " Accessed: " + acc + "."
    body += " [Online]. Available: " + (url or "")
    return body


# ---------------------------------------------------------------- format command

def intext_surname(entry_people):
    names = entry_people
    n = len(names)
    if n == 1:
        return names[0][1]
    if n == 2:
        return "%s and %s" % (names[0][1], names[1][1])
    return names[0][1] + " et al."


def cmd_format(args):
    doc = load_json(args.input)
    if not isinstance(doc, dict):
        fail("top level must be an object with entries and citations")
    entries, cites = doc.get("entries"), doc.get("citations")
    if not isinstance(entries, list) or not entries:
        fail("entries must be a non-empty list")
    if len(entries) > MAX_ENTRIES:
        fail("more than %d entries" % MAX_ENTRIES)
    if not isinstance(cites, list) or not cites:
        fail("citations must be a non-empty list")
    by_id = {}
    for e in entries:
        if not isinstance(e, dict):
            fail("each entry must be an object")
        eid = clean(e.get("id"))
        if not eid:
            fail("every entry needs an id")
        if eid in by_id:
            fail("duplicate entry id %s" % eid[:30])
        by_id[eid] = e
    number = {}
    order = []
    issues = []
    in_text = []
    for ci, c in enumerate(cites, 1):
        narrative = False
        if isinstance(c, dict):
            narrative = c.get("narrative") is True
            items = c.get("ids")
        else:
            items = c
        if not isinstance(items, list) or not items:
            fail("citation %d must be a non-empty list of ids" % ci)
        parts, nums = [], []
        for it in items:
            loc = None
            if isinstance(it, dict):
                key, loc = clean(it.get("id")), clean(it.get("locator"))
            else:
                key = clean(it)
            if key not in by_id:
                fail("citation %d uses unknown id %s" % (ci, str(key)[:30]))
            if key not in number:
                number[key] = len(number) + 1
                order.append(key)
            nums.append(number[key])
            parts.append((key, number[key], loc))
        if narrative:
            if len(parts) > 2:
                fail("citation %d: a narrative citation names at most two sources" % ci)
            texts = []
            for key, n, loc in parts:
                ppl = people(by_id[key].get("authors"), key, [])
                if not ppl:
                    fail("citation %d: source %s has no authors for a narrative citation" % (ci, key[:30]))
                br = "[%d%s]" % (n, (", " + fix_loc(loc, args.ascii)) if loc else "")
                texts.append("%s %s" % (intext_surname(ppl[1]), br))
            text = " and ".join(texts)
        else:
            text = ", ".join("[%d%s]" % (n, (", " + fix_loc(loc, args.ascii)) if loc else "")
                             for _, n, loc in parts)
        in_text.append({"citation": ci, "text": text, "numbers": nums})
    refs = []
    for key in order:
        ref_issues = []
        text = build_reference(by_id[key], key, ref_issues, args.ascii)
        refs.append({"number": number[key], "id": key, "text": text})
        issues.extend(ref_issues)
    for key in by_id:
        if key not in number:
            issues.append(finding("warning", "uncited_entry",
                                  "never cited, so it is not in the numbered list", key))
    seen = {}
    for r in refs:
        e = by_id[r["id"]]
        d = (clean(e.get("doi")) or "").lower()
        t = re.sub(r"\W+", "", (clean(e.get("title")) or "").lower()) + str(clean(e.get("year")))
        for k in ([("doi", d)] if d else []) + [("title", t)]:
            if k in seen and seen[k] != r["number"]:
                issues.append(finding("warning", "possible_duplicate_source",
                                      "[%d] and [%d] look like the same source; one number should be reused" % (
                                          seen[k], r["number"]), r["id"]))
            seen.setdefault(k, r["number"])
    errors = sum(1 for i in issues if i["severity"] == "error")
    warns = sum(1 for i in issues if i["severity"] == "warning")
    report = {"schema_version": SCHEMA_VERSION, "tool": "ieee_format", "mode": "format",
              "source": os.path.basename(args.input), "ascii": bool(args.ascii),
              "in_text": in_text, "references": refs, "issues": issues,
              "summary": {"citations": len(in_text), "references": len(refs),
                          "errors": errors, "warnings": warns,
                          "verdict": "fail" if errors else ("review" if warns else "pass")}}
    if args.text_out:
        out_path_ok(args.text_out, args.input)
        write_new(args.text_out, "".join("[%d] %s\n" % (r["number"], r["text"]) for r in refs))
    return report, errors


def fix_loc(loc, ascii_mode):
    return loc if ascii_mode else re.sub(r"(?<=\d)\s*[-–—]+\s*(?=\d)", DASH, loc)


# ---------------------------------------------------------------- verify command

NAME_RE = re.compile(r"(?:[A-Z]\.[ -]?)+[A-Za-zÀ-ɏ'’-]+(?: (?:Jr|Sr|II|III|IV)\.?)?")
SEP_RE = re.compile(r"\s*(?:,\s*and\s+|,\s*|\s+and\s+)")
URL_END_RE = re.compile(r"(?:https?://|www\.)\S+$")


def author_names(text):
    pos, count = 0, 0
    while True:
        m = NAME_RE.match(text, pos)
        if not m:
            break
        count += 1
        pos = m.end()
        s = SEP_RE.match(text, pos)
        if not s:
            break
        pos = s.end()
    return count, pos


def check_ref(n, text):
    out = []

    def add(sev, code, msg):
        out.append(finding(sev, code, msg, str(n)))

    count, pos = author_names(text)
    if re.match(r"[A-Z][A-Za-z'’-]+,\s*[A-Z]\.", text):
        add("error", "author_surname_first", "names go initials first, as in J. K. Author")
    elif count == 0 and re.match(r"[A-Z][a-z]{2,}\s+[A-Z][a-z]+(?:\s+and\b|,)", text):
        add("warning", "given_name_spelled_out", "given names are reduced to initials placed before the surname")
    if count > 6:
        add("error", "more_than_six_authors", "%d names listed; with more than six give the first author and et al." % count)
    m = re.search(r"\bet al\b(\.?)", text)
    if m:
        if not m.group(1):
            add("error", "et_al_period", "write et al. with a period")
        if author_names(text[:m.start()])[0] > 1:
            add("error", "et_al_with_several_names", "et al. follows only the first author")
    if re.search(r"[A-Za-z],\s*(?:Jr|Sr|III)\b", text):
        add("error", "comma_before_suffix", "no comma before Jr., Sr. or III")
    if re.search(r"[”\"],", text):
        add("error", "comma_outside_quote", "the comma after a quoted title goes inside the closing quotation mark")
    last = text.split()[-1] if text.split() else ""
    if URL_END_RE.fullmatch(last):
        if last.endswith("."):
            add("error", "url_trailing_period", "a reference that ends with a URL has no final period")
    elif not text.endswith("."):
        add("error", "missing_final_period", "every reference not ending in a URL ends with a period")
    if re.search(r"\b%s\s+(?:\d|\(n)" % FULL_MONTH_RE, text) or re.search(r"\bSept\.", text):
        add("error", "month_not_abbreviated", "months are abbreviated: Jan. Feb. Mar. Apr. May Jun. Jul. Aug. Sep. Oct. Nov. Dec.")
    if re.search(r"\b%s(?![\w.])\s+\d" % SHORT_MONTH_RE, text):
        add("error", "month_missing_period", "abbreviated months end with a period, except May")
    if re.search(r"\b(?:Vol|No|Pp|PP|Ch)\.", text) or re.search(r"\b[Vv]olume\s+\d|\b[Ii]ssue\s+\d", text) \
            or re.search(r"\bpp?\s*\d", text) or re.search(r", (?:pp|vol|no)\s+\d", text):
        add("error", "label_format", "labels are lowercase with a period: vol., no., pp., p., ch.")
    if re.search(r"\bpp\.\s*\d+(?!\s*[-–—\d])\s*[,.]", text):
        add("error", "pp_for_single_page", "a single page is p., not pp.")
    if re.search(r"(?<![a-z])p\.\s*\d+\s*[-–—]\s*\d+", text):
        add("error", "p_for_page_range", "a page range is pp., not p.")
    if re.search(r"\bpp?\.\s*[A-Za-z]+\d", text):
        add("error", "article_id_in_page_slot", "an article number belongs after the year as Art. no. xxx")
    if re.search(r"\bto appear\b", text, re.I):
        add("error", "to_appear_in", "use to be published, not to appear in")
    if re.search(r"\bDOI\b|\bDoi\b|doi\.org|doi:\S", text):
        add("error", "doi_format", "write doi: 10.xxxx/xxxx with lowercase doi, a colon and a space, no URL form")
    if "Available" in text and not re.search(r"\[Online\]\. Available: \S", text):
        add("error", "online_available_format", "use [Online]. Available: URL")
    if re.search(r"\[Online\](?!\. Available)", text):
        add("error", "online_available_format", "use [Online]. Available: URL")
    for am in re.finditer(r"\bAccessed\b(:?)\s*([^\s,.]*\.?)\s*(\d{1,2}),\s*(\d{4})", text):
        if not am.group(1) or am.group(2) not in ABBR_SET:
            add("error", "accessed_format", "write Accessed: Mon. d, yyyy with an abbreviated month")
    if re.search(r"\bAccessed\b(?!:)|\bRetrieved\b", text):
        add("error", "accessed_format", "write Accessed: Mon. d, yyyy")
    if re.search(r"\b\d+(?:st|nd|rd|th)\s+(?:edition|Ed\.|ed(?!\.))", text) or \
            re.search(r"\b(?:%s)\s+ed(?:ition)?\b" % "|".join(ORDINAL_WORDS), text, re.I):
        add("error", "edition_format", "an edition is written as 2nd ed. (numeral, lowercase ed.)")
    if re.search(r"\bUnited States\b|\bU\.S\.A\b|\bU\.S\.:", text):
        add("warning", "usa_form", "the guide prints USA after a U.S. state")
    for um in re.finditer(r"(\S+),\s*USA\b", text):
        if not re.fullmatch(r"[A-Z]{2}", um.group(1)):
            add("warning", "us_state_form", "a U.S. place is City, ST, USA with the two-letter state")
    if not re.search(r"\b(?:1[5-9]|20)\d\d\b|\(n\.d\.\)|to be published|submitted for publication", text):
        add("error", "no_year", "a year is required, or (n.d.) when none exists")
    sec = re.search(r"[”\"]\s*in\s+(Proc[^,]*)", text)
    if sec:
        seg = sec.group(1)
        if re.search(r"\b(?:Proceedings|International|Conference|Symposium|Annual|Technical Digest)\b", seg):
            add("warning", "conference_name_unabbreviated", "conference names use Proc., Int., Conf., Symp., Annu., Tech. Dig.")
        if re.search(r"\b(?:%s)\b" % "|".join(ORDINAL_WORDS), seg, re.I):
            add("warning", "ordinal_not_numeric", "ordinals are numerals, such as 4th")
    return out


def parse_list(text):
    refs, stray = [], False
    for line in text.splitlines():
        if not line.strip():
            continue
        m = re.match(r"\s*\[(\d{1,6})\]\s+(.*)$", line)
        if m:
            refs.append([int(m.group(1)), m.group(2).strip()])
        elif refs:
            refs[-1][1] += " " + line.strip()
        else:
            stray = True
    return refs, stray


BRACKET_RE = re.compile(r"\[[^\[\]\n]{1,80}\]")


def check_manuscript(text, listed):
    out, seq = [], []
    for m in BRACKET_RE.finditer(text):
        body = m.group(0)[1:-1].strip()
        after = text[m.end():m.end() + 6]
        nums = []
        if re.fullmatch(r"\d+\s*[–—-]\s*\d+", body):
            a, b = [int(x) for x in re.findall(r"\d+", body)]
            out.append(finding("error", "range_dash", "write every number out: [%d], ... [%d]; %s" % (a, b, m.group(0))))
            nums = list(range(a, b + 1)) if a <= b and b - a < 100 else [a, b]
        elif re.fullmatch(r"\d+(?:\s*,\s*\d+)+", body):
            out.append(finding("warning", "combined_numbers_in_bracket", "the guide writes each number in its own bracket: %s" % m.group(0)))
            nums = [int(x) for x in re.findall(r"\d+", body)]
        elif re.match(r"\d+(?:\s*,\s*[A-Za-z])", body) or re.fullmatch(r"\d+", body):
            nums = [int(re.match(r"\d+", body).group(0))]
        if re.match(r"\s*[–—-]\s*\[\d", after) and nums and re.fullmatch(r"\d+", body):
            rest = re.match(r"\s*[–—-]\s*\[(\d+)\]", text[m.end():m.end() + 14])
            if rest:
                out.append(finding("error", "range_dash", "write every number out: %s%s" % (m.group(0), rest.group(0))))
                lo, hi = nums[0], int(rest.group(1))
                if lo <= hi and hi - lo < 100:
                    nums = list(range(lo, hi + 1))
        seq.extend(nums)
    first = []
    for n in seq:
        if n not in first:
            first.append(n)
    if first != list(range(1, len(first) + 1)):
        out.append(finding("error", "first_citation_order",
                           "numbers must appear first in the order 1, 2, 3 ...; first appearances are %s" % first[:30]))
    cited = set(first)
    for n in sorted(cited - set(listed)):
        out.append(finding("error", "cited_not_in_list", "[%d] is cited but not in the list" % n, str(n)))
    for n in sorted(set(listed) - cited):
        out.append(finding("warning", "listed_not_cited", "[%d] is in the list but never cited" % n, str(n)))
    return out, first


def cmd_verify(args):
    text = read_text(args.input)
    refs, stray = parse_list(text)
    if not refs:
        fail("no lines starting with [number] found")
    if len(refs) > MAX_ENTRIES:
        fail("more than %d references" % MAX_ENTRIES)
    issues = []
    if stray:
        issues.append(finding("warning", "stray_text", "text before the first [n] line was ignored"))
    nums = [r[0] for r in refs]
    for i, n in enumerate(nums, 1):
        if nums.count(n) > 1 and nums.index(n) == i - 1:
            issues.append(finding("error", "duplicate_number", "[%d] appears more than once" % n, str(n)))
    if nums != list(range(1, len(nums) + 1)) and len(set(nums)) == len(nums):
        issues.append(finding("error", "number_sequence", "list numbers must run 1, 2, 3 ... without gaps or reordering; found %s" % nums[:30]))
    seen = {}
    for n, t in refs:
        issues.extend(check_ref(n, t))
        key = re.sub(r"\W+", "", t.lower())
        dm = re.search(r"doi: (10\.\S+?)\.?$", t)
        for k in [("t", key)] + ([("d", dm.group(1).lower())] if dm else []):
            if k in seen and seen[k] != n:
                issues.append(finding("warning", "duplicate_reference",
                                      "[%d] repeats [%d]; a repeated source reuses its number" % (n, seen[k]), str(n)))
            seen.setdefault(k, n)
    first = None
    if args.manuscript:
        ms = read_text(args.manuscript)
        more, first = check_manuscript(ms, nums)
        issues.extend(more)
    errors = sum(1 for i in issues if i["severity"] == "error")
    warns = sum(1 for i in issues if i["severity"] == "warning")
    report = {"schema_version": SCHEMA_VERSION, "tool": "ieee_format", "mode": "verify",
              "source": os.path.basename(args.input), "issues": issues,
              "first_appearance_order": first,
              "summary": {"references": len(refs), "errors": errors, "warnings": warns,
                          "verdict": "fail" if errors else ("review" if warns else "pass")}}
    return report, errors


# ---------------------------------------------------------------- main

def build_parser():
    p = argparse.ArgumentParser(prog="ieee_format.py", description=__doc__.split("\n")[0])
    sub = p.add_subparsers(dest="cmd")
    f = sub.add_parser("format")
    f.add_argument("input")
    f.add_argument("--ascii", action="store_true")
    f.add_argument("--text-out")
    f.add_argument("--output")
    v = sub.add_parser("verify")
    v.add_argument("input")
    v.add_argument("--manuscript")
    v.add_argument("--output")
    return p


def main(argv=None):
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        if exc.code in (0, None):
            return 0
        print(json.dumps({"schema_version": SCHEMA_VERSION, "error": "usage error"}))
        return 2
    try:
        if not args.cmd:
            fail("choose format or verify")
        out_path_ok(args.output, args.input)
        tout = getattr(args, "text_out", None)
        if tout and args.output and os.path.realpath(tout) == os.path.realpath(args.output):
            fail("--text-out and --output are the same path")
        report, errors = cmd_format(args) if args.cmd == "format" else cmd_verify(args)
        text = json.dumps(report, ensure_ascii=True, indent=2, allow_nan=False)
        if args.output:
            write_new(args.output, text + "\n")
        print(text)
        return 1 if errors else 0
    except InputError as exc:
        print(json.dumps({"schema_version": SCHEMA_VERSION, "error": str(exc)}))
        return 2


if __name__ == "__main__":
    sys.exit(main())
