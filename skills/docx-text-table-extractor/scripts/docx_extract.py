"""Extract paragraphs and top-level tables from a .docx file into text and CSV files.

Usage:
    python -I docx_extract.py <input-file> <output-dir>

Reads word/document.xml and word/styles.xml from the .docx package with
zipfile and xml.etree. Writes paragraphs.txt (one line per non-empty paragraph,
"style<TAB>text") and one table-NNN.csv per top-level table into <output-dir>.
Every output file is created with mode "x", so an existing file is never
overwritten, and the input file is never written to.

Prints a JSON summary to stdout on success. Prints a one-line JSON error to
stderr on failure.
Exit codes: 0 ok, 1 findings (outputs are still written), 2 usage or input error.
Standard library only. No network, no subprocess, no eval or exec.
"""

import csv
import json
import os
import re
import sys
import xml.etree.ElementTree as ET
import zipfile
import zlib

MAX_INPUT_BYTES = 2 * 1024 * 1024
MAX_ZIP_ENTRIES = 2000
MAX_TOTAL_UNCOMPRESSED = 20 * 1024 * 1024
MAX_PART_UNCOMPRESSED = 10 * 1024 * 1024
MAX_GRID_SPAN = 64

WML = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
DOC_PART = "word/document.xml"
STYLES_PART = "word/styles.xml"
HEADING_RE = re.compile(r"^heading\s+\d+$", re.IGNORECASE)
WS_RE = re.compile(r"\s+")


class ExtractError(Exception):
    def __init__(self, code, message):
        Exception.__init__(self, message)
        self.code = code
        self.message = message


def clean(text):
    return WS_RE.sub(" ", text).strip()


DTD_NEEDLES = (b"<!DOCTYPE", b"<!ENTITY")


def check_no_dtd(data, part):
    # Raw-bytes scan before any parse: the same markup is checked in UTF-8,
    # UTF-16 LE and UTF-16 BE, case-insensitively, so no encoding hides it.
    haystack = data.lower()
    for needle in DTD_NEEDLES:
        text = needle.decode("ascii")
        for form in (needle, text.encode("utf-16-le"), text.encode("utf-16-be")):
            if form.lower() in haystack:
                raise ExtractError("DTD_FOUND", part + " declares a DTD or an entity")
    # UTF-16 and UTF-32 input (byte order marks, or NUL bytes, which XML 1.0
    # forbids) is refused rather than decoded, so the scan above cannot be bypassed.
    if data[:2] in (b"\xff\xfe", b"\xfe\xff") or b"\x00" in data:
        raise ExtractError("XML_INVALID", part + " is UTF-16 or UTF-32 encoded or contains NUL bytes")


def read_part(zf, infos, name, required):
    info = infos.get(name)
    if info is None:
        if required:
            raise ExtractError("NOT_DOCX", "the package has no " + name)
        return None
    if info.file_size > MAX_PART_UNCOMPRESSED:
        raise ExtractError("ZIP_LIMIT", name + " is larger than 10 MB uncompressed")
    try:
        with zf.open(info) as fh:
            data = fh.read(MAX_PART_UNCOMPRESSED + 1)
    except (zipfile.BadZipFile, RuntimeError, NotImplementedError, OSError, zlib.error):
        raise ExtractError("NOT_DOCX", "cannot read " + name)
    if len(data) > MAX_PART_UNCOMPRESSED:
        raise ExtractError("ZIP_LIMIT", name + " is larger than 10 MB uncompressed")
    check_no_dtd(data, name)
    try:
        return ET.fromstring(data)
    except (ET.ParseError, RecursionError):
        raise ExtractError("XML_INVALID", name + " is not well-formed UTF-8 XML")


def load_document(path):
    if not os.path.isfile(path):
        raise ExtractError("FILE_MISSING", "the input file does not exist")
    if os.path.splitext(path)[1].lower() != ".docx":
        raise ExtractError("NOT_DOCX", "the input must have a .docx extension")
    if os.path.getsize(path) > MAX_INPUT_BYTES:
        raise ExtractError("FILE_TOO_LARGE", "the input is larger than 2 MB")
    try:
        zf = zipfile.ZipFile(path, "r")
    except (zipfile.BadZipFile, OSError):
        raise ExtractError("NOT_DOCX", "the input is not a readable zip package")
    with zf:
        entries = zf.infolist()
        if len(entries) > MAX_ZIP_ENTRIES:
            raise ExtractError("ZIP_LIMIT", "the package has more than 2000 entries")
        if sum(e.file_size for e in entries) > MAX_TOTAL_UNCOMPRESSED:
            raise ExtractError("ZIP_LIMIT", "the package is larger than 20 MB uncompressed")
        infos = dict((e.filename, e) for e in entries)
        doc_root = read_part(zf, infos, DOC_PART, True)
        styles_root = read_part(zf, infos, STYLES_PART, False)
    return doc_root, styles_root


def style_map(root):
    names = {}
    if root is None:
        return names
    for style in root.iter(WML + "style"):
        sid = style.get(WML + "styleId")
        name_el = style.find(WML + "name")
        if sid and name_el is not None and name_el.get(WML + "val"):
            names[sid] = clean(name_el.get(WML + "val"))
    return names


def para_text(p):
    parts = []
    for node in p.iter():
        if node.tag == WML + "t" and node.text:
            parts.append(node.text)
        elif node.tag in (WML + "tab", WML + "br", WML + "cr"):
            parts.append(" ")
    return clean("".join(parts))


def para_style(p, styles):
    ppr = p.find(WML + "pPr")
    sid = None
    if ppr is not None:
        pstyle = ppr.find(WML + "pStyle")
        if pstyle is not None:
            sid = pstyle.get(WML + "val")
    if not sid:
        return "Normal"
    return styles.get(sid, clean(sid))


def read_table(tbl, number):
    rows = []
    counts = {"MERGED_HORIZONTAL": 0, "MERGED_VERTICAL": 0, "NESTED_TABLE": 0}
    for tr in tbl.findall(WML + "tr"):
        row = []
        for tc in tr.findall(WML + "tc"):
            span = 1
            tcpr = tc.find(WML + "tcPr")
            if tcpr is not None:
                gspan = tcpr.find(WML + "gridSpan")
                if gspan is not None:
                    try:
                        span = int(gspan.get(WML + "val", "1"))
                    except ValueError:
                        raise ExtractError("XML_INVALID", "a gridSpan value is not a number")
                    if span < 1 or span > MAX_GRID_SPAN:
                        raise ExtractError("XML_INVALID", "a gridSpan value is outside 1 to 64")
                    if span > 1:
                        counts["MERGED_HORIZONTAL"] += 1
                if tcpr.find(WML + "vMerge") is not None:
                    counts["MERGED_VERTICAL"] += 1
            if tc.find(WML + "tbl") is not None:
                counts["NESTED_TABLE"] += 1
            texts = [para_text(p) for p in tc.findall(WML + "p")]
            row.append(clean(" ".join(t for t in texts if t)))
            row.extend([""] * (span - 1))
        rows.append(row)
    width = max([len(r) for r in rows] or [0])
    for r in rows:
        r.extend([""] * (width - len(r)))
    findings = [{"code": k, "table": number, "count": v} for k, v in counts.items() if v]
    return rows, width, findings


def walk_body(doc_root, styles):
    body = doc_root.find(WML + "body")
    if body is None:
        raise ExtractError("XML_INVALID", "the document part has no body element")
    lines = []
    tables = []
    findings = []
    para_count = 0
    heading_count = 0
    for child in body:
        if child.tag == WML + "p":
            text = para_text(child)
            if text:
                style = para_style(child, styles)
                lines.append(style + "\t" + text)
                para_count += 1
                if HEADING_RE.match(style):
                    heading_count += 1
        elif child.tag == WML + "tbl":
            number = len(tables) + 1
            rows, width, found = read_table(child, number)
            tables.append({"number": number, "rows": rows, "width": width})
            findings.extend(found)
            lines.append("(table)\tsee " + table_name(number))
    return lines, tables, findings, para_count, heading_count


def table_name(number):
    return "table-%03d.csv" % number


def check_output_dir(in_path, out_dir):
    if not os.path.isdir(out_dir):
        raise ExtractError("OUTPUT_PATH_INVALID", "the output directory does not exist")
    in_folder = os.path.normcase(os.path.dirname(os.path.abspath(in_path)))
    if in_folder == os.path.normcase(os.path.abspath(out_dir)):
        raise ExtractError("OUTPUT_PATH_INVALID", "the output directory is the input file's folder")


def write_outputs(out_dir, lines, tables):
    names = ["paragraphs.txt"] + [table_name(t["number"]) for t in tables]
    for name in names:
        if os.path.exists(os.path.join(out_dir, name)):
            raise ExtractError("OUTPUT_EXISTS", name + " already exists in the output directory")
    try:
        with open(os.path.join(out_dir, "paragraphs.txt"), "x", encoding="utf-8", newline="") as fh:
            for line in lines:
                fh.write(line + "\n")
        for t in tables:
            path = os.path.join(out_dir, table_name(t["number"]))
            with open(path, "x", encoding="utf-8", newline="") as fh:
                csv.writer(fh, lineterminator="\n").writerows(t["rows"])
    except FileExistsError:
        raise ExtractError("OUTPUT_EXISTS", "an output file was created by another process during the run")
    except OSError:
        raise ExtractError("OUTPUT_PATH_INVALID", "an output file could not be written")
    return names


def main(argv):
    if len(argv) != 3:
        sys.stderr.write(json.dumps({"error": "USAGE", "message": "usage: docx_extract.py <input-file> <output-dir>"}) + "\n")
        return 2
    in_path, out_dir = argv[1], argv[2]
    try:
        check_output_dir(in_path, out_dir)
        doc_root, styles_root = load_document(in_path)
        lines, tables, findings, para_count, heading_count = walk_body(doc_root, style_map(styles_root))
        names = write_outputs(out_dir, lines, tables)
    except ExtractError as exc:
        sys.stderr.write(json.dumps({"error": exc.code, "message": exc.message}) + "\n")
        return 2
    summary = {
        "status": "findings" if findings else "ok",
        "input": os.path.basename(in_path),
        "headings": heading_count,
        "paragraphs": para_count,
        "tables": len(tables),
        "rows": sum(len(t["rows"]) for t in tables),
        "table_list": [
            {"table": t["number"], "rows": len(t["rows"]), "columns": t["width"], "file": table_name(t["number"])}
            for t in tables
        ],
        "files_written": names,
        "findings": findings,
    }
    sys.stdout.write(json.dumps(summary, indent=2) + "\n")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
