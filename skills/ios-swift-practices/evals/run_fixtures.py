#!/usr/bin/env python3
"""Run the fixture cases in fixtures/cases.json against scripts/swift_scan.py.

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
import swift_scan  # noqa: E402


def run_case(case):
    args = [os.path.join(HERE, "fixtures", a) if a.endswith(".swift") else a for a in case["args"]]
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        try:
            code = swift_scan.main(args)
        except SystemExit as exc:
            code = exc.code
    problems = []
    if code != case["exit"]:
        problems.append("exit %r, wanted %r" % (code, case["exit"]))
    try:
        rep = json.loads(out.getvalue())
    except ValueError:
        return problems + ["stdout is not strict JSON"]
    exp = case["expect"]
    if code in (0, 1) and exp:
        pf = rep["per_file"][0] if rep.get("per_file") else {}
        dens = [f for f in rep["findings"] if f["rule"] == "force-unwrap-density"]
        bod = [f for f in rep["findings"] if f["rule"] == "giant-view-body"]
        got = {
            "total_findings": rep["total_findings"],
            "counts_by_rule": rep["counts_by_rule"],
            "findings": [[f["line"], f["rule"], f["severity"]] for f in rep["findings"]],
            "force_unwraps": pf.get("force_unwraps"),
            "code_lines": pf.get("code_lines"),
            "force_per_100": pf.get("force_unwraps_per_100_lines"),
            "test_files_skipped_for_rules": rep["test_files_skipped_for_rules"],
            "density_lines": dens[0]["lines"] if dens else None,
            "body_lines": bod[0]["body_lines"] if bod else None,
        }
        for key, want in exp.items():
            if got.get(key) != want:
                problems.append("%s: got %r, wanted %r" % (key, got.get(key), want))
    if code == 2 and "error" not in rep:
        problems.append("exit 2 without an error key")
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
