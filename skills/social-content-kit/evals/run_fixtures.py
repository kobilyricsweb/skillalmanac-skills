#!/usr/bin/env python3
"""Run the fixture cases in fixtures/cases.json against scripts/calendar_check.py.

    python evals/run_fixtures.py

Reads fixtures; writes nothing. Also checks that the output is strict JSON.
Exit 0 if every case matches, 1 otherwise.
"""
import contextlib
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "scripts"))
import calendar_check  # noqa: E402


def strict_loads(text):
    def refuse(name):
        raise ValueError("non-standard JSON constant " + name)
    return json.loads(text, parse_constant=refuse)


def run_case(case):
    args = [os.path.join(HERE, "fixtures", a) if a.endswith((".json", ".csv")) else a for a in case["args"]]
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = calendar_check.main(args)
    problems = []
    if code != case["exit"]:
        problems.append(f"exit {code}, wanted {case['exit']}")
    if code in (0, 1):
        try:
            rep = strict_loads(out.getvalue())
        except ValueError as exc:
            return problems + [f"stdout is not strict JSON: {exc}"]
        got = {"ok": rep["ok"], "posts": rep["posts"], "errors": rep["errors"], "warnings": rep["warnings"],
               "codes": sorted(f"{f['severity']}:{f['code']}:{f['post_id']}" for f in rep["findings"])}
        for key, want in case["expect"].items():
            if got[key] != want:
                problems.append(f"{key}: got {got[key]!r}, wanted {want!r}")
    elif out.getvalue().strip():
        problems.append("stdout should be empty on exit 2")
    elif not err.getvalue().strip():
        problems.append("exit 2 needs a message on stderr")
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
    print(f"{len(cases) - failed}/{len(cases)} cases passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
