"""docx_inspect: read-only structure report for a Word .docx file.

Usage:
    python -I scripts/docx_inspect.py <file.docx>

The script reads word/document.xml and, when present, word/comments.xml from
the .docx zip container. It prints one JSON report to stdout. It never writes
a file, never opens a network connection and never starts another process.
The only output channel is stdout, so an output path can never overlap an
input path.

Exit codes: 0 no findings, 1 findings present, 2 usage or input error.
Errors are printed as one line of JSON on stdout, for example:
    {"error": "not a .docx file: zip container is damaged or missing"}
"""

import argparse
import io
import json
import os
import re
import sys
import zipfile
import zlib
import xml.etree.ElementTree as ET
from collections import Counter

MAX_FILE_BYTES = 2 * 1024 * 1024        # input file cap (working value)
MAX_ENTRIES = 2000                      # zip entries cap (working value)
MAX_PART_BYTES = 8 * 1024 * 1024        # bytes read per part, after decompression
MAX_DECLARED_BYTES = 20 * 1024 * 1024   # header-declared size refusal
MAX_RATIO = 100                         # compression ratio refusal (working value)
RATIO_CHECK_FROM = 1024 * 1024          # ratio is only checked above this size
MAX_DEPTH = 200                         # XML nesting cap (working value)
MAX_AUTHORS = 50
MAX_TEXT = 120                          # heading text is truncated to this many chars
MAX_AUTHOR_CHARS = 80
HEADING_RE = re.compile(r"^heading([1-9])$", re.IGNORECASE)
BREAK_TAGS = ("drawing", "pict", "object", "br", "tab")


class InputError(Exception):
    """Usage or input problem; the message is printed as one JSON line."""


def local(tag):
    """Return the local name of an XML tag, without its namespace part."""
    if not isinstance(tag, str):
        return ""
    return tag.rsplit("}", 1)[-1]


def attr(elem, name):
    """Return an attribute value by local name, or None."""
    for key, value in elem.attrib.items():
        if local(key) == name:
            return value
    return None


def read_part(zf, name, required):
    """Read one zip part with size and ratio guards. Returns bytes or None."""
    try:
        info = zf.getinfo(name)
    except KeyError:
        if required:
            raise InputError("not a .docx file: missing word/document.xml")
        return None
    if info.file_size > MAX_DECLARED_BYTES:
        raise InputError(name + " declares more than 20 MB uncompressed")
    if (info.file_size > RATIO_CHECK_FROM and info.compress_size > 0
            and info.file_size > MAX_RATIO * info.compress_size):
        raise InputError(name + " has a compression ratio above 100 to 1")
    with zf.open(info) as handle:
        data = handle.read(MAX_PART_BYTES + 1)
    if len(data) > MAX_PART_BYTES:
        raise InputError(name + " exceeds 8 MB after decompression")
    return data


def parse_xml(data, name):
    """Parse one XML part with a nesting cap and no DTD allowed."""
    if b"<!DOCTYPE" in data or b"<!ENTITY" in data:
        raise InputError(name + " contains a DTD or entity declaration")
    root = None
    depth = 0
    try:
        for event, elem in ET.iterparse(io.BytesIO(data), events=("start", "end")):
            if event == "start":
                if root is None:
                    root = elem
                depth += 1
                if depth > MAX_DEPTH:
                    raise InputError(name + " nests deeper than 200 levels")
            else:
                depth -= 1
    except ET.ParseError:
        raise InputError(name + " is not well-formed XML or not valid UTF-8")
    except (MemoryError, RecursionError):
        raise InputError(name + " is too large or too deeply nested to parse")
    if root is None:
        raise InputError(name + " is empty")
    return root


def paragraph_text(para):
    """Concatenate the text runs (w:t) of a paragraph."""
    return "".join((e.text or "") for e in para.iter() if local(e.tag) == "t")


def has_break(para):
    """True when the paragraph holds a drawing, picture, object, break or tab."""
    for e in para.iter():
        if local(e.tag) in BREAK_TAGS:
            return True
    return False


def heading_level(para):
    """Return 1..9 from a Heading styleId (for example Heading2), else None."""
    for child in para:
        if local(child.tag) != "pPr":
            continue
        for sub in child:
            if local(sub.tag) == "pStyle":
                match = HEADING_RE.match(attr(sub, "val") or "")
                if match:
                    return int(match.group(1))
    return None


def analyze(doc_root, com_root):
    """Walk document.xml in order and build the report dictionary."""
    counts = Counter()
    authors = set()
    outline = []
    skips = []
    paragraphs = 0
    empty = 0
    prev_level = 0
    for elem in doc_root.iter():
        name = local(elem.tag)
        counts[name] += 1
        if name in ("ins", "del"):
            author = attr(elem, "author")
            if author:
                authors.add(author)
        elif name == "p":
            paragraphs += 1
            text = paragraph_text(elem).strip()
            if not text and not has_break(elem):
                empty += 1
            level = heading_level(elem)
            if level is not None:
                if level > prev_level + 1:
                    skips.append({"paragraph": paragraphs,
                                  "from_level": prev_level,
                                  "to_level": level})
                prev_level = level
                outline.append({"paragraph": paragraphs,
                                "level": level,
                                "text": text[:MAX_TEXT]})
    comments = 0
    if com_root is not None:
        for elem in com_root.iter():
            if local(elem.tag) == "comment":
                comments += 1
                author = attr(elem, "author")
                if author:
                    authors.add(author)
    insertions = counts["ins"]
    deletions = counts["del"]
    findings = comments + insertions + deletions + len(skips) + empty
    author_list = [a[:MAX_AUTHOR_CHARS] for a in sorted(authors)][:MAX_AUTHORS]
    return {
        "paragraphs": paragraphs,
        "empty_paragraphs": empty,
        "tables": counts["tbl"],
        "images": counts["drawing"] + counts["pict"],
        "comments": comments,
        "tracked_insertions": insertions,
        "tracked_deletions": deletions,
        "heading_outline": outline,
        "heading_skips": skips,
        "authors": author_list,
        "findings": findings,
    }


def inspect(path):
    """Open a .docx read-only and return the report dictionary."""
    if not os.path.isfile(path):
        raise InputError("file not found")
    if os.path.getsize(path) > MAX_FILE_BYTES:
        raise InputError("file is larger than 2 MB")
    with open(path, "rb") as handle:
        raw = handle.read(MAX_FILE_BYTES + 1)
    if len(raw) > MAX_FILE_BYTES:
        raise InputError("file is larger than 2 MB")
    try:
        with zipfile.ZipFile(io.BytesIO(raw)) as zf:
            if len(zf.infolist()) > MAX_ENTRIES:
                raise InputError("zip has more than 2000 entries")
            doc_bytes = read_part(zf, "word/document.xml", True)
            com_bytes = read_part(zf, "word/comments.xml", False)
    except zipfile.BadZipFile:
        raise InputError("not a .docx file: zip container is damaged or missing")
    except (zlib.error, NotImplementedError, RuntimeError, EOFError):
        raise InputError("a zip entry could not be decompressed")
    doc_root = parse_xml(doc_bytes, "word/document.xml")
    com_root = None
    if com_bytes is not None:
        com_root = parse_xml(com_bytes, "word/comments.xml")
    return analyze(doc_root, com_root)


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Read-only structure report for a .docx file.")
    parser.add_argument("path", help="path to the .docx file to inspect")
    args = parser.parse_args(argv)
    try:
        report = inspect(args.path)
    except InputError as exc:
        sys.stdout.write(json.dumps({"error": str(exc)}) + "\n")
        return 2
    except MemoryError:
        sys.stdout.write(json.dumps({"error": "input too large to process"}) + "\n")
        return 2
    sys.stdout.write(json.dumps(report, indent=2, ensure_ascii=True) + "\n")
    return 1 if report["findings"] else 0


if __name__ == "__main__":
    sys.exit(main())
