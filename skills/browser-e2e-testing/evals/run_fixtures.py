#!/usr/bin/env python3
"""Run the fixture cases in fixtures/cases.json against scripts/audit_e2e.py.

    python evals/run_fixtures.py

Reads fixtures; writes nothing. Arguments ending in .spec.ts or .py are resolved
inside evals/fixtures. Exit 0 if every case matches, 1 otherwise.
"""
import contextlib
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "scripts"))
import audit_e2e  # noqa: E402


def run_case(case):
    args = [os.path.join(HERE, "fixtures", a) if a.endswith((".ts", ".py", ".js")) else a for a in case["args"]]
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        try:
            code = audit_e2e.main(args)
        except SystemExit as exc:
            code = exc.code
    problems = []
    if code != case["exit"]:
        problems.append("exit %r, wanted %r" % (code, case["exit"]))
    if code in (0, 1) and case["expect"]:
        rep = json.loads(out.getvalue())
        rep["finding_keys"] = ["%d %s" % (f["line"], f["rule"]) for f in rep["findings"]]
        for key, want in case["expect"].items():
            if rep.get(key) != want:
                problems.append("%s: got %r, wanted %r" % (key, rep.get(key), want))
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
