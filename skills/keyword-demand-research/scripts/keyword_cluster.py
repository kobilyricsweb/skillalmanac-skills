#!/usr/bin/env python3
"""Cluster a keyword export, de-duplicate close variants, label intent and read trends.

Usage:
    python keyword_cluster.py keywords.csv [--out clusters.csv] [--rules rules.json]
                              [--brand "acme,acme corp"] [--exclude "regex"] [--json]

Reads:  one CSV exported from the user's own keyword tool. Required column: `keyword`.
        Monthly volume columns are any headers that end in YYYY-MM (for example `2026-10`
        or `us_2026-10`). At least 6 monthly columns are needed for trend reading.
        Optional: --rules, a JSON file {"intents": [{"label": "...", "pattern": "regex"}, ...]},
        first match wins; it replaces the built-in intent rules.
Writes: only the file given with --out (one row per keyword with its cluster). Nothing else.
Network: none.
Exit codes: 0 = report produced, 2 = input problem (message says what to fix).

Edit the rules file, never this script, to change how keywords are labelled.
"""
import csv
import json
import re
import statistics
import sys

MONTH_COL = re.compile(r"(?:^|[^0-9])(\d{4})-(\d{2})$")
# A change inside +/-15% between two 3-month windows is within the noise of bucketed
# volume data (neighbouring Google Ads buckets differ by 20-25%), so it is called flat.
TREND_THRESHOLD_PCT = 15.0
# Identical monthly series are strong evidence of a merged close variant only when the
# volume is high enough that two unrelated keywords rarely share every bucket.
IDENTICAL_SERIES_MIN_AVG = 500
IDENTICAL_SERIES_SHARED_WORDS_MIN_AVG = 200
# A month this many times above the median, outside the last 3 months, is a one-off spike.
SPIKE_RATIO = 3.0
# A last-month rise this large after 3 falling months is flagged so nobody calls it a recovery.
REBOUND_PCT = 10.0
MIN_MONTHS_FOR_TREND = 6

DEFAULT_INTENTS = [
    ("transactional", r"\b(buy|price|prices|pricing|cost|coupon|discount|deal|deals|cheap|order|for sale|near me|"
                      r"download|free|template|templates|generator|calculator|tool|tools|app|software|hire|quote)\b"),
    ("commercial", r"\b(best|top|vs|versus|review|reviews|alternative|alternatives|comparison|compare|compared|"
                   r"worth it|ranking|rated)\b"),
    ("informational", r"\b(how|what|why|when|where|who|which|guide|tutorial|example|examples|meaning|definition|"
                      r"ideas|tips|is|are|can|does|do|should|learn|explained|checklist)\b"),
]


def fail(msg):
    sys.stderr.write("ERROR: " + msg + "\n")
    sys.exit(2)


def tokens(keyword):
    """Lower-case words with punctuation removed and a simple plural 's' stripped."""
    words = re.sub(r"[^a-z0-9 ]+", " ", keyword.lower()).split()
    out = []
    for w in words:
        if len(w) > 3 and w.endswith("s") and not w.endswith("ss"):
            w = w[:-1]
        out.append(w)
    return out


def to_number(text):
    text = (text or "").strip().replace(",", "")
    if text == "":
        return None
    try:
        return float(text)
    except ValueError:
        return None


class Groups:
    """Union-find that remembers which rule joined each keyword."""

    def __init__(self, n):
        self.parent = list(range(n))
        self.rule = [""] * n

    def find(self, i):
        while self.parent[i] != i:
            self.parent[i] = self.parent[self.parent[i]]
            i = self.parent[i]
        return i

    def join(self, a, b, rule):
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.parent[rb] = ra
            if not self.rule[b]:
                self.rule[b] = rule


def pct(new, old):
    if old is None or new is None or old == 0:
        return None
    return round((new - old) / old * 100.0, 1)


def mean(values):
    values = [v for v in values if v is not None]
    return sum(values) / len(values) if values else None


def read_trend(series):
    """series: list of monthly values, oldest first (None allowed). Returns a dict of readings."""
    out = {"avg12": None, "last": None, "peak_month_index": None, "peak": None, "last3_vs_prev3_pct": None,
           "yoy_3m_pct": None, "trend": "not enough months", "flags": []}
    vals = [v for v in series if v is not None]
    if not vals:
        return out
    out["avg12"] = round(mean(series[-12:]) or 0, 1)
    out["last"] = series[-1]
    peak = max(vals)
    out["peak"] = peak
    out["peak_month_index"] = max(i for i, v in enumerate(series) if v == peak)
    if len(series) < MIN_MONTHS_FOR_TREND:
        return out
    last3, prev3 = mean(series[-3:]), mean(series[-6:-3])
    change = pct(last3, prev3)
    out["last3_vs_prev3_pct"] = change
    if change is None:
        out["trend"] = "new" if (prev3 in (None, 0) and (last3 or 0) > 0) else "no volume"
    elif change > TREND_THRESHOLD_PCT:
        out["trend"] = "rising"
    elif change < -TREND_THRESHOLD_PCT:
        out["trend"] = "falling"
    else:
        out["trend"] = "flat"
    if len(series) >= 15:
        year_ago3 = mean(series[-15:-12])
        out["yoy_3m_pct"] = pct(last3, year_ago3)
        if year_ago3 in (None, 0) and (last3 or 0) > 0:
            out["flags"].append("new-in-last-12-months")
    elif len(series) >= 13:
        if series[-13] in (None, 0) and (series[-1] or 0) > 0:
            out["flags"].append("new-in-last-12-months")
    median = statistics.median(vals)
    if median > 0 and peak >= SPIKE_RATIO * median and out["peak_month_index"] < len(series) - 3:
        out["flags"].append("one-off-spike")
    if len(series) >= 5 and all(v is not None for v in series[-5:]):
        a, b, c, d, e = series[-5:]
        if a > b > c > d and d > 0 and (e - d) / d * 100.0 >= REBOUND_PCT:
            out["flags"].append("one-month-rebound-after-decline")
    if out["peak_month_index"] < len(series) - 3 and out["last"] is not None and peak > 0:
        out["flags"].append("%d%%-below-peak" % round((peak - out["last"]) / peak * 100.0))
    return out


def load_rules(path):
    if not path:
        return [(label, re.compile(pattern)) for label, pattern in DEFAULT_INTENTS]
    try:
        data = json.load(open(path, encoding="utf-8"))
        return [(r["label"], re.compile(r["pattern"])) for r in data["intents"]]
    except (OSError, ValueError, KeyError, TypeError, re.error) as exc:
        fail("cannot read rules file %s: %s. Expected {\"intents\": [{\"label\": ..., \"pattern\": ...}]}" % (path, exc))


def main(argv):
    args, opts, flags = [], {}, set()
    i = 0
    while i < len(argv):
        a = argv[i]
        if a in ("--out", "--rules", "--brand", "--exclude"):
            if i + 1 >= len(argv):
                fail("%s needs a value" % a)
            opts[a] = argv[i + 1]
            i += 2
        elif a.startswith("--"):
            flags.add(a)
            i += 1
        else:
            args.append(a)
            i += 1
    if len(args) != 1:
        print(__doc__)
        return 2
    try:
        fh = open(args[0], encoding="utf-8-sig", newline="")
    except OSError as exc:
        fail("cannot open %s: %s" % (args[0], exc))
    with fh:
        reader = csv.DictReader(fh)
        if not reader.fieldnames or "keyword" not in [f.strip().lower() for f in reader.fieldnames]:
            fail("the CSV needs a header row with a 'keyword' column")
        kw_col = [f for f in reader.fieldnames if f.strip().lower() == "keyword"][0]
        month_cols = sorted((f for f in reader.fieldnames if MONTH_COL.search(f.strip())),
                            key=lambda f: MONTH_COL.search(f.strip()).groups())
        rows = [r for r in reader if (r.get(kw_col) or "").strip()]
    if not rows:
        fail("no keyword rows found")
    if not month_cols:
        fail("no monthly columns found; headers must end in YYYY-MM, for example 2026-10")
    months = ["-".join(MONTH_COL.search(c.strip()).groups()) for c in month_cols]
    if len(set(months)) != len(months):
        fail("two columns end in the same month; export one location per file or keep one prefix")

    rules = load_rules(opts.get("--rules"))
    brands = [b.strip().lower() for b in opts.get("--brand", "").split(",") if b.strip()]
    try:
        exclude = re.compile(opts["--exclude"], re.I) if "--exclude" in opts else None
    except re.error as exc:
        fail("--exclude is not a valid regular expression: %s" % exc)

    items = []
    seen = set()
    for r in rows:
        kw = r[kw_col].strip()
        if kw.lower() in seen:
            continue
        seen.add(kw.lower())
        series = [to_number(r.get(c)) for c in month_cols]
        items.append({"keyword": kw, "series": series, "tokens": tokens(kw)})

    # --- close-variant clustering ---
    groups = Groups(len(items))
    by_tokens, by_series = {}, {}
    for idx, it in enumerate(items):
        key = " ".join(it["tokens"])
        if key in by_tokens:
            groups.join(by_tokens[key], idx, "same words after plural/punctuation")
        else:
            by_tokens[key] = idx
        if all(v is not None for v in it["series"]) and len(it["series"]) >= MIN_MONTHS_FOR_TREND and sum(it["series"]) > 0:
            by_series.setdefault(tuple(it["series"]), []).append(idx)
    for series, members in by_series.items():
        avg = sum(series[-12:]) / len(series[-12:])
        first = members[0]
        for other in members[1:]:
            a, b = set(items[first]["tokens"]), set(items[other]["tokens"])
            shared = len(a & b) / max(1, min(len(a), len(b)))
            if a == b:
                groups.join(first, other, "identical series, same word set")
            elif avg >= IDENTICAL_SERIES_MIN_AVG:
                groups.join(first, other, "identical series, avg >= %d" % IDENTICAL_SERIES_MIN_AVG)
            elif avg >= IDENTICAL_SERIES_SHARED_WORDS_MIN_AVG and shared >= 0.5:
                groups.join(first, other, "identical series, half the words shared")

    clusters = {}
    for idx, it in enumerate(items):
        clusters.setdefault(groups.find(idx), []).append(idx)

    def avg12(it):
        return mean(it["series"][-12:]) or 0

    out_clusters = []
    for members in clusters.values():
        rep = max(members, key=lambda m: (avg12(items[m]), -len(items[m]["keyword"])))
        kw = items[rep]["keyword"]
        low = kw.lower()
        if exclude and exclude.search(low):
            intent = "excluded"
        elif any(re.search(r"\b" + re.escape(b) + r"\b", low) for b in brands):
            intent = "navigational-brand"
        else:
            intent = next((label for label, rx in rules if rx.search(low)), "unclassified")
        reading = read_trend(items[rep]["series"])
        out_clusters.append({"representative": kw, "intent": intent, "variants": [items[m]["keyword"] for m in members],
                             "merge_rules": sorted({groups.rule[m] for m in members if groups.rule[m]}),
                             "raw_sum_avg12": round(sum(avg12(items[m]) for m in members), 1), **reading,
                             "peak_month": months[reading["peak_month_index"]] if reading["peak_month_index"] is not None else None})
    out_clusters.sort(key=lambda c: -(c["avg12"] or 0))

    counted = [c for c in out_clusters if c["intent"] not in ("excluded", "navigational-brand")]
    raw_total = round(sum(avg12(it) for it in items), 1)
    dedup_total = round(sum(c["avg12"] or 0 for c in out_clusters), 1)
    counted_total = round(sum(c["avg12"] or 0 for c in counted), 1)
    by_intent = {}
    for c in out_clusters:
        slot = by_intent.setdefault(c["intent"], {"clusters": 0, "avg12": 0.0})
        slot["clusters"] += 1
        slot["avg12"] = round(slot["avg12"] + (c["avg12"] or 0), 1)

    n = len(months)
    total_reading = None
    if n >= MIN_MONTHS_FOR_TREND:
        rep_series = []
        for c in counted:
            rep_item = next(it for it in items if it["keyword"] == c["representative"])
            rep_series.append(rep_item["series"])
        monthly_totals = [sum((s[k] or 0) for s in rep_series) for k in range(n)]
        total_reading = read_trend(monthly_totals)
        total_reading["monthly_totals"] = dict(zip(months, monthly_totals))
        total_reading["peak_month"] = months[total_reading["peak_month_index"]]

    summary = {
        "input": {"keywords": len(items), "months": months[0] + " to " + months[-1], "month_count": n},
        "totals": {"raw_sum_avg12_all_keywords": raw_total, "dedup_sum_avg12_all_clusters": dedup_total,
                   "dedup_sum_avg12_counted": counted_total, "clusters": len(out_clusters),
                   "clusters_counted": len(counted),
                   "double_counted_if_raw": round(raw_total - dedup_total, 1)},
        "by_intent": by_intent,
        "total_trend_counted": total_reading,
        "windows": {"last3": months[-3:] if n >= 3 else months, "prev3": months[-6:-3] if n >= 6 else [],
                    "year_ago3": months[-15:-12] if n >= 15 else []},
        "clusters": out_clusters,
        "limits": ["Volumes from ad platforms are buckets, not counts; close variants often share one number.",
                   "Intent labels come from word rules; read the top clusters by eye and fix the rules file.",
                   "Searches inside AI assistants, apps and marketplaces are not in any keyword export.",
                   "Identical-series merges can be wrong; the merge rule is listed per cluster for review."],
    }

    if "--out" in opts:
        try:
            with open(opts["--out"], "w", encoding="utf-8", newline="") as out:
                w = csv.writer(out)
                w.writerow(["keyword", "cluster_representative", "is_representative", "intent", "avg12", "cluster_trend",
                            "last3_vs_prev3_pct", "yoy_3m_pct", "flags", "merge_rules"])
                for c in out_clusters:
                    for v in c["variants"]:
                        item = next(it for it in items if it["keyword"] == v)
                        w.writerow([v, c["representative"], int(v == c["representative"]), c["intent"], round(avg12(item), 1),
                                    c["trend"], c["last3_vs_prev3_pct"], c["yoy_3m_pct"], "; ".join(c["flags"]),
                                    "; ".join(c["merge_rules"])])
        except OSError as exc:
            fail("cannot write %s: %s" % (opts["--out"], exc))

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if "--json" in flags:
        print(json.dumps(summary, indent=2))
        return 0
    t = summary["totals"]
    print("KEYWORD DEMAND REPORT")
    print("Input: %d keywords, %d months (%s)" % (len(items), n, summary["input"]["months"]))
    print("Raw sum of 12-month averages (every keyword):   %s" % t["raw_sum_avg12_all_keywords"])
    print("De-duplicated sum (one per cluster):            %s   <- working figure" % t["dedup_sum_avg12_all_clusters"])
    print("Counted (minus excluded and brand-navigational): %s in %d clusters" % (t["dedup_sum_avg12_counted"], t["clusters_counted"]))
    print("Double counting removed: %s" % t["double_counted_if_raw"])
    print("\nBy intent:")
    for label, slot in sorted(by_intent.items(), key=lambda kv: -kv[1]["avg12"]):
        print("  %-20s %4d clusters  %10s" % (label, slot["clusters"], slot["avg12"]))
    if total_reading:
        print("\nTotal trend (counted clusters): %s; last 3 months vs previous 3: %s%%; vs same 3 months a year ago: %s%%"
              % (total_reading["trend"], total_reading["last3_vs_prev3_pct"], total_reading["yoy_3m_pct"]))
        print("  peak %s = %s; last month = %s; flags: %s" % (total_reading["peak_month"], total_reading["peak"],
              total_reading["last"], ", ".join(total_reading["flags"]) or "none"))
        print("  windows: last3 = %s, prev3 = %s" % (", ".join(summary["windows"]["last3"]), ", ".join(summary["windows"]["prev3"])))
    else:
        print("\nTrend: not read (fewer than %d monthly columns)." % MIN_MONTHS_FOR_TREND)
    print("\nClusters (largest first):")
    print("  %-38s %-18s %9s %-9s %8s %8s  %s" % ("representative", "intent", "avg12", "trend", "3m%", "yoy3m%", "variants / flags"))
    for c in out_clusters:
        extra = []
        if len(c["variants"]) > 1:
            extra.append("%d variants (%s)" % (len(c["variants"]), "; ".join(c["merge_rules"])))
        extra += c["flags"]
        print("  %-38s %-18s %9s %-9s %8s %8s  %s" % (c["representative"][:38], c["intent"], c["avg12"], c["trend"],
              c["last3_vs_prev3_pct"], c["yoy_3m_pct"], " | ".join(extra)))
    print("\nLimits:")
    for line in summary["limits"]:
        print("  - " + line)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
