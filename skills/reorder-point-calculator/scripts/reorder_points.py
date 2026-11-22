#!/usr/bin/env python3
"""Compute reorder points, days of stock left and order quantities from a sales CSV.

Usage:
    python reorder_points.py SALES.csv ITEMS.csv --buffer-days N
        [--cover-days N] [--as-of YYYY-MM-DD] [--missing-days zero|skip]
        [--exclude-spikes] [--z Z] [--out FILE [--force] [--dry-run]]

SALES.csv  columns: item (or sku), date (YYYY-MM-DD), qty (or quantity, units_sold);
           optional: unit. Several rows for one item and day are summed.
ITEMS.csv  columns: item (or sku), lead_time_days, stock; optional: moq, unit,
           buffer_days (overrides --buffer-days for that item).

Reads both files, prints one JSON document to stdout. Writes a file only when --out
is given; --out is refused when it resolves to SALES.csv or ITEMS.csv, even with
--force; an existing --out file needs --force; --dry-run writes nothing.

Exit codes: 0 report produced, 2 unusable input or arguments (message on stderr).
Arithmetic on the supplied numbers only. It does not predict demand.
"""
import argparse
import csv
import datetime as dt
import json
import math
import os
import statistics
import sys

# Demand basis: the most recent 28 days, long enough to cover four of every weekday.
WINDOW_DAYS = 28
# Fewer than 14 days of history gives an average dominated by one or two days.
MIN_DAYS = 14
# A day is a spike when above median + 3 * MAD (median absolute deviation).
SPIKE_K = 3.0
# More than 180 days of stock at the current rate is reported as a slow mover.
SLOW_DAYS = 180

ITEM_KEYS = ("item", "sku")
DATE_KEYS = ("date", "day")
QTY_KEYS = ("qty", "quantity", "units_sold")


class InputError(Exception):
    pass


def pick(header, keys):
    for k in keys:
        if k in header:
            return k
    return None


def read_csv(path, label):
    if not os.path.isfile(path):
        raise InputError(f"{label} file not found: {path}")
    try:
        with open(path, newline="", encoding="utf-8-sig") as fh:
            reader = csv.DictReader(fh)
            header = [h.strip().lower() for h in (reader.fieldnames or [])]
            rows = []
            for lineno, raw in enumerate(reader, start=2):
                row = {}
                for k, v in raw.items():
                    if k is None:
                        continue
                    row[k.strip().lower()] = (v or "").strip()
                rows.append((lineno, row))
    except (OSError, UnicodeDecodeError, csv.Error) as exc:
        raise InputError(f"cannot read {label} file {path}: {exc}")
    if not header or not rows:
        raise InputError(f"{label} file is empty or has no data rows: {path}")
    return header, rows


def parse_num(text):
    value = float(text)
    if math.isnan(value) or math.isinf(value):
        raise ValueError("not finite")
    return value


def ceil_clean(x):
    return int(math.ceil(round(x, 6)))


def num(x, digits=3):
    return None if x is None else round(x, digits)


def load_sales(path):
    header, rows = read_csv(path, "sales")
    ik, dk, qk = pick(header, ITEM_KEYS), pick(header, DATE_KEYS), pick(header, QTY_KEYS)
    if not (ik and dk and qk):
        raise InputError("sales file needs columns item (or sku), date and qty (or quantity, units_sold)")
    sales, bad = {}, []
    for lineno, row in rows:
        name = row.get(ik, "")
        try:
            day = dt.date.fromisoformat(row.get(dk, ""))
            qty = parse_num(row.get(qk, ""))
        except ValueError:
            bad.append(lineno)
            continue
        if not name:
            bad.append(lineno)
            continue
        sales.setdefault(name.casefold(), []).append((day, qty, row.get("unit", "").casefold()))
    warns = []
    if bad:
        warns.append(f"{len(bad)} sales rows skipped (blank item, date not YYYY-MM-DD, or qty not a number); first lines: {bad[:5]}")
    return sales, warns


def load_items(path):
    header, rows = read_csv(path, "items")
    ik = pick(header, ITEM_KEYS)
    if not ik or "lead_time_days" not in header or "stock" not in header:
        raise InputError("items file needs columns item (or sku), lead_time_days and stock")
    items, seen = [], set()
    for lineno, row in rows:
        name = row.get(ik, "")
        if not name:
            raise InputError(f"items file line {lineno}: blank item name")
        if name.casefold() in seen:
            raise InputError(f"items file line {lineno}: item listed twice: {name}")
        seen.add(name.casefold())
        items.append((name, row))
    return items


def analyse(name, row, rows, as_of, cfg):
    warns = []
    res = {
        "item": name, "action": None, "stock": None, "lead_time_days": None, "buffer_days": None,
        "window_days": None, "days_observed": None, "avg_daily": None, "std_daily": None,
        "safety_stock": None, "reorder_point": None, "days_left": None,
        "days_to_reorder_point": None, "stockout_before_arrival": None,
        "suggested_order_qty": None, "spike_days": [], "spikes_excluded": False,
        "dead_stock": False, "warnings": warns,
    }
    problems = []
    try:
        lead = parse_num(row.get("lead_time_days", ""))
        if lead < 0:
            raise ValueError
        res["lead_time_days"] = num(lead)
    except ValueError:
        lead = None
        problems.append("lead_time_days is missing, not a number, or negative")
    try:
        stock = parse_num(row.get("stock", ""))
        res["stock"] = num(stock)
    except ValueError:
        stock = None
        problems.append("stock is missing or not a number")
    try:
        buf = parse_num(row["buffer_days"]) if row.get("buffer_days", "") != "" else cfg["buffer_days"]
        if buf < 0:
            raise ValueError
    except ValueError:
        buf = None
        problems.append("buffer_days is not a non-negative number")
    res["buffer_days"] = num(buf)
    try:
        moq = parse_num(row["moq"]) if row.get("moq", "") != "" else 1.0
        if moq < 0:
            raise ValueError
    except ValueError:
        moq = 1.0
        problems.append("moq is not a non-negative number")
    if stock is not None and stock < 0:
        problems.append("stock is negative: fix the count before acting on this line")
    if lead == 0:
        warns.append("lead_time_days is 0: the reorder point is the buffer only; confirm the supplier lead time")

    units = {u for _, _, u in rows if u}
    item_unit = row.get("unit", "").casefold()
    if item_unit:
        units.add(item_unit)
    if len(units) > 1:
        problems.append("unit mismatch between sales rows and items file: " + ", ".join(sorted(units)))
    blocking = [p for p in problems if not p.startswith("stock is negative")]

    rows = [r for r in rows if r[0] <= as_of]
    if not rows:
        warns.append("no sales rows on or before the as-of date")
        res["action"] = "check data" if blocking else "too little data"
        warns.extend(problems)
        res["days_observed"] = 0
        return res
    first = min(d for d, _, _ in rows)
    span = (as_of - first).days + 1
    window = min(WINDOW_DAYS, span)
    start = as_of - dt.timedelta(days=window - 1)
    res["window_days"] = window

    per_day, negatives = {}, 0
    for d, q, _ in rows:
        if d < start:
            continue
        if q < 0:
            negatives += 1
            per_day.setdefault(d, 0.0)
        else:
            per_day[d] = per_day.get(d, 0.0) + q
    if negatives:
        warns.append(f"{negatives} negative-quantity rows (returns?) in the window were left out of demand")
    days_no_row = window - len(per_day)
    series = []
    for i in range(window):
        d = start + dt.timedelta(days=i)
        if d in per_day:
            series.append((d, per_day[d]))
        elif cfg["missing"] == "zero":
            series.append((d, 0.0))
    if days_no_row:
        how = "counted as zero sales" if cfg["missing"] == "zero" else "left out of the average"
        warns.append(f"{days_no_row} of {window} days have no sales row; {how}")
    res["days_observed"] = len(series)

    if blocking:
        res["action"] = "check data"
        warns.extend(problems)
        return res
    if len(series) < MIN_DAYS:
        res["action"] = "too little data"
        warns.append(f"only {len(series)} days of history in the window; at least {MIN_DAYS} are needed")
        warns.extend(problems)
        return res

    vals = [v for _, v in series]
    med = statistics.median(vals)
    mad = statistics.median([abs(v - med) for v in vals])
    if mad > 0:
        limit = med + SPIKE_K * mad
        spikes = [(d, v) for d, v in series if v > limit]
        res["spike_days"] = [{"date": d.isoformat(), "qty": num(v)} for d, v in spikes]
        if spikes:
            warns.append(f"{len(spikes)} spike day(s) above {round(limit, 3)} (median + {SPIKE_K:g} x MAD)")
            if cfg["exclude_spikes"]:
                keep = {d for d, _ in spikes}
                series = [(d, v) for d, v in series if d not in keep]
                res["spikes_excluded"] = True
                res["days_observed"] = len(series)
    else:
        warns.append("MAD is 0 (most days identical): spike check not applied")
    vals = [v for _, v in series]
    if not vals:
        res["action"] = "check data"
        warns.append("no days left after excluding spikes")
        return res

    avg = sum(vals) / len(vals)
    std = statistics.stdev(vals) if len(vals) > 1 else 0.0
    res["avg_daily"] = num(avg, 4)
    res["std_daily"] = num(std, 4)
    safety = avg * buf
    rop = ceil_clean(avg * lead + safety)
    res["safety_stock"] = num(safety)
    res["reorder_point"] = rop
    if cfg["z"] is not None:
        res["reorder_point_statistical"] = ceil_clean(avg * lead + cfg["z"] * std * math.sqrt(lead))

    if avg == 0:
        res["action"] = "no sales"
        if stock > 0:
            res["dead_stock"] = True
            warns.append(f"dead stock: {num(stock)} on hand and no sales in the window")
        warns.extend(problems)
        return res

    days_left = stock / avg
    to_rp = max(0.0, (stock - rop) / avg)
    res["days_left"] = num(days_left, 1)
    res["days_to_reorder_point"] = num(to_rp, 1)
    res["stockout_before_arrival"] = days_left < lead
    if res["stockout_before_arrival"]:
        warns.append(f"stock lasts {round(days_left, 1)} days, less than the {num(lead)}-day lead time: a stockout is likely before an order placed today arrives")
    if days_left > SLOW_DAYS:
        warns.append(f"slow mover: {round(days_left)} days of stock at the current rate")

    if problems:
        res["action"] = "check data"
        warns.extend(problems)
        return res
    if stock <= rop:
        res["action"] = "order now"
        target = rop + cfg["cover_days"] * avg
        res["suggested_order_qty"] = max(ceil_clean(target - stock), ceil_clean(moq))
    elif to_rp <= lead:
        res["action"] = "order within lead time"
    else:
        res["action"] = "fine"
    return res


def build_report(sales_path, items_path, cfg):
    sales, warns = load_sales(sales_path)
    items = load_items(items_path)
    all_dates = [d for rows in sales.values() for d, _, _ in rows]
    if not all_dates:
        raise InputError("sales file has no usable rows")
    as_of = cfg["as_of"] or max(all_dates)
    later = sum(1 for d in all_dates if d > as_of)
    if later:
        warns.append(f"{later} sales rows after the as-of date {as_of.isoformat()} were ignored")
    out, known = [], set()
    for name, row in items:
        known.add(name.casefold())
        out.append(analyse(name, row, sales.get(name.casefold(), []), as_of, cfg))
    unmatched = sorted(k for k in sales if k not in known)
    if unmatched:
        warns.append(f"{len(unmatched)} items have sales but are not in the items file: {unmatched[:10]}")
    counts = {}
    for r in out:
        counts[r["action"]] = counts.get(r["action"], 0) + 1
    return {
        "tool": "reorder_points",
        "as_of": as_of.isoformat(),
        "assumptions": {
            "window_days": WINDOW_DAYS, "min_days": MIN_DAYS, "spike_rule": f"median + {SPIKE_K:g} x MAD",
            "buffer_days_default": cfg["buffer_days"], "cover_days": cfg["cover_days"],
            "missing_days": cfg["missing"], "exclude_spikes": cfg["exclude_spikes"], "z": cfg["z"],
            "formula": "reorder_point = ceil(avg_daily x lead_time_days + avg_daily x buffer_days)",
        },
        "summary": counts,
        "file_warnings": warns,
        "items": out,
    }


def same_file(a, b):
    ra, rb = os.path.realpath(a), os.path.realpath(b)
    if os.path.normcase(ra) == os.path.normcase(rb):
        return True
    try:
        return os.path.exists(a) and os.path.exists(b) and os.path.samefile(a, b)
    except OSError:
        return False


def main(argv=None):
    ap = argparse.ArgumentParser(description="Reorder points from a sales CSV (arithmetic only).")
    ap.add_argument("sales")
    ap.add_argument("items")
    ap.add_argument("--buffer-days", type=float, required=True, help="days of demand kept as buffer (your choice)")
    ap.add_argument("--cover-days", type=float, default=0.0, help="extra days of demand to order beyond the reorder point (default 0)")
    ap.add_argument("--as-of", help="YYYY-MM-DD; default is the latest date in the sales file")
    ap.add_argument("--missing-days", choices=("zero", "skip"), default="zero")
    ap.add_argument("--exclude-spikes", action="store_true")
    ap.add_argument("--z", type=float, help="optional z-score for an extra statistical reorder point")
    ap.add_argument("--out")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    try:
        args = ap.parse_args(argv)
    except SystemExit as exc:
        return 2 if exc.code else 0
    if args.buffer_days < 0 or args.cover_days < 0 or (args.z is not None and args.z < 0):
        print("error: --buffer-days, --cover-days and --z must not be negative", file=sys.stderr)
        return 2
    as_of = None
    if args.as_of:
        try:
            as_of = dt.date.fromisoformat(args.as_of)
        except ValueError:
            print("error: --as-of must be YYYY-MM-DD", file=sys.stderr)
            return 2
    if args.out:
        for src in (args.sales, args.items):
            if same_file(args.out, src):
                print(f"error: --out resolves to an input file ({src}); refusing even with --force", file=sys.stderr)
                return 2
        if os.path.exists(args.out) and not args.force:
            print(f"error: {args.out} exists; pass --force to replace it", file=sys.stderr)
            return 2
    cfg = {"buffer_days": args.buffer_days, "cover_days": args.cover_days, "as_of": as_of,
           "missing": args.missing_days, "exclude_spikes": args.exclude_spikes, "z": args.z}
    try:
        report = build_report(args.sales, args.items, cfg)
    except InputError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    text = json.dumps(report, indent=2, allow_nan=False)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    print(text)
    if args.out:
        if args.dry_run:
            print(f"dry run: would write {len(text)} bytes to {args.out}", file=sys.stderr)
        else:
            try:
                with open(args.out, "w", encoding="utf-8") as fh:
                    fh.write(text + "\n")
            except OSError as exc:
                print(f"error: cannot write {args.out}: {exc}", file=sys.stderr)
                return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
