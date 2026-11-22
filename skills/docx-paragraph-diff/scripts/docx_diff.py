"""Compare two .docx files by body paragraph and by table cell, and list the differences.

Reads word/document.xml from each package with zipfile and xml.etree.ElementTree.
Only visible text is compared. Formatting (bold, styles, fonts, colors, highlights)
is ignored. Body paragraphs are aligned with difflib; table cells are matched by
(table number, row number, cell number). Nothing is written unless --out is given,
and --out must name a new file that is not one of the inputs.

Usage:
    python -I scripts/docx_diff.py <old-docx> <new-docx> [--out <report-json>]

Exit codes: 0 = no differences, 1 = differences found, 2 = usage or input error.
Output: one JSON object on stdout (the same object is written to --out if given).
Input errors print one JSON line with "result": "error" and exit 2.
"""

import argparse
import difflib
import json
import os
import sys
import xml.etree.ElementTree as ET
import zipfile
import zlib

MAX_FILE_BYTES = 2 * 1024 * 1024
MAX_ZIP_ENTRIES = 2000
MAX_UNCOMPRESSED_BYTES = 20 * 1024 * 1024
W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"

# DTD and entity markers, searched in the raw bytes in UTF-8, UTF-16 LE and UTF-16 BE forms.
DTD_MARKERS = ("<!doctype", "<!entity")
DTD_BYTE_FORMS = tuple(m.encode(enc) for m in DTD_MARKERS for enc in ("utf-8", "utf-16-le", "utf-16-be"))
DTD_REFUSED = "DTD or entity declarations are refused"
NOT_WELL_FORMED = "word/document.xml is not well-formed UTF-8 XML"


class InputError(Exception):
    """Raised for any input that cannot be compared. The message never contains file paths."""


def check_raw_bytes(data):
    """Refuse DTD/entity declarations in any encoding, and UTF-16/UTF-32 or NUL-byte input.

    Runs on the raw bytes before any XML parse, so an encoding trick cannot hide a DTD.
    ASCII letters are compared case-insensitively (both sides are lowered).
    """
    lowered = data.lower()
    for form in DTD_BYTE_FORMS:
        if form.lower() in lowered:
            raise InputError(DTD_REFUSED)
    if data[:2] in (b"\xff\xfe", b"\xfe\xff") or b"\x00" in data:
        raise InputError(NOT_WELL_FORMED)


def load_body(path):
    """Return the w:body element of a .docx file, or raise InputError."""
    if not os.path.isfile(path):
        raise InputError("input file not found")
    if os.path.getsize(path) > MAX_FILE_BYTES:
        raise InputError("input file is larger than 2 MB")
    try:
        zf = zipfile.ZipFile(path)
    except (zipfile.BadZipFile, OSError):
        raise InputError("input is not a readable .docx (zip) package")
    with zf:
        infos = zf.infolist()
        if len(infos) > MAX_ZIP_ENTRIES:
            raise InputError("package has more than 2000 entries")
        if sum(i.file_size for i in infos) > MAX_UNCOMPRESSED_BYTES:
            raise InputError("uncompressed package size is over 20 MB")
        try:
            data = zf.read("word/document.xml")
        except KeyError:
            raise InputError("word/document.xml is missing")
        except (zipfile.BadZipFile, RuntimeError, OSError, zlib.error):
            raise InputError("word/document.xml cannot be read (corrupt or encrypted)")
    check_raw_bytes(data)
    try:
        root = ET.fromstring(data)
    except ET.ParseError:
        raise InputError(NOT_WELL_FORMED)
    body = root.find(W + "body")
    if body is None:
        raise InputError("word/document.xml has no w:body element")
    return body


def para_text(p):
    """Visible text of one w:p: w:t text, w:tab as tab, w:br and w:cr as newline."""
    parts = []
    for node in p.iter():
        if node.tag == W + "t":
            parts.append(node.text or "")
        elif node.tag == W + "tab":
            parts.append("\t")
        elif node.tag in (W + "br", W + "cr"):
            parts.append("\n")
    return "".join(parts)


def split_body(body):
    """Return (body paragraph texts in order, body-level tbl elements in order)."""
    paragraphs = []
    tables = []

    def visit(container):
        for child in container:
            if child.tag == W + "p":
                paragraphs.append(para_text(child))
            elif child.tag == W + "tbl":
                tables.append(child)
            elif child.tag == W + "sdt":
                content = child.find(W + "sdtContent")
                if content is not None:
                    visit(content)

    visit(body)
    return paragraphs, tables


def cell_texts(tables):
    """Map (table, row, cell) numbers, all 1-based, to the cell text. Nested paragraphs are joined by newline."""
    cells = {}
    for t_no, tbl in enumerate(tables, start=1):
        for r_no, tr in enumerate(tbl.findall(W + "tr"), start=1):
            for c_no, tc in enumerate(tr.findall(W + "tc"), start=1):
                cells[(t_no, r_no, c_no)] = "\n".join(para_text(p) for p in tc.iter(W + "p"))
    return cells


def diff_paragraphs(old, new):
    out = []

    def removed(i):
        out.append({"kind": "paragraph_removed", "old_index": i + 1, "new_index": None,
                    "table": None, "row": None, "col": None, "old_text": old[i], "new_text": None})

    def added(j):
        out.append({"kind": "paragraph_added", "old_index": None, "new_index": j + 1,
                    "table": None, "row": None, "col": None, "old_text": None, "new_text": new[j]})

    def changed(i, j):
        out.append({"kind": "paragraph_changed", "old_index": i + 1, "new_index": j + 1,
                    "table": None, "row": None, "col": None, "old_text": old[i], "new_text": new[j]})

    matcher = difflib.SequenceMatcher(None, old, new, autojunk=False)
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            continue
        if tag == "delete":
            for i in range(i1, i2):
                removed(i)
        elif tag == "insert":
            for j in range(j1, j2):
                added(j)
        else:
            paired = min(i2 - i1, j2 - j1)
            for k in range(paired):
                changed(i1 + k, j1 + k)
            for i in range(i1 + paired, i2):
                removed(i)
            for j in range(j1 + paired, j2):
                added(j)
    return out


def diff_cells(old, new):
    out = []
    for key in sorted(set(old) | set(new)):
        t_no, r_no, c_no = key
        if key in old and key in new:
            if old[key] == new[key]:
                continue
            kind, old_text, new_text = "cell_changed", old[key], new[key]
        elif key in old:
            kind, old_text, new_text = "cell_removed", old[key], None
        else:
            kind, old_text, new_text = "cell_added", None, new[key]
        out.append({"kind": kind, "old_index": None, "new_index": None,
                    "table": t_no, "row": r_no, "col": c_no,
                    "old_text": old_text, "new_text": new_text})
    return out


def same_file(a, b):
    return os.path.normcase(os.path.abspath(a)) == os.path.normcase(os.path.abspath(b))


def build_report(old_path, new_path):
    old_body = load_body(old_path)
    new_body = load_body(new_path)
    old_paras, old_tables = split_body(old_body)
    new_paras, new_tables = split_body(new_body)
    old_cells = cell_texts(old_tables)
    new_cells = cell_texts(new_tables)
    diffs = diff_paragraphs(old_paras, new_paras) + diff_cells(old_cells, new_cells)
    kinds = ["paragraph_changed", "paragraph_added", "paragraph_removed",
             "cell_changed", "cell_added", "cell_removed"]
    counts = {k: 0 for k in kinds}
    for d in diffs:
        counts[d["kind"]] += 1
    return {
        "result": "differences" if diffs else "identical",
        "old_file": os.path.basename(old_path),
        "new_file": os.path.basename(new_path),
        "paragraphs": {"old": len(old_paras), "new": len(new_paras)},
        "tables": {"old": len(old_tables), "new": len(new_tables)},
        "counts": counts,
        "differences": diffs,
    }


def main(argv=None):
    ap = argparse.ArgumentParser(description="Compare two .docx files by paragraph and table cell.")
    ap.add_argument("old", help="the earlier .docx file")
    ap.add_argument("new", help="the later .docx file")
    ap.add_argument("--out", help="write the JSON report to this NEW file (refused if it exists)")
    args = ap.parse_args(argv)

    try:
        if args.out:
            if same_file(args.out, args.old) or same_file(args.out, args.new):
                raise InputError("--out must not be one of the input files")
            if os.path.exists(args.out):
                raise InputError("--out file already exists; choose a new name")
        report = build_report(args.old, args.new)
    except InputError as exc:
        print(json.dumps({"result": "error", "message": str(exc)}, ensure_ascii=True))
        return 2

    text = json.dumps(report, ensure_ascii=True, indent=2)
    if args.out:
        try:
            with open(args.out, "x", encoding="utf-8") as fh:
                fh.write(text + "\n")
        except FileExistsError:
            print(json.dumps({"result": "error", "message": "--out file already exists; choose a new name"}))
            return 2
        except OSError:
            print(json.dumps({"result": "error", "message": "cannot write --out file"}))
            return 2
    print(text)
    return 1 if report["differences"] else 0


if __name__ == "__main__":
    sys.exit(main())
