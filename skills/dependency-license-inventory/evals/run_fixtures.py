#!/usr/bin/env python3
"""Run the fixture cases in fixtures/cases.json against scripts/license_inventory.py.

    python evals/run_fixtures.py

Reads fixtures; writes nothing. It also hashes every fixture file before and
after the runs and fails if any changed (the inventory script must never write).
Exit 0 if every case matches, 1 otherwise.
"""
import contextlib
import hashlib
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
FIX = os.path.join(HERE, "fixtures")
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "scripts"))
import license_inventory  # noqa: E402


def snapshot():
    state = {}
    for base, _dirs, files in os.walk(FIX):
        for f in files:
            p = os.path.join(base, f)
            with open(p, "rb") as fh:
                state[p] = hashlib.sha256(fh.read()).hexdigest()
    return state


def run_case(case):
    args = [a.replace("@fx", FIX) for a in case["args"]]
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        try:
            code = license_inventory.main(args)
        except SystemExit as exc:
            code = exc.code
    problems = []
    if code != case["exit"]:
        problems.append("exit %r, wanted %r" % (code, case["exit"]))
    exp = case["expect"]
    if not exp or code not in (0, 1):
        return problems
    rep = json.loads(out.getvalue())
    got = {}
    if rep.get("command") == "scan":
        pk = {p["name"]: p for p in rep["packages"]}
        got["summary"] = rep["summary"]
        got["unknown"] = [[u["name"], u["reason"]] for u in rep["unknown"]]
        got["conflicts"] = [[c["name"], c["kind"]] for c in rep["conflicts"]]
        if "mentions" in exp:
            got["mentions"] = [[m["name"], sorted(m["mentions"])] for m in rep["mentions"]]
        if "actions" in exp:
            got["actions"] = {n: pk[n]["policy_action"] for n in exp["actions"]}
        if "normalised" in exp:
            got["normalised"] = {n: pk[n]["normalised"] for n in exp["normalised"]}
    else:
        got["norm"] = [[r["normalised"], r["bucket"]] for r in rep["results"]]
    for key, want in exp.items():
        if got.get(key) != want:
            problems.append("%s: got %r, wanted %r" % (key, got.get(key), want))
    return problems


def main():
    cases = json.load(open(os.path.join(FIX, "cases.json"), encoding="utf-8"))["cases"]
    before = snapshot()
    failed = 0
    for case in cases:
        problems = run_case(case)
        print(("PASS " if not problems else "FAIL ") + case["label"])
        for p in problems:
            print("    " + p)
        failed += bool(problems)
    unchanged = snapshot() == before
    print(("PASS " if unchanged else "FAIL ") + "no fixture file changed (script is read-only)")
    failed += not unchanged
    total = len(cases) + 1
    print("%d/%d cases passed" % (total - failed, total))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
