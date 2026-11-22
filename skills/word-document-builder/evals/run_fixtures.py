#!/usr/bin/env python3
"""Run the cases in fixtures/cases.json against scripts/docx_inspect.py.

    python evals/run_fixtures.py

Builds the .docx fixtures into a temporary directory (evals/make_docx.py), runs each
case in-process, compares exit code and the listed JSON fields. Writes nothing outside
the temporary directory. Exit 0 if every case matches, 1 otherwise.
"""
import contextlib
import io
import json
import os
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "scripts"))
sys.path.insert(0, HERE)
import docx_inspect  # noqa: E402
import make_docx  # noqa: E402


def resolve(arg, fx):
    if arg.startswith("@fx/"):
        return os.path.join(fx, arg[4:])
    if arg.startswith("@skill/"):
        return os.path.join(ROOT, arg[7:])
    if arg.startswith("@fixtures/"):
        return os.path.join(HERE, "fixtures", arg[10:])
    return arg


def get(rep, key):
    if key == "$rules":
        return [v["rule"] for v in (rep.get("contract") or {}).get("violations", [])]
    if key == "$codes":
        return [f["code"] for f in rep.get("findings", [])]
    count = key.endswith("#")
    cur = rep
    for part in key.rstrip("#").split("."):
        if isinstance(cur, list):
            cur = cur[int(part)]
        else:
            cur = cur[part]
    return len(cur) if count else cur


def run_case(case, fx):
    args = [resolve(a, fx) for a in case["args"]]
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = docx_inspect.main(args)
    problems = []
    if code != case["exit"]:
        problems.append("exit %r, wanted %r" % (code, case["exit"]))
    if code in (0, 1):
        try:
            rep = json.loads(out.getvalue())
        except ValueError:
            return problems + ["stdout is not valid JSON"]
        for key, want in case["expect"].items():
            try:
                got = get(rep, key)
            except (KeyError, IndexError, TypeError):
                got = "<missing>"
            if got != want:
                problems.append("%s: got %r, wanted %r" % (key, got, want))
    elif not err.getvalue().strip():
        problems.append("exit 2 without an error message on stderr")
    return problems


def main():
    cases = json.load(open(os.path.join(HERE, "fixtures", "cases.json"), encoding="utf-8"))["cases"]
    fx = tempfile.mkdtemp(prefix="docx_fx_")
    failed = 0
    try:
        make_docx.build(fx)
        for case in cases:
            problems = run_case(case, fx)
            print(("PASS " if not problems else "FAIL ") + case["name"])
            for p in problems:
                print("    " + p)
            failed += bool(problems)
    finally:
        shutil.rmtree(fx, ignore_errors=True)
    print("%d/%d cases passed" % (len(cases) - failed, len(cases)))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
