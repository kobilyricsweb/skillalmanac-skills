"""Build a sitemap.xml from a plain text list of page URLs.

Input: one entry per line, a URL optionally followed by one space or tab and a
lastmod date. Blank lines and lines starting with a hash are skipped.

The script makes no network calls, runs no other programs, and reads the input
only. It writes a NEW sitemap file (exclusive create) containing every entry
that passes the checks, and prints one JSON summary line on stdout.

Usage: python -I scripts/sitemap_build.py <input-file> <output-file>

Exit codes: 0 every entry written, 1 some entries excluded (output written),
2 usage or input error (nothing written, one-line JSON error on stderr).
"""
import datetime
import json
import re
import sys
from collections import Counter
from xml.sax.saxutils import escape

MAX_INPUT_BYTES = 2 * 1024 * 1024
MAX_URLS = 50000
MAX_OUTPUT_BYTES = 52428800
MAX_URL_CHARS = 2048
NAMESPACE = "http://www.sitemaps.org/schemas/sitemap/0.9"
LASTMOD_RE = re.compile(
    r"[0-9]{4}-[0-9]{2}-[0-9]{2}"
    r"(T([01][0-9]|2[0-3]):[0-5][0-9](:[0-5][0-9](\.[0-9]+)?)?"
    r"(Z|[+-]([01][0-9]|2[0-3]):[0-5][0-9])?)?"
)
CODES = (
    "BAD_LINE",
    "INVALID_URL",
    "FRAGMENT",
    "TOO_LONG",
    "BAD_LASTMOD",
    "MIXED_SCHEME",
    "HOST_MISMATCH",
    "DUPLICATE",
)


def fail(code, message):
    sys.stderr.write(json.dumps({"error": code, "message": message}) + "\n")
    return 2


def read_entries(path):
    """Return (line_number, fields) for every entry line; raise ValueError(code, msg)."""
    try:
        with open(path, "rb") as handle:
            data = handle.read(MAX_INPUT_BYTES + 1)
    except FileNotFoundError:
        raise ValueError("FILE_NOT_FOUND")
    except OSError:
        raise ValueError("INPUT_READ_ERROR")
    if len(data) > MAX_INPUT_BYTES:
        raise ValueError("INPUT_TOO_LARGE")
    try:
        text = data.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise ValueError("INVALID_UTF8")
    entries = []
    for number, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        entries.append((number, stripped.split()))
    return entries


def split_url(url):
    """Split an absolute URL into (scheme, netloc, path, query); None when there is no scheme separator."""
    scheme, sep, rest = url.partition("://")
    if not sep:
        return None
    cut = len(rest)
    for ch in "/?#":
        pos = rest.find(ch)
        if 0 <= pos < cut:
            cut = pos
    remainder = rest[cut:].split("#", 1)[0]
    path, _, query = remainder.partition("?")
    return scheme.lower(), rest[:cut].lower(), path, query


def parse_base(url):
    """Return (scheme, netloc, path, query) for a usable http or https URL, else None."""
    if not url.isascii() or any(ord(ch) < 33 or ord(ch) == 127 for ch in url):
        return None
    parts = split_url(url)
    if parts is None:
        return None
    scheme, netloc = parts[0], parts[1]
    if scheme not in ("http", "https"):
        return None
    if not netloc or "@" in netloc or "[" in netloc:
        return None
    host, _, port = netloc.partition(":")
    if not host or (port and not port.isdigit()):
        return None
    return parts


def valid_lastmod(value):
    if not LASTMOD_RE.fullmatch(value):
        return False
    try:
        datetime.date.fromisoformat(value[:10])
    except ValueError:
        return False
    return True


def duplicate_key(base):
    netloc, path, query = base[1], base[2], base[3]
    return (netloc, path.rstrip("/") or "/", query)


def build_xml(kept):
    lines = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="%s">' % NAMESPACE]
    for url, lastmod in kept:
        item = "<loc>%s</loc>" % escape(url)
        if lastmod is not None:
            item += "<lastmod>%s</lastmod>" % lastmod
        lines.append("<url>%s</url>" % item)
    lines.append("</urlset>")
    return "\n".join(lines) + "\n"


def main(argv):
    if len(argv) != 3:
        return fail("USAGE", "usage: sitemap_build.py <input-file> <output-file>")
    input_path, output_path = argv[1], argv[2]
    try:
        entries = read_entries(input_path)
    except ValueError as err:
        return fail(str(err), "input file could not be used; see the error code")
    if not entries:
        return fail("NO_ENTRIES", "input has no URL lines")

    # Pass 1: fields, usable base URLs, and the reference scheme and host.
    records = []
    for number, fields in entries:
        if len(fields) > 2:
            records.append((number, None, None, "BAD_LINE"))
        else:
            lastmod = fields[1] if len(fields) == 2 else None
            records.append((number, fields[0], lastmod, None))
    bases = {}
    schemes = Counter()
    for index, (number, url, lastmod, code) in enumerate(records):
        if url is None:
            continue
        bases[index] = parse_base(url)
        if bases[index] is not None:
            schemes[bases[index][0]] += 1
    if not schemes:
        return fail("NO_VALID_URLS", "no line holds an http or https URL with a host")
    ref_scheme = "https" if schemes["https"] >= schemes["http"] else "http"
    hosts = Counter(
        base[1] for base in bases.values() if base is not None and base[0] == ref_scheme
    )
    ref_host = hosts.most_common(1)[0][0]

    # Pass 2: first failing check wins; the first kept copy of a duplicate stays.
    kept = []
    findings = []
    seen = set()
    for index, (number, url, lastmod, code) in enumerate(records):
        if code is None:
            base = bases[index]
            if base is None:
                code = "INVALID_URL"
            elif "#" in url:
                code = "FRAGMENT"
            elif len(url) > MAX_URL_CHARS:
                code = "TOO_LONG"
            elif lastmod is not None and not valid_lastmod(lastmod):
                code = "BAD_LASTMOD"
            elif base[0] != ref_scheme:
                code = "MIXED_SCHEME"
            elif base[1] != ref_host:
                code = "HOST_MISMATCH"
            else:
                key = duplicate_key(base)
                if key in seen:
                    code = "DUPLICATE"
                else:
                    seen.add(key)
                    kept.append((url, lastmod))
                    continue
        findings.append((number, code))

    if not kept:
        return fail("NO_VALID_URLS", "every line was excluded; fix the input and run again")
    if len(kept) > MAX_URLS:
        return fail("URL_LIMIT_EXCEEDED", "more than 50000 URLs; split the list into several sitemaps")
    xml_text = build_xml(kept)
    if len(xml_text.encode("utf-8")) > MAX_OUTPUT_BYTES:
        return fail("SIZE_LIMIT_EXCEEDED", "sitemap would exceed 50 MB uncompressed")
    try:
        with open(output_path, "x", encoding="utf-8", newline="\n") as handle:
            handle.write(xml_text)
    except FileExistsError:
        return fail("OUTPUT_EXISTS", "output path already exists; choose a new file name")
    except OSError:
        return fail("OUTPUT_WRITE_ERROR", "output file could not be created")

    counts = Counter(code for _, code in findings)
    summary = {
        "status": "findings" if findings else "ok",
        "entries": len(records),
        "urls_written": len(kept),
        "reference_scheme": ref_scheme,
        "reference_host": ref_host,
        "counts": {code: counts.get(code, 0) for code in CODES},
        "excluded": [{"line": number, "code": code} for number, code in findings],
    }
    sys.stdout.write(json.dumps(summary, separators=(",", ":")) + "\n")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
