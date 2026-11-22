#!/usr/bin/env python3
"""Run the cases in fixtures/cases.json against scripts/size_model.py.

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
import size_model  # noqa: E402


def run_case(case):
    path = os.path.join(HERE, "fixtures", case["spec"])
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = size_model.main([path])
    problems = []
    if code != case["exit"]:
        problems.append(f"exit {code}, wanted {case['exit']}")
    if code not in (0, 1):
        if not err.getvalue().strip():
            problems.append("exit 2 without a message on stderr")
        return problems
    rep = json.loads(out.getvalue())
    for text in case.get("global_warnings_contain", []):
        if not any(text in w for w in rep["warnings"]):
            problems.append(f"global warning missing: {text!r}")
    for hw_i, text in case.get("hw_warnings_contain", []):
        if not any(text in w for w in rep["hardware"][hw_i]["warnings"]):
            problems.append(f"hardware[{hw_i}] warning missing: {text!r}")
    for hw_i, quant, text in case.get("row_warnings_contain", []):
        row = next(r for r in rep["hardware"][hw_i]["per_quant"] if r["quant"] == quant)
        if not any(text in w for w in row["warnings"]):
            problems.append(f"hardware[{hw_i}] {quant} warning missing: {text!r}")
    for hw_i, start in case.get("recommendation_starts", []):
        rec = rep["hardware"][hw_i]["recommendation"]
        if len(rec) != 3 or not rec[0].startswith(start):
            problems.append(f"recommendation[{hw_i}] wrong: {rec!r}")
    for want in case.get("rows", []):
        row = next(r for r in rep["hardware"][want["hw"]]["per_quant"] if r["quant"] == want["quant"])
        for key, val in want.items():
            if key in ("hw", "quant"):
                continue
            if row.get(key) != val:
                problems.append(f"hardware[{want['hw']}] {want['quant']} {key}: got {row.get(key)!r}, wanted {val!r}")
    return problems


def main():
    with open(os.path.join(HERE, "fixtures", "cases.json"), encoding="utf-8") as fh:
        cases = json.load(fh)["cases"]
    failed = 0
    for case in cases:
        problems = run_case(case)
        print(("PASS " if not problems else "FAIL ") + case["spec"])
        for p in problems:
            print("    " + p)
        failed += bool(problems)
    print(f"{len(cases) - failed}/{len(cases)} cases passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
