"""Build a small .docx test package at runtime. Only this text helper is stored on disk.

Usage:
    python -I build_fixture.py <output.docx> [--merged | --hostile]

Writes one new .docx file. Refuses (exit 2) if the output path already exists,
because the zip is opened with mode "x".
Default content: two headings, two body paragraphs and one 3-row by 2-column
table with no merged cells. --merged adds one horizontal merge (gridSpan = 2)
and two vertical merge cells (one restart, one continuation) so the extractor
reports findings. --hostile writes word/document.xml as UTF-16 with a DOCTYPE
and an entity declaration, which the extractor must refuse.
Standard library only.
"""

import sys
import zipfile
from xml.sax.saxutils import escape

WNS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
XML_HEAD = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'

CONTENT_TYPES = (
    XML_HEAD
    + '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
    + '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
    + '<Default Extension="xml" ContentType="application/xml"/>'
    + '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
    + '<Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>'
    + "</Types>"
)

RELS = (
    XML_HEAD
    + '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
    + '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>'
    + "</Relationships>"
)

STYLES = (
    XML_HEAD
    + '<w:styles xmlns:w="%s">' % WNS
    + '<w:style w:type="paragraph" w:default="1" w:styleId="Normal"><w:name w:val="Normal"/></w:style>'
    + '<w:style w:type="paragraph" w:styleId="Heading1"><w:name w:val="heading 1"/></w:style>'
    + '<w:style w:type="paragraph" w:styleId="Heading2"><w:name w:val="heading 2"/></w:style>'
    + "</w:styles>"
)


def run(text):
    return '<w:r><w:t xml:space="preserve">%s</w:t></w:r>' % escape(text)


def para(text, style=None):
    ppr = '<w:pPr><w:pStyle w:val="%s"/></w:pPr>' % style if style else ""
    return "<w:p>%s%s</w:p>" % (ppr, run(text) if text else "")


def cell(text, span=1, vmerge=None):
    tcpr = ""
    if span > 1:
        tcpr += '<w:gridSpan w:val="%d"/>' % span
    if vmerge == "restart":
        tcpr += '<w:vMerge w:val="restart"/>'
    elif vmerge == "continue":
        tcpr += "<w:vMerge/>"
    if tcpr:
        tcpr = "<w:tcPr>%s</w:tcPr>" % tcpr
    return "<w:tc>%s%s</w:tc>" % (tcpr, para(text))


def table(rows):
    body = "".join("<w:tr>%s</w:tr>" % "".join(r) for r in rows)
    return "<w:tbl><w:tblPr/><w:tblGrid><w:gridCol/><w:gridCol/></w:tblGrid>%s</w:tbl>" % body


def document(merged):
    if merged:
        rows = [
            [cell("Summary", span=2)],
            [cell("Total", vmerge="restart"), cell("1200")],
            [cell("", vmerge="continue"), cell("950")],
        ]
    else:
        rows = [
            [cell("Region"), cell("Revenue")],
            [cell("North, east"), cell("1200")],
            [cell("South"), cell("950")],
        ]
    parts = [
        para("Quarterly Report", "Heading1"),
        para("Revenue by region."),
        para("Regions", "Heading2"),
        table(rows),
        para("End of report."),
    ]
    return XML_HEAD + '<w:document xmlns:w="%s"><w:body>%s</w:body></w:document>' % (WNS, "".join(parts))


def hostile_document():
    # UTF-16 (with byte order mark) and a DOCTYPE with an entity declaration.
    text = (
        '<!DOCTYPE w:document [<!ENTITY x "y">]>'
        + '<w:document xmlns:w="%s"><w:body>%s</w:body></w:document>' % (WNS, para("Hostile"))
    )
    return text.encode("utf-16")


def main(argv):
    options = ("--merged", "--hostile")
    if len(argv) not in (2, 3) or (len(argv) == 3 and argv[2] not in options):
        sys.stderr.write("usage: build_fixture.py <output.docx> [--merged | --hostile]\n")
        return 2
    out_path = argv[1]
    option = argv[2] if len(argv) == 3 else None
    if option == "--hostile":
        document_bytes = hostile_document()
    else:
        document_bytes = document(option == "--merged").encode("utf-8")
    parts = [
        ("[Content_Types].xml", CONTENT_TYPES.encode("utf-8")),
        ("_rels/.rels", RELS.encode("utf-8")),
        ("word/document.xml", document_bytes),
        ("word/styles.xml", STYLES.encode("utf-8")),
    ]
    try:
        with zipfile.ZipFile(out_path, "x", zipfile.ZIP_DEFLATED) as zf:
            for name, data in parts:
                zf.writestr(name, data)
    except FileExistsError:
        sys.stderr.write("refused: the output path already exists\n")
        return 2
    except OSError:
        sys.stderr.write("refused: the output could not be written\n")
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
