"""Export each worksheet of an .xlsx workbook to its own CSV file (Python standard library only).

Usage:
    python -I scripts/xlsx_to_csv.py <input-file> <output-dir> [--convert-dates]

The input is only read. One new CSV is written per worksheet into <output-dir>;
an existing file is never overwritten. Numbers are copied as stored text so no
digits are lost. Without --convert-dates, date-styled cells are exported as their
serial numbers.

Exit codes: 0 export ok, 1 export written with findings, 2 usage or input error
(one JSON error line is printed and nothing is written).
"""

import csv
import datetime
import decimal
import json
import os
import re
import sys
import xml.etree.ElementTree as ET
import zipfile
import zlib

MAX_INPUT_BYTES = 2 * 1024 * 1024
MAX_ZIP_ENTRIES = 500
MAX_ENTRY_BYTES = 10 * 1024 * 1024
MAX_TOTAL_UNCOMPRESSED = 20 * 1024 * 1024
MAX_SHEETS = 100
MAX_ROWS = 100000
MAX_COLS = 1000
MAX_GRID_CELLS = 5000000
MAX_FINDINGS_LISTED = 50
MAX_SERIAL = 2958465  # 9999-12-31 in the 1900 date system

MAIN_NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
REL_NS = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"
PKG_REL_NS = "{http://schemas.openxmlformats.org/package/2006/relationships}"
BUILTIN_DATE_FORMATS = {14, 15, 16, 17, 18, 19, 20, 21, 22, 45, 46, 47}
CELL_REF = re.compile(r"^([A-Z]{1,3})([1-9][0-9]*)$")
UNSAFE_NAME_CHARS = re.compile(r'[\\/:*?"<>|\x00-\x1f]')
DTD_MESSAGE = "XML DTD or entity declarations are refused"
# Raw-byte needles in every encoding that could carry a declaration, matched case-insensitively for ASCII.
DTD_RAW_PATTERNS = [
    re.compile(re.escape(needle.encode(codec)), re.IGNORECASE)
    for needle in ("<!DOCTYPE", "<!ENTITY")
    for codec in ("utf-8", "utf-16-le", "utf-16-be")
]
DTD_DECODED = re.compile(r"<!DOCTYPE|<!ENTITY", re.IGNORECASE)
BOM_CODECS = [
    (b"\xff\xfe\x00\x00", "utf-32"),
    (b"\x00\x00\xfe\xff", "utf-32"),
    (b"\xff\xfe", "utf-16"),
    (b"\xfe\xff", "utf-16"),
]
DATE_TOKENS = re.compile(r"[ymdhs]", re.IGNORECASE)
LITERAL_PARTS = re.compile(r'"[^"]*"|\[[^\]]*\]|\\.')


def fail(message):
    """Print a one-line JSON error and exit 2."""
    print(json.dumps({"status": "error", "message": message}))
    sys.exit(2)


def to_int(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        fail("non-numeric attribute in workbook part")


def open_package(path):
    if os.path.getsize(path) > MAX_INPUT_BYTES:
        fail("input is larger than 2 MB")
    try:
        zf = zipfile.ZipFile(path)
    except (zipfile.BadZipFile, OSError):
        fail("input is not a readable .xlsx zip package")
    infos = zf.infolist()
    if len(infos) > MAX_ZIP_ENTRIES:
        fail("zip package has more than 500 entries")
    total = 0
    for info in infos:
        name = info.filename
        if name.startswith("/") or "\\" in name or ".." in name.split("/"):
            fail("unsafe entry name in zip package")
        if info.file_size > MAX_ENTRY_BYTES:
            fail("a zip entry is larger than 10 MB uncompressed")
        total += info.file_size
        if total > MAX_TOTAL_UNCOMPRESSED:
            fail("uncompressed workbook is larger than 20 MB")
    return zf


def xml_source(data):
    """Refuse DTD or entity declarations before any parse, then return what to parse.

    The raw bytes are scanned in UTF-8, UTF-16 LE and UTF-16 BE forms, so an encoded
    declaration cannot slip past. A UTF-16 or UTF-32 byte order mark is decoded first
    and the same check runs on the decoded text, which is then parsed.
    """
    if any(pattern.search(data) for pattern in DTD_RAW_PATTERNS):
        fail(DTD_MESSAGE)
    for bom, codec in BOM_CODECS:
        if data.startswith(bom):
            try:
                text = data.decode(codec)
            except UnicodeDecodeError:
                fail("malformed XML in workbook part")
            if DTD_DECODED.search(text):
                fail(DTD_MESSAGE)
            return text
    return data


def read_part(zf, name):
    """Return the parsed XML root of a package part, or None if the part is absent."""
    try:
        data = zf.read(name)
    except KeyError:
        return None
    except (zipfile.BadZipFile, zlib.error, RuntimeError, EOFError, OSError):
        fail("corrupt zip entry in workbook")
    source = xml_source(data)
    try:
        return ET.fromstring(source)
    except ET.ParseError:
        fail("malformed XML in workbook part")


def plain_text(element):
    """Join the text runs of a string item, skipping phonetic (rPh) runs."""
    pieces = []
    for child in element:
        if child.tag == MAIN_NS + "t":
            pieces.append(child.text or "")
        elif child.tag == MAIN_NS + "r":
            for run_text in child.findall(MAIN_NS + "t"):
                pieces.append(run_text.text or "")
    return "".join(pieces)


def load_shared_strings(zf):
    root = read_part(zf, "xl/sharedStrings.xml")
    if root is None:
        return []
    return [plain_text(si) for si in root.findall(MAIN_NS + "si")]


def looks_like_date(code):
    return DATE_TOKENS.search(LITERAL_PARTS.sub("", code)) is not None


def load_date_styles(zf):
    """Return the set of cellXfs indexes whose number format is a date or time format."""
    date_styles = set()
    root = read_part(zf, "xl/styles.xml")
    if root is None:
        return date_styles
    custom = {}
    numfmts = root.find(MAIN_NS + "numFmts")
    if numfmts is not None:
        for fmt in numfmts.findall(MAIN_NS + "numFmt"):
            custom[to_int(fmt.get("numFmtId", ""))] = fmt.get("formatCode", "")
    xfs = root.find(MAIN_NS + "cellXfs")
    if xfs is None:
        return date_styles
    for index, xf in enumerate(xfs.findall(MAIN_NS + "xf")):
        fmt_id = to_int(xf.get("numFmtId", "0"))
        if fmt_id in BUILTIN_DATE_FORMATS or (fmt_id in custom and looks_like_date(custom[fmt_id])):
            date_styles.add(index)
    return date_styles


def load_sheet_list(zf):
    """Return (sheet name, package part name) pairs in workbook order."""
    workbook = read_part(zf, "xl/workbook.xml")
    if workbook is None:
        fail("not an xlsx workbook: xl/workbook.xml is missing")
    rels = read_part(zf, "xl/_rels/workbook.xml.rels")
    targets = {}
    if rels is not None:
        for rel in rels.findall(PKG_REL_NS + "Relationship"):
            targets[rel.get("Id")] = rel.get("Target", "")
    sheets_el = workbook.find(MAIN_NS + "sheets")
    if sheets_el is None:
        fail("workbook has no sheets element")
    found = sheets_el.findall(MAIN_NS + "sheet")
    if len(found) > MAX_SHEETS:
        fail("workbook has more than 100 sheets")
    pairs = []
    for sheet in found:
        name = sheet.get("name") or "sheet"
        target = targets.get(sheet.get(REL_NS + "id"), "")
        if target.startswith("/"):
            part = target[1:]
        else:
            part = "xl/" + target
        pairs.append((name, part))
    return pairs


def column_number(letters):
    number = 0
    for letter in letters:
        number = number * 26 + (ord(letter) - ord("A") + 1)
    return number


def serial_to_text(raw):
    """Convert a 1900-system serial number to an ISO date or date-time; keep raw text if impossible."""
    try:
        serial = decimal.Decimal(raw)
    except decimal.InvalidOperation:
        return raw
    if not serial.is_finite() or serial < 0 or serial > MAX_SERIAL:
        return raw
    total_seconds = int((serial * 86400).to_integral_value(rounding=decimal.ROUND_HALF_UP))
    days, seconds = divmod(total_seconds, 86400)
    # Excel treats 1900 as a leap year: serials below 61 use 1899-12-31 as day zero.
    base = datetime.date(1899, 12, 31) if days < 61 else datetime.date(1899, 12, 30)
    try:
        day = base + datetime.timedelta(days=days)
    except OverflowError:
        return raw
    if seconds == 0:
        return day.isoformat()
    hours, rest = divmod(seconds, 3600)
    minutes, secs = divmod(rest, 60)
    return "%s %02d:%02d:%02d" % (day.isoformat(), hours, minutes, secs)


def cell_text(cell, shared, date_styles, convert):
    """Return (text, is_formula, finding code or None) for one cell element."""
    kind = cell.get("t", "n")
    value_el = cell.find(MAIN_NS + "v")
    value = value_el.text if value_el is not None else None
    is_formula = cell.find(MAIN_NS + "f") is not None
    code = None
    if kind == "s":
        if value is None:
            text = ""
        else:
            index = to_int(value)
            if not 0 <= index < len(shared):
                fail("shared string index is out of range")
            text = shared[index]
    elif kind == "inlineStr":
        inline = cell.find(MAIN_NS + "is")
        text = plain_text(inline) if inline is not None else ""
    elif kind == "b":
        if value is None:
            text = ""
        else:
            text = "TRUE" if value.strip() == "1" else "FALSE"
    elif kind == "e":
        text = value or ""
        code = "F_ERROR_VALUE"
    elif kind == "str":
        text = value or ""
    else:
        style = to_int(cell.get("s", "0"))
        if value is None:
            text = ""
        elif convert and style in date_styles:
            text = serial_to_text(value)
        else:
            text = value
    if is_formula and value is None:
        code = "F_FORMULA_NO_CACHE"
    return text, is_formula, code


def read_sheet(root, sheet_name, shared, date_styles, convert, findings):
    """Return (table as a list of rows, formula cell count) for one worksheet."""
    grid = {}
    formulas = 0
    data = root.find(MAIN_NS + "sheetData")
    row_elements = data.findall(MAIN_NS + "row") if data is not None else []
    for row_el in row_elements:
        for cell in row_el.findall(MAIN_NS + "c"):
            ref = cell.get("r", "")
            match = CELL_REF.match(ref)
            if not match:
                fail("bad cell reference in sheet %s" % sheet_name)
            col = column_number(match.group(1))
            row = int(match.group(2))
            if row > MAX_ROWS or col > MAX_COLS:
                fail("sheet %s is larger than 100000 rows or 1000 columns" % sheet_name)
            text, is_formula, code = cell_text(cell, shared, date_styles, convert)
            if is_formula:
                formulas += 1
            if code:
                findings.append({"code": code, "sheet": sheet_name, "cell": ref})
            grid[(row, col)] = text
    if not grid:
        return [], formulas
    rows_n = max(r for r, _ in grid)
    cols_n = max(c for _, c in grid)
    if rows_n * cols_n > MAX_GRID_CELLS:
        fail("sheet %s is larger than 5000000 grid cells" % sheet_name)
    table = [[grid.get((r, c), "") for c in range(1, cols_n + 1)] for r in range(1, rows_n + 1)]
    return table, formulas


def file_stem(sheet_name, used):
    base = UNSAFE_NAME_CHARS.sub("_", sheet_name).strip(" .")[:100] or "sheet"
    candidate = base
    counter = 2
    while candidate.lower() in used:
        candidate = "%s_%d" % (base, counter)
        counter += 1
    used.add(candidate.lower())
    return candidate + ".csv"


def main(argv):
    args = argv[1:]
    convert = "--convert-dates" in args
    paths = [a for a in args if a != "--convert-dates"]
    if len(paths) != 2 or any(a.startswith("--") for a in paths):
        fail("usage: xlsx_to_csv.py <input-file> <output-dir> [--convert-dates]")
    in_path, out_dir = paths
    if not os.path.isfile(in_path):
        fail("input file not found")
    if not os.path.isdir(out_dir):
        fail("output directory not found")

    zf = open_package(in_path)
    shared = load_shared_strings(zf)
    date_styles = load_date_styles(zf)
    sheet_pairs = load_sheet_list(zf)

    exported = []
    skipped = []
    findings = []
    for sheet_name, part in sheet_pairs:
        root = read_part(zf, part)
        if root is None or root.tag != MAIN_NS + "worksheet":
            skipped.append(sheet_name)
            continue
        table, formulas = read_sheet(root, sheet_name, shared, date_styles, convert, findings)
        exported.append((sheet_name, table, formulas))
    zf.close()

    used = set()
    plan = []
    for sheet_name, table, formulas in exported:
        filename = file_stem(sheet_name, used)
        path = os.path.join(out_dir, filename)
        if os.path.abspath(path) == os.path.abspath(in_path) or os.path.exists(path):
            fail("output file already exists: %s" % filename)
        plan.append((sheet_name, filename, path, table, formulas))

    summary = []
    for sheet_name, filename, path, table, formulas in plan:
        try:
            with open(path, "x", newline="", encoding="utf-8") as handle:
                csv.writer(handle, lineterminator="\n").writerows(table)
        except FileExistsError:
            fail("output file appeared during export: %s" % filename)
        except OSError:
            fail("cannot create output file: %s" % filename)
        summary.append({
            "sheet": sheet_name,
            "file": filename,
            "rows": len(table),
            "columns": len(table[0]) if table else 0,
            "formula_cells": formulas,
        })

    result = {
        "status": "findings" if findings else "ok",
        "sheets": summary,
        "skipped_sheets": skipped,
        "findings_total": len(findings),
        "findings": findings[:MAX_FINDINGS_LISTED],
    }
    print(json.dumps(result))
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
