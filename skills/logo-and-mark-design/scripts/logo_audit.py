#!/usr/bin/env python3
"""Audit an SVG logo or mark for production problems. Prints one strict JSON object.

    python scripts/logo_audit.py [--kind mark|wordmark|lockup] logo.svg

Reads the one file given; writes nothing; no network. Standard library only.

Checks: viewBox present and plausible, aspect ratio for the kind, shape and
path counts, node count (complexity), stroke-width consistency, distinct
colours, gradients and opacity, text not converted to outlines, embedded
raster images, scripts, filters, and a legibility estimate from the smallest
feature size relative to the viewBox at 16, 32 and 64 px.

Exit codes: 0 verdict pass or review, 1 verdict fail, 2 unreadable or invalid
input (a JSON object with an "error" key is still printed on stdout).

The legibility estimate is geometric and approximate (see SKILL.md Limits):
it does not measure gaps between shapes and does not render the file.
"""
import argparse
import json
import math
import os
import re
import sys
import xml.etree.ElementTree as ET

MAX_BYTES = 5 * 1024 * 1024  # refuse huge files; a logo this large is already a defect
NUM = re.compile(r"[-+]?(?:\d*\.\d+|\d+\.?)(?:[eE][-+]?\d+)?")
ARGC = {"M": 2, "L": 2, "H": 1, "V": 1, "C": 6, "S": 4, "Q": 4, "T": 2, "A": 7}

# Thresholds. Each is a working value from SKILL.md, not a measured optimum.
SQUARE_MIN, SQUARE_MAX = 0.8, 1.25   # a stand-alone mark should sit in a near-square box
EXTREME_RATIO = 8.0                  # wordmark/lockup wider than 8:1 (or taller than 1:8) is unusable in most slots
NODES_COMPLEX = 200                  # above this a logo is hard to simplify for 16 px
PATHS_COMPLEX = 25
NODES_TRACED = 1000                  # above this the file is almost certainly an auto-trace of a raster
MAX_COLOURS = 3                      # more than 3 flat colours rarely survives one-colour printing
STROKE_CLUSTER_TOLERANCE = 1.02      # widths within 2% count as the same weight
ASPECT_ATTR_TOLERANCE = 0.02         # width/height attributes may differ from viewBox ratio by 2%
MIN_FEATURE_PX = 1.0                 # a feature thinner than 1 device pixel blurs away
TEST_SIZES = (16, 32, 64)

SHAPES = ("path", "rect", "circle", "ellipse", "line", "polyline", "polygon")
NONRENDER = ("defs", "clipPath", "mask", "symbol", "pattern", "marker")
INHERITED = ("fill", "stroke", "stroke-width", "font-family")
NAMED = {"black": "#000000", "white": "#ffffff"}


class Fail(Exception):
    pass


def local(tag):
    return tag.rsplit("}", 1)[-1] if isinstance(tag, str) else ""


def num(text):
    if text is None:
        return None
    m = NUM.match(str(text).strip())
    if not m:
        return None
    rest = str(text).strip()[m.end():].strip().lower()
    if rest not in ("", "px"):
        return None  # em, %, pt and friends are not resolved
    return float(m.group())


def rnd(x):
    return round(x, 4) if isinstance(x, float) and math.isfinite(x) else (x if not isinstance(x, float) else None)


# ---------------------------------------------------------------- path data
def arc_points(x1, y1, rx, ry, phi, fa, fs, x2, y2, steps=16):
    """Sample an SVG elliptical arc (endpoint form) into points."""
    if (x1 == x2 and y1 == y2) or rx == 0 or ry == 0:
        return [(x2, y2)]
    rx, ry = abs(rx), abs(ry)
    ph = math.radians(phi)
    c, s = math.cos(ph), math.sin(ph)
    dx, dy = (x1 - x2) / 2, (y1 - y2) / 2
    x1p, y1p = c * dx + s * dy, -s * dx + c * dy
    lam = x1p ** 2 / rx ** 2 + y1p ** 2 / ry ** 2
    if lam > 1:
        k = math.sqrt(lam)
        rx, ry = rx * k, ry * k
    den = rx * rx * y1p * y1p + ry * ry * x1p * x1p
    num_ = rx * rx * ry * ry - den
    coef = math.sqrt(max(0.0, num_ / den)) if den else 0.0
    if fa == fs:
        coef = -coef
    cxp, cyp = coef * rx * y1p / ry, -coef * ry * x1p / rx
    cx, cy = c * cxp - s * cyp + (x1 + x2) / 2, s * cxp + c * cyp + (y1 + y2) / 2

    def ang(ux, uy, vx, vy):
        return math.atan2(ux * vy - uy * vx, ux * vx + uy * vy)

    ux, uy = (x1p - cxp) / rx, (y1p - cyp) / ry
    th1 = ang(1, 0, ux, uy)
    dth = ang(ux, uy, (-x1p - cxp) / rx, (-y1p - cyp) / ry)
    if not fs and dth > 0:
        dth -= 2 * math.pi
    elif fs and dth < 0:
        dth += 2 * math.pi
    pts = []
    for k in range(1, steps + 1):
        t = th1 + dth * k / steps
        ex, ey = rx * math.cos(t), ry * math.sin(t)
        pts.append((cx + ex * c - ey * s, cy + ex * s + ey * c))
    pts[-1] = (x2, y2)
    return pts


def parse_path(d):
    """Return (subpaths, nodes). Subpaths are lists of absolute points."""
    i, n = 0, len(d)
    cmd = None
    cx = cy = sx = sy = 0.0
    subs, cur, nodes = [], None, 0

    def skip():
        nonlocal i
        while i < n and d[i] in " \t\r\n,":
            i += 1

    def number():
        nonlocal i
        skip()
        m = NUM.match(d, i)
        if not m:
            raise Fail("path data: expected a number at offset %d" % i)
        i = m.end()
        return float(m.group())

    def flag():
        nonlocal i
        skip()
        if i < n and d[i] in "01":
            i += 1
            return d[i - 1] == "1"
        raise Fail("path data: expected an arc flag at offset %d" % i)

    while True:
        skip()
        if i >= n:
            break
        ch = d[i]
        if ch.isalpha():
            if ch.upper() not in ARGC and ch not in "Zz":
                raise Fail("path data: unknown command %r" % ch)
            if cmd is None and ch not in "Mm":
                raise Fail("path data must start with M")
            cmd = ch
            i += 1
            if ch in "Zz":
                cx, cy = sx, sy
                cur = None
                continue
        elif cmd is None or cmd in "Zz":
            raise Fail("path data: unexpected number at offset %d" % i)
        up, rel = cmd.upper(), cmd.islower()
        if up != "M" and cur is None:
            cur = [(cx, cy)]
            subs.append(cur)
        ox, oy = (cx, cy) if rel else (0.0, 0.0)
        if up == "M":
            x, y = number() + ox, number() + oy
            cx, cy, sx, sy = x, y, x, y
            cur = [(x, y)]
            subs.append(cur)
            cmd = "l" if rel else "L"
        elif up == "L" or up == "T":
            x, y = number() + ox, number() + oy
            cur.append((x, y))
            cx, cy = x, y
        elif up == "H":
            x = number() + (cx if rel else 0.0)
            cur.append((x, cy))
            cx = x
        elif up == "V":
            y = number() + (cy if rel else 0.0)
            cur.append((cx, y))
            cy = y
        elif up in "CSQ":
            pts = [(number() + ox, number() + oy) for _ in range(ARGC[up] // 2)]
            cur.extend(pts)
            cx, cy = pts[-1]
        elif up == "A":
            rx, ry, rot = number(), number(), number()
            fa, fs = flag(), flag()
            x, y = number() + ox, number() + oy
            cur.extend(arc_points(cx, cy, rx, ry, rot, fa, fs, x, y))
            cx, cy = x, y
        nodes += 1
    return subs, nodes


def bbox_min_dim(points):
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    return min(max(xs) - min(xs), max(ys) - min(ys))


# ---------------------------------------------------------------- styles
def props_of(el):
    props = dict(el.attrib)
    style = el.get("style")
    if style:
        for decl in style.split(";"):
            if ":" in decl:
                k, v = decl.split(":", 1)
                props[k.strip()] = v.strip()
    return props


def transform_scale(text):
    s = 1.0
    for name, args in re.findall(r"(\w+)\s*\(([^)]*)\)", text or ""):
        vals = [float(v) for v in NUM.findall(args)]
        if name == "scale" and vals:
            sx = vals[0]
            sy = vals[1] if len(vals) > 1 else sx
            s *= math.sqrt(abs(sx * sy))
        elif name == "matrix" and len(vals) == 6:
            s *= math.sqrt(abs(vals[0] * vals[3] - vals[1] * vals[2]))
    return s


def norm_colour(value):
    """Return (key, has_alpha) or (None, False) for none/transparent/inherit."""
    v = value.strip().lower()
    if v in ("none", "transparent", "inherit", ""):
        return None, False
    if v == "currentcolor":
        return "currentcolor", False
    m = re.fullmatch(r"#([0-9a-f]{3,8})", v)
    if m:
        h = m.group(1)
        if len(h) in (3, 4):
            h = "".join(c * 2 for c in h)
        if len(h) == 8:
            return "#" + h[:6], h[6:] != "ff"
        if len(h) == 6:
            return "#" + h, False
    m = re.fullmatch(r"rgba?\(([^)]*)\)", v)
    if m:
        parts = [p for p in re.split(r"[ ,/]+", m.group(1).strip()) if p]
        try:
            rgb = []
            for p in parts[:3]:
                rgb.append(round(float(p[:-1]) * 2.55) if p.endswith("%") else round(float(p)))
            alpha = len(parts) > 3 and float(parts[3].rstrip("%")) < (100 if parts[3].endswith("%") else 1)
            return "#%02x%02x%02x" % tuple(max(0, min(255, c)) for c in rgb), alpha
        except (ValueError, IndexError):
            return v, False
    return NAMED.get(v, v), False


class State:
    def __init__(self):
        self.counts = {t: 0 for t in SHAPES}
        self.nodes = 0
        self.widths = []
        self.colours = {}
        self.implicit_black = False
        self.gradients = 0
        self.gradient_refs = 0
        self.opacity = False
        self.text = 0
        self.fonts = set()
        self.images = 0
        self.data_images = 0
        self.external_images = 0
        self.script = self.foreign = self.filters = self.use = self.style = 0
        self.masks = 0
        self.transforms = 0
        self.title = False
        self.features = []  # (size in user units, description)
        self.unparsed = 0
        self.stroked = 0

    def add_colour(self, value, implicit=False):
        if value.strip().lower().startswith("url("):
            self.gradient_refs += 1
            return
        key, alpha = norm_colour(value)
        if key is None:
            return
        if alpha:
            self.opacity = True
        if key == "currentcolor":
            self.colours["currentcolor"] = self.colours.get("currentcolor", 0) + 1
            return
        self.colours[key] = self.colours.get(key, 0) + 1
        if implicit and key == "#000000":
            self.implicit_black = True


def shape(el, tag, eff, scale, st):
    props = props_of(el)
    st.counts[tag] += 1
    fill = "none" if tag == "line" else eff.get("fill", "#000000")
    stroke = eff.get("stroke", "none")
    sw_raw = eff.get("stroke-width")
    sw = 1.0 if sw_raw is None else num(sw_raw)
    if sw is None:
        st.unparsed += 1
        sw = 1.0
    sw *= scale
    fill_on = fill.strip().lower() not in ("none", "transparent")
    stroke_on = stroke.strip().lower() not in ("none", "transparent") and sw > 0
    for key in ("opacity", "fill-opacity", "stroke-opacity"):
        v = num(props.get(key))
        if v is not None and v < 1:
            st.opacity = True

    # nodes and geometry
    sizes = []
    if tag == "path":
        try:
            subs, nodes = parse_path(el.get("d", ""))
        except Fail as exc:
            raise Fail("<path>: " + str(exc))
        st.nodes += nodes
        for sub in subs:
            if len(sub) > 1:
                d = bbox_min_dim(sub)
                if d > 1e-6:
                    sizes.append(d * scale)
    elif tag == "rect":
        w, h = num(el.get("width")), num(el.get("height"))
        if w is None or h is None:
            st.unparsed += 1
        else:
            sizes.append(min(w, h) * scale)
        st.nodes += 8 if (num(el.get("rx")) or num(el.get("ry"))) else 4
    elif tag == "circle":
        r = num(el.get("r"))
        if r is None:
            st.unparsed += 1
        else:
            sizes.append(2 * r * scale)
        st.nodes += 4
    elif tag == "ellipse":
        rx, ry = num(el.get("rx")), num(el.get("ry"))
        if rx is None or ry is None:
            st.unparsed += 1
        else:
            sizes.append(2 * min(rx, ry) * scale)
        st.nodes += 4
    elif tag == "line":
        st.nodes += 2
    else:  # polyline, polygon
        vals = [float(v) for v in NUM.findall(el.get("points", ""))]
        pts = list(zip(vals[0::2], vals[1::2]))
        st.nodes += len(pts)
        if len(pts) > 1:
            d = bbox_min_dim(pts)
            if d > 1e-6:
                sizes.append(d * scale)

    if fill_on:
        st.add_colour(fill, implicit="fill" not in eff)
        for s in sizes:
            st.features.append((s, "filled <%s> bounding box" % tag))
    if stroke_on:
        st.add_colour(stroke)
        st.widths.append(sw)
        st.stroked += 1
        st.features.append((sw, "stroke-width on <%s>" % tag))


def walk(el, eff, scale, render, st):
    tag = local(el.tag)
    props = props_of(el)
    if el.get("transform"):
        st.transforms += 1
    scale = scale * transform_scale(el.get("transform"))
    if tag == "title":
        st.title = bool((el.text or "").strip())
        return
    if tag in ("desc", "metadata"):
        return
    if tag in ("linearGradient", "radialGradient"):
        st.gradients += 1
        for stop in el:
            if local(stop.tag) == "stop":
                p = props_of(stop)
                st.add_colour(p.get("stop-color", "#000000"))
        return
    if tag == "style":
        st.style += 1
        return
    if tag == "script":
        st.script += 1
        return
    if tag == "foreignObject":
        st.foreign += 1
        return
    if tag == "image":
        st.images += 1
        href = next((v for k, v in el.attrib.items() if k.endswith("href")), "")
        if href.strip().lower().startswith("data:"):
            st.data_images += 1
        elif href.strip():
            st.external_images += 1
        return
    if tag == "use":
        st.use += 1
        return
    if tag == "filter":
        st.filters += 1
        return
    if props.get("filter"):
        st.filters += 1
    if tag in ("clipPath", "mask"):
        st.masks += 1
    eff = dict(eff)
    for key in INHERITED:
        if key in props:
            eff[key] = props[key]
    if tag == "text":
        st.text += 1
        fam = eff.get("font-family", "")
        for f in fam.split(","):
            f = f.strip().strip("'\"")
            if f:
                st.fonts.add(f)
        return
    if tag in SHAPES:
        if render:
            shape(el, tag, eff, scale, st)
        return
    for child in el:
        walk(child, eff, scale, render and tag not in NONRENDER, st)


# ---------------------------------------------------------------- audit
def parse_viewbox(text):
    vals = [float(v) for v in NUM.findall(text or "")]
    return vals if len(vals) == 4 else None


def cluster_widths(widths):
    clusters = []
    for w in sorted(widths):
        if clusters and w <= clusters[-1][0] * STROKE_CLUSTER_TOLERANCE:
            continue
        clusters.append((w,))
    return [c[0] for c in clusters]


def audit(root, kind):
    findings = []

    def add(sev, code, msg):
        findings.append({"severity": sev, "code": code, "message": msg})

    st = State()
    vb_text = root.get("viewBox")
    vb = parse_viewbox(vb_text)
    declared_w, declared_h = num(root.get("width")), num(root.get("height"))
    viewbox = {"present": vb_text is not None}
    ref_w = ref_h = None
    if vb_text is None:
        add("fail", "no_viewbox", "No viewBox on the root <svg>. Add viewBox=\"0 0 W H\" so the file scales.")
        if declared_w and declared_h:
            ref_w, ref_h = declared_w, declared_h
    elif vb is None or vb[2] <= 0 or vb[3] <= 0:
        add("fail", "bad_viewbox", "viewBox must be four numbers with positive width and height.")
    else:
        ref_w, ref_h = vb[2], vb[3]
        ratio = ref_w / ref_h
        shape_word = "square" if 0.95 <= ratio <= 1.05 else ("wide" if ratio > 1 else "tall")
        viewbox.update({"min_x": rnd(vb[0]), "min_y": rnd(vb[1]), "width": rnd(ref_w), "height": rnd(ref_h),
                        "aspect_ratio": rnd(ratio), "shape": shape_word})
        if vb[0] != 0 or vb[1] != 0:
            add("info", "viewbox_origin_nonzero", "viewBox origin is not 0 0; harmless but easy to break when editing.")
        if kind == "mark" and not (SQUARE_MIN <= ratio <= SQUARE_MAX):
            add("warn", "aspect_not_square", "Aspect ratio %.2f is outside %.2f-%.2f for a stand-alone mark; use --kind wordmark or lockup if this is not a mark, or crop the box." % (ratio, SQUARE_MIN, SQUARE_MAX))
        if kind != "mark" and (ratio > EXTREME_RATIO or ratio < 1 / EXTREME_RATIO):
            add("warn", "aspect_extreme", "Aspect ratio %.2f is beyond %d:1; it will not fit most header or avatar slots." % (ratio, int(EXTREME_RATIO)))
        if declared_w and declared_h and abs((declared_w / declared_h) / ratio - 1) > ASPECT_ATTR_TOLERANCE:
            add("warn", "size_attr_mismatch", "width/height attributes do not match the viewBox ratio; the logo will letterbox or distort.")

    walk(root, {}, 1.0, True, st)

    total_shapes = sum(st.counts.values())
    if st.nodes > NODES_TRACED:
        cls = "traced"
        add("fail", "traced_complexity", "%d nodes: this looks auto-traced from a raster. Redraw it from simple geometry." % st.nodes)
    elif st.nodes > NODES_COMPLEX or st.counts["path"] > PATHS_COMPLEX:
        cls = "complex"
        add("warn", "high_complexity", "%d nodes across %d paths; above %d nodes or %d paths it rarely simplifies to 16 px." % (st.nodes, st.counts["path"], NODES_COMPLEX, PATHS_COMPLEX))
    elif st.nodes > 80:
        cls = "moderate"
    else:
        cls = "simple"

    clusters = cluster_widths(st.widths)
    ratio_w = (max(st.widths) / min(st.widths)) if st.widths else None
    if len(clusters) > 1:
        add("warn", "stroke_widths_inconsistent", "%d different stroke weights (%s). Use one weight unless the contrast is a documented design choice." % (len(clusters), ", ".join(str(rnd(c)) for c in clusters)))
    if st.stroked:
        add("info", "strokes_not_outlined", "%d live stroked element(s). Expand strokes to outlines in the final export so weight does not change when scaled in other tools." % st.stroked)

    colours = sorted(k for k in st.colours if k != "currentcolor")
    if len(colours) > MAX_COLOURS:
        add("warn", "too_many_colours", "%d distinct colours; more than %d rarely reproduces in one-colour or two-colour print." % (len(colours), MAX_COLOURS))
    if st.gradients or st.gradient_refs:
        add("warn", "gradient_used", "Gradients or patterns present; they do not reproduce in one-colour use and need a flat fallback.")
    if st.opacity:
        add("warn", "opacity_used", "Transparency present (opacity or alpha colours); it changes the look on different backgrounds and in print.")
    if "currentcolor" in st.colours:
        add("info", "uses_currentcolor", "currentColor used: the mark takes the surrounding text colour; fine for a mono file, not for a colour master.")

    if st.text:
        add("fail", "text_not_outlined", "%d <text> element(s). Convert letters to paths so the logo does not depend on installed fonts (fonts: %s)." % (st.text, ", ".join(sorted(st.fonts)) or "unspecified"))
    if st.images:
        add("fail", "raster_embedded", "%d <image> element(s) (%d data URI, %d external). A logo SVG must be pure vector." % (st.images, st.data_images, st.external_images))
    if st.script:
        add("fail", "script_element", "<script> inside a logo file; remove it.")
    if st.foreign:
        add("warn", "foreign_object", "<foreignObject> is not portable across logo tools and print.")
    if st.filters:
        add("warn", "filter_effect", "Filter effects (blur, shadow) do not survive export to print or other tools; bake them out.")
    if st.style:
        add("warn", "style_element_not_evaluated", "A <style> block is present; this audit reads only attributes and inline style, so colours, strokes and sizes from CSS rules are not counted.")
    if st.use:
        add("warn", "use_not_resolved", "<use> references are not followed; their geometry is not measured here.")
    if st.unparsed:
        add("warn", "unparsed_geometry", "%d length(s) in em, %%, pt or similar units were skipped; convert to plain user units." % st.unparsed)
    if not st.title:
        add("info", "no_title", "No <title>; add one for accessibility and for tools that show a name.")

    # legibility
    ref = None
    if ref_w and ref_h:
        ref = max(ref_w, ref_h) if kind == "mark" else ref_h
    legibility = {"reference": "longest side" if kind == "mark" else "height", "risk": "unknown"}
    if st.features and ref:
        size, source = min(st.features, key=lambda f: f[0])
        px = {str(s): rnd(size / ref * s) for s in TEST_SIZES}
        legibility.update({
            "smallest_feature_units": rnd(size), "smallest_feature_fraction": rnd(size / ref),
            "smallest_feature_source": source, "feature_px": px,
            "min_feature_px_required": MIN_FEATURE_PX,
        })
        if size / ref * 16 >= MIN_FEATURE_PX:
            legibility["risk"] = "low"
        elif size / ref * 32 >= MIN_FEATURE_PX:
            legibility["risk"] = "medium"
            add("warn", "legibility_medium", "Smallest feature is %.2f px at 16 px: fine at 32 px, lost at 16 px. Plan a simplified favicon variant." % (size / ref * 16))
        else:
            legibility["risk"] = "high"
            add("warn", "legibility_high", "Smallest feature is %.2f px at 32 px and %.2f px at 64 px: thicken or remove it." % (size / ref * 32, size / ref * 64))

    verdict = "fail" if any(f["severity"] == "fail" for f in findings) else ("review" if any(f["severity"] == "warn" for f in findings) else "pass")
    return {
        "tool": "logo_audit", "kind": kind, "verdict": verdict,
        "viewbox": viewbox,
        "declared_size": {"width": rnd(declared_w), "height": rnd(declared_h)},
        "elements": {"paths": st.counts["path"], "shapes_total": total_shapes,
                     "by_tag": {k: v for k, v in st.counts.items() if v}},
        "complexity": {"nodes": st.nodes, "paths": st.counts["path"], "class": cls},
        "strokes": {"stroked_elements": st.stroked, "distinct_widths": [rnd(c) for c in clusters],
                    "max_to_min_ratio": rnd(ratio_w), "consistent": len(clusters) <= 1},
        "colours": {"distinct": len(colours), "values": colours, "implicit_default_black": st.implicit_black,
                    "gradients_defined": st.gradients, "opacity_used": st.opacity,
                    "uses_currentcolor": "currentcolor" in st.colours},
        "text": {"text_elements": st.text, "font_families": sorted(st.fonts)},
        "raster": {"images": st.images, "data_uri": st.data_images, "external": st.external_images},
        "transforms": {"elements_with_transform": st.transforms},
        "legibility": legibility,
        "findings": findings,
    }


def load(path):
    if not os.path.isfile(path):
        raise Fail("file not found: %s" % path)
    if os.path.getsize(path) > MAX_BYTES:
        raise Fail("file is larger than %d MB; a logo should be a few KB" % (MAX_BYTES // 1048576))
    data = open(path, "rb").read()
    if not data.strip():
        raise Fail("file is empty")
    if re.search(rb"<!ENTITY", data, re.I):
        raise Fail("file declares XML entities; refusing to parse")
    try:
        root = ET.fromstring(data)
    except ET.ParseError as exc:
        raise Fail("not well-formed XML: %s" % exc)
    if local(root.tag) != "svg":
        raise Fail("root element is <%s>, not <svg>" % local(root.tag))
    return root


def emit(obj):
    print(json.dumps(obj, indent=2, sort_keys=False, allow_nan=False))


def main(argv=None):
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except (ValueError, OSError):
            pass
    ap = argparse.ArgumentParser(description="Audit an SVG logo; prints strict JSON.")
    ap.add_argument("svg")
    ap.add_argument("--kind", choices=("mark", "wordmark", "lockup"), default="mark",
                    help="mark: square symbol (default); wordmark or lockup: wide, sized by height")
    args = ap.parse_args(argv)
    try:
        root = load(args.svg)
        report = audit(root, args.kind)
        report["file"] = os.path.basename(args.svg)
    except Fail as exc:
        sys.stderr.write("logo_audit: %s\n" % exc)
        emit({"tool": "logo_audit", "file": os.path.basename(args.svg), "error": str(exc)})
        return 2
    emit(report)
    return 1 if report["verdict"] == "fail" else 0


if __name__ == "__main__":
    sys.exit(main())
