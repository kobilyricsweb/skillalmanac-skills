#!/usr/bin/env python3
"""Run the fixture cases in fixtures/cases.json against scripts/prose_scan.py.

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
import prose_scan  # noqa: E402


def run_case(case):
    args = [os.path.join(HERE, "fixtures", a) if a.endswith(".md") else a for a in case["args"]]
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        try:
            code = prose_scan.main(args)
        except SystemExit as exc:
            code = exc.code
    problems = []
    if code != case["exit"]:
        problems.append(f"exit {code}, wanted {case['exit']}")
    exp = case["expect"]
    if exp and code in (0, 1):
        rep = json.loads(out.getvalue())
        got = {
            "verdict": rep.get("verdict"), "words": rep.get("words"), "sentences": rep.get("sentences"),
            "per_100_words": rep.get("per_100_words"), "counts_by_category": rep.get("counts_by_category"),
            "finding_lines": [f["line"] for f in rep.get("findings", [])] if rep.get("command") == "scan" else None,
            "ok": rep.get("ok"),
            "missing_numbers": rep.get("missing", {}).get("numbers"), "added_numbers": rep.get("added", {}).get("numbers"),
            "missing_urls": rep.get("missing", {}).get("urls"), "missing_quotes": rep.get("missing", {}).get("quotes"), "added_names": rep.get("added", {}).get("names"),
        }
        for key, want in exp.items():
            if got.get(key) != want:
                problems.append(f"{key}: got {got.get(key)!r}, wanted {want!r}")
    return problems


def main():
    cases = json.load(open(os.path.join(HERE, "fixtures", "cases.json"), encoding="utf-8"))["cases"]
    failed = 0
    for case in cases:
        problems = run_case(case)
        label = " ".join(case["args"])
        print(("PASS " if not problems else "FAIL ") + label)
        for p in problems:
            print("    " + p)
        failed += bool(problems)
    print(f"{len(cases) - failed}/{len(cases)} cases passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
