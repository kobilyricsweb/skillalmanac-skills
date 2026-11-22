#!/usr/bin/env python3
"""Run the fixture cases in fixtures/cases.json against scripts/alt_text_review.py.

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
import alt_text_review  # noqa: E402


def derive(rep):
    flags_by_line = {}
    for img in rep["images"]:
        if img["flags"]:
            flags_by_line.setdefault(str(img["line"]), []).extend(img["flags"])
    return {
        "images_total": rep["images_total"],
        "images_flagged": rep["images_flagged"],
        "needs_user_description": rep["needs_user_description"],
        "verdict": rep["verdict"],
        "counts_by_flag": rep["counts_by_flag"],
        "flags_by_line": {k: sorted(v) for k, v in flags_by_line.items()},
        "proposals_total": len(rep["proposals"]),
        "proposals_failing": sum(1 for p in rep["proposals"] if not p["ok"]),
        "proposal_flags": {p["src"]: sorted(p["flags"]) for p in rep["proposals"] if p["flags"]},
        "unmatched_descriptions": rep["unmatched_descriptions"],
    }


def run_case(case):
    args = []
    for a in case["args"]:
        cand = os.path.join(HERE, "fixtures", a)
        args.append(cand if (a.endswith((".html", ".md", ".json"))) else a)
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        try:
            code = alt_text_review.main(args)
        except SystemExit as exc:
            code = exc.code
    problems = []
    if code != case["exit"]:
        problems.append("exit %r, wanted %r" % (code, case["exit"]))
    if code in (0, 1) and case["expect"]:
        got = derive(json.loads(out.getvalue()))
        for key, want in case["expect"].items():
            if got.get(key) != want:
                problems.append("%s: got %r, wanted %r" % (key, got.get(key), want))
    if code == 2 and not err.getvalue().startswith("error:"):
        problems.append("exit 2 without a plain error message")
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
