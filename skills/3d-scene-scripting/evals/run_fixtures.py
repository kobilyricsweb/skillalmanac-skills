#!/usr/bin/env python3
"""Run the cases in fixtures/cases.json against scripts/scene_check.py.

    python evals/run_fixtures.py

Reads fixtures; writes nothing. Exit 0 if every case matches, 1 otherwise.
Also checks that stdout is strict JSON (parsed with NaN and Infinity rejected).
"""
import contextlib
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "scripts"))
import scene_check  # noqa: E402


def _strict(name):
    raise ValueError("non-finite " + name)


def run_case(case):
    args = [os.path.join(HERE, "fixtures", a) for a in case["args"]]
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = scene_check.main(args)
    problems = []
    if code != case["exit"]:
        problems.append("exit %r, wanted %r" % (code, case["exit"]))
    if code in (0, 1):
        try:
            rep = json.loads(out.getvalue(), parse_constant=_strict)
        except ValueError as exc:
            return problems + ["stdout is not strict JSON: %s" % exc]
        got = {
            "ok": rep["ok"], "errors": rep["errors"], "warnings": rep["warnings"],
            "rules": [f["rule"] for f in rep["findings"]],
        }
        for key, want in case["expect"].items():
            if got.get(key) != want:
                problems.append("%s: got %r, wanted %r" % (key, got.get(key), want))
    elif not err.getvalue().strip():
        problems.append("exit 2 without a message on stderr")
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
