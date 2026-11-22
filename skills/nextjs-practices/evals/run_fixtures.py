#!/usr/bin/env python3
"""Run the fixture cases in fixtures/cases.json against scripts/next_scan.py.

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
import next_scan  # noqa: E402


def run_case(case):
    args = [os.path.join(HERE, "fixtures", a) if a.startswith(("bad_site", "good_site", "warn_site")) else a
            for a in case["args"]]
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = next_scan.main(args)
    problems = []
    if code != case["exit"]:
        problems.append(f"exit {code}, wanted {case['exit']}")
    exp = case.get("expect")
    if exp and code in (0, 1):
        rep = json.loads(out.getvalue())
        got = {
            "ok": rep["ok"], "files_scanned": rep["files_scanned"], "suppressed": rep["suppressed"],
            "counts_by_rule": rep["counts_by_rule"],
            "findings": [[f["file"], f["line"], f["rule"], f["severity"]] for f in rep["findings"]],
        }
        for key, want in exp.items():
            if got.get(key) != want:
                problems.append(f"{key}: got {got.get(key)!r}, wanted {want!r}")
    return problems


def main():
    cases = json.load(open(os.path.join(HERE, "fixtures", "cases.json"), encoding="utf-8"))["cases"]
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
