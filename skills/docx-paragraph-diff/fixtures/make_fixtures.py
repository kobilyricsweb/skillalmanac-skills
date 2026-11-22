"""Build the smoke-test pair of .docx files at runtime. No binary .docx is shipped.

Usage:
    python -I fixtures/make_fixtures.py <new-empty-folder>

Writes old.docx and new.docx into the folder. The folder is created if missing and
must be empty; the helper exits 2 otherwise. The pair differs in exactly two body
paragraphs (2 and 4) and one table cell (table 1, row 2, column 2). Paragraph 3 only
gains bold formatting, so it must NOT appear in the report.

It also writes hostile.docx: a UTF-16 (BOM) word/document.xml with a DOCTYPE and an
ENTITY declaration. docx_diff.py must refuse it with exit 2.
"""

import os
import sys
import zipfile
from xml.sax.saxutils import escape

W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"

CONTENT_TYPES = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
    '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
    '<Default Extension="xml" ContentType="application/xml"/>'
    '<Override PartName="/word/document.xml" '
    'ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
    "</Types>"
)

ROOT_RELS = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
    '<Relationship Id="rId1" '
    'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" '
    'Target="word/document.xml"/>'
    "</Relationships>"
)


def para(text, bold=False):
    run_props = "<w:rPr><w:b/></w:rPr>" if bold else ""
    return ('<w:p><w:r>' + run_props + '<w:t xml:space="preserve">' + escape(text)
            + "</w:t></w:r></w:p>")


def table(rows):
    out = ["<w:tbl>"]
    for row in rows:
        out.append("<w:tr>")
        for cell in row:
            out.append("<w:tc>" + para(cell) + "</w:tc>")
        out.append("</w:tr>")
    out.append("</w:tbl>")
    return "".join(out)


def document_xml(body_parts):
    return ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<w:document xmlns:w="' + W_NS + '"><w:body>' + "".join(body_parts)
            + "</w:body></w:document>")


def old_body():
    return [
        para("Quarterly summary for the review board."),
        para("Revenue grew in the second quarter."),
        para("The team hired four engineers."),
        para("Next steps are listed below."),
        table([["Item", "Owner"], ["Budget", "Ana"], ["Timeline", "Ben"]]),
        para("Contact the office with questions."),
    ]


def new_body():
    return [
        para("Quarterly summary for the review board."),
        para("Revenue grew in the third quarter."),
        para("The team hired four engineers.", bold=True),
        para("Next steps are listed in the appendix."),
        table([["Item", "Owner"], ["Budget", "Anya"], ["Timeline", "Ben"]]),
        para("Contact the office with questions."),
    ]


HOSTILE_XML = (
    '<?xml version="1.0" encoding="UTF-16"?>'
    '<!DOCTYPE w:document [<!ENTITY x "expanded">]>'
    '<w:document xmlns:w="' + W_NS + '"><w:body>'
    '<w:p><w:r><w:t>&x;</w:t></w:r></w:p>'
    "</w:body></w:document>"
)


def write_package(path, document_bytes):
    with zipfile.ZipFile(path, "x", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", CONTENT_TYPES)
        zf.writestr("_rels/.rels", ROOT_RELS)
        zf.writestr("word/document.xml", document_bytes)


def write_docx(path, body_parts):
    write_package(path, document_xml(body_parts).encode("utf-8"))


def write_hostile(path):
    # UTF-16 LE with a byte-order mark, built here at runtime; nothing is shipped.
    write_package(path, b"\xff\xfe" + HOSTILE_XML.encode("utf-16-le"))


def main(argv):
    if len(argv) != 2:
        print("usage: make_fixtures.py <new-empty-folder>")
        return 2
    folder = argv[1]
    if os.path.exists(folder) and os.listdir(folder):
        print("folder exists and is not empty")
        return 2
    os.makedirs(folder, exist_ok=True)
    try:
        write_docx(os.path.join(folder, "old.docx"), old_body())
        write_docx(os.path.join(folder, "new.docx"), new_body())
        write_hostile(os.path.join(folder, "hostile.docx"))
    except (FileExistsError, OSError):
        print("could not write fixtures")
        return 2
    print("wrote old.docx, new.docx and hostile.docx")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
