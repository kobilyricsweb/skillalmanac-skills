"""Extract slide titles, body text, table cells and speaker notes from a .pptx file.

Usage:
    python pptx_text.py <input-file> [--format {md,txt}] [--out <new-file>]

Rendered text goes to stdout, or to --out when given. --out must not exist and
must not be the input path. On success a one-line JSON summary goes to stderr.
On failure a one-line JSON error goes to stderr and the exit code is 2.

Exit codes:
    0  ok: every slide has a title, body text or table text
    1  findings: one or more empty slides (the text is still written)
    2  usage or input error

Standard library only. No network, no subprocess, no eval. The input is read only.
"""

import argparse
import json
import os
import posixpath
import sys
import xml.etree.ElementTree as ET
import zipfile
import zlib

MAX_INPUT_BYTES = 2 * 1024 * 1024
MAX_ENTRIES = 400
MAX_UNCOMPRESSED_BYTES = 20 * 1024 * 1024
MAX_PART_BYTES = 5 * 1024 * 1024
MAX_SLIDES = 300

NS_P = "http://schemas.openxmlformats.org/presentationml/2006/main"
NS_A = "http://schemas.openxmlformats.org/drawingml/2006/main"
NS_R = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
NS_PKG_REL = "http://schemas.openxmlformats.org/package/2006/relationships"
PRESENTATION_PART = "ppt/presentation.xml"
SKIPPED_PH_TYPES = ("dt", "ftr", "sldNum")
TITLE_PH_TYPES = ("title", "ctrTitle")


class ExtractError(Exception):
    def __init__(self, code, message):
        Exception.__init__(self, message)
        self.code = code
        self.message = message


def emit_error(code, message):
    sys.stderr.write(json.dumps({"error": code, "message": message}) + "\n")
    sys.exit(2)


class _Parser(argparse.ArgumentParser):
    def error(self, message):
        emit_error("usage", message)


UTF_BOM_PREFIXES = (b"\xff\xfe", b"\xfe\xff")
UNSAFE_NEEDLES = tuple(
    text.encode(enc).lower()
    for text in ("<!DOCTYPE", "<!ENTITY")
    for enc in ("utf-8", "utf-16-le", "utf-16-be"))


def unsafe_bytes(data):
    # Raw-byte scan before any parse: DTD or entity markers in UTF-8, UTF-16 LE
    # or UTF-16 BE, case-insensitive; UTF-16/UTF-32 byte-order marks and NUL
    # bytes are refused outright, so no encoded form reaches the XML parser.
    if data.startswith(UTF_BOM_PREFIXES) or b"\x00" in data:
        return True
    lowered = data.lower()
    return any(needle in lowered for needle in UNSAFE_NEEDLES)


def read_part(zf, name):
    try:
        info = zf.getinfo(name)
    except KeyError:
        raise ExtractError("missing_part", "package part not found: " + name)
    if info.file_size > MAX_PART_BYTES:
        raise ExtractError("part_too_large", "package part is larger than 5 MB: " + name)
    try:
        data = zf.read(name)
    except (zipfile.BadZipFile, RuntimeError, NotImplementedError, OSError,
            EOFError, ValueError, zlib.error):
        raise ExtractError("bad_part", "package part cannot be read: " + name)
    if len(data) > MAX_PART_BYTES:
        raise ExtractError("part_too_large", "package part is larger than 5 MB: " + name)
    if unsafe_bytes(data):
        raise ExtractError("unsafe_xml", "DTD, entity, UTF-16/UTF-32 marker or NUL byte refused: " + name)
    return data


def parse_xml(data, name):
    try:
        return ET.fromstring(data)
    except ET.ParseError:
        raise ExtractError("bad_xml", "XML part cannot be parsed: " + name)


def resolve_target(base_dir, target):
    if target.startswith("/"):
        path = target.lstrip("/")
    else:
        path = posixpath.normpath(posixpath.join(base_dir, target))
    if path == ".." or path.startswith("../") or path.startswith("/"):
        raise ExtractError("bad_structure", "relationship target leaves the package")
    return path


def read_rels(zf, part):
    folder, base = posixpath.split(part)
    rels_name = posixpath.join(folder, "_rels", base + ".rels")
    try:
        zf.getinfo(rels_name)
    except KeyError:
        return {}
    root = parse_xml(read_part(zf, rels_name), rels_name)
    rels = {}
    for rel in root.iter("{%s}Relationship" % NS_PKG_REL):
        if rel.get("TargetMode") == "External":
            continue
        target = resolve_target(folder, rel.get("Target", ""))
        rels[rel.get("Id")] = (rel.get("Type", ""), target)
    return rels


def slide_parts(zf):
    root = parse_xml(read_part(zf, PRESENTATION_PART), PRESENTATION_PART)
    rels = read_rels(zf, PRESENTATION_PART)
    parts = []
    for sld in root.iter("{%s}sldId" % NS_P):
        rid = sld.get("{%s}id" % NS_R)
        if rid not in rels:
            raise ExtractError("bad_structure", "presentation slide relationship is missing")
        parts.append(rels[rid][1])
    return parts


def para_lines(element):
    lines = []
    for para in element.iter("{%s}p" % NS_A):
        text = "".join(t.text or "" for t in para.iter("{%s}t" % NS_A)).strip()
        if text:
            lines.append(text)
    return lines


def parse_slide(root):
    title = None
    body = []
    tables = []
    for sp in root.iter("{%s}sp" % NS_P):
        ph = sp.find(".//{%s}ph" % NS_P)
        kind = "textbox" if ph is None else ph.get("type", "obj")
        if kind in SKIPPED_PH_TYPES:
            continue
        lines = para_lines(sp)
        if not lines:
            continue
        if kind in TITLE_PH_TYPES and title is None:
            title = " ".join(lines)
        else:
            body.extend(lines)
    for frame in root.iter("{%s}graphicFrame" % NS_P):
        tbl = frame.find(".//{%s}tbl" % NS_A)
        if tbl is None:
            continue
        rows = []
        for tr in tbl.findall("{%s}tr" % NS_A):
            rows.append([" ".join(para_lines(tc)) for tc in tr.findall("{%s}tc" % NS_A)])
        if any(cell for row in rows for cell in row):
            tables.append(rows)
    return title, body, tables


def read_notes(zf, part):
    root = parse_xml(read_part(zf, part), part)
    lines = []
    for sp in root.iter("{%s}sp" % NS_P):
        ph = sp.find(".//{%s}ph" % NS_P)
        if ph is not None and ph.get("type") == "body":
            lines.extend(para_lines(sp))
    return lines


def read_deck(path):
    try:
        zf = zipfile.ZipFile(path, "r")
    except zipfile.BadZipFile:
        raise ExtractError("not_zip", "input is not a zip-based .pptx package")
    except OSError:
        raise ExtractError("unreadable", "input file cannot be opened")
    with zf:
        infos = zf.infolist()
        if len(infos) > MAX_ENTRIES:
            raise ExtractError("too_many_entries", "package has more than 400 entries")
        if sum(info.file_size for info in infos) > MAX_UNCOMPRESSED_BYTES:
            raise ExtractError("uncompressed_too_large", "package uncompressed size exceeds 20 MB")
        parts = slide_parts(zf)
        if not parts:
            raise ExtractError("no_slides", "presentation lists no slides")
        if len(parts) > MAX_SLIDES:
            raise ExtractError("too_many_slides", "presentation has more than 300 slides")
        deck = []
        for part in parts:
            title, body, tables = parse_slide(parse_xml(read_part(zf, part), part))
            notes = []
            for rel_type, target in read_rels(zf, part).values():
                if rel_type.endswith("/notesSlide"):
                    notes = read_notes(zf, target)
                    break
            deck.append({"title": title, "body": body, "tables": tables, "notes": notes})
    return deck


def check_output(input_path, out_path):
    if os.path.normcase(os.path.abspath(out_path)) == os.path.normcase(os.path.abspath(input_path)):
        raise ExtractError("same_path", "output path is the input path")
    if os.path.lexists(out_path):
        raise ExtractError("exists", "output file already exists; choose a new name")


def write_new(path, text):
    try:
        with open(path, "x", encoding="utf-8", newline="\n") as handle:
            handle.write(text)
    except FileExistsError:
        raise ExtractError("exists", "output file already exists; choose a new name")
    except OSError:
        raise ExtractError("out_unwritable", "output file cannot be created; check the folder exists")


def render_table(rows, markdown):
    width = max(len(row) for row in rows)
    if width == 0:
        return []
    norm = []
    for row in rows:
        cells = [cell.replace("\n", " ").strip() for cell in row]
        norm.append(cells + [""] * (width - len(cells)))
    if not markdown:
        return [" | ".join(row) for row in norm]
    lines = []
    lines.append("| " + " | ".join(c.replace("|", "\\|") for c in norm[0]) + " |")
    lines.append("| " + " | ".join("---" for _ in range(width)) + " |")
    for row in norm[1:]:
        lines.append("| " + " | ".join(c.replace("|", "\\|") for c in row) + " |")
    return lines


def render(deck, name, markdown):
    out = ["# Slide text: " + name if markdown else "Slide text: " + name, ""]
    for number, slide in enumerate(deck, 1):
        title = slide["title"] or "(no title)"
        head = "Slide %d: %s" % (number, title)
        out.append(("## " if markdown else "") + head)
        out.append("")
        out.append("Body:")
        out.extend(slide["body"] or ["(none)"])
        out.append("")
        for index, rows in enumerate(slide["tables"], 1):
            out.append("Table %d:" % index)
            out.extend(render_table(rows, markdown))
            out.append("")
        out.append("Notes:")
        out.extend(slide["notes"] or ["(none)"])
        out.append("")
    return "\n".join(out).rstrip("\n") + "\n"


def main(argv=None):
    parser = _Parser(prog="pptx_text.py", description="Extract slide text from a .pptx file.")
    parser.add_argument("input", help="path to the .pptx file")
    parser.add_argument("--format", choices=("md", "txt"), default="md")
    parser.add_argument("--out", default=None, help="new file to write; must not exist")
    args = parser.parse_args(argv)
    try:
        if not os.path.isfile(args.input):
            raise ExtractError("not_found", "input file does not exist")
        if os.path.getsize(args.input) > MAX_INPUT_BYTES:
            raise ExtractError("too_large", "input file is larger than 2 MB")
        if args.out is not None:
            check_output(args.input, args.out)
        deck = read_deck(args.input)
        text = render(deck, os.path.basename(args.input), args.format == "md")
        if args.out is not None:
            write_new(args.out, text)
    except ExtractError as exc:
        emit_error(exc.code, exc.message)
    empty = [n for n, s in enumerate(deck, 1) if not (s["title"] or s["body"] or s["tables"])]
    summary = {
        "slide_count": len(deck),
        "empty_slides": empty,
        "table_count": sum(len(s["tables"]) for s in deck),
        "slides_with_notes": sum(1 for s in deck if s["notes"]),
    }
    if args.out is None:
        sys.stdout.write(text)
    sys.stderr.write(json.dumps(summary) + "\n")
    return 1 if empty else 0


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass
    sys.exit(main())
