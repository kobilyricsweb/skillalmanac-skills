#!/usr/bin/env python3
"""Run the fixture cases in fixtures/cases.json against scripts/test_regex.py.

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
import test_regex  # noqa: E402


def summarize(rep):
    cases = rep.get("cases", [])
    probe = rep.get("probe", [])
    return {
        "verdict": rep.get("verdict"),
        "summary": rep.get("summary"),
        "static_flag_ids": [f["id"] for f in rep.get("static_flags", [])],
        "probe_verdicts": [p["verdict"] for p in probe],
        "review_kinds": [c["kind"] for c in cases if c["verdict"] == "review"],
        "skipped_kinds": [c["kind"] for c in cases if c["verdict"] == "skipped"],
        "search_only_inputs": [c["input"] for c in cases if "only because search" in c.get("note", "")],
        "failed_inputs": [c["input"] for c in cases if c["verdict"] == "fail"],
        "compile_ok": rep.get("compile", {}).get("ok"),
        "compile_error": rep.get("compile", {}).get("error"),
        "compile_position": rep.get("compile", {}).get("position"),
        "untestable_ids": [u["id"] for u in rep.get("untestable_constructs", [])],
    }


def run_case(case):
    args = [os.path.join(HERE, "fixtures", a) for a in case["args"]]
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        try:
            code = test_regex.main(args)
        except SystemExit as exc:
            code = exc.code
    problems = []
    if code != case["exit"]:
        problems.append("exit %r, wanted %r" % (code, case["exit"]))
    if case["expect"] and code in (0, 1):
        got = summarize(json.loads(out.getvalue()))
        for key, want in case["expect"].items():
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
