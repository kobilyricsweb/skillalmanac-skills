#!/usr/bin/env python3
"""Run the cases in fixtures/cases.json against scripts/schedule_conflicts.py.

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
import schedule_conflicts  # noqa: E402

FILE_SUFFIXES = (".csv", ".ics", ".json")


def short(rep):
    return {
        "summary": rep.get("summary"),
        "conflicts_short": [f"{c['type']}:{'+'.join(c['ids'])}" for c in rep.get("conflicts", [])],
        "unassigned": [f"{u['id']}:{u['missing']}" for u in rep.get("unassigned", [])],
        "rejected": [f"{r['id']}:{r['reason']}" for r in rep.get("rejected_rows", [])],
        "skipped": [f"{s['id']}:{s['reason']}" for s in rep.get("skipped", [])],
        "moves_short": [f"{m['id']}->{m['to_start']}" for m in rep.get("suggested_moves", [])],
        "unmovable": [f"{u['type']}:{'+'.join(u['ids'])}" for u in rep.get("unmovable", [])],
        "remaining_after_moves": rep.get("remaining_after_moves"),
        "free_slots": rep.get("free_slots"),
    }


def run_case(case):
    args = [os.path.join(HERE, "fixtures", a) if a.endswith(FILE_SUFFIXES) else a for a in case["args"]]
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        try:
            code = schedule_conflicts.main(args)
        except SystemExit as exc:
            code = exc.code
    problems = []
    if code != case["exit"]:
        problems.append(f"exit {code}, wanted {case['exit']}")
    if code in (0, 1):
        got = short(json.loads(out.getvalue()))
        for key, want in case["expect"].items():
            if got.get(key) != want:
                problems.append(f"{key}: got {got.get(key)!r}, wanted {want!r}")
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
