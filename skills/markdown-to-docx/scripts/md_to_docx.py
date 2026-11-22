"""Convert one Markdown file into a new Word .docx file, standard library only.

Usage:
    python -I md_to_docx.py <input-file> <output-file>.docx

The input is read once as UTF-8 (at most 2 MB). The output is created with
exclusive-create mode, so an existing file is never overwritten and the input
is never written. After writing, the .docx is re-opened and paragraphs,
headings, list items and tables are counted from the stored XML and compared
with the counts written.

Exit codes: 0 = converted, no findings. 1 = converted with findings
(unsupported syntax, or a read-back mismatch). 2 = usage or input error,
nothing written.
Result: one JSON line on stdout. Error: one JSON line on stderr.
"""
import json
import os
import re
import sys
import zipfile
import xml.etree.ElementTree as ET
from xml.sax.saxutils import escape

MAX_BYTES = 2 * 1024 * 1024
W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
FINDINGS_SHOWN = 200
CELL_WIDTH = 2000  # twips, working value

FENCE_RE = re.compile(r"^\s*(```|~~~)")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.*\S)\s*$")
HR_RE = re.compile(r"^\s*([-*_])(\s*\1){2,}\s*$")
BULLET_RE = re.compile(r"^(\s*)[-*+]\s+(.*\S)\s*$")
NUMBER_RE = re.compile(r"^(\s*)(\d{1,9}[.)])\s+(.*\S)\s*$")
QUOTE_RE = re.compile(r"^\s*>\s?(.*)$")
HTML_RE = re.compile(r"^\s*</?[A-Za-z!]")
SEP_RE = re.compile(r"^\s*\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)*\|?\s*$")
INLINE_RE = re.compile(
    r"`([^`]+)`"
    r"|!\[([^\]]*)\]\(([^)\s]+)\)"
    r"|\[([^\]]+)\]\(([^)\s]+)\)"
    r"|\*\*(.+?)\*\*"
    r"|\*(?![\s*])([^*]+?)\*"
)
UNDERSCORE_RE = re.compile(r"(?<!\w)_(?!\s)[^_]+?_(?!\w)")
CONTROL_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")


def fail(code, detail):
    sys.stderr.write(json.dumps({"error": code, "detail": detail}) + "\n")
    sys.exit(2)


def add(findings, line, code, detail):
    findings.append({"line": line, "code": code, "detail": detail})


def inline_runs(text, line, findings):
    """Split inline Markdown into (text, bold, italic, code) runs."""
    runs = []

    def plain(s):
        if not s:
            return
        if UNDERSCORE_RE.search(s):
            add(findings, line, "UNDERSCORE_EMPHASIS_LITERAL",
                "underscore emphasis is kept as literal underscores")
        runs.append((s, False, False, False))

    pos = 0
    for m in INLINE_RE.finditer(text):
        plain(text[pos:m.start()])
        pos = m.end()
        if m.group(1) is not None:
            runs.append((m.group(1), False, False, True))
        elif m.group(3) is not None:
            add(findings, line, "IMAGE_NOT_EMBEDDED",
                "image written as alt text followed by its path")
            alt = m.group(2)
            runs.append(((alt + " " if alt else "") + "(" + m.group(3) + ")",
                         False, False, False))
        elif m.group(5) is not None:
            runs.append((m.group(4), False, False, False))
            runs.append((" (" + m.group(5) + ")", False, False, False))
        elif m.group(6) is not None:
            if "*" in m.group(6):
                add(findings, line, "NESTED_EMPHASIS_LITERAL",
                    "emphasis inside bold is kept as literal asterisks")
            runs.append((m.group(6), True, False, False))
        else:
            runs.append((m.group(7), False, True, False))
    plain(text[pos:])
    return runs


def runs_xml(runs, force_bold=False):
    out = []
    for text, bold, italic, code in runs:
        text = CONTROL_RE.sub("", text)
        if not text:
            continue
        rpr = ""
        if code:
            rpr += '<w:rFonts w:ascii="Consolas" w:hAnsi="Consolas"/>'
        if bold or force_bold:
            rpr += "<w:b/>"
        if italic:
            rpr += "<w:i/>"
        out.append("<w:r>" + ("<w:rPr>" + rpr + "</w:rPr>" if rpr else "")
                   + '<w:t xml:space="preserve">' + escape(text) + "</w:t></w:r>")
    return "".join(out)


def para_xml(runs, style=None, bullet=False, force_bold=False):
    ppr = ""
    if style:
        ppr += '<w:pStyle w:val="%s"/>' % style
    if bullet:
        ppr += '<w:numPr><w:ilvl w:val="0"/><w:numId w:val="1"/></w:numPr>'
    return ("<w:p>" + ("<w:pPr>" + ppr + "</w:pPr>" if ppr else "")
            + runs_xml(runs, force_bold) + "</w:p>")


def split_row(line):
    s = line.strip()
    if s.startswith("|"):
        s = s[1:]
    if s.endswith("|") and not s.endswith("\\|"):
        s = s[:-1]
    cells = re.split(r"(?<!\\)\|", s)
    return [c.strip().replace("\\|", "|") for c in cells]


def convert(lines):
    """Return (body_xml_list, counts, findings) for the Markdown lines."""
    body = []
    findings = []
    counts = {"paragraphs": 0, "headings": 0, "list_items": 0, "tables": 0}
    pending = []

    def emit(xml, kind):
        body.append(xml)
        if kind in ("para", "heading", "list"):
            counts["paragraphs"] += 1
        if kind == "heading":
            counts["headings"] += 1
        if kind == "list":
            counts["list_items"] += 1
        if kind == "table":
            counts["tables"] += 1

    def flush():
        if pending:
            first = pending[0][0]
            text = " ".join(t for _, t in pending)
            emit(para_xml(inline_runs(text, first, findings)), "para")
            pending.clear()

    def row_xml(cells, lineno, is_header):
        trpr = "<w:trPr><w:tblHeader/></w:trPr>" if is_header else ""
        tcs = []
        for c in cells:
            para = para_xml(inline_runs(c, lineno, findings), force_bold=is_header)
            tcs.append('<w:tc><w:tcPr><w:tcW w:w="%d" w:type="dxa"/></w:tcPr>%s</w:tc>'
                       % (CELL_WIDTH, para))
        return "<w:tr>" + trpr + "".join(tcs) + "</w:tr>"

    def table_xml(header, header_line, rows):
        ncol = len(header)
        edges = ("top", "left", "bottom", "right", "insideH", "insideV")
        borders = "".join('<w:%s w:val="single" w:sz="4" w:space="0" w:color="auto"/>' % e
                          for e in edges)
        grid = "".join('<w:gridCol w:w="%d"/>' % CELL_WIDTH for _ in range(ncol))
        parts = ['<w:tbl><w:tblPr><w:tblW w:w="0" w:type="auto"/><w:tblBorders>'
                 + borders + "</w:tblBorders></w:tblPr><w:tblGrid>" + grid + "</w:tblGrid>"]
        parts.append(row_xml(header, header_line, True))
        for lineno, cells in rows:
            if len(cells) != ncol:
                add(findings, lineno, "TABLE_RAGGED_ROW",
                    "row has %d cells, header has %d; padded or cut" % (len(cells), ncol))
                cells = (cells + [""] * ncol)[:ncol]
            parts.append(row_xml(cells, lineno, False))
        parts.append("</w:tbl>")
        return "".join(parts)

    i = 0
    n = len(lines)
    in_quote = False
    while i < n:
        lineno = i + 1
        line = CONTROL_RE.sub("", lines[i]).rstrip()
        was_quote = in_quote
        in_quote = False

        if not line.strip():
            flush()
            i += 1
            continue

        if FENCE_RE.match(line):
            flush()
            add(findings, lineno, "CODE_FENCE_AS_PARAGRAPH",
                "fence markers dropped, code lines kept as plain paragraphs")
            i += 1
            while i < n and not FENCE_RE.match(lines[i]):
                code_line = CONTROL_RE.sub("", lines[i]).rstrip()
                if code_line.strip():
                    emit(para_xml([(code_line, False, False, False)]), "para")
                i += 1
            i += 1
            continue

        m = HEADING_RE.match(line)
        if m:
            flush()
            level = len(m.group(1))
            runs = inline_runs(m.group(2), lineno, findings)
            if level <= 3:
                emit(para_xml(runs, style="Heading%d" % level), "heading")
            else:
                add(findings, lineno, "HEADING_LEVEL_UNSUPPORTED",
                    "level %d written as a Normal paragraph" % level)
                emit(para_xml(runs), "para")
            i += 1
            continue

        if HR_RE.match(line):
            flush()
            add(findings, lineno, "HORIZONTAL_RULE_DROPPED", "rule removed")
            i += 1
            continue

        if "|" in line and i + 1 < n and "|" in lines[i + 1] and SEP_RE.match(lines[i + 1]):
            flush()
            header = split_row(line)
            rows = []
            j = i + 2
            while j < n and "|" in lines[j] and lines[j].strip():
                rows.append((j + 1, split_row(CONTROL_RE.sub("", lines[j]))))
                j += 1
            emit(table_xml(header, lineno, rows), "table")
            i = j
            continue

        if line.lstrip().startswith("|"):
            add(findings, lineno, "TABLE_MISSING_SEPARATOR",
                "pipe line without a separator row kept as paragraph text")

        qm = QUOTE_RE.match(line)
        if qm:
            if not was_quote:
                add(findings, lineno, "BLOCKQUOTE_AS_PARAGRAPH",
                    "quote marker removed, text kept as a paragraph")
            in_quote = True
            pending.append((lineno, qm.group(1).strip()))
            i += 1
            continue

        if HTML_RE.match(line):
            add(findings, lineno, "HTML_TEXT_KEPT", "raw HTML kept as plain text")

        bm = BULLET_RE.match(line)
        nm = NUMBER_RE.match(line)
        if bm or nm:
            flush()
            mm = bm or nm
            if len(mm.group(1).expandtabs(4)) >= 2:
                add(findings, lineno, "NESTED_LIST_FLATTENED",
                    "indented list item written at the top list level")
            if bm:
                runs = inline_runs(bm.group(2), lineno, findings)
                emit(para_xml(runs, style="ListParagraph", bullet=True), "list")
            else:
                runs = [(nm.group(2) + " ", False, False, False)]
                runs += inline_runs(nm.group(3), lineno, findings)
                emit(para_xml(runs, style="ListParagraph"), "list")
            i += 1
            continue

        pending.append((lineno, line.strip()))
        i += 1

    flush()
    return body, counts, findings


CT_NS = "http://schemas.openxmlformats.org/package/2006/content-types"
REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
OFFICE_REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
XML_HEAD = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'

CONTENT_TYPES = (
    XML_HEAD
    + '<Types xmlns="%s">' % CT_NS
    + '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
    + '<Default Extension="xml" ContentType="application/xml"/>'
    + '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
    + '<Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>'
    + '<Override PartName="/word/numbering.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.numbering+xml"/>'
    + "</Types>"
)
ROOT_RELS = (
    XML_HEAD
    + '<Relationships xmlns="%s"><Relationship Id="rId1" Type="%s/officeDocument" Target="word/document.xml"/></Relationships>'
    % (REL_NS, OFFICE_REL)
)
DOC_RELS = (
    XML_HEAD
    + '<Relationships xmlns="%s">' % REL_NS
    + '<Relationship Id="rId1" Type="%s/styles" Target="styles.xml"/>' % OFFICE_REL
    + '<Relationship Id="rId2" Type="%s/numbering" Target="numbering.xml"/>' % OFFICE_REL
    + "</Relationships>"
)
STYLES = (
    XML_HEAD
    + '<w:styles xmlns:w="%s">' % W
    + '<w:docDefaults><w:rPrDefault><w:rPr><w:rFonts w:ascii="Calibri" w:hAnsi="Calibri" '
      'w:eastAsia="Calibri" w:cs="Calibri"/><w:sz w:val="22"/></w:rPr></w:rPrDefault>'
      '<w:pPrDefault><w:pPr><w:spacing w:after="160" w:line="259" w:lineRule="auto"/>'
      '</w:pPr></w:pPrDefault></w:docDefaults>'
    + '<w:style w:type="paragraph" w:default="1" w:styleId="Normal"><w:name w:val="Normal"/>'
      '<w:qFormat/></w:style>'
    + '<w:style w:type="paragraph" w:styleId="Heading1"><w:name w:val="heading 1"/>'
      '<w:basedOn w:val="Normal"/><w:next w:val="Normal"/><w:qFormat/><w:pPr><w:keepNext/>'
      '<w:spacing w:before="240" w:after="120"/><w:outlineLvl w:val="0"/></w:pPr>'
      '<w:rPr><w:b/><w:sz w:val="32"/></w:rPr></w:style>'
    + '<w:style w:type="paragraph" w:styleId="Heading2"><w:name w:val="heading 2"/>'
      '<w:basedOn w:val="Normal"/><w:next w:val="Normal"/><w:qFormat/><w:pPr><w:keepNext/>'
      '<w:spacing w:before="200" w:after="100"/><w:outlineLvl w:val="1"/></w:pPr>'
      '<w:rPr><w:b/><w:sz w:val="28"/></w:rPr></w:style>'
    + '<w:style w:type="paragraph" w:styleId="Heading3"><w:name w:val="heading 3"/>'
      '<w:basedOn w:val="Normal"/><w:next w:val="Normal"/><w:qFormat/><w:pPr><w:keepNext/>'
      '<w:spacing w:before="160" w:after="80"/><w:outlineLvl w:val="2"/></w:pPr>'
      '<w:rPr><w:b/><w:sz w:val="24"/></w:rPr></w:style>'
    + '<w:style w:type="paragraph" w:styleId="ListParagraph"><w:name w:val="List Paragraph"/>'
      '<w:basedOn w:val="Normal"/><w:qFormat/><w:pPr><w:spacing w:after="60"/>'
      '<w:ind w:left="360" w:hanging="360"/></w:pPr></w:style>'
    + "</w:styles>"
)
NUMBERING = (
    XML_HEAD
    + '<w:numbering xmlns:w="%s">' % W
    + '<w:abstractNum w:abstractNumId="0"><w:multiLevelType w:val="singleLevel"/>'
      '<w:lvl w:ilvl="0"><w:start w:val="1"/><w:numFmt w:val="bullet"/>'
      '<w:lvlText w:val="\u2022"/><w:lvlJc w:val="left"/>'
      '<w:pPr><w:ind w:left="360" w:hanging="360"/></w:pPr></w:lvl></w:abstractNum>'
    + '<w:num w:numId="1"><w:abstractNumId w:val="0"/></w:num>'
    + "</w:numbering>"
)


def document_xml(body):
    return (
        XML_HEAD
        + '<w:document xmlns:w="%s"><w:body>' % W
        + "".join(body)
        + '<w:sectPr><w:pgSz w:w="12240" w:h="15840"/>'
          '<w:pgMar w:top="1440" w:right="1440" w:bottom="1440" w:left="1440" '
          'w:header="720" w:footer="720" w:gutter="0"/></w:sectPr></w:body></w:document>'
    )


def write_docx(path, body):
    parts = [
        ("[Content_Types].xml", CONTENT_TYPES),
        ("_rels/.rels", ROOT_RELS),
        ("word/document.xml", document_xml(body)),
        ("word/styles.xml", STYLES),
        ("word/numbering.xml", NUMBERING),
        ("word/_rels/document.xml.rels", DOC_RELS),
    ]
    try:
        # mode "x" raises FileExistsError if the path already exists
        with zipfile.ZipFile(path, "x", compression=zipfile.ZIP_DEFLATED) as z:
            for name, content in parts:
                z.writestr(name, content.encode("utf-8"))
    except FileExistsError:
        raise
    except OSError:
        if os.path.exists(path):
            os.remove(path)
        raise


def read_back(path):
    """Re-open the written .docx and count body-level elements from the XML."""
    with zipfile.ZipFile(path, "r") as z:
        if z.testzip() is not None:
            raise ValueError("bad CRC in written file")
        xml_bytes = z.read("word/document.xml")
    if b"<!DOCTYPE" in xml_bytes or b"<!ENTITY" in xml_bytes:
        raise ValueError("DTD or entity declaration found")
    root = ET.fromstring(xml_bytes)
    body = root.find("{%s}body" % W)
    counts = {"paragraphs": 0, "headings": 0, "list_items": 0, "tables": 0}
    if body is None:
        raise ValueError("no w:body element")
    for el in body:
        if el.tag == "{%s}tbl" % W:
            counts["tables"] += 1
        elif el.tag == "{%s}p" % W:
            counts["paragraphs"] += 1
            st = el.find("{%s}pPr/{%s}pStyle" % (W, W))
            val = st.get("{%s}val" % W, "") if st is not None else ""
            if val.startswith("Heading"):
                counts["headings"] += 1
            elif val == "ListParagraph":
                counts["list_items"] += 1
    return counts


def main(argv):
    if len(argv) != 3:
        fail("USAGE", "usage: md_to_docx.py <input-file> <output-file>.docx")
    src, dst = argv[1], argv[2]
    if not dst.lower().endswith(".docx"):
        fail("OUTPUT_NOT_DOCX", "output name must end in .docx")
    if not os.path.isfile(src):
        fail("INPUT_MISSING", "input file not found")
    if os.path.getsize(src) > MAX_BYTES:
        fail("INPUT_TOO_LARGE", "input is larger than 2 MB")
    if os.path.abspath(src) == os.path.abspath(dst):
        fail("OUTPUT_SAME_AS_INPUT", "output path must differ from the input path")
    if not os.path.isdir(os.path.dirname(os.path.abspath(dst))):
        fail("OUTPUT_DIR_MISSING", "output folder does not exist")
    if os.path.exists(dst):
        fail("OUTPUT_EXISTS", "output already exists; choose a new file name")
    with open(src, "rb") as fh:
        data = fh.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        fail("INPUT_TOO_LARGE", "input is larger than 2 MB")
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        fail("INPUT_NOT_UTF8", "input is not valid UTF-8 text")
    text = text.lstrip("\ufeff")

    body, counts, findings = convert(text.splitlines())
    try:
        write_docx(dst, body)
    except FileExistsError:
        fail("OUTPUT_EXISTS", "output already exists; choose a new file name")
    except OSError:
        fail("WRITE_FAILED", "could not write the output file")

    got = None
    try:
        got = read_back(dst)
    except (zipfile.BadZipFile, ET.ParseError, SyntaxError, KeyError, OSError, ValueError) as exc:
        add(findings, 0, "READBACK_MISMATCH", "re-open failed: %s" % type(exc).__name__)
    if got is not None and got != counts:
        add(findings, 0, "READBACK_MISMATCH", "counts read back differ from counts written")

    findings.sort(key=lambda f: f["line"])
    result = {
        "status": "findings" if findings else "ok",
        "input": os.path.basename(src),
        "output": os.path.basename(dst),
        "written": counts,
        "readback": got,
        "match": got == counts,
        "findings_total": len(findings),
        "findings": findings[:FINDINGS_SHOWN],
    }
    sys.stdout.write(json.dumps(result, ensure_ascii=True) + "\n")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
