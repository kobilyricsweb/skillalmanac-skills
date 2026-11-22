#!/usr/bin/env python3
"""Turn a large log file into a ranked table of error signatures.

    python cluster_logs.py LOG [LOG ...] [options]

Options
    --format auto|plain|jsonl   default auto: a line that is a JSON object is a JSON record,
                                everything else is parsed as plain text
    --min-level LEVEL           trace|debug|info|warning|error|critical (default error)
    --include-unknown           also keep records with no level (default: dropped)
    --since TS / --until TS     time window, ISO 8601 or YYYY-MM-DD; naive times mean UTC
    --baseline LOG              a second log (for example before a deploy); marks each cluster
                                new or not new against it and lists signatures that vanished
    --year N                    year for syslog stamps such as "Nov 20 10:15:30" (default: this year)
    --bucket-seconds N          size of the rate bucket (default 60)
    --merge-threshold X         token similarity 0.5-1.0 above which near signatures merge (default 0.85)
    --top N                     clusters to print (default 25)
    --out PATH [--force]        write the JSON report to PATH instead of stdout

Reads only the files named on the command line. Writes nothing unless --out is given. Never
writes over a log or baseline file: an --out path that resolves to an input is refused, even
with --force. Standard library only, no network.

Exit codes
    0 report produced and the logs parsed well
    1 report produced but unreliable: no records found, or more than half of the lines
      could not be parsed
    2 usage error, unreadable file, or refused output path

JSON contract (schema_version 1), printed to stdout or written to --out
    {"schema_version": 1, "command": "cluster", "files": [str], "baseline": str|null,
     "window": {"since": iso|null, "until": iso|null, "start": iso|null, "end": iso|null},
     "min_level": str, "stats": {...}, "warnings": [str],
     "total_clusters": int, "clusters_omitted": int,
     "clusters": [{"id": str, "triage_rank": int, "triage_reason": str, "signature": str,
                   "level": str, "count": int, "first_seen": iso|null, "last_seen": iso|null,
                   "rate_per_min": float|null, "peak": {"at": iso, "count": int}|null,
                   "histogram": [int x 24], "trend": str, "new_vs_baseline": bool|null,
                   "baseline_count": int|null, "sample": str, "stack_head": [str],
                   "merged_variants": [str]}],
     "vanished": [{"signature": str, "count": int, "last_seen": iso|null}]}
    Times are UTC, formatted YYYY-MM-DDTHH:MM:SSZ. Strict JSON: no NaN, no Infinity.
    trend is one of burst, rising, falling, steady, too_few, no_time.
    All text in sample, stack_head and signature has secret-looking strings masked.
"""
import argparse
import calendar
import collections
import datetime
import hashlib
import json
import os
import re
import sys

SCHEMA_VERSION = 1

LEVEL_RANK = {"trace": 0, "debug": 1, "info": 2, "warning": 3, "error": 4, "critical": 5}
# Every level word seen in the field mapped to the six classes above. SEVERE is Java's
# highest-but-fatal-less level and behaves like error; notice is below warning.
LEVEL_WORDS = {
    "trace": "trace", "debug": "debug", "info": "info", "notice": "info",
    "warn": "warning", "warning": "warning", "err": "error", "error": "error",
    "severe": "error", "crit": "critical", "critical": "critical", "fatal": "critical",
    "emerg": "critical", "emergency": "critical", "alert": "critical", "panic": "critical",
}
# Numeric levels in JSON logs follow the pino/bunyan convention.
NUMERIC_LEVELS = {10: "trace", 20: "debug", 30: "info", 40: "warning", 50: "error", 60: "critical"}

HISTOGRAM_SLOTS = 24          # enough to see a shape, small enough to print
MIN_EVENTS_FOR_TREND = 6      # below this a trend label would be noise
RISING_RATIO = 2.0            # second half at least twice the first half
MIN_TREND_DIFFERENCE = 3      # and at least 3 more events, so 1 -> 2 is not "rising"
BURST_MIN_EVENTS = 10         # a burst needs a real count
BURST_SHARE = 0.5             # in one bucket at least half of all events
SKEW_SECONDS = 60             # a timestamp this far behind the running maximum is a clock jump
MAX_LINE_CHARS = 5000         # longer lines are cut before parsing
SAMPLE_CHARS = 300
STACK_HEAD_LINES = 3
STACK_LINE_CHARS = 200
SIGNATURE_CHARS = 200         # signatures longer than this are cut so that long tails do not split clusters
MAX_SIGNATURES = 20000        # distinct signatures kept; more are counted but not clustered
MAX_MERGE_SIGNATURES = 2000   # near-merge is quadratic; above this it is skipped with a warning
MIN_MERGE_TOKENS = 5          # shorter messages differ by one word in meaning, so never merge them
UNPARSEABLE_WARN_SHARE = 0.2
UNPARSEABLE_FAIL_SHARE = 0.5

TS_ISO = re.compile(
    r"(\d{4})[-/](\d{2})[-/](\d{2})[T ](\d{2}):(\d{2}):(\d{2})(?:[.,](\d{1,9}))?"
    r"(?:\s?(Z)(?![A-Za-z])|\s?([+-]\d{2}:?\d{2})(?!\d))?")
TS_CLF = re.compile(r"(\d{2})/([A-Z][a-z]{2})/(\d{4}):(\d{2}):(\d{2}):(\d{2})(?:\s?([+-]\d{4}))?")
TS_SYSLOG = re.compile(r"\b([A-Z][a-z]{2})\s+(\d{1,2})\s+(\d{2}):(\d{2}):(\d{2})\b")
TS_EPOCH = re.compile(r"^\[?(\d{10}|\d{13})(?:\.(\d{1,6}))?\]?(?=\s)")
MONTHS = {m: i for i, m in enumerate(
    ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"], 1)}

LEVEL_BRACKET = re.compile(
    r"(?i)(?:\[\s*|\blevel[=:]\s*\"?|\blvl[=:]\s*\"?|\bseverity[=:]\s*\"?)"
    r"(trace|debug|info|notice|warn|warning|err|error|severe|crit|critical|fatal|emerg|emergency|alert|panic)"
    r"(?![A-Za-z])")
LEVEL_UPPER = re.compile(
    r"(?<![A-Za-z])(TRACE|DEBUG|INFO|NOTICE|WARN|WARNING|ERR|ERROR|SEVERE|CRIT|CRITICAL|FATAL|EMERG|EMERGENCY|ALERT|PANIC)(?![A-Za-z])")
LEVEL_LEADING = re.compile(
    r"(?i)^\s*(trace|debug|info|notice|warn|warning|err|error|severe|crit|critical|fatal|emerg|emergency|alert|panic)\s*[:|]")

STACK_START = re.compile(
    r"^(?:\s+\S|Traceback \(most recent call last\)|Caused by:|Exception in thread|panic:|goroutine \d+|"
    r"\.\.\. \d+ (?:more|common)|[A-Za-z_][\w.$]*(?:Error|Exception|Exit|Panic)\b)")
EXC_CLASS = re.compile(r"^\s*(?:Caused by:\s*)?([A-Za-z_][\w.$]*(?:Error|Exception|Exit|Panic))\b")
STACK_HINT = re.compile(r"Traceback \(most recent call last\)|(?:Error|Exception)\b|\bat [\w.$<>]+\(|panic:")

JSON_MSG_KEYS = ("msg", "message", "event", "log", "text")
JSON_LEVEL_KEYS = ("level", "severity", "lvl", "levelname", "severity_text", "log.level", "loglevel")
JSON_TIME_KEYS = ("timestamp", "@timestamp", "time", "ts", "asctime", "datetime", "t")
JSON_STACK_KEYS = ("stack", "stack_trace", "stacktrace", "traceback", "exception", "exc_info", "error.stack")

# Secret masking runs on every string that reaches the output. Content patterns only.
SECRET_PATTERNS = [
    ("private_key", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----.*?(?:-----END [A-Z ]*PRIVATE KEY-----|$)"), "<PRIVATE_KEY>"),
    ("aws_key", re.compile(r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b"), "<AWS_KEY>"),
    ("api_token", re.compile(r"\b(?:sk-[A-Za-z0-9_-]{16,}|gh[pousr]_[A-Za-z0-9]{30,}|xox[baprs]-[A-Za-z0-9-]{10,}"
                             r"|AIza[0-9A-Za-z_-]{35}|glpat-[A-Za-z0-9_-]{20,})"), "<API_TOKEN>"),
    ("jwt", re.compile(r"\beyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}"), "<JWT>"),
    ("bearer", re.compile(r"(?i)\b(Bearer|Basic)\s+[A-Za-z0-9._~+/=-]{12,}"), r"\1 <SECRET>"),
    ("keyed_value", re.compile(
        r"(?i)\b([\w.-]*(?:password|passwd|pwd|secret|token|api[_-]?key|access[_-]?key|authorization|credential)[\w.-]*)"
        r"(\s*[=:]\s*|\"\s*:\s*\"?)(\"[^\"]*\"|'[^']*'|[^\s,;&\"']+)"), r"\1\2<SECRET>"),
    ("url_credentials", re.compile(r"(?<=://)[^/\s:@]+:[^/\s@]+@"), "<CREDS>@"),
    ("email", re.compile(r"\b[\w.+-]+@[\w-]+(?:\.[\w-]+)+\b"), "<EMAIL>"),
    ("opaque_token", re.compile(r"\b(?=[A-Za-z0-9_-]*\d)(?=[A-Za-z0-9_-]*[A-Za-z])[A-Za-z0-9_-]{40,}\b"), "<SECRET>"),
]

# Signature normalisation, applied in this order. Order matters: URLs and paths are
# masked before bare numbers so that ports and segments do not leave stray digits.
NORMALISERS = [
    (re.compile(r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b"), "<UUID>"),
    (re.compile(r"(https?://[^/\s:?#]+)(?::\d+)?(?:/[^\s\"']*)?"), r"\1<PATH>"),
    (re.compile(r"\b\d{1,3}(?:\.\d{1,3}){3}(?::\d+)?\b"), "<IP>"),
    (re.compile(r"\b(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}\b"), "<IP>"),
    (re.compile(r"\b[A-Za-z]:\\(?:[^\s\\:*?\"<>|]+\\)*[^\s\\:*?\"<>|]*"), "<PATH>"),
    (re.compile(r"(?<![\w/<>.:)])/(?:[\w.@+~-]+/)*[\w.@+~-]+"), "<PATH>"),
    (re.compile(r"\b0x[0-9a-fA-F]+\b"), "<HEX>"),
    (re.compile(r"\b(?=[0-9a-f]*\d)(?=[0-9a-f]*[a-f])[0-9a-f]{8,}\b", re.I), "<HEX>"),
    (re.compile(r"\"[^\"\n]*\""), "<STR>"),
    (re.compile(r"(?<![\w'])'[^'\n]{1,200}'(?![\w'])"), "<STR>"),
    (re.compile(r"\d+(?:\.\d+)?"), "<N>"),
]
WHITESPACE = re.compile(r"\s+")


def mask_secrets(text, counter=None):
    """Return text with secret-looking strings replaced; count what was masked by kind."""
    for kind, pattern, repl in SECRET_PATTERNS:
        text, n = pattern.subn(repl, text)
        if n and counter is not None:
            counter[kind] += n
    return text


def normalise(message):
    """Replace variable parts with placeholders so equal errors become equal strings."""
    for pattern, repl in NORMALISERS:
        message = pattern.sub(repl, message)
    message = WHITESPACE.sub(" ", message).strip()
    return message[:SIGNATURE_CHARS] if message else "<empty>"


def epoch_to_iso(epoch):
    if epoch is None:
        return None
    moment = datetime.datetime(1970, 1, 1) + datetime.timedelta(seconds=int(epoch))
    return moment.strftime("%Y-%m-%dT%H:%M:%SZ")


def _make_epoch(year, month, day, hour, minute, second, frac, offset_seconds):
    try:
        datetime.datetime(year, month, day, hour, minute, second)
    except ValueError:
        return None
    return calendar.timegm((year, month, day, hour, minute, second)) - offset_seconds + frac


def _offset_seconds(text):
    if not text:
        return 0
    sign = -1 if text[0] == "-" else 1
    digits = text[1:].replace(":", "")
    return sign * (int(digits[:2]) * 3600 + int(digits[2:4]) * 60)


def parse_timestamp(text, year):
    """Find a timestamp in text. Return (epoch, tz_aware, start, end, kind) or None."""
    m = TS_ISO.search(text)
    if m:
        frac = float("0." + m.group(7)) if m.group(7) else 0.0
        zone = m.group(8) or m.group(9)
        epoch = _make_epoch(int(m.group(1)), int(m.group(2)), int(m.group(3)), int(m.group(4)),
                            int(m.group(5)), int(m.group(6)), frac, _offset_seconds("+0000" if m.group(8) else m.group(9)))
        if epoch is not None:
            return epoch, bool(zone), m.start(), m.end(), "iso"
    m = TS_CLF.search(text)
    if m and m.group(2) in MONTHS:
        epoch = _make_epoch(int(m.group(3)), MONTHS[m.group(2)], int(m.group(1)), int(m.group(4)),
                            int(m.group(5)), int(m.group(6)), 0.0, _offset_seconds(m.group(7)))
        if epoch is not None:
            return epoch, bool(m.group(7)), m.start(), m.end(), "clf"
    m = TS_EPOCH.search(text)
    if m:
        digits = m.group(1)
        value = int(digits) / (1000.0 if len(digits) == 13 else 1.0)
        return value, True, m.start(1), m.end(1), "epoch"
    m = TS_SYSLOG.search(text)
    if m and m.group(1) in MONTHS:
        epoch = _make_epoch(year, MONTHS[m.group(1)], int(m.group(2)), int(m.group(3)),
                            int(m.group(4)), int(m.group(5)), 0.0, 0)
        if epoch is not None:
            return epoch, False, m.start(), m.end(), "syslog"
    return None


def json_epoch(value, year):
    """Epoch seconds from a JSON time field (number or string), or None."""
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        v = float(value)
        if v > 1e17:
            v /= 1e9
        elif v > 1e14:
            v /= 1e6
        elif v > 1e11:
            v /= 1e3
        return v if v > 1e8 else None
    if isinstance(value, str):
        found = parse_timestamp(value, year)
        return found[0] if found else None
    return None


def json_level(value):
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return NUMERIC_LEVELS.get(int(value))
    if isinstance(value, str):
        return LEVEL_WORDS.get(value.strip().lower())
    return None


def find_level(text):
    """Return (level, start, end) for a level word near the start of text, or None."""
    head = text[:100]
    for pattern in (LEVEL_BRACKET, LEVEL_UPPER, LEVEL_LEADING):
        m = pattern.search(head)
        if m:
            word = LEVEL_WORDS.get(m.group(1).lower())
            if word:
                return word, m.start(1), m.end(1)
    return None


class Record:
    __slots__ = ("line_no", "epoch", "aware", "level", "message", "raw", "stack", "inferred", "kind")

    def __init__(self, line_no, epoch, aware, level, message, raw, stack=None):
        self.line_no = line_no
        self.epoch = epoch
        self.aware = aware
        self.level = level or "unknown"
        self.message = message
        self.raw = raw
        self.stack = stack or []
        self.inferred = False
        self.kind = None


def parse_json_line(line, line_no, year):
    try:
        obj = json.loads(line)
    except ValueError:
        return None
    if not isinstance(obj, dict):
        return None
    message = ""
    for key in JSON_MSG_KEYS:
        if isinstance(obj.get(key), str) and obj[key].strip():
            message = obj[key].strip()
            break
    if not message:
        for key in ("error", "err"):
            if isinstance(obj.get(key), str) and obj[key].strip():
                message = obj[key].strip()
                break
    level = None
    for key in JSON_LEVEL_KEYS:
        if key in obj:
            level = json_level(obj[key])
            if level:
                break
    epoch = None
    for key in JSON_TIME_KEYS:
        if key in obj:
            epoch = json_epoch(obj[key], year)
            if epoch is not None:
                break
    stack = []
    for key in JSON_STACK_KEYS:
        value = obj.get(key)
        if isinstance(value, str) and value.strip():
            stack = value.splitlines()
            break
    first, _, rest = message.partition("\n")
    if rest:
        stack = rest.splitlines() + stack
    return Record(line_no, epoch, epoch is not None, level, first.strip(), line, stack)


def parse_plain_line(line, line_no, year):
    """Return a Record if the line starts a log record, else None."""
    ts = parse_timestamp(line[:120], year)
    if ts and ts[2] > 40:
        ts = None
    rest = line
    epoch = aware = None
    if ts:
        epoch, aware = ts[0], ts[1]
        rest = line[:ts[2]] + " " + line[ts[3]:]
    lvl = find_level(rest.lstrip())
    stripped = rest.lstrip()
    level = None
    if lvl:
        word, s, e = lvl
        if ts or s <= 30:
            level = word
            rest = stripped[:s] + " " + stripped[e:]
    if not ts and not level:
        return None
    message = re.sub(r"^[\s\[\]\-|:,]+", "", rest)
    message = re.sub(r"^[\[\]\s|:,-]+", "", message.replace("[]", " "))
    record = Record(line_no, epoch, bool(aware) if ts else False, level, message.strip(), line)
    record.kind = ts[4] if ts else None
    return record


def open_lines(path):
    """Yield text lines from a file, handling UTF-8, UTF-8 BOM and UTF-16 (BOM)."""
    with open(path, "rb") as probe:
        head = probe.read(4)
    if head.startswith((b"\xff\xfe", b"\xfe\xff")):
        encoding = "utf-16"
    else:
        encoding = "utf-8-sig"
    with open(path, "r", encoding=encoding, errors="replace", newline=None) as handle:
        for line in handle:
            yield line.rstrip("\r\n")[:MAX_LINE_CHARS]


def stream_records(path, fmt, year, stats):
    """Yield finished Records with their stack lines attached; update line statistics."""
    current = None
    for line_no, line in enumerate(open_lines(path), 1):
        if not line.strip():
            continue
        stats["lines"] += 1
        record = None
        if fmt != "plain" and line.lstrip().startswith("{"):
            record = parse_json_line(line, line_no, year)
        if record is None and fmt != "jsonl":
            looks_continued = current is not None and STACK_START.match(line) and (
                line[:1].isspace() or not (parse_timestamp(line[:120], year) or find_level(line)))
            if looks_continued:
                current.stack.append(line)
                stats["continuation_lines"] += 1
                continue
            record = parse_plain_line(line, line_no, year)
        if record is None:
            stats["unparseable_lines"] += 1
            if len(stats["unparseable_examples"]) < 3:
                stats["unparseable_examples"].append(line[:120])
            continue
        if current is not None:
            yield current
        current = record
    if current is not None:
        yield current


def similar(tokens_a, tokens_b, threshold):
    if not tokens_a or not tokens_b:
        return False
    small, large = sorted((len(tokens_a), len(tokens_b)))
    if small < MIN_MERGE_TOKENS or large > small * 1.5:
        return False
    inter = len(tokens_a & tokens_b)
    return inter / float(len(tokens_a | tokens_b)) >= threshold


class Cluster:
    __slots__ = ("signature", "exc", "level_class", "count", "count_timed", "first", "last", "levels",
                 "buckets", "sample", "stack_head", "variants", "tokens")

    def __init__(self, signature, exc, level_class):
        self.signature = signature
        self.exc = exc
        self.level_class = level_class
        self.count = 0
        self.count_timed = 0
        self.first = None
        self.last = None
        self.levels = collections.Counter()
        self.buckets = collections.Counter()
        self.sample = ""
        self.stack_head = []
        self.variants = []
        self.tokens = frozenset(signature.split())

    def absorb(self, other):
        self.count += other.count
        self.count_timed += other.count_timed
        for attr, pick in (("first", min), ("last", max)):
            a, b = getattr(self, attr), getattr(other, attr)
            setattr(self, attr, b if a is None else a if b is None else pick(a, b))
        self.levels.update(other.levels)
        self.buckets.update(other.buckets)
        if other.signature not in self.variants and len(self.variants) < 3:
            self.variants.append(other.signature)


def level_class(level):
    rank = LEVEL_RANK.get(level, -1)
    return "critical" if rank >= 5 else "error" if rank == 4 else "warning" if rank == 3 else "other"


class Clusterer:
    def __init__(self, bucket_seconds, threshold):
        self.bucket_seconds = bucket_seconds
        self.threshold = threshold
        self.by_key = {}
        self.overflow = 0
        self.secrets = collections.Counter()
        self.merged = None

    def add(self, record):
        exc = ""
        for line in record.stack:
            m = EXC_CLASS.match(line)
            if m:
                exc = m.group(1)
        message = mask_secrets(record.message, self.secrets)
        signature = normalise(message)
        key = (signature, exc, level_class(record.level))
        cluster = self.by_key.get(key)
        if cluster is None:
            if len(self.by_key) >= MAX_SIGNATURES:
                self.overflow += 1
                return
            cluster = Cluster(signature, exc, key[2])
            self.by_key[key] = cluster
            cluster.sample = mask_secrets(record.raw)[:SAMPLE_CHARS]
            cluster.stack_head = [mask_secrets(s.strip())[:STACK_LINE_CHARS]
                                  for s in record.stack[:STACK_HEAD_LINES]]
        cluster.count += 1
        cluster.levels[record.level] += 1
        if record.epoch is not None:
            cluster.count_timed += 1
            cluster.buckets[int(record.epoch) // self.bucket_seconds * self.bucket_seconds] += 1
            cluster.first = record.epoch if cluster.first is None else min(cluster.first, record.epoch)
            cluster.last = record.epoch if cluster.last is None else max(cluster.last, record.epoch)

    def merge_near(self, warnings):
        clusters = sorted(self.by_key.values(), key=lambda c: -c.count)
        if len(clusters) > MAX_MERGE_SIGNATURES:
            warnings.append("near-signature merge skipped: %d distinct signatures is above %d"
                            % (len(clusters), MAX_MERGE_SIGNATURES))
            self.merged = clusters
            return
        kept = []
        for cluster in clusters:
            target = None
            for candidate in kept:
                if (candidate.exc == cluster.exc and candidate.level_class == cluster.level_class
                        and similar(candidate.tokens, cluster.tokens, self.threshold)):
                    target = candidate
                    break
            if target is None:
                kept.append(cluster)
            else:
                target.absorb(cluster)
        self.merged = kept

    def match(self, cluster):
        """Find this cluster (or a near one) in an already merged clusterer; return it or None."""
        for other in self.merged:
            if other.exc != cluster.exc or other.level_class != cluster.level_class:
                continue
            if (other.signature == cluster.signature or cluster.signature in other.variants
                    or similar(other.tokens, cluster.tokens, self.threshold)):
                return other
        return None


def new_stats():
    return {"lines": 0, "continuation_lines": 0, "unparseable_lines": 0, "unparseable_examples": [],
            "records": 0, "records_by_level": collections.Counter(), "in_scope": 0, "no_time_records": 0,
            "excluded_by_window": 0, "level_inferred": 0, "backward_jumps": 0, "max_backward_seconds": 0,
            "naive_timestamps": 0, "aware_timestamps": 0, "syslog_timestamps": 0}


def scan_log(paths, args, since, until, role):
    """Stream the logs once. Return (clusterer, pre_window clusterer, stats, window bounds)."""
    main_c = Clusterer(args.bucket_seconds, args.merge_threshold)
    pre_c = Clusterer(args.bucket_seconds, args.merge_threshold)
    stats = new_stats()
    min_rank = LEVEL_RANK[args.min_level]
    lo = hi = None
    for path in paths:
        running_max = None
        for record in stream_records(path, args.format, args.year, stats):
            stats["records"] += 1
            if record.level == "unknown" and any(STACK_HINT.search(s) for s in record.stack):
                record.level, record.inferred = "error", True
                stats["level_inferred"] += 1
            stats["records_by_level"][record.level] += 1
            if record.kind == "syslog":
                stats["syslog_timestamps"] += 1
            if record.epoch is not None:
                stats["aware_timestamps" if record.aware else "naive_timestamps"] += 1
                if running_max is not None and record.epoch < running_max - SKEW_SECONDS:
                    stats["backward_jumps"] += 1
                    stats["max_backward_seconds"] = max(stats["max_backward_seconds"], int(running_max - record.epoch))
                running_max = record.epoch if running_max is None else max(running_max, record.epoch)
            else:
                stats["no_time_records"] += 1
            rank = LEVEL_RANK.get(record.level, -1)
            if rank < min_rank and not (record.level == "unknown" and args.include_unknown):
                continue
            if role == "main" and (since is not None or until is not None):
                if record.epoch is None:
                    stats["excluded_by_window"] += 1
                    continue
                if since is not None and record.epoch < since:
                    pre_c.add(record)
                    stats["excluded_by_window"] += 1
                    continue
                if until is not None and record.epoch >= until:
                    stats["excluded_by_window"] += 1
                    continue
            stats["in_scope"] += 1
            main_c.add(record)
            if record.epoch is not None:
                lo = record.epoch if lo is None else min(lo, record.epoch)
                hi = record.epoch if hi is None else max(hi, record.epoch)
    return main_c, pre_c, stats, (lo, hi)


def trend_of(cluster, histogram, peak_count):
    n = cluster.count_timed
    if n == 0:
        return "no_time"
    if n < MIN_EVENTS_FOR_TREND:
        return "too_few"
    if peak_count >= BURST_MIN_EVENTS and peak_count / float(n) >= BURST_SHARE:
        return "burst"
    half = HISTOGRAM_SLOTS // 2
    first, second = sum(histogram[:half]), sum(histogram[half:])
    if second >= RISING_RATIO * first and second - first >= MIN_TREND_DIFFERENCE:
        return "rising"
    if first >= RISING_RATIO * second and first - second >= MIN_TREND_DIFFERENCE:
        return "falling"
    return "steady"


def build_cluster_row(cluster, start, end, comparison):
    span = (end - start) if (start is not None and end is not None) else 0
    histogram = [0] * HISTOGRAM_SLOTS
    peak_bucket, peak_count = None, 0
    for bucket, n in cluster.buckets.items():
        if span > 0:
            slot = min(HISTOGRAM_SLOTS - 1, max(0, int((bucket - start) * HISTOGRAM_SLOTS / span)))
        else:
            slot = 0
        histogram[slot] += n
        if n > peak_count or (n == peak_count and peak_bucket is not None and bucket < peak_bucket):
            peak_bucket, peak_count = bucket, n
    trend = trend_of(cluster, histogram, peak_count)
    rate = round(cluster.count_timed / (span / 60.0), 3) if span >= 60 and cluster.count_timed else None
    level = max(cluster.levels, key=lambda lv: (LEVEL_RANK.get(lv, -1), cluster.levels[lv]))
    new_flag = None
    base_count = None
    if comparison is not None:
        found = comparison.match(cluster)
        new_flag = found is None
        base_count = found.count if found else 0
    sig_id = hashlib.sha1((cluster.signature + "|" + cluster.exc).encode("utf-8")).hexdigest()[:8]
    shown_signature = cluster.signature + ((" || " + cluster.exc) if cluster.exc else "")
    return {
        "id": sig_id, "triage_rank": 0, "triage_reason": "", "signature": shown_signature, "level": level,
        "count": cluster.count, "first_seen": epoch_to_iso(cluster.first), "last_seen": epoch_to_iso(cluster.last),
        "rate_per_min": rate,
        "peak": {"at": epoch_to_iso(peak_bucket), "count": peak_count} if peak_bucket is not None else None,
        "histogram": histogram, "trend": trend, "new_vs_baseline": new_flag, "baseline_count": base_count,
        "sample": cluster.sample, "stack_head": cluster.stack_head, "merged_variants": cluster.variants,
        "_first": cluster.first if cluster.first is not None else float("inf"),
    }


def triage(rows, new_label):
    """Order rows: new first, then rising or burst, then the rest by count; ties by first seen."""
    for row in rows:
        if row["new_vs_baseline"] is True:
            row["_tier"], row["triage_reason"] = 0, new_label
        elif row["trend"] in ("rising", "burst"):
            row["_tier"], row["triage_reason"] = 1, "rate is " + row["trend"]
        else:
            row["_tier"], row["triage_reason"] = 2, "ranked by count"
    rows.sort(key=lambda r: (r["_tier"], -r["count"], r["_first"], r["signature"]))
    for rank, row in enumerate(rows, 1):
        row["triage_rank"] = rank
        del row["_tier"], row["_first"]


def parse_bound(text):
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", text.strip()):
        text = text.strip() + "T00:00:00"
    found = parse_timestamp(text, 2000)
    return found[0] if found else None


def refuse_output(out_path, inputs):
    real_out = os.path.realpath(out_path)
    for path in inputs:
        if os.path.realpath(path) == real_out:
            return True
        try:
            if os.path.exists(out_path) and os.path.samefile(out_path, path):
                return True
        except OSError:
            pass
    return False


def build_parser():
    p = argparse.ArgumentParser(prog="cluster_logs.py", description="Cluster log lines into error signatures.")
    p.add_argument("logs", nargs="+")
    p.add_argument("--format", choices=("auto", "plain", "jsonl"), default="auto")
    p.add_argument("--min-level", choices=sorted(LEVEL_RANK, key=LEVEL_RANK.get), default="error")
    p.add_argument("--include-unknown", action="store_true")
    p.add_argument("--since")
    p.add_argument("--until")
    p.add_argument("--baseline")
    p.add_argument("--year", type=int, default=datetime.date.today().year)
    p.add_argument("--bucket-seconds", type=int, default=60)
    p.add_argument("--merge-threshold", type=float, default=0.85)
    p.add_argument("--top", type=int, default=25)
    p.add_argument("--out")
    p.add_argument("--force", action="store_true")
    return p


def main(argv=None):
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        return 2 if exc.code else 0
    problems = []
    if args.bucket_seconds < 1:
        problems.append("--bucket-seconds must be at least 1")
    if not 0.5 <= args.merge_threshold <= 1.0:
        problems.append("--merge-threshold must be between 0.5 and 1.0")
    if args.top < 1:
        problems.append("--top must be at least 1")
    since = until = None
    if args.since:
        since = parse_bound(args.since)
        if since is None:
            problems.append("--since is not an ISO 8601 time: " + args.since)
    if args.until:
        until = parse_bound(args.until)
        if until is None:
            problems.append("--until is not an ISO 8601 time: " + args.until)
    if since is not None and until is not None and since >= until:
        problems.append("--since must be earlier than --until")
    inputs = list(args.logs) + ([args.baseline] if args.baseline else [])
    for path in inputs:
        if not os.path.isfile(path):
            problems.append("file not found or not a file: " + path)
    if args.out:
        if refuse_output(args.out, inputs):
            problems.append("refusing to write the report over an input file: " + args.out)
        elif os.path.isdir(args.out):
            problems.append("--out is a directory: " + args.out)
        elif os.path.exists(args.out) and not args.force:
            problems.append("--out exists; pass --force to replace it: " + args.out)
    if problems:
        for message in problems:
            sys.stderr.write("error: " + message + "\n")
        return 2

    warnings = []
    main_c, pre_c, stats, (lo, hi) = scan_log(args.logs, args, since, until, "main")
    main_c.merge_near(warnings)
    comparison = None
    if args.baseline:
        comparison = scan_log([args.baseline], args, None, None, "baseline")[0]
        comparison.merge_near(warnings)
    elif since is not None:
        pre_c.merge_near(warnings)
        comparison = pre_c
    start = since if since is not None else lo
    end = until if until is not None else hi
    rows = [build_cluster_row(c, start, end, comparison) for c in main_c.merged]
    triage(rows, "new compared with the baseline" if args.baseline else "new in the window: not seen earlier in the log")

    vanished = []
    if comparison is not None and args.baseline:
        current = Clusterer(args.bucket_seconds, args.merge_threshold)
        current.merged = main_c.merged
        for old in sorted(comparison.merged, key=lambda c: -c.count):
            if current.match(old) is None:
                vanished.append({"signature": old.signature + ((" || " + old.exc) if old.exc else ""),
                                 "count": old.count, "last_seen": epoch_to_iso(old.last)})
        vanished = vanished[:20]

    lines = max(stats["lines"], 1)
    share = round(stats["unparseable_lines"] / float(lines), 4)
    if share > UNPARSEABLE_WARN_SHARE:
        warnings.append("%.0f%% of lines could not be parsed as log records; counts are a lower bound" % (share * 100))
    if stats["backward_jumps"]:
        warnings.append("clock skew: %d timestamps are more than %d s behind an earlier one (largest %d s); "
                        "first/last seen and rates may be off" % (stats["backward_jumps"], SKEW_SECONDS, stats["max_backward_seconds"]))
    if stats["naive_timestamps"] and stats["aware_timestamps"]:
        warnings.append("mixed timestamps with and without a time zone; times without one were read as UTC")
    elif stats["naive_timestamps"]:
        warnings.append("timestamps carry no time zone; they were read as UTC")
    if stats["records"] and stats["no_time_records"] == stats["records"]:
        warnings.append("no record has a timestamp; first_seen, last_seen, rate and trend are unavailable")
    if main_c.overflow:
        warnings.append("%d records belonged to signatures beyond the %d tracked and were not clustered"
                        % (main_c.overflow, MAX_SIGNATURES))
    if stats["syslog_timestamps"]:
        warnings.append("syslog timestamps have no year; year %d was assumed (use --year)" % args.year)

    stats_out = {k: (dict(sorted(v.items())) if isinstance(v, collections.Counter) else v) for k, v in stats.items()}
    stats_out["unparseable_share"] = share
    stats_out["secrets_masked"] = dict(sorted((main_c.secrets + pre_c.secrets).items()))
    report = {
        "schema_version": SCHEMA_VERSION, "command": "cluster", "files": list(args.logs),
        "baseline": args.baseline, "min_level": args.min_level,
        "window": {"since": epoch_to_iso(since), "until": epoch_to_iso(until),
                   "start": epoch_to_iso(start), "end": epoch_to_iso(end)},
        "stats": stats_out, "warnings": warnings, "total_clusters": len(rows),
        "clusters_omitted": max(0, len(rows) - args.top), "clusters": rows[:args.top], "vanished": vanished,
    }
    text = json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False)
    if args.out:
        with open(args.out, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(text + "\n")
        print(json.dumps({"wrote": args.out, "total_clusters": len(rows)}))
    else:
        print(text)
    if stats["records"] == 0 or share > UNPARSEABLE_FAIL_SHARE:
        return 1
    return 0


if __name__ == "__main__":
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass
    sys.exit(main())
