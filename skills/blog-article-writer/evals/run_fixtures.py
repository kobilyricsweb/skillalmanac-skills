#!/usr/bin/env python3
"""Run the fixture cases in fixtures/cases.json against scripts/article_audit.py.

    python evals/run_fixtures.py

Reads fixtures; writes nothing. Exit 0 if every case matches, 1 otherwise.
Each case lists the arguments (file names are resolved inside evals/fixtures/),
the expected exit code, and expected values: dotted paths into the JSON output,
plus "rules", the sorted rule ids of all findings.
"""
import contextlib
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "scripts"))
import article_audit  # noqa: E402


def resolve(args):
    out = []
    for a in args:
        p = os.path.join(HERE, "fixtures", a)
        out.append(p if a.endswith(".md") else a)
    return out


def dig(obj, path):
    for part in path.split("."):
        obj = obj[part]
    return obj


def run_case(case):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        try:
            code = article_audit.main(resolve(case["args"]))
        except SystemExit as exc:
            code = exc.code
    problems = []
    if code != case["exit"]:
        problems.append("exit %r, wanted %r" % (code, case["exit"]))
    try:
        rep = json.loads(out.getvalue())
    except ValueError:
        return problems + ["stdout is not a single JSON object"]
    for key, want in case["expect"].items():
        if key == "rules":
            got = sorted(f["rule"] for f in rep.get("findings", []))
        else:
            try:
                got = dig(rep, key)
            except (KeyError, TypeError):
                got = "<missing>"
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
