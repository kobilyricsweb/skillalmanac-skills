#!/usr/bin/env python3
"""Run the fixture cases in fixtures/cases.json against scripts/validate_ad_plan.py.

    python evals/run_fixtures.py

Reads fixtures; writes nothing. Exit 0 if every case matches, 1 otherwise.
"""
import contextlib
import io
import json
import os
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "scripts"))
import validate_ad_plan  # noqa: E402


def run_case(case):
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        code = validate_ad_plan.main([os.path.join(HERE, "fixtures", case["file"])])
    problems = []
    if code != case["exit"]:
        problems.append(f"exit {code}, wanted {case['exit']}")
    try:
        rep = json.loads(out.getvalue())  # strict JSON on stdout is part of the contract
    except ValueError as exc:
        return problems + [f"stdout is not JSON: {exc}"]
    exp = case["expect"]
    if rep.get("valid") != exp["valid"]:
        problems.append(f"valid {rep.get('valid')}, wanted {exp['valid']}")
    if "errors" in exp:
        s = rep.get("summary", {})
        if s.get("errors") != exp["errors"] or s.get("warnings") != exp["warnings"]:
            problems.append(f"errors/warnings {s.get('errors')}/{s.get('warnings')}, wanted {exp['errors']}/{exp['warnings']}")
        got = dict(Counter(f["code"] for f in rep.get("findings", [])))
        if got != exp["codes"]:
            problems.append(f"codes {got}, wanted {exp['codes']}")
    return problems


def main():
    cases = json.load(open(os.path.join(HERE, "fixtures", "cases.json"), encoding="utf-8"))["cases"]
    failed = 0
    for case in cases:
        problems = run_case(case)
        print(("PASS " if not problems else "FAIL ") + case["file"])
        for p in problems:
            print("    " + p)
        failed += bool(problems)
    print(f"{len(cases) - failed}/{len(cases)} cases passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
