#!/usr/bin/env python3
"""Profile one CSV file and print a strict-JSON report. Standard library only.

Usage:
    python eda_profile.py data.csv
    python eda_profile.py data.csv --target churned
    python eda_profile.py data.csv --delimiter ";" --max-rows 200000 --top 8 --no-corr --strict

Reads the file you name and prints JSON to standard output (ASCII only, no NaN or
Infinity). It writes nothing, uses no network and starts no processes.

Per column it reports: inferred type, missing count and percent (and which tokens
counted as missing), distinct count, numeric summary (min, p05, p25, median, p75,
p95, max, mean, std, zeros, negatives, Tukey outlier counts), top values,
string length, date range and row order, and a list of flags (constant, likely id,
mixed types, suspected sentinel codes, zero-padded codes, case variants, ...).
At file level it reports bad rows, exact duplicate rows, near-duplicate numeric
column pairs (Pearson) and, with --target, leakage candidates.

Bad rows (field count different from the header, or a csv parse error) are
excluded from every statistic and listed by line number. Blank lines are skipped.

Exit codes: 0 report printed; 1 report printed but --strict was given and bad rows
exist; 2 the file could not be read, has no header or no data rows, or the
arguments are wrong (a one-line message goes to standard error).
"""
import argparse
import csv
import json
import math
import os
import re
import sys
from array import array
from collections import Counter
from datetime import datetime

VERSION = "1.0.0"

# Tokens read as "missing" after strip and lower-casing. "none" and "-" can be real
# categories in some files; the report lists which tokens matched so the analyst can check.
NULL_TOKENS = {"", "na", "n/a", "#n/a", "null", "none", "nan", "nil", "-", "--", "?", "#null!"}
BOOL_TOKENS = {"true", "false", "yes", "no", "t", "f", "y", "n"}

# A column takes a type when at least this share of its non-missing values fit it.
TYPE_SHARE = 0.95
# Stop adding new distinct values to the counter beyond this (counts of known values go on).
MAX_DISTINCT = 50000
# Largest file slice profiled by default; protects memory (8 bytes per numeric cell).
DEFAULT_MAX_ROWS = 500000
# Correlation is computed on at most this many evenly spaced rows and this many columns,
# so the pure-Python pair loop stays near ten seconds.
CORR_SAMPLE_ROWS = 20000
CORR_MAX_COLS = 30
CORR_MIN_PAIRS = 30       # fewer shared rows than this gives r = null
NEAR_DUP_R = 0.9          # |r| at or above this is listed as a near-duplicate pair
LEAK_R = 0.95             # |r| with the target at or above this is a leakage candidate
LEAK_PURITY = 0.99        # one category maps to one target class at least this often
LEAK_PURITY_LIFT = 0.03   # ...and beats the majority-class share by at least this much
PAIR_CAP = 2000          # value/target pairs tracked per column before giving up
TARGET_CLASS_MAX = 20     # a target with more distinct values is treated as continuous
NEAR_CONSTANT = 0.99      # top value share that makes a column near-constant
ID_UNIQUE_MIN_ROWS = 20   # "all values unique" is only meaningful above this many rows
SENTINELS = {-99999, -9999, -999, -99, -9, 99, 999, 9999, 99999, 999999}
MAX_ROW_SPAN_LINES = 100  # a csv record spanning more physical lines than this hints at a stray quote
CHUNK = 1 << 20
NAN = float("nan")

INT_RE = re.compile(r"^[+-]?\d+$")
FLOAT_RE = re.compile(r"^[+-]?(\d+\.\d*|\.\d+|\d+)([eE][+-]?\d+)?$")
FORMATTED_RE = re.compile(
    r"^[+-]?[$€£]?\s?[+-]?\d{1,3}(,\d{3})+(\.\d+)?%?$"
    r"|^[$€£]\s?[+-]?\d+(\.\d+)?%?$"
    r"|^[+-]?\d+(\.\d+)?%$"
)
ISO_RE = re.compile(
    r"^(\d{4})-(\d{2})-(\d{2})(?:[T ](\d{2}):(\d{2})(?::(\d{2})(?:\.\d+)?)?)?\s?(?:Z|[+-]\d{2}:?\d{2})?$"
)
YMD_SLASH_RE = re.compile(r"^(\d{4})/(\d{1,2})/(\d{1,2})(?:[ T](\d{1,2}):(\d{2})(?::(\d{2}))?)?$")
NUM_DATE_RE = re.compile(r"^(\d{1,2})([/.\-])(\d{1,2})\2(\d{4})(?:[ T](\d{1,2}):(\d{2})(?::(\d{2}))?)?$")
MON_RE1 = re.compile(r"^(\d{1,2})[- ]([A-Za-z]{3,9})[- ](\d{4})$")
MON_RE2 = re.compile(r"^([A-Za-z]{3,9})\.? (\d{1,2}),? (\d{4})$")
MONTHS = {m: i + 1 for i, m in enumerate("jan feb mar apr may jun jul aug sep oct nov dec".split())}
ID_NAME_RE = re.compile(r"(^|[_\s.-])(id|uuid|guid|key|pk|idx|index)$|^id[_\s.-]|^(row|record)[_\s-]?(no|num|number)$", re.I)
YEAR_NAME_RE = re.compile(r"year|yr", re.I)


def _mk(y, mo, d, hh=0, mi=0, ss=0):
    try:
        return datetime(int(y), int(mo), int(d), int(hh or 0), int(mi or 0), int(ss or 0))
    except ValueError:
        return None


def parse_date(s):
    """Return (list of (format_key, datetime), has_time) or None when s is not a date."""
    m = ISO_RE.match(s)
    if m:
        dt = _mk(*m.group(1, 2, 3, 4, 5, 6))
        return ([("iso", dt)], m.group(4) is not None) if dt else None
    m = YMD_SLASH_RE.match(s)
    if m:
        dt = _mk(*m.group(1, 2, 3, 4, 5, 6))
        return ([("ymd/", dt)], m.group(4) is not None) if dt else None
    m = NUM_DATE_RE.match(s)
    if m:
        a, sep, b, y, hh, mi, ss = m.groups()
        out = []
        mdy = _mk(y, a, b, hh, mi, ss)
        dmy = _mk(y, b, a, hh, mi, ss)
        if mdy:
            out.append(("mdy" + sep, mdy))
        if dmy:
            out.append(("dmy" + sep, dmy))
        return (out, hh is not None) if out else None
    m = MON_RE1.match(s)
    if m and m.group(2)[:3].lower() in MONTHS:
        dt = _mk(m.group(3), MONTHS[m.group(2)[:3].lower()], m.group(1))
        return ([("d-mon-y", dt)], False) if dt else None
    m = MON_RE2.match(s)
    if m and m.group(1)[:3].lower() in MONTHS:
        dt = _mk(m.group(3), MONTHS[m.group(1)[:3].lower()], m.group(2))
        return ([("mon d, y", dt)], False) if dt else None
    return None


def classify(s):
    """Return (kind, value, flag). kind is bool, int, float, date or str."""
    if s.lower() in BOOL_TOKENS:
        return "bool", None, None
    if INT_RE.match(s):
        digits = s.lstrip("+-")
        if len(digits) > 1 and digits[0] == "0":
            return "str", None, "zero_padded"      # zip codes, product codes: not numbers
        if len(digits) > 15:
            return "str", None, "long_digits"      # beyond float precision: an identifier
        return "int", float(int(s)), None
    if FLOAT_RE.match(s):
        v = float(s)
        if not math.isfinite(v):
            return "str", None, "nonfinite"
        return "float", v, None
    if FORMATTED_RE.match(s):
        t = re.sub(r"[,$€£%\s]", "", s)
        return ("float" if "." in t else "int"), float(t), "formatted"
    d = parse_date(s)
    if d:
        return "date", d, None
    return "str", None, None


def num(x):
    """JSON-safe number: None for nan or inf, an int for whole numbers, else 6 significant digits."""
    if x is None or not math.isfinite(x):
        return None
    if x == int(x) and abs(x) < 1e15:
        return int(x)
    return float("%.6g" % x)


def pct(a, b):
    return round(100.0 * a / b, 2) if b else None


def percentile(sorted_vals, p):
    pos = (len(sorted_vals) - 1) * p
    lo = int(math.floor(pos))
    hi = min(lo + 1, len(sorted_vals) - 1)
    return sorted_vals[lo] + (sorted_vals[hi] - sorted_vals[lo]) * (pos - lo)


class Col:
    def __init__(self, name, index):
        self.name = name
        self.index = index
        self.n = 0
        self.missing = 0
        self.tokens = Counter()
        self.kinds = Counter()
        self.flags = Counter()
        self.samples = {}
        self.counts = Counter()
        self.capped = False
        self.nums = None
        self.padded = 0
        self.len_min = None
        self.len_max = 0
        self.len_sum = 0
        self.len_n = 0
        self.fmts = {}
        self.has_time = False
        self.pairs = Counter()

    def sample(self, key, s):
        lst = self.samples.setdefault(key, [])
        if len(lst) < 3 and s not in lst:
            lst.append(s[:60])

    def add(self, raw, tval):
        n = self.n
        self.n += 1
        s = raw.strip()
        if s != raw:
            self.padded += 1
        low = s.lower()
        if low in NULL_TOKENS:
            self.missing += 1
            self.tokens[low if low else "(empty)"] += 1
            if self.nums is not None:
                self.nums.append(NAN)
            if tval is not None and self.pairs is not None:
                # missingness itself can leak the outcome (a field filled in only after it happens)
                key = ("(missing)", tval)
                if key in self.pairs or len(self.pairs) < PAIR_CAP:
                    self.pairs[key] += 1
                else:
                    self.pairs = None
            return
        kind, val, flag = classify(s)
        self.kinds[kind] += 1
        if flag:
            self.flags[flag] += 1
            self.sample(flag, s)
        self.sample(kind, s)
        if s in self.counts or len(self.counts) < MAX_DISTINCT:
            self.counts[s] += 1
        else:
            self.capped = True
        if kind in ("int", "float"):
            if self.nums is None:
                self.nums = array("d", [NAN]) * n
            self.nums.append(val)
        elif self.nums is not None:
            self.nums.append(NAN)
        if kind == "str":
            ln = len(s)
            self.len_min = ln if self.len_min is None else min(self.len_min, ln)
            self.len_max = max(self.len_max, ln)
            self.len_sum += ln
            self.len_n += 1
        elif kind == "date":
            cands, has_time = val
            self.has_time = self.has_time or has_time
            for key, dt in cands:
                f = self.fmts.setdefault(key, {"n": 0, "min": dt, "max": dt, "prev": None, "asc": 0, "desc": 0})
                f["n"] += 1
                if dt < f["min"]:
                    f["min"] = dt
                if dt > f["max"]:
                    f["max"] = dt
                if f["prev"] is not None:
                    if dt < f["prev"]:
                        f["asc"] += 1
                    if dt > f["prev"]:
                        f["desc"] += 1
                f["prev"] = dt
        if tval is not None and self.pairs is not None:
            key = (s, tval)
            if key in self.pairs or len(self.pairs) < PAIR_CAP:
                self.pairs[key] += 1
            else:
                self.pairs = None


def numeric_summary(values):
    vals = sorted(values)
    n = len(vals)
    mean = math.fsum(vals) / n
    std = math.sqrt(math.fsum((v - mean) ** 2 for v in vals) / (n - 1)) if n > 1 else 0.0
    q1, q3 = percentile(vals, 0.25), percentile(vals, 0.75)
    iqr = q3 - q1
    out = {
        "n": n, "min": num(vals[0]), "p05": num(percentile(vals, 0.05)), "p25": num(q1),
        "median": num(percentile(vals, 0.5)), "p75": num(q3), "p95": num(percentile(vals, 0.95)),
        "max": num(vals[-1]), "mean": num(mean), "std": num(std),
        "zeros": sum(1 for v in vals if v == 0), "negatives": sum(1 for v in vals if v < 0),
    }
    if iqr > 0:
        for label, k in (("outliers_iqr_1_5", 1.5), ("outliers_iqr_3", 3.0)):
            lo, hi = q1 - k * iqr, q3 + k * iqr
            out[label] = {"below": sum(1 for v in vals if v < lo), "above": sum(1 for v in vals if v > hi)}
    else:
        out["outliers_iqr_1_5"] = None
        out["outliers_iqr_3"] = None
    return out, vals


def finalize(col, top_n):
    total = col.n - col.missing
    rep = {
        "name": col.name, "index": col.index, "type": None,
        "missing": col.missing, "missing_pct": pct(col.missing, col.n), "non_missing": total,
        "distinct": len(col.counts),
    }
    flags = []
    if col.capped:
        rep["distinct_is_lower_bound"] = True
    if col.tokens:
        rep["missing_tokens"] = dict(col.tokens.most_common())
    if total == 0:
        rep["type"] = "empty"
        rep["flags"] = ["all_missing"]
        return rep, None
    rep["distinct_pct"] = pct(len(col.counts), total)
    k = col.kinds
    numeric_n = k["int"] + k["float"]
    date_n = k["date"]
    ctype = "mixed"
    if col.flags.get("zero_padded") and (col.flags["zero_padded"] + k["int"]) / total >= TYPE_SHARE and not k["float"]:
        ctype = "string"          # digit codes with leading zeros: a label, not a quantity
        numeric_n = 0
    elif numeric_n / total >= TYPE_SHARE:
        ctype = "float" if k["float"] else "integer"
    elif k["bool"] / total >= TYPE_SHARE:
        ctype = "boolean"
    elif date_n / total >= TYPE_SHARE:
        ctype = "datetime" if col.has_time else "date"
    elif k["str"] / total >= TYPE_SHARE:
        ctype = "string"
    rep["type"] = ctype
    if ctype == "mixed":
        flags.append("mixed_types")
        rep["kind_counts"] = {a: b for a, b in k.items()}
    if ctype in ("integer", "float"):
        bad = total - numeric_n
        if bad:
            rep["non_numeric_values"] = {"count": bad, "examples": col.samples.get("str", []) + col.samples.get("bool", []) + col.samples.get("date", [])}
            flags.append("non_numeric_in_numeric")

    # numeric
    clean_vals = None
    if ctype in ("integer", "float") and col.nums is not None:
        clean_vals = [v for v in col.nums if v == v]
        summ, vals = numeric_summary(clean_vals)
        rep["numeric"] = summ
        suspects = []
        for sv in SENTINELS:
            c = sum(1 for v in vals if v == sv) if (vals[0] == sv or vals[-1] == sv) else 0
            if c >= 3 and c / len(vals) >= 0.005:
                suspects.append({"value": sv, "count": c})
        if suspects:
            rep["sentinel_suspects"] = sorted(suspects, key=lambda d: -d["count"])
            flags.append("sentinel_suspect")
        keys = set(col.counts)
        if ctype == "integer" and keys <= {"0", "1"} and len(keys) == 2:
            flags.append("binary_01")
        if ctype == "integer" and YEAR_NAME_RE.search(col.name) and summ["min"] >= 1800 and summ["max"] <= 2100:
            flags.append("possible_year")
        if col.flags.get("formatted"):
            flags.append("formatted_numbers")
        o = summ.get("outliers_iqr_3")
        if o and (o["below"] + o["above"]) > 0:
            flags.append("extreme_outliers")
    # string length
    if col.len_n:
        rep["string_length"] = {"min": col.len_min, "mean": num(col.len_sum / col.len_n), "max": col.len_max}
    # dates
    if col.fmts and ctype in ("date", "datetime"):
        ordered = sorted(col.fmts.items(), key=lambda kv: -kv[1]["n"])
        best_key, best = ordered[0]
        ambiguous = len(ordered) > 1 and ordered[1][1]["n"] >= TYPE_SHARE * date_n and best["n"] >= TYPE_SHARE * date_n
        if ambiguous:
            order_pref = [kv for kv in ordered if kv[0].startswith("mdy")]
            best_key, best = (order_pref or ordered)[0]
        def fmt(dt):
            return dt.isoformat(sep=" ") if col.has_time else dt.date().isoformat()

        info = {"format": best_key, "min": fmt(best["min"]), "max": fmt(best["max"]),
                "span_days": (best["max"] - best["min"]).days, "has_time": col.has_time}
        if best["n"] < 2:
            info["row_order"] = "single"
        elif best["asc"] == 0:
            info["row_order"] = "ascending"
        elif best["desc"] == 0:
            info["row_order"] = "descending"
        else:
            info["row_order"] = "unsorted"
        if ambiguous:
            alt = [kv for kv in ordered if kv[0].startswith("dmy")]
            info["date_order_ambiguous"] = True
            if alt:
                info["alt_range_if_day_first"] = [fmt(alt[0][1]["min"]), fmt(alt[0][1]["max"])]
            flags.append("date_order_ambiguous")
        rep["date"] = info
    # top values
    if ctype in ("string", "boolean", "mixed") or (clean_vals is not None and len(col.counts) <= 20):
        rep["top_values"] = [{"value": v[:80], "count": c, "pct": pct(c, total)} for v, c in col.counts.most_common(top_n)]
    # flags from counts
    if len(col.counts) == 1:
        flags.append("constant")
    elif col.counts and max(col.counts.values()) / total >= NEAR_CONSTANT and not col.capped:
        flags.append("near_constant")
    if col.padded:
        rep["whitespace_padded_values"] = col.padded
        flags.append("whitespace_padded")
    if col.flags.get("zero_padded"):
        flags.append("zero_padded_codes")
    if col.flags.get("long_digits"):
        flags.append("long_digit_strings")
    if ctype in ("string", "mixed", "boolean") and not col.capped:
        groups = {}
        for v in col.counts:
            groups.setdefault(re.sub(r"\s+", " ", v).lower(), []).append(v)
        multi = [g for g in groups.values() if len(g) > 1]
        if multi:
            rep["case_variant_groups"] = {"count": len(multi), "examples": [g[:3] for g in multi[:3]]}
            flags.append("case_variants")
    # id detection
    distinct = len(col.counts)
    ratio = distinct / total
    name_id = bool(ID_NAME_RE.search(col.name.strip()))
    unique = (not col.capped) and distinct == total and col.missing == 0 and total >= ID_UNIQUE_MIN_ROWS
    mean_len = (col.len_sum / col.len_n) if col.len_n else 0
    reasons = []
    conf = None
    if ctype in ("integer", "string") and unique:
        if ctype == "string" and mean_len > 40:
            flags.append("likely_free_text")
        else:
            reasons.append("all_values_unique")
            if ctype == "integer" and clean_vals is not None:
                lo_v, hi_v = min(clean_vals), max(clean_vals)
                if hi_v - lo_v == len(clean_vals) - 1:
                    reasons.append("sequential_integers")
            if name_id:
                reasons.append("name_looks_like_id")
                conf = "high"
            elif ctype == "string" or "sequential_integers" in reasons:
                conf = "medium"
            else:
                conf = "low"
    elif name_id and col.capped and ctype in ("integer", "string"):
        reasons = ["name_looks_like_id", "distinct_count_capped"]
        conf = "medium"
    elif name_id and ctype in ("integer", "string", "mixed"):
        if ratio >= 0.5:
            reasons = ["name_looks_like_id", "mostly_unique"]
            conf = "medium"
        else:
            flags.append("repeating_key")
            rep["id_note"] = "name looks like a key but values repeat: a join key, not a row id"
    if conf:
        rep["id_confidence"] = conf
        rep["id_reasons"] = reasons
        flags.append("likely_id" if conf in ("high", "medium") else "possible_id")
    if ctype == "string" and not unique and ratio >= 0.9 and total >= ID_UNIQUE_MIN_ROWS and "likely_free_text" not in flags:
        flags.append("high_cardinality_string")
    rep["flags"] = flags
    return rep, clean_vals


def pearson(xs, ys):
    sx = sy = sxx = syy = sxy = 0.0
    n = 0
    for x, y in zip(xs, ys):
        if x == x and y == y:
            n += 1
            sx += x
            sy += y
            sxx += x * x
            syy += y * y
            sxy += x * y
    if n < CORR_MIN_PAIRS:
        return None, n
    vx = sxx - sx * sx / n
    vy = syy - sy * sy / n
    if vx <= 1e-12 or vy <= 1e-12:
        return None, n
    r = (sxy - sx * sy / n) / math.sqrt(vx * vy)
    return max(-1.0, min(1.0, r)), n


def detect_encoding(path):
    import codecs
    dec = codecs.getincrementaldecoder("utf-8-sig")()
    with open(path, "rb") as fh:
        while True:
            chunk = fh.read(CHUNK)
            if not chunk:
                dec.decode(b"", final=True)
                break
            dec.decode(chunk)
    return "utf-8-sig"


def pick_delimiter(first_line):
    best, best_n = ",", 0
    for d in (",", ";", "\t", "|"):
        try:
            n = len(next(csv.reader([first_line], delimiter=d)))
        except (csv.Error, StopIteration):
            continue
        if n > best_n:
            best, best_n = d, n
    return best


def fail(msg):
    sys.stderr.write("eda_profile: " + msg + "\n")
    return 2


def clean_json(o):
    if isinstance(o, float):
        return o if math.isfinite(o) else None
    if isinstance(o, dict):
        return {str(k): clean_json(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [clean_json(v) for v in o]
    return o


def main(argv=None):
    ap = argparse.ArgumentParser(description="Profile a CSV file and print strict JSON.")
    ap.add_argument("path")
    ap.add_argument("--delimiter", help="single character; default is detected from the header line")
    ap.add_argument("--max-rows", type=int, default=DEFAULT_MAX_ROWS, help="profile at most this many good rows")
    ap.add_argument("--top", type=int, default=5, help="top values listed per column")
    ap.add_argument("--target", help="column name of an outcome to check for leakage")
    ap.add_argument("--no-corr", action="store_true", help="skip the correlation step")
    ap.add_argument("--strict", action="store_true", help="exit 1 when any row was bad")
    try:
        args = ap.parse_args(argv)
    except SystemExit as exc:
        return 2 if exc.code else 0
    if args.max_rows < 1 or args.top < 1:
        return fail("--max-rows and --top must be at least 1")
    path = args.path
    if not os.path.isfile(path):
        return fail("file not found: " + path)
    if os.path.getsize(path) == 0:
        return fail("file is empty: " + path)
    warnings = []
    try:
        detect_encoding(path)
        encoding = "utf-8-sig"
    except UnicodeDecodeError:
        encoding = "latin-1"
        warnings.append("file is not valid UTF-8; read as latin-1 (accented characters may be wrong)")
    except OSError as exc:
        return fail("cannot read file: " + str(exc))
    csv.field_size_limit(1 << 24)
    nul = [0]

    def lines(fh):
        for line in fh:
            if "\0" in line:
                nul[0] += 1
                line = line.replace("\0", "")
            yield line

    try:
        fh = open(path, "r", encoding=encoding, newline="")
    except OSError as exc:
        return fail("cannot open file: " + str(exc))
    with fh:
        first = ""
        for raw_line in fh:
            if raw_line.strip():
                first = raw_line
                break
        if not first:
            return fail("file has no header row")
        delim = args.delimiter or pick_delimiter(first.replace("\0", ""))
        if len(delim) != 1:
            return fail("--delimiter must be one character")
        fh.seek(0)
        reader = csv.reader(lines(fh), delimiter=delim)
        header = None
        while header is None:
            try:
                row = next(reader)
            except StopIteration:
                return fail("file has no header row")
            except csv.Error as exc:
                return fail("header could not be parsed: " + str(exc))
            if any(c.strip() for c in row):
                header = row
        names, seen = [], Counter()
        if encoding == "latin-1" and header and header[0].startswith("ï»¿"):
            header[0] = header[0][3:]      # a UTF-8 byte-order mark read as latin-1
        for i, h in enumerate(header):
            h = h.strip()
            if not h:
                h = "col_%d" % (i + 1)
                warnings.append("empty header in position %d renamed %s" % (i + 1, h))
            seen[h] += 1
            if seen[h] > 1:
                new = "%s__%d" % (h, seen[h])
                warnings.append("duplicate header %r renamed %s" % (h, new))
                h = new
            names.append(h)
        ncols = len(names)
        if all(classify(h.strip())[0] in ("int", "float") for h in header if h.strip()) and len(header) > 0:
            warnings.append("every header cell is numeric: the file may have no header row")
        tcol = None
        if args.target is not None:
            if args.target not in names:
                return fail("--target %r is not a column; columns: %s" % (args.target, ", ".join(names[:30])))
            tcol = names.index(args.target)
        cols = [Col(nm, i) for i, nm in enumerate(names)]
        rows = 0
        read_rows = 0
        blank = 0
        dups = 0
        seen_rows = set()
        bad = []
        bad_count = 0
        bad_shapes = Counter()
        span_warned = False
        truncated = False
        while True:
            if rows >= args.max_rows:
                try:
                    row = next(reader)
                    truncated = True
                except (StopIteration, csv.Error):
                    pass
                break
            start_line = reader.line_num
            try:
                row = next(reader)
            except StopIteration:
                break
            except csv.Error as exc:
                bad_count += 1
                read_rows += 1
                if len(bad) < 5:
                    bad.append({"line": reader.line_num, "problem": "csv error: " + str(exc)[:80]})
                continue
            if reader.line_num - start_line > MAX_ROW_SPAN_LINES and not span_warned:
                span_warned = True
                warnings.append("one record starting at line %d spans %d lines: check for an unbalanced quote"
                                % (start_line + 1, reader.line_num - start_line))
            if not row or not any(c.strip() for c in row):
                blank += 1
                continue
            read_rows += 1
            if len(row) != ncols:
                bad_count += 1
                bad_shapes[len(row)] += 1
                if len(bad) < 5:
                    bad.append({"line": reader.line_num, "fields": len(row), "expected": ncols})
                continue
            h = hash(tuple(row))
            if h in seen_rows:
                dups += 1
            else:
                seen_rows.add(h)
            tval = None
            if tcol is not None:
                tv = row[tcol].strip()
                if tv.lower() not in NULL_TOKENS:
                    tval = tv
            for i, c in enumerate(cols):
                c.add(row[i], None if i == tcol else tval)
            rows += 1
    if nul[0]:
        warnings.append("%d line(s) contained NUL characters; they were removed" % nul[0])
    if rows == 0:
        return fail("no usable data rows (bad rows: %d)" % bad_count)
    if truncated:
        warnings.append("stopped after --max-rows %d good rows; statistics describe that slice only" % args.max_rows)
    if bad_count:
        warnings.append("%d bad row(s) excluded from all statistics (%.2f%% of rows read)" % (bad_count, 100.0 * bad_count / max(read_rows, 1)))

    col_reports, numeric_cols = [], {}
    for c in cols:
        rep, vals = finalize(c, args.top)
        col_reports.append(rep)
        if vals is not None and len(vals) > 1:
            numeric_cols[c.name] = c
    by_name = {r["name"]: r for r in col_reports}

    report = {
        "tool": "eda_profile", "version": VERSION, "file": os.path.basename(path), "encoding": encoding,
        "delimiter": delim, "rows_profiled": rows, "rows_truncated": truncated, "columns": ncols,
        "blank_lines_skipped": blank, "duplicate_rows": dups,
        "bad_rows": {"count": bad_count, "pct_of_rows_read": pct(bad_count, read_rows),
                     "field_counts_seen": {str(k): v for k, v in bad_shapes.most_common(5)}, "first_examples": bad,
                     "policy": "excluded from every statistic"},
        "warnings": warnings,
    }
    flag_lists = {"constant": "constant_columns", "near_constant": "near_constant_columns",
                  "all_missing": "all_missing_columns", "likely_id": "likely_id_columns",
                  "repeating_key": "repeating_key_columns", "mixed_types": "mixed_type_columns",
                  "sentinel_suspect": "sentinel_suspect_columns", "case_variants": "case_variant_columns"}
    for flag, key in flag_lists.items():
        report[key] = [r["name"] for r in col_reports if flag in r.get("flags", [])]
    report["date_columns"] = [{"name": r["name"], "min": r["date"]["min"], "max": r["date"]["max"],
                               "row_order": r["date"]["row_order"]} for r in col_reports if "date" in r]
    report["missing_over_20_pct"] = [{"name": r["name"], "missing_pct": r["missing_pct"]} for r in col_reports
                                     if r["missing_pct"] is not None and r["missing_pct"] >= 20 and r["type"] != "empty"]

    # correlation and target checks
    corr_pairs, target_info, leaks = [], None, []
    usable = [nm for nm in numeric_cols if "likely_id" not in by_name[nm].get("flags", []) and "constant" not in by_name[nm].get("flags", [])]
    if tcol is not None and names[tcol] in numeric_cols and names[tcol] not in usable:
        usable.append(names[tcol])
    sample_idx = None
    sampled = {}
    if (not args.no_corr) and len(usable) >= 2:
        if len(usable) > CORR_MAX_COLS:
            warnings.append("correlation limited to the first %d numeric columns of %d" % (CORR_MAX_COLS, len(usable)))
            keep = usable[:CORR_MAX_COLS]
            if tcol is not None and names[tcol] in usable and names[tcol] not in keep:
                keep.append(names[tcol])
            usable = keep
        step = max(1, rows // CORR_SAMPLE_ROWS)
        sample_idx = range(0, rows, step)
        for nm in usable:
            arr = numeric_cols[nm].nums
            sampled[nm] = [arr[i] for i in sample_idx]
        for ai in range(len(usable)):
            for bi in range(ai + 1, len(usable)):
                a, b = usable[ai], usable[bi]
                r, n = pearson(sampled[a], sampled[b])
                if r is not None and abs(r) >= NEAR_DUP_R:
                    corr_pairs.append({"a": a, "b": b, "r": round(r, 4), "pairs": n})
        corr_pairs.sort(key=lambda d: -abs(d["r"]))
        report["correlation_note"] = "Pearson on %d evenly spaced rows; linear association only" % len(sample_idx)
    report["near_duplicate_numeric_pairs"] = corr_pairs[:20]

    if tcol is not None:
        tname = names[tcol]
        trep = by_name[tname]
        target_info = {"column": tname, "type": trep["type"], "missing_pct": trep["missing_pct"], "distinct": trep["distinct"]}
        tcounts = cols[tcol].counts
        ttotal = sum(tcounts.values())
        categorical = trep["type"] in ("string", "boolean", "mixed") or trep["distinct"] <= TARGET_CLASS_MAX
        if categorical and ttotal:
            target_info["classes"] = [{"value": v[:60], "count": c, "pct": pct(c, ttotal)} for v, c in tcounts.most_common(10)]
            target_info["majority_share"] = round(tcounts.most_common(1)[0][1] / ttotal, 4)
        if tname in numeric_cols and sampled and tname in sampled:
            tc = []
            for nm in usable:
                if nm == tname:
                    continue
                r, n = pearson(sampled[nm], sampled[tname])
                if r is not None:
                    tc.append({"column": nm, "r": round(r, 4), "pairs": n})
                    if abs(r) >= LEAK_R:
                        leaks.append({"column": nm, "check": "numeric_correlation", "value": round(r, 4),
                                      "note": "|r| with the target at or above %.2f: leakage or a restatement of the target" % LEAK_R})
            tc.sort(key=lambda d: -abs(d["r"]))
            target_info["top_numeric_correlations"] = tc[:10]
        if categorical and ttotal:
            majority = tcounts.most_common(1)[0][1] / ttotal
            for c in cols:
                if c.index == tcol or c.pairs is None or not c.pairs:
                    continue
                flags = by_name[c.name].get("flags", [])
                if "likely_id" in flags or "constant" in flags or "all_missing" in flags:
                    continue
                total_pairs = sum(c.pairs.values())
                nvals = len({v for v, _ in c.pairs})
                if total_pairs < 30 or nvals < 2 or nvals > 0.5 * total_pairs:
                    continue
                best = {}
                for (v, t), cnt in c.pairs.items():
                    best[v] = max(best.get(v, 0), cnt)
                purity = sum(best.values()) / total_pairs
                if purity >= LEAK_PURITY and purity - majority >= LEAK_PURITY_LIFT:
                    leaks.append({"column": c.name, "check": "category_purity", "value": round(purity, 4),
                                  "note": "each value (a missing cell counts as a value) almost always maps to one target class: leakage or a proxy of the target"})
        target_info["leakage_candidates"] = leaks
    report["target"] = target_info
    report["columns_detail"] = col_reports
    report["type_counts"] = dict(Counter(r["type"] for r in col_reports))
    report["not_computed"] = ["causal claims", "significance tests", "multivariate structure", "text meaning"]

    out = json.dumps(clean_json(report), indent=2, allow_nan=False, ensure_ascii=True)
    sys.stdout.buffer.write((out + "\n").encode("ascii"))
    return 1 if (args.strict and bad_count) else 0


if __name__ == "__main__":
    sys.exit(main())
