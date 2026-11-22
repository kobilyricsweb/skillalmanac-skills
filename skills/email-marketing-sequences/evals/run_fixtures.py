#!/usr/bin/env python3
"""Run the fixture cases in fixtures/cases.json against scripts/sequence_check.py.

    python evals/run_fixtures.py

Reads fixtures; writes nothing. Exit 0 if every case matches, 1 otherwise.
Each case: args (a .json argument is resolved inside fixtures/), exit code, and expected
fields: ok, summary, codes (list of "LEVEL code email" strings, compared in order),
timeline_days, error_contains.
"""
import contextlib
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "scripts"))
import sequence_check  # noqa: E402


def run_case(case):
    args = [os.path.join(HERE, "fixtures", a) if a.endswith(".json") else a for a in case["args"]]
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = sequence_check.main(args)
    problems = []
    if code != case["exit"]:
        problems.append("exit %r, wanted %r" % (code, case["exit"]))
    try:
        rep = json.loads(out.getvalue(), parse_constant=lambda c: (_ for _ in ()).throw(ValueError(c)))
    except ValueError as exc:
        return problems + ["stdout is not strict JSON: %s" % exc]
    exp = case["expect"]
    got = {
        "ok": rep.get("ok"),
        "summary": rep.get("summary"),
        "codes": ["%s %s %s" % (f["level"], f["code"], f.get("email", "-")) for f in rep.get("findings", [])],
        "timeline_days": [t["day"] for t in rep.get("timeline", [])],
        "error_contains": rep.get("error"),
    }
    for key, want in exp.items():
        have = got.get(key)
        if key == "error_contains":
            if not isinstance(have, str) or want not in have:
                problems.append("error: got %r, wanted text %r" % (have, want))
        elif have != want:
            problems.append("%s: got %r, wanted %r" % (key, have, want))
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
