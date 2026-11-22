#!/usr/bin/env python3
"""Static accessibility checker for HTML files (standard library only).

Usage:
    python a11y_static_check.py page.html [more.html ...] [--json]

Reads each HTML file plus its inline <style> blocks and locally linked CSS
files. Writes nothing. Uses no network. Reports machine-detectable problems
mapped to WCAG 2.2 success criteria, then lists what a static read cannot see.

Levels:
    FAIL  a defect that can be decided from the source
    WARN  a likely defect that needs a human look

Exit codes: 0 = no FAIL, 1 = at least one FAIL, 2 = usage or read error.

It does not execute JavaScript, does not render, and does not resolve the CSS
cascade. A clean run is not a conformance claim.
"""
import json
import os
import re
import sys
from html.parser import HTMLParser

VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr"}
NATIVE_FOCUSABLE = {"button", "select", "textarea", "summary"}
# Non-abstract WAI-ARIA 1.2 roles (plus "image", the 1.3 synonym of img).
ROLES = set("""alert alertdialog application article banner blockquote button caption cell checkbox code
columnheader combobox complementary contentinfo definition deletion dialog directory document emphasis feed
figure form generic grid gridcell group heading img image insertion link list listbox listitem log main
marquee math menu menubar menuitem menuitemcheckbox menuitemradio meter navigation none note option
paragraph presentation progressbar radio radiogroup region row rowgroup rowheader scrollbar search
searchbox separator slider spinbutton status strong subscript superscript switch tab table tablist
tabpanel term textbox time timer toolbar tooltip tree treegrid treeitem""".split())
ARIA_ATTRS = set("""activedescendant atomic autocomplete braillelabel brailleroledescription busy checked
colcount colindex colindextext colspan controls current describedby description details disabled
dropeffect errormessage expanded flowto grabbed haspopup hidden invalid keyshortcuts label labelledby
level live modal multiline multiselectable orientation owns placeholder posinset pressed readonly
relevant required roledescription rowcount rowindex rowindextext rowspan selected setsize sort valuemax
valuemin valuenow valuetext""".split())
ID_REF_ATTRS = ("aria-labelledby", "aria-describedby", "aria-controls", "aria-owns", "aria-errormessage",
                "aria-activedescendant", "aria-details", "aria-flowto")
GENERIC_LINK_TEXT = {"click here", "here", "read more", "learn more", "more", "link", "details", "this", "continue", "more info"}
# Fields that collect data about the user need an autocomplete token (WCAG 1.3.5).
PERSONAL = re.compile(r"e-?mail|phone|\btel\b|first.?name|last.?name|full.?name|\bname\b|address|zip|postal|\bcity\b|country|cc-?num|card.?number", re.I)
NAMED = {"black": "#000000", "white": "#ffffff", "red": "#ff0000", "green": "#008000", "blue": "#0000ff",
         "gray": "#808080", "grey": "#808080", "silver": "#c0c0c0", "yellow": "#ffff00", "orange": "#ffa500",
         "lightgray": "#d3d3d3", "lightgrey": "#d3d3d3", "darkgray": "#a9a9a9", "darkgrey": "#a9a9a9",
         "navy": "#000080", "purple": "#800080", "teal": "#008080", "maroon": "#800000", "whitesmoke": "#f5f5f5",
         "gainsboro": "#dcdcdc", "dimgray": "#696969", "dimgrey": "#696969", "transparent": None}
AA_TEXT = 4.5      # WCAG 1.4.3 normal text
AA_LARGE = 3.0     # WCAG 1.4.3 large text (24px, or 18.66px bold)
MIN_TARGET = 24    # WCAG 2.5.8 minimum target size in CSS px


class Node:
    __slots__ = ("tag", "attrs", "parent", "children", "text", "line")

    def __init__(self, tag, attrs, parent, line):
        self.tag, self.attrs, self.parent, self.line = tag, attrs, parent, line
        self.children, self.text = [], ""

    def get(self, name, default=None):
        return self.attrs.get(name, default)

    def has(self, name):
        return name in self.attrs

    def walk(self):
        yield self
        for c in self.children:
            if isinstance(c, Node):
                yield from c.walk()

    def ancestors(self):
        p = self.parent
        while p is not None:
            yield p
            p = p.parent


class Dom(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = Node("#root", {}, None, 0)
        self.cur = self.root
        self.styles = []
        self._in_style = False

    def handle_starttag(self, tag, attrs):
        node = Node(tag, {k.lower(): (v if v is not None else "") for k, v in attrs}, self.cur, self.getpos()[0])
        self.cur.children.append(node)
        if tag == "style":
            self._in_style = True
        if tag not in VOID:
            self.cur = node

    def handle_startendtag(self, tag, attrs):
        node = Node(tag, {k.lower(): (v if v is not None else "") for k, v in attrs}, self.cur, self.getpos()[0])
        self.cur.children.append(node)

    def handle_endtag(self, tag):
        if tag == "style":
            self._in_style = False
        n = self.cur
        while n is not None and n.tag != tag:
            n = n.parent
        if n is not None and n.parent is not None:
            self.cur = n.parent

    def handle_data(self, data):
        if self._in_style:
            self.styles.append(data)
        else:
            self.cur.children.append(data)


def hidden(node):
    return node.get("aria-hidden") == "true" or node.has("hidden") or re.search(r"display\s*:\s*none", node.get("style", ""))


def text_of(node, ids=None):
    """Text content the way a name computation sees it: skips hidden parts, uses alt and aria-label."""
    out = []
    for c in node.children:
        if isinstance(c, str):
            out.append(c)
        elif c.tag in ("script", "style") or hidden(c):
            continue
        elif c.get("aria-label", "").strip():
            out.append(c.get("aria-label"))
        elif c.tag == "img":
            out.append(c.get("alt", ""))
        elif c.tag == "svg":
            out.extend(text_of(t) for t in c.children if isinstance(t, Node) and t.tag == "title")
        else:
            out.append(text_of(c, ids))
    return re.sub(r"\s+", " ", " ".join(out)).strip()


def labelledby_text(node, ids):
    refs = node.get("aria-labelledby", "").split()
    return " ".join(text_of(ids[r][0]) for r in refs if r in ids).strip()


def acc_name(node, ids, labels_for):
    if node.get("aria-labelledby"):
        t = labelledby_text(node, ids)
        if t:
            return t
    if node.get("aria-label", "").strip():
        return node.get("aria-label").strip()
    if node.tag in ("input", "select", "textarea"):
        if node.get("id") in labels_for and text_of(labels_for[node.get("id")]):
            return text_of(labels_for[node.get("id")])
        for a in node.ancestors():
            if a.tag == "label" and text_of(a):
                return text_of(a)
        if node.tag == "input" and node.get("type", "").lower() in ("submit", "button", "reset"):
            return node.get("value", "").strip() or ("Submit" if node.get("type", "").lower() == "submit" else "")
        if node.tag == "input" and node.get("type", "").lower() == "image":
            return node.get("alt", "").strip()
        return ""
    t = text_of(node)
    return t or node.get("title", "").strip()


# ---------- CSS ----------

def parse_color(val, variables=None, depth=0):
    if val is None:
        return None
    val = val.strip().lower()
    val = re.sub(r"\s*!important", "", val)
    m = re.match(r"var\(\s*(--[\w-]+)\s*(?:,\s*([^)]+))?\)", val)
    if m and depth < 6:
        ref = (variables or {}).get(m.group(1), m.group(2))
        return parse_color(ref, variables, depth + 1)
    if val in NAMED:
        val = NAMED[val]
        if val is None:
            return None
    m = re.match(r"#([0-9a-f]{3,8})$", val)
    if m:
        h = m.group(1)
        if len(h) in (3, 4):
            h = "".join(ch * 2 for ch in h)
        if len(h) == 8 and h[6:] != "ff":
            return None  # translucent: cannot be measured without the backdrop
        if len(h) in (6, 8):
            return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))
        return None
    m = re.match(r"rgba?\(([^)]+)\)", val)
    if m:
        parts = [p for p in re.split(r"[,\s/]+", m.group(1).strip()) if p]
        try:
            if len(parts) >= 4 and float(parts[3].rstrip("%")) not in (1.0, 100.0):
                return None
            return tuple(int(round(float(p.rstrip("%")) * (2.55 if p.endswith("%") else 1))) for p in parts[:3])
        except ValueError:
            return None
    return None


def luminance(rgb):
    def ch(v):
        v = v / 255.0
        return v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4
    r, g, b = (ch(v) for v in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a, b):
    la, lb = sorted((luminance(a), luminance(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def css_rules(css):
    """Yield (selector, {prop: value}, in_reduced_motion). Flattens @media and similar blocks."""
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)

    def block(text, reduced):
        i, n = 0, len(text)
        while i < n:
            j = text.find("{", i)
            if j == -1:
                return
            head = text[i:j].strip()
            depth, k = 1, j + 1
            while k < n and depth:
                depth += {"{": 1, "}": -1}.get(text[k], 0)
                k += 1
            body = text[j + 1:k - 1]
            if head.startswith("@"):
                if not head.startswith(("@font-face", "@keyframes", "@-webkit-keyframes", "@page")):
                    yield from block(body, reduced or "prefers-reduced-motion" in head)
            else:
                decl = {}
                for part in body.split(";"):
                    if ":" in part:
                        p, v = part.split(":", 1)
                        decl[p.strip().lower()] = v.strip()
                yield head, decl, reduced
            i = k

    yield from block(css, False)


def px(val):
    m = re.match(r"\s*([\d.]+)\s*(px|rem|em|pt)?\s*(?:!important)?$", val or "")
    if not m:
        return None
    n = float(m.group(1))
    return n * {"px": 1, None: 1, "rem": 16, "em": 16, "pt": 4 / 3}[m.group(2)]


def check_css(css, add, source):
    rules = list(css_rules(css))
    variables = {}
    for sel, decl, _ in rules:
        if re.search(r":root|^html\b|^body\b", sel):
            variables.update({k: v for k, v in decl.items() if k.startswith("--")})
    page_bg, page_fg = (255, 255, 255), (0, 0, 0)
    for sel, decl, _ in rules:
        if re.fullmatch(r"(html|body|:root)(\s*,\s*(html|body|:root))*", sel.strip()):
            page_bg = parse_color(decl.get("background-color") or (decl.get("background", "").split() or [None])[0], variables) or page_bg
            page_fg = parse_color(decl.get("color"), variables) or page_fg
    if contrast(page_fg, page_bg) < AA_TEXT:
        add("FAIL", "1.4.3", "AA", "contrast", 0, f"{source}: page text {contrast(page_fg, page_bg):.2f}:1 against the page background (needs {AA_TEXT}:1)",
            "Darken the text colour or lighten the background until the ratio is at least 4.5:1.")
    has_focus_visible = any(":focus-visible" in s or (":focus" in s and ("outline" in d or "box-shadow" in d or "border" in d)
                                                     and not re.match(r"(none|0)\b", d.get("outline", "x")))
                            for s, d, _ in rules)
    has_scroll_padding = any("scroll-padding-top" in d or "scroll-margin-top" in d or "scroll-padding" in d for _, d, _ in rules)
    has_reduced = any(r for _, _, r in rules)
    motion_seen = False
    for sel, decl, reduced in rules:
        fg = parse_color(decl.get("color"), variables)
        bg_raw = decl.get("background-color") or (re.split(r"\s+", decl.get("background", "")) or [None])[0]
        bg = parse_color(bg_raw, variables) if bg_raw else None
        is_page_rule = re.fullmatch(r"(html|body|:root)(\s*,\s*(html|body|:root))*", sel.strip()) is not None
        if fg and not is_page_rule and not re.search(r"::?(selection|marker)", sel):
            size = px(decl.get("font-size", "")) or 16
            bold = re.search(r"\b(bold|[6-9]00)\b", decl.get("font-weight", "")) is not None
            need = AA_LARGE if size >= 24 or (size >= 18.66 and bold) else AA_TEXT
            if bg:
                ratio = contrast(fg, bg)
                if ratio < need:
                    add("FAIL", "1.4.3", "AA", "contrast", 0, f"{source}: `{sel}` text {ratio:.2f}:1 on its own background (needs {need}:1)",
                        "Change the text or background colour of this rule until the ratio passes.")
            elif "gradient" not in decl.get("background", "") and "url(" not in decl.get("background", "") + decl.get("background-image", ""):
                ratio = contrast(fg, page_bg)
                if ratio < need:
                    kind = "placeholder text" if "placeholder" in sel else "text"
                    add("WARN", "1.4.3", "AA", "contrast-page-bg", 0,
                        f"{source}: `{sel}` {kind} {ratio:.2f}:1 if it sits on the page background (needs {need}:1)",
                        "Confirm the real background behind this text; if it is the page background, darken the colour.")
        if re.match(r"(none|0)\b", decl.get("outline", "x")) or decl.get("outline-width", "").strip() in ("0", "0px") or decl.get("outline-style") == "none":
            replaced = any(k in decl for k in ("box-shadow", "border", "border-color", "background", "background-color", "text-decoration"))
            if not replaced:
                level = "WARN" if has_focus_visible else "FAIL"
                add(level, "2.4.7", "AA", "focus-removed", 0, f"{source}: `{sel}` removes the focus outline with no replacement in the same rule",
                    "Delete the outline reset or add a visible :focus-visible style (2px outline with 3:1 contrast).")
        if re.match(r"(sticky|fixed)", decl.get("position", "")) and not has_scroll_padding and re.match(r"0", decl.get("top", "x")):
            add("WARN", "2.4.11", "AA", "focus-obscured", 0, f"{source}: `{sel}` is pinned to the top and no scroll-padding-top is set, so focused elements can end up hidden under it",
                "Set scroll-padding-top on html to the height of the pinned bar.")
        if re.search(r"(^|[\s,>+~])(a|button)\b|\.btn|icon|close|toggle", sel) and "::" not in sel:
            w, h = px(decl.get("width", "")), px(decl.get("height", ""))
            if w is not None and h is not None and (w < MIN_TARGET or h < MIN_TARGET):
                add("WARN", "2.5.8", "AA", "target-size", 0, f"{source}: `{sel}` is {w:g}x{h:g}px, under the 24x24px minimum target",
                    "Make the control at least 24x24px (44x44px for primary touch controls) or add padding.")
        if not reduced and (("animation" in decl and not re.match(r"none", decl["animation"])) or "animation-name" in decl):
            motion_seen = True
        if re.search(r"justify", decl.get("text-align", "")):
            add("WARN", "1.4.8", "AAA", "justified-text", 0, f"{source}: `{sel}` justifies text (advisory, level AAA)", "Use left alignment for running text.")
    if motion_seen and not has_reduced:
        add("WARN", "2.3.3", "AAA", "reduced-motion", 0, f"{source}: animations are defined and there is no prefers-reduced-motion rule (advisory; 2.2.2 applies if anything moves for over 5 seconds)",
            "Wrap non-essential animation in @media (prefers-reduced-motion: no-preference) or disable it under reduce.")


# ---------- HTML ----------

def is_focusable(n):
    if n.has("tabindex") and n.get("tabindex").strip() != "-1":
        return True
    if n.tag in NATIVE_FOCUSABLE or (n.tag == "input" and n.get("type", "").lower() != "hidden"):
        return not n.has("disabled")
    return n.tag in ("a", "area") and n.has("href")


def check_html(dom, add):
    nodes = list(dom.root.walk())[1:]
    ids = {}
    for n in nodes:
        if n.get("id"):
            ids.setdefault(n.get("id"), []).append(n)
    labels_for = {n.get("for"): n for n in nodes if n.tag == "label" and n.get("for")}
    referenced = set(labels_for)
    for n in nodes:
        for a in ID_REF_ATTRS:
            referenced.update(n.get(a, "").split())

    html = next((n for n in nodes if n.tag == "html"), None)
    if html is None or not html.get("lang", "").strip():
        add("FAIL", "3.1.1", "A", "page-lang", 1, "the html element has no lang attribute", 'Add lang to the html element, for example lang="en".')
    elif not re.fullmatch(r"[a-zA-Z]{2,3}(-[a-zA-Z0-9]{2,8})*", html.get("lang").strip()):
        add("WARN", "3.1.1", "A", "page-lang", html.line, f'lang="{html.get("lang")}" is not a valid language tag', "Use a BCP 47 tag such as en or pt-BR.")
    title = next((n for n in nodes if n.tag == "title" and any(a.tag == "head" for a in n.ancestors())), None)
    if title is None or not text_of(title):
        add("FAIL", "2.4.2", "A", "page-title", 1, "the page has no title", "Add a title that names the page and the site.")
    for n in nodes:
        if n.tag == "meta" and n.get("name", "").lower() == "viewport":
            c = n.get("content", "").replace(" ", "").lower()
            m = re.search(r"maximum-scale=([\d.]+)", c)
            if "user-scalable=no" in c or "user-scalable=0" in c or (m and float(m.group(1)) < 2):
                add("FAIL", "1.4.4", "AA", "zoom-blocked", n.line, "the viewport meta tag blocks or limits pinch zoom", "Remove user-scalable=no and any maximum-scale under 2.")
        if n.tag == "meta" and n.get("http-equiv", "").lower() == "refresh":
            add("FAIL", "2.2.1", "A", "meta-refresh", n.line, "the page refreshes or redirects on a timer", "Remove the timed refresh or let the user control it.")
    if not any(n.tag == "main" or n.get("role") == "main" for n in nodes):
        add("WARN", "2.4.1", "A", "no-main", 1, "no main landmark and so no reliable way to skip repeated content", "Wrap the primary content in a main element.")

    last_level = 0
    if not any(n.tag == "h1" for n in nodes):
        add("WARN", "1.3.1", "A", "no-h1", 1, "no h1 on the page", "Give the page one h1 that matches its purpose.")
    radio_groups = {}
    for n in nodes:
        t, line = n.tag, n.line
        for a in n.attrs:
            if a.startswith("aria-") and a[5:] not in ARIA_ATTRS:
                add("FAIL", "4.1.2", "A", "aria-unknown", line, f"<{t}> has `{a}`, which is not an ARIA attribute (browsers ignore it)", "Fix the spelling, for example aria-labelledby.")
        role = n.get("role", "").strip().lower()
        if role and not all(r in ROLES or r.startswith(("doc-", "graphics-")) for r in role.split()):
            add("FAIL", "4.1.2", "A", "aria-role", line, f'<{t} role="{role}"> is not a valid role', "Use a valid role or remove the attribute.")
        for a in ID_REF_ATTRS:
            for ref in n.get(a, "").split():
                if ref not in ids:
                    add("FAIL", "1.3.1", "A", "broken-reference", line, f'<{t} {a}="{n.get(a)}"> points to id "{ref}", which does not exist', "Point the attribute at an existing id or remove it.")
        if n.get("id") and len(ids[n.get("id")]) > 1 and ids[n.get("id")][0] is n:
            lvl = "FAIL" if n.get("id") in referenced else "WARN"
            add(lvl, "1.3.1", "A", "duplicate-id", line, f'id "{n.get("id")}" is used {len(ids[n.get("id")])} times' + (" and is the target of a label or ARIA reference" if lvl == "FAIL" else ""),
                "Make every id unique.")
        if n.has("tabindex"):
            try:
                if int(n.get("tabindex")) > 0:
                    add("FAIL", "2.4.3", "A", "tabindex-positive", line, f'<{t} tabindex="{n.get("tabindex")}"> overrides the natural focus order', "Use tabindex 0 or -1 only and fix the order in the DOM.")
            except ValueError:
                pass
        if n.get("aria-hidden") == "true" and any(is_focusable(d) for d in n.walk()):
            add("FAIL", "4.1.2", "A", "hidden-focusable", line, f'<{t} aria-hidden="true"> contains or is a focusable element, so keyboard focus lands on something screen readers cannot see',
                "Remove aria-hidden, or make the content inert (the inert attribute, or tabindex -1 on each control).")
        if hidden(n) or any(hidden(a) for a in n.ancestors()):
            continue

        if t in ("h1", "h2", "h3", "h4", "h5", "h6") or role == "heading":
            level = int(t[1]) if t[0] == "h" and len(t) == 2 else int(n.get("aria-level", "2") or 2)
            if not text_of(n):
                add("FAIL", "1.3.1", "A", "empty-heading", line, f"<{t}> is empty", "Remove the empty heading or give it text.")
            if last_level and level > last_level + 1:
                add("WARN", "1.3.1", "A", "heading-skip", line, f"heading jumps from h{last_level} to h{level}: \"{text_of(n)[:50]}\"", "Use the next level down; style the size with CSS.")
            last_level = level
        if t == "img":
            alt = n.get("alt")
            if alt is None and role not in ("presentation", "none"):
                add("FAIL", "1.1.1", "A", "img-alt", line, f'<img src="{n.get("src", "")[:50]}"> has no alt attribute', 'Add alt text that says what the image conveys, or alt="" if it is decorative.')
            elif alt and (re.search(r"\.(png|jpe?g|gif|svg|webp)$", alt.strip(), re.I) or alt.strip().lower() in ("image", "photo", "picture", "img", "graphic", "icon", "logo")):
                add("WARN", "1.1.1", "A", "img-alt-quality", line, f'alt="{alt}" does not describe the image', "Describe the content or function of the image.")
        if t in ("area",) and n.has("href") and not n.get("alt", "").strip():
            add("FAIL", "1.1.1", "A", "area-alt", line, "<area> has no alt text", "Add alt text that names the link target.")
        if t == "svg" and role in ("img", "image") and not acc_name(n, ids, labels_for):
            add("FAIL", "1.1.1", "A", "svg-name", line, '<svg role="img"> has no accessible name', "Add a title child element or aria-label.")
        if t == "iframe" and not n.get("title", "").strip() and not n.get("aria-label", "").strip():
            add("FAIL", "4.1.2", "A", "iframe-title", line, "<iframe> has no title", "Add a title that describes the embedded content.")
        if t in ("marquee", "blink"):
            add("FAIL", "2.2.2", "A", "moving-content", line, f"<{t}> moves or blinks with no way to pause", "Replace it with static content.")
        if t in ("video", "audio"):
            if n.has("autoplay") and not n.has("muted"):
                add("FAIL", "1.4.2", "A", "autoplay-audio", line, f"<{t} autoplay> plays sound on load", "Remove autoplay, or start muted with visible controls.")
            if n.has("autoplay") and n.has("loop") and not n.has("controls"):
                add("WARN", "2.2.2", "A", "autoplay-loop", line, f"<{t}> autoplays in a loop with no controls", "Add controls or a pause button.")
            if t == "video" and not any(c.tag == "track" and c.get("kind", "subtitles").lower() in ("captions", "subtitles") for c in n.walk()):
                add("WARN", "1.2.2", "A", "captions", line, "<video> has no captions track", "Add a track element with kind=captions, unless the video has no speech or sound that matters.")
        if t == "table" and role not in ("presentation", "none"):
            cells = [c for c in n.walk() if c.tag in ("th", "td")]
            if cells and not any(c.tag == "th" or c.get("role") in ("columnheader", "rowheader") for c in cells):
                add("FAIL", "1.3.1", "A", "table-headers", line, "data table has no header cells", "Mark header cells with th and scope, or add role=presentation if the table is only layout.")
            elif cells and not any(c.tag == "caption" for c in n.walk()) and not n.get("aria-label") and not n.get("aria-labelledby"):
                add("WARN", "1.3.1", "A", "table-caption", line, "data table has no caption or label", "Add a caption that names the table.")
        if role in ("dialog", "alertdialog") and not (n.get("aria-label", "").strip() or labelledby_text(n, ids)):
            add("FAIL", "4.1.2", "A", "dialog-name", line, f'<{t} role="{role}"> has no accessible name', "Add aria-labelledby pointing at the dialog heading.")
        if t == "dialog" and not n.get("aria-label") and not labelledby_text(n, ids):
            add("WARN", "4.1.2", "A", "dialog-name", line, "<dialog> has no aria-labelledby or aria-label", "Point aria-labelledby at the dialog heading.")

        # --- names of controls ---
        if t == "label" and n.get("for") and n.get("for") not in ids:
            pass  # reported by the control that lacks a label
        is_field = t in ("select", "textarea") or (t == "input" and n.get("type", "text").lower() not in ("hidden", "submit", "button", "reset", "image"))
        if is_field:
            name = acc_name(n, ids, labels_for)
            if not name:
                if n.get("placeholder", "").strip():
                    add("FAIL", "3.3.2", "A", "placeholder-as-label", line, f'<{t} placeholder="{n.get("placeholder")[:40]}"> has only a placeholder as its label; it vanishes on input',
                        "Add a visible label element tied to the field with for and id.")
                elif n.get("title", "").strip():
                    add("WARN", "3.3.2", "A", "title-as-label", line, f"<{t}> is named only by a title attribute", "Add a visible label element.")
                else:
                    add("FAIL", "4.1.2", "A", "field-name", line, f'<{t} name="{n.get("name", "")}" id="{n.get("id", "")}"> has no label', "Add a label element tied to the field with for and id.")
            typ = n.get("type", "text").lower()
            hint = " ".join((n.get("name", ""), n.get("id", ""), typ if typ in ("email", "tel") else ""))
            if t == "input" and typ in ("text", "email", "tel", "") and PERSONAL.search(hint) and not n.has("autocomplete"):
                add("WARN", "1.3.5", "AA", "autocomplete", line, f'<input name="{n.get("name", n.get("id", ""))}"> collects personal data and has no autocomplete token', 'Add the matching token, for example autocomplete="email".')
            if t == "input" and typ == "password":
                if n.get("autocomplete", "").lower() == "off" or re.search(r"return\s+false|preventDefault", n.get("onpaste", "")):
                    add("FAIL", "3.3.8", "AA", "auth-paste-blocked", line, "the password field blocks paste or password managers", 'Allow paste and set autocomplete="current-password" or "new-password".')
            if n.get("aria-invalid") == "true" and not n.get("aria-describedby") and not n.get("aria-errormessage"):
                add("WARN", "3.3.1", "A", "error-not-linked", line, f"<{t} aria-invalid> is not linked to its error text", "Point aria-describedby at the element that holds the error message.")
            if t == "input" and typ == "radio" and n.get("name"):
                radio_groups.setdefault(n.get("name"), []).append(n)
            if t == "select" and re.search(r"submit\(|location", n.get("onchange", "")):
                add("WARN", "3.2.2", "A", "change-on-input", line, "<select> navigates or submits as soon as the value changes", "Add a button that applies the choice.")
        if t == "input" and n.get("type", "").lower() == "image" and not n.get("alt", "").strip():
            add("FAIL", "1.1.1", "A", "input-image-alt", line, '<input type="image"> has no alt text', "Add alt text that names the action.")
        if t == "button" or role == "button" or (t == "input" and n.get("type", "").lower() in ("submit", "button", "reset")):
            if not acc_name(n, ids, labels_for):
                add("FAIL", "4.1.2", "A", "button-name", line, f"<{t}> has no accessible name (icon-only or empty)", "Add visible text or an aria-label that says what the button does.")
        if t == "a" and n.has("href"):
            name = acc_name(n, ids, labels_for)
            if not name:
                add("FAIL", "2.4.4", "A", "link-name", line, f'<a href="{n.get("href")[:40]}"> has no accessible name', "Add link text, or alt text on the image inside it.")
            elif name.lower().strip(" .>»") in GENERIC_LINK_TEXT and not n.get("aria-describedby"):
                add("WARN", "2.4.4", "A", "link-purpose", line, f'link text "{name}" does not say where the link goes', "Write link text that names the destination.")
        if t == "a" and not n.has("href") and (n.has("onclick") or role == "button") and not n.has("tabindex"):
            add("FAIL", "2.1.1", "A", "keyboard-anchor", line, "<a> without href acts as a control but cannot be reached by keyboard", "Use a button element, or give the link a real href.")
        if n.has("onclick") and t not in ("a", "button", "input", "select", "textarea", "summary", "label", "option", "body", "html", "details", "form"):
            if not role or not n.has("tabindex"):
                add("FAIL", "2.1.1", "A", "keyboard-clickable", line, f"<{t} onclick> is clickable but has no role and tabindex, so keyboard and screen reader users cannot operate it", "Use a button element.")
            elif not (n.has("onkeydown") or n.has("onkeyup") or n.has("onkeypress")):
                add("WARN", "2.1.1", "A", "keyboard-handler", line, f"<{t} role tabindex onclick> has no key handler in the markup", "Use a button element, or confirm Enter and Space are handled in script.")
        elif role in ("button", "link", "checkbox", "switch", "tab", "menuitem", "option") and t not in ("a", "button", "input", "summary", "option") and not n.has("tabindex") and not n.has("aria-disabled"):
            add("FAIL", "2.1.1", "A", "role-not-focusable", line, f'<{t} role="{role}"> cannot receive keyboard focus', "Use the native element, or add tabindex 0 and key handling.")
        if n.has("onmouseover") and not n.has("onfocus"):
            add("WARN", "2.1.1", "A", "hover-only", line, f"<{t} onmouseover> has no keyboard equivalent (onfocus)", "Trigger the same behaviour on focus.")
        if n.get("draggable") == "true":
            add("WARN", "2.5.7", "AA", "dragging", line, f"<{t} draggable> needs a single-pointer alternative that does not require dragging", "Add buttons (move up, move down) or a menu that does the same thing.")
        style = n.get("style", "")
        if style:
            decl = dict((p.split(":", 1)[0].strip().lower(), p.split(":", 1)[1].strip()) for p in style.split(";") if ":" in p)
            fg, bg = parse_color(decl.get("color")), parse_color(decl.get("background-color") or (decl.get("background", "").split() or [None])[0])
            if fg and bg and contrast(fg, bg) < AA_TEXT:
                add("FAIL", "1.4.3", "AA", "contrast", line, f"<{t}> inline style gives text {contrast(fg, bg):.2f}:1 (needs {AA_TEXT}:1; 3:1 only for large text)", "Change the inline colours until the ratio passes.")
    for name, radios in radio_groups.items():
        if len(radios) > 1 and not any(a.tag == "fieldset" or a.get("role") in ("radiogroup", "group") for a in radios[0].ancestors()):
            add("WARN", "1.3.1", "A", "radio-group", radios[0].line, f'radio buttons named "{name}" are not grouped, so their shared question is not announced', "Wrap them in a fieldset with a legend.")


MANUAL = [
    "Keyboard: every control reachable and operable, no trap, order follows the visual order (2.1.1, 2.1.2, 2.4.3)",
    "Focus: indicator visible on every control and not hidden behind sticky or overlay content (2.4.7, 2.4.11)",
    "Scripted widgets: name, role, state updates, focus management in dialogs and menus (4.1.2, 4.1.3)",
    "Errors and status: announced without a focus change, identified in text, with a suggested fix (3.3.1, 3.3.3, 4.1.3)",
    "Meaning carried by colour, shape or position alone (1.3.3, 1.4.1)",
    "Contrast of text over images, gradients and translucent layers, and of control borders and icons (1.4.3, 1.4.11)",
    "Reflow at 320 CSS px and text resize to 200% without loss (1.4.10, 1.4.4, 1.4.12)",
    "Alt text accuracy, captions and transcripts quality (1.1.1, 1.2.x)",
    "Timing, motion and auto-updating content can be paused or extended (2.2.1, 2.2.2)",
    "Real assistive technology behaviour: not tested by any static tool",
]


def run(path):
    findings = []

    def add(level, sc, conf, code, line, msg, fix):
        findings.append({"level": level, "sc": sc, "conformance": conf, "code": code, "line": line, "message": msg, "fix": fix})

    with open(path, encoding="utf-8", errors="replace") as fh:
        source = fh.read()
    if not source.strip():
        raise ValueError("file is empty")
    dom = Dom()
    dom.feed(source)
    check_html(dom, add)
    css_parts = [("inline <style>", "\n".join(dom.styles))]
    for n in dom.root.walk():
        if n.tag == "link" and "stylesheet" in n.get("rel", "").lower():
            href = n.get("href", "")
            if re.match(r"^(https?:)?//", href):
                add("WARN", "-", "-", "remote-css", n.line, f"remote stylesheet {href[:60]} was not read; its rules are not checked", "Check that stylesheet separately.")
                continue
            local = os.path.join(os.path.dirname(os.path.abspath(path)), href.split("?")[0])
            if os.path.isfile(local):
                with open(local, encoding="utf-8", errors="replace") as fh:
                    css_parts.append((os.path.basename(local), fh.read()))
            else:
                add("WARN", "-", "-", "missing-css", n.line, f"linked stylesheet {href[:60]} was not found; its rules are not checked", "Pass the page from its real folder.")
    for name, css in css_parts:
        if css.strip():
            check_css(css, add, name)
    seen, unique = set(), []
    for f in findings:
        key = (f["code"], f["line"], f["message"])
        if key not in seen:
            seen.add(key)
            unique.append(f)
    unique.sort(key=lambda f: (f["level"] != "FAIL", f["sc"], f["line"]))
    return unique


def main(argv):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass
    paths = [a for a in argv if not a.startswith("--")]
    if not paths:
        print(__doc__)
        return 2
    results, failed = {}, False
    for p in paths:
        if not os.path.isfile(p):
            print(f"error: {p} is not a file. Pass the path of an HTML file.", file=sys.stderr)
            return 2
        try:
            results[p] = run(p)
        except ValueError as e:
            print(f"error: {p}: {e}", file=sys.stderr)
            return 2
        failed = failed or any(f["level"] == "FAIL" for f in results[p])
    if "--json" in argv:
        print(json.dumps({"files": results, "manual_checks": MANUAL}, indent=2))
        return 1 if failed else 0
    for p, items in results.items():
        print(f"== {p}")
        for f in items:
            where = f"line {f['line']}: " if f["line"] else ""
            print(f"{f['level']} [{f['sc']} {f['conformance']}] {f['code']}: {where}{f['message']}\n     fix: {f['fix']}")
        nf = sum(f["level"] == "FAIL" for f in items)
        print(f"SUMMARY {os.path.basename(p)}: {nf} FAIL, {len(items) - nf} WARN (static checks only)")
    print("\nNOT CHECKED BY THIS SCRIPT (review by hand and report as untested if not done):")
    for m in MANUAL:
        print(f"  - {m}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
