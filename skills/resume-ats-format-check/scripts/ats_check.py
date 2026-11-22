#!/usr/bin/env python3
"""Checks a plain-text or Markdown resume for layout and wording patterns that
applicant tracking systems commonly misparse.

Usage:
    python -I ats_check.py <input-file>

Reads one file (UTF-8, at most 2 MB) and writes one JSON object to stdout.
Writes no files and makes no network calls. Exit codes: 0 no findings,
1 one or more findings, 2 usage or input error (one-line JSON on stderr).
"""
import json
import re
import sys
import unicodedata

MAX_BYTES = 2 * 1024 * 1024
LONG_LINE = 200  # working value, characters per line

# Bullet glyphs outside the plain hyphen, asterisk and plus set (escapes keep this file ASCII).
BULLETS = ("•●◦▪■►➢✓✔★→"
           "➤◆‣⁃∙➔✦✧")

EXPERIENCE = {"experience", "work experience", "professional experience",
              "employment", "employment history", "work history"}
EDUCATION = {"education", "academic background"}
SKILLS = {"skills", "technical skills", "core skills", "key skills", "core competencies"}
OTHER_STANDARD = {"summary", "profile", "professional summary", "projects", "certifications",
                  "certificates", "awards", "publications", "languages",
                  "volunteer experience", "references", "contact"}
ACCEPTED = EXPERIENCE | EDUCATION | SKILLS | OTHER_STANDARD
GROUPS = (("experience", EXPERIENCE, "Experience"),
          ("education", EDUCATION, "Education"),
          ("skills", SKILLS, "Skills"))

MONTH = (r"(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|june?|july?|aug(?:ust)?"
         r"|sep(?:t(?:ember)?)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)\.?")
DATE_PATTERNS = (
    ("month_name", re.compile(r"\b" + MONTH + r"\s+(?:19|20)\d{2}\b", re.I)),
    ("numeric_slash", re.compile(r"\b\d{1,2}/(?:\d{1,2}/)?\d{2,4}\b")),
    ("iso", re.compile(r"\b\d{4}-\d{2}(?:-\d{2})?\b")),
)
YEAR_OR_NOW = r"(?:\b(?:19|20)\d{2}\b|\bpresent\b|\bcurrent\b)"
RANGE = re.compile(r"(?i)" + YEAR_OR_NOW + r"\s*(?:-|–|—|\bto\b)\s*"
                   r"(?:(?:[a-z]{3,9}\.?\s+|\d{1,2}/)?\b(?:19|20)\d{2}\b|\bpresent\b|\bcurrent\b)")
EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
PHONE_CANDIDATE = re.compile(r"\+?\(?\d[\d\s().-]{7,}\d")
SPACING_RUN = re.compile(r"\S {3,}\S")

DETAIL = {
    "MISSING_SECTION": "no standard heading found for this section",
    "NONSTANDARD_HEADING": "heading-like line that is not a standard section name",
    "TAB_OR_SPACE_RUN": "tab or run of three or more spaces between text",
    "TABLE_PIPE": "pipe character, usually a table or column separator",
    "UNUSUAL_BULLET": "bullet glyph outside the hyphen, asterisk and plus set",
    "SPECIAL_SYMBOL": "non-ASCII symbol or bullet glyph inside the text",
    "MISSING_EMAIL": "no email address pattern found in the file",
    "MISSING_PHONE": "no phone pattern with 10 to 15 digits found in the file",
    "NO_DATE_RANGE": "no line holds a date range (two years, or a year and Present or Current)",
    "LONG_LINE": "line longer than 200 characters",
}


def fail(message):
    sys.stderr.write(json.dumps({"error": message}) + "\n")
    sys.exit(2)


def analyze(lines):
    findings = []

    def add(line_no, code, detail=None):
        findings.append({"line": line_no, "code": code, "detail": detail or DETAIL[code]})

    first = next((i for i, raw in enumerate(lines) if raw.strip()), None)
    found_groups = set()
    date_hits = []      # (line number, set of date format names on that line)
    format_lines = {}   # format name -> number of lines using it
    has_range = has_email = has_phone = False

    for idx, raw in enumerate(lines):
        n = idx + 1
        s = raw.strip()
        if not s:
            continue
        core = s.lstrip("#").strip().rstrip(":").strip()
        key = core.lower()

        for group_name, members, _label in GROUPS:
            if key in members and len(s) <= 60:
                found_groups.add(group_name)

        lead = s[0]
        if idx != first and lead not in "-*+" and not lead.isdigit():
            is_candidate = s.startswith("#") or s.endswith(":") or (core.isupper() and len(core) >= 3)
            if (is_candidate and core and any(c.isalpha() for c in core)
                    and len(core.split()) <= 4 and len(core) <= 40 and key not in ACCEPTED):
                add(n, "NONSTANDARD_HEADING")

        if "\t" in raw or SPACING_RUN.search(raw):
            add(n, "TAB_OR_SPACE_RUN")
        if "|" in raw:
            add(n, "TABLE_PIPE")
        if lead in BULLETS:
            add(n, "UNUSUAL_BULLET")
        body = s[1:] if lead in BULLETS else s
        if any(ord(ch) > 127 and (ch in BULLETS or unicodedata.category(ch) in ("So", "Sm"))
               for ch in body):
            add(n, "SPECIAL_SYMBOL")

        names = set()
        for name, pattern in DATE_PATTERNS:
            hits = len(pattern.findall(s))
            if hits:
                names.add(name)
                format_lines[name] = format_lines.get(name, 0) + 1
        if names:
            date_hits.append((n, names))

        if RANGE.search(s):
            has_range = True
        if EMAIL.search(s):
            has_email = True
        for match in PHONE_CANDIDATE.finditer(s):
            if 10 <= sum(ch.isdigit() for ch in match.group()) <= 15:
                has_phone = True

        if len(raw) > LONG_LINE:
            add(n, "LONG_LINE")

    order = [name for name, _ in DATE_PATTERNS]
    present = [name for name in order if format_lines.get(name)]
    if len(present) > 1:
        dominant = max(present, key=lambda name: format_lines[name])
        for n, names in date_hits:
            for name in sorted(names - {dominant}):
                add(n, "DATE_FORMAT_MIXED",
                    f"minority date format '{name}'; most common format in file is '{dominant}'")

    for group_name, _members, label in GROUPS:
        if group_name not in found_groups:
            add(0, "MISSING_SECTION", f"no standard heading found for {label}")
    if not has_range:
        add(0, "NO_DATE_RANGE")
    if not has_email:
        add(0, "MISSING_EMAIL")
    if not has_phone:
        add(0, "MISSING_PHONE")
    return findings


def main(argv):
    if len(argv) != 2:
        fail("usage: ats_check.py <input-file>")
    try:
        with open(argv[1], "rb") as handle:
            raw = handle.read(MAX_BYTES + 1)
    except FileNotFoundError:
        fail("file_not_found")
    except OSError:
        fail("unreadable_input")
    if len(raw) > MAX_BYTES:
        fail("input_over_2_mb")
    if b"\x00" in raw:
        fail("binary_input")
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        fail("invalid_utf8")

    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    if lines and lines[-1] == "":
        lines.pop()

    findings = sorted(analyze(lines), key=lambda f: (f["line"], f["code"]))
    counts = {}
    for item in findings:
        counts[item["code"]] = counts.get(item["code"], 0) + 1
    result = {
        "lines_scanned": len(lines),
        "total": len(findings),
        "counts": dict(sorted(counts.items())),
        "findings": findings,
    }
    sys.stdout.write(json.dumps(result, ensure_ascii=True, indent=2) + "\n")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
