#!/usr/bin/env python3
"""Run the fixture cases in fixtures/cases.json against scripts/spec_trace.py.

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
import spec_trace  # noqa: E402


def resolve(arg):
    return os.path.join(HERE, "fixtures", arg) if arg.startswith("spec_") else arg


def run_case(case):
    args = [resolve(a) for a in case["args"]]
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        try:
            code = spec_trace.main(args)
        except SystemExit as exc:
            code = exc.code
    problems = []
    if code != case["exit"]:
        problems.append(f"exit {code}, wanted {case['exit']}")
    if code in (0, 1):
        rep = json.loads(out.getvalue())
        got = dict(rep)
        got["unknown_ids"] = [u["id"] for u in rep.get("unknown_in_tests", [])]
        got["open_marker_ids"] = sorted({o["id"] for o in rep.get("open_markers", [])})
        for key, want in case["expect"].items():
            if got.get(key) != want:
                problems.append(f"{key}: got {got.get(key)!r}, wanted {want!r}")
    elif case["expect"]:
        problems.append("expected JSON but the script exited with an error")
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
