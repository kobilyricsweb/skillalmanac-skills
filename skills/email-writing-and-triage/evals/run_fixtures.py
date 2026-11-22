#!/usr/bin/env python3
"""Run the fixture cases in fixtures/cases.json against scripts/triage_mailbox.py.

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
import triage_mailbox  # noqa: E402

FIXTURE_SUFFIXES = (".json", ".mbox", ".txt")


def check_triage(rep, exp):
    problems = []
    rows = {r["id"]: r for r in rep["messages"]}
    for key in ("reference_date", "counts_by_category", "queue", "quarantine"):
        if key in exp and rep[key] != exp[key]:
            problems.append(f"{key}: got {rep[key]!r}, wanted {exp[key]!r}")
    for mid, want in exp.get("categories", {}).items():
        got = rows.get(mid, {}).get("category")
        if got != want:
            problems.append(f"category of {mid}: got {got!r}, wanted {want!r}")
    for mid, want in exp.get("deadlines", {}).items():
        got = [[d["text"], d["resolved_date"], d["days_left"]] for d in rows.get(mid, {}).get("deadlines", [])]
        if got != want:
            problems.append(f"deadlines of {mid}: got {got!r}, wanted {want!r}")
    for mid, want in exp.get("flags", {}).items():
        got = rows.get(mid, {}).get("flags")
        if got != want:
            problems.append(f"flags of {mid}: got {got!r}, wanted {want!r}")
    for mid, want in exp.get("reply_actions", {}).items():
        got = rows.get(mid, {}).get("reply_action")
        if got != want:
            problems.append(f"reply_action of {mid}: got {got!r}, wanted {want!r}")
    for mid, want in exp.get("subjects", {}).items():
        got = rows.get(mid, {}).get("subject")
        if got != want:
            problems.append(f"subject of {mid}: got {got!r}, wanted {want!r}")
    errors = triage_mailbox.validate(rep)
    if errors:
        problems.append(f"own output fails check: {errors}")
    return problems


def run_case(case):
    args = [os.path.join(HERE, "fixtures", a) if a.endswith(FIXTURE_SUFFIXES) else a for a in case["args"]]
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = triage_mailbox.main(args)
    problems = []
    if code != case["exit"]:
        problems.append(f"exit {code}, wanted {case['exit']}")
    if code == 2 and not err.getvalue().strip():
        problems.append("exit 2 without a message on stderr")
    exp = case["expect"]
    if exp and code in (0, 1):
        rep = json.loads(out.getvalue())
        if case["args"][0] == "triage":
            problems += check_triage(rep, exp)
        else:
            if "ok" in exp and rep["ok"] != exp["ok"]:
                problems.append(f"ok: got {rep['ok']!r}, wanted {exp['ok']!r}")
            if "error_count" in exp and len(rep["errors"]) != exp["error_count"]:
                problems.append(f"error_count: got {len(rep['errors'])}, wanted {exp['error_count']}")
    return problems


def main():
    with open(os.path.join(HERE, "fixtures", "cases.json"), encoding="utf-8") as fh:
        cases = json.load(fh)["cases"]
    failed = 0
    for case in cases:
        problems = run_case(case)
        print(("PASS " if not problems else "FAIL ") + case["name"])
        for p in problems:
            print("    " + p)
        failed += bool(problems)
    print(f"{len(cases) - failed}/{len(cases)} cases passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
