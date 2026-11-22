#!/usr/bin/env python3
"""Translate exported design-tool node JSON into CSS declarations (standard library only).

Usage:
    python node_to_css.py design.json [--tokens tokens.css] [--node "Frame name or id"]
                          [--diff "Frame A" "Frame B"] [--json]

design.json  node JSON in the REST shape used by Figma file and node exports: objects
             with type, name, children and layout fields (layoutMode, itemSpacing,
             padding*, fills, strokes, style ...). Accepted wrappers: a bare node, a
             list of nodes, {"document": ...} or {"nodes": {id: {"document": ...}}}.
--tokens     a CSS file with custom properties; exact matches are printed as
             var(--name), near misses are flagged as off-token with the nearest token.
--node       print only the subtree whose name or id matches.
--diff       compare two frames node by node (matched by layer name) and print the
             declarations that differ: the raw material for breakpoint rules.

Reads the files named. Writes nothing. No network.
Exit codes: 0 = ok, 2 = usage, read or shape error.

The output is a faithful reading of the spec, not finished code: semantics, states,
responsiveness and component reuse still need a person or agent to decide.
"""
import json
import math
import os
import re
import sys

SEP = " > "   # separator in layer paths; layer names often contain "/"
VECTOR_TYPES = {"VECTOR", "BOOLEAN_OPERATION", "STAR", "LINE", "REGULAR_POLYGON"}
JUSTIFY = {"MIN": None, "CENTER": "center", "MAX": "flex-end", "SPACE_BETWEEN": "space-between"}
ALIGN = {"MIN": "flex-start", "CENTER": "center", "MAX": "flex-end", "BASELINE": "baseline"}
ELEMENT_HINTS = [(r"\b(btn|button|cta)\b", "button (or a, if it navigates)"), (r"\b(input|field|textbox|search)\b", "label + input"),
                 (r"\bnav(bar|igation)?\b", "nav"), (r"\bheader\b", "header"), (r"\bfooter\b", "footer"), (r"\bcard\b", "article or li"),
                 (r"\b(list|menu)\b", "ul"), (r"\b(checkbox|radio|toggle|switch)\b", "native input with label"), (r"\b(link)\b", "a"),
                 (r"\b(icon)\b", "inline SVG, aria-hidden if decorative"), (r"\b(modal|dialog)\b", "dialog"), (r"\b(tab)s?\b", "tablist pattern")]
# Property families used to pick the best token when several share one value.
AFFINITY = {"background-color": r"bg|surface|background|fill|accent|brand", "color": r"text|fg|on-|content|ink|label|accent|link",
            "border": r"border|stroke|outline|divider", "gap": r"space|spacing|gap", "padding": r"space|spacing|pad|inset",
            "border-radius": r"radius|round|corner", "font-size": r"font|text|size|type", "line-height": r"line|leading",
            "box-shadow": r"shadow|elevation", "width": r"(?<!font-)size|width|container", "height": r"(?<!font-)size|height"}


def fmt(n):
    return f"{round(n, 2):g}"


def hex_color(c, opacity=1.0):
    a = c.get("a", 1.0) * opacity
    r, g, b = (round(max(0, min(1, c.get(k, 0))) * 255) for k in "rgb")
    if a >= 0.999:
        return f"#{r:02x}{g:02x}{b:02x}"
    return f"rgba({r}, {g}, {b}, {fmt(a)})"


class Tokens:
    def __init__(self, path):
        self.colors, self.lengths, self.raw, self.other = {}, {}, {}, {}
        if not path:
            return
        with open(path, encoding="utf-8", errors="replace") as fh:
            css = re.sub(r"/\*.*?\*/", "", fh.read(), flags=re.S)
        for name, val in re.findall(r"(--[\w-]+)\s*:\s*([^;}]+)", css):
            self.raw.setdefault(name, val.strip())
        for name in self.raw:
            val = self.resolve(name)
            if val is None:
                continue
            m = re.fullmatch(r"#([0-9a-fA-F]{3}|[0-9a-fA-F]{6})", val)
            if m:
                h = m.group(1).lower()
                h = "".join(ch * 2 for ch in h) if len(h) == 3 else h
                self.colors.setdefault("#" + h, []).append(name)
                continue
            m = re.fullmatch(r"(-?[\d.]+)(px|rem)", val)
            if m:
                self.lengths.setdefault(round(float(m.group(1)) * (16 if m.group(2) == "rem" else 1), 3), []).append(name)
                continue
            self.other.setdefault(self.norm(val), []).append(name)

    @staticmethod
    def norm(value):
        """Normalise a composite value (shadow, font stack) so equal values compare equal."""
        return re.sub(r"\s+", "", re.sub(r"\b0px\b", "0", value.lower())).replace('"', "").replace("'", "")

    def composite(self, value, prop):
        names = [n for n in self.other.get(self.norm(value), []) if re.search(AFFINITY.get(prop, "."), n)]
        return f"var({names[0]}) /* {value} */" if names else value

    def font(self, family):
        for val, names in self.other.items():
            if val.startswith(family.lower().replace(" ", "")) and any("font" in n for n in names):
                return f"var({next(n for n in names if 'font' in n)})"
        return None

    def resolve(self, name, depth=0):
        val = self.raw.get(name)
        m = re.fullmatch(r"var\(\s*(--[\w-]+)\s*(?:,[^)]*)?\)", val or "")
        if m and depth < 8:
            return self.resolve(m.group(1), depth + 1)
        return val

    def pick(self, names, prop):
        """Prefer a token whose name fits the property, then one that is itself an alias (semantic)."""
        pat = AFFINITY.get(prop, "")
        scored = sorted(names, key=lambda n: (not (pat and re.search(pat, n)), not self.raw[n].startswith("var("), len(n)))
        return scored[0], scored[1:]

    def color(self, value, prop, flags):
        if not self.raw or not value.startswith("#"):
            return value
        if value in self.colors:
            best, others = self.pick(self.colors[value], prop)
            return f"var({best})" + (f" /* {value}; also {', '.join(others[:3])} */" if others else f" /* {value} */")
        if self.colors:
            rgb = [int(value[i:i + 2], 16) for i in (1, 3, 5)]
            near = min(self.colors, key=lambda h: sum((int(h[i:i + 2], 16) - c) ** 2 for i, c in zip((1, 3, 5), rgb)))
            flags.append(f"off-token colour {value} ({prop}); nearest token {self.pick(self.colors[near], prop)[0]} = {near}. Decide (token or spec value) and report it; never keep a raw colour silently")
        return value

    def length(self, px, prop, flags, unit="px"):
        text = f"{fmt(px)}{unit}"
        if not self.raw or px == 0:
            return "0" if px == 0 else text
        key = round(px, 3)
        if key in self.lengths:
            fam = "gap" if prop in ("gap", "row-gap", "column-gap") else "padding" if prop.startswith("padding") else prop
            cands = [n for n in self.lengths[key] if re.search(AFFINITY.get(fam, "."), n)]
            if cands:
                best, _ = self.pick(cands, fam)
                return f"var({best}) /* {text} */"
        fam = "gap" if prop in ("gap", "row-gap", "column-gap") else "padding" if prop.startswith("padding") else prop
        pool = {v: n for v, n in self.lengths.items() if any(re.search(AFFINITY.get(fam, "$^"), x) for x in n)}
        if pool and fam in ("gap", "padding", "border-radius", "font-size"):
            name_of = lambda v: next(x for x in pool[v] if re.search(AFFINITY[fam], x))
            lower, upper = [v for v in pool if v < px], [v for v in pool if v > px]
            near = [f"{name_of(v)} = {fmt(v)}px" for v in ([max(lower)] if lower else []) + ([min(upper)] if upper else [])]
            flags.append(f"off-token {prop} {text}; nearest tokens {' and '.join(near)}. Decide (token or spec value) and report it")
        return text


def gradient(paint):
    hp = paint.get("gradientHandlePositions") or []
    stops = paint.get("gradientStops") or []
    angle = 180.0
    if len(hp) >= 2:
        angle = (math.degrees(math.atan2(hp[1]["y"] - hp[0]["y"], hp[1]["x"] - hp[0]["x"])) + 90) % 360
    parts = [f"{hex_color(s['color'], paint.get('opacity', 1.0))} {fmt(s['position'] * 100)}%" for s in stops]
    return f"linear-gradient({fmt(angle)}deg, {', '.join(parts)})"


def node_css(node, parent, tokens):
    """Return (ordered list of (property, value), flags)."""
    css, flags = [], []
    t = node.get("type", "")
    box = node.get("absoluteBoundingBox") or {}
    w, h = box.get("width"), box.get("height")
    mode = node.get("layoutMode", "NONE")
    pmode = (parent or {}).get("layoutMode", "NONE")

    def add(prop, value):
        if value is not None:
            css.append((prop, value))

    # --- position inside the parent ---
    if parent and node.get("layoutPositioning") == "ABSOLUTE":
        pbox = parent.get("absoluteBoundingBox") or {}
        if box and pbox:
            cons = node.get("constraints") or {}
            left, top = box["x"] - pbox["x"], box["y"] - pbox["y"]
            right, bottom = pbox["width"] - left - w, pbox["height"] - top - h
            add("position", "absolute")
            hc, vc = cons.get("horizontal", "LEFT"), cons.get("vertical", "TOP")
            if hc in ("LEFT", "LEFT_RIGHT", "SCALE"):
                add("left", f"{fmt(left)}px")
            if hc in ("RIGHT", "LEFT_RIGHT"):
                add("right", f"{fmt(right)}px")
            if hc == "CENTER":
                add("left", "50%")
                flags.append("centred horizontally by constraint: add transform: translateX(-50%) or use auto margins")
            if vc in ("TOP", "TOP_BOTTOM", "SCALE"):
                add("top", f"{fmt(top)}px")
            if vc in ("BOTTOM", "TOP_BOTTOM"):
                add("bottom", f"{fmt(bottom)}px")
            if vc == "CENTER":
                add("top", "50%")
                flags.append("centred vertically by constraint: add transform: translateY(-50%)")
            flags.append("absolutely positioned: the parent needs position: relative")

    # --- auto layout container ---
    if mode in ("HORIZONTAL", "VERTICAL"):
        add("display", "flex")
        add("flex-direction", "column" if mode == "VERTICAL" else None)
        if node.get("layoutWrap") == "WRAP":
            add("flex-wrap", "wrap")
        primary = node.get("primaryAxisAlignItems", "MIN")
        add("justify-content", JUSTIFY.get(primary))
        add("align-items", ALIGN.get(node.get("counterAxisAlignItems", "MIN")))
        gap = node.get("itemSpacing", 0)
        if primary == "SPACE_BETWEEN":
            if len([c for c in node.get("children", []) if c.get("visible", True)]) > 1:
                flags.append("spacing is 'auto' (space-between); itemSpacing is ignored by the design tool here")
        elif gap:
            add("gap", tokens.length(gap, "gap", flags))
        if node.get("layoutWrap") == "WRAP" and node.get("counterAxisSpacing"):
            add("row-gap", tokens.length(node["counterAxisSpacing"], "row-gap", flags))
        pt, pr, pb, pl = (node.get(k, 0) or 0 for k in ("paddingTop", "paddingRight", "paddingBottom", "paddingLeft"))
        if any((pt, pr, pb, pl)):
            vals = [pt, pr, pb, pl]
            if pt == pb and pl == pr:
                vals = [pt] if pt == pl else [pt, pr]
            elif pl == pr:
                vals = [pt, pr, pb]
            add("padding", " ".join(tokens.length(v, "padding", flags) for v in vals))
    elif mode == "GRID":
        add("display", "grid")
        flags.append("grid auto layout: read gridRowCount / gridColumnCount and the track sizes from the node and write grid-template by hand")
    elif node.get("children") and t in ("FRAME", "COMPONENT", "INSTANCE", "GROUP", "COMPONENT_SET", "SECTION") and len(node["children"]) > 1:
        flags.append("no auto layout: children are placed by x/y. Infer the intended flow (stack, row, grid) from their positions; do not copy coordinates")

    # --- size ---
    sizing = {"h": node.get("layoutSizingHorizontal"), "v": node.get("layoutSizingVertical")}
    if sizing["h"] is None and pmode in ("HORIZONTAL", "VERTICAL"):
        grow, stretch = node.get("layoutGrow", 0) == 1, node.get("layoutAlign") == "STRETCH"
        sizing["h"] = "FILL" if (grow and pmode == "HORIZONTAL") or (stretch and pmode == "VERTICAL") else None
        sizing["v"] = "FILL" if (grow and pmode == "VERTICAL") or (stretch and pmode == "HORIZONTAL") else None
    if sizing["h"] is None and mode in ("HORIZONTAL", "VERTICAL"):
        own = node.get("primaryAxisSizingMode" if mode == "HORIZONTAL" else "counterAxisSizingMode", "AUTO")
        sizing["h"] = "FIXED" if own == "FIXED" else "HUG"
    if sizing["v"] is None and mode in ("HORIZONTAL", "VERTICAL"):
        own = node.get("primaryAxisSizingMode" if mode == "VERTICAL" else "counterAxisSizingMode", "AUTO")
        sizing["v"] = "FIXED" if own == "FIXED" else "HUG"
    for axis, dim, prop in (("h", w, "width"), ("v", h, "height")):
        s = sizing[axis]
        along = (pmode == "HORIZONTAL" and axis == "h") or (pmode == "VERTICAL" and axis == "v")
        if s == "FILL":
            if along:
                add("flex", "1 1 0")
                add("min-width" if axis == "h" else "min-height", "0")
            elif pmode in ("HORIZONTAL", "VERTICAL"):
                add("align-self", "stretch")
            else:
                add(prop, "100%")
        elif s == "FIXED" and dim is not None:
            if parent is None and axis == "h":
                flags.append(f"top-level frame is {fmt(dim)}px wide: that is the artboard, not a width to hard-code; use max-width or a breakpoint")
            elif t == "TEXT" and axis == "v":
                pass  # text height follows from line-height and content
            else:
                add(prop, tokens.length(dim, prop, []))
                if along:
                    add("flex-shrink", "0")
                if axis == "v" and mode in ("HORIZONTAL", "VERTICAL") and t != "TEXT":
                    flags.append(f"fixed height {fmt(dim)}px on a container: content that grows (long text, translation) will overflow; prefer min-height unless the spec says clip")
        elif s is None and dim is not None and t not in ("TEXT",) and not node.get("children") and pmode not in ("HORIZONTAL", "VERTICAL"):
            add(prop, f"{fmt(dim)}px")
    for key, prop in (("minWidth", "min-width"), ("maxWidth", "max-width"), ("minHeight", "min-height"), ("maxHeight", "max-height")):
        if node.get(key) is not None:
            add(prop, f"{fmt(node[key])}px")

    # --- paint ---
    fills = [f for f in node.get("fills", []) if f.get("visible", True)]
    if len(fills) > 1:
        flags.append(f"{len(fills)} stacked fills: only the top one is translated; combine them by hand")
    if fills:
        f = fills[-1]
        if f.get("type") == "SOLID":
            value = hex_color(f["color"], f.get("opacity", 1.0))
            add("color" if t == "TEXT" else "background-color", tokens.color(value, "color" if t == "TEXT" else "background-color", flags))
        elif f.get("type") == "GRADIENT_LINEAR":
            add("background-image" if t != "TEXT" else "color", gradient(f) if t != "TEXT" else "/* gradient text: needs background-clip: text */")
        elif f.get("type") == "IMAGE":
            flags.append(f"image fill (scaleMode {f.get('scaleMode', 'FILL')}): export the asset; FILL maps to object-fit: cover, FIT to contain")
        else:
            flags.append(f"fill type {f.get('type')} is not translated")
    strokes = [s for s in node.get("strokes", []) if s.get("visible", True)]
    if strokes and strokes[-1].get("type") == "SOLID" and (node.get("strokeWeight") or node.get("individualStrokeWeights")):
        col = tokens.color(hex_color(strokes[-1]["color"], strokes[-1].get("opacity", 1.0)), "border", flags)
        style = "dashed" if node.get("strokeDashes") else "solid"
        ind = node.get("individualStrokeWeights")
        if ind:
            for side in ("top", "right", "bottom", "left"):
                if ind.get(side):
                    add(f"border-{side}", f"{fmt(ind[side])}px {style} {col}")
        else:
            align = node.get("strokeAlign", "INSIDE")
            sw = node["strokeWeight"]
            if align == "OUTSIDE":
                add("outline", f"{fmt(sw)}px {style} {col}")
                flags.append("stroke is OUTSIDE the box: outline (or box-shadow 0 0 0) keeps the box size; a border would grow it")
            else:
                add("border", f"{fmt(sw)}px {style} {col}")
                if align == "CENTER":
                    flags.append(f"stroke is CENTER aligned: the visual box is {fmt(sw)}px larger than the frame size; INSIDE matches box-sizing: border-box")
    radii = node.get("rectangleCornerRadii")
    radius = node.get("cornerRadius")
    if radii and len(set(radii)) > 1:
        add("border-radius", " ".join(f"{fmt(r)}px" for r in radii))
    elif radius or (radii and radii[0]):
        r = radius or radii[0]
        if w and h and r >= min(w, h) / 2:
            pill = tokens.length(9999, "border-radius", [])
            add("border-radius", pill if pill.startswith("var(") else "9999px")
        else:
            add("border-radius", tokens.length(r, "border-radius", flags))
    if t == "ELLIPSE" and w == h:
        add("border-radius", "50%")
    shadows = []
    for e in node.get("effects", []):
        if not e.get("visible", True):
            continue
        if e["type"] in ("DROP_SHADOW", "INNER_SHADOW"):
            off = e.get("offset", {"x": 0, "y": 0})
            sh = f"{'inset ' if e['type'] == 'INNER_SHADOW' else ''}{fmt(off['x'])}px {fmt(off['y'])}px {fmt(e.get('radius', 0))}px {fmt(e.get('spread', 0))}px {hex_color(e['color'])}"
            shadows.append(sh)
        elif e["type"] == "LAYER_BLUR":
            add("filter", f"blur({fmt(e.get('radius', 0) / 2)}px)")
        elif e["type"] == "BACKGROUND_BLUR":
            add("backdrop-filter", f"blur({fmt(e.get('radius', 0) / 2)}px)")
    if shadows:
        if t == "TEXT":
            add("text-shadow", ", ".join(re.sub(r"px \S+px (#|rgba)", r"px \1", s, count=1) for s in shadows))
        else:
            add("box-shadow", tokens.composite(", ".join(shadows), "box-shadow"))
    if node.get("opacity", 1) < 1:
        add("opacity", fmt(node["opacity"]))
    if node.get("clipsContent") and node.get("children"):
        add("overflow", "hidden")
    if node.get("rotation"):
        flags.append(f"rotated (exported value {fmt(node['rotation'])}, in radians in REST exports): add transform: rotate()")

    # --- text ---
    if t == "TEXT":
        st = node.get("style", {})
        size = st.get("fontSize")
        if st.get("fontFamily"):
            add("font-family", tokens.font(st["fontFamily"]) or f'"{st["fontFamily"]}", <fallback stack from the project>')
        if size:
            add("font-size", tokens.length(size, "font-size", flags))
        if st.get("fontWeight"):
            add("font-weight", str(int(st["fontWeight"])))
        if st.get("italic"):
            add("font-style", "italic")
        unit = st.get("lineHeightUnit")
        if unit == "PIXELS" and st.get("lineHeightPx") and size:
            add("line-height", f"{round(st['lineHeightPx'] / size, 3):g} /* {fmt(st['lineHeightPx'])}px on {fmt(size)}px */")
        elif unit == "FONT_SIZE_%" and st.get("lineHeightPercentFontSize"):
            add("line-height", fmt(st["lineHeightPercentFontSize"] / 100))
        elif unit == "INTRINSIC_%":
            add("line-height", "normal")
        if st.get("letterSpacing") and size:
            add("letter-spacing", f"{round(st['letterSpacing'] / size, 3):g}em /* {fmt(st['letterSpacing'])}px */")
        align = st.get("textAlignHorizontal", "LEFT")
        if align != "LEFT":
            add("text-align", {"CENTER": "center", "RIGHT": "right", "JUSTIFIED": "justify"}.get(align, "left"))
        case = st.get("textCase")
        if case in ("UPPER", "LOWER", "TITLE"):
            add("text-transform", {"UPPER": "uppercase", "LOWER": "lowercase", "TITLE": "capitalize"}[case])
            flags.append("case comes from a text style: keep the source text in sentence case and transform in CSS")
        if st.get("textDecoration") in ("UNDERLINE", "STRIKETHROUGH"):
            add("text-decoration", "underline" if st["textDecoration"] == "UNDERLINE" else "line-through")
        if st.get("textAutoResize") == "TRUNCATE" or st.get("textTruncation") == "ENDING":
            if st.get("maxLines", 1) > 1:
                add("display", "-webkit-box")
                add("-webkit-line-clamp", str(st["maxLines"]))
                add("-webkit-box-orient", "vertical")
                add("overflow", "hidden")
            else:
                add("white-space", "nowrap")
                add("overflow", "hidden")
                add("text-overflow", "ellipsis")
        if st.get("paragraphSpacing"):
            flags.append(f"paragraph spacing {fmt(st['paragraphSpacing'])}px: margin between paragraphs, not line-height")
    if t in VECTOR_TYPES:
        return [], ["vector shape: export as SVG; do not rebuild with CSS"]
    if t == "INSTANCE":
        props = node.get("componentProperties") or {}
        desc = ", ".join(f"{k.split('#')[0]}={v.get('value')}" for k, v in props.items()) if props else "no properties exported"
        flags.append(f"instance of a design component ({desc}): look for an existing code component with this name before writing new markup")
    return css, flags


def slug(name):
    s = re.sub(r"[^a-zA-Z0-9]+", "-", name).strip("-").lower()
    return s or "node"


def walk(node, parent, tokens, out, path, counts, hidden):
    if not node.get("visible", True):
        hidden.append(SEP.join(path + [node.get("name", "?")]))
        return
    name = node.get("name", node.get("type", "node"))
    key = SEP.join(path + [name])
    counts[key] = counts.get(key, 0) + 1
    if counts[key] > 1:
        key += f"#{counts[key]}"
    css, flags = node_css(node, parent, tokens)
    hint = next((el for pat, el in ELEMENT_HINTS if re.search(pat, name, re.I)), None)
    box = node.get("absoluteBoundingBox") or {}
    pbox = (parent or {}).get("absoluteBoundingBox") or {}
    offset = None
    if parent and parent.get("layoutMode", "NONE") in ("NONE", None) and box and pbox:
        offset = f"x {fmt(box['x'] - pbox['x'])}, y {fmt(box['y'] - pbox['y'])} in parent (reference only)"
    out.append({"path": key, "depth": len(path), "name": name, "type": node.get("type"), "id": node.get("id"), "class": slug(name),
                "size": f"{fmt(box['width'])}x{fmt(box['height'])}" if box else "", "text": node.get("characters"),
                "element_hint": hint, "css": css, "flags": flags, "offset": offset})
    for child in node.get("children", []):
        walk(child, node, tokens, out, path + [name], counts, hidden)


def roots(data):
    if isinstance(data, list):
        return data
    if "nodes" in data and isinstance(data["nodes"], dict):
        return [v["document"] for v in data["nodes"].values() if isinstance(v, dict) and "document" in v]
    if "document" in data:
        return [data["document"]]
    return [data]


def find(nodes, wanted):
    for n in nodes:
        if n.get("name") == wanted or n.get("id") == wanted:
            return n
        hit = find(n.get("children", []), wanted)
        if hit:
            return hit
    return None


def render(items):
    lines = []
    for it in items:
        ind = "  " * it["depth"]
        head = f"{ind}/* {it['name']} | {it['type']}" + (f" {it['size']}" if it["size"] else "") + (f" | id {it['id']}" if it["id"] else "") + " */"
        lines.append(head)
        if it["text"] is not None:
            lines.append(f"{ind}/* text: {json.dumps(it['text'], ensure_ascii=False)} */")
        if it.get("offset"):
            lines.append(f"{ind}/* at {it['offset']} */")
        if it["element_hint"]:
            lines.append(f"{ind}/* element: {it['element_hint']} */")
        if it["css"]:
            lines.append(f"{ind}.{it['class']} {{")
            lines += [f"{ind}  {p}: {v};" for p, v in it["css"]]
            lines.append(f"{ind}}}")
        lines += [f"{ind}/* ! {f} */" for f in it["flags"]]
    return "\n".join(lines)


def main(argv):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass
    files, opts, flags = [], {}, set()
    it = iter(argv)
    for a in it:
        if a in ("--tokens", "--node"):
            opts[a] = next(it, None)
        elif a == "--diff":
            opts[a] = (next(it, None), next(it, None))
        elif a.startswith("--"):
            flags.add(a)
        else:
            files.append(a)
    if len(files) != 1:
        print(__doc__)
        return 2
    for p in [files[0]] + ([opts["--tokens"]] if opts.get("--tokens") else []):
        if not p or not os.path.isfile(p):
            print(f"error: {p} is not a file.", file=sys.stderr)
            return 2
    try:
        with open(files[0], encoding="utf-8-sig") as fh:
            data = json.load(fh)
    except json.JSONDecodeError as e:
        print(f"error: {files[0]} is not valid JSON (line {e.lineno}: {e.msg}).", file=sys.stderr)
        return 2
    top = [n for n in roots(data) if isinstance(n, dict)]
    if not top or not any("type" in n for n in top):
        print("error: no design nodes found. Expected objects with 'type' and 'name' (a node, a list of nodes, or a 'document' / 'nodes' wrapper).", file=sys.stderr)
        return 2
    tokens = Tokens(opts.get("--tokens"))

    def translate(node):
        out, hidden = [], []
        walk(node, None, tokens, out, [], {}, hidden)
        return out, hidden

    if opts.get("--diff"):
        a, b = (find(top, n) for n in opts["--diff"])
        if not a or not b:
            print(f"error: frame not found for --diff: {opts['--diff'][0] if not a else opts['--diff'][1]}", file=sys.stderr)
            return 2
        ia, ib = translate(a)[0], translate(b)[0]
        strip = lambda items: {it["path"].split(SEP, 1)[1] if SEP in it["path"] else "(root)": it for it in items}
        ma, mb = strip(ia), strip(ib)
        print(f"/* DIFF {a.get('name')} -> {b.get('name')}: declarations that change. Write {a.get('name')} as the base and these as the override, or the reverse. */")
        for path in ma:
            if path not in mb:
                print(f"/* only in {a.get('name')}: {path} */")
                continue
            da, db = dict(ma[path]["css"]), dict(mb[path]["css"])
            bare = lambda v: v.split("/*")[0].strip() if isinstance(v, str) else v   # ignore the px note in comments
            changed = [(p, da.get(p), db.get(p)) for p in dict.fromkeys(list(da) + list(db)) if bare(da.get(p)) != bare(db.get(p))]
            if changed or ma[path]["text"] != mb[path]["text"]:
                print(f".{ma[path]['class']} {{  /* {path} */")
                for p, va, vb in changed:
                    print(f"  {p}: {va if va is not None else '(unset)'}  ->  {vb if vb is not None else '(unset)'};")
                if ma[path]["text"] != mb[path]["text"]:
                    print(f"  /* text differs: {json.dumps(ma[path]['text'], ensure_ascii=False)} -> {json.dumps(mb[path]['text'], ensure_ascii=False)} */")
                print("}")
        for path in mb:
            if path not in ma:
                print(f"/* only in {b.get('name')}: {path} */")
        return 0

    if opts.get("--node"):
        sel = find(top, opts["--node"])
        if not sel:
            print(f"error: no node named or with id '{opts['--node']}'.", file=sys.stderr)
            return 2
        top = [sel]
    all_items, all_hidden = [], []
    for n in top:
        items, hidden = translate(n)
        all_items += items
        all_hidden += hidden
    if "--json" in flags:
        print(json.dumps({"nodes": all_items, "hidden_layers_skipped": all_hidden}, indent=2, ensure_ascii=False))
        return 0
    print(render(all_items))
    n_flags = sum(len(i["flags"]) for i in all_items)
    off = sum(1 for i in all_items for f in i["flags"] if f.startswith("off-token"))
    print(f"\n/* SUMMARY: {len(all_items)} nodes, {n_flags} flags ({off} off-token values), {len(all_hidden)} hidden layer(s) skipped" + (f": {', '.join(all_hidden[:5])}" if all_hidden else "") + " */")
    print("/* NOT IN THE EXPORT: hover, focus and disabled states unless drawn as variants; behaviour; breakpoints between drawn frames; real content lengths. */")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
