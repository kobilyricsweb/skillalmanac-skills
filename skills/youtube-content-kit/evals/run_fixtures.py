#!/usr/bin/env python3
"""Run the fixture cases in fixtures/cases.json against scripts/video_check.py.

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
import video_check  # noqa: E402


def run_case(case):
    args = [os.path.join(HERE, "fixtures", a) for a in case["args"]]
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        code = video_check.main(args)
    problems = []
    if code != case["exit"]:
        problems.append(f"exit {code}, wanted {case['exit']}")
    try:
        rep = json.loads(out.getvalue())
    except json.JSONDecodeError:
        return problems + ["output is not strict JSON"]
    findings = rep.get("findings", [])
    got = dict(rep)
    got["fail_checks"] = sorted(f["check"] for f in findings if f["severity"] == "FAIL")
    got["warn_checks"] = sorted(f["check"] for f in findings if f["severity"] == "WARN")
    for key, want in case["expect"].items():
        if got.get(key) != want:
            problems.append(f"{key}: got {got.get(key)!r}, wanted {want!r}")
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
