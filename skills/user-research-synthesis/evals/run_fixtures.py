#!/usr/bin/env python3
"""Run the fixture cases in fixtures/cases.json against scripts/synthesis_check.py.

    python evals/run_fixtures.py

Reads fixtures; writes nothing. Also checks that every output is strict JSON.
Exit 0 if every case matches, 1 otherwise.
"""
import contextlib
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "scripts"))
import synthesis_check  # noqa: E402


def strict_loads(text):
    def reject(name):
        raise ValueError("non-strict JSON constant " + name)
    return json.loads(text, parse_constant=reject)


def run_case(case):
    args = [os.path.join(HERE, "fixtures", a) if a.endswith(".json") else a for a in case["args"]]
    out = io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(io.StringIO()):
        try:
            code = synthesis_check.main(args)
        except SystemExit as exc:
            code = exc.code
    problems = []
    if code != case["exit"]:
        problems.append("exit %r, wanted %r" % (code, case["exit"]))
    try:
        rep = strict_loads(out.getvalue())
    except ValueError as exc:
        return problems + ["output is not strict JSON: %s" % exc]
    summary = rep.get("summary") or {}
    got = {
        "ok": rep.get("ok"),
        "errors": summary.get("errors"),
        "warnings": summary.get("warnings"),
        "untagged_notes": summary.get("untagged_notes"),
        "participants_never_cited": summary.get("participants_never_cited"),
        "codes": sorted(f["code"] for f in rep.get("findings", [])),
        "max_confidence": {t["id"]: t["max_confidence"] for t in rep.get("themes", [])},
    }
    for key, want in case["expect"].items():
        if key == "fatal_contains":
            if want not in rep.get("fatal", ""):
                problems.append("fatal %r lacks %r" % (rep.get("fatal"), want))
        elif got.get(key) != want:
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
