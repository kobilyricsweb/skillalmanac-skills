#!/usr/bin/env python3
"""Run the fixture cases in fixtures/cases.json against scripts/eda_profile.py.

    python evals/run_fixtures.py

Reads fixtures; writes nothing. Exit 0 if every case matches, 1 otherwise.
A missing path counts as None, so "expect": {"x": null} asserts absence.
"""
import contextlib
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "scripts"))
import eda_profile  # noqa: E402


def lookup(report, path):
    cur = report
    for part in path.split("/"):
        if cur is None:
            return None
        if part.startswith("col:"):
            name = part[4:]
            cur = next((c for c in report["columns_detail"] if c["name"] == name), None)
        elif isinstance(cur, list):
            try:
                cur = cur[int(part)]
            except (ValueError, IndexError):
                return None
        elif isinstance(cur, dict):
            cur = cur.get(part)
        else:
            return None
    return cur


def run_case(case):
    args = [os.path.join(HERE, "fixtures", a) if a.endswith(".csv") else a for a in case["args"]]
    out = io.TextIOWrapper(io.BytesIO(), encoding="ascii")
    err = io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        try:
            code = eda_profile.main(args)
        except SystemExit as exc:
            code = exc.code
        out.flush()
    problems = []
    if code != case["exit"]:
        problems.append("exit %r, wanted %r" % (code, case["exit"]))
    if code in (0, 1) and case["expect"]:
        text = out.buffer.getvalue().decode("ascii")
        for bad in ("NaN", "Infinity"):
            if bad in text:
                problems.append("output contains " + bad)
        report = json.loads(text)
        for path, want in case["expect"].items():
            got = lookup(report, path)
            if got != want:
                problems.append("%s: got %r, wanted %r" % (path, got, want))
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
