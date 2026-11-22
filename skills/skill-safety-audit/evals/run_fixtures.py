#!/usr/bin/env python3
"""Run the fixture cases in fixtures/cases.json against scripts/skill_audit.py.

    python evals/run_fixtures.py

Reads fixtures; writes nothing. Exit 0 if every case matches, 1 otherwise.
Compared per case: exit code, and (when the scan ran) verdict, severity counts,
risk-table levels, hosts, and the ordered list of findings as rule@file:line.
"""
import contextlib
import io
import json
import os
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "scripts"))
import skill_audit  # noqa: E402


def materialize(src, dest):
    """Copy an inert fixture folder to dest, stripping the trailing .txt from every file name."""
    for dirpath, _dirs, files in os.walk(src):
        rel = os.path.relpath(dirpath, src)
        target = dest if rel == "." else os.path.join(dest, rel)
        os.makedirs(target, exist_ok=True)
        for name in files:
            if name.lower() == "readme.md":
                continue
            out = name[:-4] if name.endswith(".txt") else name
            shutil.copyfile(os.path.join(dirpath, name), os.path.join(target, out))


def run_case(case):
    folder = os.path.join(HERE, "fixtures", case["folder"])
    tmp = None
    if case.get("inert"):
        tmp = tempfile.mkdtemp(prefix="skill_audit_fx_")
        materialize(folder, tmp)
        folder = tmp
    try:
        return _run(case, folder)
    finally:
        if tmp:
            shutil.rmtree(tmp, ignore_errors=True)


def _run(case, folder):
    args = ["scan", folder]
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = skill_audit.main(args)
    problems = []
    if code != case["exit"]:
        problems.append("exit %r, wanted %r" % (code, case["exit"]))
    exp = case["expect"]
    if exp and code in (0, 1, 3):
        rep = json.loads(out.getvalue())
        got = {
            "verdict": rep["summary"]["verdict"],
            "counts": rep["summary"]["counts"],
            "hosts": rep["summary"]["hosts"],
            "levels": {row["capability"]: row["level"] for row in rep["risk_table"]},
            "findings": ["%s@%s:%d" % (f["rule"], f["file"], f["line"]) for f in rep["findings"]],
            "contexts": sorted({f["context"] for f in rep["findings"]}),
        }
        for key, want in exp.items():
            if got.get(key) != want:
                problems.append("%s: got %r, wanted %r" % (key, got.get(key), want))
    elif case["exit"] == 2 and "stderr_contains" in case:
        if case["stderr_contains"] not in err.getvalue():
            problems.append("stderr %r lacks %r" % (err.getvalue(), case["stderr_contains"]))
    return problems


def main():
    if len(sys.argv) == 3 and sys.argv[1] == "--materialize":
        base = os.path.join(HERE, "fixtures", "malicious")
        for name in sorted(os.listdir(base)):
            if os.path.isdir(os.path.join(base, name)):
                materialize(os.path.join(base, name), os.path.join(sys.argv[2], name))
        print("materialised into " + sys.argv[2] + " (inspect only; never install or run)")
        return 0
    with open(os.path.join(HERE, "fixtures", "cases.json"), encoding="utf-8") as fh:
        cases = json.load(fh)["cases"]
    failed = 0
    for case in cases:
        problems = run_case(case)
        print(("PASS " if not problems else "FAIL ") + case["folder"] + " (exit %d)" % case["exit"])
        for p in problems:
            print("    " + p)
        failed += bool(problems)
    print("%d/%d cases passed" % (len(cases) - failed, len(cases)))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
