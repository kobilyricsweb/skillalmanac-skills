#!/usr/bin/env python3
"""Run the fixture cases in fixtures/cases.json against scripts/validate_config.py.

    python evals/run_fixtures.py

Reads fixtures; writes only into a temporary directory (one case writes a report there).
Exit 0 if every case matches, 1 otherwise.
"""
import contextlib
import io
import json
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "scripts"))
import validate_config  # noqa: E402

FIX = os.path.join(HERE, "fixtures")


def run_case(case, tmp):
    args = []
    for a in case["args"]:
        if a.startswith("TMP/"):
            args.append(os.path.join(tmp, a[4:]))
        elif not a.startswith("--") and os.path.exists(os.path.join(FIX, a)):
            args.append(os.path.join(FIX, a))
        else:
            args.append(a)
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = validate_config.main(args)
    problems = []
    if code != case["exit"]:
        problems.append("exit %r, wanted %r" % (code, case["exit"]))
    exp = case["expect"]
    if code == 2 and "error" in exp:
        try:
            got_error = json.loads(out.getvalue()).get("error")
        except ValueError:
            got_error = None
        if got_error != exp["error"]:
            problems.append("error: got %r, wanted %r" % (got_error, exp["error"]))
        return problems
    if not exp or code not in (0, 1):
        return problems
    text = out.getvalue()
    rep = json.loads(text)
    first = rep["files"][0]["errors"]
    got = {
        "findings": ["%s@%s" % (f["class"], f["line"] if f["line"] is not None else "-") for f in first],
        "summary": [rep["summary"]["errors"], rep["summary"]["warnings"]],
        "parsed": [f["parsed"] for f in rep["files"]],
        "masked_keys": sorted(m["key"] for m in rep["masked_values"]),
    }
    for key, want in exp.items():
        if key == "no_raw_secrets":
            for s in want:
                if s in text:
                    problems.append("raw secret leaked into output: " + s[:2] + "...")
        elif key == "report_written":
            path = os.path.join(tmp, "out.json")
            ok = os.path.isfile(path) and json.load(open(path, encoding="utf-8")) == rep
            if ok != want:
                problems.append("report_written: got %r" % ok)
        elif got.get(key) != want:
            problems.append("%s: got %r, wanted %r" % (key, got.get(key), want))
    return problems


def main():
    cases = json.load(open(os.path.join(FIX, "cases.json"), encoding="utf-8"))["cases"]
    failed = 0
    with tempfile.TemporaryDirectory() as tmp:
        for case in cases:
            problems = run_case(case, tmp)
            print(("PASS " if not problems else "FAIL ") + " ".join(case["args"]))
            for p in problems:
                print("    " + p)
            failed += bool(problems)
    print("%d/%d cases passed" % (len(cases) - failed, len(cases)))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
