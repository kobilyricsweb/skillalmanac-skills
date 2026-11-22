#!/usr/bin/env python3
"""Run the cases in fixtures/cases.json against scripts/validate_workflow.py.

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
import validate_workflow  # noqa: E402


def run_case(case):
    path = os.path.join(HERE, "fixtures", case["file"])
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        code = validate_workflow.main(["validate_workflow.py", path])
    problems = []
    if code != case["exit"]:
        problems.append(f"exit {code}, wanted {case['exit']}")
    try:
        rep = json.loads(out.getvalue())
    except ValueError:
        return problems + ["stdout is not a single JSON object"]
    if rep.get("ok") != case["ok"]:
        problems.append(f"ok {rep.get('ok')}, wanted {case['ok']}")
    if "fatal" in case:
        fatal = rep.get("fatal", "")
        if not fatal.startswith(case["fatal"].split(":")[0]):
            problems.append(f"fatal {fatal!r}, wanted {case['fatal']!r}")
        if case["file"] != "does_not_exist.json" and fatal != case["fatal"]:
            problems.append(f"fatal {fatal!r}, wanted {case['fatal']!r}")
    else:
        s = rep.get("summary", {})
        if s.get("errors") != case["errors"] or s.get("warnings") != case["warnings"]:
            problems.append(f"summary {s}, wanted errors={case['errors']} warnings={case['warnings']}")
        got = sorted(f["rule"] + ":" + f["severity"] for f in rep.get("findings", []))
        if got != sorted(case["findings"]):
            problems.append(f"findings {got}, wanted {sorted(case['findings'])}")
        raw = out.getvalue()
        for needle in ("k9x8w7v6u5t4s3r2", "q1w2e3r4t5y6", "AKIAABCDEFGHIJKLMNOP", "abcd1234efgh5678"):
            if needle in raw:
                problems.append("a secret value was echoed in the output")
    return problems


def main():
    cases = json.load(open(os.path.join(HERE, "fixtures", "cases.json"), encoding="utf-8"))["cases"]
    failed = 0
    for case in cases:
        problems = run_case(case)
        print(("PASS " if not problems else "FAIL ") + case["file"])
        for p in problems:
            print("    " + p)
        failed += bool(problems)
    print(f"{len(cases) - failed}/{len(cases)} cases passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
