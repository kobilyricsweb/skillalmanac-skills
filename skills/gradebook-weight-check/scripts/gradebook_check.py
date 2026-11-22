#!/usr/bin/env python3
"""Recompute weighted final grades from a CSV gradebook and a scheme file.

Usage:
    python gradebook_check.py SCORES.csv SCHEME.json [options]

Options:
    --missing {flag,exclude,zero}  how blank scores are treated (default: flag,
                                   which computes like exclude and marks the
                                   result provisional)
    --id-column NAME               CSV column holding the student id (student_id)
    --expected-column NAME         CSV column with the teacher's recorded final
                                   (overrides "expected_column" in the scheme)
    --tolerance N                  allowed gap to the recorded final (0.05)
    --what-if ITEM --target N      minimum score on ITEM (blank for that student)
                                   that makes the recorded final reach N
    --delimiter CHAR               CSV delimiter (default ",")
    --out FILE [--force]           write the JSON report to FILE instead of stdout

Reads: the scores CSV and the scheme JSON. Only the id column, the item
columns and the expected column are used; any other column (for example a
name column) is never read into the output or into error messages.
Writes: nothing, unless --out is given. --out refuses a path that resolves to
the scores file or the scheme file, even with --force, and refuses an existing
file unless --force is given.

Output: strict JSON (no NaN or Infinity). See SKILL.md for the contract.
Exit codes: 0 computed and consistent, 1 scheme invalid or the recorded final
disagrees with the recomputed one for at least one student, 2 usage or file
problem (message on stderr).

This script does arithmetic and consistency checks only. It never decides a
grade or a policy.
"""
import argparse
import csv
import json
import os
import sys
from decimal import ROUND_HALF_EVEN, ROUND_HALF_UP, Decimal, getcontext

getcontext().prec = 40

# Weights are typed by hand; 0.05 absorbs 33.3 + 33.3 + 33.4 style entries
# without hiding a real 95 or 105 total.
WEIGHT_TOLERANCE = Decimal("0.05")
# A final within half a point of a cut-off is where one rounding rule or one
# missing-score choice moves a letter, so it goes to a human.
BOUNDARY_MARGIN = Decimal("0.5")
DEFAULT_TOLERANCE = Decimal("0.05")
MISSING_TOKENS = {"", "na", "n/a", "-", "--", "missing", "none", "null"}
EXCUSED_TOKENS = {"ex", "excused"}
POLICIES = ("flag", "exclude", "zero")
SCHEME_KEYS = {"categories", "letters", "rounding", "expected_column"}
CATEGORY_KEYS = {"weight", "items", "drop_lowest", "method"}
METHODS = ("points", "mean_of_percents")
ROUNDING_MODES = {"half_up": ROUND_HALF_UP, "half_even": ROUND_HALF_EVEN}
MAX_DECIMALS = 4


class UsageError(Exception):
    """A problem with arguments or files, reported on stderr with exit 2."""


def _reject_constant(name):
    raise ValueError("non-finite number %s is not allowed" % name)


def _no_duplicate_keys(pairs):
    out = {}
    for key, value in pairs:
        if key in out:
            raise ValueError("duplicate key %r" % key)
        out[key] = value
    return out


def load_json(path):
    try:
        with open(path, encoding="utf-8-sig") as fh:
            return json.load(fh, parse_constant=_reject_constant, object_pairs_hook=_no_duplicate_keys)
    except OSError as exc:
        raise UsageError("cannot read %s: %s" % (path, exc.strerror or exc))
    except (ValueError, UnicodeDecodeError) as exc:
        raise UsageError("%s is not valid JSON: %s" % (path, exc))


def to_dec(value):
    """Decimal from a JSON number or CSV text; None when it is not a finite number."""
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        value = repr(value)
    try:
        number = Decimal(str(value).strip())
    except Exception:
        return None
    return number if number.is_finite() else None


def quant(value, decimals, mode=ROUND_HALF_UP):
    return value.quantize(Decimal(1).scaleb(-decimals), rounding=mode)


def num(value, places=4):
    """JSON-safe float rounded for display; None passes through."""
    if value is None:
        return None
    return float(quant(value, places))


def fmt(value):
    """Plain decimal text without exponent notation (10, not 1E+1)."""
    return format(value.normalize(), "f")


def problem(code, detail):
    return {"code": code, "detail": detail}


def validate_scheme(scheme, columns):
    """Return (problems, normalised) where normalised is None when invalid."""
    problems = []
    if not isinstance(scheme, dict):
        return [problem("scheme_not_object", "the scheme file must hold one JSON object")], None
    for key in sorted(set(scheme) - SCHEME_KEYS):
        extra = " Late-work penalties are not applied; enter scores after any penalty." if "late" in key.lower() else ""
        problems.append(problem("unsupported_key", "scheme key %r is not supported.%s" % (key, extra)))
    raw_cats = scheme.get("categories")
    cats = []
    if not isinstance(raw_cats, dict) or not raw_cats:
        problems.append(problem("no_categories", "scheme needs a non-empty \"categories\" object"))
        raw_cats = {}
    seen_items = {}
    total = Decimal(0)
    for name, spec in raw_cats.items():
        if not isinstance(spec, dict):
            problems.append(problem("category_not_object", "category %r must be an object" % name))
            continue
        for key in sorted(set(spec) - CATEGORY_KEYS):
            problems.append(problem("unsupported_key", "category %r has unsupported key %r" % (name, key)))
        weight = to_dec(spec.get("weight"))
        if weight is None or weight < 0:
            problems.append(problem("bad_weight", "category %r needs a numeric weight of 0 or more" % name))
            weight = Decimal(0)
        total += weight
        items_raw = spec.get("items")
        items = []
        if not isinstance(items_raw, dict) or not items_raw:
            problems.append(problem("empty_category", "category %r has no items; give an object of item column to maximum points" % name))
        else:
            for item, mx in items_raw.items():
                mxd = to_dec(mx)
                if mxd is None or mxd <= 0:
                    problems.append(problem("bad_max", "item %r in %r needs a maximum above 0" % (item, name)))
                    continue
                if item in seen_items:
                    problems.append(problem("item_in_two_categories", "item %r is listed in %r and %r" % (item, seen_items[item], name)))
                    continue
                seen_items[item] = name
                items.append((item, mxd))
                if columns is not None and item not in columns:
                    problems.append(problem("item_column_missing", "item %r (category %r) is not a column in the CSV" % (item, name)))
        drop = spec.get("drop_lowest", 0)
        if isinstance(drop, bool) or not isinstance(drop, int) or drop < 0:
            problems.append(problem("bad_drop_lowest", "drop_lowest in %r must be a whole number of 0 or more" % name))
            drop = 0
        elif items and drop >= len(items):
            problems.append(problem("drop_leaves_zero", "drop_lowest %d in %r would remove all %d items" % (drop, name, len(items))))
        method = spec.get("method", "points")
        if method not in METHODS:
            problems.append(problem("bad_method", "method in %r must be one of %s" % (name, ", ".join(METHODS))))
            method = "points"
        cats.append({"name": name, "weight": weight, "items": items, "drop": drop, "method": method})
    if cats and abs(total - 100) > WEIGHT_TOLERANCE:
        problems.append(problem("weights_not_100", "weights add up to %s, not 100" % fmt(total)))
    rounding = scheme.get("rounding", {})
    decimals, mode_name, per_cat = 1, "half_up", False
    if not isinstance(rounding, dict):
        problems.append(problem("bad_rounding", "rounding must be an object"))
    else:
        for key in sorted(set(rounding) - {"decimals", "mode", "per_category"}):
            problems.append(problem("unsupported_key", "rounding key %r is not supported" % key))
        decimals = rounding.get("decimals", 1)
        if isinstance(decimals, bool) or not isinstance(decimals, int) or not 0 <= decimals <= MAX_DECIMALS:
            problems.append(problem("bad_rounding", "rounding.decimals must be a whole number from 0 to %d" % MAX_DECIMALS))
            decimals = 1
        mode_name = rounding.get("mode", "half_up")
        if mode_name not in ROUNDING_MODES:
            problems.append(problem("bad_rounding", "rounding.mode must be one of %s" % ", ".join(ROUNDING_MODES)))
            mode_name = "half_up"
        per_cat = rounding.get("per_category", False)
        if not isinstance(per_cat, bool):
            problems.append(problem("bad_rounding", "rounding.per_category must be true or false"))
            per_cat = False
    letters = []
    raw_letters = scheme.get("letters")
    if raw_letters is not None:
        if not isinstance(raw_letters, list) or not raw_letters:
            problems.append(problem("bad_letters", "letters must be a non-empty list of {letter, min}"))
        else:
            for entry in raw_letters:
                low = to_dec(entry.get("min")) if isinstance(entry, dict) else None
                if low is None or not isinstance(entry.get("letter"), str):
                    problems.append(problem("bad_letters", "each letters entry needs a text \"letter\" and a numeric \"min\""))
                    continue
                letters.append((entry["letter"], low))
            mins = [m for _, m in letters]
            if len(set(mins)) != len(mins):
                problems.append(problem("bad_letters", "two letters share the same cut-off"))
            if letters and min(mins) > 0:
                problems.append(problem("bad_letters", "the lowest cut-off must be 0 or below so every final gets a letter"))
            letters.sort(key=lambda pair: pair[1], reverse=True)
    expected = scheme.get("expected_column")
    if expected is not None and not isinstance(expected, str):
        problems.append(problem("bad_expected_column", "expected_column must be a column name"))
        expected = None
    if problems:
        return problems, None
    return [], {"cats": cats, "decimals": decimals, "mode": mode_name, "per_category": per_cat,
                "letters": letters, "expected": expected}


def parse_cell(raw, delimiter):
    """Classify a CSV cell as ("num", value), ("missing", None), ("excused", None) or ("bad", None)."""
    text = (raw or "").strip()
    low = text.lower()
    if low in MISSING_TOKENS:
        return ("missing", None)
    if low in EXCUSED_TOKENS:
        return ("excused", None)
    if delimiter != "," and "," in text:
        text = text.replace(",", ".")
    value = to_dec(text)
    return ("num", value) if value is not None else ("bad", None)


def load_scores(path, delimiter):
    try:
        with open(path, encoding="utf-8-sig", newline="") as fh:
            rows = list(csv.reader(fh, delimiter=delimiter))
    except OSError as exc:
        raise UsageError("cannot read %s: %s" % (path, exc.strerror or exc))
    except (UnicodeDecodeError, csv.Error) as exc:
        raise UsageError("%s is not readable as UTF-8 CSV: %s" % (path, exc))
    rows = [r for r in rows if any(c.strip() for c in r)]
    if len(rows) < 2:
        raise UsageError("%s needs a header row and at least one student row" % path)
    header = [h.strip() for h in rows[0]]
    if len(set(header)) != len(header):
        raise UsageError("%s has a repeated column name in the header row" % path)
    return header, rows[1:]


def category_result(cat, states, policy, forced):
    """Average of one category for one student under the missing-score policy."""
    counted, missing = [], []
    for idx, (item, mx) in enumerate(cat["items"]):
        if forced is not None and item == forced[0]:
            counted.append((idx, item, forced[1], mx))
            continue
        kind, val = states[item]
        if kind == "num":
            counted.append((idx, item, val, mx))
        elif kind == "missing":
            missing.append(item)
            if policy == "zero":
                counted.append((idx, item, Decimal(0), mx))
    dropped, reduced = [], False
    if cat["drop"] and counted:
        allowed = min(cat["drop"], len(counted) - 1)
        reduced = allowed < cat["drop"]
        order = sorted(counted, key=lambda c: (c[2] / c[3], c[0]))
        dropped = [c[1] for c in order[:allowed]]
        counted = [c for c in counted if c[1] not in dropped]
    if not counted:
        pct = None
    elif cat["method"] == "points":
        pct = sum(c[2] for c in counted) / sum(c[3] for c in counted) * 100
    else:
        pct = sum(c[2] / c[3] for c in counted) / len(counted) * 100
    return {"pct": pct, "counted": len(counted), "dropped": dropped, "missing": missing, "reduced": reduced}


def final_for(norm, states, policy, forced=None, per_category=None):
    """Weighted final before rounding. Absent categories are left out and the rest re-weighted."""
    if per_category is None:
        per_category = norm["per_category"]
    results, weighted, weight_sum, absent = {}, Decimal(0), Decimal(0), []
    for cat in norm["cats"]:
        res = category_result(cat, states, policy, forced)
        results[cat["name"]] = res
        pct = res["pct"]
        if pct is None:
            absent.append(cat["name"])
            continue
        if per_category:
            pct = quant(pct, norm["decimals"], ROUND_HALF_UP if norm["mode"] == "half_up" else ROUND_HALF_EVEN)
        weighted += cat["weight"] * pct
        weight_sum += cat["weight"]
    final = weighted / weight_sum if weight_sum > 0 else None
    return {"final": final, "cats": results, "absent": absent}


def rounded(norm, value):
    return None if value is None else quant(value, norm["decimals"], ROUNDING_MODES[norm["mode"]])


def letter_for(letters, value):
    if value is None or not letters:
        return None
    for letter, low in letters:
        if value >= low:
            return letter
    return None


def nearest_cutoff(letters, value):
    cuts = [(letter, low) for letter, low in letters if low > 0]
    if not cuts or value is None:
        return None
    return min(cuts, key=lambda pair: abs(value - pair[1]))


def what_if_needed(norm, states, policy, item, target):
    """Smallest score on `item`, in steps of 0.01, whose recorded final reaches target."""
    max_pts = next(mx for cat in norm["cats"] for it, mx in cat["items"] if it == item)
    top = int((max_pts * 100).to_integral_value(rounding="ROUND_CEILING"))

    def reaches(step):
        value = Decimal(step) / 100
        res = final_for(norm, states, policy, forced=(item, min(value, max_pts)))
        return rounded(norm, res["final"]) >= target

    if reaches(0):
        return Decimal(0), True, "already secured with a score of 0 on this item"
    if not reaches(top):
        return None, False, "target not reachable even with full marks on this item"
    lo, hi = 0, top
    while hi - lo > 1:
        mid = (lo + hi) // 2
        if reaches(mid):
            hi = mid
        else:
            lo = mid
    return min(Decimal(hi) / 100, max_pts), True, None


def build_report(args):
    delimiter = args.delimiter
    header, rows = load_scores(args.scores, delimiter)
    scheme = load_json(args.scheme)
    problems, norm = validate_scheme(scheme, set(header))
    if args.id_column not in header:
        raise UsageError("id column %r not found in the CSV header; use --id-column" % args.id_column)
    report = {"tool": "gradebook_check", "scheme_ok": norm is not None, "scheme_problems": problems,
              "policy": args.missing, "rounding": None, "students_total": 0, "duplicate_ids": [],
              "blank_id_rows": [], "unmapped_columns": [], "expected_compared": 0, "students": [],
              "boundary_cases": [], "mismatches_with_expected": [], "what_if": None, "flag_counts": {}}
    if norm is None:
        return report
    report["rounding"] = {"decimals": norm["decimals"], "mode": norm["mode"], "per_category": norm["per_category"]}
    item_names = {it for cat in norm["cats"] for it, _ in cat["items"]}
    expected_col = args.expected_column or norm["expected"]
    if expected_col and expected_col not in header:
        raise UsageError("expected column %r not found in the CSV header" % expected_col)
    report["unmapped_columns"] = [h for h in header if h not in item_names and h != args.id_column and h != expected_col]
    if args.what_if and args.what_if not in item_names:
        raise UsageError("--what-if item %r is not an item in the scheme" % args.what_if)
    col = {h: i for i, h in enumerate(header)}
    seen, dup_rows = {}, {}
    what_if_rows = []
    flag_counts = {}
    for line_no, row in enumerate(rows, start=2):
        cells = row + [""] * (len(header) - len(row))
        sid = cells[col[args.id_column]].strip()
        if not sid:
            report["blank_id_rows"].append(line_no)
            continue
        if sid in seen:
            dup_rows.setdefault(sid, [seen[sid]]).append(line_no)
            continue
        seen[sid] = line_no
        states, flags = {}, []
        for cat in norm["cats"]:
            for item, mx in cat["items"]:
                kind, val = parse_cell(cells[col[item]], delimiter)
                if kind == "bad":
                    flags.append(problem("non_numeric_score", "%s: cell is not a number; treated as missing" % item))
                    kind = "missing"
                if kind == "num":
                    if val < 0:
                        flags.append(problem("negative_score", "%s: %s is below 0; used as entered" % (item, fmt(val))))
                    elif val > mx:
                        flags.append(problem("score_above_max", "%s: %s exceeds the maximum %s; used as entered" % (item, fmt(val), fmt(mx))))
                states[item] = (kind, val)
        main = final_for(norm, states, args.missing)
        any_missing = any(res["missing"] for res in main["cats"].values())
        for cat in norm["cats"]:
            res = main["cats"][cat["name"]]
            for item in res["missing"]:
                note = {"zero": "counted as 0", "exclude": "left out of the average", "flag": "left out; result is provisional"}[args.missing]
                flags.append(problem("missing_score", "%s: no score, %s" % (item, note)))
            if res["reduced"]:
                flags.append(problem("drop_lowest_reduced", "%s: only %d scored item(s), so fewer than %d were dropped" % (cat["name"], res["counted"], cat["drop"])))
        for name in main["absent"]:
            flags.append(problem("category_absent", "%s has no scores; the other categories are re-weighted" % name))
        final_unr = main["final"]
        final_r = rounded(norm, final_unr)
        letter = letter_for(norm["letters"], final_r)
        if final_unr is not None and norm["letters"]:
            if letter_for(norm["letters"], final_unr) != letter:
                flags.append(problem("rounding_changes_letter", "unrounded %s gives %s, rounded %s gives %s" % (
                    num(final_unr), letter_for(norm["letters"], final_unr), num(final_r, norm["decimals"]), letter)))
            other = rounded(norm, final_for(norm, states, args.missing, per_category=not norm["per_category"])["final"])
            if letter_for(norm["letters"], other) != letter:
                flags.append(problem("rounding_order_changes_letter", "rounding %s gives %s, the other order gives %s" % (
                    "each category first" if norm["per_category"] else "only at the end", letter, letter_for(norm["letters"], other))))
        effect = None
        if any_missing:
            effect = {}
            for pol in ("exclude", "zero"):
                f = rounded(norm, final_for(norm, states, pol)["final"])
                effect[pol] = {"final": num(f, norm["decimals"]), "letter": letter_for(norm["letters"], f)}
            if effect["exclude"]["final"] is not None and effect["zero"]["final"] is not None:
                effect["difference"] = round(effect["exclude"]["final"] - effect["zero"]["final"], norm["decimals"] + 2)
            else:
                effect["difference"] = None
            if effect["exclude"]["letter"] != effect["zero"]["letter"]:
                flags.append(problem("letter_depends_on_missing_policy", "%s if excluded, %s if counted as 0" % (effect["exclude"]["letter"], effect["zero"]["letter"])))
        if final_unr is not None and norm["letters"]:
            near = nearest_cutoff(norm["letters"], final_unr)
            if near and abs(final_unr - near[1]) <= BOUNDARY_MARGIN:
                report["boundary_cases"].append({"student_id": sid, "final": num(final_r, norm["decimals"]), "final_unrounded": num(final_unr),
                                                 "cutoff_letter": near[0], "cutoff": num(near[1]), "distance": num(final_unr - near[1])})
        if expected_col:
            exp_kind, exp_val = parse_cell(cells[col[expected_col]], delimiter)
            if exp_kind == "num" and final_r is not None:
                report["expected_compared"] += 1
                diff = exp_val - final_r
                if abs(diff) > args.tolerance:
                    explained = None
                    if effect:
                        for pol in ("zero", "exclude"):
                            alt = effect[pol]["final"]
                            if alt is not None and abs(exp_val - Decimal(str(alt))) <= args.tolerance:
                                explained = pol
                                break
                    report["mismatches_with_expected"].append({"student_id": sid, "expected": num(exp_val), "computed": num(final_r, norm["decimals"]),
                                                               "difference": num(diff), "explained_by_missing_policy": explained})
            elif exp_kind == "bad":
                flags.append(problem("expected_not_numeric", "%s: cell is not a number; not compared" % expected_col))
        if args.what_if:
            kind = states[args.what_if][0]
            if kind == "missing":
                needed, feasible, note = what_if_needed(norm, states, args.missing, args.what_if, args.target)
                max_pts = next(mx for cat in norm["cats"] for it, mx in cat["items"] if it == args.what_if)
                what_if_rows.append({"student_id": sid, "feasible": feasible, "needed_score": num(needed, 2),
                                     "needed_percent_of_max": None if needed is None else num(needed / max_pts * 100, 2), "note": note})
        for flag in flags:
            flag_counts[flag["code"]] = flag_counts.get(flag["code"], 0) + 1
        by_cat = {}
        for cat in norm["cats"]:
            res = main["cats"][cat["name"]]
            by_cat[cat["name"]] = {"percent": num(res["pct"]), "counted": res["counted"], "dropped": res["dropped"], "missing": res["missing"]}
        report["students"].append({"student_id": sid, "final": num(final_r, norm["decimals"]), "final_unrounded": num(final_unr), "letter": letter,
                                   "provisional": bool(args.missing == "flag" and any_missing), "by_category": by_cat,
                                   "policy_effect": effect, "flags": flags})
    report["duplicate_ids"] = [{"student_id": k, "rows": v} for k, v in dup_rows.items()]
    for entry in report["duplicate_ids"]:
        flag_counts["duplicate_id"] = flag_counts.get("duplicate_id", 0) + 1
    report["students_total"] = len(report["students"])
    if args.what_if:
        cat_name = next(cat["name"] for cat in norm["cats"] if any(it == args.what_if for it, _ in cat["items"]))
        report["what_if"] = {"item": args.what_if, "category": cat_name, "target": num(args.target), "students": what_if_rows}
    report["flag_counts"] = dict(sorted(flag_counts.items()))
    return report


def check_out_path(out, scores, scheme, force):
    target = os.path.realpath(out)
    for src in (scores, scheme):
        if target == os.path.realpath(src) or (os.path.exists(out) and os.path.exists(src) and os.path.samefile(out, src)):
            raise UsageError("refusing to write the report over an input file (%s), even with --force" % src)
    if os.path.exists(out) and not force:
        raise UsageError("%s already exists; pass --force to replace it" % out)


def parse_args(argv):
    parser = argparse.ArgumentParser(description="Recompute weighted final grades from a CSV gradebook and a scheme.")
    parser.add_argument("scores")
    parser.add_argument("scheme")
    parser.add_argument("--missing", choices=POLICIES, default="flag")
    parser.add_argument("--id-column", default="student_id")
    parser.add_argument("--expected-column")
    parser.add_argument("--tolerance", default=str(DEFAULT_TOLERANCE))
    parser.add_argument("--what-if")
    parser.add_argument("--target")
    parser.add_argument("--delimiter", default=",")
    parser.add_argument("--out")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args(argv)
    tol = to_dec(args.tolerance)
    if tol is None or tol < 0:
        raise UsageError("--tolerance must be a number of 0 or more")
    args.tolerance = tol
    if len(args.delimiter) != 1:
        raise UsageError("--delimiter must be a single character")
    if bool(args.what_if) != bool(args.target):
        raise UsageError("--what-if and --target must be given together")
    if args.target:
        args.target = to_dec(args.target)
        if args.target is None:
            raise UsageError("--target must be a number")
    return args


def main(argv=None):
    try:
        for stream in (sys.stdout, sys.stderr):
            if hasattr(stream, "reconfigure"):
                stream.reconfigure(encoding="utf-8")
        args = parse_args(sys.argv[1:] if argv is None else argv)
        if args.out:
            check_out_path(args.out, args.scores, args.scheme, args.force)
        report = build_report(args)
        text = json.dumps(report, indent=2, allow_nan=False, ensure_ascii=False)
        if args.out:
            with open(args.out, "w", encoding="utf-8") as fh:
                fh.write(text + "\n")
            print("wrote %s" % args.out, file=sys.stderr)
        else:
            print(text)
        return 0 if report["scheme_ok"] and not report["mismatches_with_expected"] else 1
    except UsageError as exc:
        print("error: %s" % exc, file=sys.stderr)
        return 2
    except SystemExit as exc:
        return 2 if exc.code else 0


if __name__ == "__main__":
    sys.exit(main())
