#!/usr/bin/env python3
"""Run the fixture cases in fixtures/cases.json against scripts/tokens_check.py.

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
import tokens_check  # noqa: E402


def run_case(case):
    args = [case["args"][0]] + [os.path.join(HERE, "fixtures", a) for a in case["args"][1:]]
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        try:
            code = tokens_check.main(args)
        except SystemExit as exc:
            code = exc.code
    problems = []
    if code != case["exit"]:
        problems.append("exit %r, wanted %r" % (code, case["exit"]))
    if case["args"][0] == "css" and code == 0 and not out.getvalue().startswith(":root {"):
        problems.append("css output does not start with ':root {'")
    if case["args"][0] == "check" and code in (0, 1):
        rep = json.loads(out.getvalue())  # strict JSON or the case fails
        got = dict(rep)
        got["error_paths"] = sorted(f["path"] for f in rep["findings"] if f["severity"] == "error")
        for key, want in case["expect"].items():
            if got.get(key) != want:
                problems.append("%s: got %r, wanted %r" % (key, got.get(key), want))
    if code == 2 and not err.getvalue().startswith("error:"):
        problems.append("exit 2 without an 'error:' message on stderr")
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
