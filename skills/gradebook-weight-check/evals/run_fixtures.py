#!/usr/bin/env python3
"""Run the fixture cases in fixtures/cases.json against scripts/gradebook_check.py.

    python evals/run_fixtures.py

Reads fixtures; writes nothing (the cases that pass --out are all refusals).
Also checks that no student name from the fixture CSV files appears in any
output. Exit 0 if every case matches, 1 otherwise.
"""
import contextlib
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
FIX = os.path.join(HERE, "fixtures")
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "scripts"))
import gradebook_check  # noqa: E402


def resolve(arg):
    return os.path.join(FIX, arg[3:]) if arg.startswith("fx:") else arg


def extract(rep):
    students = rep.get("students", [])
    flag_counts = rep.get("flag_counts", {})
    what_if = rep.get("what_if")
    return {
        "scheme_ok": rep.get("scheme_ok"),
        "finals": {s["student_id"]: s["final"] for s in students},
        "letters": {s["student_id"]: s["letter"] for s in students},
        "provisional_ids": [s["student_id"] for s in students if s["provisional"]],
        "boundary_ids": [b["student_id"] for b in rep.get("boundary_cases", [])],
        "mismatch_ids": [m["student_id"] for m in rep.get("mismatches_with_expected", [])],
        "explained_by": {m["student_id"]: m["explained_by_missing_policy"] for m in rep.get("mismatches_with_expected", [])},
        "flag_counts": flag_counts,
        "unmapped_columns": rep.get("unmapped_columns"),
        "expected_compared": rep.get("expected_compared"),
        "duplicate_ids": {d["student_id"]: d["rows"] for d in rep.get("duplicate_ids", [])},
        "blank_id_rows": rep.get("blank_id_rows"),
        "students_total": rep.get("students_total"),
        "problem_codes": sorted({p["code"] for p in rep.get("scheme_problems", [])}),
        "what_if": {w["student_id"]: {"needed_score": w["needed_score"], "feasible": w["feasible"]} for w in what_if["students"]} if what_if else None,
    }


def subset(want, got):
    """Every key in `want` must match in `got`; dicts are compared key by key for the listed keys only."""
    if isinstance(want, dict) and isinstance(got, dict):
        return all(k in got and subset(v, got[k]) for k, v in want.items())
    return want == got


def run_case(case, banned):
    args = [resolve(a) for a in case["args"]]
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = gradebook_check.main(args)
    problems = []
    if code != case["exit"]:
        problems.append("exit %s, wanted %s" % (code, case["exit"]))
    for name in banned:
        if name in out.getvalue() or name in err.getvalue():
            problems.append("student name %r leaked into the output" % name)
    exp = dict(case["expect"])
    needle = exp.pop("stderr_contains", None)
    if needle and needle not in err.getvalue():
        problems.append("stderr lacks %r: %r" % (needle, err.getvalue().strip()))
    if exp and code in (0, 1):
        got = extract(json.loads(out.getvalue()))
        for key, want in exp.items():
            if not subset(want, got.get(key)):
                problems.append("%s: got %r, wanted %r" % (key, got.get(key), want))
    return problems


def main():
    with open(os.path.join(FIX, "cases.json"), encoding="utf-8") as fh:
        data = json.load(fh)
    failed = 0
    for case in data["cases"]:
        problems = run_case(case, data["never_in_output"])
        print(("PASS " if not problems else "FAIL ") + case["name"])
        for p in problems:
            print("    " + p)
        failed += bool(problems)
    print("%d/%d cases passed" % (len(data["cases"]) - failed, len(data["cases"])))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
