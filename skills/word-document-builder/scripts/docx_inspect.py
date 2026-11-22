#!/usr/bin/env python3
"""Inspect a .docx file and optionally check it against a style contract.

Usage:
    python docx_inspect.py FILE.docx [--contract CONTRACT.json]

Reads: the .docx (a zip of XML parts) and, if given, the contract JSON.
Writes: one JSON document to stdout. Nothing is written to disk, nothing is
executed, no network is used. Only the Python standard library is imported.

Exit codes:
    0  file parsed; no contract given, or every contract rule passed
    1  file parsed; at least one contract rule failed
    2  usage problem, unreadable or unsupported file, or invalid contract

What is measured (all from the XML, nothing is rendered):
    document properties (title, author), page size / orientation / margins,
    heading hierarchy from paragraph styles (Title, Heading 1-9, outline level),
    heading numbering, tables (rows, columns, style, repeat-header-row flag,
    caption neighbour), images (alt text in wp:docPr descr, decorative flag,
    caption neighbour), empty sections, table of contents field, page-number
    field in footers, leftover placeholder text, tracked changes.
"""
import json
import os
import re
import sys
import zipfile
import xml.etree.ElementTree as ET

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
WP = "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"
PIC = "http://schemas.openxmlformats.org/drawingml/2006/picture"
VML = "urn:schemas-microsoft-com:vml"
CP = "http://schemas.openxmlformats.org/package/2006/metadata/core-properties"
DC = "http://purl.org/dc/elements/1.1/"
PKG_REL = "http://schemas.openxmlformats.org/package/2006/relationships"

# Refuse parts larger than this after decompression: guards against zip bombs.
MAX_PART_BYTES = 40 * 1024 * 1024
# Page-size match tolerance in twips (1/1440 inch); Word rounds sizes by a few twips.
SIZE_TOLERANCE_TWIPS = 60
PAPERS = {"A4": (11906, 16838), "Letter": (12240, 15840), "Legal": (12240, 20160), "A3": (16838, 23811)}
TWIPS_PER_CM = 567.0  # 1440 twips per inch / 2.54 cm per inch = 566.93
CONTRACT_KEYS = {
    "title_required": bool, "author_required": bool, "max_heading_depth": int,
    "h1_min": int, "h1_max": int, "numbered_headings": bool, "heading_max_words": int,
    "allow_empty_sections": bool, "table_header_row": bool, "table_styles_allowed": list,
    "table_captions": bool, "figure_captions": bool, "alt_text": bool, "paper": str,
    "orientation": str, "margin_min_cm": (int, float), "footer_page_numbers": bool,
    "toc": bool, "no_placeholders": bool, "no_tracked_changes": bool,
}
NUMBERED_TEXT = re.compile(r"^\s*(\d+(\.\d+)*[.)]?|[A-Z][.)]|[IVXLC]+[.)])\s+\S")
CAPTION_TEXT = re.compile(r"^\s*(table|figure|fig\.|chart|exhibit|image)\s+[\dA-Z]+", re.I)
PLACEHOLDER_CI = re.compile(r"lorem ipsum|\[(insert|your|company|client|name|date|tbd|placeholder|needed)[^\]]*\]|\{\{[^}]*\}\}|<<[^>]*>>", re.I)
PLACEHOLDER_CS = re.compile(r"\b(TODO|TBD|FIXME|XXX+)\b")


def q(ns, tag):
    return "{%s}%s" % (ns, tag)


class InputError(Exception):
    pass


def read_part(zf, name, required=False):
    try:
        info = zf.getinfo(name)
    except KeyError:
        if required:
            raise InputError("not a Word document: missing part %s" % name)
        return None
    if info.file_size > MAX_PART_BYTES:
        raise InputError("part %s is larger than %d MB after decompression; refusing" % (name, MAX_PART_BYTES // 1048576))
    data = zf.read(name)
    if b"<!DOCTYPE" in data[:4096].upper():
        raise InputError("part %s declares a DOCTYPE; refusing to parse (not produced by a word processor)" % name)
    try:
        return ET.fromstring(data)
    except ET.ParseError as exc:
        raise InputError("part %s is not valid XML: %s" % (name, exc))


def find_main_part(zf):
    root = read_part(zf, "_rels/.rels")
    if root is not None:
        for rel in root.iter(q(PKG_REL, "Relationship")):
            if rel.get("Type", "").endswith("/officeDocument"):
                target = rel.get("Target", "").lstrip("/")
                return target if target.startswith("word/") or "/" in target else "word/" + target
    return "word/document.xml"


def load_styles(root):
    styles = {}
    if root is None:
        return styles
    for st in root.iter(q(W, "style")):
        sid = st.get(q(W, "styleId"))
        if not sid:
            continue
        name_el = st.find(q(W, "name"))
        based = st.find(q(W, "basedOn"))
        ppr = st.find(q(W, "pPr"))
        outline = None
        numbered = False
        if ppr is not None:
            ol = ppr.find(q(W, "outlineLvl"))
            if ol is not None and ol.get(q(W, "val"), "").isdigit():
                outline = int(ol.get(q(W, "val")))
            num = ppr.find(q(W, "numPr"))
            if num is not None:
                nid = num.find(q(W, "numId"))
                numbered = nid is not None and nid.get(q(W, "val")) not in (None, "0")
        styles[sid] = {
            "name": name_el.get(q(W, "val")) if name_el is not None else sid,
            "based": based.get(q(W, "val")) if based is not None else None,
            "outline": outline, "numbered": numbered, "type": st.get(q(W, "type")),
        }
    return styles


def style_name(styles, sid):
    if sid is None:
        return "Normal"
    return styles.get(sid, {}).get("name", sid)


def style_chain(styles, sid):
    seen = []
    while sid is not None and sid in styles and sid not in seen and len(seen) < 12:
        seen.append(sid)
        sid = styles[sid]["based"]
    return seen


def heading_level_from_name(name):
    low = name.strip().lower()
    if low == "title":
        return 0
    m = re.match(r"^heading\s*([1-9])$", low)
    return int(m.group(1)) if m else None


def paragraph_info(p, styles):
    ppr = p.find(q(W, "pPr"))
    sid = None
    own_outline = None
    own_num = None
    if ppr is not None:
        ps = ppr.find(q(W, "pStyle"))
        sid = ps.get(q(W, "val")) if ps is not None else None
        ol = ppr.find(q(W, "outlineLvl"))
        if ol is not None and ol.get(q(W, "val"), "").isdigit():
            own_outline = int(ol.get(q(W, "val")))
        num = ppr.find(q(W, "numPr"))
        if num is not None:
            nid = num.find(q(W, "numId"))
            own_num = nid is not None and nid.get(q(W, "val")) not in (None, "0")
    level = None
    numbered_style = False
    for link in style_chain(styles, sid):
        nm = styles[link]["name"]
        lv = heading_level_from_name(nm)
        if lv is not None and level is None:
            level = lv
        if level is None and styles[link]["outline"] is not None and styles[link]["outline"] < 9:
            level = styles[link]["outline"] + 1
        numbered_style = numbered_style or styles[link]["numbered"]
    if level is None and sid and sid not in styles:
        level = heading_level_from_name(re.sub(r"(?<=[a-zA-Z])(?=\d)", " ", sid))
    if own_outline is not None and own_outline < 9 and level is None:
        level = own_outline + 1
    texts = []
    for t in p.iter(q(W, "t")):
        texts.append(t.text or "")
    text = "".join(texts).strip()
    return {
        "style": style_name(styles, sid), "level": level, "text": text,
        "num": bool(own_num) if own_num is not None else numbered_style,
    }


def body_elements(body):
    out = []
    for child in list(body):
        tag = child.tag
        if tag == q(W, "p") or tag == q(W, "tbl"):
            out.append(child)
        elif tag == q(W, "sdt"):
            content = child.find(q(W, "sdtContent"))
            if content is not None:
                out.extend(body_elements(content))
    return out


def has_content(el):
    if el.tag == q(W, "tbl"):
        return True
    if any(True for _ in el.iter(q(WP, "docPr"))) or any(True for _ in el.iter(q(VML, "imagedata"))):
        return True
    return "".join(t.text or "" for t in el.iter(q(W, "t"))).strip() != ""


def truthy(el):
    if el is None:
        return False
    return el.get(q(W, "val"), "true").lower() not in ("0", "false", "off")


def caption_kind(info):
    low_style = info["style"].lower()
    m = CAPTION_TEXT.match(info["text"])
    is_cap = "caption" in low_style or bool(m)
    if not is_cap:
        return None
    first = m.group(1).lower() if m else ""
    if first == "table" or "table" in low_style:
        return "table"
    if first in ("figure", "fig.", "chart", "exhibit", "image") or "image" in low_style or "figure" in low_style:
        return "figure"
    return "any"


def inspect(path):
    try:
        zf = zipfile.ZipFile(path)
    except zipfile.BadZipFile:
        raise InputError("not a .docx file (not a zip archive; a legacy .doc must be converted to .docx first)")
    with zf:
        if "[Content_Types].xml" not in zf.namelist():
            raise InputError("not an Office Open XML package: [Content_Types].xml is missing")
        main = find_main_part(zf)
        doc = read_part(zf, main, required=True)
        styles = load_styles(read_part(zf, "word/styles.xml"))
        core = read_part(zf, "docProps/core.xml")
        footer_names = [n for n in zf.namelist() if re.match(r"^word/footer\d*\.xml$", n)]
        footers = [read_part(zf, n) for n in footer_names]

    body = doc.find(q(W, "body"))
    if body is None:
        raise InputError("document has no w:body")

    props = {"title": None, "author": None}
    if core is not None:
        t = core.find(q(DC, "title"))
        c = core.find(q(DC, "creator"))
        props["title"] = (t.text or "").strip() if t is not None else None
        props["author"] = (c.text or "").strip() if c is not None else None

    elems = body_elements(body)
    headings, tables, images, captions = [], [], [], []
    findings = []
    order = []  # ("h", idx) / ("c", None) for content / ("e", None) for empty paragraph
    infos = {}
    words = 0
    placeholders = []
    top_level_docpr = set()
    para_no = 0

    for idx, el in enumerate(elems):
        if el.tag == q(W, "p"):
            para_no += 1
            info = paragraph_info(el, styles)
            infos[idx] = info
            words += len(info["text"].split())
            for pat in (PLACEHOLDER_CI, PLACEHOLDER_CS):
                for m in pat.finditer(info["text"]):
                    placeholders.append({"element": idx, "text": info["text"][max(0, m.start() - 15):m.end() + 15]})
            for dp in el.iter(q(WP, "docPr")):
                top_level_docpr.add(id(dp))
            if info["level"] is not None:
                if info["level"] == 0:
                    order.append(("t", None))
                else:
                    numbered_text = bool(NUMBERED_TEXT.match(info["text"]))
                    headings.append({
                        "element": idx, "level": info["level"], "text": info["text"], "style": info["style"],
                        "numbered": info["num"] or numbered_text,
                        "numbering": "field" if info["num"] else ("text" if numbered_text else "none"),
                    })
                    order.append(("h", len(headings) - 1))
                    continue
            if has_content(el):
                order.append(("c", None))
        else:
            order.append(("c", None))

    # Title paragraph
    title_present = any(i["level"] == 0 for i in infos.values())

    # Headings: hierarchy problems
    prev = 0
    for n, h in enumerate(headings):
        if not h["text"]:
            findings.append({"code": "empty_heading", "severity": "warn", "detail": "a heading paragraph has no text (element %d)" % h["element"]})
        if n == 0 and h["level"] > 1:
            findings.append({"code": "first_heading_not_h1", "severity": "warn", "detail": "first heading is level %d: %r" % (h["level"], h["text"][:60])})
        elif h["level"] > prev + 1 and n > 0:
            findings.append({"code": "heading_level_skip", "severity": "warn", "detail": "level %d follows level %d at %r" % (h["level"], prev, h["text"][:60])})
        prev = h["level"]
    kinds = {h["numbered"] for h in headings}
    if len(kinds) > 1:
        findings.append({"code": "mixed_heading_numbering", "severity": "warn", "detail": "%d of %d headings are numbered" % (sum(1 for h in headings if h["numbered"]), len(headings))})

    # Empty sections: heading followed by a heading of same or higher rank, or by the end.
    empty_sections = []
    for pos, (kind, ref) in enumerate(order):
        if kind != "h":
            continue
        h = headings[ref]
        has_body = False
        for k2, r2 in order[pos + 1:]:
            if k2 == "c":
                has_body = True
                break
            if k2 == "h":
                has_body = headings[r2]["level"] > h["level"]
                break
            if k2 == "t":
                break
        if not has_body:
            empty_sections.append({"heading": h["text"], "level": h["level"]})
    for e in empty_sections:
        findings.append({"code": "empty_section", "severity": "warn", "detail": "heading %r has no content before the next heading of the same or higher level" % e["heading"][:60]})

    # Tables (top level) and captions
    def neighbours(i):
        res = []
        for j in (i - 1, i + 1):
            if 0 <= j < len(elems) and elems[j].tag == q(W, "p"):
                k = caption_kind(infos[j])
                if k:
                    res.append(k)
        return res

    nested = 0
    for idx, el in enumerate(elems):
        if el.tag != q(W, "tbl"):
            continue
        nested += sum(1 for _ in el.iter(q(W, "tbl"))) - 1
        rows = el.findall(q(W, "tr"))
        grid = el.find(q(W, "tblGrid"))
        cols = len(grid.findall(q(W, "gridCol"))) if grid is not None else (len(rows[0].findall(q(W, "tc"))) if rows else 0)
        tpr = el.find(q(W, "tblPr"))
        ts = tpr.find(q(W, "tblStyle")) if tpr is not None else None
        header = False
        if rows:
            trpr = rows[0].find(q(W, "trPr"))
            header = trpr is not None and truthy(trpr.find(q(W, "tblHeader")))
        cap = [k for k in neighbours(idx) if k in ("table", "any")]
        tables.append({
            "element": idx, "rows": len(rows), "cols": cols,
            "style": style_name(styles, ts.get(q(W, "val"))) if ts is not None else "Normal Table",
            "header_row": header, "caption": bool(cap),
        })
    for n, t in enumerate(tables, 1):
        if not t["header_row"]:
            findings.append({"code": "table_no_header_row", "severity": "warn", "detail": "table %d: first row is not marked as a repeating header row" % n})
        if not t["caption"]:
            findings.append({"code": "table_no_caption", "severity": "warn", "detail": "table %d has no caption paragraph directly before or after it" % n})

    # Images
    n_img = 0
    for cont in doc.iter():
        if cont.tag not in (q(WP, "inline"), q(WP, "anchor")):
            continue
        is_picture = any(True for e in cont.iter() if e.tag == q(PIC, "pic") or e.tag.endswith("}chart"))
        if not is_picture:
            continue
        dp = cont.find(q(WP, "docPr"))
        if dp is None:
            continue
        n_img += 1
        descr = (dp.get("descr") or "").strip()
        decorative = any(e.tag.endswith("}decorative") and e.get("val") in ("1", "true") for e in dp.iter())
        in_top = id(dp) in top_level_docpr
        cap_ok = None
        if in_top and not decorative:
            for idx, el in enumerate(elems):
                if el.tag == q(W, "p") and any(d is dp for d in el.iter(q(WP, "docPr"))):
                    cap_ok = any(k in ("figure", "any") for k in neighbours(idx))
                    break
        images.append({"index": n_img, "name": dp.get("name"), "alt": descr, "has_alt": bool(descr), "decorative": decorative, "caption": cap_ok, "kind": "inline" if cont.tag == q(WP, "inline") else "floating"})
    for shape in doc.iter(q(VML, "shape")):
        if shape.find(q(VML, "imagedata")) is not None:
            n_img += 1
            alt = (shape.get("alt") or "").strip()
            images.append({"index": n_img, "name": shape.get("id"), "alt": alt, "has_alt": bool(alt), "decorative": False, "caption": None, "kind": "legacy-vml"})
    for im in images:
        if not im["has_alt"] and not im["decorative"]:
            findings.append({"code": "image_no_alt", "severity": "warn", "detail": "image %d (%s) has no alt text and is not marked decorative" % (im["index"], im["name"])})
        if im["caption"] is False:
            findings.append({"code": "image_no_caption", "severity": "warn", "detail": "image %d has no caption paragraph directly before or after it" % im["index"]})

    # Captions list
    for idx, info in infos.items():
        k = caption_kind(info)
        if k:
            captions.append({"element": idx, "kind": k, "text": info["text"][:80]})

    # Fields
    def has_field(root, word):
        for it in root.iter(q(W, "instrText")):
            if re.search(r"\b%s\b" % word, it.text or ""):
                return True
        for fs in root.iter(q(W, "fldSimple")):
            if re.search(r"\b%s\b" % word, fs.get(q(W, "instr"), "")):
                return True
        return False

    toc = has_field(doc, "TOC")
    footer_page = any(f is not None and has_field(f, "PAGE") for f in footers)

    # Page setup, one entry per section
    sections = []
    for sp in doc.iter(q(W, "sectPr")):
        sz = sp.find(q(W, "pgSz"))
        mar = sp.find(q(W, "pgMar"))
        entry = {"width_cm": None, "height_cm": None, "paper": None, "orientation": None, "margins_cm": None}
        if sz is not None and (sz.get(q(W, "w")) or "").isdigit() and (sz.get(q(W, "h")) or "").isdigit():
            w, h = int(sz.get(q(W, "w"))), int(sz.get(q(W, "h")))
            entry["width_cm"], entry["height_cm"] = round(w / TWIPS_PER_CM, 1), round(h / TWIPS_PER_CM, 1)
            entry["orientation"] = "landscape" if w > h else "portrait"
            lo, hi = min(w, h), max(w, h)
            for pname, (pw, ph) in PAPERS.items():
                if abs(lo - pw) <= SIZE_TOLERANCE_TWIPS and abs(hi - ph) <= SIZE_TOLERANCE_TWIPS:
                    entry["paper"] = pname
                    break
            if entry["paper"] is None:
                entry["paper"] = "custom"
        if mar is not None:
            m = {}
            for side in ("top", "bottom", "left", "right"):
                v = mar.get(q(W, side))
                try:
                    m[side] = round(int(v) / TWIPS_PER_CM, 2) if v is not None else None
                except ValueError:
                    m[side] = None
            entry["margins_cm"] = m
        sections.append(entry)

    tracked = sum(1 for _ in doc.iter(q(W, "ins"))) + sum(1 for _ in doc.iter(q(W, "del")))
    if tracked:
        findings.append({"code": "tracked_changes", "severity": "warn", "detail": "%d tracked insertions/deletions remain" % tracked})
    if placeholders:
        findings.append({"code": "placeholder_text", "severity": "warn", "detail": "%d placeholder-looking strings, first: %r" % (len(placeholders), placeholders[0]["text"])})
    if not props["title"]:
        findings.append({"code": "no_title_property", "severity": "warn", "detail": "document property Title is empty"})
    if not props["author"]:
        findings.append({"code": "no_author_property", "severity": "warn", "detail": "document property Author is empty"})

    return {
        "properties": props,
        "title_paragraph": title_present,
        "words": words,
        "sections": sections,
        "headings": headings,
        "empty_sections": empty_sections,
        "tables": tables,
        "nested_tables": nested,
        "images": images,
        "captions": captions,
        "toc": toc,
        "footer_page_numbers": footer_page,
        "placeholders": placeholders,
        "tracked_changes": tracked,
        "findings": findings,
    }


def load_contract(path):
    try:
        with open(path, encoding="utf-8-sig") as fh:
            contract = json.load(fh)
    except OSError as exc:
        raise InputError("cannot read contract %s: %s" % (path, exc))
    except ValueError as exc:
        raise InputError("contract %s is not valid JSON: %s" % (path, exc))
    if not isinstance(contract, dict):
        raise InputError("contract must be a JSON object")
    for key, val in contract.items():
        if key not in CONTRACT_KEYS:
            raise InputError("unknown contract key %r; allowed: %s" % (key, ", ".join(sorted(CONTRACT_KEYS))))
        want = CONTRACT_KEYS[key]
        if isinstance(val, bool) and want is not bool:
            raise InputError("contract key %r must not be a boolean" % key)
        if not isinstance(val, want):
            raise InputError("contract key %r has the wrong type" % key)
    if "paper" in contract and contract["paper"] not in list(PAPERS) + ["any"]:
        raise InputError("contract paper must be one of %s or 'any'" % ", ".join(PAPERS))
    if "orientation" in contract and contract["orientation"] not in ("portrait", "landscape", "any"):
        raise InputError("contract orientation must be portrait, landscape or any")
    return contract


def check_contract(rep, c):
    v = []

    def fail(rule, detail):
        v.append({"rule": rule, "severity": "error", "detail": detail})

    props = rep["properties"]
    if c.get("title_required") and not props["title"]:
        fail("title_required", "document property Title is empty")
    if c.get("author_required") and not props["author"]:
        fail("author_required", "document property Author is empty")
    heads = rep["headings"]
    if "max_heading_depth" in c:
        deep = [h for h in heads if h["level"] > c["max_heading_depth"]]
        if deep:
            fail("max_heading_depth", "%d heading(s) deeper than level %d, first: %r" % (len(deep), c["max_heading_depth"], deep[0]["text"][:60]))
    n1 = sum(1 for h in heads if h["level"] == 1)
    if "h1_min" in c and n1 < c["h1_min"]:
        fail("h1_min", "%d Heading 1 paragraph(s), at least %d required" % (n1, c["h1_min"]))
    if "h1_max" in c and n1 > c["h1_max"]:
        fail("h1_max", "%d Heading 1 paragraph(s), at most %d allowed" % (n1, c["h1_max"]))
    if "numbered_headings" in c:
        bad = [h for h in heads if h["numbered"] != c["numbered_headings"]]
        if bad:
            fail("numbered_headings", "%d heading(s) %s numbered, first: %r" % (len(bad), "not" if c["numbered_headings"] else "wrongly", bad[0]["text"][:60]))
    if "heading_max_words" in c:
        long_ = [h for h in heads if len(h["text"].split()) > c["heading_max_words"]]
        if long_:
            fail("heading_max_words", "%d heading(s) longer than %d words, first: %r" % (len(long_), c["heading_max_words"], long_[0]["text"][:60]))
    if c.get("allow_empty_sections") is False and rep["empty_sections"]:
        fail("allow_empty_sections", "%d empty section(s), first: %r" % (len(rep["empty_sections"]), rep["empty_sections"][0]["heading"][:60]))
    if c.get("table_header_row"):
        bad = [i for i, t in enumerate(rep["tables"], 1) if not t["header_row"]]
        if bad:
            fail("table_header_row", "table(s) %s have no repeating header row" % bad)
    if "table_styles_allowed" in c:
        allowed = {s.lower() for s in c["table_styles_allowed"]}
        bad = [i for i, t in enumerate(rep["tables"], 1) if t["style"].lower() not in allowed]
        if bad:
            fail("table_styles_allowed", "table(s) %s use a style outside the allowed list %s" % (bad, c["table_styles_allowed"]))
    if c.get("table_captions"):
        bad = [i for i, t in enumerate(rep["tables"], 1) if not t["caption"]]
        if bad:
            fail("table_captions", "table(s) %s have no caption" % bad)
    if c.get("figure_captions"):
        bad = [i["index"] for i in rep["images"] if i["caption"] is False]
        if bad:
            fail("figure_captions", "image(s) %s have no caption" % bad)
    if c.get("alt_text"):
        bad = [i["index"] for i in rep["images"] if not i["has_alt"] and not i["decorative"]]
        if bad:
            fail("alt_text", "image(s) %s have no alt text" % bad)
    secs = rep["sections"]
    if "paper" in c and c["paper"] != "any":
        bad = [s["paper"] for s in secs if s["paper"] != c["paper"]]
        if bad or not secs:
            fail("paper", "page size is %s, contract wants %s" % (sorted(set(bad)) or "undeclared", c["paper"]))
    if "orientation" in c and c["orientation"] != "any":
        bad = [s["orientation"] for s in secs if s["orientation"] != c["orientation"]]
        if bad:
            fail("orientation", "orientation is %s, contract wants %s" % (sorted(set(map(str, bad))), c["orientation"]))
    if "margin_min_cm" in c:
        low = []
        for s in secs:
            for side, val in (s["margins_cm"] or {}).items():
                if val is not None and val < c["margin_min_cm"]:
                    low.append("%s=%s" % (side, val))
        if low:
            fail("margin_min_cm", "margins below %s cm: %s" % (c["margin_min_cm"], ", ".join(sorted(set(low)))))
    if c.get("footer_page_numbers") and not rep["footer_page_numbers"]:
        fail("footer_page_numbers", "no PAGE field found in any footer")
    if c.get("toc") and not rep["toc"]:
        fail("toc", "no TOC field found")
    if c.get("no_placeholders") and rep["placeholders"]:
        fail("no_placeholders", "%d placeholder string(s), first: %r" % (len(rep["placeholders"]), rep["placeholders"][0]["text"]))
    if c.get("no_tracked_changes") and rep["tracked_changes"]:
        fail("no_tracked_changes", "%d tracked change(s) remain" % rep["tracked_changes"])
    return v


def main(argv):
    path = None
    contract_path = None
    args = list(argv)
    while args:
        a = args.pop(0)
        if a == "--contract":
            if not args:
                sys.stderr.write("--contract needs a path\n")
                return 2
            contract_path = args.pop(0)
        elif path is None and not a.startswith("--"):
            path = a
        else:
            sys.stderr.write("usage: docx_inspect.py FILE.docx [--contract CONTRACT.json]\n")
            return 2
    if path is None:
        sys.stderr.write("usage: docx_inspect.py FILE.docx [--contract CONTRACT.json]\n")
        return 2
    try:
        if not os.path.isfile(path):
            raise InputError("file not found: %s" % path)
        contract = load_contract(contract_path) if contract_path else None
        rep = inspect(path)
    except InputError as exc:
        sys.stderr.write("error: %s\n" % exc)
        return 2
    violations = check_contract(rep, contract) if contract is not None else []
    out = {
        "schema_version": 1,
        "tool": "docx_inspect",
        "file": os.path.basename(path),
        "ok": not violations,
        "contract": None if contract is None else {"rules_checked": sorted(contract), "violations": violations},
    }
    out.update(rep)
    sys.stdout.write(json.dumps(out, indent=2, ensure_ascii=True, sort_keys=False) + "\n")
    return 1 if violations else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
