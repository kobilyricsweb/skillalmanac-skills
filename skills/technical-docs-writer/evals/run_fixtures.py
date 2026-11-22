#!/usr/bin/env python3
"""Run the fixture cases in fixtures/cases.json against scripts/docs_audit.py.

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
import docs_audit  # noqa: E402


def run_case(case):
    args = []
    for a in case["args"]:
        cand = os.path.join(HERE, "fixtures", a)
        args.append(cand if os.path.exists(cand) else a)
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        try:
            code = docs_audit.main(args)
        except SystemExit as exc:
            code = exc.code
    problems = []
    if code != case["exit"]:
        problems.append("exit %r, wanted %r" % (code, case["exit"]))
    exp = case["expect"]
    if exp and code in (0, 1):
        rep = json.loads(out.getvalue())
        got = {
            "files_scanned": rep["files_scanned"], "ok": rep["ok"],
            "summary": {k: rep["summary"][k] for k in ("findings", "errors", "warnings", "by_rule")},
            "types": {f["path"]: [f["doc_type"], f["detected_by"]] for f in rep["files"]},
            "findings": {f["path"]: [[x["line"], x["rule"]] for x in f["findings"]] for f in rep["files"] if f["findings"]},
        }
        for key, want in exp.items():
            if key == "types":
                for path, pair in want.items():
                    if got["types"].get(path) != pair:
                        problems.append("type of %s: got %r, wanted %r" % (path, got["types"].get(path), pair))
            elif key == "findings":
                if got["findings"] != want:
                    problems.append("findings: got %r, wanted %r" % (got["findings"], want))
            elif got[key] != want:
                problems.append("%s: got %r, wanted %r" % (key, got[key], want))
    return problems


def main():
    cases = json.load(open(os.path.join(HERE, "fixtures", "cases.json"), encoding="utf-8"))["cases"]
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
