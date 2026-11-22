#!/usr/bin/env python3
"""Run the fixture cases in fixtures/cases.json against scripts/ledger_check.py.

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
import ledger_check  # noqa: E402


def run_case(case):
    args = [os.path.join(HERE, "fixtures", a) for a in case["args"]]
    out = io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(io.StringIO()):
        try:
            code = ledger_check.main(args)
        except SystemExit as exc:
            code = exc.code
    problems = []
    if code != case["exit"]:
        problems.append("exit %r, wanted %r" % (code, case["exit"]))
    try:
        rep = json.loads(out.getvalue(), parse_constant=lambda c: (_ for _ in ()).throw(ValueError(c)))
    except ValueError as exc:
        return problems + ["stdout is not strict JSON: %s" % exc]
    got = dict(rep)
    got["codes"] = sorted({f["code"] for f in rep.get("findings", []) if f["severity"] == "error"})
    got["warning_codes"] = sorted({f["code"] for f in rep.get("findings", []) if f["severity"] == "warning"})
    for key, want in case["expect"].items():
        if got.get(key) != want:
            problems.append("%s: got %r, wanted %r" % (key, got.get(key), want))
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
