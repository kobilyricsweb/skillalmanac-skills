#!/usr/bin/env python3
"""Run the fixture cases in fixtures/cases.json against scripts/decision_matrix.py.

    python evals/run_fixtures.py

Reads fixtures; writes nothing. Exit 0 if every case matches, 1 otherwise.
"""
import contextlib
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "scripts"))
import decision_matrix  # noqa: E402

FIX = os.path.join(HERE, "fixtures")


def run_case(case):
    args = [os.path.join(FIX, a) if a.endswith((".json", ".csv")) else a for a in case["args"]]
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        code = decision_matrix.main(args)
    problems = []
    if code != case["exit"]:
        problems.append(f"exit {code}, wanted {case['exit']}")
    try:
        got = json.loads(out.getvalue())
    except ValueError:
        return problems + ["output is not valid JSON"]
    if case.get("expected"):
        want = json.load(open(os.path.join(FIX, case["expected"]), encoding="utf-8"))
        if got != want:
            keys = [k for k in want if got.get(k) != want[k]]
            problems.append("output differs from " + case["expected"] + " in: " + ", ".join(keys))
    if "winner" in case and got.get("winner", {}).get("option") != case["winner"]:
        problems.append(f"winner {got.get('winner')!r}, wanted {case['winner']!r}")
    for name, score in case.get("scores", {}).items():
        have = next((r["score"] for r in got.get("ranking", []) if r["option"] == name), None)
        if have != score:
            problems.append(f"score of {name}: {have!r}, wanted {score!r}")
    if "error_contains" in case:
        if got.get("ok") is not False or case["error_contains"] not in got.get("error", ""):
            problems.append(f"error text {got.get('error')!r} lacks {case['error_contains']!r}")
    return problems


def main():
    cases = json.load(open(os.path.join(FIX, "cases.json"), encoding="utf-8"))["cases"]
    failed = 0
    for case in cases:
        problems = run_case(case)
        print(("PASS " if not problems else "FAIL ") + " ".join(case["args"]))
        for p in problems:
            print("    " + p)
        failed += bool(problems)
    print(f"{len(cases) - failed}/{len(cases)} cases passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
