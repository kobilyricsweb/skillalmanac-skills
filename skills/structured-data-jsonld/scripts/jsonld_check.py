#!/usr/bin/env python3
"""Check JSON-LD structured data for syntax, required properties and policy problems (offline).

Usage:
    python jsonld_check.py <page.html | markup.json> [--page-type item|list] [--json]

Reads:  an HTML file (every <script type="application/ld+json"> block is checked, and marked-up
        ratings and names are compared with the page's visible text) or a .json file holding
        one JSON-LD object or array.
        --page-type list  tells the checker the page is a category, list or comparison page,
                          where rating markup is not allowed.
Writes: nothing.
Network: none.
Exit codes: 0 = no FAIL, 1 = at least one FAIL, 2 = input problem.

The type tables below mirror references/rich-result-status.md. When the search engine changes
a feature, update both together and re-run the fixtures; do not edit the script to silence a finding.
"""
import json
import os
import re
import sys
from html.parser import HTMLParser

# Required properties for the rich result of each type. A string is a property that must be
# present; a tuple means "at least one of". Dotted names are nested properties.
REQUIRED = {
    "Product": ["name", ("review", "aggregateRating", "offers")],
    "SoftwareApplication": ["name", "offers.price", ("aggregateRating", "review")],
    "WebApplication": ["name", "offers.price", ("aggregateRating", "review")],
    "MobileApplication": ["name", "offers.price", ("aggregateRating", "review")],
    "Review": ["author", "reviewRating.ratingValue"],
    "AggregateRating": ["ratingValue", ("ratingCount", "reviewCount")],
    "VideoObject": ["name", "thumbnailUrl", "uploadDate"],
    "BreadcrumbList": ["itemListElement"],
    "Event": ["name", "startDate", "location"],
    "Recipe": ["name", "image"],
    "JobPosting": ["title", "description", "datePosted", "hiringOrganization"],
    "LocalBusiness": ["name", "address"],
    "QAPage": ["mainEntity"],
    "Question": ["name", ("acceptedAnswer", "suggestedAnswer")],
    "ProfilePage": ["mainEntity"],
    "DiscussionForumPosting": ["author", "datePublished"],
    "Dataset": ["name", "description"],
}
RECOMMENDED = {
    "Article": ["headline", "image", "datePublished", "dateModified", "author"],
    "NewsArticle": ["headline", "image", "datePublished", "dateModified", "author"],
    "BlogPosting": ["headline", "image", "datePublished", "dateModified", "author"],
    "Organization": ["name", "url", "logo"],
    "WebSite": ["name", "url"],
    "VideoObject": ["description", "duration", "contentUrl"],
    "SoftwareApplication": ["applicationCategory", "operatingSystem"],
}
# Types whose rich result was retired. The markup is harmless but earns nothing.
RETIRED = {
    "FAQPage": "FAQ rich results are no longer shown",
    "HowTo": "How-to rich results are no longer shown",
    "SpecialAnnouncement": "special announcement results are no longer shown",
    "ClaimReview": "fact-check results are being phased out",
    "Quiz": "practice-problem results are no longer shown",
}
# Types with no rich result of their own; useful as semantics only.
SEMANTIC_ONLY = {"WebPage", "CollectionPage", "ItemList", "DefinedTerm", "SoftwareSourceCode", "TechArticle",
                 "AboutPage", "ContactPage", "Person", "Offer", "ImageObject", "ListItem", "Answer", "Rating", "Thing"}
RATING_HOSTS_BLOCKED = {"Organization", "LocalBusiness"}
LIST_TYPES = {"ItemList", "CollectionPage", "SearchResultsPage"}
URL_PROPS = {"url", "image", "logo", "item", "thumbnailUrl", "contentUrl", "embedUrl", "sameAs"}
DATE_PROPS = {"datePublished", "dateModified", "uploadDate", "startDate", "endDate", "datePosted", "validThrough", "dateCreated"}
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}(T\d{2}:\d{2}(:\d{2}(\.\d+)?)?(Z|[+-]\d{2}:?\d{2})?)?$")
HAS_TZ = re.compile(r"(Z|[+-]\d{2}:?\d{2})$")


class Extract(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.blocks, self.text, self._in_ld, self._buf, self._skip = [], [], False, [], 0

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "script" and (a.get("type") or "").lower() == "application/ld+json":
            self._in_ld, self._buf = True, []
        elif tag in ("script", "style", "noscript", "template"):
            self._skip += 1

    def handle_endtag(self, tag):
        if tag == "script" and self._in_ld:
            self.blocks.append("".join(self._buf))
            self._in_ld = False
        elif tag in ("script", "style", "noscript", "template") and self._skip:
            self._skip -= 1

    def handle_data(self, data):
        if self._in_ld:
            self._buf.append(data)
        elif not self._skip:
            self.text.append(data)


def types_of(node):
    t = node.get("@type")
    if isinstance(t, str):
        return [t]
    if isinstance(t, list):
        return [x for x in t if isinstance(x, str)]
    return []


def get(node, dotted):
    cur = [node]
    for part in dotted.split("."):
        nxt = []
        for c in cur:
            if isinstance(c, dict) and part in c and c[part] not in (None, "", [], {}):
                v = c[part]
                nxt.extend(v if isinstance(v, list) else [v])
        cur = nxt
    return cur


def walk(value, path, parent_types, out):
    """Collect every typed object with its path and the types of all typed objects that contain it."""
    if isinstance(value, list):
        for i, v in enumerate(value):
            walk(v, "%s[%d]" % (path, i), parent_types, out)
    elif isinstance(value, dict):
        mine = types_of(value)
        if mine:
            out.append((path, value, parent_types))
        for k, v in value.items():
            if k != "@context":
                walk(v, path + "." + k if path else k, parent_types + mine, out)


def number(v):
    try:
        return float(str(v).replace(",", "."))
    except ValueError:
        return None


def main(argv):
    args = [a for a in argv if not a.startswith("--")]
    page_type = "item"
    if "--page-type" in argv:
        i = argv.index("--page-type")
        page_type = argv[i + 1] if i + 1 < len(argv) else ""
        args = [a for a in args if a != page_type]
        if page_type not in ("item", "list"):
            sys.stderr.write("ERROR: --page-type must be 'item' or 'list'\n")
            return 2
    if len(args) != 1 or not os.path.isfile(args[0]):
        print(__doc__)
        return 2
    raw = open(args[0], "rb").read().decode("utf-8-sig", "replace")
    is_html = not args[0].lower().endswith((".json", ".jsonld"))
    visible = None
    if is_html:
        ex = Extract()
        ex.feed(raw)
        blocks, visible = ex.blocks, " ".join(" ".join(ex.text).split())
    else:
        blocks = [raw]

    findings = []

    def add(level, code, where, msg):
        findings.append({"level": level, "code": code, "node": where, "message": msg})

    if not blocks:
        add("NOTE", "NONE", "-", "no JSON-LD block found in the file")
    nodes, top_types = [], []
    for bi, block in enumerate(blocks):
        label = "block%d" % (bi + 1)
        try:
            data = json.loads(block)
        except ValueError as exc:
            add("FAIL", "PARSE", label, "JSON does not parse: %s" % exc)
            continue
        tops = data if isinstance(data, list) else [data]
        for top in tops:
            if not isinstance(top, dict):
                add("FAIL", "PARSE", label, "top level must be an object or an array of objects")
                continue
            ctx = json.dumps(top.get("@context", ""))
            if "schema.org" not in ctx:
                add("FAIL", "CONTEXT", label, "missing \"@context\": \"https://schema.org\"")
            graph = top.get("@graph") if isinstance(top.get("@graph"), list) else [top]
            for g in graph:
                if isinstance(g, dict):
                    top_types.extend(types_of(g))
        walk(data, label, [], nodes)

    summary = []
    for path, node, parents in nodes:
        kinds = types_of(node)
        where = "%s (%s)" % (path, "/".join(kinds))
        is_ref = set(node) <= {"@id", "@type", "name", "url"} and "@id" in node
        for kind in kinds:
            if kind in RETIRED:
                add("WARN", "RETIRED", where, "%s; keep it only for other consumers, expect no rich result" % RETIRED[kind])
                summary.append((where, "retired"))
            elif kind in REQUIRED and not is_ref:
                missing = []
                for req in REQUIRED[kind]:
                    if isinstance(req, tuple):
                        if not any(get(node, r) for r in req):
                            missing.append(" or ".join(req))
                    elif not get(node, req):
                        missing.append(req)
                nested_in_rated = kind in ("Review", "AggregateRating") and parents
                if kind in ("Review", "AggregateRating") and not nested_in_rated and not get(node, "itemReviewed.name"):
                    missing.append("itemReviewed.name (or nest it under the reviewed item)")
                if missing:
                    add("FAIL", "REQUIRED", where, "missing required: %s; not eligible for the rich result" % ", ".join(missing))
                    summary.append((where, "not eligible: missing required properties"))
                else:
                    summary.append((where, "required properties present"))
            elif kind in SEMANTIC_ONLY:
                summary.append((where, "semantic only, no rich result of its own"))
            for rec in RECOMMENDED.get(kind, []):
                if not is_ref and not get(node, rec):
                    add("NOTE", "RECOMMENDED", where, "recommended property missing: %s" % rec)
        # breadcrumb items
        if "BreadcrumbList" in kinds:
            items = get(node, "itemListElement")
            if len(items) < 2:
                add("FAIL", "REQUIRED", where, "BreadcrumbList needs at least 2 ListItem entries")
            for n, it in enumerate(items):
                if isinstance(it, dict):
                    if "position" not in it or not (it.get("name") or get(it, "item.name")):
                        add("FAIL", "REQUIRED", where, "ListItem %d needs position and name" % (n + 1))
                    if n < len(items) - 1 and not it.get("item"):
                        add("FAIL", "REQUIRED", where, "ListItem %d needs item (the URL); only the last may omit it" % (n + 1))
        if "Question" in kinds:
            for ans in get(node, "acceptedAnswer") + get(node, "suggestedAnswer"):
                if isinstance(ans, dict) and not ans.get("text"):
                    add("FAIL", "REQUIRED", where, "each Answer needs text")
            if "answerCount" not in node:
                add("FAIL", "REQUIRED", where, "Question needs answerCount")
        # dates
        for prop in DATE_PROPS & set(node):
            for v in get(node, prop):
                if not isinstance(v, str) or not DATE_RE.match(v.strip()):
                    add("FAIL", "DATE", where, "%s is not ISO 8601: %r" % (prop, v))
                elif "T" in v and not HAS_TZ.search(v.strip()):
                    add("WARN", "DATE-TZ", where, "%s has a time but no time zone: %s" % (prop, v))
        # urls
        for prop in URL_PROPS & set(node):
            for v in get(node, prop):
                if isinstance(v, str) and not re.match(r"^https?://", v.strip()):
                    add("WARN", "URL", where, "%s is not an absolute URL: %r" % (prop, v))
        nid = node.get("@id")
        if isinstance(nid, str) and not re.match(r"^https?://", nid):
            add("WARN", "ID", where, "@id should be a stable absolute URL with a fragment, not %r" % nid)
        # ratings
        rating_nodes = []
        if "AggregateRating" in kinds or "Rating" in kinds:
            rating_nodes.append(node)
        for rn in rating_nodes:
            best = number(rn.get("bestRating", 5)) or 5
            worst = number(rn.get("worstRating", 1))
            worst = 1 if worst is None else worst
            val = number(rn.get("ratingValue")) if "ratingValue" in rn else None
            if "ratingValue" in rn and val is None:
                add("FAIL", "RATING", where, "ratingValue is not a number: %r" % rn.get("ratingValue"))
            elif val is not None and not worst <= val <= best:
                add("FAIL", "RATING", where, "ratingValue %s is outside %s-%s; set bestRating/worstRating or fix the value" % (val, worst, best))
            for cnt in ("ratingCount", "reviewCount"):
                if cnt in rn:
                    c = number(rn[cnt])
                    if c is None or c < 1 or c != int(c):
                        add("FAIL", "RATING", where, "%s must be a positive whole number, got %r" % (cnt, rn[cnt]))
            if visible is not None and val is not None and "AggregateRating" in kinds:
                shown = {str(rn.get("ratingValue")), ("%g" % val), ("%.1f" % val)}
                if not any(re.search(r"(?<![\d.])%s(?![\d])" % re.escape(s), visible) for s in shown):
                    add("WARN", "VISIBLE", where, "ratingValue %s does not appear in the page's visible text; marked-up ratings must be shown to users" % rn.get("ratingValue"))
                for cnt in ("ratingCount", "reviewCount"):
                    if cnt in rn and not re.search(r"(?<!\d)%s(?!\d)" % re.escape(str(rn[cnt]).replace(",", "")), visible.replace(",", "")):
                        add("WARN", "VISIBLE", where, "%s %s does not appear in the page's visible text" % (cnt, rn[cnt]))
        has_rating = bool(get(node, "aggregateRating") or get(node, "review"))
        if has_rating and (set(kinds) & RATING_HOSTS_BLOCKED):
            add("WARN", "SELF-SERVING", where, "ratings on %s: not eligible when the entity controls reviews about itself (allowed only on sites reviewing other businesses)" % "/".join(kinds))
        if has_rating and (page_type == "list" or set(parents) & LIST_TYPES or set(kinds) & LIST_TYPES):
            add("FAIL", "LIST-RATING", where, "rating or review markup on a list, category or comparison page; ratings must be about one specific item that is the page's subject")
        if visible is not None and "Review" in kinds:
            for author in get(node, "author.name") + [a for a in get(node, "author") if isinstance(a, str)]:
                if isinstance(author, str) and author and author not in visible:
                    add("WARN", "VISIBLE", where, "review author %r does not appear in the visible text" % author)

    main_types = [t for t in top_types if t not in SEMANTIC_ONLY and t not in ("Organization", "WebSite", "BreadcrumbList")]
    if len(set(main_types)) > 1:
        add("NOTE", "MAIN", "-", "several main entity types at top level (%s); make sure one is the page's subject and the others reference it" % ", ".join(sorted(set(main_types))))
    if any("SearchAction" in json.dumps(n) for _, n, _ in nodes if "WebSite" in types_of(n)):
        add("NOTE", "RETIRED", "WebSite", "SearchAction no longer produces a sitelinks search box; harmless, optional")

    order = {"FAIL": 0, "WARN": 1, "NOTE": 2}
    findings.sort(key=lambda f: (order[f["level"]], f["code"]))
    counts = {k: sum(1 for f in findings if f["level"] == k) for k in order}
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    reminder = ("Passing here means the structure is sound. It does not guarantee a rich result: run the search engine's "
                "rich-result tester and the schema.org validator, and check that every marked-up value is visible on the page.")
    if "--json" in argv:
        print(json.dumps({"blocks": len(blocks), "typed_nodes": len(nodes), "counts": counts, "findings": findings,
                          "nodes": [{"node": w, "status": s} for w, s in summary], "reminder": reminder}, indent=2))
    else:
        print("JSON-LD CHECK: %d block(s), %d typed node(s), %d FAIL, %d WARN, %d NOTE" % (len(blocks), len(nodes), counts["FAIL"], counts["WARN"], counts["NOTE"]))
        for f in findings:
            print("%-4s %-12s %s: %s" % (f["level"], f["code"], f["node"], f["message"]))
        if summary:
            print("\nNodes:")
            for w, s in summary:
                print("  %s -> %s" % (w, s))
        print("\n" + reminder)
    return 1 if counts["FAIL"] else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
