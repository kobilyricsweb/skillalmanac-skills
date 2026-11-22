"""Audit a .pptx deck for text-heavy slides, missing titles and missing speaker notes.

Read-only. Stdlib only (argparse, json, os, posixpath, re, sys, zipfile, zlib,
xml.etree.ElementTree). The .pptx is opened as a zip; each ppt/slides/slideN.xml
is parsed, and the notes slide linked from its relationships file is checked.
Prints one JSON document to stdout. Writes no files and makes no network calls.

Exit codes: 0 no findings, 1 one or more findings (dense_text,
too_many_bullets, missing_title), 2 usage or input error. On exit 2 a single
line of JSON {"error": "..."} is written to stderr.
"""
import argparse
import json
import os
import posixpath
import re
import sys
import zipfile
import zlib
import xml.etree.ElementTree as ET

MAX_FILE_BYTES = 2 * 1024 * 1024
MAX_ENTRIES = 300
MAX_TOTAL_UNCOMPRESSED = 20 * 1024 * 1024
MAX_ENTRY_UNCOMPRESSED = 4 * 1024 * 1024
MAX_COMPRESSION_RATIO = 100
MAX_XML_DEPTH = 64
MAX_SLIDES = 200

NS_A = "{http://schemas.openxmlformats.org/drawingml/2006/main}"
NS_P = "{http://schemas.openxmlformats.org/presentationml/2006/main}"
NS_REL = "{http://schemas.openxmlformats.org/package/2006/relationships}"

SLIDE_RE = re.compile(r"^ppt/slides/slide(\d+)\.xml$")
NOTES_PH_SKIP = ("sldImg", "sldNum", "hdr", "ftr", "dt")


class InputError(Exception):
    """Raised for any input the script refuses. Message goes to the error JSON."""


def read_entry(zf, name):
    """Return the bytes of one zip member, enforcing size and ratio caps."""
    info = zf.getinfo(name)
    if info.file_size > MAX_ENTRY_UNCOMPRESSED:
        raise InputError("entry too large: " + name)
    if info.compress_size and info.file_size > info.compress_size * MAX_COMPRESSION_RATIO:
        raise InputError("compression ratio too high: " + name)
    with zf.open(info) as fh:
        data = fh.read(MAX_ENTRY_UNCOMPRESSED + 1)
    if len(data) > MAX_ENTRY_UNCOMPRESSED:
        raise InputError("entry expands beyond cap: " + name)
    if b"<!DOCTYPE" in data or b"<!ENTITY" in data:
        raise InputError("DTD or entity declaration refused: " + name)
    return data


def parse_xml(data, name):
    """Parse XML bytes into an element tree, refusing deep nesting and bad encoding."""
    parser = ET.XMLPullParser(events=("start", "end"))
    try:
        parser.feed(data)
        parser.close()
    except ET.ParseError:
        raise InputError("malformed or non-UTF-8 XML: " + name)
    depth = 0
    root = None
    for event, element in parser.read_events():
        if event == "start":
            depth += 1
            if depth > MAX_XML_DEPTH:
                raise InputError("XML nesting too deep: " + name)
        else:
            depth -= 1
            if depth == 0:
                root = element
    if root is None:
        raise InputError("empty XML: " + name)
    return root


def run_text(element):
    """Concatenate the text of a:r runs under element. a:fld fields are skipped."""
    parts = []
    for run in element.iter(NS_A + "r"):
        t = run.find(NS_A + "t")
        if t is not None and t.text:
            parts.append(t.text)
    return "".join(parts)


def word_count(element):
    total = 0
    for run in element.iter(NS_A + "r"):
        t = run.find(NS_A + "t")
        if t is not None and t.text:
            total += len(t.text.split())
    return total


def is_title(sp):
    ph = sp.find(NS_P + "nvSpPr/" + NS_P + "nvPr/" + NS_P + "ph")
    return ph is not None and ph.get("type") in ("title", "ctrTitle")


def slide_metrics(root):
    words = word_count(root)
    title_present = False
    bullets = 0
    for sp in root.iter(NS_P + "sp"):
        if is_title(sp):
            if run_text(sp).strip():
                title_present = True
            continue
        for para in sp.iter(NS_A + "p"):
            if not run_text(para).strip():
                continue
            ppr = para.find(NS_A + "pPr")
            if ppr is not None and ppr.find(NS_A + "buNone") is not None:
                continue
            bullets += 1
    return words, bullets, title_present


def notes_body_text(root):
    """Text of the notes body placeholder, ignoring slide image and number placeholders."""
    parts = []
    for sp in root.iter(NS_P + "sp"):
        ph = sp.find(NS_P + "nvSpPr/" + NS_P + "nvPr/" + NS_P + "ph")
        if ph is None or ph.get("type") in NOTES_PH_SKIP:
            continue
        text = run_text(sp).strip()
        if text:
            parts.append(text)
    return " ".join(parts)


def notes_present(zf, names, slide_no):
    rels_name = "ppt/slides/_rels/slide%d.xml.rels" % slide_no
    if rels_name not in names:
        return False
    rels_root = parse_xml(read_entry(zf, rels_name), rels_name)
    for rel in rels_root.iter(NS_REL + "Relationship"):
        if not (rel.get("Type") or "").endswith("/notesSlide"):
            continue
        target = rel.get("Target") or ""
        full = posixpath.normpath(posixpath.join("ppt/slides", target)).lstrip("/")
        if full not in names:
            return False
        notes_root = parse_xml(read_entry(zf, full), full)
        return notes_body_text(notes_root) != ""
    return False


def audit(path, max_words, max_bullets):
    if not os.path.isfile(path):
        raise InputError("input is not a readable file")
    if os.path.getsize(path) > MAX_FILE_BYTES:
        raise InputError("input exceeds 2 MB")
    try:
        zf = zipfile.ZipFile(path)
    except zipfile.BadZipFile:
        raise InputError("input is not a zip container")
    with zf:
        infos = zf.infolist()
        if len(infos) > MAX_ENTRIES:
            raise InputError("too many zip entries")
        if sum(i.file_size for i in infos) > MAX_TOTAL_UNCOMPRESSED:
            raise InputError("uncompressed size exceeds 20 MB")
        names = set(zf.namelist())
        if "ppt/presentation.xml" not in names:
            raise InputError("not a pptx package: ppt/presentation.xml missing")
        parse_xml(read_entry(zf, "ppt/presentation.xml"), "ppt/presentation.xml")
        slide_nos = sorted(
            int(m.group(1)) for m in (SLIDE_RE.match(n) for n in names) if m
        )
        if not slide_nos:
            raise InputError("no slides found")
        if len(slide_nos) > MAX_SLIDES:
            raise InputError("too many slides")
        slides = []
        findings = 0
        without_notes = 0
        flagged = 0
        for no in slide_nos:
            name = "ppt/slides/slide%d.xml" % no
            root = parse_xml(read_entry(zf, name), name)
            words, bullets, title_present = slide_metrics(root)
            has_notes = notes_present(zf, names, no)
            flags = []
            if words > max_words:
                flags.append("dense_text")
            if bullets > max_bullets:
                flags.append("too_many_bullets")
            if not title_present:
                flags.append("missing_title")
            if not has_notes:
                without_notes += 1
            if flags:
                flagged += 1
                findings += len(flags)
            slides.append({
                "slide": no,
                "words": words,
                "bullets": bullets,
                "title_present": title_present,
                "notes_present": has_notes,
                "flags": flags,
            })
    return {
        "tool": "pptx_density",
        "input": os.path.basename(path),
        "thresholds": {"max_words": max_words, "max_bullets": max_bullets},
        "slide_count": len(slides),
        "slides": slides,
        "findings_count": findings,
        "summary": {
            "slides_flagged": flagged,
            "slides_without_notes": without_notes,
        },
    }


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Audit a .pptx deck for dense slides, missing titles and missing notes."
    )
    parser.add_argument("input", help="path to a .pptx file (read only)")
    parser.add_argument("--max-words", type=int, default=60,
                        help="flag a slide whose total word count is above this (default 60)")
    parser.add_argument("--max-bullets", type=int, default=7,
                        help="flag a slide with more bullet paragraphs than this (default 7)")
    args = parser.parse_args(argv)
    if args.max_words < 1 or args.max_bullets < 1:
        parser.error("--max-words and --max-bullets must be 1 or more")
    try:
        result = audit(args.input, args.max_words, args.max_bullets)
    except InputError as exc:
        sys.stderr.write(json.dumps({"error": str(exc)}) + "\n")
        return 2
    except (OSError, zipfile.BadZipFile, zlib.error, RuntimeError, KeyError,
            RecursionError, MemoryError):
        sys.stderr.write(json.dumps({"error": "unreadable package or resource limit"}) + "\n")
        return 2
    print(json.dumps(result, indent=2))
    return 1 if result["findings_count"] else 0


if __name__ == "__main__":
    sys.exit(main())
