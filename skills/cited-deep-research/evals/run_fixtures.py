#!/usr/bin/env python3
"""Run the fixture cases in fixtures/cases.json against scripts/validate_research.py.

    python evals/run_fixtures.py

Reads fixtures; writes nothing. Compares exit code, ok flag, counts and the
sorted lists of error and warning codes. Exit 0 if every case matches, 1 otherwise.
"""
import contextlib
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "scripts"))
import validate_research  # noqa: E402


def run_case(case):
    args = [os.path.join(HERE, "fixtures", a) if a.endswith(".md") else a for a in case["args"]]
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        try:
            code = validate_research.main(args)
        except SystemExit as exc:
            code = exc.code
    problems = []
    if code != case["exit"]:
        problems.append(f"exit {code}, wanted {case['exit']}")
    if code in (0, 1):
        rep = json.loads(out.getvalue())
        got = {
            "ok": rep["ok"], "counts": rep["counts"],
            "error_codes": sorted(e["code"] for e in rep["errors"]),
            "warning_codes": sorted(w["code"] for w in rep["warnings"]),
        }
        for key, want in case["expect"].items():
            want = sorted(want) if key.endswith("_codes") else want
            if got[key] != want:
                problems.append(f"{key}: got {got[key]!r}, wanted {want!r}")
    return problems


def main():
    with open(os.path.join(HERE, "fixtures", "cases.json"), encoding="utf-8") as handle:
        cases = json.load(handle)["cases"]
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
