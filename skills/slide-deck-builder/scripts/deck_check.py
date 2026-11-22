#!/usr/bin/env python3
"""Check a slide deck outline or an existing .pptx against the deck contract.

Usage:
    python deck_check.py <file.md|file.json|file.pptx> [--max-lines N] [--max-words N]

Input formats (chosen by extension):
    .md .markdown .txt  Markdown outline, slides separated by a line holding only ---
    .json               {"slides": [...]} or a bare list of slide objects
    .pptx               an existing PowerPoint file (read with zipfile + xml, no PowerPoint needed)

Reads the one file it is given and prints one JSON object to stdout. Writes nothing,
uses no network, runs no other program.

Exit codes: 0 no errors (warnings may exist), 1 at least one error finding,
2 unreadable or malformed input, or bad arguments (a plain message goes to stderr).

Markdown slide syntax understood (see references/outline-format.md in the skill):
    # Headline                first heading line of the slide
    - body line               any other non-empty line counts as one body line
    Chart: what it shows      one chart (also: an image whose alt text or path says chart, graph or plot)
    Source: publisher, period a chart needs one on the same slide
    Notes: speaker notes      to the end of the slide (a <!-- comment --> is also read as notes)
    ![alt text](file.png)     image; empty alt text is a finding
A slide whose headline starts with "Appendix" begins the appendix; every later slide is appendix.
"""
import json
import posixpath
import re
import sys
import zipfile
import xml.etree.ElementTree as ET

# Thresholds. Each has a reason; the skill text states the same numbers.
MAX_LINES = 6            # a slide read in a few seconds: more than six lines is a document, not a slide
MAX_WORDS = 50           # about six short lines; past this the audience reads instead of listens
APPENDIX_MAX_LINES = 12  # appendix is reference material, allowed to be denser
APPENDIX_MAX_WORDS = 120
MAX_HEADLINE_WORDS = 15  # a takeaway that needs more than two lines of title is two takeaways
MIN_NOTES_WORDS = 25     # under this the notes are a label, not something a person can speak from
MAX_NOTES_WORDS = 220    # about 100 seconds at 130 words a minute; longer notes get read aloud
BODY_FONT_PT = 18        # smallest comfortable body size for a projected 16:9 slide
MIN_FONT_PT = 12         # nothing smaller, not even a source line
MAX_ZIP_MEMBER = 20 * 1024 * 1024  # refuse to expand any single part past 20 MB
MAX_SLIDES = 500

P_NS = "http://schemas.openxmlformats.org/presentationml/2006/main"
A_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"
R_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"

# Headline verb heuristic: a takeaway has a verb. This is a word list, not grammar.
TOPIC_LABELS = {
    "overview", "agenda", "summary", "executive summary", "introduction", "intro", "background",
    "results", "findings", "next steps", "q&a", "questions", "thank you", "thanks", "contents",
    "conclusion", "conclusions", "recap", "context", "timeline", "roadmap", "team", "about us",
    "recommendations", "discussion", "contact", "references", "objectives", "goals",
}
AUXILIARIES = {
    "is", "are", "was", "were", "be", "been", "being", "has", "have", "had", "will", "would", "can", "could",
    "should", "must", "may", "might", "does", "do", "did", "isn't", "aren't", "won't", "can't", "don't",
    "doesn't", "didn't", "cannot", "shall",
}
BASE_VERBS = (
    "grow rise fall drop cut double triple halve reduce lift boost lose win gain save spend earn miss beat hit "
    "reach cross shrink expand slow stall stop start begin end finish deliver ship build buy sell hire fire "
    "cause create make take give get keep let need want require allow enable prevent avoid "
    "fix solve break fail succeed serve trail outperform exceed replace remove add "
    "show prove mean suggest indicate depend rely matter justify pay owe choose pick approve decide "
    "stay remain become turn bring put see find know think believe expect help ask tell improve "
    "pause cancel delay accelerate unlock convert retain attract merge split "
    "secure recover rebuild simplify automate outgrow undercut punish ignore"
).split()
IRREGULAR_PAST = (
    "grew grown rose risen fell fallen lost won spent met built bought sold drove driven made took taken gave "
    "given got kept left brought saw seen found knew known thought chose chosen became ran led paid broke broken "
    "shrank shrunk stood held said felt began begun hit cut put let set"
).split()
NOT_VERB_ED = {"speed", "embed", "seed", "feed", "weed", "breed", "need"}


def _forms(base):
    out = {base, base + "s", base + "es", base + "ing"}
    if base.endswith("e"):
        out.update({base + "d", base[:-1] + "ing"})
    if base.endswith("y"):
        out.add(base[:-1] + "ies")
        out.add(base[:-1] + "ied")
    return out


VERB_WORDS = set(AUXILIARIES) | set(IRREGULAR_PAST)
for _b in BASE_VERBS:
    VERB_WORDS |= _forms(_b)
# "-ing" forms alone read as topics ("Marketing overview"), so drop them from the verb set
VERB_WORDS = {w for w in VERB_WORDS if not w.endswith("ing") or w in AUXILIARIES}


def words_of(text):
    return re.findall(r"[A-Za-z0-9][A-Za-z0-9'%$.,&/+-]*", text)


def has_verb(headline):
    for tok in re.findall(r"[a-z]+(?:'[a-z]+)?", headline.lower()):
        if tok in VERB_WORDS:
            return True
        if re.search(r"'(re|ve|ll|d)$", tok):
            return True
        if tok.endswith("ed") and len(tok) >= 5 and tok not in NOT_VERB_ED:
            return True
    return False


def is_topic_label(headline):
    norm = re.sub(r"[^a-z& ]+", " ", headline.lower())
    norm = re.sub(r"\s+", " ", norm).strip()
    norm = re.sub(r"^appendix\s*[a-z]?\s*", "", norm).strip()
    return norm in TOPIC_LABELS


# ---------------------------------------------------------------- Markdown outline

FENCE = re.compile(r"^\s*(```|~~~)")
SEPARATOR = re.compile(r"^\s*---\s*$")
HEADING = re.compile(r"^\s{0,3}#{1,3}\s+(.*?)\s*#*\s*$")
NOTES_LINE = re.compile(r"^\s*(?:speaker\s+)?notes?\s*:\s*(.*)$", re.I)
SOURCE_LINE = re.compile(r"^\s*(?:[-*]\s+)?sources?\s*:\s*(.*)$", re.I)
CHART_LINE = re.compile(r"^\s*(?:[-*]\s+)?chart\s*:\s*(.*)$", re.I)
IMAGE_LINE = re.compile(r"^\s*!\[(.*?)\]\((.*?)\)\s*$")
TABLE_RULE = re.compile(r"^\s*\|?\s*:?-{2,}:?\s*(\|\s*:?-{2,}:?\s*)*\|?\s*$")
COMMENT = re.compile(r"<!--(.*?)-->", re.S)
DIRECTIVE = re.compile(r"^\s*_?(class|backgroundcolor|color|paginate|header|footer|theme|style|size|backgroundimage|marp)\s*:", re.I)
CHART_WORD = re.compile(r"chart|graph|plot", re.I)


def strip_front_matter(lines):
    i = 0
    while i < len(lines) and not lines[i].strip():
        i += 1
    if i < len(lines) and SEPARATOR.match(lines[i]):
        for j in range(i + 1, len(lines)):
            if SEPARATOR.match(lines[j]):
                block = [l for l in lines[i + 1:j] if l.strip()]
                if block and all(re.match(r"^[\w-]+\s*:", l) for l in block):
                    return lines[j + 1:]
                break
    return lines


def split_slides(lines):
    chunks, cur, in_fence = [], [], False
    for line in lines:
        if FENCE.match(line):
            in_fence = not in_fence
        if not in_fence and SEPARATOR.match(line):
            chunks.append(cur)
            cur = []
        else:
            cur.append(line)
    chunks.append(cur)
    return [c for c in chunks if any(l.strip() for l in c)]


def parse_markdown_slide(chunk):
    text = "\n".join(chunk)
    notes_parts = []

    def take_comment(m):
        inner = m.group(1).strip()
        if inner and not DIRECTIVE.match(inner):
            notes_parts.append(re.sub(r"^\s*(?:speaker\s+)?notes?\s*:\s*", "", inner, flags=re.I))
        return ""

    text = COMMENT.sub(take_comment, text)
    headline, body, charts, images = "", [], [], []
    source_texts = []
    in_notes, in_fence = False, False
    for line in text.split("\n"):
        if in_notes:
            notes_parts.append(line)
            continue
        if FENCE.match(line):
            in_fence = not in_fence
            continue
        if in_fence:
            if line.strip():
                body.append(line.strip())
            continue
        if not line.strip():
            continue
        m = NOTES_LINE.match(line)
        if m:
            in_notes = True
            if m.group(1).strip():
                notes_parts.append(m.group(1))
            continue
        m = HEADING.match(line)
        if m and not headline:
            headline = m.group(1)
            continue
        m = SOURCE_LINE.match(line)
        if m:
            if m.group(1).strip():
                source_texts.append(m.group(1).strip())
            continue
        m = CHART_LINE.match(line)
        if m:
            charts.append({"description": m.group(1).strip()})
            continue
        m = IMAGE_LINE.match(line)
        if m:
            alt, path = m.group(1).strip(), m.group(2)
            images.append({"alt": alt})
            if CHART_WORD.search(alt) or CHART_WORD.search(path):
                charts.append({"description": alt})
            continue
        if TABLE_RULE.match(line):
            continue
        body.append(line.strip())
    # a Source: line anywhere on the slide covers every chart on it
    for c in charts:
        c["source"] = source_texts[0] if source_texts else ""
    return {"headline": headline, "body": body, "notes": "\n".join(notes_parts).strip(),
            "charts": charts, "images": images}


def read_markdown(text):
    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    lines = strip_front_matter(lines)
    return [parse_markdown_slide(c) for c in split_slides(lines)]


# ---------------------------------------------------------------- JSON outline

def as_text_list(value, where):
    if value is None:
        return []
    if isinstance(value, str):
        return [l.strip() for l in value.split("\n") if l.strip()]
    if isinstance(value, list) and all(isinstance(v, str) for v in value):
        return [v.strip() for v in value if v.strip()]
    raise ValueError(f"{where} must be a string or a list of strings")


def read_json(text):
    data = json.loads(text)
    items = data.get("slides") if isinstance(data, dict) else data
    if not isinstance(items, list):
        raise ValueError('JSON must be a list of slides or an object with a "slides" list')
    slides = []
    for n, s in enumerate(items, 1):
        if not isinstance(s, dict):
            raise ValueError(f"slide {n} must be an object")
        headline = s.get("headline", s.get("title", ""))
        if not isinstance(headline, str):
            raise ValueError(f"slide {n}: headline must be a string")
        notes = s.get("notes", "")
        if not isinstance(notes, str):
            raise ValueError(f"slide {n}: notes must be a string")
        charts = []
        for c in s.get("charts", []) or []:
            if not isinstance(c, dict):
                raise ValueError(f"slide {n}: each chart must be an object")
            src = c.get("source", "")
            desc = c.get("description", c.get("alt", ""))
            charts.append({"description": str(desc or ""), "source": src.strip() if isinstance(src, str) else ""})
        images = []
        for im in s.get("images", []) or []:
            if not isinstance(im, dict):
                raise ValueError(f"slide {n}: each image must be an object")
            alt = im.get("alt", "")
            images.append({"alt": alt.strip() if isinstance(alt, str) else ""})
        slides.append({"headline": headline.strip(), "body": as_text_list(s.get("body"), f"slide {n} body"),
                       "notes": notes.strip(), "charts": charts, "images": images,
                       "appendix": bool(s.get("appendix", False))})
    return slides


# ---------------------------------------------------------------- PPTX

def q(ns, tag):
    return "{%s}%s" % (ns, tag)


def read_part(zf, name):
    try:
        info = zf.getinfo(name)
    except KeyError:
        return None
    if info.file_size > MAX_ZIP_MEMBER:
        raise ValueError(f"part {name} is larger than {MAX_ZIP_MEMBER // (1024 * 1024)} MB, refusing to read it")
    data = zf.read(name)
    head = data[:4096].upper()
    if b"<!DOCTYPE" in head or b"<!ENTITY" in head:
        raise ValueError(f"part {name} declares a DTD or entity, refusing to parse it")
    return data


def parse_xml(zf, name):
    data = read_part(zf, name)
    if data is None:
        return None
    try:
        return ET.fromstring(data)
    except ET.ParseError as exc:
        raise ValueError(f"part {name} is not valid XML: {exc}")


def read_rels(zf, part):
    folder, base = posixpath.split(part)
    root = parse_xml(zf, posixpath.join(folder, "_rels", base + ".rels"))
    rels = {}
    if root is not None:
        for rel in root.findall(q(REL_NS, "Relationship")):
            target = rel.get("Target", "")
            if rel.get("TargetMode") == "External":
                continue
            full = target.lstrip("/") if target.startswith("/") else posixpath.normpath(posixpath.join(folder, target))
            rels[rel.get("Id")] = (rel.get("Type", ""), full)
    return rels


def para_text(p):
    return "".join(t.text or "" for t in p.iter(q(A_NS, "t"))).strip()


def placeholder_type(sp):
    ph = sp.find("./%s/%s/%s" % (q(P_NS, "nvSpPr"), q(P_NS, "nvPr"), q(P_NS, "ph")))
    if ph is None:
        return None
    return ph.get("type") or "body"


def read_pptx_slide(zf, slide_part):
    root = parse_xml(zf, slide_part)
    if root is None:
        raise ValueError(f"slide part {slide_part} is missing")
    title_parts, body, sizes = [], [], []
    source_present = False
    for sp in root.iter(q(P_NS, "sp")):
        ptype = placeholder_type(sp)
        if ptype in ("sldNum", "ftr", "dt"):
            continue
        for p in sp.iter(q(A_NS, "p")):
            txt = para_text(p)
            if not txt:
                continue
            if ptype in ("title", "ctrTitle"):
                title_parts.append(txt)
                continue
            is_source = bool(re.match(r"^\s*sources?\s*:", txt, re.I))
            source_present = source_present or (is_source and len(txt) > 8)
            if not is_source:
                body.append(txt)
            for r in p.iter(q(A_NS, "rPr")):
                if r.get("sz", "").isdigit():
                    sizes.append((int(r.get("sz")) / 100.0, is_source))
    for gf in root.iter(q(P_NS, "graphicFrame")):
        for p in gf.iter(q(A_NS, "p")):
            txt = para_text(p)
            if txt:
                body.append(txt)
    charts, images = [], []
    for gf in root.iter(q(P_NS, "graphicFrame")):
        gd = gf.find(".//" + q(A_NS, "graphicData"))
        if gd is not None and (gd.get("uri") or "").endswith("/chart"):
            charts.append({"description": "", "source": ""})
    for pic in root.iter(q(P_NS, "pic")):
        c = pic.find("./%s/%s" % (q(P_NS, "nvPicPr"), q(P_NS, "cNvPr")))
        alt = (c.get("descr") if c is not None else "") or ""
        name = (c.get("name") if c is not None else "") or ""
        images.append({"alt": alt.strip()})
        if CHART_WORD.search(alt) or CHART_WORD.search(name):
            charts.append({"description": alt.strip(), "source": ""})
    for c in charts:
        c["source"] = "present" if source_present else ""
    rels = read_rels(zf, slide_part)
    notes_text = ""
    for typ, target in rels.values():
        if typ.endswith("/notesSlide"):
            nroot = parse_xml(zf, target)
            if nroot is not None:
                parts = []
                for sp in nroot.iter(q(P_NS, "sp")):
                    if placeholder_type(sp) == "body":
                        parts.extend(t for t in (para_text(p) for p in sp.iter(q(A_NS, "p"))) if t)
                notes_text = "\n".join(parts)
    return {"headline": " ".join(title_parts).strip(), "body": body, "notes": notes_text.strip(),
            "charts": charts, "images": images, "font_sizes": sizes}


def read_pptx(path):
    try:
        zf = zipfile.ZipFile(path)
    except zipfile.BadZipFile:
        raise ValueError("file is not a valid .pptx (not a zip archive)")
    with zf:
        pres = parse_xml(zf, "ppt/presentation.xml")
        if pres is None:
            raise ValueError("ppt/presentation.xml not found: not a PowerPoint presentation")
        rels = read_rels(zf, "ppt/presentation.xml")
        lst = pres.find(q(P_NS, "sldIdLst"))
        ids = [] if lst is None else [e.get(q(R_NS, "id")) for e in lst.findall(q(P_NS, "sldId"))]
        if len(ids) > MAX_SLIDES:
            raise ValueError(f"more than {MAX_SLIDES} slides, refusing to read")
        slides = []
        for rid in ids:
            if rid not in rels:
                raise ValueError(f"slide relationship {rid} has no target")
            slides.append(read_pptx_slide(zf, rels[rid][1]))
        return slides


# ---------------------------------------------------------------- checks

def check(slides, max_lines, max_words, fmt):
    findings, summary = [], []
    appendix_from = None
    seen = {}
    for n, s in enumerate(slides, 1):
        head = s["headline"]
        if appendix_from is None and (head.lower().startswith("appendix") or s.get("appendix")):
            appendix_from = n
        in_appx = appendix_from is not None
        lines = len(s["body"])
        wcount = sum(len(words_of(l)) for l in s["body"])
        notes_words = len(words_of(s["notes"]))
        divider = lines == 0 and not s["charts"] and not s["images"]

        def add(sev, rule, msg):
            findings.append({"slide": n, "severity": sev, "rule": rule, "message": msg})

        if not head:
            add("error", "no-headline", "slide has no headline" + (" (no title placeholder)" if fmt == "pptx" else ""))
        else:
            key = re.sub(r"[^a-z0-9]+", " ", re.sub(r"\(cont\.?\)|\bcontinued\b", "", head.lower())).strip()
            if key in seen:
                add("error", "duplicate-headline", f"same headline as slide {seen[key]}: '{head}'")
            else:
                seen[key] = n
            if len(words_of(head)) > MAX_HEADLINE_WORDS:
                add("warning", "headline-long", f"headline has {len(words_of(head))} words, limit {MAX_HEADLINE_WORDS}")
            exempt = divider or (n == 1 and lines <= 2) or in_appx
            if not exempt and (is_topic_label(head) or not has_verb(head)):
                add("warning", "headline-topic", f"headline looks like a topic, not a takeaway: '{head}'")
        lim_l, lim_w = (APPENDIX_MAX_LINES, APPENDIX_MAX_WORDS) if in_appx else (max_lines, max_words)
        if lines > lim_l:
            add("error", "too-many-lines", f"{lines} body lines, limit {lim_l}")
        if wcount > lim_w:
            add("error", "too-many-words", f"{wcount} body words, limit {lim_w}")
        if not in_appx and not divider:
            if notes_words == 0:
                add("error", "missing-notes", "no speaker notes")
            elif notes_words < MIN_NOTES_WORDS:
                add("warning", "notes-thin", f"notes have {notes_words} words, under {MIN_NOTES_WORDS}")
        if notes_words > MAX_NOTES_WORDS:
            add("warning", "notes-long", f"notes have {notes_words} words, over {MAX_NOTES_WORDS}")
        if len(s["charts"]) > 1:
            add("error", "multiple-charts", f"{len(s['charts'])} charts on one slide, limit 1")
        for c in s["charts"]:
            if not c.get("source"):
                add("error", "chart-no-source", "chart has no stated source")
        missing_alt = sum(1 for im in s["images"] if not im["alt"])
        if missing_alt:
            add("error", "image-no-alt", f"{missing_alt} image(s) without a description")
        sizes = s.get("font_sizes") or []
        if sizes:
            if any(pt < MIN_FONT_PT for pt, _ in sizes):
                add("error", "font-too-small", f"text set below {MIN_FONT_PT} pt (smallest {min(p for p, _ in sizes):g} pt)")
            elif any(pt < BODY_FONT_PT and not src for pt, src in sizes):
                add("warning", "font-below-body-size",
                    f"body text set below {BODY_FONT_PT} pt (smallest {min(p for p, src in sizes if not src):g} pt)")
        entry = {"slide": n, "headline": head, "body_lines": lines, "body_words": wcount,
                 "has_notes": notes_words > 0, "notes_words": notes_words,
                 "charts": len(s["charts"]), "images": len(s["images"]), "appendix": in_appx}
        if sizes:
            entry["min_font_pt"] = min(p for p, _ in sizes)
        summary.append(entry)
    return summary, findings, appendix_from


def build_report(path, slides, fmt, max_lines, max_words):
    summary, findings, appx = check(slides, max_lines, max_words, fmt)
    if not slides:
        findings.append({"slide": 0, "severity": "error", "rule": "empty-deck", "message": "no slides found"})
    errors = sum(1 for f in findings if f["severity"] == "error")
    warnings = len(findings) - errors
    return {
        "file": path, "format": fmt, "slide_count": len(slides), "appendix_starts_at": appx,
        "limits": {"max_lines": max_lines, "max_words": max_words},
        "slides": summary, "findings": findings,
        "counts": {"error": errors, "warning": warnings}, "ok": errors == 0,
    }


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    max_lines, max_words, path = MAX_LINES, MAX_WORDS, None
    i = 0
    try:
        while i < len(argv):
            a = argv[i]
            if a == "--max-lines":
                max_lines = int(argv[i + 1]); i += 2
            elif a == "--max-words":
                max_words = int(argv[i + 1]); i += 2
            elif a.startswith("-") and path is None and a != "-":
                raise ValueError(f"unknown option {a}")
            elif path is None:
                path = a; i += 1
            else:
                raise ValueError("only one input file is accepted")
    except (IndexError, ValueError) as exc:
        sys.stderr.write(f"deck_check: {exc}\nusage: deck_check.py <file.md|file.json|file.pptx> [--max-lines N] [--max-words N]\n")
        return 2
    if path is None:
        sys.stderr.write("deck_check: no input file\nusage: deck_check.py <file.md|file.json|file.pptx> [--max-lines N] [--max-words N]\n")
        return 2
    ext = path.lower().rsplit(".", 1)[-1] if "." in path else ""
    try:
        if ext == "pptx":
            fmt, slides = "pptx", read_pptx(path)
        else:
            with open(path, "rb") as fh:
                raw = fh.read()
            if not raw.strip():
                raise ValueError("file is empty")
            text = raw.decode("utf-8-sig")
            if ext == "json":
                fmt, slides = "json", read_json(text)
            elif ext in ("md", "markdown", "txt"):
                fmt, slides = "markdown", read_markdown(text)
            else:
                raise ValueError("unsupported extension; use .md, .markdown, .txt, .json or .pptx")
    except OSError as exc:
        sys.stderr.write(f"deck_check: cannot read {path}: {exc.strerror or exc}\n")
        return 2
    except UnicodeDecodeError:
        sys.stderr.write(f"deck_check: {path} is not valid UTF-8 text\n")
        return 2
    except (ValueError, json.JSONDecodeError) as exc:
        sys.stderr.write(f"deck_check: {exc}\n")
        return 2
    report = build_report(path, slides, fmt, max_lines, max_words)
    sys.stdout.write(json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False) + "\n")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass
    sys.exit(main())
