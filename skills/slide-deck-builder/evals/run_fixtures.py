#!/usr/bin/env python3
"""Run the fixture cases in fixtures/cases.json against scripts/deck_check.py.

    python evals/run_fixtures.py

Text fixtures are read from evals/fixtures/. The .pptx fixtures are built on the
fly from the PPTX_BUILDS table below into a temporary folder (so the package
stays text only) and deleted afterwards. Nothing else is written.
Exit 0 if every case matches, 1 otherwise.
"""
import contextlib
import io
import json
import os
import sys
import tempfile
import zipfile
from xml.sax.saxutils import escape

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "scripts"))
import deck_check  # noqa: E402

NS = ('xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" '
      'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" '
      'xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"')
REL_TYPE = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"


def para(text, sz=None):
    rpr = '<a:rPr lang="en-US" sz="%d"/>' % int(sz * 100) if sz else '<a:rPr lang="en-US"/>'
    return "<a:p><a:r>%s<a:t>%s</a:t></a:r></a:p>" % (rpr, escape(text))


def shape(sid, ph, paras):
    ph_xml = '<p:ph type="%s"/>' % ph if ph else ""
    return ('<p:sp><p:nvSpPr><p:cNvPr id="%d" name="S%d"/><p:cNvSpPr/><p:nvPr>%s</p:nvPr></p:nvSpPr>'
            '<p:spPr/><p:txBody><a:bodyPr/>%s</p:txBody></p:sp>' % (sid, sid, ph_xml, "".join(paras)))


def picture(sid, name, descr):
    return ('<p:pic><p:nvPicPr><p:cNvPr id="%d" name="%s" descr="%s"/><p:cNvPicPr/><p:nvPr/></p:nvPicPr>'
            '<p:blipFill/><p:spPr/></p:pic>' % (sid, escape(name), escape(descr)))


def chart_frame(sid):
    return ('<p:graphicFrame><p:nvGraphicFramePr><p:cNvPr id="%d" name="Chart %d"/><p:cNvGraphicFramePr/><p:nvPr/>'
            '</p:nvGraphicFramePr><p:xfrm/><a:graphic><a:graphicData '
            'uri="http://schemas.openxmlformats.org/drawingml/2006/chart"/></a:graphic></p:graphicFrame>' % (sid, sid))


def build_pptx(path, slides):
    """slides: list of dicts with optional keys title, paras [(text, pt)], pics [(name, descr)], chart, notes."""
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", '<?xml version="1.0"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"/>')
        ids = "".join('<p:sldId id="%d" r:id="rId%d"/>' % (255 + i, i) for i in range(1, len(slides) + 1))
        z.writestr("ppt/presentation.xml", '<?xml version="1.0"?><p:presentation %s><p:sldIdLst>%s</p:sldIdLst></p:presentation>' % (NS, ids))
        rels = "".join('<Relationship Id="rId%d" Type="%s/slide" Target="slides/slide%d.xml"/>' % (i, REL_TYPE, i)
                       for i in range(1, len(slides) + 1))
        z.writestr("ppt/_rels/presentation.xml.rels",
                   '<?xml version="1.0"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">%s</Relationships>' % rels)
        for i, s in enumerate(slides, 1):
            body, sid = [], 2
            if s.get("title"):
                body.append(shape(sid, "title", [para(s["title"], 32)])); sid += 1
            if s.get("paras"):
                body.append(shape(sid, None, [para(t, pt) for t, pt in s["paras"]])); sid += 1
            body.append(shape(sid, "sldNum", [para("%d" % i, 10)])); sid += 1
            if s.get("chart"):
                body.append(chart_frame(sid)); sid += 1
            for name, descr in s.get("pics", []):
                body.append(picture(sid, name, descr)); sid += 1
            z.writestr("ppt/slides/slide%d.xml" % i,
                       '<?xml version="1.0"?><p:sld %s><p:cSld><p:spTree>%s</p:spTree></p:cSld></p:sld>' % (NS, "".join(body)))
            if s.get("notes"):
                z.writestr("ppt/slides/_rels/slide%d.xml.rels" % i,
                           '<?xml version="1.0"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                           '<Relationship Id="rId1" Type="%s/notesSlide" Target="../notesSlides/notesSlide%d.xml"/></Relationships>' % (REL_TYPE, i))
                z.writestr("ppt/notesSlides/notesSlide%d.xml" % i,
                           '<?xml version="1.0"?><p:notes %s><p:cSld><p:spTree>%s%s</p:spTree></p:cSld></p:notes>'
                           % (NS, shape(2, "sldImg", []), shape(3, "body", [para(s["notes"])])))


LONG_NOTES = ("Say the result first, then explain how we measured it. The figures come from the live system over three "
              "months, and the control group stayed flat, so season does not explain the change we saw here.")

PPTX_BUILDS = {
    "good.pptx": [
        {"title": "Support tickets fell 40% after in-app help", "paras": [("Pilot: 2,000 accounts", 20)], "notes": LONG_NOTES},
        {"title": "Tickets per 100 accounts dropped from 12.5 to 7.5",
         "paras": [("Source: Support desk export, Mar-May 2026", 12)],
         "pics": [("Chart 1", "Bar chart: control 12.5, pilot 7.5 tickets per 100 accounts")], "notes": LONG_NOTES},
    ],
    "bad.pptx": [
        {"title": "Overview", "paras": [("Line %d of the agenda for today" % k, 20) for k in range(1, 9)]},
        {"title": "Overview", "paras": [("Footnote text that is far too small to read", 10)],
         "chart": True, "pics": [("Picture 7", "")], "notes": LONG_NOTES},
        {"paras": [("A slide with no title", 14)], "notes": LONG_NOTES},
    ],
}


def run_case(case, tmp):
    if "build" in case:
        path = os.path.join(tmp, case["build"])
        build_pptx(path, PPTX_BUILDS[case["build"]])
    else:
        path = os.path.join(HERE, "fixtures", case["file"])
    args = [path] + case.get("extra_args", [])
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = deck_check.main(args)
    problems = []
    if code != case["exit"]:
        problems.append("exit %r, wanted %r" % (code, case["exit"]))
    if code in (0, 1):
        rep = json.loads(out.getvalue())
        got = {
            "format": rep["format"], "slide_count": rep["slide_count"], "counts": rep["counts"], "ok": rep["ok"],
            "appendix_starts_at": rep["appendix_starts_at"],
            "rules": ["%d:%s" % (f["slide"], f["rule"]) for f in rep["findings"]],
        }
        for key, want in case["expect"].items():
            if got.get(key) != want:
                problems.append("%s: got %r, wanted %r" % (key, got.get(key), want))
    elif case["expect"].get("stderr_contains") and case["expect"]["stderr_contains"] not in err.getvalue():
        problems.append("stderr %r does not contain %r" % (err.getvalue(), case["expect"]["stderr_contains"]))
    return problems


def main():
    cases = json.load(open(os.path.join(HERE, "fixtures", "cases.json"), encoding="utf-8"))["cases"]
    failed = 0
    with tempfile.TemporaryDirectory() as tmp:
        for case in cases:
            problems = run_case(case, tmp)
            print(("PASS " if not problems else "FAIL ") + case["name"])
            for p in problems:
                print("    " + p)
            failed += bool(problems)
    print("%d/%d cases passed" % (len(cases) - failed, len(cases)))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
