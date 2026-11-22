#!/usr/bin/env python3
"""Run the fixture cases in fixtures/cases.json against scripts/check_summary.py.

    python evals/run_fixtures.py

Reads fixtures; writes nothing. Exit 0 if every case matches, 1 otherwise.
"""
import contextlib
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
FIX = os.path.join(HERE, "fixtures")
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "scripts"))
import check_summary  # noqa: E402


def summarise(rep):
    return {
        "ok": rep.get("ok"),
        "ratio": rep.get("ratio"),
        "ratio_status": rep.get("target", {}).get("status"),
        "unsupported_texts": [u["text"] for u in rep.get("unsupported", [])],
        "altered": [a["summary"] for a in rep.get("altered_numbers", [])],
        "negation_sentences": [n["sentence"] for n in rep.get("negation_flips", [])],
        "hedge_sentences": [h["sentence"] for h in rep.get("hedge_drops", [])],
        "copied_count": len(rep.get("copied_spans", [])),
        "weak_or_unsupported_sentences": [s["sentence"] for s in rep.get("unsupported_sentences", [])],
        "keyword_coverage": rep.get("coverage", {}).get("keyword_coverage"),
    }


def run_case(case):
    args = [os.path.join(FIX, a) if a.endswith(".txt") else a for a in case["args"]]
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = check_summary.main(args)
    problems = []
    if code != case["exit"]:
        problems.append(f"exit {code}, wanted {case['exit']}")
    if case["expect"] and code in (0, 1):
        got = summarise(json.loads(out.getvalue()))
        for key, want in case["expect"].items():
            if got.get(key) != want:
                problems.append(f"{key}: got {got.get(key)!r}, wanted {want!r}")
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
