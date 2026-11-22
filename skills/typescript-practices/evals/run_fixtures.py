#!/usr/bin/env python3
"""Run the cases in fixtures/cases.json against scripts/ts_scan.py.

    python evals/run_fixtures.py

Reads fixtures; writes nothing. Also checks that stdout is one strict JSON
object (no NaN or Infinity, ASCII only). Exit 0 if every case matches, 1 otherwise.
"""
import contextlib
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "scripts"))
import ts_scan  # noqa: E402

FIXTURES = os.path.join(HERE, "fixtures")


def strict_loads(text):
    def refuse(name):
        raise ValueError("non-strict JSON constant " + name)
    return json.loads(text, parse_constant=refuse)


def run_case(case):
    args = []
    for a in case["args"]:
        path = os.path.join(FIXTURES, a)
        args.append(path if not a.startswith("--") and (os.path.exists(path) or a.endswith((".ts", ".tsx"))) else a)
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = ts_scan.main(args)
    problems = []
    if code != case["exit"]:
        problems.append("exit %r, wanted %r" % (code, case["exit"]))
    if code in (0, 1):
        text = out.getvalue()
        try:
            rep = strict_loads(text)
        except ValueError as exc:
            return problems + ["stdout is not strict JSON: %s" % exc]
        if not text.isascii():
            problems.append("stdout is not ASCII")
        got = {
            "total_findings": rep["total_findings"],
            "files_scanned": rep["files_scanned"],
            "pairs": sorted([f["line"], f["rule"]] for f in rep["findings"]),
            "suppressed_pairs": sorted([s["line"], s["rule"]] for s in rep["suppressed"]),
        }
        for key, want in case["expect"].items():
            if key in ("pairs", "suppressed_pairs"):
                want = sorted(want)
            if got[key] != want:
                problems.append("%s: got %r, wanted %r" % (key, got[key], want))
    elif not err.getvalue().strip():
        problems.append("exit 2 without a plain-text message on stderr")
    return problems


def main():
    cases = json.load(open(os.path.join(FIXTURES, "cases.json"), encoding="utf-8"))["cases"]
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
