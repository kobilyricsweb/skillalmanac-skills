#!/usr/bin/env python3
"""Run the fixture cases in fixtures/cases.json against scripts/check_outline.py.

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
import check_outline  # noqa: E402


def run_case(case):
    args = [os.path.join(HERE, "fixtures", a) if a.endswith(".json") else a for a in case["args"]]
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = check_outline.main(args)
    problems = []
    if code != case["exit"]:
        problems.append("exit %r, wanted %r" % (code, case["exit"]))
    exp = case["expect"]
    if exp and code in (0, 1):
        rep = json.loads(out.getvalue())
        summary = rep.get("summary", {})
        got = {
            "ok": rep.get("ok"),
            "errors": summary.get("errors"),
            "warnings": summary.get("warnings"),
            "planned_words": summary.get("planned_words"),
            "counts_by_code": rep.get("counts_by_code"),
        }
        if rep.get("command") == "budget":
            got["budgets"] = {b["beat"]: b["budget_words"] for b in rep["beats"]}
        if "defect_scenes" in exp:
            ds = {}
            for d in rep["defects"]:
                ds.setdefault(d["code"], []).append(d["scene_id"])
            got["defect_scenes"] = {k: sorted(ds.get(k, [])) for k in exp["defect_scenes"]}
        for key, want in exp.items():
            if got.get(key) != want:
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
