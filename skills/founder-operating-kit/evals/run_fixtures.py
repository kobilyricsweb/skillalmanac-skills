#!/usr/bin/env python3
"""Run the fixture cases in fixtures/cases.json against scripts/founder_ops.py.

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
import founder_ops  # noqa: E402


class _Out(io.StringIO):
    """Collects what the script writes through sys.stdout.buffer."""

    def __init__(self):
        super().__init__()
        self.buffer = io.BytesIO()


def lookup(report, dotted):
    if dotted == "error_codes":
        return [e["code"] for e in report.get("errors", [])]
    if dotted == "warning_codes":
        return [e["code"] for e in report.get("warnings", [])]
    cur = report
    for part in dotted.split("."):
        if isinstance(cur, list):
            cur = cur[int(part)] if int(part) < len(cur) else None
        elif isinstance(cur, dict):
            cur = cur.get(part)
        else:
            return None
    return cur


def run_case(case):
    args = [os.path.join(HERE, "fixtures", a) if "." in a else a for a in case["args"]]
    out, err = _Out(), io.StringIO()
    real = sys.stdout
    sys.stdout = out
    try:
        with contextlib.redirect_stderr(err):
            code = founder_ops.main(args)
    finally:
        sys.stdout = real
    problems = []
    if code != case["exit"]:
        problems.append(f"exit {code}, wanted {case['exit']}")
    if case["expect"] and code in (0, 1):
        report = json.loads(out.buffer.getvalue().decode("utf-8"))
        for key, want in case["expect"].items():
            got = lookup(report, key)
            if got != want:
                problems.append(f"{key}: got {got!r}, wanted {want!r}")
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
    print(f"{len(cases) - failed}/{len(cases)} cases passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
