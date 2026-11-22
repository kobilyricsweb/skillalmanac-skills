"""Build a sitemap index XML file from a list of sitemap shard URLs.

Usage:
  python -I scripts/sitemap_index.py --shards <input-file> --host <host> --out <output-xml> [--local-shard <shard-xml>]...

Reads the shard list (one URL per line, optional lastmod after whitespace),
checks scheme and host, drops exact duplicate URLs, writes a sitemap index
with exclusive-create, and prints one JSON report on stdout.
Local shard files (sitemap urlset XML) are counted against the 50,000 URL limit.

Exit codes: 0 no findings, 1 findings reported, 2 usage or input error.
The input and local shard files are read only. The output file is never overwritten.
"""
import argparse
import json
import os
import re
import sys
import xml.etree.ElementTree as ET
from datetime import datetime
from xml.sax.saxutils import escape

MAX_INPUT_BYTES = 2 * 1024 * 1024
MAX_ENTRIES = 50000
SITEMAP_NS = "http://www.sitemaps.org/schemas/sitemap/0.9"
LASTMOD_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
LASTMOD_DATETIME = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(:\d{2}(\.\d+)?)?(Z|[+-]\d{2}:\d{2})$"
)
DTD_OR_ENTITY_PATTERNS = [
    re.compile(re.escape(text.encode(enc)), re.IGNORECASE)
    for enc in ("utf-8", "utf-16-le", "utf-16-be")
    for text in ("<!DOCTYPE", "<!ENTITY")
]
UNSAFE_BOMS = (b"\xff\xfe", b"\xfe\xff", b"\x00\x00\xfe\xff")


def fail(message):
    """Print a one-line JSON error on stderr and exit 2."""
    sys.stderr.write(json.dumps({"error": message}) + "\n")
    sys.exit(2)


def read_capped(path):
    """Return the bytes of a file no larger than 2 MB."""
    name = os.path.basename(path)
    try:
        size = os.path.getsize(path)
    except OSError:
        fail("cannot read file: " + name)
    if size > MAX_INPUT_BYTES:
        fail("file larger than 2 MB: " + name)
    try:
        with open(path, "rb") as fh:
            return fh.read(MAX_INPUT_BYTES + 1)
    except OSError:
        fail("cannot read file: " + name)


def valid_lastmod(value):
    """Accept YYYY-MM-DD or a W3C datetime with a timezone designator."""
    if LASTMOD_DATE.match(value):
        try:
            datetime.strptime(value, "%Y-%m-%d")
            return True
        except ValueError:
            return False
    if LASTMOD_DATETIME.match(value):
        try:
            datetime.strptime(value[:10], "%Y-%m-%d")
            return True
        except ValueError:
            return False
    return False


def parse_shards(text, host):
    """Return (input_lines, entries, findings, duplicates, rejected)."""
    findings = []
    entries = []
    seen = set()
    input_lines = 0
    duplicates = 0
    rejected = 0
    for line_no, raw in enumerate(text.splitlines(), 1):
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            continue
        input_lines += 1
        fields = stripped.split()
        if len(fields) > 2:
            findings.append({"code": "INPUT_LINE_MALFORMED", "line": line_no,
                             "detail": "more than two fields on the line"})
            rejected += 1
            continue
        url = fields[0]
        lastmod = fields[1] if len(fields) == 2 else None
        if not url.lower().startswith("https://"):
            findings.append({"code": "INPUT_NOT_HTTPS", "line": line_no,
                             "detail": "URL scheme is not https"})
            rejected += 1
            continue
        netloc = re.split(r"[/?#]", url[len("https://"):], 1)[0]
        if netloc.lower() != host.lower():
            findings.append({"code": "HOST_MISMATCH", "line": line_no,
                             "detail": "host differs from --host"})
            rejected += 1
            continue
        if url in seen:
            findings.append({"code": "DUPLICATE_SHARD", "line": line_no,
                             "detail": "URL already listed earlier; line dropped"})
            duplicates += 1
            continue
        seen.add(url)
        if lastmod is not None and not valid_lastmod(lastmod):
            findings.append({"code": "LASTMOD_INVALID", "line": line_no,
                             "detail": "lastmod is not YYYY-MM-DD or W3C datetime; entry written without lastmod"})
            lastmod = None
        entries.append((url, lastmod))
    return input_lines, entries, findings, duplicates, rejected


def refuse_unsafe_xml(data, name):
    """Scan the raw bytes before any parse; refuse DTD or entity text in
    UTF-8, UTF-16 LE or UTF-16 BE, UTF-16/UTF-32 byte order marks, and NUL bytes."""
    for pattern in DTD_OR_ENTITY_PATTERNS:
        if pattern.search(data):
            fail("DTD or entity declaration refused: " + name)
    if data.startswith(UNSAFE_BOMS) or b"\x00" in data:
        fail("UTF-16, UTF-32, or NUL bytes refused: " + name)


def count_local_shard(path):
    """Return the number of url elements in a local sitemap urlset file."""
    name = os.path.basename(path)
    data = read_capped(path)
    refuse_unsafe_xml(data, name)
    try:
        root = ET.fromstring(data)
    except ET.ParseError:
        fail("invalid XML: " + name)
    if root.tag.split("}")[-1] != "urlset":
        fail("root element is not urlset: " + name)
    return sum(1 for child in root if child.tag.split("}")[-1] == "url")


def write_index(path, entries):
    """Write the sitemap index with exclusive-create mode."""
    lines = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<sitemapindex xmlns="%s">' % SITEMAP_NS]
    for url, lastmod in entries:
        lines.append("  <sitemap>")
        lines.append("    <loc>%s</loc>" % escape(url))
        if lastmod is not None:
            lines.append("    <lastmod>%s</lastmod>" % escape(lastmod))
        lines.append("  </sitemap>")
    lines.append("</sitemapindex>")
    data = "\n".join(lines) + "\n"
    try:
        with open(path, "x", encoding="utf-8", newline="\n") as fh:
            fh.write(data)
    except FileExistsError:
        fail("output file already exists")
    except OSError:
        fail("cannot write output file")


def main(argv=None):
    ap = argparse.ArgumentParser(description="Build a sitemap index from shard URLs.")
    ap.add_argument("--shards", required=True, help="text file, one shard URL per line")
    ap.add_argument("--host", required=True, help="required host, for example www.example.com")
    ap.add_argument("--out", required=True, help="new XML file to create; must not exist")
    ap.add_argument("--local-shard", action="append", default=[],
                    help="local sitemap urlset file to count; repeat for more files")
    args = ap.parse_args(argv)

    host = args.host.strip()
    if not host or "/" in host or "://" in host or "@" in host:
        fail("--host must be a bare host name")

    if os.path.exists(args.out):
        fail("output file already exists")
    input_paths = [os.path.normcase(os.path.abspath(p))
                   for p in [args.shards] + list(args.local_shard)]
    if os.path.normcase(os.path.abspath(args.out)) in input_paths:
        fail("output path is also an input path")

    try:
        text = read_capped(args.shards).decode("utf-8-sig")
    except UnicodeDecodeError:
        fail("shard list is not valid UTF-8")

    input_lines, entries, findings, duplicates, rejected = parse_shards(text, host)

    local_shards = []
    for local_path in args.local_shard:
        count = count_local_shard(local_path)
        local_shards.append({"file": os.path.basename(local_path), "url_count": count})
        if count > MAX_ENTRIES:
            findings.append({"code": "LOCAL_SHARD_OVER_LIMIT", "line": None,
                             "detail": "local shard has more than 50,000 url elements"})

    status = "written"
    if not entries:
        findings.append({"code": "NO_VALID_SHARDS", "line": None,
                         "detail": "no entries remain after filtering; nothing written"})
        status = "not_written"
    elif len(entries) > MAX_ENTRIES:
        findings.append({"code": "SHARD_COUNT_OVER_LIMIT", "line": None,
                         "detail": "more than 50,000 shard entries; nothing written"})
        status = "not_written"

    if status == "written":
        write_index(args.out, entries)

    report = {
        "status": status,
        "output_file": os.path.basename(args.out),
        "input_lines": input_lines,
        "entries_written": len(entries) if status == "written" else 0,
        "duplicates_dropped": duplicates,
        "rejected_lines": rejected,
        "local_shards": local_shards,
        "findings": findings,
    }
    print(json.dumps(report, indent=2))
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
