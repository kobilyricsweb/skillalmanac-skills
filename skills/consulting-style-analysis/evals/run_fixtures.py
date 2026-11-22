#!/usr/bin/env python3
"""Run the cases in fixtures/cases.json against scripts/analysis_check.py.

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
import analysis_check  # noqa: E402


def run_case(case):
    args = [os.path.join(HERE, "fixtures", a) if a.endswith(".json") else a for a in case["args"]]
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = analysis_check.main(args)
    problems = []
    if code != case["exit"]:
        problems.append("exit %r, wanted %r" % (code, case["exit"]))
    exp = case.get("expect")
    if exp and code in (0, 1):
        rep = json.loads(out.getvalue())
        got = {
            "ok": rep["ok"],
            "error_codes": sorted(e["code"] for e in rep["errors"]),
            "warning_codes": sorted(w["code"] for w in rep["warnings"]),
            "counts": rep["counts"],
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
        print(("PASS " if not problems else "FAIL ") + " ".join(case["args"]))
        for p in problems:
            print("    " + p)
        failed += bool(problems)
    print("%d/%d cases passed" % (len(cases) - failed, len(cases)))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
