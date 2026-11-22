#!/usr/bin/env python3
"""Run the fixture cases in fixtures/cases.json against scripts/iac_scan.py.

    python evals/run_fixtures.py

Reads fixtures; writes nothing. Exit 0 if every case matches, 1 otherwise.
"""
import contextlib
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
FIX = os.path.join(HERE, "fixtures")
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "scripts"))
import iac_scan  # noqa: E402


def run_case(case):
    args = [os.path.join(FIX, a) if os.path.exists(os.path.join(FIX, a)) else a for a in case["args"]]
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = iac_scan.main(args)
    problems = []
    if code != case["exit"]:
        problems.append("exit %r, wanted %r" % (code, case["exit"]))
    if code in (0, 1):
        rep = json.loads(out.getvalue())
        got = dict(rep)
        if rep["command"] == "scan":
            got["findings"] = ["%d:%s:%s" % (f["line"], f["rule"], f["severity"]) for f in rep["findings"]]
        else:
            got["risky"] = ["%s:%s" % (r["address"], r["severity"]) for r in rep["risky"]]
        for key, want in case["expect"].items():
            if got.get(key) != want:
                problems.append("%s: got %r, wanted %r" % (key, got.get(key), want))
    return problems


def main():
    with open(os.path.join(FIX, "cases.json"), encoding="utf-8") as fh:
        cases = json.load(fh)["cases"]
    failed = 0
    for case in cases:
        problems = run_case(case)
        print(("PASS " if not problems else "FAIL ") + case["name"] + ": " + " ".join(case["args"]))
        for p in problems:
            print("    " + p)
        failed += bool(problems)
    print("%d/%d cases passed" % (len(cases) - failed, len(cases)))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
