"""Build the smoke-test workbook pair for xlsx_diff.py at runtime.

Binary .xlsx files are never stored in the skill folder. This helper writes
old.xlsx and new.xlsx into an output folder that you name, which must exist.

Usage:
  python -I make_fixtures.py <output-folder>

The pair differs by three edited values, one changed formula (same cached
result), and one added sheet named Summary:
  Budget!A2  value    Rent -> Housing
  Budget!A3  value    Food -> Groceries
  Budget!B5  value    0.05 -> 0.06
  Budget!C4  formula  B4*0.5 -> B4/2 (cached value 750 in both files)
  Summary    added sheet in the new file
Total cells that differ: 4. Formula cells keep their cached totals, so no
dependent cell changes.

It also writes hostile.xlsx, a refusal fixture whose workbook part is UTF-16 LE
with a DOCTYPE. xlsx_diff.py must refuse it with exit 2; it is not part of the
smoke pair.

Exit codes: 0 written, 2 usage or write error (one-line JSON on stderr).
"""

import json
import os
import re
import sys
import zipfile
from xml.sax.saxutils import escape

MAIN_NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
REL_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
PKG_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
REF_RE = re.compile(r"^([A-Z]+)([0-9]+)$")

OLD_SHEETS = [
    ("Budget", {
        "A1": ("s", "Item"), "B1": ("s", "Amount"), "C1": ("s", "Half"),
        "A2": ("s", "Rent"), "B2": ("n", "1200"),
        "A3": ("s", "Food"), "B3": ("n", "300"),
        "A4": ("s", "Total"), "B4": ("f", "SUM(B2:B3)", "1500"),
        "C4": ("f", "B4*0.5", "750"),
        "A5": ("s", "Rate"), "B5": ("n", "0.05"),
    }),
    ("Notes", {
        "A1": ("i", "Memo"), "A2": ("i", "Paid on time"),
    }),
]

NEW_SHEETS = [
    ("Budget", {
        "A1": ("s", "Item"), "B1": ("s", "Amount"), "C1": ("s", "Half"),
        "A2": ("s", "Housing"), "B2": ("n", "1200"),
        "A3": ("s", "Groceries"), "B3": ("n", "300"),
        "A4": ("s", "Total"), "B4": ("f", "SUM(B2:B3)", "1500"),
        "C4": ("f", "B4/2", "750"),
        "A5": ("s", "Rate"), "B5": ("n", "0.06"),
    }),
    ("Notes", {
        "A1": ("i", "Memo"), "A2": ("i", "Paid on time"),
    }),
    ("Summary", {
        "A1": ("i", "Totals"), "B1": ("f", "Budget!B4", "1500"),
    }),
]


def split_ref(ref):
    m = REF_RE.match(ref)
    if not m:
        raise ValueError("bad ref " + ref)
    letters, row = m.group(1), int(m.group(2))
    col = 0
    for ch in letters:
        col = col * 26 + (ord(ch) - 64)
    return row, col


def build(path, sheets, hostile_workbook=False):
    shared = []
    for _, cells in sheets:
        for spec in cells.values():
            if spec[0] == "s" and spec[1] not in shared:
                shared.append(spec[1])

    sheet_parts = []
    for _, cells in sheets:
        rows = {}
        for ref in cells:
            row, col = split_ref(ref)
            rows.setdefault(row, []).append((col, ref))
        body = []
        for row in sorted(rows):
            cell_xml = []
            for _, ref in sorted(rows[row]):
                spec = cells[ref]
                kind = spec[0]
                if kind == "n":
                    cell_xml.append('<c r="%s"><v>%s</v></c>' % (ref, spec[1]))
                elif kind == "s":
                    cell_xml.append('<c r="%s" t="s"><v>%d</v></c>' % (ref, shared.index(spec[1])))
                elif kind == "i":
                    cell_xml.append('<c r="%s" t="inlineStr"><is><t>%s</t></is></c>' % (ref, escape(spec[1])))
                elif kind == "f":
                    cell_xml.append('<c r="%s"><f>%s</f><v>%s</v></c>' % (ref, escape(spec[1]), spec[2]))
            body.append('<row r="%d">%s</row>' % (row, "".join(cell_xml)))
        sheet_parts.append(
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<worksheet xmlns="%s"><sheetData>%s</sheetData></worksheet>' % (MAIN_NS, "".join(body))
        )

    sheets_xml = "".join(
        '<sheet name="%s" sheetId="%d" r:id="rId%d"/>' % (escape(name), i + 1, i + 1)
        for i, (name, _) in enumerate(sheets)
    )
    workbook_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<workbook xmlns="%s" xmlns:r="%s"><sheets>%s</sheets></workbook>' % (MAIN_NS, REL_NS, sheets_xml)
    )
    rel_items = "".join(
        '<Relationship Id="rId%d" Type="%s/worksheet" Target="worksheets/sheet%d.xml"/>'
        % (i + 1, REL_NS, i + 1) for i in range(len(sheets))
    )
    sst_rid = len(sheets) + 1
    rel_items += '<Relationship Id="rId%d" Type="%s/sharedStrings" Target="sharedStrings.xml"/>' % (sst_rid, REL_NS)
    rels_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="%s">%s</Relationships>' % (PKG_NS, rel_items)
    )
    sst_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<sst xmlns="%s" count="%d" uniqueCount="%d">%s</sst>'
        % (MAIN_NS, len(shared), len(shared),
           "".join("<si><t>%s</t></si>" % escape(s) for s in shared))
    )
    overrides = "".join(
        '<Override PartName="/xl/worksheets/sheet%d.xml" '
        'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
        % (i + 1) for i in range(len(sheets))
    )
    content_types = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        '<Override PartName="/xl/workbook.xml" '
        'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
        '<Override PartName="/xl/sharedStrings.xml" '
        'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sharedStrings+xml"/>'
        '%s</Types>' % overrides
    )
    root_rels = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="%s"><Relationship Id="rId1" '
        'Type="%s/officeDocument" Target="xl/workbook.xml"/></Relationships>' % (PKG_NS, REL_NS)
    )

    if hostile_workbook:
        # UTF-16 LE with BOM and a DOCTYPE with an entity: must be refused.
        workbook_part = b"\xff\xfe" + ('<!DOCTYPE workbook [<!ENTITY note "x">]>' + workbook_xml).encode("utf-16-le")
    else:
        workbook_part = workbook_xml

    with zipfile.ZipFile(path, "x", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", content_types)
        zf.writestr("_rels/.rels", root_rels)
        zf.writestr("xl/workbook.xml", workbook_part)
        zf.writestr("xl/_rels/workbook.xml.rels", rels_xml)
        zf.writestr("xl/sharedStrings.xml", sst_xml)
        for i, part in enumerate(sheet_parts):
            zf.writestr("xl/worksheets/sheet%d.xml" % (i + 1), part)


def main(argv):
    if len(argv) != 1 or not os.path.isdir(argv[0]):
        raise ValueError("usage: make_fixtures.py <existing-output-folder>")
    out = argv[0]
    build(os.path.join(out, "old.xlsx"), OLD_SHEETS)
    build(os.path.join(out, "new.xlsx"), NEW_SHEETS)
    build(os.path.join(out, "hostile.xlsx"), NEW_SHEETS, hostile_workbook=True)
    print(json.dumps({"written": ["old.xlsx", "new.xlsx", "hostile.xlsx"]}))
    return 0


if __name__ == "__main__":
    try:
        code = main(sys.argv[1:])
    except Exception as exc:
        sys.stderr.write(json.dumps({"status": "error", "message": str(exc)}) + "\n")
        code = 2
    sys.exit(code)
