#!/usr/bin/env python3
"""Run the fixture cases in fixtures/cases.json against scripts/refactor_diff.py.

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
import refactor_diff  # noqa: E402


def dig(rep, dotted):
    cur = rep
    for part in dotted.split("."):
        cur = cur.get(part) if isinstance(cur, dict) else None
    return cur


def run_case(case):
    args = [os.path.join(HERE, "fixtures", a) if a.endswith(".py") else a for a in case["args"]]
    class Capture:
        """Stands in for sys.stdout; the script writes bytes to .buffer."""
        buffer = io.BytesIO()

    Capture.buffer = io.BytesIO()
    real_stdout = sys.stdout
    sys.stdout = Capture
    try:
        code = refactor_diff.main(args)
    except SystemExit as exc:
        code = exc.code
    finally:
        sys.stdout = real_stdout
    text = Capture.buffer.getvalue().decode("ascii")
    problems = []
    try:
        rep = json.loads(text)
    except ValueError:
        return ["stdout is not valid JSON: %r" % text[:80]]
    if code != case["exit"]:
        problems.append("exit %r, wanted %r" % (code, case["exit"]))
    if code == 2 and "error" not in rep:
        problems.append("exit 2 without an error field")
    rep["changed_signature_names"] = [c["name"] for c in rep.get("changed_signatures", [])]
    rep["breaking_names"] = [c["name"] for c in rep.get("changed_signatures", []) if c["breaking"]]
    for key, want in case["expect"].items():
        got = dig(rep, key)
        if got != want:
            problems.append("%s: got %r, wanted %r" % (key, got, want))
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
