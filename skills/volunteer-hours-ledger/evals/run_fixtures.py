#!/usr/bin/env python3
"""Run the fixture cases in fixtures/cases.json against scripts/volunteer_ledger.py.

    python evals/run_fixtures.py

Reads the fixtures. Writes only inside a temporary folder it creates and removes.
Checks the exit code, selected JSON fields, that protected input files are
byte-identical after a refused write, and that --output matches stdout.
Exit 0 if every case matches, 1 otherwise.
"""
import contextlib
import io
import json
import os
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
FIX = os.path.join(HERE, "fixtures")
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "scripts"))
import volunteer_ledger  # noqa: E402


def lookup(rep, path):
    if path == "flag_types":
        return sorted({f["type"] for p in rep["people"] for f in p["flags"]})
    if path == "rejected_reasons":
        return [r["reason"] for r in rep["rejected_rows"]]
    cur = rep
    for part in path.split("."):
        if isinstance(cur, list):
            cur = cur[int(part)]
        else:
            cur = cur[part]
    return cur


def run_case(case, tmp):
    args = []
    for a in case["args"]:
        if a.startswith("@tmp/"):
            args.append(os.path.join(tmp, a[5:]))
        elif a.startswith("@"):
            args.append(os.path.join(FIX, a[1:]))
        else:
            args.append(a)
    before = None
    if case.get("unchanged"):
        with open(os.path.join(FIX, case["unchanged"]), "rb") as fh:
            before = fh.read()
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        try:
            code = volunteer_ledger.main(args)
        except SystemExit as exc:
            code = exc.code
    problems = []
    if code != case["exit"]:
        problems.append("exit %r, wanted %r" % (code, case["exit"]))
    rep = None
    if code in (0, 1):
        rep = json.loads(out.getvalue())
        if rep.get("schema_version") != "1":
            problems.append("schema_version is not 1")
    for key, want in case["expect"].items():
        if rep is None:
            problems.append("no JSON to check %s" % key)
            continue
        try:
            got = lookup(rep, key)
        except (KeyError, IndexError, ValueError) as exc:
            problems.append("%s: cannot read (%r)" % (key, exc))
            continue
        if got != want:
            problems.append("%s: got %r, wanted %r" % (key, got, want))
    if before is not None:
        with open(os.path.join(FIX, case["unchanged"]), "rb") as fh:
            if fh.read() != before:
                problems.append("%s was modified" % case["unchanged"])
    if case.get("output_file_matches_stdout"):
        path = os.path.join(tmp, case["output_file_matches_stdout"])
        try:
            with open(path, encoding="utf-8") as fh:
                if json.load(fh) != rep:
                    problems.append("--output file differs from stdout")
        except (OSError, ValueError) as exc:
            problems.append("--output file unreadable: %r" % exc)
    return problems


def main():
    with open(os.path.join(FIX, "cases.json"), encoding="utf-8") as fh:
        cases = json.load(fh)["cases"]
    failed = 0
    tmp = tempfile.mkdtemp(prefix="vhl_fixtures_")
    try:
        for case in cases:
            problems = run_case(case, tmp)
            print(("PASS " if not problems else "FAIL ") + " ".join(case["args"]))
            for p in problems:
                print("    " + p)
            failed += bool(problems)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print("%d/%d cases passed" % (len(cases) - failed, len(cases)))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
