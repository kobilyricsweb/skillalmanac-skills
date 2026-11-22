#!/usr/bin/env python3
"""Audit one HTML file, one CSS file or one design-tokens JSON file against the rules in
references/rules.md. Prints a single JSON object.

    python ui_audit.py <file.html|file.css|tokens.json> [--strict]

Reads the one file it is given. Writes nothing. No network. Errors go to stderr.
The kind is chosen by extension: .html/.htm, .css, .json (design tokens).
Linked stylesheets are not followed; they are listed as an info finding.

Exit codes
    0  verdict pass or review (no FAIL findings; with --strict, no WARN either)
    1  at least one FAIL finding (with --strict, also any WARN finding)
    2  usage error, unreadable, empty or invalid file

JSON contract (schema_version 1)
    {"schema_version": 1, "command": "check", "file": str,
     "kind": "html" | "css" | "tokens",
     "verdict": "pass" | "review" | "fail",
     "counts": {"fail": int, "warn": int, "info": int},
     "findings": [{"rule": str, "severity": "fail"|"warn"|"info",
                   "line": int|null, "message": str, "evidence": str}],
     "stats": {...}}
    Findings are sorted by severity (fail, warn, info), then line, then rule.
    verdict: fail if any FAIL, review if any WARN, else pass.

The checks are surface heuristics on source text. They do not render the page, so they
cannot see computed styles, inherited backgrounds or images. A pass is not a design review.
"""
import colorsys
import json
import os
import re
import sys
from html.parser import HTMLParser

SCHEMA_VERSION = 1
SEV_ORDER = {"fail": 0, "warn": 1, "info": 2}

# Thresholds. Each has a reason; they are working values, not measured optima.
MIN_FONT_PX = 12              # below this, body-adjacent text is hard to read on phones
BODY_FONT_PX = 16             # default browser size; smaller body text needs a reason
MAX_SIZES = 8                 # a usable type scale rarely needs more than 8 steps
MIN_SIZE_RATIO = 1.1          # closer sizes read as a mistake, not a hierarchy
MAX_SIZE_RATIO = 1.7          # a larger jump leaves no mid step for secondary text
MAX_WEIGHTS = 4               # more weights stop signalling rank
MAX_FAMILIES = 3              # body, display, mono
BODY_LH_MIN, BODY_LH_MAX = 1.4, 1.8
HEADING_LH_MAX = 1.4          # tall line height on big headings looks loose
MAX_MEASURE_CH = 80           # line length above about 80 characters tires the eye
GRID = 4                      # spacing base unit in px
GRID_TOLERATED = (2, 6)       # half steps tolerated; 1px hairlines are ignored
MAX_OFFGRID_RATIO = 0.2
MAX_SPACING_VALUES = 12
MAX_COLORS = 14               # distinct colour values in one file
MAX_RADII = 4
MAX_BREAKPOINTS = 5
MIN_TARGET_PX = 40            # touch targets; 44 is the common guidance, 24 is the WCAG floor
CONTRAST_TEXT = 4.5           # WCAG 1.4.3, normal text
CONTRAST_LARGE = 3.0          # WCAG 1.4.3, large text (24px, or 18.66px bold)
EVIDENCE_MAX = 6

FILLER = [
    "lorem ipsum", "unlock the power", "seamless", "elevate your", "revolutionize",
    "supercharge", "next-generation", "next generation", "cutting-edge", "cutting edge",
    "game-changer", "game changer", "all-in-one platform", "to the next level",
    "welcome to our", "empower your", "harness the power", "reimagine",
]
INTERACTIVE_SEL = re.compile(r"(^|[\s,>+~])(a|button|input|select|textarea|summary)\b|\.btn|\.button|\[role=.?button", re.I)
NAMED = {"white": (255, 255, 255), "black": (0, 0, 0), "gray": (128, 128, 128),
         "grey": (128, 128, 128), "red": (255, 0, 0), "blue": (0, 0, 255)}
EMOJI = re.compile("[\U0001F300-\U0001FAFF☀-⛿✅✨⭐❌❤]")


class Report:
    def __init__(self):
        self.findings = []

    def add(self, rule, severity, line, message, evidence=""):
        self.findings.append({"rule": rule, "severity": severity, "line": line,
                              "message": message, "evidence": evidence})

    def sorted(self):
        return sorted(self.findings, key=lambda f: (SEV_ORDER[f["severity"]],
                      f["line"] if f["line"] is not None else 0, f["rule"]))


# ---------- colour helpers ----------

def parse_color(text):
    """Return (r, g, b, a) with a in 0..1, or None when the value is not a plain colour."""
    s = text.strip().lower()
    if s in NAMED:
        r, g, b = NAMED[s]
        return (r, g, b, 1.0)
    m = re.fullmatch(r"#([0-9a-f]{3,8})", s)
    if m:
        h = m.group(1)
        if len(h) in (3, 4):
            h = "".join(c * 2 for c in h)
        if len(h) == 6:
            h += "ff"
        if len(h) != 8:
            return None
        return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), int(h[6:8], 16) / 255.0)
    m = re.fullmatch(r"(rgba?|hsla?)\(([^)]*)\)", s)
    if not m:
        return None
    parts = [p for p in re.split(r"[\s,/]+", m.group(2).strip()) if p]
    if len(parts) < 3:
        return None
    try:
        alpha = 1.0
        if len(parts) > 3:
            alpha = float(parts[3][:-1]) / 100 if parts[3].endswith("%") else float(parts[3])
        if m.group(1).startswith("rgb"):
            vals = [float(p[:-1]) * 2.55 if p.endswith("%") else float(p) for p in parts[:3]]
            return (int(round(vals[0])), int(round(vals[1])), int(round(vals[2])), alpha)
        hue = float(parts[0].replace("deg", "")) % 360 / 360.0
        sat = float(parts[1].rstrip("%")) / 100
        lig = float(parts[2].rstrip("%")) / 100
        r, g, b = colorsys.hls_to_rgb(hue, lig, sat)
        return (int(round(r * 255)), int(round(g * 255)), int(round(b * 255)), alpha)
    except ValueError:
        return None


def luminance(rgb):
    def chan(v):
        v = v / 255.0
        return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
    return 0.2126 * chan(rgb[0]) + 0.7152 * chan(rgb[1]) + 0.0722 * chan(rgb[2])


def contrast(a, b):
    la, lb = luminance(a), luminance(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


def hex_of(rgb):
    return "#%02x%02x%02x" % tuple(rgb[:3])


def hue_sat(rgb):
    h, l, s = colorsys.rgb_to_hls(rgb[0] / 255.0, rgb[1] / 255.0, rgb[2] / 255.0)
    return h * 360, s, l


COLOR_TOKEN = re.compile(r"#[0-9a-fA-F]{3,8}\b|(?:rgba?|hsla?)\([^)]*\)")


def colors_in(value):
    out = []
    for tok in COLOR_TOKEN.findall(value):
        c = parse_color(tok)
        if c:
            out.append(c)
    return out


# ---------- CSS parsing ----------

def strip_comments(css):
    return re.sub(r"/\*.*?\*/", lambda m: re.sub(r"[^\n]", " ", m.group(0)), css, flags=re.S)


def split_decls(body):
    """Split declaration text on ';' outside parentheses and quotes. Yields (offset, text)."""
    depth, quote, start = 0, None, 0
    for i, ch in enumerate(body):
        if quote:
            if ch == quote:
                quote = None
        elif ch in "\"'":
            quote = ch
        elif ch == "(":
            depth += 1
        elif ch == ")":
            depth = max(0, depth - 1)
        elif ch == ";" and depth == 0:
            yield start, body[start:i]
            start = i + 1
    if body[start:].strip():
        yield start, body[start:]


def parse_css(css, line0=1):
    """Return a list of rules: {selector, decls [(prop, value, line)], media, keyframes, line}."""
    css = strip_comments(css)
    rules, ctx = [], []
    i, start, n = 0, 0, len(css)

    def line_at(pos):
        return line0 + css.count("\n", 0, pos)

    while i < n:
        ch = css[i]
        if ch == "{":
            prelude = css[start:i].strip()
            if prelude.startswith("@") and re.match(r"@(media|supports|layer|container|keyframes|-webkit-keyframes)", prelude, re.I):
                ctx.append(prelude)
                start = i + 1
            else:
                depth, j = 1, i + 1
                while j < n and depth:
                    depth += (css[j] == "{") - (css[j] == "}")
                    j += 1
                body = css[i + 1:j - 1]
                first = start + (len(css[start:i]) - len(css[start:i].lstrip()))
                decls = []
                if "{" not in body:  # nested rules are not parsed
                    for off, text in split_decls(body):
                        if ":" not in text:
                            continue
                        prop, _, val = text.partition(":")
                        pos = i + 1 + off + (len(text) - len(text.lstrip()))
                        decls.append((prop.strip().lower(), val.strip(), line_at(pos)))
                media = " ".join(c for c in ctx if not re.match(r"@(-webkit-)?keyframes", c, re.I)) or None
                rules.append({"selector": re.sub(r"\s+", " ", prelude), "decls": decls, "media": media,
                              "keyframes": any(re.match(r"@(-webkit-)?keyframes", c, re.I) for c in ctx),
                              "line": line_at(first)})
                i = j - 1
                start = j
        elif ch == "}":
            if ctx:
                ctx.pop()
            start = i + 1
        elif ch == ";" and not ctx and css[start:i].strip().startswith("@"):
            start = i + 1
        i += 1
    return rules


# ---------- HTML parsing ----------

class PageParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.styles, self.inline, self.links = [], [], []
        self.headings, self.text_hits, self.emoji_lines = [], [], []
        self.viewport = None
        self.signals = []
        self.counts = {"form": 0, "table": 0, "li": 0, "button": 0, "a": 0, "input": 0, "script_fetch": 0}
        self._stack = []
        self._in_style = False
        self._in_script = False
        self._in_title = False

    def handle_starttag(self, tag, attrs):
        a = {k: (v or "") for k, v in attrs}
        line = self.getpos()[0]
        if tag in self.counts:
            self.counts[tag] += 1
        if tag == "meta" and a.get("name", "").lower() == "viewport":
            self.viewport = a.get("content", "")
        if tag == "link" and "stylesheet" in a.get("rel", "").lower():
            self.links.append(a.get("href", ""))
        if tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
            self.headings.append((int(tag[1]), line))
        if "style" in a:
            self.inline.append((a["style"], line))
        for key in ("class", "id", "role", "aria-live", "aria-busy", "aria-invalid", "placeholder"):
            if key in a:
                self.signals.append((key + "=" + a[key]).lower())
        if tag == "style":
            self._in_style = True
        elif tag == "script":
            self._in_script = True
        if tag not in ("meta", "link", "br", "img", "input", "hr"):
            self._stack.append(tag)

    def handle_endtag(self, tag):
        if tag == "style":
            self._in_style = False
        elif tag == "script":
            self._in_script = False
        if tag in self._stack:
            while self._stack and self._stack.pop() != tag:
                pass

    def handle_data(self, data):
        line = self.getpos()[0]
        if self._in_style:
            self.styles.append((data, line))
            return
        if self._in_script:
            if re.search(r"\bfetch\(|XMLHttpRequest|axios", data):
                self.counts["script_fetch"] += 1
            self.signals.append(data.lower())
            return
        low = data.lower()
        self.signals.append(low)
        for phrase in FILLER:
            if phrase in low:
                self.text_hits.append((phrase, line))
        if any(t in self._stack for t in ("h1", "h2", "h3", "h4", "h5", "h6", "button", "a", "li", "th", "label")):
            if EMOJI.search(data):
                self.emoji_lines.append((line, data.strip()[:40]))


# ---------- CSS checks ----------

def px_of(value):
    m = re.fullmatch(r"(-?\d*\.?\d+)(px|rem|em|pt)", value.strip().lower())
    if not m:
        return None
    v = float(m.group(1))
    return v * {"px": 1, "rem": 16, "em": 16, "pt": 96 / 72.0}[m.group(2)]


def resolver(rules):
    light, dark = {}, {}
    for r in rules:
        is_dark = bool(r["media"] and "prefers-color-scheme" in r["media"] and "dark" in r["media"])
        for prop, val, _ in r["decls"]:
            if prop.startswith("--"):
                (dark if is_dark else light)[prop] = val
    def resolve(value, is_dark=False):
        env = dict(light)
        if is_dark:
            env.update(dark)
        for _ in range(6):
            new = re.sub(r"var\(\s*(--[\w-]+)\s*(?:,\s*([^)]*))?\)",
                         lambda m: env.get(m.group(1), m.group(2) if m.group(2) is not None else m.group(0)), value)
            if new == value:
                break
            value = new
        return value
    return resolve


def check_css(rules, rep, stats, has_html_interactive):
    resolve = resolver(rules)
    live = [r for r in rules if not r["keyframes"]]
    all_css_text_sel = " ".join(r["selector"] for r in live)

    # --- typography ---
    sizes, weights, families, clamp = {}, set(), set(), 0
    lh_issues, measure_issues = [], []
    for r in live:
        for prop, val, line in r["decls"]:
            v = resolve(val)
            if prop == "font-size" or prop == "font":
                token = v
                if prop == "font":
                    m = re.search(r"(?:^|\s)(-?\d*\.?\d+(?:px|rem|em|pt))(?:\s*/\s*[\d.]+\w*)?(?=\s)", v + " ")
                    token = m.group(1) if m else ""
                    fam = v.split(",") and re.search(r"(?:px|rem|em|pt)(?:\s*/\s*[\d.]+\w*)?\s+(.*)$", v)
                    if fam:
                        families.add(fam.group(1).split(",")[0].strip().strip("\"'").lower())
                if "clamp(" in token or "calc(" in token:
                    clamp += 1
                else:
                    px = px_of(token)
                    if px is not None:
                        sizes.setdefault(round(px, 2), line)
            elif prop == "font-weight":
                if v.isdigit():
                    weights.add(int(v))
                elif v in ("bold", "bolder"):
                    weights.add(700)
                elif v == "normal":
                    weights.add(400)
            elif prop == "font-family":
                families.add(v.split(",")[0].strip().strip("\"'").lower())
            elif prop == "line-height":
                try:
                    num = float(v)
                except ValueError:
                    continue
                sel = r["selector"].lower()
                if re.search(r"(^|[\s,])(body|html|:root|p)(?=[\s,{:]|$)", sel) and not (BODY_LH_MIN <= num <= BODY_LH_MAX):
                    lh_issues.append("%s line-height %s (line %d)" % (r["selector"], v, line))
                if re.search(r"(^|[\s,])h[1-6](?=[\s,{:]|$)", sel) and num > HEADING_LH_MAX:
                    lh_issues.append("%s line-height %s (line %d)" % (r["selector"], v, line))
            elif prop == "max-width":
                m = re.fullmatch(r"(\d*\.?\d+)ch", v.strip().lower())
                if m and float(m.group(1)) > MAX_MEASURE_CH and re.search(r"(^|[\s,])(p|article|main|\.prose|\.content)(?=[\s,{:]|$)", r["selector"].lower()):
                    measure_issues.append("%s max-width %s (line %d)" % (r["selector"], v, line))
    ordered = sorted(sizes)
    stats["font_sizes_px"] = ordered
    stats["font_weights"] = sorted(weights)
    stats["font_families"] = sorted(f for f in families if f)
    if clamp:
        rep.add("type-fluid", "info", None, "%d fluid font-size value(s) (clamp/calc) were not checked against the scale" % clamp)
    small = [(s, sizes[s]) for s in ordered if s < MIN_FONT_PX]
    if small:
        rep.add("type-min-size", "warn", small[0][1], "Font size below %dpx; keep it for legal or badge text only" % MIN_FONT_PX,
                ", ".join("%gpx" % s for s, _ in small))
    for r in live:
        if re.fullmatch(r"(html|body|:root)", r["selector"].strip().lower()):
            for prop, val, line in r["decls"]:
                if prop == "font-size":
                    px = px_of(resolve(val))
                    if px is not None and px < BODY_FONT_PX:
                        rep.add("type-body-size", "warn", line, "Body font-size is below %dpx" % BODY_FONT_PX, "%s: %s" % (r["selector"], val))
    if len(ordered) > MAX_SIZES:
        rep.add("type-scale-count", "warn", None, "%d distinct font sizes; a scale of %d or fewer steps is easier to keep consistent" % (len(ordered), MAX_SIZES),
                ", ".join("%gpx" % s for s in ordered[:12]))
    near = [(a, b) for a, b in zip(ordered, ordered[1:]) if b / a < MIN_SIZE_RATIO]
    if near:
        rep.add("type-near-duplicates", "warn", sizes[near[0][1]], "Neighbouring font sizes closer than ratio %.2f read as a mistake, not a hierarchy" % MIN_SIZE_RATIO,
                ", ".join("%g/%gpx" % p for p in near[:EVIDENCE_MAX]))
    if len(weights) > MAX_WEIGHTS:
        rep.add("type-weights", "warn", None, "%d font weights in use; limit to %d" % (len(weights), MAX_WEIGHTS), ", ".join(str(w) for w in sorted(weights)))
    fams = [f for f in families if f and not f.startswith("var(") and f not in ("inherit", "monospace", "serif", "sans-serif", "system-ui")]
    if len(set(fams)) > MAX_FAMILIES:
        rep.add("type-families", "warn", None, "%d font families; limit to %d" % (len(set(fams)), MAX_FAMILIES), ", ".join(sorted(set(fams))))
    if lh_issues:
        rep.add("type-line-height", "warn", None, "Line height outside %.1f-%.1f for body text or above %.1f for headings" % (BODY_LH_MIN, BODY_LH_MAX, HEADING_LH_MAX), "; ".join(lh_issues[:EVIDENCE_MAX]))
    if measure_issues:
        rep.add("type-measure", "warn", None, "Text column wider than %dch" % MAX_MEASURE_CH, "; ".join(measure_issues[:EVIDENCE_MAX]))

    # --- spacing ---
    values, off = [], []
    for r in live:
        for prop, val, line in r["decls"]:
            if re.match(r"(margin|padding)(-(top|right|bottom|left|inline|block)(-(start|end))?)?$|(row-|column-)?gap$", prop):
                for tok in re.split(r"\s+", resolve(val).strip()):
                    px = px_of(tok)
                    if px is None or abs(px) <= 1:
                        continue
                    px = abs(px)
                    values.append(round(px, 2))
                    if px % GRID != 0 and px not in GRID_TOLERATED:
                        off.append((round(px, 2), line))
    distinct = sorted(set(values))
    stats["spacing_values_px"] = distinct
    if len(off) >= 3 and len(off) / float(len(values)) > MAX_OFFGRID_RATIO:
        rep.add("space-grid", "warn", off[0][1], "%d of %d spacing values are off the %dpx grid" % (len(off), len(values), GRID),
                ", ".join("%gpx" % v for v in sorted(set(o[0] for o in off))[:EVIDENCE_MAX]))
    if len(distinct) > MAX_SPACING_VALUES:
        rep.add("space-distinct", "warn", None, "%d distinct spacing values; a scale needs about %d" % (len(distinct), MAX_SPACING_VALUES),
                ", ".join("%gpx" % v for v in distinct[:14]))

    # --- colour and contrast ---
    def is_dark_rule(r):
        return bool(r["media"] and "prefers-color-scheme" in r["media"] and "dark" in r["media"])

    has_dark = any(is_dark_rule(r) for r in rules)
    page_bg, page_fg = {False: None, True: None}, {False: None, True: None}
    for mode in (False, True):
        for r in live:
            if not re.fullmatch(r"(html|body|:root)", r["selector"].strip().lower()):
                continue
            if is_dark_rule(r) and not mode:
                continue
            for prop, val, _ in r["decls"]:
                if prop in ("background", "background-color", "color") and "gradient" not in val:
                    c = parse_color(resolve(val, mode))
                    if c and c[3] == 1.0:
                        (page_fg if prop == "color" else page_bg)[mode] = c
    bg_selectors = set()
    for r in live:
        if any(p in ("background", "background-color", "background-image") for p, _, _ in r["decls"]):
            for part in r["selector"].split(","):
                bg_selectors.add(part.strip().lower())
    distinct_colors = set()
    bad_contrast = []
    for r in live:
        modes = [True] if is_dark_rule(r) else [False]
        if has_dark and not is_dark_rule(r) and any("var(" in v for _, v, _ in r["decls"]):
            modes.append(True)
        for dark in modes:
            fg = bg = None
            size_px, bold = None, False
            for prop, val, line in r["decls"]:
                v = resolve(val, dark)
                if prop in ("color", "background-color", "background", "border-color", "fill", "stroke") and not dark:
                    for c in colors_in(v):
                        if c[3] > 0:
                            distinct_colors.add(hex_of(c) if c[3] == 1.0 else hex_of(c) + "/a")
                if prop == "color":
                    c = parse_color(v)
                    if c and c[3] == 1.0:
                        fg = c
                elif prop in ("background-color", "background") and "gradient" not in v and "url(" not in v:
                    c = parse_color(v)
                    if c is None and prop == "background":
                        found = colors_in(v)
                        c = found[0] if found else None
                    if c and c[3] == 1.0:
                        bg = c
                elif prop == "font-size":
                    size_px = px_of(v)
                elif prop == "font-weight":
                    bold = v in ("bold", "bolder") or (v.isdigit() and int(v) >= 700)
            assumed = False
            is_page = bool(re.fullmatch(r"(html|body|:root)", r["selector"].strip().lower()))
            if fg and not bg:
                parts = re.split(r"[\s>+~]+", r["selector"].strip().lower())
                if len(parts) > 1 and parts[0] in bg_selectors:
                    continue  # an ancestor sets its own background; not knowable from source
                bg, assumed = page_bg[dark], True
            elif bg and not fg and not is_page:
                fg, assumed = page_fg[dark], True
            if fg and bg:
                ratio = contrast(fg, bg)
                large = size_px is not None and (size_px >= 24 or (size_px >= 18.66 and bold))
                need = CONTRAST_LARGE if large else CONTRAST_TEXT
                if ratio < need:
                    bad_contrast.append((r, ratio, need, fg, bg, assumed, dark))
    stats["distinct_colors"] = len(distinct_colors)
    for r, ratio, need, fg, bg, assumed, dark in bad_contrast:
        sev = "warn" if assumed else "fail"
        note = " (background assumed from body/html; verify)" if assumed else ""
        rep.add("contrast-text", sev, r["line"], "Contrast %.2f:1 is below %.1f:1%s" % (ratio, need, note),
                "%s: %s on %s%s" % (r["selector"], hex_of(fg), hex_of(bg), " [dark scheme]" if dark else ""))
    if len(distinct_colors) > MAX_COLORS:
        rep.add("palette-size", "warn", None, "%d distinct colour values; define about 10-14 tokens and reuse them" % len(distinct_colors))

    # --- states ---
    sels = [r["selector"].lower() for r in live]
    joined = " ".join(sels)
    styled_interactive = any(INTERACTIVE_SEL.search(s) for s in sels)
    if styled_interactive or has_html_interactive:
        if ":hover" not in joined:
            rep.add("state-hover", "warn", None, "No :hover style for interactive elements")
        has_focus_vis = False
        for r in live:
            if ":focus-visible" in r["selector"].lower() or ":focus-within" in r["selector"].lower():
                if any(p in ("outline", "outline-color", "outline-width", "box-shadow", "border", "border-color", "background", "background-color") for p, _, _ in r["decls"]):
                    has_focus_vis = True
        if ":focus" not in joined:
            rep.add("state-focus", "warn", None, "No :focus or :focus-visible style; keyboard users get no position marker")
        for r in live:
            for prop, val, line in r["decls"]:
                removed = (prop == "outline" and re.match(r"(none|0)(\s|$)", val.strip().lower())) or \
                          (prop in ("outline-style",) and val.strip().lower() == "none") or \
                          (prop == "outline-width" and val.strip() in ("0", "0px"))
                if removed:
                    props = [p for p, _, _ in r["decls"]]
                    replaced = any(p in ("box-shadow", "border", "border-color") for p in props) and ":focus" in r["selector"].lower()
                    if not replaced and not has_focus_vis:
                        rep.add("focus-outline-removed", "fail", line, "Outline removed with no visible replacement focus style", "%s { %s: %s }" % (r["selector"], prop, val))
        if not re.search(r":disabled|\[disabled|\[aria-disabled", joined) and (has_html_interactive or re.search(r"button|input|\.btn", joined)):
            rep.add("state-disabled", "info", None, "No :disabled style found for buttons or inputs")
    small_targets = []
    for r in live:
        if re.search(r"(^|[\s,])(button|input|select|\.btn[\w-]*|\.button[\w-]*)(?=[\s,{:.\[]|$)", r["selector"].lower()):
            for prop, val, line in r["decls"]:
                if prop in ("height", "min-height"):
                    px = px_of(resolve(val))
                    if px is not None and px < MIN_TARGET_PX:
                        small_targets.append("%s %s: %s (line %d)" % (r["selector"], prop, val, line))
    if small_targets:
        rep.add("touch-target", "warn", None, "Control height under %dpx; 44px is the usual touch target" % MIN_TARGET_PX, "; ".join(small_targets[:EVIDENCE_MAX]))

    # --- responsive ---
    bps, mins, maxs = set(), 0, 0
    for r in live:
        if r["media"]:
            for kind, num, unit in re.findall(r"\((min|max)-width:\s*(\d*\.?\d+)(px|em|rem)\)", r["media"]):
                bps.add(float(num) * (1 if unit == "px" else 16))
                mins += kind == "min"
                maxs += kind == "max"
    stats["breakpoints_px"] = sorted(bps)
    fixed = []
    for r in live:
        props = dict((p, v) for p, v, _ in r["decls"])
        if "width" in props and "max-width" not in props:
            px = px_of(props["width"])
            if px is not None and px >= 480:
                fixed.append("%s width: %s (line %d)" % (r["selector"], props["width"], r["line"]))
    if fixed:
        rep.add("responsive-fixed-width", "warn", None, "Fixed width of 480px or more with no max-width; it overflows small screens", "; ".join(fixed[:EVIDENCE_MAX]))
    flexible = re.search(r"clamp\(|minmax\(|auto-fit|auto-fill|flex-wrap\s*:\s*wrap", " ".join(v for r in live for _, v, _ in r["decls"]) + " " + " ".join(p + ":" + v for r in live for p, v, _ in r["decls"]))
    multi_col = fixed or any(p == "display" and re.search(r"(flex|grid)", v) or p == "float" and v.strip() in ("left", "right")
                             for r in live for p, v, _ in r["decls"])
    if not bps and not flexible and multi_col:
        rep.add("responsive-none", "warn", None, "Fixed or multi-column layout with no width media queries and no intrinsic layout (wrap, auto-fit, minmax, clamp)")
    if len(bps) > MAX_BREAKPOINTS:
        rep.add("responsive-breakpoints", "warn", None, "%d distinct breakpoints; use %d or fewer" % (len(bps), MAX_BREAKPOINTS), ", ".join("%gpx" % b for b in sorted(bps)))
    if maxs >= 2 and mins == 0:
        rep.add("responsive-desktop-first", "info", None, "Only max-width queries; mobile-first (min-width) is easier to extend")

    # --- motion ---
    motion = any(p in ("animation", "animation-name", "transition", "transition-property") and not re.match(r"(none|0s?)\b", v.strip().lower())
                 for r in live for p, v, _ in r["decls"]) or any(r["keyframes"] for r in rules)
    if motion and not any(r["media"] and "prefers-reduced-motion" in r["media"] for r in rules):
        rep.add("motion-reduced", "warn", None, "Animations or transitions without a prefers-reduced-motion rule")
    for r in live:
        for prop, val, line in r["decls"]:
            if prop == "transition" and re.match(r"all\b", val.strip().lower()):
                rep.add("transition-all", "warn", line, "transition: all animates every property and causes layout work; list the properties", r["selector"])
                break

    # --- machine-made tells ---
    grads, text_grad, glass = [], [], []
    shadows, radii, centered, important = set(), set(), 0, 0
    for r in live:
        for prop, val, line in r["decls"]:
            v = resolve(val)
            important += v.count("!important")
            if "gradient(" in v and prop in ("background", "background-image"):
                cols = colors_in(v)
                purple = [c for c in cols if c[3] > 0 and 250 <= hue_sat(c)[0] <= 310 and hue_sat(c)[1] > 0.35]
                if purple and len(cols) >= 2:
                    grads.append("%s (line %d)" % (r["selector"], line))
            if prop in ("-webkit-background-clip", "background-clip") and v.strip() == "text":
                item = "%s (line %d)" % (r["selector"], line)
                if item not in text_grad:
                    text_grad.append(item)
            if prop in ("backdrop-filter", "-webkit-backdrop-filter") and "blur" in v:
                glass.append("%s (line %d)" % (r["selector"], line))
            if prop == "box-shadow" and v.strip() != "none":
                shadows.add(re.sub(r"\s+", " ", v.strip().lower()))
            if prop == "border-radius":
                for tok in v.split():
                    px = px_of(tok)
                    if px and px > 0 and px < 999:
                        radii.add(round(px, 2))
            if prop == "text-align" and v.strip() == "center":
                centered += 1
    stats["radii_px"] = sorted(radii)
    stats["shadow_values"] = len(shadows)
    if grads:
        rep.add("tell-purple-gradient", "warn", None, "Violet/indigo gradient: the most common default of generated interfaces; pick a brand colour instead", "; ".join(grads[:EVIDENCE_MAX]))
    if text_grad:
        rep.add("tell-gradient-text", "warn", None, "Gradient-filled text (background-clip: text)", "; ".join(text_grad[:EVIDENCE_MAX]))
    if len(glass) >= 3:
        rep.add("tell-glass", "warn", None, "%d blurred translucent surfaces; use at most one, for a real overlay" % len(glass), "; ".join(glass[:EVIDENCE_MAX]))
    if len(shadows) > 4:
        rep.add("tell-shadow-sprawl", "warn", None, "%d distinct box-shadow values; define 2-4 elevations" % len(shadows))
    if len(radii) > MAX_RADII:
        rep.add("tell-radius-sprawl", "warn", None, "%d distinct border radii; use %d or fewer" % (len(radii), MAX_RADII), ", ".join("%gpx" % x for x in sorted(radii)))
    if centered >= 6:
        rep.add("tell-center-everything", "warn", None, "%d rules centre text; left-align body copy and lists" % centered)
    if important > 5:
        rep.add("important-overuse", "warn", None, "%d uses of !important; fix the cascade instead" % important)


def check_html(parser, rep, stats):
    if parser.viewport is None:
        rep.add("viewport-meta", "fail", None, 'Missing <meta name="viewport" content="width=device-width, initial-scale=1>"')
    elif "width=device-width" not in parser.viewport.replace(" ", ""):
        rep.add("viewport-meta", "fail", None, "Viewport meta does not set width=device-width", parser.viewport)
    elif re.search(r"user-scalable\s*=\s*(no|0)|maximum-scale\s*=\s*1(\.0)?\b", parser.viewport):
        rep.add("viewport-zoom", "fail", None, "Viewport meta blocks pinch zoom", parser.viewport)
    h = parser.headings
    stats["headings"] = [lvl for lvl, _ in h]
    ones = [x for x in h if x[0] == 1]
    if len(ones) != 1:
        rep.add("heading-h1", "warn", ones[1][1] if len(ones) > 1 else None, "Expected exactly one h1, found %d" % len(ones))
    for (a, _), (b, line) in zip(h, h[1:]):
        if b > a + 1:
            rep.add("heading-skip", "warn", line, "Heading level jumps from h%d to h%d" % (a, b))
            break
    if len(parser.emoji_lines) >= 3:
        rep.add("tell-emoji-icons", "warn", parser.emoji_lines[0][0], "%d headings, buttons or list items start or contain emoji used as icons; use one icon set" % len(parser.emoji_lines),
                "; ".join("line %d: %s" % e for e in parser.emoji_lines[:EVIDENCE_MAX]))
    for phrase, line in parser.text_hits[:EVIDENCE_MAX]:
        rep.add("tell-filler-copy", "fail" if phrase == "lorem ipsum" else "warn", line,
                "Placeholder copy" if phrase == "lorem ipsum" else "Stock marketing phrase; say what the product does", phrase)
    sig = " ".join(parser.signals)
    c = parser.counts
    stats["counts"] = {k: v for k, v in c.items() if v}
    has_list = c["table"] > 0 or c["li"] >= 3 or re.search(r"\b(list|grid|feed|results|cards?)\b", sig)
    if has_list and not re.search(r"empty|no results|nothing (here|yet)|no (items|data|matches)", sig):
        rep.add("states-empty", "warn", None, "A list, table or grid is present but no empty state was found (explain what is missing and offer one action)")
    if c["form"] and not re.search(r"error|invalid|role=alert|aria-invalid|aria-live", sig):
        rep.add("states-error", "warn", None, "A form is present but no error state was found (message next to the field, not colour alone)")
    if (c["form"] or c["script_fetch"]) and not re.search(r"loading|skeleton|spinner|aria-busy|progress|saving|submitting", sig):
        rep.add("states-loading", "warn", None, "Forms or fetches are present but no loading state was found")
    for href in parser.links:
        rep.add("external-stylesheet", "info", None, "Linked stylesheet not audited; run the script on it separately", href)


# ---------- tokens ----------

def token_value(v):
    if isinstance(v, dict):
        v = v.get("value", v.get("$value"))
    return v if isinstance(v, str) else None


def to_px(v):
    if isinstance(v, bool):
        return None
    if isinstance(v, (int, float)):
        return float(v)
    if isinstance(v, str):
        return px_of(v) if not re.fullmatch(r"-?\d*\.?\d+", v.strip()) else float(v)
    return None


def check_tokens(data, rep, stats):
    for key in ("colors", "font_sizes", "spacing"):
        if key not in data:
            rep.add("tokens-missing", "warn", None, "Token file has no '%s' section" % key)
    allowed = {"colors", "contrast_pairs", "font_sizes", "spacing", "radius", "line_heights", "breakpoints", "$schema", "name"}
    extra = sorted(set(data) - allowed)
    if extra:
        rep.add("tokens-unknown-keys", "info", None, "Sections not checked: " + ", ".join(extra))
    colors = {}
    for name, raw in (data.get("colors") or {}).items():
        val = token_value(raw)
        c = parse_color(val) if val else None
        if c is None:
            rep.add("tokens-color-invalid", "warn", None, "Colour '%s' is not a hex, rgb or hsl value" % name, str(raw))
        else:
            colors[name] = c
    stats["color_tokens"] = len(colors)
    pairs = data.get("contrast_pairs")
    if not pairs:
        pairs = [[a, b] for a, b in (("text", "background"), ("text-muted", "background")) if a in colors and b in colors]
        if not pairs and colors:
            rep.add("contrast-pairs-missing", "warn", None, "No contrast_pairs given and no text/background tokens to check")
    results = []
    for pair in pairs:
        if not (isinstance(pair, list) and len(pair) in (2, 3) and pair[0] in colors and pair[1] in colors):
            rep.add("contrast-pair-invalid", "warn", None, "Contrast pair refers to an unknown colour token", str(pair))
            continue
        need = CONTRAST_LARGE if len(pair) == 3 and pair[2] == "large" else CONTRAST_TEXT
        ratio = contrast(colors[pair[0]], colors[pair[1]])
        results.append({"pair": pair[:2], "ratio": round(ratio, 2)})
        if ratio < need:
            rep.add("contrast-text", "fail", None, "Contrast %.2f:1 is below %.1f:1" % (ratio, need),
                    "%s (%s) on %s (%s)" % (pair[0], hex_of(colors[pair[0]]), pair[1], hex_of(colors[pair[1]])))
    stats["contrast"] = results
    chromatic = set()
    for c in colors.values():
        hue, sat, lig = hue_sat(c)
        if sat > 0.15 and 0.1 < lig < 0.95:
            chromatic.add(int(hue // 30))
    if len(chromatic) > 4:
        rep.add("palette-hues", "warn", None, "Colour tokens span %d hue families; one accent plus status colours is usually enough" % len(chromatic))
    if len(colors) > MAX_COLORS:
        rep.add("palette-size", "warn", None, "%d colour tokens; keep about 10-14" % len(colors))
    sizes = [to_px(v) for v in data.get("font_sizes", [])]
    if any(s is None for s in sizes):
        rep.add("tokens-size-invalid", "warn", None, "font_sizes must be numbers (px) or px/rem/em strings")
    sizes = sorted(set(s for s in sizes if s is not None))
    stats["font_sizes_px"] = sizes
    if sizes:
        if len(sizes) > MAX_SIZES:
            rep.add("type-scale-count", "warn", None, "%d font sizes; use %d or fewer" % (len(sizes), MAX_SIZES))
        if len(sizes) < 4:
            rep.add("type-scale-count", "warn", None, "%d font sizes; fewer than 4 leaves no room for hierarchy" % len(sizes))
        if sizes[0] < MIN_FONT_PX:
            rep.add("type-min-size", "warn", None, "Smallest font size is below %dpx" % MIN_FONT_PX, "%gpx" % sizes[0])
        if BODY_FONT_PX not in sizes:
            rep.add("type-body-size", "warn", None, "No %dpx step; body text needs a defined base size" % BODY_FONT_PX)
        ratios = [(a, b) for a, b in zip(sizes, sizes[1:])]
        near = [p for p in ratios if p[1] / p[0] < MIN_SIZE_RATIO]
        big = [p for p in ratios if p[1] / p[0] > MAX_SIZE_RATIO]
        if near:
            rep.add("type-near-duplicates", "warn", None, "Steps closer than ratio %.2f" % MIN_SIZE_RATIO, ", ".join("%g/%g" % p for p in near))
        if big:
            rep.add("type-scale-jump", "warn", None, "Steps further apart than ratio %.1f" % MAX_SIZE_RATIO, ", ".join("%g/%g" % p for p in big))
    sp = [to_px(v) for v in data.get("spacing", [])]
    sp = sorted(set(s for s in sp if s is not None and s > 0))
    stats["spacing_px"] = sp
    off = [s for s in sp if s % GRID != 0 and s not in GRID_TOLERATED]
    if off:
        rep.add("space-grid", "warn", None, "Spacing tokens off the %dpx grid" % GRID, ", ".join("%g" % s for s in off))
    if sp and len(sp) > MAX_SPACING_VALUES:
        rep.add("space-distinct", "warn", None, "%d spacing tokens; use about 8-10" % len(sp))
    if sp and len(sp) < 5:
        rep.add("space-distinct", "warn", None, "%d spacing tokens; fewer than 5 forces ad-hoc values" % len(sp))
    radii = [to_px(v) for v in data.get("radius", [])]
    radii = sorted(set(r for r in radii if r is not None and 0 < r < 999))
    if len(radii) > MAX_RADII:
        rep.add("tell-radius-sprawl", "warn", None, "%d radius tokens; use %d or fewer" % (len(radii), MAX_RADII))
    lh = data.get("line_heights") or {}
    if isinstance(lh, dict):
        body, head = lh.get("body"), lh.get("heading")
        if isinstance(body, (int, float)) and not (BODY_LH_MIN <= body <= BODY_LH_MAX):
            rep.add("type-line-height", "warn", None, "Body line height %s outside %.1f-%.1f" % (body, BODY_LH_MIN, BODY_LH_MAX))
        if isinstance(head, (int, float)) and head > HEADING_LH_MAX:
            rep.add("type-line-height", "warn", None, "Heading line height %s above %.1f" % (head, HEADING_LH_MAX))
    bps = [to_px(v) for v in data.get("breakpoints", [])]
    bps = [b for b in bps if b is not None]
    stats["breakpoints_px"] = bps
    if len(bps) > MAX_BREAKPOINTS:
        rep.add("responsive-breakpoints", "warn", None, "%d breakpoints; use %d or fewer" % (len(bps), MAX_BREAKPOINTS))
    if bps != sorted(bps):
        rep.add("responsive-breakpoints", "warn", None, "Breakpoints are not in ascending order")
    if "breakpoints" in data and not bps:
        rep.add("responsive-none", "warn", None, "Breakpoints section is empty")


# ---------- main ----------

def load_text(path):
    try:
        with open(path, "rb") as fh:
            raw = fh.read()
    except OSError as exc:
        sys.stderr.write("Cannot read %s: %s\n" % (path, exc.strerror or exc))
        return None
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        text = raw.decode("latin-1")
    if not text.strip():
        sys.stderr.write("File is empty: %s\n" % path)
        return None
    return text


def main(argv):
    args = [a for a in argv if not a.startswith("--")]
    strict = "--strict" in argv
    if len(args) != 1 or any(a.startswith("--") and a != "--strict" for a in argv):
        sys.stderr.write("Usage: ui_audit.py <file.html|file.css|tokens.json> [--strict]\n")
        return 2
    path = args[0]
    text = load_text(path)
    if text is None:
        return 2
    ext = os.path.splitext(path)[1].lower()
    rep, stats = Report(), {}
    if ext in (".html", ".htm"):
        kind = "html"
        parser = PageParser()
        parser.feed(text)
        parser.close()
        rules = []
        for css, line in parser.styles:
            rules.extend(parse_css(css, line))
        for style, line in parser.inline:
            rules.extend(parse_css("[style] {" + style + "}", line))
        check_html(parser, rep, stats)
        interactive = parser.counts["button"] + parser.counts["a"] + parser.counts["input"] > 0
        check_css(rules, rep, stats, interactive)
        if not rules and not parser.links:
            rep.add("css-none", "info", None, "No <style> blocks or inline styles found; only the markup was checked")
    elif ext == ".css":
        kind = "css"
        check_css(parse_css(text), rep, stats, False)
    elif ext == ".json":
        kind = "tokens"
        try:
            data = json.loads(text)
        except ValueError as exc:
            sys.stderr.write("Invalid JSON in %s: %s\n" % (path, exc))
            return 2
        if not isinstance(data, dict):
            sys.stderr.write("Tokens file must be a JSON object. See references/tokens-schema.md.\n")
            return 2
        check_tokens(data, rep, stats)
    else:
        sys.stderr.write("Unsupported file type '%s'. Use .html, .htm, .css or .json.\n" % ext)
        return 2
    findings = rep.sorted()
    counts = {s: sum(1 for f in findings if f["severity"] == s) for s in ("fail", "warn", "info")}
    verdict = "fail" if counts["fail"] else ("review" if counts["warn"] else "pass")
    out = {"schema_version": SCHEMA_VERSION, "command": "check", "file": os.path.basename(path), "kind": kind,
           "verdict": verdict, "counts": counts, "findings": findings, "stats": stats}
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    print(json.dumps(out, indent=2, ensure_ascii=False))
    if counts["fail"] or (strict and counts["warn"]):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
