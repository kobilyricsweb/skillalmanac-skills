"""Write a new .xlsx workbook from a CSV or JSON record file (Python stdlib only).

Usage:
    python -I scripts/to_xlsx.py <input-file> <output-file.xlsx> [--sheet NAME]

Input: a UTF-8 .csv (first row is the header) or a UTF-8 .json file holding a
non-empty array of flat objects. Output: one new worksheet with a bold header
row, plain decimal numbers as numeric cells, all other text as inline strings,
and column widths taken from content. No macros and no formulas are written.

The output path must not exist. After writing, the file is read back with
zipfile and every part is parsed with xml.etree to count the rows.

Exit codes: 0 ok, 1 findings (workbook written, review the listed codes),
2 usage or input error (one-line JSON on stderr).
"""
import csv
import io
import json
import math
import os
import re
import sys
import zipfile
import xml.etree.ElementTree as ET
from xml.sax.saxutils import escape

MAX_INPUT_BYTES = 2 * 1024 * 1024
MAX_DATA_ROWS = 1048575
MAX_COLUMNS = 16384
MAX_SIG_DIGITS = 15
MIN_WIDTH = 8
MAX_WIDTH = 60
NUMBER_RE = re.compile(r"^-?(0|[1-9][0-9]*)(\.[0-9]+)?$")
XML_BAD_RE = re.compile("[\x00-\x08\x0b\x0c\x0e-\x1f￾￿]")
SHEET_BAD_RE = re.compile(r"[\[\]:*?/\\]")
MAIN_URI = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
REL_URI = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
MAIN_NS = "{%s}" % MAIN_URI
BOM_PREFIXES = (b"\xff\xfe", b"\xfe\xff", b"\x00\x00\xfe\xff")
HOSTILE_PATTERNS = tuple(
    piece
    for token in ("<!doctype", "<!entity")
    for piece in (token.encode("ascii"), token.encode("utf-16-le"), token.encode("utf-16-be"))
)

CONTENT_TYPES = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
    '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
    '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
    '<Default Extension="xml" ContentType="application/xml"/>'
    '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
    '<Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
    '<Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>'
    '</Types>'
)
ROOT_RELS = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
    '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
    '<Relationship Id="rId1" Type="%s/officeDocument" Target="xl/workbook.xml"/>'
    '</Relationships>' % REL_URI
)
WORKBOOK_RELS = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
    '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
    '<Relationship Id="rId1" Type="%s/worksheet" Target="worksheets/sheet1.xml"/>'
    '<Relationship Id="rId2" Type="%s/styles" Target="styles.xml"/>'
    '</Relationships>' % (REL_URI, REL_URI)
)
STYLES = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
    '<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
    '<fonts count="2">'
    '<font><sz val="11"/><name val="Calibri"/></font>'
    '<font><b/><sz val="11"/><name val="Calibri"/></font>'
    '</fonts>'
    '<fills count="2"><fill><patternFill patternType="none"/></fill>'
    '<fill><patternFill patternType="gray125"/></fill></fills>'
    '<borders count="1"><border><left/><right/><top/><bottom/><diagonal/></border></borders>'
    '<cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>'
    '<cellXfs count="2">'
    '<xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/>'
    '<xf numFmtId="0" fontId="1" fillId="0" borderId="0" xfId="0" applyFont="1"/>'
    '</cellXfs>'
    '<cellStyles count="1"><cellStyle name="Normal" xfId="0" builtinId="0"/></cellStyles>'
    '</styleSheet>'
)


class ToolError(Exception):
    def __init__(self, code, message):
        Exception.__init__(self, message)
        self.code = code
        self.message = message


def fail(code, message):
    sys.stderr.write(json.dumps({"status": "error", "code": code, "message": message}) + "\n")
    return 2


def reject_constant(name):
    raise ValueError("non-finite number")


def parse_csv(text):
    try:
        rows = [row for row in csv.reader(io.StringIO(text, newline="")) if row]
    except csv.Error:
        raise ToolError("E_INPUT_FORMAT", "CSV could not be parsed")
    if not rows:
        raise ToolError("E_INPUT_FORMAT", "CSV has no header row")
    return rows[0], rows[1:]


def parse_json(text):
    try:
        data = json.loads(text, parse_constant=reject_constant)
    except (ValueError, RecursionError):
        raise ToolError("E_INPUT_FORMAT", "JSON could not be parsed")
    if not isinstance(data, list) or not data:
        raise ToolError("E_JSON_SHAPE", "JSON must be a non-empty array of objects")
    header = []
    seen = set()
    for number, item in enumerate(data, start=1):
        if not isinstance(item, dict):
            raise ToolError("E_JSON_SHAPE", "item %d is not an object" % number)
        for key, value in item.items():
            if isinstance(value, (dict, list)):
                raise ToolError("E_JSON_SHAPE", "item %d has a nested value" % number)
            if isinstance(value, float) and not math.isfinite(value):
                raise ToolError("E_JSON_SHAPE", "item %d has a non-finite number" % number)
            if key not in seen:
                seen.add(key)
                header.append(key)
    if not header:
        raise ToolError("E_JSON_SHAPE", "the objects have no fields")
    return header, [[item.get(key) for key in header] for item in data]


def refuse_wide_bom(raw):
    if raw.startswith(BOM_PREFIXES):
        raise ToolError("E_INPUT_FORMAT", "UTF-16 or UTF-32 input is refused; save the file as UTF-8")


def refuse_xml_dtd(raw):
    # Raw-byte scan before any XML parse: catches DOCTYPE/ENTITY in UTF-8,
    # UTF-16LE and UTF-16BE forms (ASCII letters compared case-insensitively),
    # and refuses UTF-16/UTF-32 byte order marks outright.
    lowered = raw.lower()
    if raw.startswith(BOM_PREFIXES) or any(p in lowered for p in HOSTILE_PATTERNS):
        raise ToolError("E_XML_DTD", "XML with a DOCTYPE or ENTITY declaration, or a UTF-16/UTF-32 byte order mark, is refused")


def read_input(path):
    ext = os.path.splitext(path)[1].lower()
    if ext not in (".csv", ".json"):
        raise ToolError("E_INPUT_FORMAT", "input must end in .csv or .json")
    if not os.path.isfile(path):
        raise ToolError("E_INPUT_MISSING", "input file not found")
    if os.path.getsize(path) > MAX_INPUT_BYTES:
        raise ToolError("E_INPUT_TOO_LARGE", "input is larger than 2 MB")
    with open(path, "rb") as handle:
        raw = handle.read(MAX_INPUT_BYTES + 1)
    if len(raw) > MAX_INPUT_BYTES:
        raise ToolError("E_INPUT_TOO_LARGE", "input is larger than 2 MB")
    refuse_wide_bom(raw)
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise ToolError("E_INPUT_FORMAT", "input is not valid UTF-8")
    if ext == ".csv":
        return parse_csv(text)
    return parse_json(text)


def sig_digits(text):
    return len(text.replace("-", "").replace(".", "").lstrip("0"))


def cell_text(value):
    if value is None:
        return ""
    if isinstance(value, bool):
        return "TRUE" if value else "FALSE"
    if isinstance(value, float):
        return repr(value)
    return str(value)


def is_numeric(value):
    if value is None or isinstance(value, bool):
        return False
    if isinstance(value, float):
        return True
    if isinstance(value, int):
        return sig_digits(str(value)) <= MAX_SIG_DIGITS
    return bool(NUMBER_RE.match(value)) and sig_digits(value) <= MAX_SIG_DIGITS


def col_letter(index):
    letters = ""
    n = index + 1
    while n:
        n, rem = divmod(n - 1, 26)
        letters = chr(65 + rem) + letters
    return letters


def cell_xml(ref, value, is_header):
    text = cell_text(value)
    if text == "":
        return ""
    if XML_BAD_RE.search(text):
        raise ToolError("E_XML_CHAR", "a value holds a character XML 1.0 cannot carry")
    if not is_header and is_numeric(value):
        return '<c r="%s"><v>%s</v></c>' % (ref, text)
    style = ' s="1"' if is_header else ""
    return ('<c r="%s"%s t="inlineStr"><is><t xml:space="preserve">%s</t></is></c>'
            % (ref, style, escape(text)))


def build_parts(sheet_name, header, rows):
    all_rows = [header] + rows
    ncols = max(len(r) for r in all_rows)
    widths = [0] * ncols
    row_xml = []
    for r_index, row in enumerate(all_rows, start=1):
        cells = []
        for c in range(ncols):
            value = row[c] if c < len(row) else None
            widths[c] = max(widths[c], len(cell_text(value)))
            cells.append(cell_xml("%s%d" % (col_letter(c), r_index), value, r_index == 1))
        row_xml.append('<row r="%d">%s</row>' % (r_index, "".join(cells)))
    cols = "".join(
        '<col min="%d" max="%d" width="%d" customWidth="1"/>'
        % (c + 1, c + 1, max(MIN_WIDTH, min(MAX_WIDTH, widths[c] + 2)))
        for c in range(ncols)
    )
    last_ref = "%s%d" % (col_letter(ncols - 1), len(all_rows))
    sheet_part = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
        '<worksheet xmlns="%s"><dimension ref="A1:%s"/><cols>%s</cols>'
        '<sheetData>%s</sheetData></worksheet>'
        % (MAIN_URI, last_ref, cols, "".join(row_xml))
    )
    workbook_part = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
        '<workbook xmlns="%s" xmlns:r="%s"><sheets>'
        '<sheet name="%s" sheetId="1" r:id="rId1"/></sheets></workbook>'
        % (MAIN_URI, REL_URI, escape(sheet_name, {'"': "&quot;"}))
    )
    parts = [
        ("[Content_Types].xml", CONTENT_TYPES),
        ("_rels/.rels", ROOT_RELS),
        ("xl/workbook.xml", workbook_part),
        ("xl/_rels/workbook.xml.rels", WORKBOOK_RELS),
        ("xl/styles.xml", STYLES),
        ("xl/worksheets/sheet1.xml", sheet_part),
    ]
    return parts, ncols


def write_new_file(path, parts):
    try:
        handle = open(path, "xb")
    except FileExistsError:
        raise ToolError("E_OUTPUT_EXISTS", "output path already exists; choose a new name")
    try:
        with zipfile.ZipFile(handle, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for name, content in parts:
                archive.writestr(name, content.encode("utf-8"))
    except BaseException:
        handle.close()
        os.remove(path)
        raise
    handle.close()


def read_back(path):
    findings = set()
    try:
        with zipfile.ZipFile(path) as archive:
            if archive.testzip() is not None:
                raise zipfile.BadZipFile("member failed CRC")
            for name in archive.namelist():
                raw = archive.read(name)
                refuse_xml_dtd(raw)
                ET.fromstring(raw)
            workbook = ET.fromstring(archive.read("xl/workbook.xml"))
            sheet = ET.fromstring(archive.read("xl/worksheets/sheet1.xml"))
    except (ET.ParseError, zipfile.BadZipFile):
        return 0, ["F_XML_NOT_WELL_FORMED"], []
    names = [el.get("name") for el in workbook.iter(MAIN_NS + "sheet")]
    count = len(sheet.findall(MAIN_NS + "sheetData/" + MAIN_NS + "row"))
    return count, sorted(findings), names


def run(argv):
    args = list(argv[1:])
    sheet = "Sheet1"
    if "--sheet" in args:
        at = args.index("--sheet")
        if at + 1 >= len(args):
            raise ToolError("E_USAGE", "--sheet needs a name")
        sheet = args[at + 1]
        del args[at:at + 2]
    if len(args) != 2 or any(a.startswith("-") for a in args):
        raise ToolError("E_USAGE", "usage: to_xlsx.py <input-file> <output-file.xlsx> [--sheet NAME]")
    src, dst = args
    if (not 1 <= len(sheet) <= 31 or SHEET_BAD_RE.search(sheet) or XML_BAD_RE.search(sheet)
            or sheet.startswith("'") or sheet.endswith("'")):
        raise ToolError("E_SHEET_NAME", "sheet name must be 1-31 characters, must not contain [ ] : * ? / or control characters, and must not start or end with an apostrophe")
    if not dst.lower().endswith(".xlsx") or not os.path.isdir(os.path.dirname(os.path.abspath(dst))):
        raise ToolError("E_OUTPUT_PATH", "output must end in .xlsx and its folder must exist")
    if os.path.exists(dst):
        raise ToolError("E_OUTPUT_EXISTS", "output path already exists; choose a new name")

    header, rows = read_input(src)
    if len(rows) > MAX_DATA_ROWS or max(len(r) for r in [header] + rows) > MAX_COLUMNS:
        raise ToolError("E_LIMIT", "more than 1,048,575 data rows or 16,384 columns")
    ragged = sum(1 for r in rows if len(r) != len(header))

    parts, ncols = build_parts(sheet, header, rows)
    write_new_file(dst, parts)

    try:
        read_count, findings, names = read_back(dst)
    except ToolError:
        os.remove(dst)
        raise
    if names != [sheet] or read_count != len(rows) + 1:
        findings.append("F_READBACK_MISMATCH")
    if ragged:
        findings.append("F_RAGGED_ROW")
    findings = sorted(set(findings))
    result = {
        "status": "findings" if findings else "ok",
        "output": dst,
        "sheet": sheet,
        "columns": ncols,
        "data_rows": len(rows),
        "read_back_rows": read_count,
        "ragged_rows": ragged,
        "findings": findings,
    }
    print(json.dumps(result))
    return 1 if findings else 0


def main(argv):
    try:
        return run(argv)
    except ToolError as err:
        return fail(err.code, err.message)
    except OSError:
        return fail("E_IO", "the input could not be read or the output could not be written")


if __name__ == "__main__":
    sys.exit(main(sys.argv))
