#!/usr/bin/env python3
"""Run the fixture cases in fixtures/cases.json against scripts/critical_path.py.

    python evals/run_fixtures.py

Reads fixtures; writes only into a temporary directory it creates and removes.
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
import critical_path  # noqa: E402


def resolve(arg):
    return os.path.join(FIXTURES, arg[3:]) if arg.startswith("fx:") else arg


def digest(name):
    with open(os.path.join(FIXTURES, name), "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()


def project(rep):
    tasks = rep.get("tasks", [])
    got = {key: rep.get(key) for key in (
        "ok", "scheduled", "project_duration", "start_date", "finish_date", "deadline_days",
        "deadline_gap", "critical_count", "paths", "cycles")}
    got["dangling"] = [[d["task"], d["predecessor"]] for d in rep.get("dangling", [])]
    got["table"] = {t["id"]: [t.get(k) for k in ("es", "ef", "ls", "lf", "slack")] for t in tasks} if rep.get("scheduled") else None
    got["task_dates"] = {t["id"]: [t["start_date"], t["finish_date"]] for t in tasks} if rep.get("scheduled") else None
    got["overloads"] = [[o["owner"], o["from_day"], o["to_day"], o["tasks"]] for o in rep.get("overloads", [])]
    got["warning_rules"] = [w["rule"] for w in rep.get("warnings", []) if w["severity"] != "info"]
    return got


def run_case(case):
    args = [resolve(a) for a in case["args"]]
    before = {name: digest(name) for name in case.get("unchanged", [])}
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = critical_path.main(args)
    problems = []
    if code != case["exit"]:
        problems.append("exit %r, wanted %r" % (code, case["exit"]))
    if code in (0, 1):
        got = project(json.loads(out.getvalue()))
        for key, want in case["expect"].items():
            if got.get(key) != want:
                problems.append("%s: got %r, wanted %r" % (key, got.get(key), want))
    elif code == 2:
        if "error" not in json.loads(out.getvalue()):
            problems.append("exit 2 without an error key in the JSON")
    for name, old in before.items():
        if digest(name) != old:
            problems.append("input %s was modified" % name)
    return problems


def run_out_file_case():
    """--out writes a report that equals stdout, refuses an existing file, accepts --force."""
    problems = []
    plan = resolve("fx:clean_launch.json")
    with tempfile.TemporaryDirectory() as tmp:
        target = os.path.join(tmp, "report.json")
        out = io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(io.StringIO()):
            first = critical_path.main([plan, "--out", target])
        if first != 0:
            problems.append("first --out run exit %r, wanted 0" % first)
        elif json.load(open(target, encoding="utf-8")) != json.loads(out.getvalue()):
            problems.append("file written by --out differs from stdout")
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            second = critical_path.main([plan, "--out", target])
            third = critical_path.main([plan, "--out", target, "--force"])
        if second != 2:
            problems.append("second run without --force exit %r, wanted 2" % second)
        if third != 0:
            problems.append("run with --force exit %r, wanted 0" % third)
    return problems


def main():
    cases = json.load(open(os.path.join(FIXTURES, "cases.json"), encoding="utf-8"))["cases"]
    failed = 0
    for case in cases:
        problems = run_case(case)
        label = " ".join(a[3:] if a.startswith("fx:") else a for a in case["args"])
        print(("PASS " if not problems else "FAIL ") + label)
        for item in problems:
            print("    " + item)
        failed += bool(problems)
    problems = run_out_file_case()
    print(("PASS " if not problems else "FAIL ") + "--out writes, refuses existing file, accepts --force")
    for item in problems:
        print("    " + item)
    failed += bool(problems)
    total = len(cases) + 1
    print("%d/%d cases passed" % (total - failed, total))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
