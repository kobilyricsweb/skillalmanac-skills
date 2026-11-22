#!/usr/bin/env python3
"""Check train/validation/test files for contamination between splits.

Usage:
    python check_leakage.py --split train=train.csv --split valid=valid.csv \
        --split test=test.csv [--id-col ID] [--text-cols A,B] [--group-col G] \
        [--date-col D] [--label-col Y] [--feature-cols C,D] [--threshold 0.8] \
        [--out report.json [--force]]

Reads: the split files only (CSV, or JSONL for .jsonl/.ndjson), UTF-8.
Writes: nothing, unless --out is given. --out writes one JSON report; it
refuses a path that resolves to any input file, even with --force, and refuses
an existing file without --force. Data is never modified.
Prints: one JSON object (see SKILL.md for the fields) on stdout.
Exit codes: 0 no leakage signal, 1 leakage or drift found (verdict warn or
fail), 2 usage or input error (message on stderr).

Splits are given in the order they are expected to run in time (train first).
Standard library only; no network.
"""
import argparse
import csv
import hashlib
import json
import os
import sys
import unicodedata
from datetime import datetime, timezone

# Word-shingle size. 3 words keeps short texts distinctive but still catches a
# changed word or two in a sentence.
SHINGLE_WORDS = 3
# Default Jaccard similarity for a near-duplicate. 0.8 means about four fifths
# of the 3-word shingles are shared; the user may change it.
DEFAULT_THRESHOLD = 0.8
# A shingle present in more rows than this in one split is a boilerplate
# phrase; indexing it would make the comparison quadratic. Skipped and counted.
MAX_POSTING = 500
# Cap on example rows or pairs listed per finding, to keep the report readable.
MAX_LISTED = 50
# Class-share difference (absolute, 0.10 = ten percentage points) reported as drift.
DRIFT_SHARE = 0.10
# Below this many labelled rows in a split, class shares are too noisy to make
# any drift claim (one row moves a 2 percent class by half).
MIN_SPLIT_LABELED = 100
# A class with fewer rows than this in a split is listed as rare.
RARE_CLASS_ROWS = 5
# Fewer pooled rows than this: no target-leakage claim.
MIN_TARGET_ROWS = 30
# A feature whose value predicts the label this often is near perfect.
NEAR_PERFECT_PURITY = 0.99
# A column with more distinct values than this share of rows is id-like and is
# not tested for value-to-label purity (it would be trivially pure).
ID_LIKE_SHARE = 0.5


class UsageError(Exception):
    pass


def norm_text(value):
    """Case, whitespace and punctuation normalisation for comparison keys."""
    text = unicodedata.normalize("NFKC", str(value)).casefold()
    out = []
    for ch in text:
        out.append(" " if unicodedata.category(ch).startswith("P") else ch)
    return " ".join("".join(out).split())


def load_rows(path):
    if not os.path.isfile(path):
        raise UsageError("file not found: " + path)
    ext = os.path.splitext(path)[1].lower()
    try:
        with open(path, "r", encoding="utf-8-sig", newline="") as fh:
            if ext in (".jsonl", ".ndjson"):
                rows = []
                for n, line in enumerate(fh, 1):
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        obj = json.loads(line)
                    except ValueError:
                        raise UsageError("%s line %d is not valid JSON" % (path, n))
                    if not isinstance(obj, dict):
                        raise UsageError("%s line %d is not a JSON object" % (path, n))
                    rows.append({k: (v if isinstance(v, str) else ("" if v is None else json.dumps(v, ensure_ascii=False))) for k, v in obj.items()})
                return rows
            csv.field_size_limit(min(sys.maxsize, 2 ** 31 - 1))
            reader = csv.DictReader(fh)
            if reader.fieldnames is None:
                raise UsageError("file is empty: " + path)
            return [{k: (v if v is not None else "") for k, v in r.items() if k is not None} for r in reader]
    except UnicodeDecodeError:
        raise UsageError("not valid UTF-8: " + path + " (re-save the file as UTF-8)")


def parse_date(value):
    """Return a naive UTC datetime or None. ISO text or epoch seconds/ms."""
    s = str(value).strip()
    if not s:
        return None
    try:
        num = float(s)
        if abs(num) >= 1e11:  # epoch milliseconds
            num /= 1000.0
        return datetime.fromtimestamp(num, tz=timezone.utc).replace(tzinfo=None)
    except (ValueError, OverflowError, OSError):
        pass
    t = s.replace("Z", "+00:00").replace("/", "-")
    try:
        dt = datetime.fromisoformat(t)
    except ValueError:
        return None
    if dt.tzinfo is not None:
        dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt


def digest(text):
    return hashlib.sha1(text.encode("utf-8")).hexdigest()[:16]


def shingles(norm):
    words = norm.split()
    if len(words) <= SHINGLE_WORDS:
        return {hash(" ".join(words))}
    return {hash(" ".join(words[i:i + SHINGLE_WORDS])) for i in range(len(words) - SHINGLE_WORDS + 1)}


def parse_splits(items):
    splits = []
    seen = set()
    for item in items:
        if "=" in item:
            name, path = item.split("=", 1)
        else:
            path = item
            name = os.path.splitext(os.path.basename(item))[0]
        if not name or not path:
            raise UsageError("bad --split value: " + item)
        if name in seen:
            raise UsageError("duplicate split name: " + name)
        seen.add(name)
        splits.append((name, path))
    if len(splits) < 2:
        raise UsageError("give at least two --split name=path values")
    return splits


def need_columns(name, rows, cols):
    have = set(rows[0].keys()) if rows else set()
    for c in cols:
        if rows and c not in have:
            raise UsageError("split %s has no column %r (columns: %s)" % (name, c, ", ".join(sorted(have))))


def check(args):
    split_defs = parse_splits(args.split)
    text_cols = [c for c in (args.text_cols or "").split(",") if c]
    feature_cols = [c for c in (args.feature_cols or "").split(",") if c]
    data = []
    for name, path in split_defs:
        rows = load_rows(path)
        if not rows:
            raise UsageError("split %s has no data rows: %s" % (name, path))
        data.append((name, path, rows))
    first_cols = list(data[0][2][0].keys())
    reserved = {c for c in (args.id_col, args.group_col, args.date_col, args.label_col) if c}
    for name, _p, rows in data:
        need_columns(name, rows, [c for c in [args.id_col, args.group_col, args.date_col, args.label_col] + text_cols + feature_cols if c])
    if not text_cols:
        text_cols = [c for c in first_cols if c not in reserved]
    if not text_cols:
        raise UsageError("no text columns left to compare; pass --text-cols")
    if not feature_cols:
        feature_cols = [c for c in first_cols if c not in reserved]

    report = {"splits": [], "text_columns": text_cols, "threshold": args.threshold}
    keyed = []  # per split: list of (row_id, norm_key, row)
    for name, path, rows in data:
        items = []
        empty = 0
        for i, row in enumerate(rows, 1):
            rid = row.get(args.id_col, "") if args.id_col else ""
            rid = rid if rid != "" else str(i)
            key = norm_text(" ".join(row.get(c, "") for c in text_cols))
            if not key:
                empty += 1
                continue
            items.append((rid, key, row))
        keyed.append((name, items))
        report["splits"].append({"name": name, "path": path, "rows": len(rows), "empty_key_rows": empty})

    # Exact overlaps (hash of the normalised key) between splits.
    where = {}
    within = {}
    for si, (name, items) in enumerate(keyed):
        seen_here = {}
        for rid, key, row in items:
            h = digest(key)
            where.setdefault(h, []).append((si, rid, row.get(args.label_col, "") if args.label_col else None))
            seen_here[h] = seen_here.get(h, 0) + 1
        within[name] = sum(c - 1 for c in seen_here.values() if c > 1)
    for s in report["splits"]:
        s["duplicate_rows_within_split"] = within[s["name"]]
    exact = []
    for h, locs in where.items():
        present = sorted({l[0] for l in locs})
        if len(present) > 1:
            rec = {"hash": h, "splits": [keyed[i][0] for i in present],
                   "rows": [{"split": keyed[l[0]][0], "row_id": l[1]} for l in locs[:MAX_LISTED]]}
            if args.label_col:
                labels = sorted({l[2] for l in locs})
                rec["labels"] = labels
                rec["label_conflict"] = len(labels) > 1
            exact.append(rec)
    exact.sort(key=lambda r: (-len(r["rows"]), r["hash"]))
    report["exact_overlaps"] = {"count": len(exact), "examples": exact[:MAX_LISTED]}
    exact_hashes = {r["hash"] for r in exact}

    # Near duplicates by word-shingle Jaccard, across splits only.
    near = []
    skipped_shingles = 0
    prepared = []
    for name, items in keyed:
        prepared.append([(rid, key, shingles(key)) for rid, key, _r in items])
    for a in range(len(prepared)):
        index = {}
        for ri, (_rid, _k, sh) in enumerate(prepared[a]):
            for s in sh:
                index.setdefault(s, []).append(ri)
        for s in [s for s, p in index.items() if len(p) > MAX_POSTING]:
            skipped_shingles += 1
            del index[s]
        for b in range(a + 1, len(prepared)):
            for rid_b, key_b, sh_b in prepared[b]:
                counts = {}
                for s in sh_b:
                    for ri in index.get(s, ()):
                        counts[ri] = counts.get(ri, 0) + 1
                for ri, inter in counts.items():
                    rid_a, key_a, sh_a = prepared[a][ri]
                    if key_a == key_b:
                        continue
                    union = len(sh_a) + len(sh_b) - inter
                    sim = inter / union if union else 0.0
                    if sim >= args.threshold:
                        near.append({"split_a": keyed[a][0], "row_id_a": rid_a, "split_b": keyed[b][0],
                                     "row_id_b": rid_b, "similarity": round(sim, 4)})
    near.sort(key=lambda r: (-r["similarity"], r["split_a"], str(r["row_id_a"]), str(r["row_id_b"])))
    report["near_duplicates"] = {"count": len(near), "skipped_common_shingles": skipped_shingles,
                                 "pairs": near[:MAX_LISTED]}

    # Group overlap.
    if args.group_col:
        groups = {}
        for si, (name, _items) in enumerate(keyed):
            rows = data[si][2]
            for row in rows:
                g = row.get(args.group_col, "").strip()
                if g:
                    groups.setdefault(g, {}).setdefault(si, 0)
                    groups[g][si] += 1
        shared = {g: d for g, d in groups.items() if len(d) > 1}
        per_split = []
        for si, (name, _i) in enumerate(keyed):
            rows = data[si][2]
            hit = sum(1 for r in rows if r.get(args.group_col, "").strip() in shared)
            per_split.append({"split": name, "rows_in_shared_groups": hit, "share": round(hit / len(rows), 4)})
        ex = [{"group": g, "splits": {keyed[i][0]: n for i, n in sorted(d.items())}} for g, d in sorted(shared.items())]
        report["group_overlaps"] = {"group_column": args.group_col, "groups_total": len(groups),
                                    "groups_shared": len(shared), "per_split": per_split, "examples": ex[:MAX_LISTED]}
    else:
        report["group_overlaps"] = None

    # Time order.
    if args.date_col:
        spans = []
        bad_dates = {}
        for si, (name, _items) in enumerate(keyed):
            dated = []
            miss = 0
            for i, row in enumerate(data[si][2], 1):
                d = parse_date(row.get(args.date_col, ""))
                rid = row.get(args.id_col, "") if args.id_col else ""
                rid = rid if rid != "" else str(i)
                if d is None:
                    miss += 1
                else:
                    dated.append((d, rid))
            bad_dates[name] = miss
            spans.append(dated)
        for s in report["splits"]:
            s["unparseable_dates"] = bad_dates[s["name"]]
        violations = []
        ranges = []
        for si, (name, _i) in enumerate(keyed):
            if spans[si]:
                ranges.append({"split": name, "min": min(d for d, _ in spans[si]).isoformat(),
                               "max": max(d for d, _ in spans[si]).isoformat()})
            else:
                ranges.append({"split": name, "min": None, "max": None})
        for a in range(len(keyed)):
            for b in range(a + 1, len(keyed)):
                if not spans[a] or not spans[b]:
                    continue
                a_max = max(d for d, _ in spans[a])
                early = sorted([(d, rid) for d, rid in spans[b] if d < a_max])
                if early:
                    violations.append({"earlier_split": keyed[a][0], "later_split": keyed[b][0],
                                       "earlier_split_max": a_max.isoformat(),
                                       "later_rows_before_that": len(early),
                                       "share_of_later_split": round(len(early) / len(spans[b]), 4),
                                       "examples": [{"row_id": rid, "date": d.isoformat()} for d, rid in early[:10]]})
        report["time_violations"] = {"date_column": args.date_col, "ranges": ranges, "violations": violations}
    else:
        report["time_violations"] = None

    # Class balance.
    if args.label_col:
        per = []
        for si, (name, _i) in enumerate(keyed):
            rows = data[si][2]
            counts = {}
            for r in rows:
                lab = r.get(args.label_col, "").strip()
                if lab != "":
                    counts[lab] = counts.get(lab, 0) + 1
            n = sum(counts.values())
            per.append({"split": name, "labeled_rows": n, "counts": dict(sorted(counts.items())),
                        "shares": {k: round(v / n, 4) for k, v in sorted(counts.items())} if n else {},
                        "enough_for_drift_claim": n >= MIN_SPLIT_LABELED})
        classes = sorted({k for p in per for k in p["counts"]})
        drift = []
        missing = []
        rare = []
        for c in classes:
            usable = [p for p in per if p["enough_for_drift_claim"]]
            if len(usable) > 1:
                shares = [(p["shares"].get(c, 0.0), p["split"]) for p in usable]
                hi, lo = max(shares), min(shares)
                if hi[0] - lo[0] >= DRIFT_SHARE:
                    drift.append({"class": c, "highest": {"split": hi[1], "share": hi[0]},
                                  "lowest": {"split": lo[1], "share": lo[0]}, "difference": round(hi[0] - lo[0], 4)})
            for p in per:
                cnt = p["counts"].get(c, 0)
                if cnt == 0:
                    missing.append({"class": c, "split": p["split"]})
                elif cnt < RARE_CLASS_ROWS:
                    rare.append({"class": c, "split": p["split"], "rows": cnt})
        report["class_balance"] = {"label_column": args.label_col, "per_split": per, "drift": drift,
                                   "missing_classes": missing, "rare_classes": rare,
                                   "note": "no drift claim for splits under %d labelled rows" % MIN_SPLIT_LABELED}
    else:
        report["class_balance"] = None

    # Target leakage.
    if args.label_col:
        pooled = [r for _n, _p, rows in data for r in rows if r.get(args.label_col, "").strip() != ""]
        leaks = []
        checked = 0
        if len(pooled) >= MIN_TARGET_ROWS:
            labels = sorted({r[args.label_col].strip() for r in pooled})
            for col in feature_cols:
                if col == args.label_col:
                    continue
                vals = [(r.get(col, "").strip(), r[args.label_col].strip()) for r in pooled]
                vals = [(v, l) for v, l in vals if v != ""]
                if len(vals) < MIN_TARGET_ROWS:
                    continue
                by = {}
                for v, l in vals:
                    by.setdefault(v, {}).setdefault(l, 0)
                    by[v][l] += 1
                distinct = len(by)
                checked += 1
                if distinct <= ID_LIKE_SHARE * len(vals):
                    pure = sum(max(d.values()) for d in by.values()) / len(vals)
                    if pure >= NEAR_PERFECT_PURITY:
                        leaks.append({"column": col, "kind": "perfect" if pure == 1.0 else "near_perfect",
                                      "purity": round(pure, 4), "distinct_values": distinct, "rows": len(vals)})
                        continue
                if len(labels) == 2:
                    nums = {}
                    ok = True
                    for v, d in by.items():
                        try:
                            nums[float(v)] = d
                        except ValueError:
                            ok = False
                            break
                    if ok and len(nums) > 2 and all(len(d) == 1 for d in nums.values()):
                        seq = [next(iter(nums[k])) for k in sorted(nums)]
                        flips = sum(1 for i in range(1, len(seq)) if seq[i] != seq[i - 1])
                        if flips == 1:
                            leaks.append({"column": col, "kind": "threshold_separable", "purity": 1.0,
                                          "distinct_values": distinct, "rows": len(vals)})
        leaks.sort(key=lambda r: (r["kind"], r["column"]))
        report["target_leakage"] = {"columns_checked": checked, "pooled_labeled_rows": len(pooled),
                                    "claim_made": len(pooled) >= MIN_TARGET_ROWS, "suspects": leaks}
    else:
        report["target_leakage"] = None

    # Verdict.
    fail, warn, actions = [], [], []
    if exact:
        fail.append("%d record(s) appear in more than one split (exact after normalising)" % len(exact))
        actions.append("Drop the repeated records from the evaluation split, or from train if the evaluation split would shrink below a usable size; then re-run.")
    gro = report["group_overlaps"]
    if gro and gro["groups_shared"]:
        fail.append("%d group(s) in %s occur in more than one split" % (gro["groups_shared"], gro["group_column"]))
        actions.append("Re-split by %s so each group lands in exactly one split (group-aware split); check the class shares afterwards." % gro["group_column"])
    tv = report["time_violations"]
    if tv and tv["violations"]:
        fail.append("%d later split(s) contain rows dated before the end of an earlier split" % len(tv["violations"]))
        actions.append("Use a time-ordered split on %s: train before validation before test, with a gap if labels mature late." % tv["date_column"])
    tl = report["target_leakage"]
    if tl and tl["suspects"]:
        fail.append("%d column(s) predict the label (almost) perfectly: %s" % (len(tl["suspects"]), ", ".join(s["column"] for s in tl["suspects"])))
        actions.append("For each suspect column, ask whether its value exists at prediction time; remove it from the features if it does not.")
    if near:
        warn.append("%d near-duplicate pair(s) across splits at similarity >= %s" % (len(near), args.threshold))
        actions.append("Review the listed pairs; remove or merge near-duplicates across splits, then re-run at the same threshold.")
    cb = report["class_balance"]
    if cb and cb["drift"]:
        warn.append("class share differs by %d points or more between splits for %d class(es)" % (int(DRIFT_SHARE * 100), len(cb["drift"])))
        actions.append("Re-split with stratification on %s." % cb["label_column"])
    if cb and cb["missing_classes"]:
        warn.append("%d class/split combination(s) have zero rows" % len(cb["missing_classes"]))
    status = "fail" if fail else ("warn" if warn else "pass")
    report["verdict"] = {"status": status, "reasons": fail + warn, "proposed_actions": actions,
                         "note": "A proposed action is a plan; no data was changed."}
    return report


def resolve(path):
    return os.path.normcase(os.path.realpath(path))


def main(argv=None):
    p = argparse.ArgumentParser(description="Check train/validation/test files for leakage between splits.")
    p.add_argument("--split", action="append", default=[], help="name=path, repeat; give them in time order")
    p.add_argument("--id-col")
    p.add_argument("--text-cols", help="comma list; default every column not named as id, group, date or label")
    p.add_argument("--group-col")
    p.add_argument("--date-col")
    p.add_argument("--label-col")
    p.add_argument("--feature-cols", help="comma list for the target-leakage check; default every non-reserved column")
    p.add_argument("--threshold", type=float, default=DEFAULT_THRESHOLD)
    p.add_argument("--out", help="write the JSON report here (never over an input)")
    p.add_argument("--force", action="store_true", help="overwrite an existing --out file")
    args = p.parse_args(argv)
    try:
        if not 0.0 < args.threshold <= 1.0:
            raise UsageError("--threshold must be above 0 and at most 1")
        if args.out:
            inputs = {resolve(path) for _n, path in parse_splits(args.split)}
            target = resolve(args.out)
            if target in inputs:
                raise UsageError("refusing to write the report over an input file: " + args.out)
            if os.path.exists(args.out) and not args.force:
                raise UsageError("output exists; pass --force to overwrite: " + args.out)
        report = check(args)
        text = json.dumps(report, indent=2, ensure_ascii=False)
        if args.out:
            with open(args.out, "w", encoding="utf-8", newline="\n") as fh:
                fh.write(text + "\n")
    except UsageError as exc:
        sys.stderr.write("error: %s\n" % exc)
        return 2
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except AttributeError:
        pass
    sys.stdout.write(text + "\n")
    return 0 if report["verdict"]["status"] == "pass" else 1


if __name__ == "__main__":
    sys.exit(main())
