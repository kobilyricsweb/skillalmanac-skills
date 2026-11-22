#!/usr/bin/env python3
"""Semantic diff of two versions of the same CSV table, matched by key column(s).

Usage:
    python csv_version_diff.py OLD.csv NEW.csv --key ID [--key ID2 ...] [options]
    python csv_version_diff.py OLD.csv NEW.csv --suggest-keys

Reads: the two CSV files, completely, into memory (fine up to a few hundred MB).
Writes: strict JSON to stdout. With --out FILE and/or --markdown FILE it also
writes those files; it never overwrites an existing file without --force and
NEVER writes to a path that is the same file as OLD or NEW, even with --force.

Options that change what counts as a difference (all off by default):
    --abs-tol X      numeric cells whose absolute difference is <= X are equal
    --rel-tol X      numeric cells whose difference is <= X * max(|old|,|new|) are equal
    --trim           collapse and strip whitespace in non-key cells before comparing
    --ignore-case    case-fold non-key cells before comparing
    --null-tokens A,B  extra spellings of "missing" (blank is always missing)

Exit codes: 0 identical or equivalent, 1 differences found, 2 usage or input error.
Standard library only; no network; no subprocess.
"""
import argparse
import csv
import io
import json
import os
import re
import sys

VERSION = "0.1.0"

# Delimiters tried when sniffing the header line. Order is the tie-break.
CANDIDATE_DELIMS = [",", ";", "\t", "|"]
# A removed and an added column are proposed as a rename when this share of
# matched rows hold the same value (the review standard asked for 90 percent).
RENAME_MATCH_SHARE = 0.90
# Fewer compared rows than this is too little evidence for a rename proposal.
RENAME_MIN_ROWS = 3
# Cap on removed x added column pairs examined for renames (cost guard).
RENAME_MAX_PAIRS = 400
# Row-count change, in percent of the old count, that is reported as a warning.
ROW_SHIFT_PCT = 20.0
# Absolute change in a column's null rate (0..1) that is reported as a warning.
NULL_JUMP = 0.20
DEFAULT_EXAMPLES = 5
MAX_VALUE_CHARS = 200

INT_RE = re.compile(r"^[+-]?\d+$")
FLOAT_RE = re.compile(r"^[+-]?(\d+\.\d*|\.\d+|\d+)([eE][+-]?\d+)?$")
# A leading zero (007, 0123, 00.5) marks an identifier or code, not a number.
LEADING_ZERO_RE = re.compile(r"^[+-]?0\d")
DATE_RE = re.compile(
    r"^(\d{4}[-/.]\d{1,2}[-/.]\d{1,2}|\d{1,2}[-/.]\d{1,2}[-/.]\d{2,4})"
    r"([T ]\d{1,2}:\d{2}(:\d{2}(\.\d+)?)?(Z|[+-]\d{2}:?\d{2})?)?$"
)


class CsvDiffError(Exception):
    """A problem the user must fix; reported as ERROR and exit code 2."""


# ---------------------------------------------------------------- reading


def decode(raw):
    """Return (text, encoding, has_bom, used_fallback)."""
    if raw.startswith(b"\xef\xbb\xbf"):
        try:
            return raw[3:].decode("utf-8"), "utf-8", True, False
        except UnicodeDecodeError:
            pass
    if raw.startswith(b"\xff\xfe") or raw.startswith(b"\xfe\xff"):
        try:
            return raw.decode("utf-16"), "utf-16", True, False
        except UnicodeDecodeError:
            pass
    try:
        return raw.decode("utf-8"), "utf-8", False, False
    except UnicodeDecodeError:
        pass
    try:
        return raw.decode("cp1252"), "cp1252", False, True
    except UnicodeDecodeError:
        return raw.decode("latin-1"), "latin-1", False, True


def sniff_delimiter(text):
    first = text.split("\n", 1)[0].rstrip("\r")
    best, best_n = ",", 1
    for d in CANDIDATE_DELIMS:
        try:
            n = len(next(csv.reader([first], delimiter=d)))
        except (csv.Error, StopIteration):
            continue
        if n > best_n:
            best, best_n = d, n
    return best


def read_table(path, forced_delim):
    try:
        with open(path, "rb") as fh:
            raw = fh.read()
    except OSError as exc:
        raise CsvDiffError("cannot read %s: %s" % (path, exc.strerror or exc))
    if not raw.strip():
        raise CsvDiffError("%s is empty; a CSV needs at least a header row" % path)
    text, enc, bom, fallback = decode(raw)
    delim = forced_delim or sniff_delimiter(text)
    try:
        csv.field_size_limit(2 ** 31 - 1)
    except (OverflowError, ValueError):
        pass
    reader = csv.reader(io.StringIO(text, newline=""), delimiter=delim)
    header = None
    rows = []
    ragged = []
    try:
        for rec in reader:
            if not rec:
                continue
            if header is None:
                header = rec
                ncols = len(header)
                continue
            if len(rec) != ncols:
                ragged.append(reader.line_num)
                rec = (rec + [""] * ncols)[:ncols]
            rows.append((reader.line_num, rec))
    except csv.Error as exc:
        raise CsvDiffError("%s is not valid CSV near line %d: %s" % (path, reader.line_num, exc))
    if header is None:
        raise CsvDiffError("%s has no header row" % path)
    cleaned, stripped, dup_headers = [], [], []
    seen = {}
    for h in header:
        c = h.replace("\ufeff", "").strip()
        if c != h:
            stripped.append(h)
        if c in seen:
            seen[c] += 1
            dup_headers.append(c)
            c = "%s#%d" % (c, seen[c])
        else:
            seen[c] = 1
        cleaned.append(c)
    return {
        "path": path, "encoding": enc, "bom": bom, "fallback": fallback,
        "delimiter": delim, "header": cleaned, "rows": rows, "ragged": ragged,
        "stripped_headers": stripped, "dup_headers": dup_headers,
    }


# ---------------------------------------------------------------- typing


def is_null(v, tokens):
    s = v.strip()
    return s == "" or s in tokens


def num(s):
    """Parse a plain decimal number; identifiers with a leading zero are not numbers."""
    s = s.strip()
    if not s or LEADING_ZERO_RE.match(s):
        return None
    if INT_RE.match(s):
        return int(s)
    if FLOAT_RE.match(s):
        try:
            f = float(s)
        except ValueError:
            return None
        if f == f and f not in (float("inf"), float("-inf")):
            return f
    return None


def classify(v, tokens):
    if is_null(v, tokens):
        return "null"
    s = v.strip()
    n = num(s)
    if isinstance(n, int):
        return "int"
    if n is not None:
        return "float"
    if DATE_RE.match(s):
        return "date"
    return "text"


def column_profiles(table, tokens):
    n = len(table["header"])
    counts = [dict(int=0, float=0, date=0, text=0, null=0) for _ in range(n)]
    for _, row in table["rows"]:
        for i in range(n):
            counts[i][classify(row[i], tokens)] += 1
    total = len(table["rows"])
    out = {}
    for i, name in enumerate(table["header"]):
        c = counts[i]
        kinds = {k for k in ("int", "float", "date", "text") if c[k]}
        if not kinds:
            t = "empty"
        elif kinds <= {"int"}:
            t = "int"
        elif kinds <= {"int", "float"}:
            t = "float"
        elif kinds == {"date"}:
            t = "date"
        else:
            t = "text"
        out[name] = {
            "type": t,
            "type_counts": {k: v for k, v in c.items() if v and k != "null"},
            "null_rate": round(c["null"] / total, 4) if total else 0.0,
        }
    return out


def fits(old_type, kind):
    if old_type in ("text", "empty") or kind == "null":
        return True
    if old_type == "int":
        return kind == "int"
    if old_type == "float":
        return kind in ("int", "float")
    return kind == old_type


# ---------------------------------------------------------------- comparison


def compare(a, b, opt):
    """Return (status, info) with status same, normalised, format_only, within_tolerance or changed."""
    if a == b:
        return "same", {}
    if is_null(a, opt.null_set) and is_null(b, opt.null_set):
        return "same", {}
    a2, b2 = a, b
    if opt.trim:
        a2, b2 = " ".join(a.split()), " ".join(b.split())
    if opt.ignore_case:
        a2, b2 = a2.casefold(), b2.casefold()
    if (opt.trim or opt.ignore_case) and a2 == b2:
        return "normalised", {}
    x, y = num(a), num(b)
    if x is not None and y is not None:
        if x == y:
            return "format_only", {}
        d = abs(x - y)
        if d <= opt.abs_tol or d <= opt.rel_tol * max(abs(x), abs(y)):
            return "within_tolerance", {}
        delta = y - x
        if isinstance(delta, float):
            delta = round(delta, 10)
        return "changed", {"delta": delta}
    info = {}
    if " ".join(a.split()) == " ".join(b.split()):
        info["note"] = "differs only by whitespace"
    elif " ".join(a.split()).casefold() == " ".join(b.split()).casefold():
        info["note"] = "differs only by case or whitespace"
    return "changed", info


def clip(v):
    return v if len(v) <= MAX_VALUE_CHARS else v[:MAX_VALUE_CHARS] + "..."


def build_index(table, keys, trim):
    pos = {c: i for i, c in enumerate(table["header"])}
    kidx = [pos[k] for k in keys]
    index, dups, blanks = {}, {}, []
    for n, (line, row) in enumerate(table["rows"]):
        kv = tuple(row[i].strip() if trim else row[i] for i in kidx)
        if any(v.strip() == "" for v in kv):
            blanks.append(line)
            continue
        if kv in index or kv in dups:
            dups[kv] = dups.get(kv, 1) + 1
            continue
        index[kv] = (n, row)
    for k in dups:
        index.pop(k, None)
    return index, dups, blanks


def norm_key(k):
    return tuple(re.sub(r"^0+(?=\d)", "", s.strip().casefold()) for s in k)


def key_dict(keys, k):
    return {keys[i]: clip(k[i]) for i in range(len(keys))}


def key_text(k):
    return "|".join(k)


# ---------------------------------------------------------------- main diff


def diff(old, new, keys, opt):
    warnings = []
    tokens = opt.null_set

    for label, t in (("old", old), ("new", new)):
        if t["bom"]:
            warnings.append({"code": "bom_present", "file": label,
                             "detail": "file starts with a byte-order mark; it was removed from the first header"})
        if t["fallback"]:
            warnings.append({"code": "encoding_fallback", "file": label,
                             "detail": "not valid UTF-8; decoded as %s, check accented text" % t["encoding"]})
        if t["ragged"]:
            warnings.append({"code": "ragged_rows", "file": label, "count": len(t["ragged"]),
                             "lines": t["ragged"][:10],
                             "detail": "rows with a different field count than the header were padded or cut"})
        if t["stripped_headers"]:
            warnings.append({"code": "header_whitespace_trimmed", "file": label,
                             "detail": "header names had surrounding whitespace or a BOM character"})
        if t["dup_headers"]:
            warnings.append({"code": "duplicate_header", "file": label, "columns": t["dup_headers"],
                             "detail": "repeated column names were renamed name#2, name#3"})
    if old["encoding"] != new["encoding"]:
        warnings.append({"code": "encoding_differs", "old": old["encoding"], "new": new["encoding"],
                         "detail": "the two files use different encodings"})
    if old["delimiter"] != new["delimiter"]:
        warnings.append({"code": "delimiter_differs", "old": old["delimiter"], "new": new["delimiter"],
                         "detail": "the two files use different delimiters; each was read with its own"})

    for k in keys:
        for label, t in (("old", old), ("new", new)):
            if k not in t["header"]:
                raise CsvDiffError("key column %r is not in the %s file; columns are: %s"
                                   % (k, label, ", ".join(t["header"])))

    old_idx, old_dups, old_blank = build_index(old, keys, opt.trim)
    new_idx, new_dups, new_blank = build_index(new, keys, opt.trim)
    for label, dups, blanks in (("old", old_dups, old_blank), ("new", new_dups, new_blank)):
        if dups:
            warnings.append({"code": "duplicate_keys_" + label, "count": len(dups),
                             "examples": [key_text(k) for k in list(dups)[:5]],
                             "detail": "rows with these keys appear more than once and are excluded from the diff in both files"})
        if blanks:
            warnings.append({"code": "blank_keys_" + label, "count": len(blanks), "lines": blanks[:10],
                             "detail": "rows with an empty key cannot be matched and are excluded"})
    ambiguous = set(old_dups) | set(new_dups)
    for k in ambiguous:
        old_idx.pop(k, None)
        new_idx.pop(k, None)

    old_total, new_total = len(old["rows"]), len(new["rows"])
    if old_total:
        pct = (new_total - old_total) * 100.0 / old_total
        if abs(pct) > opt.row_shift_pct:
            warnings.append({"code": "row_count_shift", "old_rows": old_total, "new_rows": new_total,
                             "percent": round(pct, 1),
                             "detail": "row count moved by more than %g percent; check for a truncated or filtered export" % opt.row_shift_pct})
    elif new_total:
        warnings.append({"code": "row_count_shift", "old_rows": 0, "new_rows": new_total, "percent": None,
                         "detail": "the old file has no data rows"})

    for label, idx in (("old", old_idx), ("new", new_idx)):
        groups = {}
        for k in idx:
            groups.setdefault(norm_key(k), []).append(k)
        near = [v for v in groups.values() if len(v) > 1]
        if near:
            warnings.append({"code": "near_duplicate_keys", "file": label, "count": len(near),
                             "examples": [[key_text(k) for k in g] for g in near[:5]],
                             "detail": "keys that differ only by case, spaces or leading zeros; they were treated as different keys"})

    old_prof = column_profiles(old, tokens)
    new_prof = column_profiles(new, tokens)
    old_cols, new_cols = old["header"], new["header"]
    new_set, old_set = set(new_cols), set(old_cols)
    common = [c for c in old_cols if c in new_set]
    removed_cols = [c for c in old_cols if c not in new_set]
    added_cols = [c for c in new_cols if c not in old_set]
    opos = {c: i for i, c in enumerate(old_cols)}
    npos = {c: i for i, c in enumerate(new_cols)}
    cmp_cols = [c for c in common if c not in keys]

    schema = []
    for c in removed_cols:
        schema.append({"class": "column_removed", "column": c, "old_type": old_prof[c]["type"]})
    for c in added_cols:
        schema.append({"class": "column_added", "column": c, "new_type": new_prof[c]["type"]})
    if [c for c in old_cols if c in new_set] != [c for c in new_cols if c in old_set]:
        schema.append({"class": "column_order_changed",
                       "detail": "the shared columns appear in a different order"})
    for c in common:
        ot, nt = old_prof[c]["type"], new_prof[c]["type"]
        if ot != nt and "empty" not in (ot, nt):
            if ot == "int" and nt == "float":
                direction = "widened"
            elif nt == "text":
                direction = "to_text"
            elif ot == "text":
                direction = "from_text"
            else:
                direction = "other"
            bad = []
            for line, row in new["rows"]:
                v = row[npos[c]]
                kind = classify(v, tokens)
                if not fits(ot, kind):
                    bad.append({"line": line, "value": clip(v)})
                    if len(bad) >= opt.examples:
                        break
            schema.append({"class": "type_changed", "column": c, "from": ot, "to": nt,
                           "direction": direction, "new_values_not_fitting_old_type": bad})

    # rows: matched by key
    counts = {c: {"changed_cells": 0, "format_only_cells": 0, "within_tolerance_cells": 0,
                  "normalised_cells": 0, "null_to_value": 0, "value_to_null": 0,
                  "whitespace_or_case_only": 0, "numeric_changes": 0} for c in cmp_cols}
    max_delta = {}
    examples, per_col_examples = [], {c: 0 for c in cmp_cols}
    removed_keys, common_seq = [], []
    changed_rows = unchanged = cell_changes = 0
    for k, (n, orow) in old_idx.items():
        if k not in new_idx:
            removed_keys.append(k)
            continue
        nn, nrow = new_idx[k]
        common_seq.append(nn)
        row_changed = False
        for c in cmp_cols:
            a, b = orow[opos[c]], nrow[npos[c]]
            status, info = compare(a, b, opt)
            cc = counts[c]
            if status == "same":
                continue
            if status == "normalised":
                cc["normalised_cells"] += 1
            elif status == "format_only":
                cc["format_only_cells"] += 1
            elif status == "within_tolerance":
                cc["within_tolerance_cells"] += 1
            else:
                cc["changed_cells"] += 1
                cell_changes += 1
                row_changed = True
                na, nb = is_null(a, tokens), is_null(b, tokens)
                if na and not nb:
                    cc["null_to_value"] += 1
                elif nb and not na:
                    cc["value_to_null"] += 1
                if "note" in info:
                    cc["whitespace_or_case_only"] += 1
                if "delta" in info:
                    cc["numeric_changes"] += 1
                    max_delta[c] = max(max_delta.get(c, 0), abs(info["delta"]))
                if per_col_examples[c] < opt.examples:
                    per_col_examples[c] += 1
                    ex = {"kind": "changed_cell", "key": key_dict(keys, k), "column": c,
                          "old": clip(a), "new": clip(b)}
                    ex.update(info)
                    examples.append(ex)
        if row_changed:
            changed_rows += 1
        else:
            unchanged += 1
    added_keys = [k for k in new_idx if k not in old_idx]
    order_changed = any(common_seq[i] > common_seq[i + 1] for i in range(len(common_seq) - 1))
    for c, v in max_delta.items():
        counts[c]["max_abs_delta"] = round(v, 10) if isinstance(v, float) else v
    for k in removed_keys[:opt.examples]:
        examples.append({"kind": "removed_row", "key": key_dict(keys, k)})
    for k in added_keys[:opt.examples]:
        examples.append({"kind": "added_row", "key": key_dict(keys, k)})

    if removed_keys and added_keys:
        rmap = {}
        for k in removed_keys:
            rmap.setdefault(norm_key(k), []).append(k)
        drift = [(rmap[norm_key(k)][0], k) for k in added_keys
                 if norm_key(k) in rmap and k not in rmap[norm_key(k)]]
        if drift:
            warnings.append({"code": "key_format_drift", "count": len(drift),
                             "examples": [[key_text(a), key_text(b)] for a, b in drift[:5]],
                             "detail": "removed and added keys that match after trimming, case-folding and dropping leading zeros; probably the same rows with a reformatted key"})

    # null-rate jumps and rename candidates
    for c in common:
        d = new_prof[c]["null_rate"] - old_prof[c]["null_rate"]
        if abs(d) >= opt.null_jump:
            warnings.append({"code": "null_rate_jump", "column": c, "old": old_prof[c]["null_rate"],
                             "new": new_prof[c]["null_rate"],
                             "detail": "share of missing values moved by %.0f points" % (abs(d) * 100)})
    renames = []
    if removed_cols and added_cols:
        if len(removed_cols) * len(added_cols) > RENAME_MAX_PAIRS:
            warnings.append({"code": "rename_search_skipped",
                             "detail": "too many removed x added column pairs to compare"})
        else:
            for rc in removed_cols:
                for ac in added_cols:
                    denom = match = 0
                    for k, (n, orow) in old_idx.items():
                        if k not in new_idx:
                            continue
                        a = orow[opos[rc]]
                        if is_null(a, tokens):
                            continue
                        denom += 1
                        if a.strip() == new_idx[k][1][npos[ac]].strip():
                            match += 1
                    if denom >= RENAME_MIN_ROWS and match / denom >= RENAME_MATCH_SHARE:
                        renames.append({
                            "class": "renamed_candidate", "from": rc, "to": ac,
                            "match_share": round(match / denom, 4), "rows_compared": denom,
                            "name_differs_only_by_case": rc.casefold() == ac.casefold(),
                            "question": "Is %r now called %r? Same value in %d of %d matched rows. Not applied; confirm before treating it as a rename." % (rc, ac, match, denom)})
            renames.sort(key=lambda r: -r["match_share"])
            schema.extend(renames)
            for s in schema:
                if s["class"] == "column_removed":
                    s["possible_rename_to"] = [r["to"] for r in renames if r["from"] == s["column"]]
                elif s["class"] == "column_added":
                    s["possible_rename_from"] = [r["from"] for r in renames if r["to"] == s["column"]]

    real_schema = [s for s in schema if s["class"] in ("column_added", "column_removed", "type_changed")]
    equivalent_cells = sum(v["format_only_cells"] + v["within_tolerance_cells"] + v["normalised_cells"]
                           for v in counts.values())
    order_only = (order_changed or any(s["class"] == "column_order_changed" for s in schema))
    if real_schema or added_keys or removed_keys or changed_rows:
        verdict = "differences"
    elif order_only:
        verdict = "order_only"
    elif equivalent_cells:
        verdict = "equivalent"
    else:
        verdict = "identical"

    summary = []
    for c in old_cols + added_cols:
        if c in old_set and c in new_set:
            status = "common"
        elif c in old_set:
            status = "removed"
        else:
            status = "added"
        row = {"column": c, "status": status, "is_key": c in keys,
               "old_type": old_prof.get(c, {}).get("type"), "new_type": new_prof.get(c, {}).get("type"),
               "old_null_rate": old_prof.get(c, {}).get("null_rate"),
               "new_null_rate": new_prof.get(c, {}).get("null_rate")}
        if c in counts:
            row["changed_cells"] = counts[c]["changed_cells"]
        summary.append(row)

    old_excluded = old_total - len(old_idx)
    new_excluded = new_total - len(new_idx)
    return {
        "tool": "csv_version_diff", "version": VERSION, "verdict": verdict,
        "complete": old_excluded == 0 and new_excluded == 0,
        "inputs": {
            "old": {"path": old["path"], "encoding": old["encoding"], "bom": old["bom"],
                    "delimiter": old["delimiter"], "rows": old_total, "columns": old_cols},
            "new": {"path": new["path"], "encoding": new["encoding"], "bom": new["bom"],
                    "delimiter": new["delimiter"], "rows": new_total, "columns": new_cols},
        },
        "key": keys,
        "options": {"abs_tol": opt.abs_tol, "rel_tol": opt.rel_tol, "trim": opt.trim,
                    "ignore_case": opt.ignore_case, "null_tokens": sorted(tokens)},
        "schema_changes": schema,
        "rows": {"old_total": old_total, "new_total": new_total,
                 "excluded_old": old_excluded, "excluded_new": new_excluded,
                 "common": len(common_seq), "added": len(added_keys), "removed": len(removed_keys),
                 "changed": changed_rows, "unchanged": unchanged, "cell_changes": cell_changes,
                 "order_changed": order_changed},
        "column_change_counts": counts,
        "column_summary": summary,
        "examples": examples,
        "warnings": warnings,
    }


# ---------------------------------------------------------------- output


def md_esc(v):
    return str(v).replace("|", "\\|").replace("\n", " ")


def to_markdown(rep):
    r = rep["rows"]
    out = ["# CSV version diff", "",
           "- Old: `%s` (%d rows)" % (rep["inputs"]["old"]["path"], r["old_total"]),
           "- New: `%s` (%d rows)" % (rep["inputs"]["new"]["path"], r["new_total"]),
           "- Key: %s" % ", ".join("`%s`" % k for k in rep["key"]),
           "- Verdict: **%s**%s" % (rep["verdict"], "" if rep["complete"] else " (incomplete: some rows were excluded, see warnings)"),
           "", "## Rows", "",
           "| Added | Removed | Changed | Unchanged | Order changed |", "|---|---|---|---|---|",
           "| %d | %d | %d | %d | %s |" % (r["added"], r["removed"], r["changed"], r["unchanged"],
                                           "yes" if r["order_changed"] else "no"), ""]
    out += ["## Schema changes", ""]
    if not rep["schema_changes"]:
        out += ["None.", ""]
    for s in rep["schema_changes"]:
        if s["class"] == "renamed_candidate":
            out.append("- rename question: %s" % md_esc(s["question"]))
        elif s["class"] == "type_changed":
            out.append("- type changed: `%s` %s to %s (%s)" % (s["column"], s["from"], s["to"], s["direction"]))
        elif s["class"] == "column_order_changed":
            out.append("- column order changed")
        else:
            out.append("- %s: `%s`" % (s["class"].replace("_", " "), s["column"]))
    out += ["", "## Changes by column", "",
            "| Column | Changed cells | Format only | Within tolerance | Normalised | Null to value | Value to null |",
            "|---|---|---|---|---|---|---|"]
    for c, v in rep["column_change_counts"].items():
        out.append("| %s | %d | %d | %d | %d | %d | %d |" % (
            md_esc(c), v["changed_cells"], v["format_only_cells"], v["within_tolerance_cells"],
            v["normalised_cells"], v["null_to_value"], v["value_to_null"]))
    out += ["", "## Examples", ""]
    for e in rep["examples"]:
        k = ", ".join("%s=%s" % (a, b) for a, b in e["key"].items())
        if e["kind"] == "changed_cell":
            out.append("- %s: `%s` %s to %s" % (md_esc(k), e["column"], md_esc(repr(e["old"])), md_esc(repr(e["new"]))))
        else:
            out.append("- %s: %s" % (e["kind"].replace("_", " "), md_esc(k)))
    out += ["", "## Warnings", ""]
    if not rep["warnings"]:
        out.append("None.")
    for w in rep["warnings"]:
        out.append("- `%s`: %s" % (w["code"], md_esc(w.get("detail", ""))))
    return "\n".join(out) + "\n"


def same_path(a, b):
    na, nb = os.path.normcase(os.path.realpath(a)), os.path.normcase(os.path.realpath(b))
    if na == nb:
        return True
    try:
        return os.path.exists(a) and os.path.exists(b) and os.path.samefile(a, b)
    except OSError:
        return False


def check_outputs(paths, inputs, force):
    seen = []
    for p in paths:
        for i in inputs:
            if same_path(p, i):
                raise CsvDiffError("refusing to write %s: it is the same file as an input (%s)" % (p, i))
        for s in seen:
            if same_path(p, s):
                raise CsvDiffError("--out and --markdown point at the same file")
        seen.append(p)
        if os.path.exists(p) and not force:
            raise CsvDiffError("%s already exists; pass --force to replace it" % p)
        parent = os.path.dirname(os.path.abspath(p))
        if not os.path.isdir(parent):
            raise CsvDiffError("directory does not exist: %s" % parent)


def suggest_keys(old, new):
    cands = []
    for c in old["header"]:
        if c not in new["header"]:
            continue
        ok = True
        for t in (old, new):
            i = t["header"].index(c)
            vals = [r[i] for _, r in t["rows"]]
            if not vals or any(v.strip() == "" for v in vals) or len(set(vals)) != len(vals):
                ok = False
        if ok:
            cands.append(c)
    return {"command": "suggest-keys", "candidates": cands,
            "note": "columns that are filled and unique in both files; unique does not prove it identifies the same real-world row across versions, confirm with the user"}


def build_parser():
    p = argparse.ArgumentParser(description="Diff two versions of a CSV by key column(s).")
    p.add_argument("old")
    p.add_argument("new")
    p.add_argument("--key", action="append", default=[], help="key column (repeat for a composite key)")
    p.add_argument("--suggest-keys", action="store_true", help="list candidate key columns and stop")
    p.add_argument("--abs-tol", type=float, default=0.0)
    p.add_argument("--rel-tol", type=float, default=0.0)
    p.add_argument("--trim", action="store_true")
    p.add_argument("--ignore-case", action="store_true")
    p.add_argument("--null-tokens", default="")
    p.add_argument("--delimiter", default=None, help="force one delimiter for both files")
    p.add_argument("--examples", type=int, default=DEFAULT_EXAMPLES)
    p.add_argument("--row-shift-pct", type=float, default=ROW_SHIFT_PCT)
    p.add_argument("--null-jump", type=float, default=NULL_JUMP)
    p.add_argument("--out", default=None, help="also write the JSON report here")
    p.add_argument("--markdown", default=None, help="also write a Markdown report here")
    p.add_argument("--force", action="store_true", help="replace an existing report file (never an input)")
    return p


def main(argv=None):
    opt = build_parser().parse_args(argv)
    try:
        if opt.abs_tol < 0 or opt.rel_tol < 0:
            raise CsvDiffError("tolerances must be zero or positive")
        if opt.examples < 0:
            raise CsvDiffError("--examples must be zero or positive")
        opt.null_set = {t.strip() for t in opt.null_tokens.split(",") if t.strip()}
        old = read_table(opt.old, opt.delimiter)
        new = read_table(opt.new, opt.delimiter)
        if opt.suggest_keys:
            print(json.dumps(suggest_keys(old, new), indent=2, ensure_ascii=True))
            return 0
        if not opt.key:
            raise CsvDiffError("no --key given. Ask the user which column(s) identify a row; "
                               "run with --suggest-keys to list candidates. Rows are never matched by position.")
        outs = [p for p in (opt.out, opt.markdown) if p]
        check_outputs(outs, [opt.old, opt.new], opt.force)
        rep = diff(old, new, opt.key, opt)
        text = json.dumps(rep, indent=2, ensure_ascii=True, allow_nan=False)
        if opt.out:
            with open(opt.out, "w", encoding="utf-8", newline="\n") as fh:
                fh.write(text + "\n")
        if opt.markdown:
            with open(opt.markdown, "w", encoding="utf-8", newline="\n") as fh:
                fh.write(to_markdown(rep))
        print(text)
        return 0 if rep["verdict"] in ("identical", "equivalent") else 1
    except CsvDiffError as exc:
        sys.stderr.write("ERROR: %s\n" % exc)
        return 2


if __name__ == "__main__":
    sys.exit(main())
