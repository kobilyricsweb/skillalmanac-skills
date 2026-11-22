#!/usr/bin/env python3
"""Run the fixture cases in fixtures/cases.json against scripts/jtbd_check.py.

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
import jtbd_check  # noqa: E402


def run_case(case):
    args = [os.path.join(HERE, "fixtures", a) if a.endswith(".json") else a for a in case["args"]]
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = jtbd_check.main(args)
    problems = []
    if code != case["exit"]:
        problems.append(f"exit {code}, wanted {case['exit']}")
    try:
        rep = json.loads(out.getvalue())
    except ValueError:
        return problems + ["stdout is not valid JSON"]
    summary = rep.get("summary", {})
    got = dict(summary)
    got["ok"] = rep.get("ok")
    for key, want in case["expect"].items():
        if got.get(key) != want:
            problems.append(f"{key}: got {got.get(key)!r}, wanted {want!r}")
    if code == 2 and "error" not in rep:
        problems.append("exit 2 without an error field")
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
    print(f"{len(cases) - failed}/{len(cases)} cases passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
