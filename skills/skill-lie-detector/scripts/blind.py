#!/usr/bin/env python3
"""Blind the outputs of a with/without skill test.

    python blind.py <workdir> [--seed=N] [--redact=REGEX] [--redact-with=TEXT]

Reads <workdir>/runs/<task_id>/{with,without}_<n>.md, copies each file to
<workdir>/blind/<task_id>/<random id>.md in shuffled order, and writes the arm of
every id to <workdir>/key.json. Refuses to overwrite an existing blind/ folder or
key.json, so a finished grading round cannot be silently re-keyed.

Answers often name their arm ("the skill says...", "I did not read any
SKILL.md"). Every blinded line that mentions a skill is listed under
"possible_arm_leaks". --redact=REGEX replaces matches (case-insensitive) in the
blinded copies; the files in runs/ are not changed. The replacement is
--redact-with (default "[redacted]"). Use --redact-with= (empty) to delete identity words without
leaving a marker; any inserted text that appears in one arm only gives that arm
away.

Coverage: every task in tasks.json that is not void must have the same number
of runs in both arms, equal to "reps" when tasks.json gives it; otherwise
blind.py stops. After blinding it lists "one_arm_terms": words or word pairs
found in at least half of one arm's answers and in none of the other arm's
(the arm is not named). Each is either the skill's real effect or an identity
marker to redact.

Exit codes: 0 = done, 2 = usage error or bad input.
Python 3.9+, standard library only, no network.
"""
import json
import os
import random
import re
import secrets
import sys

RUN_NAME = re.compile(r"^(with|without)_(\d+)\.md$")
LOOSE_NAME = re.compile(r"^(with|without)_\d+\.md$", re.I)
LEAK = re.compile(r"skill[.]md|(?<![a-z])skills?(?![a-z])", re.I)
TASK_ID = re.compile(r"^[A-Za-z0-9-]+$")


WORD = re.compile(r"[a-z][a-z0-9'-]{2,}")


def terms(text):
    words = WORD.findall(text.lower())
    return set(words) | {a + " " + b for a, b in zip(words, words[1:])}


def one_arm_terms(docs, limit=30):
    """Terms in at least half of one arm's answers and in none of the other arm's."""
    by_arm = {"with": [t for a, t in docs if a == "with"], "without": [t for a, t in docs if a == "without"]}
    found = []
    for arm, other in (("with", "without"), ("without", "with")):
        if not by_arm[arm]:
            continue
        seen_other = set().union(*by_arm[other]) if by_arm[other] else set()
        counts = {}
        for t in by_arm[arm]:
            for w in t - seen_other:
                counts[w] = counts.get(w, 0) + 1
        need = (len(by_arm[arm]) + 1) // 2
        found += [(c / len(by_arm[arm]), w) for w, c in counts.items() if c >= need]
    found.sort(key=lambda x: (-x[0], x[1]))
    return [{"term": w, "share_of_one_arm": round(s, 2)} for s, w in found[:limit]]


def fail(msg):
    print(f"error: {msg}", file=sys.stderr)
    sys.exit(2)


def main(argv):
    args, seed, redact, redact_with = [], None, None, "[redacted]"
    it = iter(argv)
    for a in it:
        if a.startswith("--"):
            name, _, val = a[2:].partition("=")
            if not val:
                val = next(it, "")
            if name == "seed":
                try:
                    seed = int(val)
                except ValueError:
                    fail("--seed needs an integer")
            elif name == "redact-with":
                redact_with = val
            elif name == "redact":
                try:
                    redact = re.compile(val, re.I)
                except re.error as exc:
                    fail(f"--redact is not a valid regex: {exc}")
            else:
                fail(f"unknown option --{name}")
        else:
            args.append(a)
    if len(args) != 1:
        fail("usage: python blind.py <workdir> [--seed=N] [--redact=REGEX] [--redact-with=TEXT]")
    work = args[0]
    runs = os.path.join(work, "runs")
    blind = os.path.join(work, "blind")
    key_path = os.path.join(work, "key.json")
    if not os.path.isdir(runs):
        fail(f"no runs folder at {runs}")
    if os.path.exists(blind) or os.path.exists(key_path):
        fail("blind/ or key.json already exists; move them away before re-blinding")

    tasks_path = os.path.join(work, "tasks.json")
    reps, planned = None, None
    if os.path.isfile(tasks_path):
        try:
            with open(tasks_path, encoding="utf-8") as fh:
                tdoc = json.load(fh)
        except (OSError, ValueError) as exc:
            fail(f"cannot read {tasks_path}: {exc}")
        reps = tdoc.get("reps") if isinstance(tdoc, dict) else None
        if reps is not None and (not isinstance(reps, int) or reps < 1):
            fail("reps in tasks.json must be a positive integer")
        planned = [t["id"] for t in tdoc.get("tasks", []) if not t.get("void")]
        missing = [t for t in planned if not os.path.isdir(os.path.join(runs, t))]
        if missing:
            fail(f"tasks in tasks.json with no runs folder: {missing}")

    rng = random.Random(seed) if seed is not None else random.SystemRandom()
    key = {}
    summary = []
    leaks = []
    docs = []
    for task in sorted(os.listdir(runs)):
        tdir = os.path.join(runs, task)
        if not os.path.isdir(tdir):
            continue
        if not TASK_ID.match(task):
            fail(f"task folder name not allowed: {task!r}")
        odd = [f for f in os.listdir(tdir) if LOOSE_NAME.match(f) and not RUN_NAME.match(f)]
        if odd:
            fail(f"task {task}: rename {odd} to lower case (with_1.md, without_1.md)")
        files = sorted(f for f in os.listdir(tdir) if RUN_NAME.match(f))
        arms = {RUN_NAME.match(f).group(1) for f in files}
        if arms != {"with", "without"}:
            fail(f"task {task}: needs at least one with_ and one without_ file, found {files}")
        counts = {a: sum(RUN_NAME.match(f).group(1) == a for f in files) for a in ("with", "without")}
        if counts["with"] != counts["without"]:
            fail(f"task {task}: {counts['with']} with-skill runs but {counts['without']} without; run the missing ones or void the task")
        if reps is not None and counts["with"] != reps:
            fail(f"task {task}: {counts['with']} runs per arm but tasks.json says reps {reps}")
        rng.shuffle(files)
        key[task] = {}
        os.makedirs(os.path.join(blind, task))
        used = set()
        for f in files:
            while True:
                rid = "".join(rng.choice("abcdefghjkmnpqrstuvwxyz23456789") for _ in range(6)) if seed is not None else secrets.token_hex(3)
                if rid not in used:
                    used.add(rid)
                    break
            with open(os.path.join(tdir, f), encoding="utf-8", errors="replace") as fh:
                text = fh.read()
            if redact is not None:
                text = redact.sub(lambda _m: redact_with, text)
            with open(os.path.join(blind, task, rid + ".md"), "w", encoding="utf-8") as fh:
                fh.write(text)
            for n, line in enumerate(text.splitlines(), 1):
                if LEAK.search(line):
                    leaks.append({"task": task, "id": rid, "line": n, "text": line.strip()[:160]})
            key[task][rid] = RUN_NAME.match(f).group(1)
            docs.append((key[task][rid], terms(text)))
        summary.append({"task": task, "files": len(files)})
    if not key:
        fail("no task folders found under runs/")
    with open(key_path, "w", encoding="utf-8") as fh:
        json.dump(key, fh, indent=1, sort_keys=True)
    print(json.dumps({"blinded": summary, "key": key_path,
                      "possible_arm_leaks": leaks,
                      "one_arm_terms": one_arm_terms(docs),
                      "note": "do not open key.json before grading is finished; read every leak line and, if it can reveal the arm, delete blind/ and key.json and re-run with --redact, or void the task"}, indent=1))


if __name__ == "__main__":
    main(sys.argv[1:])
