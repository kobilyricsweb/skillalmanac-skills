#!/usr/bin/env python3
"""Run the fixture cases in fixtures/cases.json against scripts/plan_check.py.

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
import plan_check  # noqa: E402


def run_case(case):
    path = os.path.join(HERE, "fixtures", case["file"])
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = plan_check.main([path])
    problems = []
    if code != case["exit"]:
        problems.append("exit %s, wanted %s" % (code, case["exit"]))
    exp = case["expect"]
    if exp and code in (0, 1):
        rep = json.loads(out.getvalue())
        got = {
            "ok": rep["ok"], "steps": rep["steps"], "counts": rep["counts"], "day_totals": rep["day_totals"],
            "codes_error": [f["code"] for f in rep["findings"] if f["severity"] == "error"],
            "codes_warning": [f["code"] for f in rep["findings"] if f["severity"] == "warning"],
        }
        for key, want in exp.items():
            if got.get(key) != want:
                problems.append("%s: got %r, wanted %r" % (key, got.get(key), want))
    return problems


def main():
    with open(os.path.join(HERE, "fixtures", "cases.json"), encoding="utf-8") as handle:
        cases = json.load(handle)["cases"]
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
