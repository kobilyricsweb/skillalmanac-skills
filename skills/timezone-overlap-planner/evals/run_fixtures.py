#!/usr/bin/env python3
"""Run the cases in fixtures/cases.json against scripts/overlap_windows.py.

    python evals/run_fixtures.py

Reads the fixtures; the only files it writes are inside a throwaway temporary folder
it creates and deletes. Exit 0 if every case passes, 1 otherwise.
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
FX = os.path.join(HERE, "fixtures")
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "scripts"))
import overlap_windows  # noqa: E402


def digest(path):
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def fetch(obj, path):
    cur = obj
    for part in path.split("."):
        if isinstance(cur, list):
            cur = cur[int(part)]
        else:
            cur = cur[part]
    return cur


def run(args):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        try:
            code = overlap_windows.main(args)
        except SystemExit as exc:
            code = exc.code
    return code, out.getvalue()


def sub(text, tmp):
    return text.replace("{fx}", FX).replace("{tmp}", tmp)


def run_case(case, tmp):
    problems = []
    watch = case.get("input_unchanged")
    before = digest(sub(watch, tmp)) if watch else None
    code, text = run([sub(a, tmp) for a in case["args"]])
    if code != case["exit"]:
        problems.append("exit %r, wanted %r" % (code, case["exit"]))
    try:
        rep = json.loads(text)
    except ValueError:
        return problems + ["stdout is not valid JSON"]
    for chk in case.get("checks", []):
        try:
            got = fetch(rep, chk["path"])
        except (KeyError, IndexError, ValueError):
            problems.append("%s: missing" % chk["path"])
            continue
        if got != chk["equals"]:
            problems.append("%s: got %r, wanted %r" % (chk["path"], got, chk["equals"]))
    if watch and digest(sub(watch, tmp)) != before:
        problems.append("input file was modified")
    spec = case.get("then_file_json")
    if spec:
        with open(sub(spec["path"], tmp), encoding="utf-8") as fh:
            if json.load(fh) != rep:
                problems.append("file written by --out differs from stdout")
    if "then_args" in case:
        code2, _ = run([sub(a, tmp) for a in case["then_args"]])
        if code2 != case["then_exit"]:
            problems.append("second run exit %r, wanted %r" % (code2, case["then_exit"]))
    return problems


def main():
    with open(os.path.join(FX, "cases.json"), encoding="utf-8") as fh:
        cases = json.load(fh)["cases"]
    tmp = tempfile.mkdtemp(prefix="tzplan_fixtures_")
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
