#!/usr/bin/env python3
"""Read-only audit of an exported team wiki (Markdown and/or HTML files).

Usage:
    python wiki_audit.py <export-folder> [--stale-days 180] [--today YYYY-MM-DD]
        [--mtime-fallback use|ignore] [--dup-threshold 0.88] [--max-depth 4]
        [--wide-folder 50] [--limit 500] [--include-pages] [--fail-on-findings]

What it reads: every .md, .markdown, .html and .htm file under the folder
(dot-folders and node_modules are skipped; files over 2 MB are skipped and
listed). The names of all other files are read only to check that links to
attachments resolve.

What it writes: nothing. It never creates, edits, moves or deletes a file.
The only output is one strict JSON document on stdout (no NaN, no comments).

Reports: pages without an owner line, pages not updated for N days, near
duplicate titles in different folders (with a body-similarity verdict), orphan
pages, broken internal links, over-deep and over-wide folders, and a proposed
archive/merge plan. The plan is a proposal; a person decides.

Exit codes: 0 audit completed; 1 audit completed and --fail-on-findings was
given and something was found; 2 bad arguments or unreadable folder.
"""
import argparse
import datetime
import hashlib
import json
import os
import posixpath
import re
import sys
from collections import Counter, defaultdict
from difflib import SequenceMatcher
from html.parser import HTMLParser

SCHEMA_VERSION = 1
PAGE_EXT = (".md", ".markdown", ".html", ".htm")
MAX_BYTES = 2000000  # a wiki page larger than this is almost surely a data dump
DEFAULT_STALE_DAYS = 180  # two review quarters; see references/archive_policy.md
DEFAULT_DUP_THRESHOLD = 0.88  # high enough that "Sprint 12 retro"-style siblings are not paired by shape alone
DEFAULT_MAX_DEPTH = 4  # folders below the export root; deeper pages are hard to navigate
DEFAULT_WIDE_FOLDER = 50  # direct pages in one folder before it needs sub-grouping
SAME_CONTENT = 0.80  # 3-word-shingle overlap at or above this: same page twice
OVERLAP = 0.30  # between OVERLAP and SAME_CONTENT: partial overlap, human merge decision
MIN_WORDS_FOR_BODY_MATCH = 20  # shorter bodies are stubs; identical stubs are not evidence of duplication
MAX_TOKEN_DF = 40  # a title word shared by more pages than this is too common to seed duplicate candidates
MAX_PAIR_CHECKS = 300000  # cap on title comparisons so a huge export still finishes
MTIME_COLLAPSE_SHARE = 0.8  # share of mtime dates on one day that means export-time stamps
ENTRY_STEMS = {"index", "readme", "home", "summary", "_sidebar", "sidebar", "_footer", "_navbar"}
GENERIC_TITLES = {
    "overview", "index", "home", "readme", "faq", "notes", "meeting notes", "agenda",
    "untitled", "getting started", "introduction", "summary", "resources", "links",
    "template", "templates", "archive", "todo", "to do", "tasks", "contacts", "glossary",
}
NOISE_TOKENS = {"copy", "old", "backup", "draft", "final", "wip"}
PLACEHOLDERS = {
    "", "tbd", "tba", "none", "n a", "na", "unknown", "unassigned", "nobody", "todo",
    "to do", "me", "x", "xx", "name", "your name", "team name", "owner", "no owner",
}
ACTION_ORDER = ["merge", "archive", "assign_owner", "review_with_owner", "fix_links", "disambiguate"]

OWNER_WORDS = r"(?:page[ _-]?owner|owners?|maintainers?|maintained[ _]by|dri|steward)"
OWNER_LINE = re.compile(r"^[>\s*_\-|#]*" + OWNER_WORDS + r"[*_\s]*[:：][*_\s]*(.*?)[\s|*_]*$", re.I)
OWNER_ROW = re.compile(r"^\|\s*" + OWNER_WORDS + r"\s*\|\s*(.*?)\s*\|?\s*$", re.I)
OWNER_KEYS = ("owner", "owners", "page_owner", "maintainer", "maintainers", "dri", "steward")
FRESH_KEYS = (
    "updated", "last_updated", "last_edited", "last_edited_time", "last_modified", "modified",
    "date_modified", "lastmod", "updated_at", "modified_at", "edited", "reviewed", "last_reviewed",
)
META_OWNER = ("owner", "maintainer", "dri")
META_FRESH = (
    "last-modified", "article:modified_time", "og:updated_time", "modified", "dcterms.modified",
    "date.modified", "revised", "last_modified",
)
FRESH_LINE = re.compile(r"last[\s_-]*(?:updated|edited|modified|reviewed)(?:[\s_-]*(?:on|time|at|date))?\b(.*)$", re.I)
UPDATED_LINE = re.compile(r"^[>\s*_\-|]*(?:updated|modified|reviewed)[*_\s]*[:：](.*)$", re.I)
MONTHS = {m: i for i, m in enumerate(
    ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"], 1)}
ISO_RE = re.compile(r"(?<!\d)(\d{4})[-/](\d{1,2})[-/](\d{1,2})(?!\d)")
MDY_RE = re.compile(r"\b([A-Za-z]{3,9})\.? (\d{1,2})(?:st|nd|rd|th)?,? (\d{4})\b")
DMY_RE = re.compile(r"\b(\d{1,2})(?:st|nd|rd|th)? ([A-Za-z]{3,9})\.?,? (\d{4})\b")
MD_LINK = re.compile(r"!?\[[^\]\n]*\]\(\s*(?:<([^>\n]+)>|([^)\s]+))(?:\s+(?:\"[^\"]*\"|'[^']*'))?\s*\)")
MD_REFDEF = re.compile(r"^\s{0,3}\[[^\]\n]+\]:\s*<?([^\s>]+)>?")
WIKILINK = re.compile(r"\[\[([^\]\n|#]+)(?:#[^\]\n|]*)?(?:\|[^\]\n]*)?\]\]")
SCHEME = re.compile(r"^[a-zA-Z][a-zA-Z0-9+.\-]*:")
DRIVE = re.compile(r"^[a-zA-Z]:[\\/]")
NOTION_ID = re.compile(r"\s[0-9a-f]{32}$")


def parse_date(text):
    """First valid calendar date in text, or None."""
    for m in ISO_RE.finditer(text):
        try:
            return datetime.date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        except ValueError:
            continue
    for m in MDY_RE.finditer(text):
        mon = MONTHS.get(m.group(1)[:3].lower())
        if mon:
            try:
                return datetime.date(int(m.group(3)), mon, int(m.group(2)))
            except ValueError:
                continue
    for m in DMY_RE.finditer(text):
        mon = MONTHS.get(m.group(2)[:3].lower())
        if mon:
            try:
                return datetime.date(int(m.group(3)), mon, int(m.group(1)))
            except ValueError:
                continue
    return None


def split_frontmatter(lines):
    """Return (dict of lowercase keys, index of first body line)."""
    if not lines or lines[0].strip() != "---":
        return {}, 0
    for i in range(1, min(len(lines), 200)):
        if lines[i].strip() in ("---", "..."):
            return parse_kv(lines[1:i]), i + 1
    return {}, 0


def parse_kv(lines):
    out = {}
    i = 0
    while i < len(lines):
        m = re.match(r"^([A-Za-z_][\w \-]*?)\s*:\s*(.*)$", lines[i])
        i += 1
        if not m:
            continue
        key = re.sub(r"[^a-z0-9]+", "_", m.group(1).lower()).strip("_")
        val = m.group(2).strip()
        if not val:
            items = []
            while i < len(lines) and re.match(r"^\s+-\s+", lines[i]):
                items.append(re.sub(r"^\s+-\s+", "", lines[i]).strip())
                i += 1
            val = ", ".join(items)
        val = val.strip("[]").strip()
        if len(val) >= 2 and val[0] == val[-1] and val[0] in "\"'":
            val = val[1:-1]
        out[key] = val.strip()
    return out


def owner_state(value):
    """Return (owner or None, state) with state set, placeholder or missing."""
    if value is None:
        return None, "missing"
    norm = re.sub(r"[^\w@.]+", " ", value).strip().lower()
    if norm in PLACEHOLDERS or norm.startswith("tbd") or re.search(r"[<\[{]\s*(name|owner|your)", value, re.I):
        return None, "placeholder"
    return value.strip(), "set"


def find_owner(fields, lines):
    """Owner from metadata fields first, then from an owner line near the top."""
    for key in OWNER_KEYS:
        if key in fields:
            return owner_state(fields[key])
    state = "missing"
    for line in lines[:60]:
        m = OWNER_LINE.match(line.strip()) or OWNER_ROW.match(line.strip())
        if m:
            val, st = owner_state(m.group(1))
            if val:
                return val, "set"
            state = "placeholder"
    return None, state


def find_updated(fields, lines, today, future):
    """Newest freshness date from metadata or body lines: (date, source) or (None, None)."""
    found = []
    unparsed = False  # a date field exists but holds no readable date
    for key in FRESH_KEYS:
        if key in fields and fields[key].strip():
            d = parse_date(fields[key])
            if d:
                found.append((d, "metadata"))
            else:
                unparsed = True
    for line in lines[:100] + lines[-30:]:
        s = line.strip()
        m = FRESH_LINE.search(s) or UPDATED_LINE.match(s)
        if m:
            d = parse_date(m.group(1))
            if d:
                found.append((d, "body"))
            elif re.search(r"\d", m.group(1)):
                unparsed = True
    ok = []
    for d, src in found:
        if d > today:
            future[0] += 1
        else:
            ok.append((d, src))
    if not ok:
        return None, ("unparsed" if unparsed and not found else None)
    return max(ok, key=lambda t: t[0])


class PageHTML(HTMLParser):
    """Collects title, first h1, meta tags, links and visible text lines."""

    BLOCK = {"p", "div", "br", "li", "tr", "h1", "h2", "h3", "h4", "h5", "h6", "table", "section", "article"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.title = []
        self.h1 = []
        self.meta = {}
        self.links = []
        self.text = []
        self._in_title = False
        self._in_h1 = False
        self._h1_done = False
        self._skip = 0

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag in ("script", "style"):
            self._skip += 1
        elif tag == "title":
            self._in_title = True
        elif tag == "h1" and not self._h1_done:
            self._in_h1 = True
        elif tag == "meta":
            name = (a.get("name") or a.get("property") or "").lower()
            if name and a.get("content") is not None:
                self.meta.setdefault(name, a["content"])
        elif tag == "a" and a.get("href"):
            self.links.append((a["href"], self.getpos()[0]))
        elif tag == "img" and a.get("src"):
            self.links.append((a["src"], self.getpos()[0]))
        if tag in self.BLOCK:
            self.text.append("\n")

    def handle_endtag(self, tag):
        if tag in ("script", "style") and self._skip:
            self._skip -= 1
        elif tag == "title":
            self._in_title = False
        elif tag == "h1" and self._in_h1:
            self._in_h1 = False
            self._h1_done = True
        elif tag == "th":
            self.text.append(": ")
        if tag in self.BLOCK or tag == "td":
            self.text.append("\n")

    def handle_data(self, data):
        if self._skip:
            return
        if self._in_title:
            self.title.append(data)
        if self._in_h1:
            self.h1.append(data)
        self.text.append(data)


def clean_title_from_name(rel):
    stem = posixpath.splitext(posixpath.basename(rel))[0]
    stem = NOTION_ID.sub("", stem)  # Notion appends a 32-hex id after a space
    stem = stem.replace("_", " ").replace("-", " ")
    return stem.strip() or posixpath.basename(rel)


def read_text(path):
    with open(path, "rb") as fh:
        data = fh.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        return None
    return data.decode("utf-8-sig", errors="replace").replace("\r\n", "\n").replace("\r", "\n")


def extract_md(text, today, future):
    lines = text.split("\n")
    fields, start = split_frontmatter(lines)
    body = lines[start:]
    clean = []
    fence = None
    for ln in body:
        s = ln.lstrip()
        if fence:
            if s.startswith(fence):
                fence = None
            clean.append("")
            continue
        if s.startswith("```") or s.startswith("~~~"):
            fence = s[:3]
            clean.append("")
            continue
        clean.append(re.sub(r"`[^`\n]*`", "", ln))
    title = fields.get("title") or None
    if not title:
        for ln in clean[:80]:
            m = re.match(r"^#\s+(.+?)\s*#*\s*$", ln)
            if m:
                title = m.group(1).strip()
                break
    links = []
    for idx, ln in enumerate(clean):
        lineno = start + idx + 1
        for m in MD_LINK.finditer(ln):
            links.append(("path", m.group(1) or m.group(2), lineno))
        m = MD_REFDEF.match(ln)
        if m:
            links.append(("path", m.group(1), lineno))
        for m in WIKILINK.finditer(ln):
            links.append(("wiki", m.group(1).strip(), lineno))
    owner, ostate = find_owner(fields, clean)
    updated, usrc = find_updated(fields, clean, today, future)
    return title, owner, ostate, updated, usrc, links, "\n".join(body)


def extract_html(text, today, future):
    parser = PageHTML()
    try:
        parser.feed(text)
        parser.close()
    except Exception:  # malformed markup: keep whatever was collected
        pass
    title = None
    if parser.title:
        title = "".join(parser.title).strip()
        if " : " in title:  # space-export titles read "Space : Page"
            title = title.rsplit(" : ", 1)[1].strip()
    if not title and parser.h1:
        title = "".join(parser.h1).strip()
    lines = [re.sub(r"\s+", " ", x).strip() for x in "".join(parser.text).split("\n")]
    lines = [x for x in lines if x]
    fields = {}
    for key in META_OWNER:
        if key in parser.meta:
            fields[key] = parser.meta[key]
    for key in META_FRESH:
        if key in parser.meta:
            fields["updated"] = parser.meta[key]
    owner, ostate = find_owner(fields, lines)
    updated, usrc = find_updated(fields, lines, today, future)
    if usrc == "metadata":
        usrc = "meta"
    links = [("path", href, line) for href, line in parser.links]
    return title or None, owner, ostate, updated, usrc, links, "\n".join(lines)


def norm_title(title):
    t = title.lower()
    t = re.sub(r"[_\-–—]+", " ", t)
    t = re.sub(r"\(\s*\d+\s*\)", " ", t)
    toks = re.findall(r"\w+", t, re.UNICODE)
    toks = [x for x in toks if x not in NOISE_TOKENS and not re.fullmatch(r"v\d+(?:\.\d+)*", x)]
    return toks


def shingles(tokens):
    if len(tokens) < 3:
        return set(tokens)
    return {" ".join(tokens[i:i + 3]) for i in range(len(tokens) - 2)}


def jaccard(a, b):
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


PCT_RUN = re.compile(r"(?:%[0-9A-Fa-f]{2})+")


def unquote(text):
    """Decode %XX sequences as UTF-8 (own decoder: no URL library is needed for file links)."""
    return PCT_RUN.sub(lambda m: bytes.fromhex(m.group(0).replace("%", "")).decode("utf-8", errors="replace"), text)


def resolve_path(src_rel, target, files, files_lower):
    """Return (resolved relative path or None, reason or None)."""
    path = target.strip().split("#", 1)[0].split("?", 1)[0]
    if not path:
        return None, "skip"
    path = unquote(path).replace("\\", "/")
    if DRIVE.match(path):
        return None, "absolute_local_path"
    if path.startswith("/"):
        base = posixpath.normpath(path.lstrip("/")) if path.lstrip("/") else "."
    else:
        base = posixpath.normpath(posixpath.join(posixpath.dirname(src_rel), path))
    if base == ".." or base.startswith("../"):
        return None, "outside_export"
    prefix = "" if base == "." else base
    cands = []
    if prefix:
        cands.append(prefix)
        cands.extend(prefix + ext for ext in (".md", ".html", ".htm", ".markdown"))
        join = prefix + "/"
    else:
        join = ""
    cands.extend(join + n for n in ("index.md", "README.md", "readme.md", "index.html", "index.htm"))
    for c in cands:
        if c in files:
            return c, None
    for c in cands:
        if c.lower() in files_lower:
            return None, "case_mismatch"
    return None, "missing_target"


def top_space(path):
    return path.split("/", 1)[0] if "/" in path else "(root)"


def main(argv=None):
    ap = argparse.ArgumentParser(description="Read-only audit of an exported team wiki. Prints strict JSON.")
    ap.add_argument("root", help="folder holding the exported Markdown/HTML pages")
    ap.add_argument("--stale-days", type=int, default=DEFAULT_STALE_DAYS, help="age in days that counts as stale (default 180)")
    ap.add_argument("--today", default=None, help="reference date YYYY-MM-DD (default: today); use it for repeatable runs")
    ap.add_argument("--mtime-fallback", choices=("use", "ignore"), default="use",
                    help="use file modified time for pages with no date in them (default), or list them as undated")
    ap.add_argument("--dup-threshold", type=float, default=DEFAULT_DUP_THRESHOLD, help="title similarity 0.5-1.0 (default 0.88)")
    ap.add_argument("--max-depth", type=int, default=DEFAULT_MAX_DEPTH, help="folders deep before a page is flagged (default 4)")
    ap.add_argument("--wide-folder", type=int, default=DEFAULT_WIDE_FOLDER, help="direct pages per folder before it is flagged (default 50)")
    ap.add_argument("--limit", type=int, default=500, help="max items per list in the output (default 500)")
    ap.add_argument("--include-pages", action="store_true", help="add a per-page table to the output")
    ap.add_argument("--fail-on-findings", action="store_true", help="exit 1 when any finding exists")
    args = ap.parse_args(argv)

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if args.stale_days < 1 or not 0.5 <= args.dup_threshold <= 1.0 or args.limit < 1:
        print("error: --stale-days must be >= 1, --dup-threshold 0.5-1.0, --limit >= 1", file=sys.stderr)
        return 2
    try:
        today = datetime.date.fromisoformat(args.today) if args.today else datetime.date.today()
    except ValueError:
        print("error: --today must look like 2026-11-21", file=sys.stderr)
        return 2
    root = os.path.abspath(args.root)
    if not os.path.isdir(root):
        print("error: not a folder: " + args.root, file=sys.stderr)
        return 2

    all_files = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(d for d in dirnames if not d.startswith(".") and d != "node_modules")
        for fn in sorted(filenames):
            full = os.path.join(dirpath, fn)
            all_files.append(os.path.relpath(full, root).replace(os.sep, "/"))
    files = set(all_files)
    files_lower = {f.lower() for f in all_files}

    future = [0]
    skipped = []
    pages = {}
    for rel in all_files:
        if not rel.lower().endswith(PAGE_EXT):
            continue
        full = os.path.join(root, *rel.split("/"))
        try:
            text = read_text(full)
        except OSError as exc:
            skipped.append({"path": rel, "reason": "unreadable: " + (exc.strerror or "os error")})
            continue
        if text is None:
            skipped.append({"path": rel, "reason": "larger than 2 MB"})
            continue
        is_html = rel.lower().endswith((".html", ".htm"))
        title, owner, ostate, updated, usrc, links, body = (extract_html if is_html else extract_md)(text, today, future)
        source = usrc
        if updated is None and usrc == "unparsed":
            source = "unparsed"  # never fall back to mtime for a page whose date field is unreadable
        elif updated is None and args.mtime_fallback == "use":
            try:
                mt = os.stat(full).st_mtime
                updated = datetime.datetime.fromtimestamp(mt, datetime.timezone.utc).date()
                source = "mtime"
            except OSError:
                updated = None
        toks = re.findall(r"\w+", body.lower(), re.UNICODE)[:20000]
        pages[rel] = {
            "path": rel, "title": title or clean_title_from_name(rel), "owner": owner, "owner_state": ostate,
            "updated": updated, "date_source": source, "links": links, "tokens": toks,
            "hash": hashlib.sha256(" ".join(toks).encode("utf-8")).hexdigest() if len(toks) >= MIN_WORDS_FOR_BODY_MATCH else None,
        }

    stems = defaultdict(list)
    for rel in pages:
        stem = posixpath.splitext(posixpath.basename(rel))[0].lower()
        stems[re.sub(r"[\s_]+", "-", stem)].append(rel)

    inbound = defaultdict(set)
    broken = []
    outbound = Counter()
    for rel, pg in pages.items():
        for kind, target, line in pg["links"]:
            if kind == "wiki":
                hits = stems.get(re.sub(r"[\s_]+", "-", target.strip().lower()))
                if hits:
                    outbound[rel] += 1
                    for other in hits:
                        if other != rel:
                            inbound[other].add(rel)
                else:
                    broken.append({"source": rel, "line": line, "target": "[[" + target + "]]", "reason": "missing_target"})
                continue
            if SCHEME.match(target.strip()) and not DRIVE.match(target.strip()):
                continue
            if target.strip().startswith(("//", "#")) or not target.strip():
                continue
            res, reason = resolve_path(rel, target, files, files_lower)
            if reason == "skip":
                continue
            if res is None:
                broken.append({"source": rel, "line": line, "target": target.strip(), "reason": reason})
                continue
            outbound[rel] += 1
            if res in pages and res != rel:
                inbound[res].add(rel)

    entry = sorted(r for r in pages if posixpath.splitext(posixpath.basename(r))[0].lower() in ENTRY_STEMS)
    entry_set = set(entry)

    ownerless, stale, undated, orphans = [], [], [], []
    for rel in sorted(pages):
        pg = pages[rel]
        if pg["owner"] is None:
            ownerless.append({"path": rel, "reason": pg["owner_state"]})
        if pg["updated"] is None:
            undated.append(rel)
        else:
            age = (today - pg["updated"]).days
            pg["age"] = age
            if age >= args.stale_days:
                stale.append({"path": rel, "updated": pg["updated"].isoformat(), "date_source": pg["date_source"], "age_days": age})
        if rel not in entry_set and not inbound.get(rel):
            orphans.append(rel)
    broken.sort(key=lambda b: (b["source"], b["line"], b["target"]))

    notes = []
    mt_dates = [pg["updated"] for pg in pages.values() if pg["date_source"] == "mtime" and pg["updated"]]
    if len(mt_dates) >= 5:
        common = Counter(mt_dates).most_common(1)[0]
        if common[1] / len(mt_dates) >= MTIME_COLLAPSE_SHARE:
            notes.append("mtime_unreliable: %d of %d pages dated by file modified time share %s, which looks like export or unzip time; staleness for those pages is not trustworthy" % (common[1], len(mt_dates), common[0].isoformat()))
    unp = sorted(r for r, pg in pages.items() if pg["date_source"] == "unparsed")
    if unp:
        notes.append("WARNING unparsed_date: %d page(s) have a date field that could not be read and are listed as undated, not dated by file time: %s" % (len(unp), ", ".join(unp[:10]) + (" ..." if len(unp) > 10 else "")))
    if future[0]:
        notes.append("future_dates_ignored: %d date values later than the reference date were ignored" % future[0])

    # duplicates ---------------------------------------------------------
    cand = []
    for rel in sorted(pages):
        toks = norm_title(pages[rel]["title"])
        joined = " ".join(toks)
        if not toks or joined in GENERIC_TITLES:
            continue
        cand.append((rel, toks, joined, tuple(sorted(t for t in toks if any(c.isdigit() for c in t)))))
    index = defaultdict(list)
    for i, (_, toks, _, _) in enumerate(cand):
        for t in set(toks):
            index[t].append(i)
    seen = set()
    checks = 0
    capped = False
    dup_pairs = []
    for t, ids in index.items():
        if len(ids) > MAX_TOKEN_DF:
            continue
        for x in range(len(ids)):
            for y in range(x + 1, len(ids)):
                i, j = ids[x], ids[y]
                if (i, j) in seen:
                    continue
                seen.add((i, j))
                a, b = cand[i], cand[j]
                if posixpath.dirname(a[0]) == posixpath.dirname(b[0]) or a[3] != b[3]:
                    continue
                checks += 1
                if checks > MAX_PAIR_CHECKS:
                    capped = True
                    break
                sim = 1.0 if a[2] == b[2] else SequenceMatcher(None, a[2], b[2]).ratio()
                if sim < args.dup_threshold:
                    continue
                pa, pb = sorted((a[0], b[0]))
                body = jaccard(shingles(pages[pa]["tokens"]), shingles(pages[pb]["tokens"]))
                if pages[pa]["hash"] and pages[pa]["hash"] == pages[pb]["hash"]:
                    body = 1.0
                rel_name = "same_content" if body >= SAME_CONTENT else ("overlapping" if body >= OVERLAP else "title_clash_only")
                dup_pairs.append({
                    "a": pa, "b": pb, "title_a": pages[pa]["title"], "title_b": pages[pb]["title"],
                    "title_similarity": round(sim, 3), "body_similarity": round(body, 3),
                    "relation": rel_name, "cross_space": top_space(pa) != top_space(pb),
                })
            if capped:
                break
        if capped:
            break
    dup_pairs.sort(key=lambda d: (d["a"], d["b"]))
    if capped:
        notes.append("duplicate_scan_capped: more than %d title comparisons were needed; raise --dup-threshold or split the export" % MAX_PAIR_CHECKS)

    by_hash = defaultdict(list)
    for rel, pg in pages.items():
        if pg["hash"]:
            by_hash[pg["hash"]].append(rel)
    identical = sorted(sorted(v) for v in by_hash.values() if len(v) > 1)

    # hierarchy ------------------------------------------------------------
    deep = sorted(r for r in pages if r.count("/") > args.max_depth)
    per_folder = Counter(posixpath.dirname(r) or "(root)" for r in pages)
    wide = [{"folder": f, "pages": n} for f, n in sorted(per_folder.items()) if n > args.wide_folder]

    # plan -----------------------------------------------------------------
    parent = {}

    def find(x):
        parent.setdefault(x, x)
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    strong = set()
    for grp in identical:
        for other in grp[1:]:
            parent[find(other)] = find(grp[0])
        strong.update(grp)
    for d in dup_pairs:
        if d["relation"] in ("same_content", "overlapping"):
            parent[find(d["a"])] = find(d["b"])
    groups = defaultdict(list)
    for x in list(parent):
        groups[find(x)].append(x)
    plan = {}
    retired = set()
    keepers = {}
    for members in groups.values():
        if len(members) < 2:
            continue
        members = sorted(members)
        keeper = max(members, key=lambda p: (pages[p]["updated"].toordinal() if pages[p]["updated"] else 0, len(inbound.get(p, ())), len(pages[p]["tokens"])))
        keepers[keeper] = members
        pair_rel = {frozenset((d["a"], d["b"])): d["relation"] for d in dup_pairs}
        for m in members:
            if m == keeper:
                continue
            high = frozenset((m, keeper)) in pair_rel and pair_rel[frozenset((m, keeper))] == "same_content" or (m in strong and keeper in strong)
            retired.add(m)
            plan[m] = {"path": m, "action": "merge", "confidence": "high" if high else "medium", "merge_into": keeper,
                       "reasons": ["content duplicates %s (keep the newer, better linked page)" % keeper]}

    stale_map = {s["path"]: s for s in stale}
    orphan_set = set(orphans)
    owner_set = {o["path"] for o in ownerless}
    broken_by = Counter(b["source"] for b in broken)
    clash = defaultdict(list)
    for d in dup_pairs:
        if d["relation"] == "title_clash_only" and d["a"] not in retired and d["b"] not in retired:
            clash[d["a"]].append(d["b"])
            clash[d["b"]].append(d["a"])

    def downgrade(conf, rel):
        if pages[rel]["date_source"] == "mtime":
            return {"high": "medium", "medium": "low"}.get(conf, conf)
        return conf

    for rel in sorted(pages):
        issues = []
        if rel in stale_map:
            issues.append("stale")
        if rel in orphan_set:
            issues.append("orphan")
        if rel in owner_set:
            issues.append("ownerless")
        if broken_by.get(rel):
            issues.append("broken_links")
        if rel in retired:
            plan[rel]["also"] = issues
            continue
        entry_rec = None
        if rel in stale_map and rel in orphan_set:
            conf = "high" if rel in owner_set else "medium"
            why = ["no updates for %d days" % stale_map[rel]["age_days"], "no page links to it"]
            if rel in owner_set:
                why.append("no owner to object")
            else:
                why.append("confirm with the owner before archiving")
            entry_rec = {"action": "archive", "confidence": downgrade(conf, rel), "reasons": why}
        elif rel in owner_set:
            why = ["no owner line" if pages[rel]["owner_state"] == "missing" else "owner line is a placeholder"]
            if rel in stale_map:
                why.append("also not updated for %d days" % stale_map[rel]["age_days"])
            entry_rec = {"action": "assign_owner", "confidence": "high", "reasons": why}
        elif rel in stale_map or (rel in orphan_set):
            if rel in stale_map:
                why = ["not updated for %d days but still linked from %d page(s)" % (stale_map[rel]["age_days"], len(inbound.get(rel, ())))]
                entry_rec = {"action": "review_with_owner", "confidence": downgrade("medium", rel), "reasons": why}
            else:
                entry_rec = {"action": "review_with_owner", "confidence": "low", "reasons": ["nothing links to it; link it from a parent or archive it"]}
        elif broken_by.get(rel):
            entry_rec = {"action": "fix_links", "confidence": "high", "reasons": ["%d broken internal link(s)" % broken_by[rel]]}
        elif clash.get(rel):
            entry_rec = {"action": "disambiguate", "confidence": "medium",
                         "reasons": ["same title as %s but different content" % ", ".join(sorted(set(clash[rel])))]}
        if entry_rec:
            entry_rec["path"] = rel
            used = {"archive": {"stale", "orphan", "ownerless"}, "assign_owner": {"ownerless", "stale"},
                    "review_with_owner": {"stale", "orphan"}, "fix_links": {"broken_links"}}.get(entry_rec["action"], set())
            entry_rec["also"] = [i for i in issues if i not in used]
            plan[rel] = entry_rec
    plan_list = []
    for rel, rec in plan.items():
        out = {"path": rec["path"], "action": rec["action"], "confidence": rec["confidence"], "reasons": rec["reasons"]}
        if "merge_into" in rec:
            out["merge_into"] = rec["merge_into"]
        out["also"] = rec.get("also", [])
        plan_list.append(out)
    plan_list.sort(key=lambda r: (ACTION_ORDER.index(r["action"]), r["path"]))

    summary = {
        "pages": len(pages), "files_total": len(all_files), "ownerless": len(ownerless), "stale": len(stale),
        "undated": len(undated), "orphans": len(orphans), "broken_links": len(broken),
        "duplicate_title_pairs": len(dup_pairs), "identical_content_groups": len(identical),
        "deep_pages": len(deep), "wide_folders": len(wide), "entry_points": len(entry),
        "plan_actions": {a: sum(1 for p in plan_list if p["action"] == a) for a in ACTION_ORDER},
    }
    findings = sum(summary[k] for k in ("ownerless", "stale", "orphans", "broken_links", "duplicate_title_pairs", "identical_content_groups", "deep_pages", "wide_folders"))

    truncated = {}

    def cap(name, items):
        if len(items) > args.limit:
            truncated[name] = len(items)
            return items[:args.limit]
        return items

    report = {
        "tool": "wiki_audit", "schema_version": SCHEMA_VERSION, "read_only": True,
        "root": os.path.basename(root) or root, "today": today.isoformat(),
        "params": {"stale_days": args.stale_days, "mtime_fallback": args.mtime_fallback, "dup_threshold": args.dup_threshold,
                   "max_depth": args.max_depth, "wide_folder": args.wide_folder},
        "summary": summary,
        "ownerless": cap("ownerless", ownerless),
        "stale": cap("stale", stale),
        "undated": cap("undated", undated),
        "orphans": cap("orphans", orphans),
        "entry_points": entry,
        "broken_links": cap("broken_links", broken),
        "duplicate_titles": cap("duplicate_titles", dup_pairs),
        "identical_content": cap("identical_content", identical),
        "deep_pages": cap("deep_pages", deep),
        "wide_folders": cap("wide_folders", wide),
        "plan": cap("plan", plan_list),
        "skipped": skipped,
        "notes": notes,
        "truncated": truncated,
    }
    if args.include_pages:
        report["pages"] = cap("pages", [
            {"path": r, "title": pages[r]["title"], "owner": pages[r]["owner"],
             "updated": pages[r]["updated"].isoformat() if pages[r]["updated"] else None,
             "date_source": pages[r]["date_source"], "inbound": len(inbound.get(r, ())), "outbound_internal": outbound.get(r, 0)}
            for r in sorted(pages)])
    sys.stdout.write(json.dumps(report, indent=2, ensure_ascii=True, allow_nan=False) + "\n")
    return 1 if (args.fail_on_findings and findings) else 0


if __name__ == "__main__":
    sys.exit(main())
