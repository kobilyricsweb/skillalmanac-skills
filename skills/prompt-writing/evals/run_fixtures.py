#!/usr/bin/env python3
"""Run the fixture cases in fixtures/cases.json against scripts/prompt_lint.py.

    python evals/run_fixtures.py

Reads fixtures; writes nothing. Also checks that stdout is one strict JSON document.
Exit 0 if every case matches, 1 otherwise.
"""
import contextlib
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "scripts"))
import prompt_lint  # noqa: E402


def strict_loads(text):
    def refuse(token):
        raise ValueError("non-standard JSON constant " + token)
    return json.loads(text, parse_constant=refuse)


def run_case(case):
    args = [os.path.join(HERE, "fixtures", a) if a.endswith(".md") else a for a in case["args"]]
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        code = prompt_lint.main(args)
    problems = []
    if code != case["exit"]:
        problems.append("exit %r, wanted %r" % (code, case["exit"]))
    try:
        rep = strict_loads(out.getvalue())
    except ValueError as exc:
        return problems + ["stdout is not strict JSON: %s" % exc]
    if code == 2:
        if "error" not in rep:
            problems.append("exit 2 without an error field")
        return problems
    checks = rep.get("checks", [])
    got = {
        "verdict": rep.get("verdict"), "score": rep.get("score"), "passed": rep.get("passed"),
        "applicable": rep.get("applicable"), "placeholders": rep.get("placeholders"),
        "failed_checks": [c["id"] for c in checks if c["status"] == "fail"],
        "na_checks": [c["id"] for c in checks if c["status"] == "na"],
        "rules": sorted({f["rule"] for c in checks for f in c["findings"]}),
        "finding_lines": [f["line"] for c in checks for f in c["findings"] if f["line"] is not None],
    }
    for key, want in case["expect"].items():
        if got.get(key) != want:
            problems.append("%s: got %r, wanted %r" % (key, got.get(key), want))
    return problems


def main():
    with open(os.path.join(HERE, "fixtures", "cases.json"), encoding="utf-8") as handle:
        cases = json.load(handle)["cases"]
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
