#!/usr/bin/env python3
"""Run the cases in evals/fixtures/cases.json against scripts/validate_outputs.py.

    python evals/run_fixtures.py

Reads the fixtures; writes only inside a fresh temporary folder per case. Checks the exit code,
selected report fields, stderr text, that refused outputs left every input byte-identical, and
that the files written to the temporary folder have the expected shape.
Exit 0 if every case passes, 1 otherwise.
"""
import contextlib
import hashlib
import io
import json
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
FIX = os.path.join(HERE, "fixtures")
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "scripts"))
import validate_outputs  # noqa: E402


def sha(path):
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def run_case(case):
    problems = []
    with tempfile.TemporaryDirectory() as tmp:
        for name, content in case.get("precreate", {}).items():
            with open(os.path.join(tmp, name), "w", encoding="utf-8") as fh:
                fh.write(content)
        args = [a.replace("{FIX}", FIX).replace("{TMP}", tmp) for a in case["args"]]
        before = {n: sha(os.path.join(FIX, n)) for n in case.get("unchanged", [])}
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            try:
                code = validate_outputs.main(args)
            except SystemExit as exc:
                code = exc.code
        if code != case["exit"]:
            problems.append("exit %r, wanted %r" % (code, case["exit"]))
        for text in case.get("stderr_contains", []):
            if text not in err.getvalue():
                problems.append("stderr lacks %r (got %r)" % (text, err.getvalue()[:200]))
        if case.get("expect") and code in (0, 1):
            report = json.loads(out.getvalue())
            for key, want in case["expect"].items():
                if report.get(key) != want:
                    problems.append("%s: got %r, wanted %r" % (key, report.get(key), want))
        for name, digest in before.items():
            if sha(os.path.join(FIX, name)) != digest:
                problems.append("input %s was modified" % name)
        for name in case.get("absent", []):
            if os.path.exists(os.path.join(FIX, name)):
                problems.append("%s should not exist" % name)
        for name, want in case.get("tmp_equals", {}).items():
            with open(os.path.join(tmp, name), encoding="utf-8") as fh:
                if fh.read() != want:
                    problems.append("%s was changed" % name)
        for name, want in case.get("tmp_lines", {}).items():
            with open(os.path.join(tmp, name), encoding="utf-8") as fh:
                got = len(fh.read().splitlines())
            if got != want:
                problems.append("%s has %d lines, wanted %d" % (name, got, want))
        for name, needles in case.get("tmp_contains", {}).items():
            with open(os.path.join(tmp, name), encoding="utf-8") as fh:
                body = fh.read()
            for needle in needles:
                if needle not in body:
                    problems.append("%s lacks %r" % (name, needle))
    return problems


def main():
    with open(os.path.join(FIX, "cases.json"), encoding="utf-8") as fh:
        cases = json.load(fh)["cases"]
    failed = 0
    for case in cases:
        problems = run_case(case)
        print(("PASS " if not problems else "FAIL ") + case["id"])
        for p in problems:
            print("    " + p)
        failed += bool(problems)
    print("%d/%d cases passed" % (len(cases) - failed, len(cases)))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
