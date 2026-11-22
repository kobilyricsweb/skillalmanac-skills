#!/usr/bin/env python3
"""Run the cases in fixtures/cases.json against scripts/clean_transcript.py.

    python evals/run_fixtures.py

Writes only into temporary folders. Exit 0 if every case matches, 1 otherwise.
Compares the exit code, selected fields of the JSON report and, where a case names
one, the cleaned file byte for byte against the hand-checked file in fixtures/.
"""
import contextlib
import io
import json
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
FIX = os.path.join(HERE, "fixtures")
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "scripts"))
import clean_transcript  # noqa: E402


def subset_problems(label, got, want):
    if isinstance(want, dict):
        out = []
        for k, v in want.items():
            out += subset_problems(label + "." + k, (got or {}).get(k) if isinstance(got, dict) else None, v)
        return out
    return [] if got == want else ["%s: got %r, wanted %r" % (label, got, want)]


def run_case(case):
    with tempfile.TemporaryDirectory() as tmp:
        args = []
        for a in case["args"]:
            a = a.replace("{out}", tmp)
            args.append(os.path.join(FIX, a[1:]) if a.startswith("@") else a)
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            try:
                code = clean_transcript.main(args)
            except SystemExit as exc:
                code = exc.code
        problems = []
        if code != case["exit"]:
            problems.append("exit %r, wanted %r" % (code, case["exit"]))
        if code in (0, 1) and case["expect"]:
            rep = json.loads(out.getvalue())
            exp = dict(case["expect"])
            view = dict(rep)
            view["mapping"] = rep["speakers"]["mapping"]
            view["ambiguous"] = rep["speakers"]["ambiguous"]
            view["after_counts"] = {k: v["count"] for k, v in rep["checks"].get("after", {}).items()}
            view["before_counts"] = rep["checks"].get("before_counts", {})
            for key, want in exp.items():
                problems += subset_problems(key, view.get(key), want)
        if "output" in case:
            path = os.path.join(tmp, case["output"]["name"])
            want_path = os.path.join(FIX, case["output"]["expected"])
            if not os.path.isfile(path):
                problems.append("no output file " + case["output"]["name"])
            else:
                if open(path, "rb").read() != open(want_path, "rb").read():
                    problems.append("output differs from " + case["output"]["expected"])
        if case.get("no_files") and os.listdir(tmp):
            problems.append("dry run wrote files: " + ", ".join(os.listdir(tmp)))
        return problems


def main():
    cases = json.load(open(os.path.join(FIX, "cases.json"), encoding="utf-8"))["cases"]
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
