#!/usr/bin/env python3
"""Run the fixture cases in fixtures/cases.json against scripts/gorust_scan.py.

    python evals/run_fixtures.py

Reads fixtures; writes nothing. Exit 0 if every case matches, 1 otherwise.
"""
import contextlib
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
FIX = os.path.join(HERE, "fixtures")
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "scripts"))
import gorust_scan  # noqa: E402


def run_case(case):
    os.chdir(FIX)  # findings carry the path as given, so run from the fixtures folder
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        try:
            code = gorust_scan.main(case["args"])
        except SystemExit as exc:
            code = exc.code
    problems = []
    if code != case["exit"]:
        problems.append(f"exit {code}, wanted {case['exit']}")
    exp = case["expect"]
    if exp and code in (0, 1):
        rep = json.loads(out.getvalue())
        got = {
            "verdict": rep.get("verdict"),
            "files_scanned": rep.get("files_scanned"),
            "suppressed": rep.get("suppressed"),
            "counts_by_rule": rep.get("counts_by_rule"),
            "finding_lines": [[f["file"], f["line"], f["rule"]] for f in rep.get("findings", [])],
            "skipped": [s["file"] for s in rep.get("files_skipped", [])],
            "rule_count": len(rep.get("rules", [])) if rep.get("command") == "rules" else None,
        }
        for key, want in exp.items():
            if got.get(key) != want:
                problems.append(f"{key}: got {got.get(key)!r}, wanted {want!r}")
    if case.get("stderr_contains") and case["stderr_contains"] not in err.getvalue():
        problems.append(f"stderr lacks {case['stderr_contains']!r}")
    return problems


def main():
    with open(os.path.join(FIX, "cases.json"), encoding="utf-8") as fh:
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
