#!/usr/bin/env python3
"""Review image alternative text in HTML and Markdown files (standard library only).

Usage:
    python alt_text_review.py PATH [PATH ...] [--max-length N] [--described FILE.json]

PATH is a file or a directory. Directories are walked for .html .htm .xhtml
.md .markdown .mdx files (.git and node_modules are skipped).

What it reads: the given files, and the optional descriptions file.
What it writes: nothing on disk. The report is strict JSON on stdout, so there
is no output path and no way to overwrite an input.

It cannot see pixels. It checks the text around each image and the alt text the
author wrote. For images the user has described, --described validates the
alt text the user or agent proposes; it never invents a description.

Exit codes: 0 no findings, 1 at least one flag or failing proposal, 2 bad input.
"""
import argparse
import difflib
import json
import os
import re
import sys
from html.parser import HTMLParser

SCHEMA_VERSION = 1

# Working limit used by many editors and checkers; WCAG itself sets no number.
DEFAULT_MAX_LEN = 125

HTML_EXT = {".html", ".htm", ".xhtml"}
MD_EXT = {".md", ".markdown", ".mdx"}
SKIP_DIRS = {".git", "node_modules", "__pycache__"}

# Text after an image searched for evidence of a long description.
WINDOW_CHARS = 800
# A figure caption at least this long can carry the long description.
LONG_CAPTION_MIN = 60
# Alt and caption this similar (difflib ratio) count as a duplicate.
CAPTION_SIMILARITY = 0.85

FLAG_ORDER = [
    "missing_alt", "empty_alt_in_link", "title_without_alt", "filename_alt",
    "generic_alt", "redundant_prefix", "long_alt", "repeated_alt",
    "caption_duplicate", "decorative_candidate", "presentation_role_with_alt",
    "complex_no_long_description",
]
FLAG_TEXT = {
    "missing_alt": "no alt attribute; add alt with text, or alt=\"\" if the image is decorative",
    "empty_alt_in_link": "image is the only content of a link or button and its alt is empty, so the link has no name",
    "title_without_alt": "title is set but alt is missing or empty; title is not a substitute for alt",
    "filename_alt": "alt looks like a file name or camera name, not a description",
    "generic_alt": "alt is a placeholder word such as image or photo and says nothing about this image",
    "redundant_prefix": "alt starts with image of, picture of or similar; screen readers already announce an image",
    "long_alt": "alt is longer than the limit; keep a short alt and move detail to visible text or a long description",
    "repeated_alt": "the same alt text is used for different images on this page",
    "caption_duplicate": "alt repeats the adjacent caption; use alt=\"\" or add only what the caption lacks",
    "decorative_candidate": "name, size or role suggests a decorative image that has non-empty alt; confirm and use alt=\"\"",
    "presentation_role_with_alt": "role=presentation or aria-hidden is set but alt has text; the two contradict each other",
    "complex_no_long_description": "chart, graph or diagram with no sign of a long description or data table nearby",
}

# Alt values that name a kind of thing, not this image.
GENERIC_ALTS = {
    "image", "images", "photo", "photograph", "picture", "pic", "graphic", "graphics",
    "icon", "img", "thumbnail", "thumb", "banner", "logo", "placeholder", "untitled",
    "screenshot", "figure", "illustration", "alt", "alt text", "spacer", "null",
    "undefined", "todo", "image placeholder", "no alt", "chart", "graph", "diagram",
    "flowchart", "flow", "infographic", "map", "diagram image",
}
FILENAME_RE = re.compile(r"\.(png|jpe?g|gif|webp|svg|avif|bmp|tiff?|heic)\b", re.I)
CAMERA_RE = re.compile(r"^(img|dsc|dscn|dscf|pxl|mvimg|screenshot|screen ?shot|image|photo|pic|untitled)[ _\-]?\(?\d{2,}", re.I)
HASH_RE = re.compile(r"^[0-9a-f]{12,}$", re.I)
PREFIX_RE = re.compile(
    r"^(an? |the )?(image|picture|photo|photograph|graphic|icon|pic)\b( of| showing| depicting| for| that shows)"
    r"|^(image|picture|photo|graphic)\s*:", re.I)

# Words in a file name or class that suggest the image is decoration only.
DECORATIVE_TOKENS = {
    "spacer", "divider", "separator", "bullet", "decoration", "decorative", "ornament",
    "border", "shadow", "background", "bg", "pixel", "flourish", "hr", "swoosh", "sprite", "1x1",
}
# Words that suggest data or structure that alt text cannot carry.
COMPLEX_TOKENS = {
    "chart", "graph", "diagram", "infographic", "flowchart", "timeline", "schematic",
    "plot", "dashboard", "heatmap", "orgchart", "map",
}
# Words that suggest the image contains readable text.
TEXT_TOKENS = {"logo", "banner", "badge", "quote", "headline", "poster", "signage", "screenshot"}

LONGDESC_RE = re.compile(
    r"long description|full description|text (alternative|description|version)|data table"
    r"|described (below|in|at)|description of|see (the )?(table|transcript|data)|transcript"
    r"|accessible (table|version)", re.I)
DYNAMIC_RE = re.compile(r"\{\{|\{%|<%|\$\{|<\?php")
ROLE_WORDS_RE = re.compile(r"^(link|click|button|go to|image)\b", re.I)

FUNCTIONS = ("informative", "decorative", "functional", "complex", "text_in_image")


def norm(s):
    """Lowercase, drop punctuation, collapse spaces, for comparisons."""
    s = re.sub(r"[^\w\s]", " ", s.casefold())
    return re.sub(r"\s+", " ", s).strip()


def tokens(s):
    return set(re.findall(r"[a-z0-9]+", s.casefold()))


def base_of(src):
    if not src:
        return ""
    return os.path.basename(src.split("?")[0].split("#")[0])


def alt_checks(alt, src, max_len):
    """Flags that depend only on the alt text itself and the file name."""
    if alt is None or alt.strip() == "" or DYNAMIC_RE.search(alt):
        return []
    a = alt.strip()
    n = norm(a)
    base = base_of(src)
    stem = os.path.splitext(base)[0]
    flags = []
    if (FILENAME_RE.search(a) or CAMERA_RE.match(a) or HASH_RE.match(re.sub(r"[\s\-]", "", a))
            or (base and a.casefold() == base.casefold()) or (stem and n and norm(stem) == n)):
        flags.append("filename_alt")
    elif n in GENERIC_ALTS:
        flags.append("generic_alt")
    elif PREFIX_RE.match(a):
        flags.append("redundant_prefix")
    if len(a) > max_len:
        flags.append("long_alt")
    return flags


def strip_tags(s):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]*>", " ", s)).strip()


class PageParser(HTMLParser):
    """Collects images and the context needed to judge them."""

    def __init__(self, text):
        super().__init__(convert_charrefs=True)
        self.text = text
        self.starts = [0]
        for m in re.finditer("\n", text):
            self.starts.append(m.end())
        self.images = []
        self.ids = set()
        self.heading = ""
        self._skip = 0
        self._links = []
        self._figures = []
        self._in_caption = 0
        self._heading_buf = None

    def _offset(self):
        line, col = self.getpos()
        return self.starts[line - 1] + col

    def handle_starttag(self, tag, attrs):
        d = {k.lower(): (v if v is not None else "") for k, v in attrs}
        if "id" in d:
            self.ids.add(d["id"])
        if tag in ("script", "style"):
            self._skip += 1
        elif tag in ("a", "button"):
            self._links.append({"text": [], "label": bool(d.get("aria-label") or d.get("aria-labelledby")), "imgs": []})
        elif tag == "figure":
            self._figures.append({"caption": []})
        elif tag == "figcaption":
            self._in_caption += 1
        elif tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
            self._heading_buf = []
        elif tag in ("img", "area", "input"):
            self._image(tag, d)

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)

    def _image(self, tag, d):
        if tag == "input" and d.get("type", "").lower() != "image":
            return
        if tag == "area" and "href" not in d:
            return
        line, _ = self.getpos()
        raw = self.get_starttag_text() or ""
        end = self._offset() + len(raw)
        img = {
            "line": line, "kind": tag, "end": end,
            "src": d.get("src") if tag != "area" else d.get("href"),
            "alt": d["alt"] if "alt" in d else None,
            "title": d.get("title"), "role": d.get("role", "").lower(),
            "aria_hidden": d.get("aria-hidden", "").lower() == "true",
            "describedby": d.get("aria-describedby", ""), "longdesc": d.get("longdesc", ""),
            "width": d.get("width", ""), "height": d.get("height", ""), "cls": d.get("class", ""),
            "in_link": bool(self._links) or tag in ("area", "input"),
            "in_figure": bool(self._figures), "figure": self._figures[-1] if self._figures else None,
            "heading": self.heading, "link_named": None,
        }
        if self._links:
            self._links[-1]["imgs"].append(img)
        self.images.append(img)

    def handle_endtag(self, tag):
        if tag in ("script", "style") and self._skip:
            self._skip -= 1
        elif tag in ("a", "button") and self._links:
            link = self._links.pop()
            named = bool("".join(link["text"]).strip()) or link["label"] or any(
                (i["alt"] or "").strip() for i in link["imgs"])
            for i in link["imgs"]:
                i["link_named"] = named
        elif tag == "figure" and self._figures:
            self._figures.pop()
        elif tag == "figcaption" and self._in_caption:
            self._in_caption -= 1
        elif tag in ("h1", "h2", "h3", "h4", "h5", "h6") and self._heading_buf is not None:
            self.heading = re.sub(r"\s+", " ", "".join(self._heading_buf)).strip()
            self._heading_buf = None

    def handle_data(self, data):
        if self._skip:
            return
        if self._links:
            self._links[-1]["text"].append(data)
        if self._in_caption and self._figures:
            self._figures[-1]["caption"].append(data)
        if self._heading_buf is not None:
            self._heading_buf.append(data)


def mask_markdown_code(text):
    """Blank out fenced code and inline code, keeping line breaks and offsets."""
    out = []
    fence = None
    for line in text.split("\n"):
        stripped = line.lstrip()
        if fence is None and (stripped.startswith("```") or stripped.startswith("~~~")):
            fence = stripped[:3]
            out.append(" " * len(line))
        elif fence is not None:
            if stripped.startswith(fence):
                fence = None
            out.append(" " * len(line))
        else:
            out.append(re.sub(r"(`+)(.+?)\1", lambda m: " " * len(m.group(0)), line))
    return "\n".join(out)


MD_IMG_RE = re.compile(
    r"!\[((?:[^\[\]\\]|\\.|\[[^\[\]]*\])*)\]\(\s*(<[^>]*>|[^\s)]*)"
    r"(?:\s+(?:\"([^\"]*)\"|'([^']*)'|\(([^)]*)\)))?\s*\)")
MD_REF_IMG_RE = re.compile(r"!\[((?:[^\[\]\\]|\\.)*)\]\[([^\]]*)\]")
MD_REF_DEF_RE = re.compile(r"^ {0,3}\[([^\]]+)\]:\s*<?(\S+?)>?(?:\s+\"([^\"]*)\")?\s*$", re.M)
MD_HEADING_RE = re.compile(r"^ {0,3}#{1,6}\s+(.+?)\s*#*\s*$")


def parse_markdown_images(masked):
    lines = masked.split("\n")
    defs = {m.group(1).casefold(): m.group(2) for m in MD_REF_DEF_RE.finditer(masked)}
    headings = []
    for i, ln in enumerate(lines, 1):
        h = MD_HEADING_RE.match(ln)
        if h:
            headings.append((i, h.group(1)))
    found = []
    for m in list(MD_IMG_RE.finditer(masked)) + list(MD_REF_IMG_RE.finditer(masked)):
        if m.re is MD_IMG_RE:
            alt, src = m.group(1), m.group(2).strip("<>")
            title = m.group(3) or m.group(4) or m.group(5)
        else:
            alt = m.group(1)
            label = (m.group(2) or alt).casefold()
            src, title = defs.get(label, "[" + label + "]"), None
        line_no = masked.count("\n", 0, m.start()) + 1
        line = lines[line_no - 1]
        col = m.start() - (masked.rfind("\n", 0, m.start()) + 1)
        before = re.search(r"\[([^\[\]]*)$", line[:col])
        after = re.match(r"([^\]\n]*)\]\(|([^\]\n]*)\]\[", line[col + len(m.group(0)):])
        in_link = bool(before and after)
        other_text = ""
        if in_link:
            other_text = (before.group(1) + (after.group(1) or after.group(2) or "")).strip()
        heading = ""
        for ln_no, text in headings:
            if ln_no <= line_no:
                heading = text
        nxt = ""
        alone = line.strip() == m.group(0).strip()
        if alone:
            for j in range(line_no, min(line_no + 2, len(lines))):
                if lines[j].strip():
                    cand = lines[j].strip()
                    # Only emphasised or labelled lines count as captions, not ordinary paragraphs.
                    if re.match(r"^[>\s]*(\*|_|figure\s*\d|fig\.?\s*\d|caption:|source:)", cand, re.I):
                        nxt = cand
                    break
        found.append({
            "line": line_no, "kind": "markdown", "end": m.end(), "src": src, "alt": alt, "title": title,
            "role": "", "aria_hidden": False, "describedby": "", "longdesc": "", "width": "", "height": "",
            "cls": "", "in_link": in_link and not other_text,
            "in_figure": False, "figure": None, "heading": heading, "link_named": not (in_link and not other_text),
            "md_next_line": nxt,
        })
    return found


def caption_text(img):
    if img.get("figure") is not None:
        return re.sub(r"\s+", " ", "".join(img["figure"]["caption"])).strip()
    nxt = img.get("md_next_line", "")
    nxt = re.sub(r"^[>*_\s]+|[*_\s]+$", "", nxt)
    nxt = re.sub(r"^(figure|fig\.?)\s*\d+\s*[:.\-]\s*", "", nxt, flags=re.I)
    return nxt


def similar(a, b):
    na, nb = norm(a), norm(b)
    if not na or not nb:
        return False
    return na == nb or difflib.SequenceMatcher(None, na, nb).ratio() >= CAPTION_SIMILARITY


def guess_function(img, alt, base, alt_dynamic):
    toks = tokens(os.path.splitext(base)[0]) | tokens(img["cls"])
    if img["in_link"] or img["kind"] in ("area", "input"):
        return "functional"
    if (alt is not None and alt.strip() == "") or toks & DECORATIVE_TOKENS or img["role"] in ("presentation", "none"):
        return "decorative"
    if (toks | (set() if alt_dynamic else tokens(alt or ""))) & COMPLEX_TOKENS:
        return "complex"
    if toks & TEXT_TOKENS:
        return "text_in_image"
    return "informative"


def has_long_description(img, text, ids):
    if img["longdesc"]:
        return True
    if img["describedby"] and any(i in ids for i in img["describedby"].split()):
        return True
    if len(caption_text(img)) >= LONG_CAPTION_MIN:
        return True
    window = text[img["end"]:img["end"] + WINDOW_CHARS]
    return bool(re.search(r"<details", window, re.I) or LONGDESC_RE.search(strip_tags(window)))


def analyze_file(path, max_len):
    with open(path, "rb") as fh:
        raw = fh.read()
    text = raw.decode("utf-8-sig", errors="replace")
    ext = os.path.splitext(path)[1].lower()
    is_md = ext in MD_EXT
    if is_md:
        text = mask_markdown_code(text)
    parser = PageParser(text)
    parser.feed(text)
    parser.close()
    images = list(parser.images)
    if is_md:
        images.extend(parse_markdown_images(text))
        for im in parser.images:
            if not im["heading"]:
                hs = [h for h in re.finditer(r"^ {0,3}#{1,6}\s+(.+?)\s*#*\s*$", text, re.M)
                      if text.count("\n", 0, h.start()) + 1 <= im["line"]]
                im["heading"] = hs[-1].group(1) if hs else ""
    images.sort(key=lambda i: (i["line"], i["end"]))

    results = []
    for img in images:
        alt = img["alt"]
        src = img["src"] or ""
        base = base_of(src)
        dynamic = alt is not None and bool(DYNAMIC_RE.search(alt))
        flags = []
        if alt is None:
            flags.append("missing_alt")
        if img["in_link"] and alt is not None and alt.strip() == "" and img["link_named"] is False:
            flags.append("empty_alt_in_link")
        if img["title"] and (alt is None or alt.strip() == ""):
            flags.append("title_without_alt")
        flags.extend(alt_checks(alt, src, max_len))
        if alt and alt.strip() and not dynamic:
            cap = caption_text(img)
            if cap and similar(alt, cap):
                flags.append("caption_duplicate")
        toks = tokens(os.path.splitext(base)[0]) | tokens(img["cls"])
        tiny = img["width"].isdigit() and img["height"].isdigit() and int(img["width"]) <= 2 and int(img["height"]) <= 2
        has_text = alt is not None and alt.strip() != ""
        if has_text and (toks & DECORATIVE_TOKENS or tiny):
            flags.append("decorative_candidate")
        if has_text and (img["role"] in ("presentation", "none") or img["aria_hidden"]):
            flags.append("presentation_role_with_alt")
        function = guess_function(img, alt, base, dynamic)
        if function == "complex" and not has_long_description(img, text, parser.ids):
            flags.append("complex_no_long_description")
        results.append({
            "file": path, "line": img["line"], "kind": img["kind"], "src": src, "alt": alt,
            "title": img["title"], "dynamic_alt": dynamic,
            "context": {"heading": img["heading"], "in_link": img["in_link"], "in_figure": img["in_figure"],
                        "caption": caption_text(img)[:120]},
            "function_guess": function, "flags": flags, "detail": {},
            "needs_user_description": False, "ask": "", "described": False, "proposal_alt": None,
        })

    groups = {}
    for r in results:
        if r["alt"] and r["alt"].strip() and not r["dynamic_alt"]:
            groups.setdefault(norm(r["alt"]), set()).add(r["src"])
    for r in results:
        if r["alt"] and r["alt"].strip() and not r["dynamic_alt"] and len(groups.get(norm(r["alt"]), ())) > 1:
            r["flags"].append("repeated_alt")
    return results


def finish_image(r):
    r["flags"] = sorted(set(r["flags"]), key=FLAG_ORDER.index)
    r["detail"] = {f: FLAG_TEXT[f] for f in r["flags"]}
    if r["described"]:
        return
    flags = set(r["flags"])
    if flags:
        r["needs_user_description"] = True
        if flags & {"decorative_candidate", "presentation_role_with_alt"}:
            r["ask"] = "Is this image purely decorative? If yes, alt should be empty."
        elif "complex_no_long_description" in flags:
            r["ask"] = "What data or structure does this show, and where should the long description live?"
        elif "empty_alt_in_link" in flags:
            r["ask"] = "Where does this link go, or what does the button do?"
        else:
            r["ask"] = "What does this image show, and why is it on this page?"
    elif r["function_guess"] == "decorative" and r["alt"] is not None and r["alt"].strip() == "":
        toks = tokens(os.path.splitext(base_of(r["src"]))[0])
        if not toks & DECORATIVE_TOKENS:
            r["needs_user_description"] = True
            r["ask"] = "alt is empty, which says decorative. Confirm the image adds no information."


def check_proposal(entry, max_len):
    """Validate one proposed alt against the rule for its declared function."""
    func = entry["function"]
    alt = entry.get("alt")
    alt = "" if alt is None else alt
    flags = []
    if func == "decorative":
        if alt.strip():
            flags.append("alt_on_decorative")
    else:
        if not alt.strip():
            if func == "text_in_image" and entry.get("text_also_on_page") is True:
                pass
            else:
                flags.append("empty_alt_for_" + func)
        flags.extend(alt_checks(alt, entry.get("src", ""), max_len))
    if func == "functional" and alt.strip() and ROLE_WORDS_RE.match(alt.strip()):
        flags.append("functional_alt_names_role_or_picture")
    if func == "complex" and not str(entry.get("long_description_location", "")).strip():
        flags.append("complex_without_long_description")
    if func == "text_in_image" and alt.strip():
        exact = str(entry.get("text", "")).strip()
        if not exact:
            flags.append("text_field_missing")
        elif re.sub(r"\s+", " ", alt.strip()).casefold() != re.sub(r"\s+", " ", exact).casefold():
            flags.append("text_not_verbatim")
    return flags


def load_described(path):
    try:
        with open(path, "rb") as fh:
            data = json.loads(fh.read().decode("utf-8-sig"))
    except (OSError, ValueError) as exc:
        raise ValueError("cannot read descriptions file %s: %s" % (path, exc))
    items = data.get("images") if isinstance(data, dict) else None
    if not isinstance(items, list):
        raise ValueError("descriptions file must be an object with an images list")
    for i, e in enumerate(items):
        if not isinstance(e, dict) or not isinstance(e.get("src"), str) or not e["src"]:
            raise ValueError("images[%d] needs a non-empty src string" % i)
        if e.get("function") not in FUNCTIONS:
            raise ValueError("images[%d].function must be one of %s" % (i, ", ".join(FUNCTIONS)))
        if e.get("alt") is not None and not isinstance(e["alt"], str):
            raise ValueError("images[%d].alt must be a string" % i)
    return items


def collect_files(paths):
    files = []
    for p in paths:
        if os.path.isdir(p):
            for root, dirs, names in os.walk(p):
                dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS)
                for n in sorted(names):
                    if os.path.splitext(n)[1].lower() in HTML_EXT | MD_EXT:
                        files.append(os.path.join(root, n))
        elif os.path.isfile(p):
            files.append(p)
        else:
            raise ValueError("path not found: %s" % p)
    return files


def main(argv=None):
    ap = argparse.ArgumentParser(description="Review image alt text in HTML and Markdown (read-only).")
    ap.add_argument("paths", nargs="+")
    ap.add_argument("--max-length", type=int, default=DEFAULT_MAX_LEN)
    ap.add_argument("--described", help="JSON file describing images the user has explained")
    args = ap.parse_args(argv)
    try:
        if args.max_length < 1:
            raise ValueError("--max-length must be at least 1")
        files = collect_files(args.paths)
        described = load_described(args.described) if args.described else []
        images = []
        for f in files:
            images.extend(analyze_file(f, args.max_length))
    except ValueError as exc:
        sys.stderr.write("error: %s\n" % exc)
        return 2
    except OSError as exc:
        sys.stderr.write("error: cannot read input: %s\n" % exc)
        return 2

    proposals, matched = [], set()
    for idx, entry in enumerate(described):
        hits = [r for r in images if r["src"] == entry["src"] or (r["src"] and base_of(r["src"]) == base_of(entry["src"]))]
        pflags = check_proposal(entry, args.max_length)
        for r in hits:
            r["described"] = True
            r["proposal_alt"] = entry.get("alt") or ""
            matched.add(idx)
        proposals.append({
            "src": entry["src"], "function": entry["function"], "alt": entry.get("alt") or "",
            "length": len(entry.get("alt") or ""), "matched_images": len(hits),
            "flags": pflags, "ok": not pflags,
        })
    for r in images:
        finish_image(r)

    counts = {}
    for r in images:
        for f in r["flags"]:
            counts[f] = counts.get(f, 0) + 1
    unmatched = [e["src"] for i, e in enumerate(described) if i not in matched]
    failing = [p for p in proposals if not p["ok"]]
    report = {
        "schema_version": SCHEMA_VERSION,
        "tool": "alt_text_review",
        "max_alt_length": args.max_length,
        "files_scanned": len(files),
        "images_total": len(images),
        "images_flagged": sum(1 for r in images if r["flags"]),
        "needs_user_description": sum(1 for r in images if r["needs_user_description"]),
        "counts_by_flag": dict(sorted(counts.items())),
        "images": images,
        "proposals": proposals,
        "unmatched_descriptions": unmatched,
        "verdict": "findings" if (counts or failing) else "clean",
        "not_checked": "Pixels, whether alt matches the real image, SVG and CSS background images, and live pages.",
    }
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    sys.stdout.write(json.dumps(report, indent=2, ensure_ascii=True) + "\n")
    return 1 if (counts or failing) else 0


if __name__ == "__main__":
    sys.exit(main())
