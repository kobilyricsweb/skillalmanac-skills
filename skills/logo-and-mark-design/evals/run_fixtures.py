#!/usr/bin/env python3
"""Run the fixture cases in fixtures/cases.json against scripts/logo_audit.py.

    python evals/run_fixtures.py

Reads fixtures; writes nothing. Also checks that every output is strict JSON
(no NaN or Infinity). Exit 0 if every case matches, 1 otherwise.
"""
import contextlib
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "scripts"))
import logo_audit  # noqa: E402


def strict_loads(text):
    def refuse(name):
        raise ValueError("non-strict JSON constant " + name)
    return json.loads(text, parse_constant=refuse)


def dig(obj, dotted):
    for part in dotted.split("."):
        if not isinstance(obj, dict) or part not in obj:
            return None
        obj = obj[part]
    return obj


def run_case(case):
    args = [os.path.join(HERE, "fixtures", a) if a.endswith(".svg") else a for a in case["args"]]
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        try:
            code = logo_audit.main(args)
        except SystemExit as exc:
            code = exc.code
    problems = []
    if code != case["exit"]:
        problems.append("exit %r, wanted %r" % (code, case["exit"]))
    try:
        rep = strict_loads(out.getvalue())
    except ValueError as exc:
        return problems + ["output is not strict JSON: %s" % exc]
    for key, want in case["expect"].items():
        if key == "finding_codes":
            got = [f["code"] for f in rep.get("findings", [])]
        elif key == "error_present":
            got = "error" in rep
        else:
            got = dig(rep, key)
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
