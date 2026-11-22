#!/usr/bin/env python3
"""Run the fixture cases in fixtures/cases.json against scripts/svg_poster_audit.py.

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
import svg_poster_audit  # noqa: E402


def run_case(case):
    args = [os.path.join(HERE, "fixtures", a) if a.endswith(".svg") else a for a in case["args"]]
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        code = svg_poster_audit.main(args)
    problems = []
    if code != case["exit"]:
        problems.append("exit %s, wanted %s" % (code, case["exit"]))
    try:
        rep = json.loads(out.getvalue())
    except ValueError:
        return problems + ["stdout is not one JSON object"]
    if code == 2:
        if "error" not in rep:
            problems.append("exit 2 without an error field")
        return problems
    findings = rep.get("findings", [])
    got = {
        "verdict": rep.get("verdict"),
        "summary": rep.get("summary"),
        "fail_checks": sorted({f["check"] for f in findings if f["severity"] == "fail"}),
        "warn_checks": sorted({f["check"] for f in findings if f["severity"] == "warn"}),
        "ratios": [c.get("ratio") for c in rep.get("contrast", [])],
        "sizes": rep.get("text", {}).get("sizes_distinct"),
        "statuses": [c.get("status") for c in rep.get("contrast", [])],
        "limits_contain": [w for w in case["expect"].get("limits_contain", []) if any(w in l for l in rep.get("limits", []))],
    }
    for key, want in case["expect"].items():
        if got.get(key) != want:
            problems.append("%s: got %r, wanted %r" % (key, got.get(key), want))
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
