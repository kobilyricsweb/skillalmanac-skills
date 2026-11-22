#!/usr/bin/env python3
"""Check saved HTML pages against a measurable technical SEO checklist (offline).

Usage:
    python seo_page_check.py <page.html | folder> [--json]

Reads:  one HTML file, or every .html/.htm file in the folder (not recursive). In a folder it
        also uses, when present:
          urls.csv     header `file,url` - the live URL each saved file came from
          robots.txt   the site's robots file
          sitemap.xml  one sitemap file (urlset)
Writes: nothing.
Network: none. Fetch the pages with your own tools first and save the raw HTML response.
Exit codes: 0 = no FAIL, 1 = at least one FAIL, 2 = input problem.

Each finding has a level (FAIL, WARN, NOTE), a rule id from references/checklist.md and a basis:
`search-engine-doc` (a documented requirement or documented behaviour) or `convention`
(an audit-tool habit with no documented rule). Do not edit this script to make a page pass.
"""
import csv
import json
import os
import re
import sys
import xml.etree.ElementTree as ET
from html.parser import HTMLParser

# Title and description ranges are audit-tool conventions tied to how much text fits in a
# result line; search engines document no character limit. They are WARN/NOTE, never FAIL.
TITLE_MIN, TITLE_MAX = 30, 60
DESC_MIN, DESC_MAX = 120, 155
# Fewer visible words than this in the raw HTML, on a page that loads scripts, usually means
# the main content is rendered client-side and is absent from the first response.
THIN_RAW_TEXT_WORDS = 50
GENERIC_ANCHORS = {"click here", "here", "read more", "learn more", "more", "this", "link"}
SKIP_TEXT_TAGS = {"script", "style", "noscript", "template", "svg", "head"}


class Page(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.titles, self.metas, self.links, self.headings, self.imgs = [], [], [], [], []
        self.anchors, self.jsonld, self.scripts_src, self.http_resources = [], [], 0, []
        self.lang, self.has_html = None, False
        self._stack, self._capture, self._buf, self._text = [], None, [], []
        self._anchor = None

    def handle_starttag(self, tag, attrs):
        a = {k.lower(): (v or "") for k, v in attrs}
        self._stack.append(tag)
        if tag == "html":
            self.has_html, self.lang = True, a.get("lang")
        elif tag == "title" and "svg" not in self._stack:
            self._capture, self._buf = "title", []
        elif tag == "meta":
            self.metas.append(a)
            self._stack.pop()
        elif tag == "link":
            self.links.append(a)
            self._stack.pop()
        elif re.fullmatch(r"h[1-6]", tag):
            self._capture, self._buf = tag, []
        elif tag == "img":
            self.imgs.append(a)
            self._stack.pop()
        elif tag == "a":
            self._anchor = {"href": a.get("href", ""), "rel": a.get("rel", ""), "text": []}
        elif tag == "script":
            if a.get("type", "").lower() == "application/ld+json":
                self._capture, self._buf = "jsonld", []
            elif a.get("src"):
                self.scripts_src += 1
        if tag in ("br", "hr", "input", "source", "wbr") and self._stack and self._stack[-1] == tag:
            self._stack.pop()
        for attr in ("src", "href"):
            if tag in ("img", "script", "iframe", "source", "video", "audio") or (tag == "link" and a.get("rel") == "stylesheet"):
                if a.get(attr, "").startswith("http://"):
                    self.http_resources.append(a[attr])

    def handle_endtag(self, tag):
        if self._capture == "title" and tag == "title":
            self.titles.append(" ".join("".join(self._buf).split()))
            self._capture = None
        elif self._capture == "jsonld" and tag == "script":
            self.jsonld.append("".join(self._buf))
            self._capture = None
        elif self._capture == tag and re.fullmatch(r"h[1-6]", tag):
            self.headings.append((int(tag[1]), " ".join("".join(self._buf).split())))
            self._capture = None
        if tag == "a" and self._anchor is not None:
            self._anchor["text"] = " ".join("".join(self._anchor["text"]).split())
            self.anchors.append(self._anchor)
            self._anchor = None
        if tag in self._stack:
            while self._stack and self._stack.pop() != tag:
                pass

    def handle_data(self, data):
        if self._capture:
            self._buf.append(data)
        if self._anchor is not None:
            self._anchor["text"].append(data)
        if not (set(self._stack) & SKIP_TEXT_TAGS):
            self._text.append(data)

    @property
    def visible_words(self):
        return len(" ".join(self._text).split())

    def meta(self, name, key="name"):
        return [m.get("content", "") for m in self.metas if m.get(key, "").lower() == name]


URL_RE = re.compile(r"^([A-Za-z][A-Za-z0-9+.-]*)://([^/?#]*)([^?#]*)(?:\?([^#]*))?")


def split_url(url):
    """(scheme, host, path, query) without importing a network-capable module."""
    m = URL_RE.match(url.strip())
    if not m:
        return "", "", url.strip(), ""
    return m.group(1).lower(), m.group(2).lower(), m.group(3) or "/", m.group(4) or ""


def norm_url(url):
    scheme, host, path, query = split_url(url)
    return "%s://%s%s%s" % (scheme, host, path, ("?" + query) if query else "")


def parse_robots(text):
    """Return {agent_token_lower: [(allow_bool, path_pattern), ...]} following RFC 9309 grouping."""
    groups, agents, in_rules = {}, [], False
    for raw in text.splitlines():
        line = raw.split("#", 1)[0].strip()
        if ":" not in line:
            continue
        field, value = [s.strip() for s in line.split(":", 1)]
        field = field.lower()
        if field == "user-agent":
            if in_rules:
                agents, in_rules = [], False
            agents.append(value.lower())
            groups.setdefault(value.lower(), [])
        elif field in ("allow", "disallow"):
            in_rules = True
            for agent in agents:
                if value or field == "allow":
                    groups[agent].append((field == "allow", value))
    return groups


def robots_allows(groups, agent, path):
    rules = groups.get(agent.lower())
    if rules is None:
        rules = groups.get("*", [])
    best = (-1, True)
    for allow, pattern in rules:
        if not pattern:
            continue
        rx = "^" + re.escape(pattern).replace(r"\*", ".*")
        if rx.endswith(r"\$"):
            rx = rx[:-2] + "$"
        if re.match(rx, path):
            length = len(pattern)
            if length > best[0] or (length == best[0] and allow):
                best = (length, allow)
    return best[1]


def read_text(path):
    raw = open(path, "rb").read()
    for enc in ("utf-8-sig", "cp1252"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", "replace")


def main(argv):
    args = [a for a in argv if not a.startswith("--")]
    if len(args) != 1 or not os.path.exists(args[0]):
        print(__doc__)
        return 2
    target = args[0]
    folder = target if os.path.isdir(target) else os.path.dirname(os.path.abspath(target))
    files = sorted(f for f in os.listdir(target) if f.lower().endswith((".html", ".htm"))) if os.path.isdir(target) \
        else [os.path.basename(target)]
    if not files:
        sys.stderr.write("ERROR: no .html or .htm files in %s. Save the raw HTML of each page there first.\n" % target)
        return 2

    url_of = {}
    map_path = os.path.join(folder, "urls.csv")
    if os.path.isfile(map_path):
        for row in csv.DictReader(open(map_path, encoding="utf-8-sig", newline="")):
            if row.get("file") and row.get("url"):
                url_of[row["file"].strip()] = norm_url(row["url"])
    robots = parse_robots(read_text(os.path.join(folder, "robots.txt"))) if os.path.isfile(os.path.join(folder, "robots.txt")) else None
    sitemap_urls, sitemap_lastmods, sitemap_error = [], [], None
    sm_path = os.path.join(folder, "sitemap.xml")
    if os.path.isfile(sm_path):
        try:
            for el in ET.parse(sm_path).getroot().iter():
                tag = el.tag.split("}")[-1]
                if tag == "loc" and el.text:
                    sitemap_urls.append(norm_url(el.text))
                elif tag == "lastmod" and el.text:
                    sitemap_lastmods.append(el.text.strip())
        except ET.ParseError as exc:
            sitemap_error = str(exc)

    findings = []

    def add(level, rule, basis, where, msg):
        findings.append({"level": level, "rule": rule, "basis": basis, "page": where, "message": msg})

    pages = {}
    for name in files:
        p = Page()
        try:
            p.feed(read_text(os.path.join(folder, name)))
        except Exception as exc:  # html.parser is tolerant; this is a last resort for broken input
            add("FAIL", "P0", "convention", name, "HTML could not be parsed: %s" % exc)
            continue
        canon = [l.get("href", "") for l in p.links if "canonical" in l.get("rel", "").lower().split()]
        url = url_of.get(name)
        if not url and len(canon) == 1 and canon[0].startswith("http"):
            url = None  # unknown: do not assume the canonical is the page's own URL
        robots_meta = ",".join(p.meta("robots") + p.meta("googlebot")).lower()
        pages[name] = {"p": p, "url": url, "canon": canon, "robots_meta": robots_meta,
                       "noindex": "noindex" in robots_meta or "none" in [t.strip() for t in robots_meta.split(",")]}

    for name, d in pages.items():
        p, url, canon = d["p"], d["url"], d["canon"]
        # titles
        if not p.titles or not p.titles[0]:
            add("FAIL", "T1", "search-engine-doc", name, "no <title> element with text")
        else:
            if len(p.titles) > 1:
                add("FAIL", "T1", "search-engine-doc", name, "%d <title> elements; keep one" % len(p.titles))
            n = len(p.titles[0])
            if not TITLE_MIN <= n <= TITLE_MAX:
                add("WARN", "T2", "convention", name, "title is %d characters (convention %d-%d): '%s'" % (n, TITLE_MIN, TITLE_MAX, p.titles[0][:70]))
        # description
        descs = p.meta("description")
        if not descs or not descs[0].strip():
            add("WARN", "D1", "search-engine-doc", name, "no meta description (the engine will write its own snippet)")
        else:
            if len(descs) > 1:
                add("WARN", "D1", "convention", name, "%d meta descriptions; keep one" % len(descs))
            n = len(descs[0].strip())
            if not DESC_MIN <= n <= DESC_MAX:
                add("NOTE", "D2", "convention", name, "meta description is %d characters (convention %d-%d; no documented limit)" % (n, DESC_MIN, DESC_MAX))
        # headings
        h1s = [h for h in p.headings if h[0] == 1]
        if len(h1s) != 1:
            add("WARN", "H1", "convention", name, "%d <h1> elements (expected exactly 1)" % len(h1s))
        prev = 0
        for level, text in p.headings:
            if prev and level > prev + 1:
                add("WARN", "H2", "convention", name, "heading level skips from h%d to h%d at '%s'" % (prev, level, text[:50]))
                break
            prev = level
        # canonical
        distinct = sorted(set(canon))
        if not canon:
            add("WARN", "C1", "search-engine-doc", name, "no rel=canonical link")
        elif len(distinct) > 1:
            add("FAIL", "C2", "search-engine-doc", name, "conflicting canonicals: %s" % ", ".join(distinct))
        else:
            c = distinct[0]
            if not c.startswith(("http://", "https://")):
                add("WARN", "C3", "search-engine-doc", name, "canonical is not an absolute URL: '%s'" % c)
            elif url and norm_url(c) != url:
                add("NOTE", "C4", "search-engine-doc", name, "canonical points to another URL (%s); this page is asking not to be the indexed version" % c)
                if split_url(c)[1] != split_url(url)[1]:
                    add("WARN", "C7", "search-engine-doc", name, "canonical points to a different host (%s); if this is a staging or old domain the live page will not be indexed" % split_url(c)[1])
            if d["noindex"] and url and c.startswith("http") and norm_url(c) != url:
                add("FAIL", "C5", "search-engine-doc", name, "noindex together with a canonical to another URL: mixed signals; pick one")
            if c.startswith("http://"):
                add("WARN", "C3", "search-engine-doc", name, "canonical uses http, not https")
        # robots meta
        if d["noindex"]:
            add("NOTE", "R1", "search-engine-doc", name, "page is noindex (robots meta: '%s'); confirm this is intended" % d["robots_meta"])
        if "nosnippet" in d["robots_meta"] or "max-snippet:0" in d["robots_meta"].replace(" ", ""):
            add("WARN", "R2", "search-engine-doc", name, "nosnippet / max-snippet:0 removes the text snippet and eligibility for AI answer features")
        # document basics
        if not p.lang:
            add("WARN", "L1", "convention", name, "<html> has no lang attribute")
        if not p.meta("viewport"):
            add("WARN", "V1", "search-engine-doc", name, "no viewport meta tag (mobile rendering)")
        missing_og = [k for k in ("og:title", "og:description", "og:image") if not p.meta(k, "property")]
        if missing_og:
            add("NOTE", "O1", "convention", name, "missing Open Graph tags: %s" % ", ".join(missing_og))
        # images
        no_alt = [i for i in p.imgs if "alt" not in i]
        if no_alt:
            add("WARN", "I1", "search-engine-doc", name, "%d of %d <img> have no alt attribute (first: %s)" % (len(no_alt), len(p.imgs), no_alt[0].get("src", "")[:60]))
        no_size = [i for i in p.imgs if not (i.get("width") and i.get("height"))]
        if no_size:
            add("NOTE", "I2", "search-engine-doc", name, "%d <img> without width and height (layout shift risk)" % len(no_size))
        # structured data syntax
        for block in p.jsonld:
            try:
                json.loads(block)
            except ValueError as exc:
                add("FAIL", "J1", "search-engine-doc", name, "a JSON-LD block does not parse: %s" % exc)
        # rendering
        if p.visible_words < THIN_RAW_TEXT_WORDS and p.scripts_src:
            add("WARN", "B1", "search-engine-doc", name, "only %d visible words in the raw HTML and %d external scripts: main content may exist only after JavaScript runs" % (p.visible_words, p.scripts_src))
        if p.http_resources:
            add("WARN", "M1", "search-engine-doc", name, "%d resources loaded over http (mixed content), first: %s" % (len(p.http_resources), p.http_resources[0][:70]))
        generic = [a["text"] for a in p.anchors if a["text"].lower() in GENERIC_ANCHORS and a["href"]]
        if generic:
            add("NOTE", "A1", "search-engine-doc", name, "%d links with generic anchor text ('%s')" % (len(generic), generic[0]))
        # hreflang
        alts = [(l.get("hreflang", "").lower(), l.get("href", "")) for l in p.links if "alternate" in l.get("rel", "").lower().split() and l.get("hreflang")]
        if alts:
            if url and url not in [norm_url(h) for _, h in alts if h.startswith("http")]:
                add("WARN", "X1", "search-engine-doc", name, "hreflang set has no self-reference")
            if "x-default" not in [c for c, _ in alts]:
                add("NOTE", "X2", "search-engine-doc", name, "hreflang set has no x-default")
            d["alts"] = {norm_url(h) for _, h in alts if h.startswith("http")}
        # robots.txt and sitemap cross-checks
        if url:
            path = split_url(url)[2]
            blocked = robots is not None and not robots_allows(robots, "googlebot", path)
            in_sitemap = url in sitemap_urls
            if blocked and in_sitemap:
                add("FAIL", "S2", "search-engine-doc", name, "URL is in the sitemap but robots.txt blocks crawling it")
            if blocked and d["noindex"]:
                add("WARN", "R3", "search-engine-doc", name, "robots.txt blocks the URL, so the noindex on it cannot be read")
            if blocked and not in_sitemap and not d["noindex"]:
                add("NOTE", "R4", "search-engine-doc", name, "robots.txt blocks crawling this URL; confirm this is intended")
            if in_sitemap and d["noindex"]:
                add("FAIL", "S1", "search-engine-doc", name, "URL is in the sitemap but the page is noindex")
            if in_sitemap and len(distinct) == 1 and distinct[0].startswith("http") and norm_url(distinct[0]) != url:
                add("FAIL", "S3", "search-engine-doc", name, "URL is in the sitemap but its canonical points elsewhere (%s)" % distinct[0])

    # cross-page checks
    by_url = {d["url"]: n for n, d in pages.items() if d["url"]}
    for label, rule, level, getter in (("title", "T3", "FAIL", lambda d: d["p"].titles[0] if d["p"].titles else ""),
                                       ("meta description", "D3", "WARN", lambda d: (d["p"].meta("description") or [""])[0].strip())):
        seen = {}
        for n, d in pages.items():
            if d["noindex"]:
                continue
            v = getter(d).lower()
            if v:
                seen.setdefault(v, []).append(n)
        for v, names in seen.items():
            if len(names) > 1:
                add(level, rule, "search-engine-doc", ", ".join(names), "duplicate %s on %d indexable pages: '%s'" % (label, len(names), v[:60]))
    for n, d in pages.items():
        for c in set(d["canon"]):
            target_name = by_url.get(norm_url(c)) if c.startswith("http") else None
            if target_name and target_name != n and pages[target_name]["noindex"]:
                add("FAIL", "C6", "search-engine-doc", n, "canonical target %s is noindex" % target_name)
        for alt in d.get("alts", ()):
            other = by_url.get(alt)
            if other and other != n and d["url"] not in pages[other].get("alts", ()):
                add("WARN", "X3", "search-engine-doc", n, "hreflang points to %s but that page does not link back" % other)
    if sitemap_error:
        add("FAIL", "S0", "search-engine-doc", "sitemap.xml", "sitemap does not parse: %s" % sitemap_error)
    if len(sitemap_lastmods) > 3 and len(set(sitemap_lastmods)) == 1:
        add("WARN", "S4", "search-engine-doc", "sitemap.xml", "all %d lastmod values are identical (%s); lastmod is only used when it is consistently accurate" % (len(sitemap_lastmods), sitemap_lastmods[0]))
    for u in sitemap_urls:
        if not u.startswith("https://"):
            add("WARN", "S5", "search-engine-doc", "sitemap.xml", "sitemap URL is not https: %s" % u)
    if robots is not None and not robots_allows(robots, "googlebot", "/"):
        add("FAIL", "R0", "search-engine-doc", "robots.txt", "robots.txt blocks the whole site for search crawlers")

    order = {"FAIL": 0, "WARN": 1, "NOTE": 2}
    findings.sort(key=lambda f: (order[f["level"]], f["rule"], f["page"]))
    counts = {k: sum(1 for f in findings if f["level"] == k) for k in order}
    not_checked = ["status codes, redirects and redirect chains (needs live requests)",
                   "rendered DOM against raw HTML (needs a browser)",
                   "Core Web Vitals field data and lab scores",
                   "internal link graph: orphans, click depth, broken links (needs a crawl)",
                   "index coverage and manual actions (needs the search engine's console)",
                   "structured-data eligibility beyond JSON syntax",
                   "pages not saved into the folder"]
    if not url_of:
        not_checked.insert(0, "self-canonical, sitemap and robots.txt cross-checks (no urls.csv mapping files to URLs)")
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if "--json" in argv:
        print(json.dumps({"pages": len(pages), "counts": counts, "findings": findings, "not_checked": not_checked}, indent=2))
    else:
        print("TECHNICAL SEO CHECK: %d pages, %d FAIL, %d WARN, %d NOTE" % (len(pages), counts["FAIL"], counts["WARN"], counts["NOTE"]))
        for f in findings:
            print("%-4s %-3s [%s] %s: %s" % (f["level"], f["rule"], f["basis"], f["page"], f["message"]))
        print("\nNot checked by this script:")
        for line in not_checked:
            print("  - " + line)
    return 1 if counts["FAIL"] else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
