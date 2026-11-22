#!/usr/bin/env python3
"""Run the fixture cases in fixtures/cases.json against scripts/deck_check.py.

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
import deck_check  # noqa: E402


def no_constants(name):
    raise ValueError("non-strict JSON constant: " + name)


def derive(rep):
    """Flatten a report into the comparable fields used by cases.json."""
    got = dict(rep)
    got["finding_pairs"] = [[f["card"], f["check"]] for f in rep.get("findings", [])]
    if "sessions" in rep:
        got["session_dates"] = [s["date"] for s in rep["sessions"]]
        got["session_kinds"] = [s["kind"] for s in rep["sessions"]]
        got["session_gaps"] = [s["gap_days"] for s in rep["sessions"]]
    if "batches" in rep:
        got["batch_review_dates"] = [b["review_dates"] for b in rep["batches"]]
        got["batch_sizes"] = [b["cards"] for b in rep["batches"]]
        got["load"] = [[d["date"], d["new"], d["reviews"]] for d in rep["daily_load"]]
    return got


def run_case(case):
    args = [os.path.join(HERE, "fixtures", a) if a.startswith("deck_") else a for a in case["args"]]
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        try:
            code = deck_check.main(args)
        except SystemExit as exc:
            code = exc.code
    problems = []
    if code != case["exit"]:
        problems.append(f"exit {code}, wanted {case['exit']}")
    if code in (0, 1):
        try:
            rep = json.loads(out.getvalue(), parse_constant=no_constants)
        except ValueError as exc:
            return problems + [f"stdout is not strict JSON: {exc}"]
        got = derive(rep)
        for key, want in case["expect"].items():
            if got.get(key) != want:
                problems.append(f"{key}: got {got.get(key)!r}, wanted {want!r}")
    elif case.get("stderr_contains") and case["stderr_contains"] not in err.getvalue():
        problems.append(f"stderr {err.getvalue().strip()!r} lacks {case['stderr_contains']!r}")
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
    print(f"{len(cases) - failed}/{len(cases)} cases passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
