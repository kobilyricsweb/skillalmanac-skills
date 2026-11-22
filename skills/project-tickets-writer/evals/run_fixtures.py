#!/usr/bin/env python3
"""Run the cases in fixtures/cases.json against scripts/tickets_lint.py.

    python evals/run_fixtures.py

Reads fixtures; writes nothing. Exit 0 if every case matches, 1 otherwise.
Each case checks the exit code, ok, error and warning counts, the sorted
(severity, rule) counts and the build order.
"""
import contextlib
import io
import json
import os
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "scripts"))
import tickets_lint  # noqa: E402


def run_case(case):
    args = [os.path.join(HERE, "fixtures", a) if a.endswith((".md", ".json")) else a for a in case["args"]]
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        code = tickets_lint.main(args)
    problems = []
    if code != case["exit"]:
        problems.append("exit %s, wanted %s" % (code, case["exit"]))
    try:
        rep = json.loads(out.getvalue())
    except json.JSONDecodeError:
        return problems + ["stdout is not a single JSON object"]
    got = {"ok": rep.get("ok"), "errors": rep.get("errors"), "warnings": rep.get("warnings"),
           "ticket_count": rep.get("ticket_count"), "build_order": rep.get("build_order"),
           "rules": sorted("%s:%s=%d" % (s, r, n) for (s, r), n in
                           Counter((f["severity"], f["rule"]) for f in rep.get("findings", [])).items()),
           "has_input_error": "input_error" in rep}
    for key, want in case["expect"].items():
        if got.get(key) != want:
            problems.append("%s: got %r, wanted %r" % (key, got.get(key), want))
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
    print("%d/%d cases passed" % (len(cases) - failed, len(cases)))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
