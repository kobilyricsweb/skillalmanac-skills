#!/usr/bin/env python3
"""Run the fixture cases in fixtures/cases.json against scripts/tracker_check.py.

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
import tracker_check  # noqa: E402

FIXTURE_SUFFIXES = (".csv", ".json")


def run_case(case):
    args = [os.path.join(HERE, "fixtures", a) if a.endswith(FIXTURE_SUFFIXES) else a for a in case["args"]]
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = tracker_check.main(args)
    problems = []
    if code != case["exit"]:
        problems.append("exit %r, wanted %r" % (code, case["exit"]))
    try:
        rep = json.loads(out.getvalue())
    except ValueError as exc:
        return problems + ["stdout is not strict JSON: %s" % exc]
    exp = case["expect"]
    got = {
        "ok": rep.get("ok"),
        "issue_counts": rep.get("summary", {}).get("issues"),
        "issue_codes": sorted(i["code"] for i in rep.get("issues", [])) if "issues" in rep else None,
        "plan_kinds": [p["kind"] for p in rep.get("weekly_plan", [])] if "weekly_plan" in rep else None,
        "first_plan_company": rep["weekly_plan"][0]["company"] if rep.get("weekly_plan") else None,
        "stale_subjects": [i["subject"] for i in rep.get("issues", []) if i["code"] == "stale_application"],
        "plan_has_kind_follow_up": any(p["kind"] == "follow_up" for p in rep.get("weekly_plan", [])),
    }
    for key, want in exp.items():
        if key == "error_contains":
            if want not in rep.get("error", ""):
                problems.append("error %r does not contain %r" % (rep.get("error"), want))
        elif got.get(key) != want:
            problems.append("%s: got %r, wanted %r" % (key, got.get(key), want))
    return problems


def main():
    with open(os.path.join(HERE, "fixtures", "cases.json"), encoding="utf-8") as handle:
        cases = json.load(handle)["cases"]
    failed = 0
    for case in cases:
        problems = run_case(case)
        print(("PASS " if not problems else "FAIL ") + case["name"])
        for p in problems:
            print("    " + p)
        failed += bool(problems)
    print("%d/%d cases passed" % (len(cases) - failed, len(cases)))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
