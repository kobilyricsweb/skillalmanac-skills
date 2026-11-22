"""Internal link graph scanner for a folder of HTML and Markdown pages.

Scans one site folder for .html, .htm and .md files, extracts relative
internal links with bounded regular expressions, and prints one JSON report:
orphan pages (no inbound internal link), unreachable pages (linked, but no
click path from the root index), pages more than 3 clicks from the root
index, broken internal links and the top link hubs.

Stdlib only. No network, no subprocess, no eval or exec. Input files are
opened read-only. The optional --out report path is refused if it is an
input file or sits inside the scanned folder. Hidden folders (names starting
with a dot) and symbolic links are skipped.

Usage:
  python -I scripts/link_graph.py <site_dir> [--out <report.json>]

Exit codes: 0 no findings, 1 findings reported, 2 usage or input error.
Errors are one line of JSON on stderr.
"""
import collections
import json
import os
import posixpath
import re
import sys

MAX_FILE_BYTES = 2 * 1024 * 1024
MAX_TOTAL_BYTES = 64 * 1024 * 1024
MAX_PAGES = 2000
MAX_ENTRIES = 5000
MAX_DEPTH = 8
MAX_CLICKS = 3
TOP_HUBS = 5
PAGE_EXTS = (".html", ".htm", ".md")
INDEX_NAMES = ("index.html", "index.md")

HTML_A = re.compile(
    r"""<a\s[^>]{0,2000}?\bhref\s*=\s*(?:"([^"]{0,2000})"|'([^']{0,2000})')""",
    re.IGNORECASE,
)
MD_LINK = re.compile(
    r"""\[[^\]\n]{0,500}\]\(\s*<?([^)\s>]{1,2000})>?(?:\s+"[^"\n]{0,200}")?\s*\)"""
)
SCHEME = re.compile(r"^[a-zA-Z][a-zA-Z0-9+.\-]*:")
PERCENT_TOKEN = re.compile(r"(%[0-9A-Fa-f]{2})")


def fail(message):
    sys.stderr.write(json.dumps({"error": message}) + "\n")
    sys.exit(2)


def percent_decode(text):
    """Decode %XX escapes as UTF-8 bytes; invalid byte sequences become U+FFFD."""
    raw = bytearray()
    for part in PERCENT_TOKEN.split(text):
        if len(part) == 3 and part[0] == "%":
            raw.append(int(part[1:], 16))
        else:
            raw.extend(part.encode("utf-8"))
    return raw.decode("utf-8", errors="replace")


def parse_args(argv):
    args = argv[1:]
    site = None
    out = None
    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--out":
            if i + 1 >= len(args):
                fail("--out needs a path")
            out = args[i + 1]
            i += 2
            continue
        if arg.startswith("-"):
            fail("unknown option: " + arg[:40])
        if site is not None:
            fail("only one site folder is accepted")
        site = arg
        i += 1
    if site is None:
        fail("usage: link_graph.py <site_dir> [--out <report.json>]")
    return site, out


def walk(root):
    files = set()
    pages = set()
    for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
        rel_dir = os.path.relpath(dirpath, root)
        depth = 0 if rel_dir == "." else len(rel_dir.split(os.sep))
        if depth > MAX_DEPTH:
            fail("folder nesting exceeds %d levels" % MAX_DEPTH)
        kept = []
        for name in dirnames:
            full = os.path.join(dirpath, name)
            if name.startswith(".") or os.path.islink(full):
                continue
            kept.append(name)
        dirnames[:] = kept
        for name in filenames:
            full = os.path.join(dirpath, name)
            if os.path.islink(full):
                continue
            rel = os.path.relpath(full, root).replace(os.sep, "/")
            files.add(rel)
            if len(files) > MAX_ENTRIES:
                fail("more than %d files in the site folder" % MAX_ENTRIES)
            if name.lower().endswith(PAGE_EXTS):
                pages.add(rel)
                if len(pages) > MAX_PAGES:
                    fail("more than %d pages" % MAX_PAGES)
    return pages, files


def read_page(root, rel, budget):
    full = os.path.join(root, *rel.split("/"))
    try:
        size = os.path.getsize(full)
        if size > MAX_FILE_BYTES:
            fail("file larger than 2 MB: " + rel)
        budget[0] += size
        if budget[0] > MAX_TOTAL_BYTES:
            fail("site folder larger than 64 MB")
        with open(full, "rb") as handle:
            data = handle.read(MAX_FILE_BYTES + 1)
    except OSError:
        fail("cannot read file: " + rel)
    if len(data) > MAX_FILE_BYTES:
        fail("file grew past 2 MB while reading: " + rel)
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        fail("file is not valid UTF-8: " + rel)


def extract_hrefs(text):
    hrefs = []
    for match in HTML_A.finditer(text):
        hrefs.append(match.group(1) if match.group(1) is not None else match.group(2))
    for match in MD_LINK.finditer(text):
        hrefs.append(match.group(1))
    return hrefs


def resolve(src, href, pages, files):
    """Return (kind, value): kind is page, asset, broken or skip."""
    h = percent_decode(href.strip()).replace("\\", "/")
    if not h or h.startswith("#") or h.startswith("//") or SCHEME.match(h):
        return ("skip", None)
    h = h.split("#", 1)[0].split("?", 1)[0]
    if not h:
        return ("skip", None)
    trailing = h.endswith("/")
    if h.startswith("/"):
        joined = h.lstrip("/")
    else:
        joined = posixpath.join(posixpath.dirname(src), h)
    norm = posixpath.normpath(joined)
    if norm == "." or norm == "/":
        norm = ""
    if norm == ".." or norm.startswith("../") or norm.startswith("/"):
        return ("broken", "outside_site")
    if trailing or norm == "":
        cands = [posixpath.join(norm, name) if norm else name for name in INDEX_NAMES]
    else:
        cands = [
            norm,
            norm + ".html",
            norm + ".md",
            posixpath.join(norm, "index.html"),
            posixpath.join(norm, "index.md"),
        ]
    for cand in cands:
        if cand in pages:
            return ("page", cand)
    for cand in cands:
        if cand in files:
            return ("asset", None)
    return ("broken", "missing_target")


def analyse(root, pages, files):
    budget = [0]
    out_edges = {}
    broken = set()
    internal_links = 0
    for src in sorted(pages):
        text = read_page(root, src, budget)
        targets = set()
        for href in extract_hrefs(text):
            kind, value = resolve(src, href, pages, files)
            if kind == "skip":
                continue
            internal_links += 1
            if kind == "page":
                if value != src:
                    targets.add(value)
            elif kind == "broken":
                broken.add((src, href.strip()[:200], value))
        out_edges[src] = targets

    index = None
    for name in INDEX_NAMES:
        if name in pages:
            index = name
            break
    if index is None:
        fail("no index.html or index.md at the site root")

    inbound = dict((p, set()) for p in pages)
    for src, targets in out_edges.items():
        for target in targets:
            inbound[target].add(src)

    depth = {index: 0}
    queue = collections.deque([index])
    while queue:
        cur = queue.popleft()
        for target in sorted(out_edges[cur]):
            if target not in depth:
                depth[target] = depth[cur] + 1
                queue.append(target)

    orphans = sorted(p for p in pages if p != index and not inbound[p])
    unreachable = sorted(p for p in pages if p not in depth and inbound[p])
    deep = [{"page": p, "clicks": depth[p]} for p in sorted(depth) if depth[p] > MAX_CLICKS]
    broken_list = [{"source": s, "href": h, "reason": r} for (s, h, r) in sorted(broken)]
    hub_pages = sorted((p for p in pages if inbound[p]), key=lambda p: (-len(inbound[p]), p))
    hubs = [{"page": p, "inbound": len(inbound[p])} for p in hub_pages[:TOP_HUBS]]
    findings = len(orphans) + len(unreachable) + len(deep) + len(broken_list)

    return {
        "tool": "link_graph",
        "version": "0.1.0",
        "index": index,
        "summary": {
            "files": len(files),
            "pages": len(pages),
            "internal_links": internal_links,
            "orphans": len(orphans),
            "unreachable": len(unreachable),
            "deep_pages": len(deep),
            "broken_links": len(broken_list),
            "findings": findings,
        },
        "orphans": orphans,
        "unreachable": unreachable,
        "deep_pages": deep,
        "broken_links": broken_list,
        "top_hubs": hubs,
    }


def check_out(out_path, root, files):
    out_real = os.path.realpath(out_path)
    if os.path.isdir(out_real):
        fail("--out path is a directory")
    for rel in files:
        if os.path.realpath(os.path.join(root, *rel.split("/"))) == out_real:
            fail("--out path is an input file")
    root_real = os.path.realpath(root)
    try:
        inside = os.path.commonpath([root_real, out_real]) == root_real
    except ValueError:
        inside = False
    if inside:
        fail("--out path is inside the scanned folder")


def main(argv):
    site, out = parse_args(argv)
    if not os.path.isdir(site):
        fail("site folder not found or not a directory")
    root = os.path.abspath(site)
    pages, files = walk(root)
    if not pages:
        fail("no .html, .htm or .md files found in the site folder")
    if out is not None:
        check_out(out, root, files)
    report = analyse(root, pages, files)
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if out is not None:
        try:
            with open(out, "w", encoding="utf-8", newline="\n") as handle:
                handle.write(text)
        except OSError:
            fail("cannot write --out file")
    sys.stdout.write(text)
    return 1 if report["summary"]["findings"] else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
