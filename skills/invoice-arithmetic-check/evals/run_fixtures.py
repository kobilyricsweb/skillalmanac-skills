#!/usr/bin/env python3
"""Run the cases in fixtures/cases.json against scripts/check_invoices.py.

    python evals/run_fixtures.py

Reads the fixtures; writes only to a temporary directory it creates and removes.
Exit 0 if every case matches, 1 otherwise.
"""
import contextlib
import hashlib
import io
import json
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
FIXTURES = os.path.join(HERE, "fixtures")
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "scripts"))
import check_invoices  # noqa: E402


def digest(path):
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def get_path(doc, dotted):
    cur = doc
    for part in dotted.split("."):
        if isinstance(cur, list):
            cur = cur[int(part)]
        else:
            cur = cur.get(part) if isinstance(cur, dict) else None
        if cur is None:
            return None
    return cur


def codes(issues):
    return sorted("%s:%s" % (i["severity"], i["code"]) for i in issues)


def run_case(case, tmp):
    args = []
    out_path = None
    for a in case["args"]:
        if a == "@TMP":
            out_path = os.path.join(tmp, "report.json")
            args.append(out_path)
        elif a.endswith((".json", ".csv")):
            args.append(os.path.join(FIXTURES, a))
        else:
            args.append(a)
    before = {n: digest(os.path.join(FIXTURES, n)) for n in case.get("unchanged", [])}
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        try:
            code = check_invoices.main(args)
        except SystemExit as exc:
            code = exc.code
    problems = []
    if code != case["exit"]:
        problems.append("exit %r, wanted %r" % (code, case["exit"]))
    for n, h in before.items():
        if digest(os.path.join(FIXTURES, n)) != h:
            problems.append("fixture %s was modified" % n)
    if case.get("writes_valid_json"):
        try:
            with open(out_path, encoding="utf-8") as fh:
                json.load(fh)
        except (OSError, ValueError) as exc:
            problems.append("output file not valid JSON: %s" % exc)
    if code in (0, 1) and (case.get("paths") or case.get("codes")):
        doc = json.loads(out.getvalue(), parse_constant=lambda c: (_ for _ in ()).throw(ValueError(c)))
        for dotted, want in case.get("paths", {}).items():
            got = get_path(doc, dotted)
            if got != want:
                problems.append("%s: got %r, wanted %r" % (dotted, got, want))
        for idx, want in case.get("codes", {}).items():
            got = codes(doc["invoices"][int(idx)]["issues"])
            if got != sorted(want):
                problems.append("invoice %s issues: got %r, wanted %r" % (idx, got, sorted(want)))
        if "file_codes" in case and codes(doc["file_issues"]) != sorted(case["file_codes"]):
            problems.append("file issues: got %r" % codes(doc["file_issues"]))
    return problems


def main():
    with open(os.path.join(FIXTURES, "cases.json"), encoding="utf-8") as fh:
        cases = json.load(fh)["cases"]
    failed = 0
    with tempfile.TemporaryDirectory() as tmp:
        for case in cases:
            problems = run_case(case, tmp)
            print(("PASS " if not problems else "FAIL ") + case["name"])
            for p in problems:
                print("    " + p)
            failed += bool(problems)
    print("%d/%d cases passed" % (len(cases) - failed, len(cases)))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
