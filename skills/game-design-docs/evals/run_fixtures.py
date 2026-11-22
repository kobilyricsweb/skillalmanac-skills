#!/usr/bin/env python3
"""Run the fixture cases in fixtures/cases.json against scripts/gdd_check.py.

    python evals/run_fixtures.py

Reads fixtures; writes nothing. Exit 0 if every case matches, 1 otherwise.
Also checks that stdout is a single strict JSON object (no NaN, no trailing text).
"""
import contextlib
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "scripts"))
import gdd_check  # noqa: E402


def strict_loads(text):
    def refuse(token):
        raise ValueError("non-standard JSON constant " + token)
    return json.loads(text, parse_constant=refuse)


def run_case(case):
    args = []
    for a in case["args"]:
        args.append(os.path.join(HERE, "fixtures", a) if a.endswith((".md", ".csv")) else a)
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = gdd_check.main(args)
    problems = []
    if code != case["exit"]:
        problems.append("exit %s, wanted %s" % (code, case["exit"]))
    try:
        rep = strict_loads(out.getvalue())
    except ValueError as exc:
        return problems + ["stdout is not strict JSON: %s" % exc]
    if rep.get("ok") != case["ok"]:
        problems.append("ok %r, wanted %r" % (rep.get("ok"), case["ok"]))
    if code != 2:
        got = sorted(f["code"] for f in rep.get("findings", []))
        if got != sorted(case["codes"]):
            problems.append("codes %s, wanted %s" % (got, sorted(case["codes"])))
    elif "error" not in rep:
        problems.append("exit 2 but no 'error' field in JSON")
    return problems


def main():
    with open(os.path.join(HERE, "fixtures", "cases.json"), encoding="utf-8") as fh:
        cases = json.load(fh)["cases"]
    failed = 0
    for case in cases:
        problems = run_case(case)
        print(("PASS " if not problems else "FAIL ") + case["name"])
        for p in problems:
            print("    " + p)
        failed += bool(problems)
    print("%d/%d cases passed" % (len(cases) - failed, len(cases)))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
