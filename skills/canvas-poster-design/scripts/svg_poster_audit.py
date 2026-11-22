#!/usr/bin/env python3
"""Audit a poster, flyer or social graphic written as one SVG file.

    python svg_poster_audit.py FILE.svg [--safe N] [--bleed N] [--min-text-pct P]

Reads FILE.svg only; writes nothing; no network. Prints ONE JSON object on
stdout. Exit codes: 0 = no FAIL finding (WARN allowed), 1 = at least one FAIL,
2 = the file is missing, empty or not parseable SVG (JSON with "error").

Units: every size is in the SVG user units of the viewBox. Thresholds are
relative to the short side of the viewBox so the audit works for pixels,
millimetres or points alike.

What it checks: viewBox, title, text sizes against a type scale, WCAG contrast
of each text fill against the rect behind it (hex, rgb() and a few names only),
and elements that cross the safe area. Text widths are ESTIMATED from character
counts, so safe-area results on text are an approximation (see "limits").
"""
import json
import re
import sys
import xml.etree.ElementTree as ET

DEFAULT_SAFE_PCT = 5.0       # safe margin, % of short side: the usual social-platform crop guard
DEFAULT_MIN_TEXT_PCT = 1.8   # smallest readable text, % of short side (about 19 px on a 1080 canvas)
MAX_DISTINCT_SIZES = 4       # more sizes than this reads as no scale at all
MIN_STEP_RATIO = 1.25        # neighbouring sizes closer than this look like a mistake, not a choice
MIN_HEADLINE_RATIO = 2.5     # headline vs smallest text: below this the hierarchy is weak
MAX_TEXT_ELEMENTS = 10       # more text blocks than this stops being a poster
CONTRAST_NORMAL = 4.5        # WCAG AA, normal text
CONTRAST_LARGE = 3.0         # WCAG AA, large text
LARGE_PX = 24.0              # WCAG large text: 24 px, or 18.66 px when bold (px on a 96 dpi canvas)
LARGE_BOLD_PX = 18.66
CHAR_WIDTH = 0.55            # average glyph width as a fraction of font size (estimate)
CHAR_WIDTH_BOLD = 0.60
BG_COVER = 0.95              # a rect covering this share of the canvas counts as the background
USAGE = "usage: svg_poster_audit.py FILE.svg [--safe N] [--bleed N] [--min-text-pct P]"
NAMED = {"white": (255, 255, 255), "black": (0, 0, 0), "red": (255, 0, 0), "blue": (0, 0, 255),
         "yellow": (255, 255, 0), "gray": (128, 128, 128), "grey": (128, 128, 128)}
SKIP_TAGS = ("defs", "clipPath", "mask", "symbol", "pattern", "marker", "title", "desc", "metadata")


def local(tag):
    return tag.rsplit("}", 1)[-1] if isinstance(tag, str) else ""


def num(value):
    """Leading number of a string such as '12.5px', or None."""
    m = re.match(r"\s*(-?\d*\.?\d+(?:e-?\d+)?)", value or "")
    return float(m.group(1)) if m else None


def parse_style(el):
    out = {}
    for part in (el.get("style") or "").split(";"):
        if ":" in part:
            k, v = part.split(":", 1)
            out[k.strip()] = v.strip()
    return out


def prop(el, name):
    style = parse_style(el)
    return style[name] if name in style else el.get(name)


def parse_color(value):
    """Return (r, g, b) or None when the colour cannot be resolved."""
    if not value:
        return None
    v = value.strip().lower()
    if v in NAMED:
        return NAMED[v]
    m = re.fullmatch(r"#([0-9a-f]{3})", v)
    if m:
        return tuple(int(c * 2, 16) for c in m.group(1))
    m = re.fullmatch(r"#([0-9a-f]{6})", v)
    if m:
        h = m.group(1)
        return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    m = re.fullmatch(r"rgb\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)", v)
    if m:
        return tuple(min(255, int(x)) for x in m.groups())
    return None


def luminance(rgb):
    def lin(c):
        c /= 255.0
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (lin(c) for c in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a, b):
    la, lb = luminance(a), luminance(b)
    return (max(la, lb) + 0.05) / (min(la, lb) + 0.05)


def hexof(rgb):
    return "#%02X%02X%02X" % rgb


def error_exit(msg):
    print(json.dumps({"tool": "svg_poster_audit", "error": msg}, indent=2))
    return 2


class Ctx:
    def __init__(self):
        self.findings = []
        self.unsupported = set()
        self.has_sheet = False

    def add(self, severity, check, message, element=None):
        item = {"severity": severity, "check": check, "message": message}
        if element:
            item["element"] = element
        self.findings.append(item)


def translate_of(el, ctx):
    t = el.get("transform")
    if not t:
        return 0.0, 0.0
    m = re.fullmatch(r"\s*translate\(\s*(-?[\d.]+)[\s,]*(-?[\d.]+)?\s*\)\s*", t)
    if m:
        return float(m.group(1)), float(m.group(2) or 0)
    ctx.unsupported.add("transform other than translate (scale, rotate, matrix, skew) is ignored: safe-area boxes and sizes of transformed elements may be wrong")
    return 0.0, 0.0


def size_of(raw, ctx):
    n = num(raw)
    if n is None:
        return None
    raw = raw.strip()
    if raw.endswith("pt"):
        ctx.unsupported.add("font-size in pt assumed to be on a 96 dpi canvas (x 1.3333)")
        return n * 96.0 / 72.0
    if re.search(r"(em|%|rem)$", raw):
        return None
    return n


def text_lines(el, inh, dx, dy, order, ctx):
    base_size = prop(el, "font-size") or inh.get("font-size")
    weight = prop(el, "font-weight") or inh.get("font-weight") or "400"
    fill = prop(el, "fill") or inh.get("fill") or "black"
    x0, y0 = (num(el.get("x")) or 0.0) + dx, (num(el.get("y")) or 0.0) + dy
    anchor = prop(el, "text-anchor") or "start"
    spans = [c for c in el if local(c.tag) == "tspan"]
    placed = [s for s in spans if s.get("x") is not None or s.get("y") is not None or s.get("dy") is not None]
    lines = []
    if placed:
        y = y0
        if (el.text or "").strip():
            lines.append((el.text.strip(), x0, y, base_size, fill, weight, anchor))
        for s in spans:
            if s.get("y") is not None:
                y = (num(s.get("y")) or 0.0) + dy
            elif s.get("dy") is not None:
                y += num(s.get("dy")) or 0.0
            x = (num(s.get("x")) + dx) if s.get("x") is not None else x0
            lines.append(("".join(s.itertext()).strip(), x, y, prop(s, "font-size") or base_size,
                          prop(s, "fill") or fill, prop(s, "font-weight") or weight,
                          prop(s, "text-anchor") or anchor))
    else:
        size = base_size
        sizes = [prop(s, "font-size") for s in spans if prop(s, "font-size")]
        if sizes:
            best = max(sizes, key=lambda v: num(v) or 0)
            if (num(best) or 0) > (num(base_size) or 0):
                size = best
        lines.append(("".join(el.itertext()).strip(), x0, y0, size, fill, weight, anchor))
    out = []
    for content, x, y, raw_size, f, w, a in lines:
        if not content:
            continue
        out.append({"order": order, "text": content, "x": x, "y": y,
                    "size": size_of(raw_size, ctx) if raw_size else None, "fill": f,
                    "bold": w.strip().lower() in ("bold", "bolder") or (num(w) or 400) >= 600,
                    "anchor": a})
    return out


def collect(root, ctx):
    """Walk the tree; return shapes and text lines in document order."""
    rects, texts = [], []
    counter = [0]

    def walk(el, inh, dx, dy):
        tag = local(el.tag)
        tx, ty = translate_of(el, ctx)
        dx, dy = dx + tx, dy + ty
        inh = dict(inh)
        if el.get("class") and ctx.has_sheet:
            inh["css_class"] = True
        for key in ("fill", "font-size", "font-weight"):
            v = prop(el, key)
            if v is not None:
                inh[key] = v
        counter[0] += 1
        order = counter[0]
        if tag in SKIP_TAGS:
            return
        if tag == "style":
            ctx.unsupported.add("<style> sheets (classes are not resolved; text or backgrounds styled by a class get contrast status unknown)")
            return
        if tag == "use":
            ctx.unsupported.add("<use> instances are not measured")
        if tag == "rect":
            w, h = num(el.get("width")), num(el.get("height"))
            x, y = num(el.get("x")) or 0.0, num(el.get("y")) or 0.0
            if w and h:
                fill = prop(el, "fill")
                classed = bool(el.get("class")) and ctx.has_sheet and "fill" not in parse_style(el)
                rects.append({"order": order, "box": (x + dx, y + dy, x + dx + w, y + dy + h),
                              "classed": classed,
                              "fill": fill if fill is not None else "black",
                              "opacity": prop(el, "fill-opacity") or prop(el, "opacity"),
                              "id": el.get("id"), "shape": "rect"})
            return
        if tag in ("circle", "ellipse"):
            cx, cy = num(el.get("cx")) or 0.0, num(el.get("cy")) or 0.0
            rx = num(el.get("r")) if tag == "circle" else num(el.get("rx"))
            ry = rx if tag == "circle" else num(el.get("ry"))
            if rx and ry:
                rects.append({"order": order, "box": (cx + dx - rx, cy + dy - ry, cx + dx + rx, cy + dy + ry),
                              "fill": None, "opacity": None, "id": el.get("id"), "shape": tag})
            return
        if tag == "text":
            made = text_lines(el, inh, dx, dy, order, ctx)
            classed = bool(inh.get("css_class")) and "fill" not in parse_style(el)
            for item in made:
                item["classed"] = classed
            texts.extend(made)
            return
        for child in el:
            walk(child, inh, dx, dy)

    walk(root, {}, 0.0, 0.0)
    return rects, texts


def text_box(t):
    size = t["size"] or 0.0
    width = len(t["text"]) * size * (CHAR_WIDTH_BOLD if t["bold"] else CHAR_WIDTH)
    x = t["x"]
    if t["anchor"] == "middle":
        x -= width / 2
    elif t["anchor"] == "end":
        x -= width
    return (x, t["y"] - size * 0.8, x + width, t["y"] + size * 0.2)


def parse_args(args):
    opts = {"--safe": None, "--bleed": 0.0, "--min-text-pct": DEFAULT_MIN_TEXT_PCT}
    path = None
    i = 0
    while i < len(args):
        a = args[i]
        if a in opts:
            if i + 1 >= len(args) or num(args[i + 1]) is None:
                return None, None, "%s needs a number. %s" % (a, USAGE)
            opts[a] = num(args[i + 1])
            i += 2
        elif a.startswith("--") or path is not None:
            return None, None, USAGE
        else:
            path = a
            i += 1
    if path is None:
        return None, None, USAGE
    return path, opts, None


def main(argv):
    path, opts, problem = parse_args(list(argv))
    if problem:
        return error_exit(problem)
    try:
        with open(path, "rb") as fh:
            data = fh.read()
    except OSError as exc:
        return error_exit("cannot read %s: %s" % (path, exc.strerror))
    if not data.strip():
        return error_exit("%s is empty" % path)
    try:
        root = ET.fromstring(data)
    except ET.ParseError as exc:
        return error_exit("not valid XML/SVG: %s" % exc)
    if local(root.tag) != "svg":
        return error_exit("root element is <%s>, not <svg>" % local(root.tag))

    ctx = Ctx()
    ctx.has_sheet = any(local(e.tag) == "style" for e in root.iter())
    vb = [num(p) for p in re.split(r"[\s,]+", (root.get("viewBox") or "").strip()) if p != ""]
    canvas = None
    if len(vb) == 4 and None not in vb and vb[2] > 0 and vb[3] > 0:
        canvas = vb
    else:
        ctx.add("fail", "viewbox-missing", "no valid viewBox; set viewBox=\"0 0 W H\" so the graphic scales and can be audited")
        w, h = num(root.get("width")), num(root.get("height"))
        if w and h:
            canvas = [0.0, 0.0, w, h]
    report = {"tool": "svg_poster_audit", "file": path, "canvas": None, "title": None, "text": None,
              "contrast": [], "outside_safe_area": [], "findings": ctx.findings, "limits": []}
    if canvas is None:
        ctx.add("fail", "canvas-unknown", "no viewBox and no width/height; nothing further can be measured")
        report["verdict"] = "fail"
        print(json.dumps(report, indent=2))
        return 1
    cw, ch = canvas[2], canvas[3]
    short = min(cw, ch)
    bleed = opts["--bleed"] or 0.0
    safe = opts["--safe"] if opts["--safe"] is not None else round(short * DEFAULT_SAFE_PCT / 100.0, 3)
    inset = bleed + safe
    sw, sh = num(root.get("width")), num(root.get("height"))
    report["canvas"] = {"viewBox": canvas, "width_attr": root.get("width"), "height_attr": root.get("height"),
                        "short_side": short, "aspect": round(cw / ch, 4), "bleed": bleed,
                        "safe_margin": safe, "safe_inset_from_edge": inset}
    if sw and sh and abs(sw / sh - cw / ch) > 0.01:
        ctx.add("warn", "aspect-mismatch", "width/height ratio %.3f differs from viewBox ratio %.3f; the graphic will letterbox" % (sw / sh, cw / ch))

    title = next((c for c in root if local(c.tag) == "title"), None)
    title_text = "".join(title.itertext()).strip() if title is not None else ""
    report["title"] = title_text or None
    if not title_text:
        ctx.add("fail", "title-missing", "no <title> as a direct child of <svg>; add one that names the poster for screen readers and search")

    rects, texts = collect(root, ctx)
    bg = None
    for r in rects:
        b = r["box"]
        ox = min(b[2], canvas[0] + cw) - max(b[0], canvas[0])
        oy = min(b[3], canvas[1] + ch) - max(b[1], canvas[1])
        if r["fill"] is not None and ox > 0 and oy > 0 and ox * oy / (cw * ch) >= BG_COVER:
            bg = r
            break
    if bleed > 0 and bg is None:
        ctx.add("fail", "bleed-background", "bleed is set but no full-canvas background rect exists; the colour must run to every viewBox edge")
    elif bleed > 0:
        b = bg["box"]
        if b[0] > canvas[0] + 0.01 or b[1] > canvas[1] + 0.01 or b[2] < canvas[0] + cw - 0.01 or b[3] < canvas[1] + ch - 0.01:
            ctx.add("fail", "bleed-background", "background rect does not reach every viewBox edge, so trimming can expose white paper")

    sized = [t for t in texts if t["size"]]
    for t in texts:
        if not t["size"]:
            ctx.add("warn", "size-unresolved", "font-size missing or in em/%/rem; cannot be checked", t["text"][:40])
    min_size = round(short * opts["--min-text-pct"] / 100.0, 2)
    distinct = sorted({round(t["size"], 2) for t in sized}, reverse=True)
    report["text"] = {"count": len(texts), "sizes_distinct": distinct, "min_allowed": min_size,
                      "largest": distinct[0] if distinct else None,
                      "elements": [{"text": t["text"][:60], "size": round(t["size"], 2), "fill": t["fill"]} for t in sized]}
    if not texts:
        ctx.add("warn", "no-text", "no text elements found; if text was converted to outlines it cannot be audited")
    if len(texts) > MAX_TEXT_ELEMENTS:
        ctx.add("warn", "text-count-high", "%d text blocks; more than %d usually means no single focus" % (len(texts), MAX_TEXT_ELEMENTS))
    for t in sized:
        if t["size"] < min_size:
            ctx.add("fail", "text-too-small", "size %.1f is below %.1f (%.1f%% of the short side)" % (t["size"], min_size, opts["--min-text-pct"]), t["text"][:40])
    if len(distinct) > MAX_DISTINCT_SIZES:
        ctx.add("warn", "too-many-sizes", "%d distinct sizes %s; use at most %d" % (len(distinct), distinct, MAX_DISTINCT_SIZES))
    for big, small in zip(distinct, distinct[1:]):
        if big / small < MIN_STEP_RATIO:
            ctx.add("warn", "sizes-too-close", "sizes %s and %s differ by x%.2f; step by at least x%.2f or merge them" % (big, small, big / small, MIN_STEP_RATIO))
    if distinct:
        n_top = sum(1 for t in sized if round(t["size"], 2) == distinct[0])
        if n_top > 1 and len(sized) > 1:
            ctx.add("warn", "headline-not-unique", "%d text elements share the largest size %s; a poster needs one headline" % (n_top, distinct[0]))
        if len(distinct) > 1 and distinct[0] / distinct[-1] < MIN_HEADLINE_RATIO:
            ctx.add("warn", "weak-hierarchy", "largest/smallest is x%.2f; headline should be at least x%.1f the smallest text" % (distinct[0] / distinct[-1], MIN_HEADLINE_RATIO))

    for t in sized:
        box = text_box(t)
        cx, cy = (box[0] + box[2]) / 2, (box[1] + box[3]) / 2
        behind = None
        for r in rects:
            if r["order"] < t["order"] and r["fill"] is not None and r["box"][0] <= cx <= r["box"][2] and r["box"][1] <= cy <= r["box"][3]:
                behind = r
        fg = parse_color(t["fill"])
        css_unknown = t.get("classed") or (behind is not None and behind.get("classed"))
        entry = {"text": t["text"][:40], "size": round(t["size"], 2), "foreground": t["fill"]}
        if behind is None:
            bgc = (255, 255, 255)
            entry["background"] = "white (assumed: no rect behind the text)"
            ctx.add("warn", "background-assumed", "no rect behind this text; white assumed. Put a background rect first in the file", t["text"][:40])
        else:
            bgc = parse_color(behind["fill"])
            entry["background"] = behind["fill"]
            if behind["opacity"] not in (None, "1", "1.0"):
                bgc = None
                entry["note"] = "background rect has opacity; blend not computed"
        if css_unknown:
            entry["ratio"] = None
            entry["status"] = "unknown"
            entry["note"] = "a CSS class may set the text or background colour; the fill read from the attributes is not trusted"
            ctx.add("warn", "css-class-unresolved", "contrast: unknown. A <style> sheet and a class apply here and are not resolved; no pass is claimed. Use plain fill attributes or check by hand", t["text"][:40])
        elif fg is None or bgc is None:
            entry["ratio"] = None
            entry["status"] = "unresolved"
            ctx.add("warn", "contrast-unresolved", "colour is a gradient, pattern, opacity or unsupported form; check contrast by hand", t["text"][:40])
        else:
            ratio = contrast(fg, bgc)
            large = t["size"] >= LARGE_PX or (t["bold"] and t["size"] >= LARGE_BOLD_PX)
            need = CONTRAST_LARGE if large else CONTRAST_NORMAL
            entry.update({"ratio": round(ratio, 2), "required": need, "large_text": large,
                          "foreground_hex": hexof(fg), "background_hex": hexof(bgc),
                          "status": "pass" if ratio >= need else "fail"})
            if ratio < need:
                ctx.add("fail", "contrast", "%.2f:1 is below %.1f:1 (%s on %s)" % (ratio, need, hexof(fg), hexof(bgc)), t["text"][:40])
        report["contrast"].append(entry)

    lo_x, lo_y = canvas[0] + inset, canvas[1] + inset
    hi_x, hi_y = canvas[0] + cw - inset, canvas[1] + ch - inset
    safe_box = [round(v, 1) for v in (lo_x, lo_y, hi_x, hi_y)]
    for t in sized:
        b = text_box(t)
        if b[0] < lo_x or b[1] < lo_y or b[2] > hi_x or b[3] > hi_y:
            rb = [round(v, 1) for v in b]
            report["outside_safe_area"].append({"kind": "text", "text": t["text"][:40], "box": rb})
            ctx.add("fail", "outside-safe-area", "estimated text box %s crosses the safe area %s" % (rb, safe_box), t["text"][:40])
    for r in rects:
        if r is bg:
            continue
        b = r["box"]
        if (b[2] - b[0]) * (b[3] - b[1]) >= BG_COVER * cw * ch:
            continue
        if b[0] < lo_x - 0.01 or b[1] < lo_y - 0.01 or b[2] > hi_x + 0.01 or b[3] > hi_y + 0.01:
            report["outside_safe_area"].append({"kind": r["shape"], "id": r.get("id"), "box": [round(v, 1) for v in b]})
            ctx.add("warn", "shape-outside-safe-area", "%s crosses the safe area; fine for a deliberate full-bleed panel, wrong for a button or badge" % r["shape"], r.get("id"))

    report["limits"] = sorted(ctx.unsupported) + [
        "text widths are estimated at %.2f x font size per character" % CHAR_WIDTH,
        "paths, images and text converted to outlines are not measured"]
    report["summary"] = {"fail": sum(f["severity"] == "fail" for f in ctx.findings),
                         "warn": sum(f["severity"] == "warn" for f in ctx.findings)}
    report["verdict"] = "fail" if report["summary"]["fail"] else "pass"
    print(json.dumps(report, indent=2, ensure_ascii=True))
    return 1 if report["summary"]["fail"] else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
