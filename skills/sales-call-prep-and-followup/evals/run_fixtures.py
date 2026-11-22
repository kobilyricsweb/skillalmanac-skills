#!/usr/bin/env python3
"""Run the cases in fixtures/cases.json against scripts/call_check.py.

    python evals/run_fixtures.py

Reads fixtures; writes nothing. Exit 0 if every case matches, 1 otherwise.
Also checks that every report is strict JSON (no NaN) and that the missing-file
error starts with the expected text.
"""
import contextlib
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "scripts"))
import call_check  # noqa: E402

FIX = os.path.join(HERE, "fixtures")


def strict_loads(text):
    def bad(const):
        raise ValueError("non-strict constant " + const)
    return json.loads(text, parse_constant=bad)


def run_case(case):
    args = []
    for a in case["args"]:
        path = os.path.join(FIX, a)
        args.append(path if (a.endswith((".md", ".json")) and not a.startswith("--")) else a)
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        code = call_check.main(args)
    problems = []
    if code != case["exit"]:
        problems.append("exit %s, wanted %s" % (code, case["exit"]))
    try:
        rep = strict_loads(out.getvalue())
    except ValueError as exc:
        return problems + ["output is not strict JSON: %s" % exc]
    exp = case["expect"]
    findings = rep.get("findings", [])
    got = {
        "ok": rep.get("ok"),
        "coverage_score": rep.get("coverage_score"),
        "unanswered_fields": rep.get("unanswered_fields"),
        "followup_checked": rep.get("followup_checked"),
        "error_codes": sorted({f["code"] for f in findings if f["severity"] == "error"}),
        "warn_codes": sorted({f["code"] for f in findings if f["severity"] == "warn"}),
        "figures": sorted(f["figure"] for f in findings if f["code"] == "figure_not_in_notes"),
        "commitment_lines": sorted(f["line"] for f in findings if f["code"] == "commitment_not_in_notes"),
    }
    for key, want in exp.items():
        if key == "error":
            if not str(rep.get("error", "")).startswith(want):
                problems.append("error: got %r, wanted prefix %r" % (rep.get("error"), want))
            continue
        if key in ("figures", "commitment_lines"):
            want = sorted(want)
        if key in ("error_codes", "warn_codes"):
            want = sorted(want)
        if got.get(key) != want:
            problems.append("%s: got %r, wanted %r" % (key, got.get(key), want))
    return problems


def main():
    with open(os.path.join(FIX, "cases.json"), encoding="utf-8") as fh:
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
