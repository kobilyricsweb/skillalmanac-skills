#!/usr/bin/env python3
"""Audit file and folder names against a naming convention. Never renames anything.

    python naming_audit.py ROOT [--convention PATTERN] [options]
    python naming_audit.py --listing FILE [--convention PATTERN] [options]

ROOT is a folder that is walked (symbolic links are not followed). --listing reads
one relative path per line instead, optionally followed by a TAB and an ISO
timestamp (modified time), so a tree can be audited from an export or a chat paste.

PATTERN is literal text plus placeholders, for example {date}_{project}_{asset}_v{nn}
    {date}   ISO date YYYY-MM-DD         {date8}  compact date YYYYMMDD
    {nn}     zero-padded version number, width = number of n (nn=2, nnn=3);
             the literal right before it must end in "v" (for example _v{nn})
    {word}   any other name is a free field of lower-case letters and digits;
             words inside a field are joined with "-" ("_" separates fields)
Without --convention the dominant existing pattern is inferred and marked
needs_confirmation.

Options
    --max-path N       flag paths longer than N characters (default 200)
    --prefix-len N     characters the synced location adds in front of the root path (default 0)
    --date-order dmy|mdy   how to read 03-04-2026; without it such dates are ambiguous
    --date-from-mtime  when the convention needs a date and the name has none, use the
                       file modified date (UTC) from disk or from the listing
    --ascii            also require ASCII-only names
    --include-hidden   do not skip names that start with a dot
    --plan FILE        write the rename plan as CSV (columns old,new)
    --report FILE      also write the JSON report to FILE
    --force            allow --plan/--report to replace an existing file

Reads: the folder or listing it is given (names, sizes and modified times; file contents
are read only to hash files inside a case-collision group). Writes: only --plan and
--report, and only when the path is not the root, not inside it, not the listing and
not any scanned file; even --force never overrides that.
Stdout is one JSON document. Exit 0 = nothing found, 1 = violations or collisions
found, 2 = usage error (message on stderr).
"""
import argparse
import csv
import datetime
import hashlib
import io
import json
import os
import re
import sys
import unicodedata
from collections import Counter, defaultdict

DEFAULT_MAX_PATH = 200          # leaves headroom under the 260-character Windows limit that sync tools still hit
LONG_NAME = 100                 # one name this long is unreadable in any file dialog
HASH_LIMIT = 50 * 1024 * 1024   # files above this are not hashed when comparing collision groups
SHARE_NEEDED = 0.5              # share of files that must show a feature before inference adopts it
FORBIDDEN = set('<>:"|?*\\/')   # not allowed on Windows; backslash and slash cannot be in a name anywhere
RISKY = set("#%&{}$!'`@+=;,^~[]()")  # legal on disk but break URLs, shells, globbing or sync tools
RESERVED = {"con", "prn", "aux", "nul"} | {"com%d" % i for i in range(1, 10)} | {"lpt%d" % i for i in range(1, 10)}
IGNORED_FILES = {".ds_store", "thumbs.db", "desktop.ini"}
IGNORED_DIRS = {"node_modules", "__pycache__", "$recycle.bin"}

MECHANICAL = {"UNICODE_FORM", "NON_ASCII", "TRAILING_DOT_SPACE", "SPACE", "FORBIDDEN_CHAR", "RISKY_CHAR",
              "MIXED_CASE", "UPPER_EXT", "DOUBLE_SEPARATOR", "NON_SORTABLE_DATE", "NON_ISO_DATE",
              "VERSION_FORMAT", "DATE_POSITION"}
DIR_CODES = {"UNICODE_FORM", "NON_ASCII", "TRAILING_DOT_SPACE", "SPACE", "FORBIDDEN_CHAR", "RISKY_CHAR",
             "DOUBLE_SEPARATOR", "RESERVED_NAME", "LONG_NAME"}

MON = (r"(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|june?|july?|aug(?:ust)?|"
       r"sep(?:t(?:ember)?)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)")
MONTHS = {m: i + 1 for i, m in enumerate("jan feb mar apr may jun jul aug sep oct nov dec".split())}
DMON_RE = re.compile(r"(?<!\d)(\d{1,2})[-_. ]*(" + MON + r")(?![a-z])[-_. ,]*(\d{4})(?!\d)", re.I)
MOND_RE = re.compile(r"(?<![a-z])(" + MON + r")(?![a-z])[-_. ]*(\d{1,2})(?:st|nd|rd|th)?[-_. ,]+(\d{4})(?!\d)", re.I)
YMD_SEP_RE = re.compile(r"(?<!\d)(\d{4})[._](\d{2})[._](\d{2})(?!\d)")
DMY_RE = re.compile(r"(?<!\d)(\d{1,2})([-._ ])(\d{1,2})\2(\d{4}|\d{2})(?!\d)")
ISO_RE = re.compile(r"(?<!\d)(\d{4})-(\d{2})-(\d{2})(?!\d)")
COMPACT_RE = re.compile(r"(?<!\d)((?:19|20)\d{2})(0[1-9]|1[0-2])(0[1-9]|[12]\d|3[01])(?!\d)")
VER_RE = re.compile(r"(?i)(?:^|[-_ ])(?:v|ver|rev|version)[-_ ]?(\d+)$")
FINAL_TOKEN = re.compile(r"^(?:v\d+)?(?:final|latest|newest|real|actual|usethis|finished)+\d*$")
COPY_RE = re.compile(r"(?i)(?:\s\(\d+\)|\s-\s?copy(?:\s\(\d+\))?|\scopy(?:\s\d+)?|[_-]copy\d*)$|^copy of ")
DOUBLE_SEP_RE = re.compile(r"__|--|_-|-_")
PLACEHOLDER_RE = re.compile(r"\{([A-Za-z_][A-Za-z0-9_]*)\}")


class UsageError(Exception):
    pass


# ---------------------------------------------------------------- convention

class Convention:
    def __init__(self, pattern, source):
        self.pattern = pattern
        self.source = source
        parts, pos = [], 0
        for m in PLACEHOLDER_RE.finditer(pattern):
            if m.start() > pos:
                parts.append(("lit", pattern[pos:m.start()]))
            parts.append(("ph", m.group(1)))
            pos = m.end()
        if pos < len(pattern):
            parts.append(("lit", pattern[pos:]))
        if not any(k == "ph" for k, _ in parts):
            raise UsageError("convention %r has no {placeholder}" % pattern)
        for k, v in parts:
            if k == "lit":
                if "{" in v or "}" in v:
                    raise UsageError("unbalanced brace in convention %r" % pattern)
                if v != v.lower():
                    raise UsageError("literal text in the convention must be lower case: %r" % v)
                if any(c in FORBIDDEN or c in RISKY or c == " " for c in v):
                    raise UsageError("literal %r contains a character the audit itself forbids" % v)
        names = [v for k, v in parts if k == "ph"]
        if len(set(names)) != len(names):
            raise UsageError("placeholder names must be unique in %r" % pattern)
        self.date_style = None
        self.ver_width = None
        self.ver_prefix = None
        self.date_first = parts[0] in (("ph", "date"), ("ph", "date8"))
        lits = [v for k, v in parts if k == "lit"]
        self.sep = next((v for v in lits if v and set(v) <= set("_-")), "_")
        literal_seps = bool(lits)
        word = r"[^\W_]+"  # letters and digits of any script; lower case is enforced by the MIXED_CASE check
        free = word + "(?:-" + word + ")*" if literal_seps else word + "(?:[-_]" + word + ")*"
        rx = []
        for i, (k, v) in enumerate(parts):
            if k == "lit":
                rx.append(re.escape(v))
            elif v == "date":
                self.date_style = "iso"
                rx.append(r"(?P<date>\d{4}-\d{2}-\d{2})")
            elif v == "date8":
                self.date_style = "compact"
                rx.append(r"(?P<date8>\d{8})")
            elif re.fullmatch(r"n{2,4}", v):
                if self.ver_width:
                    raise UsageError("only one version placeholder is supported")
                prev = parts[i - 1][1] if i > 0 and parts[i - 1][0] == "lit" else ""
                if not prev.endswith("v"):
                    raise UsageError("put a literal ending in v right before {%s}, for example _v{%s}" % (v, v))
                self.ver_width = len(v)
                self.ver_prefix = prev
                rx.append(r"(?P<%s>\d{%d})" % (v, len(v)))
            else:
                rx.append(r"(?P<%s>%s)" % (v, free))
        self.regex = re.compile("".join(rx))
        self.date_groups = [g for g in ("date", "date8") if g in names]

    def matches(self, stem):
        m = self.regex.fullmatch(stem)
        if not m:
            return False
        for g in self.date_groups:
            raw = m.group(g)
            try:
                if g == "date":
                    datetime.date(int(raw[:4]), int(raw[5:7]), int(raw[8:10]))
                else:
                    datetime.date(int(raw[:4]), int(raw[4:6]), int(raw[6:8]))
            except ValueError:
                return False
        return True


class Ctx:
    def __init__(self, conv, date_order, date_from_mtime, ascii_only):
        self.conv = conv
        self.date_order = date_order
        self.date_from_mtime = date_from_mtime
        self.ascii_only = ascii_only


def infer_pattern(stems):
    """Build a pattern from the dominant features of the existing file stems."""
    n = len(stems)
    evidence = {"stems_considered": n}
    if n == 0:
        return "{name}", evidence
    iso = sum(1 for s in stems if re.match(r"\d{4}-\d{2}-\d{2}(?:[_-]|$)", s))
    compact = sum(1 for s in stems if re.match(r"(?:19|20)\d{6}(?:[_-]|$)", s) and COMPACT_RE.match(s))
    vers = [VER_RE.search(s) for s in stems]
    vcount = sum(1 for v in vers if v)
    unders = sum(s.count("_") for s in stems)
    hyph = sum(s.count("-") for s in stems)
    spaces = sum(s.count(" ") for s in stems)
    upper = sum(1 for s in stems if s != s.lower())
    evidence.update({"iso_date_prefix_share": round(iso / n, 2), "compact_date_prefix_share": round(compact / n, 2),
                     "version_share": round(vcount / n, 2),
                     "separator_counts": {"underscore": unders, "hyphen": hyph, "space": spaces},
                     "files_with_upper_case": upper})
    sep = "_" if unders > 0 else "-"
    style = None
    if iso / n >= SHARE_NEEDED and iso >= compact:
        style = "{date}"
    elif compact / n >= SHARE_NEEDED:
        style = "{date8}"
    widths = Counter(len(v.group(1)) for v in vers if v)
    width = max(2, sorted(widths.items(), key=lambda kv: (kv[1], kv[0]))[-1][0]) if widths else 2
    has_ver = vcount / n >= SHARE_NEEDED
    parts = []
    if style:
        parts.append(style)
    parts.append("{name}")
    pattern = sep.join(parts)
    if has_ver:
        pattern += sep + "v{" + "n" * width + "}"
    return pattern, evidence


# ---------------------------------------------------------------- name analysis

def split_ext(name):
    low = name.lower()
    for d in (".tar.gz", ".tar.bz2", ".tar.xz"):
        if low.endswith(d) and len(name) > len(d):
            return name[:-len(d)], name[-len(d):]
    stem, dot, ext = name.rpartition(".")
    if not dot or not stem or not re.fullmatch(r"[A-Za-z0-9]{1,8}", ext):
        return name, ""
    return stem, "." + ext


def fmt_date(y, m, d, style):
    return "%04d%02d%02d" % (y, m, d) if style == "compact" else "%04d-%02d-%02d" % (y, m, d)


def valid_date(y, m, d):
    try:
        datetime.date(y, m, d)
        return True
    except ValueError:
        return False


def fix_dates(s, ctx):
    """Convert recognised non-sortable or non-ISO dates. Returns (text, codes, undecided codes)."""
    codes, und = set(), set()
    style = ctx.conv.date_style or "iso"

    def good(y, m, d, code):
        if valid_date(y, m, d):
            codes.add(code)
            return True
        und.add("NON_SORTABLE_DATE")
        return False

    def dmon(m):
        d, mo, y = int(m.group(1)), MONTHS[m.group(2).lower()[:3]], int(m.group(3))
        return fmt_date(y, mo, d, style) if good(y, mo, d, "NON_SORTABLE_DATE") else m.group(0)

    def mond(m):
        mo, d, y = MONTHS[m.group(1).lower()[:3]], int(m.group(2)), int(m.group(3))
        return fmt_date(y, mo, d, style) if good(y, mo, d, "NON_SORTABLE_DATE") else m.group(0)

    def ymd(m):
        y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
        return fmt_date(y, mo, d, style) if good(y, mo, d, "NON_ISO_DATE") else m.group(0)

    def dmy(m):
        a, sep, b, yy = int(m.group(1)), m.group(2), int(m.group(3)), m.group(4)
        if len(yy) == 2 and sep == ".":
            return m.group(0)  # looks like a version number, not a date
        if len(yy) == 2:
            und.add("AMBIGUOUS_DATE")
            return m.group(0)
        y = int(yy)
        order = ctx.date_order
        if a > 12 and b <= 12:
            d, mo = a, b
        elif b > 12 and a <= 12:
            mo, d = a, b
        elif a == b:
            d, mo = a, b
        elif order == "dmy":
            d, mo = a, b
        elif order == "mdy":
            mo, d = a, b
        else:
            und.add("AMBIGUOUS_DATE")
            return m.group(0)
        return fmt_date(y, mo, d, style) if good(y, mo, d, "NON_SORTABLE_DATE") else m.group(0)

    s = DMON_RE.sub(dmon, s)
    s = MOND_RE.sub(mond, s)
    s = YMD_SEP_RE.sub(ymd, s)
    s = DMY_RE.sub(dmy, s)
    if ctx.conv.date_style == "iso":
        def comp(m):
            y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
            if valid_date(y, mo, d):
                codes.add("NON_ISO_DATE")
                return fmt_date(y, mo, d, "iso")
            return m.group(0)
        s = COMPACT_RE.sub(comp, s)
    elif ctx.conv.date_style == "compact":
        def iso(m):
            y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
            if valid_date(y, mo, d):
                codes.add("NON_ISO_DATE")
                return fmt_date(y, mo, d, "compact")
            return m.group(0)
        s = ISO_RE.sub(iso, s)
    return s, codes, und


def ascii_fold(s):
    out = []
    for c in unicodedata.normalize("NFKD", s):
        if not unicodedata.combining(c):
            out.append(c)
    return "".join(out)


def analyse(name, is_dir, ctx, mtime=None):
    """Return {"codes": [...], "new": str, "undecided": [...]} for one path component."""
    codes, und = set(), set()
    nm = unicodedata.normalize("NFC", name)
    if nm != name:
        codes.add("UNICODE_FORM")
    if ctx.ascii_only and any(ord(c) > 127 for c in nm):
        codes.add("NON_ASCII")
        folded = ascii_fold(nm)
        if any(ord(c) > 127 for c in folded):
            und.add("NON_ASCII")
        nm = folded
    stem, ext = (nm, "") if is_dir else split_ext(nm)
    if nm != nm.strip(" ") or nm.endswith("."):
        codes.add("TRAILING_DOT_SPACE")
    if any(c == " " or unicodedata.category(c) == "Zs" for c in nm):
        codes.add("SPACE")
    if any(c in FORBIDDEN or ord(c) < 32 or ord(c) == 127 for c in nm):
        codes.add("FORBIDDEN_CHAR")
    if any(c in RISKY for c in nm):
        codes.add("RISKY_CHAR")
    if not is_dir and stem != stem.lower():
        codes.add("MIXED_CASE")
    if ext != ext.lower():
        codes.add("UPPER_EXT")
    if DOUBLE_SEP_RE.search(stem):
        codes.add("DOUBLE_SEPARATOR")
    if stem.split(".")[0].strip().lower() in RESERVED:
        und.add("RESERVED_NAME")
    if len(nm) > LONG_NAME:
        und.add("LONG_NAME")
    if not is_dir:
        toks = re.split(r"[-_ .]+", stem.lower())
        if any(FINAL_TOKEN.match(t) for t in toks if t):
            und.add("FINAL_STYLE")
        if COPY_RE.search(stem):
            und.add("COPY_SUFFIX")

    conv = ctx.conv
    s = stem
    if not is_dir:
        s, dcodes, dund = fix_dates(s, ctx)
        codes |= dcodes
        und |= dund
    cleaned = []
    for c in s:
        if c in "'`":
            continue
        if c in FORBIDDEN or c in RISKY or ord(c) < 32 or ord(c) == 127 or unicodedata.category(c) == "Zs":
            cleaned.append(" ")
        else:
            cleaned.append(c)
    s = "".join(cleaned)
    if not is_dir:
        s = s.lower()
    if conv.sep == "_":
        s = re.sub(r"\s+", "-", s.strip())
        s = re.sub(r"[-_]*_[-_]*", "_", s)
    else:
        s = re.sub(r"[\s_]+", "-", s.strip())
    s = re.sub(r"-{2,}", "-", s).strip(" ").rstrip("-_. ")  # a leading _ or . is a deliberate sort or hidden marker
    if not is_dir and conv.sep == "_" and conv.date_style:
        s = re.sub(r"^(\d{4}-\d{2}-\d{2}|\d{8})-(?=[^-_])", r"\1_", s)  # the field after a leading date is separated by _
    if not s:
        return {"codes": sorted(codes | {"FORBIDDEN_CHAR"}), "new": name, "undecided": sorted(und | {"FORBIDDEN_CHAR"})}

    if not is_dir and conv.ver_width:
        m = VER_RE.search(s)
        if m:
            tail = conv.ver_prefix + m.group(1).zfill(conv.ver_width)
            if m.start() == 0:
                tail = "v" + m.group(1).zfill(conv.ver_width)
            if s[m.start():] != tail:
                codes.add("VERSION_FORMAT")
                s = s[:m.start()] + tail
        else:
            und.add("NO_VERSION")
    if not is_dir and conv.date_style:
        rx = ISO_RE if conv.date_style == "iso" else COMPACT_RE
        found = list(rx.finditer(s))
        if not found:
            if ctx.date_from_mtime and mtime is not None and conv.date_first:
                d = datetime.datetime.fromtimestamp(mtime, datetime.timezone.utc)
                s = fmt_date(d.year, d.month, d.day, conv.date_style) + conv.sep + s
                codes.add("NO_DATE")
            else:
                und.add("NO_DATE")
        elif conv.date_first and found[0].start() != 0:
            if len(found) == 1:
                tok = found[0].group(0)
                rest = (s[:found[0].start()] + s[found[0].end():]).strip("-_")
                rest = re.sub(r"[-_]*_[-_]*", "_", rest) if conv.sep == "_" else re.sub(r"-{2,}", "-", rest)
                s = tok + conv.sep + rest if rest else tok
                codes.add("DATE_POSITION")
            else:
                und.add("DATE_POSITION")
                codes.add("DATE_POSITION")
    new = s + ext.lower()
    if is_dir:
        new = s
    return {"codes": sorted(codes | und), "new": new, "undecided": sorted(und)}


def detect(name, is_dir, ctx, mtime=None):
    """Codes for a name as it stands, including a plain pattern mismatch for files."""
    res = analyse(name, is_dir, ctx, mtime=None)
    codes = set(res["codes"])
    if is_dir:
        codes &= DIR_CODES
    elif not codes and not ctx.conv.matches(split_ext(name)[0]):
        codes.add("PATTERN_MISMATCH")
    return sorted(codes)


# ---------------------------------------------------------------- tree reading

def read_listing(path):
    entries = []
    try:
        text = open(path, encoding="utf-8-sig", newline="").read()
    except (OSError, UnicodeDecodeError) as exc:
        raise UsageError("cannot read listing %s: %s" % (path, exc))
    for n, line in enumerate(text.splitlines(), 1):
        if not line.strip():
            continue
        rel, _, ts = line.partition("\t")
        rel = rel.strip().replace("\\", "/").lstrip("/")
        while rel.startswith("./"):
            rel = rel[2:]
        mtime = None
        if ts.strip():
            t = ts.strip()
            if t.endswith("Z"):
                t = t[:-1] + "+00:00"
            try:
                dt = datetime.datetime.fromisoformat(t)
            except ValueError:
                raise UsageError("listing line %d: bad timestamp %r" % (n, ts.strip()))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=datetime.timezone.utc)
            mtime = dt.timestamp()
        if rel:
            entries.append((rel, mtime, None))
    return entries


def walk_tree(root, include_hidden):
    entries, ignored, errors = [], 0, []
    for cur, dirs, files in os.walk(root, followlinks=False, onerror=lambda e: errors.append(str(e))):
        keep = []
        for d in sorted(dirs):
            full = os.path.join(cur, d)
            if os.path.islink(full) or d.lower() in IGNORED_DIRS or (d.startswith(".") and not include_hidden):
                ignored += 1
            else:
                keep.append(d)
        dirs[:] = keep
        for f in sorted(files):
            full = os.path.join(cur, f)
            if os.path.islink(full) or f.lower() in IGNORED_FILES or f.startswith("~$") or (f.startswith(".") and not include_hidden):
                ignored += 1
                continue
            try:
                mt = os.stat(full).st_mtime
            except OSError as exc:
                errors.append(str(exc))
                continue
            rel = os.path.relpath(full, root).replace(os.sep, "/")
            entries.append((rel, mt, full))
    return entries, ignored, errors


# ---------------------------------------------------------------- analysis

def ckey(name):
    return unicodedata.normalize("NFC", name).casefold()


def sha256(path):
    try:
        if os.path.getsize(path) > HASH_LIMIT:
            return None
        h = hashlib.sha256()
        with open(path, "rb") as fh:
            for chunk in iter(lambda: fh.read(1 << 20), b""):
                h.update(chunk)
        return h.hexdigest()
    except OSError:
        return None


def build_report(entries, ctx, conv_info, max_path, prefix_len):
    file_info = {}      # rel path -> (mtime, fullpath)
    for rel, mt, full in entries:
        file_info[rel] = (mt, full)
    files = sorted(file_info)
    dirs = set()
    for rel in files:
        parts = rel.split("/")
        for i in range(1, len(parts)):
            dirs.add("/".join(parts[:i]))
    dirs = sorted(dirs, key=lambda p: (p.count("/"), p))

    violations, needs_decision, held_back = {}, [], []
    plan_files = {}
    new_dirs = {}
    reasons = {}

    # ---- original problems per component
    def add_violation(path, kind, codes):
        if not codes:
            return
        rec = violations.setdefault(path, {"path": path, "kind": kind, "codes": set()})
        rec["codes"] |= set(codes)

    dir_res = {}
    for d in dirs:
        base = d.rsplit("/", 1)[-1]
        res = analyse(base, True, ctx)
        codes = [c for c in res["codes"] if c in DIR_CODES]
        dir_res[d] = (res, codes)
        add_violation(d, "dir", codes)
    file_res = {}
    for f in files:
        base = f.rsplit("/", 1)[-1]
        mt = file_info[f][0]
        res = analyse(base, False, ctx, mtime=mt)
        codes = detect(base, False, ctx)
        file_res[f] = (res, codes)
        add_violation(f, "file", codes)
    for p in list(files) + dirs:
        if len(p) + prefix_len > max_path:
            add_violation(p, "dir" if p in dir_res else "file", ["OVER_LENGTH"])

    # ---- version series (original names)
    series = defaultdict(list)
    for f in files:
        base = f.rsplit("/", 1)[-1]
        stem, ext = split_ext(base)
        m = VER_RE.search(unicodedata.normalize("NFC", stem))
        if m:
            label = re.sub(r"^(?:\d{4}-\d{2}-\d{2}|\d{8})[-_ ]?", "", unicodedata.normalize("NFC", stem)[:m.start()])
            key = (ckey(f.rsplit("/", 1)[0]) if "/" in f else "", ckey(label.strip("-_ ")), ext.lower())
            series[key].append((int(m.group(1)), f))
    version_series = []
    dup_files = set()
    for key, items in sorted(series.items()):
        if len(items) < 2:
            continue
        nums = sorted(n for n, _ in items)
        top_n = max(n for n, _ in items)
        tied = sorted(p for n, p in items if n == top_n)
        top = tied[0] if len(tied) == 1 else None  # two files share the highest number: no honest answer
        mts = [(file_info[p][0], p) for _, p in items if file_info[p][0] is not None]
        by_mtime = max(mts)[1] if len(mts) == len(items) else None
        dup = defaultdict(list)
        for n, p in items:
            dup[n].append(p)
        dups = [sorted(v) for v in dup.values() if len(v) > 1]
        for group in dups:
            dup_files.update(group)
            for p in group:
                add_violation(p, "file", ["DUPLICATE_VERSION"])
        gaps = [n for n in range(nums[0], nums[-1] + 1) if n not in dup] if nums[-1] - nums[0] <= 50 else []
        version_series.append({
            "series": "%s/%s*%s" % (key[0], key[1], key[2]) if key[0] else "%s*%s" % (key[1], key[2]),
            "versions": nums,
            "latest_by_number": top,
            "latest_ambiguous": top is None,
            "latest_by_mtime": by_mtime,
            "mtime_disagrees": bool(by_mtime and top and by_mtime != top),
            "duplicate_numbers": dups,
            "gaps": gaps})

    # ---- original collisions
    groups = defaultdict(list)
    for p in files + dirs:
        groups[tuple(ckey(c) for c in p.split("/"))].append(p)
    collisions = []
    for key, members in sorted(groups.items()):
        if len(members) < 2:
            continue
        kind = "case" if len({m.casefold() for m in members}) < len(members) or any(
            a != b and a.casefold() == b.casefold() for a in members for b in members) else "unicode"
        hashes = [sha256(file_info[m][1]) if m in file_info and file_info[m][1] else None for m in members]
        identical = None
        if all(m in file_info for m in members) and all(h for h in hashes):
            identical = len(set(hashes)) == 1
        collisions.append({"paths": sorted(members), "kind": kind, "identical_content": identical})

    # ---- plan: folders first, top-down, holding back anything that would collide
    def basename(p):
        return p.rsplit("/", 1)[-1]

    def parent(p):
        return p.rsplit("/", 1)[0] if "/" in p else ""

    cand = {}
    for d in dirs:
        res, codes = dir_res[d]
        new = res["new"]
        ok = new != basename(d) and not (set(detect(new, True, ctx)) & DIR_CODES)
        cand[d] = new if ok else basename(d)
        if not ok and codes:
            needs_decision.append({"path": d, "kind": "dir", "remaining": codes, "partial": None})
    by_parent = defaultdict(list)
    for d in dirs:
        by_parent[parent(d)].append(d)
    for par in sorted(by_parent, key=lambda p: (p.count("/"), p)):
        group = by_parent[par]
        while True:
            cnt = Counter(ckey(cand[d]) for d in group)
            bad = [d for d in group if cnt[ckey(cand[d])] > 1 and cand[d] != basename(d)]
            if not bad:
                break
            for d in bad:
                held_back.append({"path": d, "kind": "dir", "would_be": cand[d],
                                  "reason": "the new folder name collides with a sibling"})
                cand[d] = basename(d)
    for d in dirs:
        pnew = new_dirs.get(parent(d), "")
        new_dirs[d] = (pnew + "/" if pnew else "") + cand[d]

    # ---- plan: files, grouped by their final folder
    fcand = {}
    for f in files:
        res, codes = file_res[f]
        new = res["new"]
        base = basename(f)
        if new != base:
            after = set(detect(new, False, ctx)) | set(res["undecided"])
            if f in dup_files:
                after.add("DUPLICATE_VERSION")
            if after:
                needs_decision.append({"path": f, "kind": "file", "remaining": sorted(after), "partial": new})
                new = base
            else:
                reasons[f] = [c for c in res["codes"] if c not in res["undecided"]]
        elif codes or f in dup_files:
            rest = set(codes) | ({"DUPLICATE_VERSION"} if f in dup_files else set())
            needs_decision.append({"path": f, "kind": "file", "remaining": sorted(rest), "partial": None})
        fcand[f] = new
    by_dir = defaultdict(list)
    for f in files:
        by_dir[parent(f)].append(f)
    for dpath, group in by_dir.items():
        fixed_new = [cand[d] for d in dirs if parent(d) == dpath]
        while True:
            cnt = Counter(ckey(fcand[f]) for f in group)
            cnt.update(ckey(n) for n in fixed_new)
            bad = [f for f in group if cnt[ckey(fcand[f])] > 1 and fcand[f] != basename(f)]
            if not bad:
                break
            for f in bad:
                peers = sorted(p for p in group if p != f and ckey(fcand[p]) == ckey(fcand[f]))
                held_back.append({"path": f, "kind": "file", "would_be": fcand[f],
                                  "reason": "the new name collides with " + (", ".join(peers) if peers else "a folder in the same place")})
                fcand[f] = basename(f)
                reasons.pop(f, None)

    rename_plan = []
    final_path = {}
    for f in files:
        pnew = new_dirs.get(parent(f), "") if parent(f) else ""
        final = (pnew + "/" if pnew else "") + fcand[f]
        final_path[f] = final
        if final != f:
            why = list(reasons.get(f, []))
            if new_dirs.get(parent(f), parent(f)) != parent(f):
                why.append("FOLDER_RENAMED")
            rename_plan.append({"old": f, "new": final, "reasons": sorted(set(why))})
    dir_renames = [{"old": d, "new": new_dirs[d]} for d in dirs if new_dirs[d] != d]

    # ---- independent verification of the end state
    end = defaultdict(list)
    for f in files:
        end[tuple(ckey(c) for c in final_path[f].split("/"))].append(f)
    for d in dirs:
        end[tuple(ckey(c) for c in new_dirs[d].split("/"))].append(d)
    problems = []
    for key, members in end.items():
        if len(members) > 1:
            changed = [m for m in members if (final_path.get(m) or new_dirs.get(m)) != m]
            if changed:
                problems.append(sorted(members))

    held = {h["path"] for h in held_back}
    viol_list = []
    for p in sorted(violations):
        rec = violations[p]
        if p in held:
            fix = "held_back"
        elif "OVER_LENGTH" in rec["codes"]:
            fix = "needs_decision"
        elif rec["kind"] == "file" and p in reasons and final_path[p] != p:
            fix = "auto"
        elif rec["kind"] == "dir" and new_dirs.get(p, p) != p:
            fix = "auto"
        else:
            fix = "needs_decision"
        viol_list.append({"path": p, "kind": rec["kind"], "codes": sorted(rec["codes"]), "fix": fix})
    by_code = Counter(c for v in viol_list for c in v["codes"])
    nd = {}
    for item in needs_decision:
        nd[item["path"]] = item
    for v in viol_list:
        if v["fix"] == "needs_decision":
            if v["path"] not in nd:
                nd[v["path"]] = {"path": v["path"], "kind": v["kind"], "remaining": v["codes"], "partial": None}
            elif "OVER_LENGTH" in v["codes"] and "OVER_LENGTH" not in nd[v["path"]]["remaining"]:
                nd[v["path"]]["remaining"] = sorted(set(nd[v["path"]]["remaining"]) | {"OVER_LENGTH"})
    clean_files = sum(1 for f in files if f not in violations)

    return {
        "convention": conv_info,
        "files_total": len(files),
        "dirs_total": len(dirs),
        "files_without_violations": clean_files,
        "violations": viol_list,
        "violations_by_code": dict(sorted(by_code.items())),
        "collisions": collisions,
        "version_series": version_series,
        "rename_plan": rename_plan,
        "dir_renames": dir_renames,
        "held_back": sorted(held_back, key=lambda h: h["path"]),
        "needs_decision": [nd[k] for k in sorted(nd)],
        "plan_is_collision_free": not problems,
        "plan_problems": problems,
    }


# ---------------------------------------------------------------- output safety

def inside(path, root):
    try:
        return os.path.commonpath([path, root]) == root
    except ValueError:
        return False


def check_output(path, label, forbidden, root_real, force, taken):
    real = os.path.realpath(path)
    if real in forbidden:
        raise UsageError("%s path %s is an input; refusing to write it (--force does not override this)" % (label, path))
    if root_real and inside(real, root_real):
        raise UsageError("%s path %s is inside the audited folder; write it somewhere else" % (label, path))
    if real in taken:
        raise UsageError("--plan and --report must be different files")
    if os.path.exists(real) and not force:
        raise UsageError("%s path %s already exists; use --force to replace it" % (label, path))
    if not os.path.isdir(os.path.dirname(real) or "."):
        raise UsageError("folder for %s path %s does not exist" % (label, path))
    return real


def write_text(path, text):
    with open(path, "w", encoding="utf-8", newline="") as fh:
        fh.write(text)


def main(argv=None):
    ap = argparse.ArgumentParser(prog="naming_audit.py", description="Read-only audit of file and folder names.")
    ap.add_argument("root", nargs="?")
    ap.add_argument("--listing")
    ap.add_argument("--convention")
    ap.add_argument("--max-path", type=int, default=DEFAULT_MAX_PATH)
    ap.add_argument("--prefix-len", type=int, default=0)
    ap.add_argument("--date-order", choices=("dmy", "mdy"))
    ap.add_argument("--date-from-mtime", action="store_true")
    ap.add_argument("--ascii", action="store_true")
    ap.add_argument("--include-hidden", action="store_true")
    ap.add_argument("--plan")
    ap.add_argument("--report")
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args(argv)
    try:
        if bool(args.root) == bool(args.listing):
            raise UsageError("give either a ROOT folder or --listing FILE")
        if args.max_path < 20 or args.prefix_len < 0:
            raise UsageError("--max-path must be at least 20 and --prefix-len not negative")
        ignored, errors = 0, []
        forbidden, root_real = set(), None
        if args.listing:
            entries = read_listing(args.listing)
            forbidden.add(os.path.realpath(args.listing))
        else:
            if not os.path.isdir(args.root):
                raise UsageError("%s is not a folder" % args.root)
            root_real = os.path.realpath(args.root)
            entries, ignored, errors = walk_tree(args.root, args.include_hidden)
            forbidden.add(root_real)
            forbidden.update(os.path.realpath(e[2]) for e in entries)
        taken = set()
        plan_real = report_real = None
        if args.plan:
            plan_real = check_output(args.plan, "--plan", forbidden, root_real, args.force, taken)
            taken.add(plan_real)
        if args.report:
            report_real = check_output(args.report, "--report", forbidden, root_real, args.force, taken)
        if args.convention is not None:
            conv = Convention(args.convention, "given")
            info = {"source": "given", "pattern": args.convention, "needs_confirmation": False}
        else:
            stems = [split_ext(e[0].rsplit("/", 1)[-1])[0] for e in entries]
            pattern, evidence = infer_pattern(stems)
            conv = Convention(pattern, "inferred")
            info = {"source": "inferred", "pattern": pattern, "needs_confirmation": True, "evidence": evidence}
        ctx = Ctx(conv, args.date_order, args.date_from_mtime, args.ascii)
        report = build_report(entries, ctx, info, args.max_path, args.prefix_len)
    except UsageError as exc:
        sys.stderr.write("naming_audit: %s\n" % exc)
        return 2

    report["max_path"] = args.max_path
    report["prefix_len"] = args.prefix_len
    report["ignored"] = ignored
    report["walk_errors"] = errors[:20]
    report["plan_written"] = None
    if plan_real:
        buf = io.StringIO()
        w = csv.writer(buf, lineterminator="\n")
        w.writerow(["old", "new"])
        for r in report["rename_plan"]:
            w.writerow([r["old"], r["new"]])
        write_text(plan_real, buf.getvalue())
        report["plan_written"] = args.plan
    text = json.dumps(report, indent=2, ensure_ascii=True) + "\n"
    if report_real:
        write_text(report_real, text)
    sys.stdout.write(text)
    found = bool(report["violations"] or report["collisions"])
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main())
