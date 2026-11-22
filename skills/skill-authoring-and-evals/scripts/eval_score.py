#!/usr/bin/env python3
"""Score the two kinds of skill evals from saved results. Writes nothing.

    python eval_score.py triggers <trigger_queries.json> <trigger_results.json> [--json]
    python eval_score.py tasks <evals.json> <task_id> <output_dir> [<baseline_dir>] [--json]

triggers: trigger_queries.json is a list of {"query": str, "should_trigger": bool}.
  trigger_results.json is a list of {"query": str, "loaded": [bool, ...]}, one bool
  per fresh-session run. The script reports the trigger rate on should-trigger
  queries, the false-trigger rate on near-misses, the same numbers on a fixed 40%
  held-out slice, and names every query that missed.

tasks: evals.json holds {"evals": [{"id": str, "checks": [...]}]}. Each check is an
  object with "type" and "path" (relative to the output folder, glob allowed):
    file_exists, file_contains (+ "pattern"), file_not_contains (+ "pattern"),
    max_lines (+ "max"), frontmatter_key (+ "key").
  A missing file fails every check, so no check can pass on an empty folder. With a baseline folder the script also lists which checks
  separate the two runs; checks that pass in both runs do not measure the skill.

Exit codes: 0 = pass bar met, 1 = not met, 2 = usage error or unreadable input.
Python 3.9+, standard library only, no network.
"""
import glob
import hashlib
import json
import os
import re
import sys

# Pass bars from the house standard: trigger at least 90% on positives, at most 10% on near-misses.
MIN_TRIGGER_RATE = 0.90
MAX_FALSE_TRIGGER_RATE = 0.10
# Fewer runs per query than this hides flaky routing.
MIN_RUNS_PER_QUERY = 3
# Fewer queries than this cannot show a 90% / 10% difference.
MIN_QUERIES = 20
# Share of queries (by hash of the text) used for tuning; the rest is held out and reported alone.
TRAIN_BUCKETS = 3
TOTAL_BUCKETS = 5


class InputError(Exception):
    pass


def load_json(path):
    try:
        with open(path, encoding="utf-8-sig") as fh:
            return json.load(fh)
    except FileNotFoundError:
        raise InputError("file not found: %s" % path)
    except (ValueError, UnicodeDecodeError) as e:
        raise InputError("cannot read %s as JSON: %s" % (path, e))


def is_held_out(query):
    digest = hashlib.sha1(query.encode("utf-8")).hexdigest()
    return int(digest, 16) % TOTAL_BUCKETS >= TRAIN_BUCKETS


def rates(rows):
    pos = [r for r in rows if r["should"]]
    neg = [r for r in rows if not r["should"]]
    pos_runs = sum(len(r["loaded"]) for r in pos)
    neg_runs = sum(len(r["loaded"]) for r in neg)
    hit = sum(sum(r["loaded"]) for r in pos)
    false = sum(sum(r["loaded"]) for r in neg)
    return {
        "positives": len(pos), "negatives": len(neg),
        "trigger_rate": (hit / pos_runs) if pos_runs else None,
        "false_trigger_rate": (false / neg_runs) if neg_runs else None,
    }


def fmt(x):
    return "n/a" if x is None else "%.0f%%" % (100 * x)


def score_triggers(queries_path, results_path):
    queries = load_json(queries_path)
    results = load_json(results_path)
    if not isinstance(queries, list) or not isinstance(results, list):
        raise InputError("both files must hold a JSON list")
    by_query = {}
    for item in results:
        if not isinstance(item, dict) or "query" not in item or not isinstance(item.get("loaded"), list):
            raise InputError("each result needs 'query' and a 'loaded' list of booleans")
        by_query[item["query"]] = [bool(x) for x in item["loaded"]]
    rows, notes = [], []
    for q in queries:
        text = q.get("query")
        if text not in by_query or not by_query[text]:
            notes.append("ERROR  no run recorded for: %s" % text)
            continue
        rows.append({"query": text, "should": bool(q.get("should_trigger")),
                     "loaded": by_query[text], "held_out": is_held_out(text)})
        if len(by_query[text]) < MIN_RUNS_PER_QUERY:
            notes.append("WARN   only %d run(s), need %d: %s" % (len(by_query[text]), MIN_RUNS_PER_QUERY, text))
    if len(queries) < MIN_QUERIES:
        notes.append("WARN   %d queries; the standard asks for at least %d (half near-misses)" % (len(queries), MIN_QUERIES))
    n_pos = sum(1 for q in queries if q.get("should_trigger"))
    if queries and (n_pos == 0 or n_pos == len(queries)):
        notes.append("WARN   queries are all one kind; a trigger test needs both should-trigger and near-miss queries")
    missed = []
    for r in rows:
        share = sum(r["loaded"]) / len(r["loaded"])
        if (r["should"] and share < MIN_TRIGGER_RATE) or (not r["should"] and share > MAX_FALSE_TRIGGER_RATE):
            kind = "MISSED   " if r["should"] else "FALSE-HIT"
            missed.append("%s %d/%d loaded: %s" % (kind, sum(r["loaded"]), len(r["loaded"]), r["query"]))
    overall = rates(rows)
    held = rates([r for r in rows if r["held_out"]])

    def meets(x):
        return (x["trigger_rate"] is None or x["trigger_rate"] >= MIN_TRIGGER_RATE) and \
               (x["false_trigger_rate"] is None or x["false_trigger_rate"] <= MAX_FALSE_TRIGGER_RATE)

    ok = bool(rows) and meets(overall) and meets(held) and not any(n.startswith("ERROR") for n in notes)
    return {"overall": overall, "held_out": held, "notes": notes, "misses": missed, "pass": ok}


def read_file(path):
    with open(path, encoding="utf-8-sig", errors="replace") as fh:
        return fh.read()


def run_check(check, folder):
    """Return (passed, detail) for one check against one output folder."""
    kind, rel = check.get("type"), check.get("path", "")
    if not rel or os.path.isabs(rel) or ".." in rel.replace("\\", "/").split("/"):
        return False, "path must be relative and stay inside the output folder"
    matches = sorted(p for p in glob.glob(os.path.join(folder, rel), recursive=True) if os.path.isfile(p))
    if not matches:
        return False, "no file matches '%s'" % rel
    if kind == "file_exists":
        return True, "%d file(s)" % len(matches)
    try:
        if kind in ("file_contains", "file_not_contains"):
            pattern = re.compile(check["pattern"], re.I | re.M)
            found = any(pattern.search(read_file(p)) for p in matches)
            return (found, "pattern %s" % ("found" if found else "not found")) if kind == "file_contains" \
                else (not found, "pattern %s" % ("absent" if not found else "present"))
        if kind == "max_lines":
            longest = max(read_file(p).count("\n") + 1 for p in matches)
            return longest <= int(check["max"]), "%d lines (max %s)" % (longest, check["max"])
        if kind == "frontmatter_key":
            for p in matches:
                text = read_file(p).replace("\r\n", "\n")
                end = text.find("\n---", 4) if text.startswith("---\n") else -1
                if end != -1 and re.search(r"(?m)^%s:" % re.escape(check["key"]), text[4:end]):
                    return True, "key present in %s" % os.path.basename(p)
            return False, "key '%s' not found in any frontmatter" % check["key"]
    except (KeyError, ValueError, re.error) as e:
        return False, "bad check definition: %s" % e
    return False, "unknown check type '%s'" % kind


def score_folder(checks, folder):
    rows = []
    for i, c in enumerate(checks, 1):
        passed, detail = run_check(c, folder)
        rows.append({"n": i, "label": c.get("label") or "%s %s" % (c.get("type"), c.get("path")),
                     "pass": passed, "detail": detail})
    return rows


def score_tasks(evals_path, task_id, out_dir, base_dir):
    data = load_json(evals_path)
    evals = data.get("evals") if isinstance(data, dict) else None
    task = next((e for e in evals or [] if e.get("id") == task_id), None)
    if task is None:
        raise InputError("task id '%s' not found in %s" % (task_id, evals_path))
    checks = task.get("checks") or []
    if not checks:
        raise InputError("task '%s' has no scripted checks" % task_id)
    for folder in (out_dir, base_dir):
        if folder and not os.path.isdir(folder):
            raise InputError("not a folder: %s" % folder)
    with_rows = score_folder(checks, out_dir)
    result = {"task": task_id, "with": with_rows, "pass": all(r["pass"] for r in with_rows)}
    if base_dir:
        base_rows = score_folder(checks, base_dir)
        result["baseline"] = base_rows
        result["separating"] = [w["label"] for w, b in zip(with_rows, base_rows) if w["pass"] and not b["pass"]]
        result["not_measuring"] = [w["label"] for w, b in zip(with_rows, base_rows) if w["pass"] == b["pass"]]
    return result


def print_triggers(r):
    for label, key in (("all queries", "overall"), ("held-out 40%", "held_out")):
        x = r[key]
        print("%-13s should-trigger %d (loaded %s, bar >= 90%%) | near-miss %d (false-loaded %s, bar <= 10%%)"
              % (label, x["positives"], fmt(x["trigger_rate"]), x["negatives"], fmt(x["false_trigger_rate"])))
    for line in r["notes"] + r["misses"]:
        print(line)
    print("RESULT: %s" % ("PASS" if r["pass"] else "FAIL"))


def print_tasks(r):
    for name in ("with", "baseline"):
        if name not in r:
            continue
        rows = r[name]
        print("[%s] %d/%d checks passed" % (name, sum(1 for x in rows if x["pass"]), len(rows)))
        for x in rows:
            print("  %s %2d. %s -- %s" % ("PASS" if x["pass"] else "FAIL", x["n"], x["label"], x["detail"]))
    if "separating" in r:
        print("separating checks (pass with skill, fail without): %d" % len(r["separating"]))
        for label in r["not_measuring"]:
            print("  NOT-MEASURING (same result in both runs): %s" % label)
    print("RESULT: %s" % ("PASS" if r["pass"] else "FAIL"))


def main(argv):
    args = [a for a in argv if not a.startswith("--")]
    as_json = "--json" in argv
    try:
        if len(args) == 3 and args[0] == "triggers":
            result = score_triggers(args[1], args[2])
            printer = print_triggers
        elif len(args) in (4, 5) and args[0] == "tasks":
            result = score_tasks(args[1], args[2], args[3], args[4] if len(args) == 5 else None)
            printer = print_tasks
        else:
            print(__doc__)
            return 2
    except InputError as e:
        print("error: %s" % e)
        return 2
    if as_json:
        print(json.dumps(result, indent=2))
    else:
        printer(result)
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main(sys.argv[1:]))
