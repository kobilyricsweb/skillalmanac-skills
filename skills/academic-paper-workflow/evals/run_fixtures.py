#!/usr/bin/env python3
"""Run the fixture cases in fixtures/cases.json against scripts/manuscript_check.py.

    python evals/run_fixtures.py

Reads fixtures; writes nothing. Exit 0 if every case matches, 1 otherwise.
"""
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "scripts"))
import manuscript_check  # noqa: E402

PATH_ARGS = 2  # the first two arguments are file names inside fixtures/


class FakeStdout:
    def __init__(self):
        self.buffer = io.BytesIO()


def run_case(case):
    args = list(case["args"])
    for i in range(PATH_ARGS):
        args[i] = os.path.join(HERE, "fixtures", args[i])
    fake, real = FakeStdout(), sys.stdout
    sys.stdout = fake
    try:
        code = manuscript_check.main(args)
    finally:
        sys.stdout = real
    rep = json.loads(fake.buffer.getvalue().decode("utf-8"))
    problems = []
    if code != case["exit"]:
        problems.append(f"exit {code}, wanted {case['exit']}")
    for key, want in case["expect"].items():
        if key == "uncited_numeric_claims_lines":
            got = [c["line"] for c in rep.get("uncited_numeric_claims", [])]
        elif key == "uncited_numeric_claims_numbers":
            got = [c["numbers"] for c in rep.get("uncited_numeric_claims", [])]
        elif key == "numeric_claims_covered_by_neighbour_lines":
            got = [c["line"] for c in rep.get("numeric_claims_covered_by_neighbour", [])]
        elif key == "error":
            got = rep.get("error", "").replace(HERE + os.sep + "fixtures" + os.sep, "")
        else:
            got = rep.get(key)
        if got != want:
            problems.append(f"{key}: got {got!r}, wanted {want!r}")
    return problems


def main():
    with open(os.path.join(HERE, "fixtures", "cases.json"), encoding="utf-8") as fh:
        cases = json.load(fh)["cases"]
    failed = 0
    for case in cases:
        problems = run_case(case)
        print(("PASS " if not problems else "FAIL ") + case["name"])
        for p in problems:
            print("    " + p)
        failed += bool(problems)
    print(f"{len(cases) - failed}/{len(cases)} cases passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
