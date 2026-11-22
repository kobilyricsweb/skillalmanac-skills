#!/usr/bin/env python3
"""Run the fixture cases in fixtures/cases.json against scripts/estimate_cost.py.

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
import estimate_cost  # noqa: E402


def dig(obj, path):
    """Follow a dotted path; numeric parts index into lists."""
    for part in path.split("."):
        if isinstance(obj, list):
            obj = obj[int(part)] if int(part) < len(obj) else None
        elif isinstance(obj, dict):
            obj = obj.get(part)
        else:
            return None
    return obj


def run_case(case):
    args = [os.path.join(HERE, "fixtures", a) if a.endswith(".json") else a for a in case["args"]]
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        try:
            code = estimate_cost.main(args)
        except SystemExit as exc:
            code = exc.code
    problems = []
    if code != case["exit"]:
        problems.append(f"exit {code}, wanted {case['exit']}")
    if case["expect"] and code in (0, 1):
        rep = json.loads(out.getvalue())
        for key, want in case["expect"].items():
            got = dig(rep, key)
            if got != want:
                problems.append(f"{key}: got {got!r}, wanted {want!r}")
    return problems


def main():
    with open(os.path.join(HERE, "fixtures", "cases.json"), encoding="utf-8") as fh:
        cases = json.load(fh)["cases"]
    failed = 0
    for case in cases:
        problems = run_case(case)
        label = " ".join(a for a in case["args"] if a != "--today" and not a[0].isdigit())
        print(("PASS " if not problems else "FAIL ") + label)
        for p in problems:
            print("    " + p)
        failed += bool(problems)
    print(f"{len(cases) - failed}/{len(cases)} cases passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
