"""Build the smoke-test .pptx at runtime in a new temporary folder.

Usage:
    python build_fixture.py [--empty-slide] [--hostile]

Writes one .pptx into a new temp folder and prints its absolute path on stdout.
No binary file is stored in the skill folder. The default deck has 3 slides with
a table and notes. --empty-slide appends a fourth slide that has notes only, no
title, body or table text, which makes the script exit 1. --hostile replaces
slide 1 with a UTF-16 part that carries a DOCTYPE, which makes the script exit 2
with code unsafe_xml.
"""

import argparse
import os
import tempfile
import zipfile
from xml.sax.saxutils import escape

NS = ('xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" '
      'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" '
      'xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"')
REL_OFFICE = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument"
REL_SLIDE = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide"
REL_NOTES = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/notesSlide"
CT_PRESENTATION = "application/vnd.openxmlformats-officedocument.presentationml.presentation.main+xml"
CT_SLIDE = "application/vnd.openxmlformats-officedocument.presentationml.slide+xml"
CT_NOTES = "application/vnd.openxmlformats-officedocument.presentationml.notesSlide+xml"
XML_HEAD = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
GROUP = '<p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr><p:grpSpPr/>'

SLIDES = [
    {"title": "Quarterly review",
     "body": ["Prepared for the sales team", "Q3 results"],
     "table": None,
     "notes": ["Open with the Q3 summary."]},
    {"title": "Regional sales",
     "body": ["North grew fastest"],
     "table": [["Region", "Sales"], ["North", "120"], ["South", "95"]],
     "notes": ["Mention the South dip."]},
    {"title": "Next steps",
     "body": ["Confirm Q4 targets", "Review hiring plan"],
     "table": None,
     "notes": []},
]
EMPTY_SLIDE = {"title": None, "body": [], "table": None,
               "notes": ["Blank slide with notes only."]}


def para(text):
    return '<a:p><a:r><a:rPr lang="en-US"/><a:t>%s</a:t></a:r></a:p>' % escape(text)


def shape(shape_id, ph_xml, lines):
    paras = "".join(para(t) for t in lines) or "<a:p/>"
    return ('<p:sp><p:nvSpPr><p:cNvPr id="%d" name="Shape %d"/><p:cNvSpPr/>'
            '<p:nvPr>%s</p:nvPr></p:nvSpPr><p:spPr/>'
            '<p:txBody><a:bodyPr/><a:lstStyle/>%s</p:txBody></p:sp>'
            % (shape_id, shape_id, ph_xml, paras))


def table_frame(shape_id, rows):
    grid = "".join('<a:gridCol w="1600000"/>' for _ in rows[0])
    trs = []
    for row in rows:
        cells = "".join('<a:tc><a:txBody><a:bodyPr/><a:lstStyle/>%s</a:txBody><a:tcPr/></a:tc>'
                        % para(c) for c in row)
        trs.append('<a:tr h="370840">%s</a:tr>' % cells)
    return ('<p:graphicFrame><p:nvGraphicFramePr><p:cNvPr id="%d" name="Table %d"/>'
            '<p:cNvGraphicFramePr/><p:nvPr/></p:nvGraphicFramePr>'
            '<p:xfrm><a:off x="457200" y="2000000"/><a:ext cx="3200000" cy="1100000"/></p:xfrm>'
            '<a:graphic><a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/table">'
            '<a:tbl><a:tblPr firstRow="1"/><a:tblGrid>%s</a:tblGrid>%s</a:tbl>'
            '</a:graphicData></a:graphic></p:graphicFrame>'
            % (shape_id, shape_id, grid, "".join(trs)))


def slide_xml(slide):
    shapes = []
    if slide["title"]:
        shapes.append(shape(2, '<p:ph type="title"/>', [slide["title"]]))
    if slide["body"]:
        shapes.append(shape(3, '<p:ph type="body" idx="1"/>', slide["body"]))
    if slide["table"]:
        shapes.append(table_frame(4, slide["table"]))
    return (XML_HEAD + '<p:sld %s><p:cSld><p:spTree>%s%s</p:spTree></p:cSld>'
            '<p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr></p:sld>'
            % (NS, GROUP, "".join(shapes)))


def notes_xml(lines):
    return (XML_HEAD + '<p:notes %s><p:cSld><p:spTree>%s%s</p:spTree></p:cSld></p:notes>'
            % (NS, GROUP, shape(2, '<p:ph type="body" idx="1"/>', lines)))


def presentation_xml(count):
    ids = "".join('<p:sldId id="%d" r:id="rId%d"/>' % (255 + n, n) for n in range(1, count + 1))
    return (XML_HEAD + '<p:presentation %s><p:sldIdLst>%s</p:sldIdLst>'
            '<p:sldSz cx="9144000" cy="6858000"/><p:notesSz cx="6858000" cy="9144000"/>'
            '</p:presentation>' % (NS, ids))


def rels_xml(items):
    body = "".join('<Relationship Id="%s" Type="%s" Target="%s"/>' % item for item in items)
    return (XML_HEAD + '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '%s</Relationships>' % body)


def content_types_xml(names):
    overrides = []
    for name in names:
        if name.endswith(".rels") or name == "[Content_Types].xml":
            continue
        if name.startswith("ppt/notesSlides/"):
            ctype = CT_NOTES
        elif name.startswith("ppt/slides/"):
            ctype = CT_SLIDE
        else:
            ctype = CT_PRESENTATION
        overrides.append('<Override PartName="/%s" ContentType="%s"/>' % (name, ctype))
    return (XML_HEAD + '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
            '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
            '<Default Extension="xml" ContentType="application/xml"/>%s</Types>' % "".join(overrides))


def hostile_slide_bytes():
    """Slide 1 encoded as UTF-16 with a DOCTYPE and an entity declaration."""
    body = slide_xml(SLIDES[0]).split("?>\n", 1)[1]
    text = ('<?xml version="1.0" encoding="UTF-16"?>\n'
            '<!DOCTYPE p:sld [<!ENTITY probe "x">]>\n' + body)
    return text.encode("utf-16")


def build(path, slides, overrides=None):
    files = {}
    files["ppt/presentation.xml"] = presentation_xml(len(slides))
    files["_rels/.rels"] = rels_xml([("rId1", REL_OFFICE, "ppt/presentation.xml")])
    pres_rels = []
    for n, slide in enumerate(slides, 1):
        pres_rels.append(("rId%d" % n, REL_SLIDE, "slides/slide%d.xml" % n))
        files["ppt/slides/slide%d.xml" % n] = slide_xml(slide)
        if slide["notes"]:
            files["ppt/slides/_rels/slide%d.xml.rels" % n] = rels_xml(
                [("rId1", REL_NOTES, "../notesSlides/notesSlide%d.xml" % n)])
            files["ppt/notesSlides/notesSlide%d.xml" % n] = notes_xml(slide["notes"])
            files["ppt/notesSlides/_rels/notesSlide%d.xml.rels" % n] = rels_xml(
                [("rId1", REL_SLIDE, "../slides/slide%d.xml" % n)])
    files["ppt/_rels/presentation.xml.rels"] = rels_xml(pres_rels)
    files.update(overrides or {})
    ordered = [("[Content_Types].xml", content_types_xml(list(files) + ["_rels/.rels"]))]
    ordered.append(("_rels/.rels", files.pop("_rels/.rels")))
    ordered.extend(files.items())
    with zipfile.ZipFile(path, "x", zipfile.ZIP_DEFLATED) as zf:
        for name, data in ordered:
            zf.writestr(name, data)


def main():
    parser = argparse.ArgumentParser(description="Build the smoke-test .pptx in a temp folder.")
    parser.add_argument("--empty-slide", action="store_true",
                        help="append a notes-only slide so the script exits 1")
    parser.add_argument("--hostile", action="store_true",
                        help="make slide 1 a UTF-16 part with a DOCTYPE so the script exits 2 (unsafe_xml)")
    args = parser.parse_args()
    slides = SLIDES + ([EMPTY_SLIDE] if args.empty_slide else [])
    overrides = {"ppt/slides/slide1.xml": hostile_slide_bytes()} if args.hostile else None
    folder = tempfile.mkdtemp(prefix="pptx_text_fixture_")
    path = os.path.join(folder, "smoke_deck.pptx")
    build(path, slides, overrides)
    print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
