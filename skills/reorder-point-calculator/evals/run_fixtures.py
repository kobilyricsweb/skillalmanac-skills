#!/usr/bin/env python3
"""Run the cases in fixtures/cases.json against scripts/reorder_points.py.

    python evals/run_fixtures.py

Reads fixtures and writes nothing (the dry-run case checks that nothing is written).
Exit 0 if every case matches, 1 otherwise.
"""
import contextlib
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
FIX = os.path.join(HERE, "fixtures")
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "scripts"))
import reorder_points  # noqa: E402


def resolve(arg):
    if arg.endswith(".csv") or arg.endswith(".json"):
        return os.path.join(FIX, arg)
    return arg


def check_item(item, want, problems):
    for key, expected in want.items():
        got = item.get(key)
        if got != expected:
            problems.append(f"{item['item']}.{key}: got {got!r}, wanted {expected!r}")


def run_case(case):
    args = [resolve(a) for a in case["args"]]
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = reorder_points.main(args)
    problems = []
    if code != case["exit"]:
        problems.append(f"exit {code}, wanted {case['exit']}")
    exp = case["expect"]
    if "no_file" in exp and os.path.exists(os.path.join(FIX, exp["no_file"])):
        problems.append("dry run wrote a file")
    if code == 0 and exp.get("items") is not None or code == 0 and "summary" in exp:
        report = json.loads(out.getvalue(), parse_constant=lambda c: (_ for _ in ()).throw(ValueError(c)))
        if "as_of" in exp and report["as_of"] != exp["as_of"]:
            problems.append(f"as_of: got {report['as_of']!r}")
        if "summary" in exp and report["summary"] != exp["summary"]:
            problems.append(f"summary: got {report['summary']!r}, wanted {exp['summary']!r}")
        by_name = {i["item"]: i for i in report["items"]}
        for name, want in exp.get("items", {}).items():
            if name not in by_name:
                problems.append(f"missing item {name}")
            else:
                check_item(by_name[name], want, problems)
        for name, needles in exp.get("warning_contains", {}).items():
            text = " | ".join(by_name[name]["warnings"])
            for needle in needles:
                if needle not in text:
                    problems.append(f"{name}: warning containing {needle!r} not found")
    if code == 2 and not err.getvalue().strip():
        problems.append("exit 2 without a message on stderr")
    return problems


def main():
    with open(os.path.join(FIX, "cases.json"), encoding="utf-8") as fh:
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
