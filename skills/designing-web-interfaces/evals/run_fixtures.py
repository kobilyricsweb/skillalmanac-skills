#!/usr/bin/env python3
"""Run the fixture cases in fixtures/cases.json against scripts/ui_audit.py.

    python evals/run_fixtures.py

Reads fixtures; writes nothing. Exit 0 if every case matches, 1 otherwise.
Each case compares the exit code, the verdict, the counts, and the exact set of
(rule, severity) pairs. The expected values were checked by hand (see VERIFICATION.md).
"""
import contextlib
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "scripts"))
import ui_audit  # noqa: E402


def run_case(case):
    path = os.path.join(HERE, "fixtures", case["file"])
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = ui_audit.main([path] + case.get("flags", []))
    problems = []
    if code != case["exit"]:
        problems.append("exit %s, wanted %s" % (code, case["exit"]))
    exp = case.get("expect")
    if exp and code in (0, 1):
        rep = json.loads(out.getvalue())
        pairs = sorted({"%s:%s" % (f["rule"], f["severity"]) for f in rep["findings"]})
        got = {"verdict": rep["verdict"], "counts": rep["counts"], "findings": pairs, "kind": rep["kind"]}
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
        print(("PASS " if not problems else "FAIL ") + case["file"] + " " + " ".join(case.get("flags", [])))
        for p in problems:
            print("    " + p)
        failed += bool(problems)
    print("%d/%d cases passed" % (len(cases) - failed, len(cases)))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
