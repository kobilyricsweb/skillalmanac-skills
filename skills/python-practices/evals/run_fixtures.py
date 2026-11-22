#!/usr/bin/env python3
"""Run the cases in fixtures/cases.json against scripts/py_audit.py.

    python evals/run_fixtures.py

Reads fixtures; writes nothing. Exit 0 if every case matches, 1 otherwise.
"""
import contextlib
import io
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "scripts"))
import py_audit  # noqa: E402


def run_case(case):
    args = [str(HERE / "fixtures" / a) for a in case["args"]]
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = py_audit.main(args)
    problems = []
    if code != case["exit"]:
        problems.append(f"exit {code}, wanted {case['exit']}")
    if case["verdict"] is not None and code in (0, 1):
        rep = json.loads(out.getvalue())
        got_findings = [[f["line"], f["rule"]] for f in rep["findings"]]
        for key, got in (("verdict", rep["verdict"]), ("files_scanned", rep["files_scanned"]), ("findings", got_findings)):
            if got != case[key]:
                problems.append(f"{key}: got {got!r}, wanted {case[key]!r}")
    return problems


def main():
    cases = json.loads((HERE / "fixtures" / "cases.json").read_text(encoding="utf-8"))["cases"]
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
