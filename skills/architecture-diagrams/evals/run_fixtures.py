#!/usr/bin/env python3
"""Run the cases in fixtures/cases.json against scripts/mermaid_check.py.

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
import mermaid_check  # noqa: E402


def run_case(case):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = mermaid_check.main([os.path.join(HERE, "fixtures", case["file"])])
    problems = []
    if code != case["exit"]:
        problems.append("exit %s, wanted %s" % (code, case["exit"]))
    if code in (0, 1):
        rep = json.loads(out.getvalue())
        if rep["verdict"] != case["verdict"]:
            problems.append("verdict %s, wanted %s" % (rep["verdict"], case["verdict"]))
        if len(rep["diagrams"]) != len(case["diagrams"]):
            problems.append("%d diagrams, wanted %d" % (len(rep["diagrams"]), len(case["diagrams"])))
        for got, want in zip(rep["diagrams"], case["diagrams"]):
            have = {
                "type": got["type"], "nodes": got["metrics"]["nodes"], "edges": got["metrics"]["edges"],
                "codes": sorted({f["code"] for f in got["findings"]}),
                "orphans": got["orphans"], "duplicate_ids": got["duplicate_ids"],
            }
            for key, value in want.items():
                if have[key] != value:
                    problems.append("%s: got %r, wanted %r" % (key, have[key], value))
    elif not err.getvalue().strip():
        problems.append("exit 2 without a message on stderr")
    return problems


def main():
    with open(os.path.join(HERE, "fixtures", "cases.json"), encoding="utf-8") as fh:
        cases = json.load(fh)["cases"]
    failed = 0
    for case in cases:
        problems = run_case(case)
        print(("PASS " if not problems else "FAIL ") + case["file"])
        for p in problems:
            print("    " + p)
        failed += bool(problems)
    print("%d/%d cases passed" % (len(cases) - failed, len(cases)))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
