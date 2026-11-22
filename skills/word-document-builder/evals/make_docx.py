#!/usr/bin/env python3
"""Build the small .docx test fixtures from plain XML strings (standard library only).

    python evals/make_docx.py OUTPUT_DIR [NAME ...]

Writes good.docx, bad.docx, custom_styles.docx, decorative.docx and not_a_docx.docx
into OUTPUT_DIR (created if missing); with NAME arguments (e.g. bad) only those. The files are minimal packages made to exercise
scripts/docx_inspect.py; they are not guaranteed to open in Word (the pictures have no
image part), because the inspector only reads the XML.
"""
import os
import sys
import zipfile

NS = (
    'xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" '
    'xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing" '
    'xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" '
    'xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture" '
    'xmlns:a14="http://schemas.microsoft.com/office/drawing/2010/main"'
)

CONTENT_TYPES = (
    '<?xml version="1.0" encoding="UTF-8"?>'
    '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
    '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
    '<Default Extension="xml" ContentType="application/xml"/>'
    '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
    '</Types>'
)
ROOT_RELS = (
    '<?xml version="1.0" encoding="UTF-8"?>'
    '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
    '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>'
    '</Relationships>'
)


def style(sid, name, based=None, outline=None, ptype="paragraph"):
    s = '<w:style w:type="%s" w:styleId="%s"><w:name w:val="%s"/>' % (ptype, sid, name)
    if based:
        s += '<w:basedOn w:val="%s"/>' % based
    if outline is not None:
        s += '<w:pPr><w:outlineLvl w:val="%d"/></w:pPr>' % outline
    return s + "</w:style>"


STYLES = (
    '<?xml version="1.0" encoding="UTF-8"?><w:styles %s>' % NS
    + style("Normal", "Normal")
    + style("Title", "Title", "Normal")
    + style("Heading1", "heading 1", "Normal", 0)
    + style("Heading2", "heading 2", "Normal", 1)
    + style("Heading3", "heading 3", "Normal", 2)
    + style("Caption", "caption", "Normal")
    + style("TableGrid", "Table Grid", ptype="table")
    + style("MyHead", "Section Head", "Heading2")
    + "</w:styles>"
)


def para(text, sid=None, extra_ppr=""):
    ppr = ""
    if sid or extra_ppr:
        ppr = "<w:pPr>%s%s</w:pPr>" % ('<w:pStyle w:val="%s"/>' % sid if sid else "", extra_ppr)
    return "<w:p>%s<w:r><w:t>%s</w:t></w:r></w:p>" % (ppr, text)


def table(header, style_id="TableGrid", rows=(("Q1", "10"), ("Q2", "12"))):
    tpr = '<w:tblPr><w:tblStyle w:val="%s"/></w:tblPr>' % style_id if style_id else "<w:tblPr/>"
    out = "<w:tbl>%s<w:tblGrid><w:gridCol w:w=\"3000\"/><w:gridCol w:w=\"3000\"/></w:tblGrid>" % tpr
    first = True
    for row in (("Quarter", "Revenue"),) + tuple(rows):
        trpr = "<w:trPr><w:tblHeader/></w:trPr>" if (first and header) else ""
        out += "<w:tr>%s%s</w:tr>" % (trpr, "".join("<w:tc><w:p><w:r><w:t>%s</w:t></w:r></w:p></w:tc>" % c for c in row))
        first = False
    return out + "</w:tbl>"


def image(descr=None, decorative=False, name="Picture 1"):
    attrs = ' descr="%s"' % descr if descr else ""
    ext = '<a:extLst><a:ext uri="{C183D7F6-B498-43B3-948B-1728B52AA6E4}"><a14:decorative val="1"/></a:ext></a:extLst>' if decorative else ""
    return (
        '<w:p><w:r><w:drawing><wp:inline><wp:extent cx="100" cy="100"/>'
        '<wp:docPr id="1" name="%s"%s>%s</wp:docPr>'
        '<a:graphic><a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture"><pic:pic/></a:graphicData></a:graphic>'
        "</wp:inline></w:drawing></w:r></w:p>" % (name, attrs, ext)
    )


def sectpr(w, h, margin):
    return '<w:sectPr><w:pgSz w:w="%d" w:h="%d"/><w:pgMar w:top="%d" w:right="%d" w:bottom="%d" w:left="%d"/></w:sectPr>' % (w, h, margin, margin, margin, margin)


def core(title, author):
    parts = ""
    if title:
        parts += "<dc:title>%s</dc:title>" % title
    if author:
        parts += "<dc:creator>%s</dc:creator>" % author
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" '
        'xmlns:dc="http://purl.org/dc/elements/1.1/">%s</cp:coreProperties>' % parts
    )


def write(path, body, sect, props=None, footer=False):
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", CONTENT_TYPES)
        zf.writestr("_rels/.rels", ROOT_RELS)
        zf.writestr("word/document.xml", '<?xml version="1.0" encoding="UTF-8"?><w:document %s><w:body>%s%s</w:body></w:document>' % (NS, body, sect))
        zf.writestr("word/styles.xml", STYLES)
        if props is not None:
            zf.writestr("docProps/core.xml", core(*props))
        if footer:
            zf.writestr("word/footer1.xml", '<?xml version="1.0" encoding="UTF-8"?><w:ftr %s><w:p><w:fldSimple w:instr=" PAGE "><w:r><w:t>1</w:t></w:r></w:fldSimple></w:p></w:ftr>' % NS)


def build(out_dir, only=None):
    """Write all fixtures, or only the named ones (e.g. only=("bad",))."""
    os.makedirs(out_dir, exist_ok=True)
    _write = globals()["write"]
    def write(path, *a, **k):
        if only is None or os.path.basename(path)[:-5] in only:
            _write(path, *a, **k)

    toc = '<w:p><w:fldSimple w:instr=" TOC \\o &quot;1-3&quot; "><w:r><w:t>Contents</w:t></w:r></w:fldSimple></w:p>'
    good = (
        para("Quarterly Report", "Title") + toc
        + para("1 Introduction", "Heading1") + para("This report covers revenue for the first half of the year.")
        + para("2 Results", "Heading1") + para("Revenue grew in both quarters.")
        + para("Table 1: Revenue by quarter", "Caption") + table(True)
        + image("Bar chart of revenue by quarter") + para("Figure 1: Revenue by quarter", "Caption")
        + para("2.1 Detail", "Heading2") + para("Quarter two was driven by renewals.")
        + para("3 Next steps", "Heading1") + para("Hire two analysts and repeat the review in September.")
    )
    write(os.path.join(out_dir, "good.docx"), good, sectpr(11906, 16838, 1440), ("Quarterly Report", "Dana Cohen"), footer=True)

    bad = (
        para("Introduction", "Heading1") + para("Opening paragraph.")
        + para("Deep detail", "Heading3") + para("TODO write this section")
        + para("Results", "Heading1")
        + para("Summary", "Heading1") + para("Short summary.")
        + table(False, style_id=None)
        + image(None)
    )
    write(os.path.join(out_dir, "bad.docx"), bad, sectpr(12240, 15840, 720), None)

    custom = (
        para("Alpha", None, '<w:outlineLvl w:val="0"/>') + para("Body of alpha.")
        + para("Beta", "MyHead") + para("Body of beta.")
    )
    write(os.path.join(out_dir, "custom_styles.docx"), custom, sectpr(11906, 16838, 1440), ("Custom", "A. Writer"))

    deco = para("Banner", "Heading1") + image(None, decorative=True) + para("Text under the banner.")
    write(os.path.join(out_dir, "decorative.docx"), deco, sectpr(11906, 16838, 1440), ("Deco", "A. Writer"))

    if only is None or "not_a_docx" in only:
        with open(os.path.join(out_dir, "not_a_docx.docx"), "w", encoding="utf-8") as fh:
            fh.write("this is plain text, not a zip archive\n")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.stderr.write("usage: make_docx.py OUTPUT_DIR\n")
        sys.exit(2)
    build(sys.argv[1], tuple(sys.argv[2:]) or None)
