#!/usr/bin/env python3
"""Run the fixture cases in fixtures/cases.json against scripts/lp_audit.py.

    python evals/run_fixtures.py

Reads fixtures; writes nothing. Exit 0 if every case matches, 1 otherwise.
A case lists CLI args (file names resolve under evals/fixtures/, or relative to evals/), the
expected exit code, and the JSON fields to compare.
"""
import contextlib
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "scripts"))
import lp_audit  # noqa: E402


def resolve(name):
    """A draft name is looked up in evals/fixtures/ first, then relative to evals/."""
    path = os.path.join(HERE, "fixtures", name)
    return path if os.path.exists(path) or "/" not in name else os.path.join(HERE, name)


def run_case(case):
    args = [resolve(a) if a.endswith((".md", ".html")) else a for a in case["args"]]
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        try:
            code = lp_audit.main(args)
        except SystemExit as exc:
            code = exc.code
    problems = []
    if code != case["exit"]:
        problems.append("exit %r, wanted %r" % (code, case["exit"]))
    exp = case["expect"]
    if exp and code in (0, 1):
        rep = json.loads(out.getvalue())
        got = {
            "verdict": rep["verdict"], "counts": rep["counts"],
            "roles": [s["role"] for s in rep["sections"]],
            "rules": [[f["line"], f["rule"]] for f in rep["findings"]],
            "stats": {k: rep["stats"].get(k) for k in exp.get("stats", {})},
        }
        for key, want in exp.items():
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
