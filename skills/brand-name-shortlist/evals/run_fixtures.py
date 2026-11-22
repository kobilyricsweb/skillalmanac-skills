#!/usr/bin/env python3
"""Run the fixture cases in fixtures/cases.json against scripts/score_names.py.

    python evals/run_fixtures.py

Reads fixtures; writes nothing. Also checks that the output is strict JSON (no NaN or
Infinity). Exit 0 if every case matches, 1 otherwise.
"""
import contextlib
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "scripts"))
import score_names  # noqa: E402

FILE_ARGS = (".txt", ".json")


def strict_loads(text):
    def refuse(token):
        raise ValueError(f"non-strict JSON constant {token}")
    return json.loads(text, parse_constant=refuse)


def run_case(case):
    args = [os.path.join(HERE, "fixtures", a) if a.endswith(FILE_ARGS) else a for a in case["args"]]
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = score_names.main(args)
    problems = []
    if code != case["exit"]:
        problems.append(f"exit {code}, wanted {case['exit']}")
    exp = case["expect"]
    if not exp or code not in (0, 1):
        return problems
    try:
        rep = strict_loads(out.getvalue())
    except ValueError as exc:
        return problems + [f"output is not strict JSON: {exc}"]
    by_name = {r["name"]: r for r in rep["ranking"]}
    checks = {
        "shortlist": [s["name"] for s in rep["shortlist"]],
        "shortfall": rep["shortlist_shortfall"],
        "near_duplicate_pairs": [[p["a"], p["b"], p["distance"]] for p in rep["near_duplicate_pairs"]],
    }
    for key in ("shortlist", "shortfall", "near_duplicate_pairs"):
        if key in exp and checks[key] != exp[key]:
            problems.append(f"{key}: got {checks[key]!r}, wanted {exp[key]!r}")
    for key, field in (("scores", "score"), ("verdicts", "verdict")):
        for name, want in exp.get(key, {}).items():
            got = by_name.get(name, {}).get(field)
            if got != want:
                problems.append(f"{key}[{name}]: got {got!r}, wanted {want!r}")
    for name, want in exp.get("flag_codes", {}).items():
        got = [f["code"] for f in by_name.get(name, {}).get("flags", [])]
        if got != want:
            problems.append(f"flag_codes[{name}]: got {got!r}, wanted {want!r}")
    for name, want in exp.get("domains", {}).items():
        got = by_name.get(name, {}).get("slugs", {}).get("domains")
        if got != want:
            problems.append(f"domains[{name}]: got {got!r}, wanted {want!r}")
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
