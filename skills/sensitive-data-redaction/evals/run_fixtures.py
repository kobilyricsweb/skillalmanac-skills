#!/usr/bin/env python3
"""Run the fixture cases in fixtures/cases.json against scripts/redact.py.

    python evals/run_fixtures.py

Writes only into a temporary folder that is removed afterwards. Besides the
expected outputs, every case that is not marked skip_forbidden also checks that
none of the fake sensitive values listed in forbidden_everywhere appear in
stdout, in the redacted output or in the report. Exit 0 if every case passes.
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
import redact  # noqa: E402


def read(path):
    with open(path, "rb") as fh:
        return fh.read().decode("utf-8")


def run_case(case, tmp, forbidden):
    for d in case.get("mkdirs", []):
        os.makedirs(os.path.join(tmp, d), exist_ok=True)
    args = [a.replace("@fix", FIX).replace("@tmp", tmp) for a in case["args"]]
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        try:
            code = redact.main(args)
        except SystemExit as exc:
            code = exc.code
    problems = []
    if code != case["exit"]:
        problems.append(f"exit {code}, wanted {case['exit']}; stderr: {err.getvalue().strip()}")
    if case["exit"] != 0:
        return problems
    report = json.loads(out.getvalue())
    if "total" in case and report.get("total_replacements") != case["total"]:
        problems.append(f"total {report.get('total_replacements')}, wanted {case['total']}")
    if "counts" in case:
        got = {k: [v["matches"], v["unique"]] for k, v in report.get("counts", {}).items()}
        if got != case["counts"]:
            problems.append(f"counts {got}, wanted {case['counts']}")
    for needle in case.get("warnings_contain", []):
        if not any(needle in w for w in report.get("warnings", [])):
            problems.append(f"no warning containing {needle!r}")
    for name, expected in case.get("files", {}).items():
        if read(os.path.join(tmp, name)) != read(os.path.join(HERE, "fixtures", expected)):
            problems.append(f"{name} differs from {expected}")
    for name, src in case.get("same_as_input", {}).items():
        if read(os.path.join(tmp, name)) != read(os.path.join(FIX, src)):
            problems.append(f"{name} differs from the input {src}")
    for name in case.get("json_valid", []):
        try:
            json.loads(read(os.path.join(tmp, name)))
        except ValueError:
            problems.append(f"{name} is not valid JSON")
    for name, needles in case.get("contains", {}).items():
        text = read(os.path.join(tmp, name))
        problems += [f"{name} lacks {n!r}" for n in needles if n not in text]
    for name, needles in case.get("not_contains", {}).items():
        text = read(os.path.join(tmp, name))
        problems += [f"{name} still contains {n!r}" for n in needles if n in text]
    if "empty_dir" in case and os.listdir(os.path.join(tmp, case["empty_dir"])):
        problems.append("dry run wrote files")
    if not case.get("skip_forbidden"):
        haystacks = [out.getvalue()]
        for name in ("support_ticket.redacted.txt", "support_ticket.redaction_report.json", "server.redacted.log",
                     "server.redaction_report.json", "customer.redacted.json", "customer.redaction_report.json"):
            path = os.path.join(tmp, name)
            if os.path.exists(path):
                haystacks.append(read(path))
        for value in forbidden:
            if any(value in h for h in haystacks):
                problems.append(f"fake sensitive value leaked: {value!r}")
    return problems


def main():
    spec = json.load(open(os.path.join(FIX, "cases.json"), encoding="utf-8"))
    tmp = tempfile.mkdtemp(prefix="redact_fixtures_")
    failed = 0
    try:
        for case in spec["cases"]:
            problems = run_case(case, tmp, spec["forbidden_everywhere"])
            print(("PASS " if not problems else "FAIL ") + case["id"])
            for p in problems:
                print("    " + p)
            failed += bool(problems)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print(f"{len(spec['cases']) - failed}/{len(spec['cases'])} cases passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
