#!/usr/bin/env python3
"""Run the fixture cases in fixtures/cases.json against scripts/test_audit.py.

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
import test_audit  # noqa: E402


def run_case(case):
    args = [os.path.join(HERE, "fixtures", a) if "." in a and not a.startswith("-") else a for a in case["args"]]
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        try:
            code = test_audit.main(args)
        except SystemExit as exc:
            code = exc.code
    problems = []
    if code != case["exit"]:
        problems.append("exit %r, wanted %r" % (code, case["exit"]))
    try:
        rep = json.loads(out.getvalue())
    except ValueError:
        return problems + ["stdout is not valid JSON"]
    got = {"ok": rep.get("ok"), "has_error": "error" in rep}
    if "summary" in rep:
        s = rep["summary"]
        got.update(tests=s["tests"], errors=s["errors"], warnings=s["warnings"], skipped=s["skipped"])
        got["findings"] = sorted([f["rule"], f["line"]] for f in rep["findings"])
    for key, want in case["expect"].items():
        have = got.get(key)
        if key == "findings":
            want = sorted(want)
        if have != want:
            problems.append("%s: got %r, wanted %r" % (key, have, want))
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
    print("%d/%d cases passed" % (len(cases) - failed, len(cases)))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
