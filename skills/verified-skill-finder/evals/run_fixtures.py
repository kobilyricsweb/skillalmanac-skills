#!/usr/bin/env python3
"""Run the fixture cases in fixtures/cases.json against scripts/skill_scan.py.

    python evals/run_fixtures.py

Reads fixtures; writes nothing. An argument that starts with @ is a path
relative to the evals folder. Exit 0 if every case matches, 1 otherwise.
"""
import contextlib
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "scripts"))
import skill_scan  # noqa: E402


def run_case(case):
    args = [os.path.join(HERE, a[1:]) if a.startswith("@") else a for a in case["args"]]
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        try:
            code = skill_scan.main(args)
        except SystemExit as exc:
            code = exc.code
    problems = []
    if code != case["exit"]:
        problems.append("exit %r, wanted %r" % (code, case["exit"]))
    if code != 0 or not case["expect"]:
        return problems
    rep = json.loads(out.getvalue(), parse_constant=lambda c: (_ for _ in ()).throw(ValueError(c)))
    skills = rep["skills"]
    exp = case["expect"]
    got = {
        "query_terms": rep["query_terms"],
        "names": [s["name"] for s in skills],
        "scores": [s["score"] for s in skills],
        "scanned": rep["scanned"],
        "shown": rep["shown"],
        "duplicate_names": [d["name"] for d in rep["duplicates"]],
    }
    for key, want in exp.items():
        if key in got and got[key] != want:
            problems.append("%s: got %r, wanted %r" % (key, got[key], want))
    if "first_fields" in exp:
        for k, want in exp["first_fields"].items():
            if skills[0].get(k) != want:
                problems.append("first.%s: got %r, wanted %r" % (k, skills[0].get(k), want))
    for name, want in exp.get("excluded", {}).items():
        have = [s["excluded_by_description"] for s in skills if s["name"] == name]
        if have != [want]:
            problems.append("excluded[%s]: got %r, wanted %r" % (name, have, [want]))
    for name, want in exp.get("license_classes_of", {}).items():
        have = [s["license_class"] for s in skills if s["name"] == name]
        if have != want:
            problems.append("license_class[%s]: got %r, wanted %r" % (name, have, want))
    for name, frag in exp.get("issue_has", {}).items():
        issues = [i for s in skills if s["name"] == name for i in s["issues"]]
        if not any(frag in i for i in issues):
            problems.append("issues[%s] lack %r (got %r)" % (name, frag, issues))
    if "warning_has" in exp and not any(exp["warning_has"] in w for w in rep["warnings"]):
        problems.append("no warning containing %r" % exp["warning_has"])
    return problems


def main():
    with open(os.path.join(HERE, "fixtures", "cases.json"), encoding="utf-8") as fh:
        cases = json.load(fh)["cases"]
    failed = 0
    for case in cases:
        problems = run_case(case)
        label = " ".join(case["args"])
        print(("PASS " if not problems else "FAIL ") + label)
        for p in problems:
            print("    " + p)
        failed += bool(problems)
    print("%d/%d cases passed" % (len(cases) - failed, len(cases)))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
