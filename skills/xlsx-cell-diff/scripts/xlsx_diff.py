"""Compare two .xlsx workbooks cell by cell and write a JSON report.

Standard library only (zipfile, xml.etree, decimal). The inputs are read in
place and never extracted or modified. Sheets are matched by name. Cell values
and formulas are compared; cell formatting is ignored. Shared formulas are
compared by their shared-formula index, not by expanded formula text.

Usage:
  python -I xlsx_diff.py <old.xlsx> <new.xlsx> <report.json>

Exit codes:
  0  no differences
  1  differences found (see the report file)
  2  usage or input error; a one-line JSON error is written to stderr
"""

import json
import os
import re
import sys
import xml.etree.ElementTree as ET
import zipfile
from decimal import Decimal, InvalidOperation

VERSION = "0.1.0"
MAX_INPUT_BYTES = 2 * 1024 * 1024           # brief: cap input at 2 MB
MAX_ZIP_ENTRIES = 2000                      # working value
MAX_UNCOMPRESSED_BYTES = 32 * 1024 * 1024   # working value, per workbook
MAX_PART_BYTES = 16 * 1024 * 1024           # working value, per XML part
MAX_CELLS = 200000                          # working value, per workbook
MAX_NUMBER_CHARS = 64                       # working value
CHANGE_KINDS = ["value", "formula", "value+formula", "added", "removed"]
REF_RE = re.compile(r"^([A-Z]{1,3})([0-9]{1,7})$")
# Raw-byte needles for DTD and entity declarations, in UTF-8, UTF-16 LE and
# UTF-16 BE, matched case-insensitively, so an encoded form cannot bypass the check.
DTD_NEEDLES = [
    re.compile(re.escape(("<!" + kw).encode(enc)), re.IGNORECASE)
    for enc in ("utf-8", "utf-16-le", "utf-16-be")
    for kw in ("DOCTYPE", "ENTITY")
]
WIDE_BOMS = (b"\xff\xfe", b"\xfe\xff", b"\x00\x00\xfe\xff")


class InputError(Exception):
    pass


def local_name(tag):
    return tag.rsplit("}", 1)[-1]


def col_number(letters):
    n = 0
    for ch in letters:
        n = n * 26 + (ord(ch) - 64)
    return n


def col_letters(n):
    out = ""
    while n > 0:
        n, rem = divmod(n - 1, 26)
        out = chr(65 + rem) + out
    return out


def parse_ref(ref):
    m = REF_RE.match(ref)
    if not m:
        raise InputError("invalid cell reference in worksheet")
    return int(m.group(2)), col_number(m.group(1))


def normalize_number(text):
    s = text.strip()
    if len(s) > MAX_NUMBER_CHARS:
        return s
    try:
        d = Decimal(s)
    except InvalidOperation:
        return s
    if not d.is_finite():
        return s
    if d == 0:
        return "0"
    return format(d.normalize(), "f")


def read_part(zf, names, part):
    if part not in names:
        raise InputError("workbook part missing: " + part)
    if zf.getinfo(part).file_size > MAX_PART_BYTES:
        raise InputError("workbook part too large: " + part)
    data = zf.read(part)
    for needle in DTD_NEEDLES:
        if needle.search(data):
            raise InputError("DTD or entity declarations are refused")
    if data.startswith(WIDE_BOMS) or b"\x00" in data:
        raise InputError("UTF-16 and UTF-32 workbook parts are refused")
    try:
        return ET.fromstring(data)
    except ET.ParseError:
        raise InputError("invalid XML in workbook part: " + part)


def cell_content(c, shared):
    ctype = c.get("t", "n")
    value = None
    formula = None
    for child in c:
        name = local_name(child.tag)
        if name == "f":
            if child.text:
                formula = child.text
            elif child.get("t") == "shared":
                formula = "shared:" + str(child.get("si"))
            else:
                formula = ""
        elif name == "v":
            value = child.text or ""
        elif name == "is":
            value = "".join(t.text or "" for t in child.iter() if local_name(t.tag) == "t")
    if ctype == "s" and value is not None:
        try:
            idx = int(value)
        except ValueError:
            raise InputError("shared string index is not a number")
        if idx < 0 or idx >= len(shared):
            raise InputError("shared string index out of range")
        value = shared[idx]
    elif ctype == "b" and value is not None:
        value = "TRUE" if value.strip() == "1" else "FALSE"
    elif ctype == "n" and value is not None:
        value = normalize_number(value)
    return value, formula


def parse_sheet(root, shared):
    cells = {}
    sheet_data = None
    for el in root.iter():
        if local_name(el.tag) == "sheetData":
            sheet_data = el
            break
    if sheet_data is None:
        return cells
    row_no = 0
    total = 0
    for row_el in sheet_data:
        if local_name(row_el.tag) != "row":
            continue
        row_no = int(row_el.get("r")) if (row_el.get("r") or "").isdigit() else row_no + 1
        col_no = 0
        for c in row_el:
            if local_name(c.tag) != "c":
                continue
            ref = c.get("r")
            if ref:
                r, col = parse_ref(ref)
            else:
                r, col = row_no, col_no + 1
            col_no = col
            value, formula = cell_content(c, shared)
            if value is None and formula is None:
                continue
            total += 1
            if total > MAX_CELLS:
                raise InputError("sheet exceeds the cell cap of 200000")
            cells[(r, col)] = (value, formula)
    return cells


def load_workbook(path):
    if not os.path.isfile(path):
        raise InputError("input file not found")
    if os.path.getsize(path) > MAX_INPUT_BYTES:
        raise InputError("input file exceeds 2 MB")
    try:
        zf = zipfile.ZipFile(path, "r")
    except (zipfile.BadZipFile, OSError):
        raise InputError("input is not a readable .xlsx zip container")
    with zf:
        infos = zf.infolist()
        if len(infos) > MAX_ZIP_ENTRIES:
            raise InputError("zip has too many entries")
        if sum(i.file_size for i in infos) > MAX_UNCOMPRESSED_BYTES:
            raise InputError("uncompressed size exceeds 32 MB")
        names = set(i.filename for i in infos)
        workbook = read_part(zf, names, "xl/workbook.xml")
        rels = read_part(zf, names, "xl/_rels/workbook.xml.rels")
        targets = {}
        for rel in rels:
            if local_name(rel.tag) == "Relationship":
                targets[rel.get("Id")] = rel.get("Target", "")
        shared = []
        if "xl/sharedStrings.xml" in names:
            sst = read_part(zf, names, "xl/sharedStrings.xml")
            for si in sst:
                if local_name(si.tag) == "si":
                    shared.append("".join(t.text or "" for t in si.iter() if local_name(t.tag) == "t"))
        sheets = []
        for sh in workbook.iter():
            if local_name(sh.tag) != "sheet":
                continue
            rid = None
            for key, val in sh.attrib.items():
                if local_name(key) == "id":
                    rid = val
            target = targets.get(rid)
            if not target:
                raise InputError("sheet has no relationship target")
            part = target[1:] if target.startswith("/") else "xl/" + target
            cells = parse_sheet(read_part(zf, names, part), shared)
            sheets.append((sh.get("name", ""), cells))
    return sheets


def ref_of(key):
    return col_letters(key[1]) + str(key[0])


def diff_cells(sheet, old_cells, new_cells):
    changes = []
    for key in sorted(set(old_cells) | set(new_cells)):
        ov = old_cells.get(key)
        nv = new_cells.get(key)
        if ov is None or nv is None:
            kind = "removed" if nv is None else "added"
        else:
            val_diff = ov[0] != nv[0]
            f_diff = ov[1] != nv[1]
            if val_diff and f_diff:
                kind = "value+formula"
            elif val_diff:
                kind = "value"
            elif f_diff:
                kind = "formula"
            else:
                continue
        changes.append({
            "sheet": sheet,
            "cell": ref_of(key),
            "change": kind,
            "old_value": ov[0] if ov is not None else None,
            "new_value": nv[0] if nv is not None else None,
            "old_formula": ov[1] if ov is not None else None,
            "new_formula": nv[1] if nv is not None else None,
        })
    return changes


def same_path(a, b):
    return os.path.normcase(os.path.abspath(a)) == os.path.normcase(os.path.abspath(b))


def main(argv):
    if len(argv) != 3:
        raise InputError("usage: xlsx_diff.py <old.xlsx> <new.xlsx> <report.json>")
    old_path, new_path, report_path = argv
    if os.path.lexists(report_path):
        raise InputError("report path already exists; choose a new file name")
    if not os.path.isdir(os.path.dirname(os.path.abspath(report_path))):
        raise InputError("report folder does not exist")
    if same_path(report_path, old_path) or same_path(report_path, new_path):
        raise InputError("report path must not be an input file")

    old_sheets = load_workbook(old_path)
    new_sheets = load_workbook(new_path)
    old_map = dict(old_sheets)
    new_map = dict(new_sheets)
    added = [n for n in new_map if n not in old_map]
    removed = [n for n in old_map if n not in new_map]
    compared = [n for n in old_map if n in new_map]
    changes = []
    for name in compared:
        changes.extend(diff_cells(name, old_map[name], new_map[name]))

    by_kind = {k: 0 for k in CHANGE_KINDS}
    for ch in changes:
        by_kind[ch["change"]] += 1
    report = {
        "tool": "xlsx_diff",
        "version": VERSION,
        "old_file": os.path.basename(old_path),
        "new_file": os.path.basename(new_path),
        "sheets_compared": compared,
        "sheets_added": added,
        "sheets_removed": removed,
        "summary": {
            "sheets_added": len(added),
            "sheets_removed": len(removed),
            "cells_changed": len(changes),
            "by_change": by_kind,
        },
        "changes": changes,
    }
    try:
        with open(report_path, "x", encoding="utf-8", newline="\n") as fh:
            json.dump(report, fh, ensure_ascii=False, indent=2)
            fh.write("\n")
    except FileExistsError:
        raise InputError("report path already exists; choose a new file name")
    except OSError:
        raise InputError("report could not be written")

    total = len(changes) + len(added) + len(removed)
    print(json.dumps({
        "status": "differences_found" if total else "no_differences",
        "cells_changed": len(changes),
        "sheets_added": len(added),
        "sheets_removed": len(removed),
        "report": report_path,
    }))
    return 1 if total else 0


if __name__ == "__main__":
    try:
        code = main(sys.argv[1:])
    except InputError as exc:
        sys.stderr.write(json.dumps({"status": "error", "message": str(exc)}) + "\n")
        code = 2
    except Exception:
        sys.stderr.write(json.dumps({"status": "error", "message": "workbook could not be read"}) + "\n")
        code = 2
    sys.exit(code)
