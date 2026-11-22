#!/usr/bin/env python3
"""Run the fixture cases in fixtures/cases.json against scripts/deal_check.py.

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
import deal_check  # noqa: E402


def run_case(case):
    args = [os.path.join(HERE, "fixtures", a) if a.endswith(".json") else a for a in case["args"]]
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        try:
            code = deal_check.main(args)
        except SystemExit as exc:
            code = exc.code
    problems = []
    if code != case["exit"]:
        problems.append("exit %r, wanted %r" % (code, case["exit"]))
    try:
        rep = json.loads(out.getvalue(), parse_constant=lambda c: (_ for _ in ()).throw(ValueError(c)))
    except ValueError as exc:
        return problems + ["stdout is not strict JSON: %s" % exc]
    rows = rep.get("rows", [])
    got = {
        "status": rep.get("status"),
        "counts": rep.get("counts"),
        "results": rep.get("results"),
        "flag_codes": sorted(f["code"] for f in rep.get("flags", rep.get("table_flags", []))),
        "row_cap_rates": [r["cap_rate"] for r in rows],
        "row_cash_on_cash": [r["cash_on_cash"] for r in rows],
        "row_dscr": [r["dscr"] for r in rows],
    }
    if "disclaimer" not in rep:
        problems.append("disclaimer missing from output")
    for key, want in case["expect"].items():
        if key == "flag_codes":
            want = sorted(want)
        if got.get(key) != want:
            problems.append("%s: got %r, wanted %r" % (key, got.get(key), want))
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
