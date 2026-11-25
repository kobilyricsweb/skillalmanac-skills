#!/usr/bin/env python3
"""Compute the with/without verdict from blind grades.

    python verdict.py <workdir> [--resamples=N] [--seed=N]

Reads <workdir>/tasks.json, key.json, grades.json, blind/ and runs/. For each
task the pass rate of a run is (checks passed) / (checks). The task difference
is the mean with-skill pass rate minus the mean without-skill pass rate, in
points (0-100). The mean of task differences gets a 95% percentile bootstrap
interval, resampled over tasks (runs of one task are not independent, so tasks
are the unit), and an exact two-sided sign-flip test over tasks.

Verdict:
  LIFT              interval above 0, at least 6 tasks, sign-flip p <= 0.05
  HARMED            interval below 0, at least 6 tasks, sign-flip p <= 0.05
  LIFT_UNCONFIRMED  mean > 0 otherwise
  NO_LIFT           mean <= 0 otherwise
  INCONCLUSIVE      fewer than 4 tasks, or the test is incomplete: a planned
                    run missing (runs per arm unequal, or not equal to "reps"
                    in tasks.json), runs/, key.json and blind/ disagreeing, a
                    blinded output not graded, or a task with no runs
With 5 tasks or fewer even a unanimous result cannot reach two-sided p <= 0.05
(5 tasks: p = 0.0625), so LIFT and HARMED need at least 6 tasks.

A check marked pass counts as failed when its quote is empty, too short to be
evidence (a fragment under 4 characters or under 6 characters in all), or not
found in the blinded output. Quotes are compared after lowercasing, collapsing
whitespace and removing markdown marks and quote characters; "..." may skip
text between fragments. A task with "void": true in tasks.json is left out and
listed.

Prints one JSON object. Exit codes: 0 = verdict computed (any verdict),
2 = usage error or inconsistent input.
Python 3.9+, standard library only, no network.
"""
import itertools
import json
import os
import random
import re
import sys

MIN_TASKS = 4
MIN_TASKS_CONFIRMED = 6
MAX_P = 0.05
DEFAULT_RESAMPLES = 10000
DEFAULT_SEED = 20261125
RUN_NAME = re.compile(r"^(with|without)_(\d+)\.md$")
STRIP = re.compile(r"[*_`\"'‘’“”>#|]")


def fail(msg):
    print(f"error: {msg}", file=sys.stderr)
    sys.exit(2)


def load(path):
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError) as exc:
        fail(f"cannot read {path}: {exc}")


def parse_args(argv):
    opts = {"resamples": DEFAULT_RESAMPLES, "seed": DEFAULT_SEED}
    pos = []
    it = iter(argv)
    for a in it:
        if a.startswith("--"):
            name, _, val = a[2:].partition("=")
            if name not in opts:
                fail(f"unknown option --{name}")
            if not val:
                val = next(it, "")
            try:
                opts[name] = int(val)
            except ValueError:
                fail(f"--{name} needs an integer")
        else:
            pos.append(a)
    if len(pos) != 1:
        fail("usage: python verdict.py <workdir> [--resamples=N] [--seed=N]")
    if opts["resamples"] < 100:
        fail("--resamples must be at least 100")
    return pos[0], opts["resamples"], opts["seed"]


def norm(text):
    return " ".join(STRIP.sub(" ", text.lower()).split())


def quote_problem(quote, raw_output):
    """None when the quote is usable evidence found in the output, else the reason."""
    raw_frags = [" ".join(f.split()) for f in re.split(r"\.\.\.|…", quote)]
    raw_frags = [f for f in raw_frags if f]
    if not raw_frags:
        return "pass without a quote"
    if min(len(f) for f in raw_frags) < 4 or sum(len(f) for f in raw_frags) < 6:
        return "quote too short to be evidence"
    for normalize in (lambda value: " ".join(value.lower().split()), norm):
        output = normalize(raw_output)
        position = 0
        for fragment in raw_frags:
            needle = normalize(fragment)
            found = output.find(needle, position) if needle else -1
            if found < 0:
                break
            position = found + len(needle)
        else:
            return None
    return "quote not found in the output"


def read_text(path):
    with open(path, encoding="utf-8", errors="replace") as fh:
        return fh.read()


def run_lengths(work):
    lengths = {"with": [], "without": []}
    runs = os.path.join(work, "runs")
    if not os.path.isdir(runs):
        return lengths
    for task in os.listdir(runs):
        tdir = os.path.join(runs, task)
        if not os.path.isdir(tdir):
            continue
        for f in os.listdir(tdir):
            m = RUN_NAME.match(f)
            if m:
                lengths[m.group(1)].append(len(read_text(os.path.join(tdir, f))))
    return lengths


def mean(xs):
    return sum(xs) / len(xs) if xs else 0.0


def sign_flip_p(diffs):
    """Exact two-sided sign-flip p: share of sign patterns whose |mean| is at least the observed |mean|."""
    m = abs(mean(diffs))
    if m == 0:
        return 1.0
    nonzero = [abs(d) for d in diffs if d != 0]
    hits = total = 0
    for signs in itertools.product((1, -1), repeat=len(nonzero)):
        s = abs(sum(a * b for a, b in zip(signs, nonzero)) / len(diffs))
        total += 1
        hits += s >= m - 1e-9
    return hits / total


def coverage_problems(work, tasks, void, key, reps):
    """Every planned run must exist in runs/, in key.json and in blind/, equally in both arms."""
    out = []
    blind_root = os.path.join(work, "blind")
    unexpected_tasks = set(os.listdir(blind_root)) - set(tasks)
    if unexpected_tasks:
        out.append(f"blind/: unexpected task entries {sorted(unexpected_tasks)}")
    unexpected_key_tasks = set(key) - set(tasks)
    if unexpected_key_tasks:
        out.append(f"key.json: unexpected task entries {sorted(unexpected_key_tasks)}")
    for task in tasks:
        if task in void:
            continue
        tdir = os.path.join(work, "runs", task)
        runs = {"with": 0, "without": 0}
        if os.path.isdir(tdir):
            for f in os.listdir(tdir):
                m = RUN_NAME.match(f)
                if m:
                    runs[m.group(1)] += 1
        blind_task = os.path.join(blind_root, task)
        actual_files = set(os.listdir(blind_task)) if os.path.isdir(blind_task) else set()
        expected_files = {f"{rid}.md" for rid in key.get(task, {})}
        unexpected = sorted(actual_files - expected_files)
        missing = sorted(expected_files - actual_files)
        if unexpected or missing:
            out.append(f"{task}: blind/key mismatch; unexpected {unexpected}, missing {missing}")
        keyed = {"with": 0, "without": 0}
        for rid, arm in key.get(task, {}).items():
            keyed[arm] = keyed.get(arm, 0) + 1
            if not os.path.isfile(os.path.join(work, "blind", task, f"{rid}.md")):
                out.append(f"{task}: blinded file {rid}.md is missing")
        if runs != keyed:
            out.append(f"{task}: runs/ has {runs} but key.json has {keyed}")
        if runs["with"] != runs["without"]:
            out.append(f"{task}: unequal runs per arm {runs}")
        if reps is not None and (runs["with"] != reps or runs["without"] != reps):
            out.append(f"{task}: tasks.json says reps {reps}, runs/ has {runs}")
    return out


def main(argv):
    work, resamples, seed = parse_args(argv)
    tdoc = load(os.path.join(work, "tasks.json"))
    if not isinstance(tdoc, dict) or not isinstance(tdoc.get("tasks"), list):
        fail("tasks.json must be an object with a 'tasks' list")
    tasks = {t["id"]: t for t in tdoc["tasks"]}
    void = sorted(t for t, v in tasks.items() if v.get("void"))
    key = load(os.path.join(work, "key.json"))
    grades = load(os.path.join(work, "grades.json"))
    if not isinstance(key, dict):
        fail("key.json must be an object")
    if not isinstance(grades, list) or not all(isinstance(g, dict) for g in grades):
        fail("grades.json must be a list of objects")
    if not os.path.isdir(os.path.join(work, "blind")):
        fail("no blind/ folder; quotes cannot be verified")

    reps = tdoc.get("reps")
    if reps is not None and (not isinstance(reps, int) or reps < 1):
        fail("reps in tasks.json must be a positive integer")

    rates = {}  # task -> arm -> [pass rate per run]
    seen = set()
    problems = []
    incomplete = coverage_problems(work, tasks, void, key, reps)
    for g in grades:
        task, rid = g.get("task"), g.get("id")
        if task not in tasks:
            fail(f"grade for unknown task {task!r}")
        if task not in key or rid not in key[task]:
            fail(f"grade id {rid!r} is not in key.json for task {task!r}")
        if (task, rid) in seen:
            fail(f"duplicate grade for {task}/{rid}")
        seen.add((task, rid))
        if task in void:
            continue
        checks = g.get("checks")
        n = len(tasks[task]["checks"])
        if not isinstance(checks, list) or len(checks) != n:
            fail(f"{task}/{rid}: check results do not match the {n} checks in tasks.json")
        path = os.path.join(work, "blind", task, f"{rid}.md")
        if not os.path.isfile(path):
            fail(f"blinded output {path} is missing")
        text = read_text(path)
        passed = 0
        for i, c in enumerate(checks, 1):
            if not isinstance(c, dict) or not isinstance(c.get("pass"), bool):
                fail(f"{task}/{rid} check {i}: 'pass' must be true or false")
            if not c["pass"]:
                continue
            why = quote_problem(str(c.get("quote", "")), text)
            if why:
                problems.append(f"{task}/{rid} check {i}: {why}, counted as fail")
            else:
                passed += 1
        rates.setdefault(task, {"with": [], "without": []})[key[task][rid]].append(passed / n)

    for task, ids in key.items():
        if task in void:
            continue
        missing = [rid for rid in ids if (task, rid) not in seen]
        if missing:
            incomplete.append(f"{task}: {len(missing)} blinded output(s) not graded")
    for task in tasks:
        if task not in void and task not in key:
            incomplete.append(f"{task}: in tasks.json but has no runs")

    per_task = []
    diffs = []
    for task in sorted(rates):
        r = rates[task]
        if not r["with"] or not r["without"]:
            incomplete.append(f"{task}: one arm has no graded run")
            continue
        w, wo = mean(r["with"]) * 100, mean(r["without"]) * 100
        diffs.append(w - wo)
        per_task.append({"task": task, "with": round(w, 1), "without": round(wo, 1),
                         "difference": round(w - wo, 1), "runs_with": len(r["with"]),
                         "runs_without": len(r["without"])})

    lengths = run_lengths(work)
    out = {
        "tasks": len(per_task),
        "per_task": per_task,
        "wins": sum(d > 0 for d in diffs),
        "ties": sum(d == 0 for d in diffs),
        "losses": sum(d < 0 for d in diffs),
        "length_chars": {"with": round(mean(lengths["with"])), "without": round(mean(lengths["without"]))},
        "void_tasks": void,
        "problems": problems + incomplete,
    }
    m = round(mean(diffs), 1) if diffs else None
    if incomplete:
        out.update({"verdict": "INCONCLUSIVE", "mean_difference": m, "ci95": None,
                    "reason": "the test is incomplete; grade every blinded output or mark the task void"})
    elif len(per_task) < MIN_TASKS:
        out.update({"verdict": "INCONCLUSIVE", "mean_difference": m, "ci95": None,
                    "reason": f"{len(per_task)} graded tasks; {MIN_TASKS} needed"})
    else:
        rng = random.Random(seed)
        boots = sorted(mean([rng.choice(diffs) for _ in diffs]) for _ in range(resamples))
        lo = boots[int(0.025 * resamples)]
        hi = boots[min(resamples - 1, int(0.975 * resamples))]
        mu = mean(diffs)
        p = sign_flip_p(diffs)
        enough = len(per_task) >= MIN_TASKS_CONFIRMED and p <= MAX_P
        if lo > 0 and enough:
            verdict = "LIFT"
        elif hi < 0 and enough:
            verdict = "HARMED"
        elif mu > 0:
            verdict = "LIFT_UNCONFIRMED"
        else:
            verdict = "NO_LIFT"
        out.update({"verdict": verdict, "mean_difference": round(mu, 1), "ci95": [round(lo, 1), round(hi, 1)],
                    "sign_flip_p": round(p, 4),
                    "method": f"percentile bootstrap over tasks, {resamples} resamples, seed {seed}; exact two-sided sign-flip test over tasks"})
        if not enough and (lo > 0 or hi < 0):
            out["reason"] = (f"interval excludes 0, but confirmation needs at least {MIN_TASKS_CONFIRMED} tasks "
                             f"and sign-flip p <= {MAX_P} (here {len(per_task)} tasks, p {round(p, 4)})")
        elif lo == 0 or hi == 0:
            out["reason"] = "the interval touches 0; treat the verdict as borderline"
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main(sys.argv[1:])
