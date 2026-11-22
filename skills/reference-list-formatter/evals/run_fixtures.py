#!/usr/bin/env python3
"""Run the fixture cases in fixtures/cases.json against scripts/format_refs.py.

    python evals/run_fixtures.py

Reads fixtures; writes nothing. Exit 0 if every case matches, 1 otherwise.
Each case lists the command line, the wanted exit code and the JSON fields to compare
(summary, references, entry statuses, missing fields, duplicates).
"""
import contextlib
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "scripts"))
import format_refs  # noqa: E402


def run_case(case):
    args = [os.path.join(HERE, "fixtures", a) if a.endswith((".bib", ".json")) else a for a in case["args"]]
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = format_refs.main(args)
    problems = []
    if code != case["exit"]:
        problems.append(f"exit {code}, wanted {case['exit']}")
    if code in (0, 1) and case.get("expect"):
        rep = json.loads(out.getvalue())
        got = {
            "summary": rep.get("summary"),
            "references": rep.get("references"),
            "statuses": {e["id"]: e["status"] for e in rep.get("entries", [])},
            "missing": {e["id"]: e["missing_required"] for e in rep.get("entries", []) if e["missing_required"]},
            "duplicates": rep.get("duplicates"),
            "in_text": {e["id"]: e["in_text"] for e in rep.get("entries", [])},
        }
        for key, want in case["expect"].items():
            if got.get(key) != want:
                problems.append(f"{key}: got {got.get(key)!r}, wanted {want!r}")
    if code == 2 and "stderr_has" in case and case["stderr_has"] not in err.getvalue():
        problems.append("stderr did not contain " + repr(case["stderr_has"]))
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
    print(f"{len(cases) - failed}/{len(cases)} cases passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
