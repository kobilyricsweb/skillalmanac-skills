#!/usr/bin/env python3
"""Run the cases in fixtures/cases.json against scripts/csv_version_diff.py.

    python evals/run_fixtures.py

Reads the fixtures, writes only inside a temporary directory it removes at the
end. Cases marked "unchanged" prove that an input file is byte-identical after a
refused write. Exit 0 if every case matches, 1 otherwise.
"""
import contextlib
import hashlib
import io
import json
import os
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
FIX = os.path.join(HERE, "fixtures")
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "scripts"))
import csv_version_diff  # noqa: E402


def sha(path):
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def dig(obj, dotted):
    for part in dotted.split("."):
        if not isinstance(obj, dict) or part not in obj:
            return "<missing>"
        obj = obj[part]
    return obj


def make_encoding(tmp):
    with open(os.path.join(tmp, "enc_old.csv"), "wb") as fh:
        fh.write(b"\xef\xbb\xbf" + "id,name\n1,Café\n".encode("utf-8"))
    with open(os.path.join(tmp, "enc_new.csv"), "wb") as fh:
        fh.write("id,name\n1,Café\n".encode("cp1252"))


def resolve(arg, tmp):
    if arg.startswith("{tmp}"):
        return tmp + arg[5:]
    if arg.endswith(".csv") and os.path.exists(os.path.join(FIX, arg)):
        return os.path.join(FIX, arg)
    return arg


def run_case(case, tmp):
    if case.get("setup") == "encoding":
        make_encoding(tmp)
    args = [resolve(a, tmp) for a in case["args"]]
    before = {f: sha(os.path.join(FIX, f)) for f in case.get("unchanged", [])}
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        try:
            code = csv_version_diff.main(args)
        except SystemExit as exc:
            code = exc.code
    problems = []
    if code != case["exit"]:
        problems.append("exit %r, wanted %r" % (code, case["exit"]))
    if code in (0, 1):
        try:
            rep = json.loads(out.getvalue())
        except ValueError:
            return problems + ["stdout is not strict JSON"]
        for path, want in case["expect"].items():
            got = dig(rep, path)
            if got != want:
                problems.append("%s: got %r, wanted %r" % (path, got, want))
        if "schema_classes" in case:
            got = sorted(s["class"] for s in rep["schema_changes"])
            if got != case["schema_classes"]:
                problems.append("schema_classes: got %r, wanted %r" % (got, case["schema_classes"]))
        if "warning_codes" in case:
            got = sorted(w["code"] for w in rep["warnings"])
            if got != case["warning_codes"]:
                problems.append("warning_codes: got %r, wanted %r" % (got, case["warning_codes"]))
    for f, h in before.items():
        if sha(os.path.join(FIX, f)) != h:
            problems.append("input %s was modified" % f)
    for f in case.get("files_written", []):
        p = resolve(f, tmp)
        if not os.path.isfile(p) or os.path.getsize(p) == 0:
            problems.append("expected output file missing or empty: %s" % f)
        elif p.endswith(".json"):
            try:
                with open(p, encoding="utf-8") as fh:
                    json.load(fh)
            except ValueError:
                problems.append("written JSON report is not valid JSON")
    return problems


def main():
    with open(os.path.join(FIX, "cases.json"), encoding="utf-8") as fh:
        cases = json.load(fh)["cases"]
    tmp = tempfile.mkdtemp(prefix="csvdiff_")
    failed = 0
    try:
        for case in cases:
            problems = run_case(case, tmp)
            print(("PASS " if not problems else "FAIL ") + case["name"])
            for p in problems:
                print("    " + p)
            failed += bool(problems)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print("%d/%d cases passed" % (len(cases) - failed, len(cases)))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
