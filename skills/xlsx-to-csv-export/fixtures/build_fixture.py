"""Build the offline smoke workbook for scripts/xlsx_to_csv.py at a path you choose.

Usage:
    python -I fixtures/build_fixture.py <output-xlsx-path> [--hostile]

Writes a two-sheet .xlsx built from the text parts in this file: 15-digit decimals,
a formula with a cached value, a date-styled cell and one #DIV/0! error cell.
With --hostile, the first sheet is replaced by a UTF-16 document with a DOCTYPE,
built at run time, to show that the export script refuses it (exit 2).
The output path must not exist (the file is created with mode "x"). Keep the
generated workbook outside the skill folder; binary workbooks are never stored here.
"""

import json
import sys
import zipfile

CONTENT_TYPES = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
    '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
    '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
    '<Default Extension="xml" ContentType="application/xml"/>'
    '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
    '<Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
    '<Override PartName="/xl/worksheets/sheet2.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
    '<Override PartName="/xl/sharedStrings.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sharedStrings+xml"/>'
    '<Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>'
    '</Types>'
)

ROOT_RELS = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
    '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
    '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>'
    '</Relationships>'
)

WORKBOOK = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
    '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
    'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
    '<sheets>'
    '<sheet name="Prices" sheetId="1" r:id="rId1"/>'
    '<sheet name="Q1 Rates" sheetId="2" r:id="rId2"/>'
    '</sheets>'
    '</workbook>'
)

WORKBOOK_RELS = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
    '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
    '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>'
    '<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet2.xml"/>'
    '<Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/sharedStrings" Target="sharedStrings.xml"/>'
    '<Relationship Id="rId4" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>'
    '</Relationships>'
)

SHARED_STRINGS = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
    '<sst xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" count="10" uniqueCount="10">'
    '<si><t>Item</t></si><si><t>Rate</t></si><si><t>Alpha</t></si><si><t>Beta</t></si>'
    '<si><t>Doubled</t></si><si><t>Code</t></si><si><t>Value</t></si><si><t>x</t></si>'
    '<si><t>y</t></si><si><t>z</t></si>'
    '</sst>'
)

STYLES = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
    '<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
    '<cellXfs count="2">'
    '<xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/>'
    '<xf numFmtId="14" fontId="0" fillId="0" borderId="0" xfId="0" applyNumberFormat="1"/>'
    '</cellXfs>'
    '</styleSheet>'
)

SHEET1 = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
    '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData>'
    '<row r="1"><c r="A1" t="s"><v>0</v></c><c r="B1" t="s"><v>1</v></c></row>'
    '<row r="2"><c r="A2" t="s"><v>2</v></c><c r="B2"><v>0.123456789012345</v></c></row>'
    '<row r="3"><c r="A3" t="s"><v>3</v></c><c r="B3"><v>1234567890.12345</v></c></row>'
    '<row r="4"><c r="A4" t="s"><v>4</v></c><c r="B4"><f>B2*2</f><v>0.24691357802469</v></c></row>'
    '</sheetData></worksheet>'
)

SHEET2 = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
    '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData>'
    '<row r="1"><c r="A1" t="s"><v>5</v></c><c r="B1" t="s"><v>6</v></c></row>'
    '<row r="2"><c r="A2" t="s"><v>7</v></c><c r="B2"><v>2.71828182845905</v></c></row>'
    '<row r="3"><c r="A3" t="s"><v>8</v></c><c r="B3" s="1"><v>45658</v></c></row>'
    '<row r="4"><c r="A4" t="s"><v>9</v></c><c r="B4" t="e"><f>1/0</f><v>#DIV/0!</v></c></row>'
    '</sheetData></worksheet>'
)

PARTS = [
    ("[Content_Types].xml", CONTENT_TYPES),
    ("_rels/.rels", ROOT_RELS),
    ("xl/workbook.xml", WORKBOOK),
    ("xl/_rels/workbook.xml.rels", WORKBOOK_RELS),
    ("xl/sharedStrings.xml", SHARED_STRINGS),
    ("xl/styles.xml", STYLES),
    ("xl/worksheets/sheet1.xml", SHEET1),
    ("xl/worksheets/sheet2.xml", SHEET2),
]


HOSTILE_SHEET = (
    '<?xml version="1.0" encoding="UTF-16"?>\n'
    '<!DOCTYPE worksheet [<!ENTITY boom "x">]>\n'
    '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData/></worksheet>'
)


def main(argv):
    args = argv[1:]
    hostile = "--hostile" in args
    paths = [a for a in args if a != "--hostile"]
    if len(paths) != 1:
        print(json.dumps({"status": "error", "message": "usage: build_fixture.py <output-xlsx-path> [--hostile]"}))
        return 2
    parts = list(PARTS)
    if hostile:
        parts[6] = ("xl/worksheets/sheet1.xml", HOSTILE_SHEET.encode("utf-16"))
    try:
        with zipfile.ZipFile(paths[0], "x", zipfile.ZIP_DEFLATED) as zf:
            for name, text in parts:
                zf.writestr(name, text)
    except FileExistsError:
        print(json.dumps({"status": "error", "message": "output path already exists"}))
        return 2
    except OSError:
        print(json.dumps({"status": "error", "message": "cannot create output path"}))
        return 2
    print(json.dumps({"status": "ok", "parts": len(PARTS)}))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
