#!/usr/bin/env python3
"""Run the cases in fixtures/cases.json against scripts/habit_review.py.

    python evals/run_fixtures.py

Reads the fixtures. Writes nothing (it also checks that the script left the
fixtures folder exactly as it found it). Exit 0 if every case matches, 1 otherwise.
"""
import contextlib
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
FIXTURES = os.path.join(HERE, "fixtures")
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "scripts"))
import habit_review  # noqa: E402


def dig(obj, dotted):
    for part in dotted.split("."):
        if not isinstance(obj, dict) or part not in obj:
            return "<missing>"
        obj = obj[part]
    return obj


def codes(warnings):
    return sorted(w.split(":", 1)[0] for w in warnings)


def snapshot():
    return sorted((n, os.path.getsize(os.path.join(FIXTURES, n))) for n in os.listdir(FIXTURES))


def run_case(case):
    args = [os.path.join(FIXTURES, a) if a.endswith(".csv") else a for a in case["args"]]
    before = snapshot()
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        try:
            code = habit_review.main(args)
        except SystemExit as exc:
            code = exc.code
    problems = []
    if snapshot() != before:
        problems.append("the fixtures folder changed during the run")
    if code != case["exit"]:
        problems.append("exit %r, wanted %r" % (code, case["exit"]))
    if code == 2:
        if not err.getvalue().strip():
            problems.append("exit 2 without a message on stderr")
        return problems
    report = json.loads(out.getvalue())
    for key, want in case["global"].items():
        got = codes(report["warnings"]) if key == "warning_codes" else report.get(key)
        if got != want:
            problems.append("%s: got %r, wanted %r" % (key, got, want))
    by_name = {h["name"]: h for h in report["habits"]}
    for name, fields in case["habits"].items():
        habit = by_name.get(name)
        if habit is None:
            problems.append("habit %r not in the report" % name)
            continue
        for key, want in fields.items():
            got = codes(habit["warnings"]) if key == "warning_codes" else dig(habit, key)
            if got != want:
                problems.append("%s.%s: got %r, wanted %r" % (name, key, got, want))
    return problems


def main():
    with open(os.path.join(FIXTURES, "cases.json"), encoding="utf-8") as fh:
        cases = json.load(fh)["cases"]
    failed = 0
    for case in cases:
        problems = run_case(case)
        print(("PASS " if not problems else "FAIL ") + case["name"])
        for p in problems:
            print("    " + p)
        failed += bool(problems)
    print("%d/%d cases passed" % (len(cases) - failed, len(cases)))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
