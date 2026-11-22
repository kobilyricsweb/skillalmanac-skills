#!/usr/bin/env python3
"""Run the fixture cases in fixtures/cases.json against scripts/check_steps.py.

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
import check_steps  # noqa: E402


def run_case(case):
    path = os.path.join(HERE, "fixtures", case["file"])
    out, err = io.StringIO(), io.StringIO()
    out.buffer = io.BytesIO()  # main() writes UTF-8 bytes to stdout.buffer when it exists
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        try:
            code = check_steps.main([path])
        except SystemExit as exc:
            code = exc.code
    problems = []
    if code != case["exit"]:
        problems.append("exit %r, wanted %r" % (code, case["exit"]))
    exp = case["expect"]
    if exp and code in (0, 1):
        rep = json.loads(out.buffer.getvalue().decode("utf-8"))
        got = {
            "statuses": [s["status"] for s in rep["steps"]],
            "first_error": None if rep["first_error"] is None else {
                "step": rep["first_error"]["step"], "slip": rep["first_error"]["suspected_slip"]},
            "drift_flagged": rep["rounding"]["drift_flagged"],
            "last_solutions": rep["steps"][-1]["solutions"],
        }
        for key, want in exp.items():
            if got.get(key) != want:
                problems.append("%s: got %r, wanted %r" % (key, got.get(key), want))
    return problems


def main():
    with open(os.path.join(HERE, "fixtures", "cases.json"), encoding="utf-8") as fh:
        cases = json.load(fh)["cases"]
    failed = 0
    for case in cases:
        problems = run_case(case)
        print(("PASS " if not problems else "FAIL ") + case["file"])
        for p in problems:
            print("    " + p)
        failed += bool(problems)
    print("%d/%d cases passed" % (len(cases) - failed, len(cases)))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
