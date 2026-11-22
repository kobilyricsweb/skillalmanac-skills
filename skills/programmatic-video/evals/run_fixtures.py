#!/usr/bin/env python3
"""Run the fixture cases in fixtures/cases.json against scripts/timeline_check.py.

    python evals/run_fixtures.py

Reads fixtures. Creates empty placeholder asset files inside a temporary
directory (removed afterwards) so no media is stored in the package. Exit 0 if
every case matches, 1 otherwise.
"""
import contextlib
import io
import json
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "scripts"))
import timeline_check  # noqa: E402


def run_case(case):
    with tempfile.TemporaryDirectory() as root:
        for rel in case["touch"]:
            target = os.path.join(root, *rel.split("/"))
            os.makedirs(os.path.dirname(target), exist_ok=True)
            open(target, "w").close()
        args = [os.path.join(HERE, "fixtures", a) if a.endswith(".json") else a for a in case["args"]]
        args += ["--root", root]
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = timeline_check.main(args)
    problems = []
    if code != case["exit"]:
        problems.append("exit %s, wanted %s" % (code, case["exit"]))
    try:
        rep = json.loads(out.getvalue(), parse_constant=lambda c: (_ for _ in ()).throw(ValueError(c)))
    except ValueError as exc:
        return problems + ["stdout is not strict JSON: %s" % exc]
    got = {"ok": rep.get("ok"), "summary": rep.get("summary"),
           "codes": sorted(f["code"] for f in rep.get("findings", []))}
    for key, want in case["expect"].items():
        if got[key] != want:
            problems.append("%s: got %r, wanted %r" % (key, got[key], want))
    return problems


def main():
    cases = json.load(open(os.path.join(HERE, "fixtures", "cases.json"), encoding="utf-8"))["cases"]
    failed = 0
    for case in cases:
        problems = run_case(case)
        print(("PASS " if not problems else "FAIL ") + case["name"])
        for p in problems:
            print("    " + p)
        failed += bool(problems)
    print("%d/%d cases passed" % (len(cases) - failed, len(cases)))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
