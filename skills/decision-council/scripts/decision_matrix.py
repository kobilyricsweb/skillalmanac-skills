#!/usr/bin/env python3
"""Weighted decision matrix: scores, sensitivity and tie report, as strict JSON.

Usage:
    python decision_matrix.py MATRIX.json|MATRIX.csv [--near-tie PCT] [--scale MIN,MAX]

Reads one file (JSON or CSV, chosen by extension; see the formats below) and
prints one JSON document on stdout. Writes nothing. No network.

JSON format:
    {"scale": {"min": 1, "max": 5},                      (optional, default 1..5)
     "criteria": [{"name": "Cost", "weight": 4, "direction": "cost"}, ...],
     "options":  [{"name": "A", "scores": {"Cost": 2, ...}}, ...]}
    direction is "benefit" (higher score is better, default) or "cost"
    (higher score is worse; the script flips it on the scale before weighting).

CSV format (UTF-8, comma separated):
    option,Cost,Speed          header: first cell ignored, then criterion names
    weight,4,3                 required row
    direction,cost,benefit     optional row
    scale,1,5                  optional row
    A,2,4                      one row per option
    "weight", "direction" and "scale" are reserved and cannot be option names.

Output fields: ranking (rank, score, score_pct, contributions), winner, margin,
tie_report (exact_ties, near_ties, resolved_by), sensitivity (per criterion: the
weight at which another option overtakes the winner), dominated, warnings.

Exit codes: 0 computed with a unique winner; 1 computed but first place is tied;
2 input error (JSON {"ok": false, "error": ...} is printed). Fix the input; do
not edit this script to change a result.
"""
import argparse
import csv
import io
import json
import math
import os
import sys

EPS = 1e-9               # float noise level; scores closer than this are an exact tie
DEFAULT_SCALE = (1.0, 5.0)   # a 1-5 scale is what the skill tells users to score on
NEAR_TIE_PCT = 2.0       # gap under 2% of the scale range is too small to act on
FRAGILE_SHIFT = 0.10     # a 10-point shift in one normalised weight flips the winner: fragile
MODERATE_SHIFT = 0.20    # a 20-point shift: moderate; larger or no flip: robust
HEAVY_WEIGHT = 0.5       # one criterion carrying over half the weight is worth a warning
BENEFIT = {"benefit", "higher", "higher_better", "max", "up"}
COST = {"cost", "lower", "lower_better", "min", "down"}
RESERVED_ROWS = {"weight", "weights", "direction", "directions", "scale"}


class InputError(Exception):
    pass


def num(value, where):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise InputError(f"{where} must be a number, got {value!r}")
    if not math.isfinite(value):
        raise InputError(f"{where} must be finite")
    return float(value)


def parse_cell(text, where):
    text = (text or "").strip()
    if text == "":
        raise InputError(f"{where} is empty; every cell needs a number")
    try:
        value = float(text)
    except ValueError:
        raise InputError(f"{where} is not a number: {text!r}")
    return num(value, where)


def direction_of(value, where):
    key = str(value).strip().lower().replace(" ", "_").replace("-", "_")
    if key in BENEFIT:
        return "benefit"
    if key in COST:
        return "cost"
    raise InputError(f"{where}: direction must be 'benefit' or 'cost', got {value!r}")


def load_json(text):
    try:
        data = json.loads(text)
    except ValueError as exc:
        raise InputError(f"not valid JSON: {exc}")
    if not isinstance(data, dict):
        raise InputError("top level must be an object with 'criteria' and 'options'")
    crits = data.get("criteria")
    opts = data.get("options")
    if not isinstance(crits, list) or not crits:
        raise InputError("'criteria' must be a non-empty list")
    if not isinstance(opts, list) or not opts:
        raise InputError("'options' must be a non-empty list")
    criteria = []
    for i, c in enumerate(crits):
        if not isinstance(c, dict) or not isinstance(c.get("name"), str) or not c["name"].strip():
            raise InputError(f"criteria[{i}] needs a non-empty string 'name'")
        name = c["name"].strip()
        criteria.append({
            "name": name,
            "weight": num(c.get("weight"), f"weight of '{name}'"),
            "direction": direction_of(c.get("direction", "benefit"), f"criterion '{name}'"),
        })
    options = []
    for i, o in enumerate(opts):
        if not isinstance(o, dict) or not isinstance(o.get("name"), str) or not o["name"].strip():
            raise InputError(f"options[{i}] needs a non-empty string 'name'")
        name = o["name"].strip()
        sc = o.get("scores")
        if not isinstance(sc, dict):
            raise InputError(f"option '{name}' needs a 'scores' object")
        options.append({"name": name, "scores": {k: num(v, f"score of '{name}' on '{k}'") for k, v in sc.items()}})
    scale = None
    if "scale" in data:
        s = data["scale"]
        if not isinstance(s, dict):
            raise InputError("'scale' must be an object with 'min' and 'max'")
        scale = (num(s.get("min"), "scale.min"), num(s.get("max"), "scale.max"))
    return {"criteria": criteria, "options": options, "scale": scale}


def load_csv(text):
    rows = [r for r in csv.reader(io.StringIO(text)) if any(c.strip() for c in r)]
    if len(rows) < 3:
        raise InputError("CSV needs a header row, a 'weight' row and at least one option row")
    names = [c.strip() for c in rows[0][1:]]
    if not names or any(not n for n in names):
        raise InputError("header row must list criterion names after the first cell")
    n = len(names)
    weights = directions = scale = None
    options = []
    for r in rows[1:]:
        label = r[0].strip()
        cells = r[1:]
        low = label.lower()
        if low in ("weight", "weights", "direction", "directions"):
            if len(cells) != n:
                raise InputError(f"row '{label}' has {len(cells)} values, expected {n}")
            if low.startswith("weight"):
                weights = [parse_cell(c, f"weight of '{names[i]}'") for i, c in enumerate(cells)]
            else:
                directions = [direction_of(c, f"criterion '{names[i]}'") for i, c in enumerate(cells)]
        elif low == "scale":
            if len(cells) < 2:
                raise InputError("scale row needs min and max: scale,1,5")
            scale = (parse_cell(cells[0], "scale min"), parse_cell(cells[1], "scale max"))
        else:
            if not label:
                raise InputError("an option row has an empty name")
            if len(cells) != n:
                raise InputError(f"option '{label}' has {len(cells)} scores, expected {n}")
            options.append({"name": label, "scores": {names[i]: parse_cell(c, f"score of '{label}' on '{names[i]}'")
                                                      for i, c in enumerate(cells)}})
    if weights is None:
        raise InputError("CSV has no 'weight' row")
    if not options:
        raise InputError("CSV has no option rows")
    criteria = [{"name": names[i], "weight": weights[i],
                 "direction": directions[i] if directions else "benefit"} for i in range(n)]
    return {"criteria": criteria, "options": options, "scale": scale}


def validate(model, scale_override):
    crit = model["criteria"]
    opts = model["options"]
    names = [c["name"] for c in crit]
    if len(set(names)) != len(names):
        raise InputError("criterion names must be unique")
    onames = [o["name"] for o in opts]
    if len(set(onames)) != len(onames):
        raise InputError("option names must be unique")
    if len(opts) < 2:
        raise InputError("need at least 2 options; include 'do nothing' as one if it is a real choice")
    for c in crit:
        if c["weight"] < 0:
            raise InputError(f"weight of '{c['name']}' is negative; use the cost direction instead")
    if sum(c["weight"] for c in crit) <= 0:
        raise InputError("weights sum to zero; give at least one criterion a positive weight")
    lo, hi = scale_override or model["scale"] or DEFAULT_SCALE
    if not lo < hi:
        raise InputError("scale min must be below scale max")
    for o in opts:
        extra = [k for k in o["scores"] if k not in names]
        if extra:
            raise InputError(f"option '{o['name']}' scores unknown criteria: {', '.join(extra)}")
        for c in crit:
            if c["name"] not in o["scores"]:
                raise InputError(f"option '{o['name']}' has no score for '{c['name']}'")
            v = o["scores"][c["name"]]
            if not lo <= v <= hi:
                raise InputError(f"score of '{o['name']}' on '{c['name']}' is {v:g}, outside the scale "
                                 f"{lo:g}..{hi:g}; fix the score or set the scale")
    return lo, hi


def rnd(x):
    return None if x is None else round(x, 6) + 0.0


def standings(weights, adj):
    """Return (scores, order, ranks) for normalised weights and adjusted scores."""
    scores = [sum(w * a for w, a in zip(weights, row)) for row in adj]
    order = sorted(range(len(scores)), key=lambda i: (-round(scores[i], 9), i))
    ranks = {}
    for pos, i in enumerate(order):
        if pos > 0 and abs(scores[i] - scores[order[pos - 1]]) < EPS:
            ranks[i] = ranks[order[pos - 1]]
        else:
            ranks[i] = pos + 1
    return scores, order, ranks


def flip_point(weights, adj, scores, lead, c):
    """Nearest weight of criterion c, others rescaled in proportion, at which an
    option overtakes `lead`. Returns (x, challenger_index) or None."""
    wc = weights[c]
    if wc >= 1 - EPS:
        return None
    best = None
    for j in range(len(adj)):
        if j == lead:
            continue
        a_l, a_j = adj[lead][c], adj[j][c]
        b_l = (scores[lead] - wc * a_l) / (1 - wc)
        b_j = (scores[j] - wc * a_j) / (1 - wc)
        d = (a_l - a_j) - (b_l - b_j)
        if abs(d) < EPS:
            continue
        x = (b_j - b_l) / d
        if x < -EPS or x > 1 + EPS or abs(x - wc) < EPS:
            continue
        x = min(1.0, max(0.0, x))
        if best is None or abs(x - wc) < abs(best[0] - wc):
            best = (x, j)
    return best


def analyse(model, scale_override, near_pct):
    lo, hi = validate(model, scale_override)
    crit, opts = model["criteria"], model["options"]
    cn = [c["name"] for c in crit]
    on = [o["name"] for o in opts]
    raw = [c["weight"] for c in crit]
    total = sum(raw)
    weights = [r / total for r in raw]
    adj = [[(o["scores"][c["name"]] if c["direction"] == "benefit" else lo + hi - o["scores"][c["name"]])
            for c in crit] for o in opts]
    scores, order, ranks = standings(weights, adj)
    span = hi - lo
    warnings = []

    ranking = []
    for i in order:
        ranking.append({
            "rank": ranks[i], "option": on[i], "score": rnd(scores[i]),
            "score_pct": rnd((scores[i] - lo) / span * 100),
            "contributions": {cn[k]: rnd(weights[k] * adj[i][k]) for k in range(len(cn))},
        })

    top_tied = sum(1 for i in order if ranks[i] == 1) > 1
    lead = order[0]
    runner = order[1]
    gap = scores[lead] - scores[runner]
    winner = {"option": None if top_tied else on[lead], "unique": not top_tied,
              "tied_for_first": [on[i] for i in order if ranks[i] == 1] if top_tied else []}
    margin = {"leader_minus_runner_up": rnd(gap), "pct_of_scale": rnd(gap / span * 100)}

    # tie report
    exact = []
    for r in sorted(set(ranks.values())):
        group = [i for i in order if ranks[i] == r]
        if len(group) > 1:
            by = None
            for c in sorted(range(len(cn)), key=lambda k: (-raw[k], k)):
                vals = [adj[i][c] for i in group]
                if max(vals) - min(vals) > EPS:
                    by = {"criterion": cn[c], "favours": [on[i] for i in group if adj[i][c] >= max(vals) - EPS]}
                    break
            exact.append({"rank": r, "options": [on[i] for i in group], "resolved_by": by})
    near = []
    for a, b in zip(order, order[1:]):
        g = scores[a] - scores[b]
        if g > EPS and g / span * 100 <= near_pct:
            near.append({"options": [on[a], on[b]], "gap": rnd(g), "gap_pct_of_scale": rnd(g / span * 100)})
    tie_report = {"exact_ties": exact, "near_ties": near, "near_tie_threshold_pct": near_pct}

    # sensitivity
    per = []
    smallest = None
    if not top_tied:
        for c in range(len(cn)):
            fp = flip_point(weights, adj, scores, lead, c)
            entry = {"criterion": cn[c], "weight": rnd(weights[c]), "weight_raw": rnd(raw[c])}
            if fp is None:
                entry.update({"flips": False, "flip_weight": None, "flip_weight_raw": None, "shift": None,
                              "direction": None, "overtaken_by": None})
            else:
                x, j = fp
                others = total - raw[c]
                flip_raw = None if x >= 1 - EPS else x * others / (1 - x)
                entry.update({"flips": True, "flip_weight": rnd(x), "flip_weight_raw": rnd(flip_raw),
                              "shift": rnd(abs(x - weights[c])),
                              "direction": "increase" if x > weights[c] else "decrease", "overtaken_by": on[j]})
                if smallest is None or abs(x - weights[c]) < smallest["shift"] - EPS:
                    smallest = {"criterion": cn[c], "shift": abs(x - weights[c]), "flip_weight": x,
                                "flip_weight_raw": flip_raw, "direction": entry["direction"], "overtaken_by": on[j]}
            per.append(entry)
    if top_tied:
        label = "tied"
    elif smallest is None:
        label = "robust"
    elif smallest["shift"] < FRAGILE_SHIFT:
        label = "fragile"
    elif smallest["shift"] < MODERATE_SHIFT:
        label = "moderate"
    else:
        label = "robust"
    if smallest:
        smallest = {k: (rnd(v) if isinstance(v, float) or v is None else v) for k, v in smallest.items()}
    eq_scores, eq_order, eq_ranks = standings([1 / len(cn)] * len(cn), adj)
    eq_leaders = [on[i] for i in eq_order if eq_ranks[i] == 1]
    sens = {"label": label, "top_tied": top_tied, "per_criterion": per, "smallest_flip": smallest,
            "equal_weights_leaders": eq_leaders,
            "equal_weights_same_winner": (not top_tied) and eq_leaders == [on[lead]]}

    # dominance
    dominated = []
    for i in range(len(on)):
        by = [on[j] for j in range(len(on)) if j != i
              and all(adj[j][k] >= adj[i][k] - EPS for k in range(len(cn)))
              and any(adj[j][k] > adj[i][k] + EPS for k in range(len(cn)))]
        if by:
            dominated.append({"option": on[i], "dominated_by": by})

    # warnings
    for k in range(len(cn)):
        col = [adj[i][k] for i in range(len(on))]
        if max(col) - min(col) < EPS:
            warnings.append(f"criterion '{cn[k]}' scores every option the same, so it cannot change the result")
        if raw[k] == 0:
            warnings.append(f"criterion '{cn[k]}' has weight 0 and is ignored")
        if weights[k] > HEAVY_WEIGHT:
            warnings.append(f"criterion '{cn[k]}' carries {weights[k] * 100:.0f}% of the weight; "
                            "the result mostly restates that one criterion")
    if len(set(raw)) == 1 and len(raw) > 1:
        warnings.append("all weights are equal; check that this reflects the user's priorities and is not a default")

    out = {
        "ok": True, "command": "score",
        "scale": {"min": lo, "max": hi},
        "criteria": [{"name": cn[k], "weight_raw": rnd(raw[k]), "weight": rnd(weights[k]),
                      "direction": crit[k]["direction"]} for k in range(len(cn))],
        "ranking": ranking, "winner": winner, "margin": margin,
        "tie_report": tie_report, "sensitivity": sens,
        "dominated": dominated, "warnings": warnings,
    }
    return out, (1 if top_tied else 0)


def emit(obj):
    text = json.dumps(obj, indent=2, allow_nan=False, ensure_ascii=True)
    sys.stdout.write(text + "\n")


def main(argv=None):
    ap = argparse.ArgumentParser(description="Weighted decision matrix with sensitivity and tie report.")
    ap.add_argument("matrix", help="path to a .json or .csv matrix")
    ap.add_argument("--near-tie", type=float, default=NEAR_TIE_PCT,
                    help="gap, in percent of the scale range, below which two options count as a near tie (default 2)")
    ap.add_argument("--scale", default=None, help="override the scale as MIN,MAX (default: file value, else 1,5)")
    try:
        args = ap.parse_args(argv)
    except SystemExit as exc:
        return 2 if exc.code else 0
    try:
        override = None
        if args.scale:
            parts = args.scale.split(",")
            if len(parts) != 2:
                raise InputError("--scale must look like 1,5")
            override = (parse_cell(parts[0], "--scale min"), parse_cell(parts[1], "--scale max"))
        if not (args.near_tie >= 0 and math.isfinite(args.near_tie)):
            raise InputError("--near-tie must be zero or positive")
        if not os.path.isfile(args.matrix):
            raise InputError(f"file not found: {args.matrix}")
        with open(args.matrix, encoding="utf-8-sig") as fh:
            text = fh.read()
        if not text.strip():
            raise InputError("file is empty")
        ext = os.path.splitext(args.matrix)[1].lower()
        if ext == ".json":
            model = load_json(text)
        elif ext == ".csv":
            model = load_csv(text)
        else:
            raise InputError("use a .json or .csv file")
        out, code = analyse(model, override, args.near_tie)
        emit(out)
        return code
    except InputError as exc:
        emit({"ok": False, "command": "score", "error": str(exc)})
        return 2
    except UnicodeDecodeError:
        emit({"ok": False, "command": "score", "error": "file is not valid UTF-8 text"})
        return 2


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
