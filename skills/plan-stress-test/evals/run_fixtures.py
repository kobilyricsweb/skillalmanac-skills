#!/usr/bin/env python3
"""Run the fixture cases in fixtures/cases.json against scripts/plan_scan.py.

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
import plan_scan  # noqa: E402


def resolve(arg):
    if arg.endswith((".md", ".json")):
        return os.path.normpath(os.path.join(HERE, "fixtures", arg))
    return arg


def run_case(case):
    args = [resolve(a) for a in case["args"]]
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        try:
            code = plan_scan.main(args)
        except SystemExit as exc:
            code = exc.code
    problems = []
    if code != case["exit"]:
        problems.append(f"exit {code}, wanted {case['exit']}")
    try:
        rep = json.loads(out.getvalue())
    except ValueError:
        return problems + ["stdout is not valid JSON"]
    summary = rep.get("summary", {})
    got = {
        "verdict": summary.get("verdict"), "open_steps": summary.get("open_steps"),
        "done_steps": summary.get("done_steps"), "gap_rate": summary.get("gap_rate"),
        "dependencies_named": summary.get("dependencies_named"),
        "dependencies_undefined": summary.get("dependencies_undefined"),
        "counts_by_kind": rep.get("counts_by_kind"),
        "high": [[f["line"], f["kind"]] for f in rep.get("findings", []) if f["severity"] == "high"] if rep.get("command") == "scan" else None,
        "ok": rep.get("ok"), "risk_count": rep.get("risk_count"),
        "errors_count": len(rep["errors"]) if "errors" in rep else None,
        "uncovered_high_lines": rep.get("uncovered_high_lines"),
        "error": ("file not found: <path>" if str(rep.get("error", "")).startswith("file not found") else rep.get("error")),
    }
    for key, want in case["expect"].items():
        if got.get(key) != want:
            problems.append(f"{key}: got {got.get(key)!r}, wanted {want!r}")
    return problems


def main():
    with open(os.path.join(HERE, "fixtures", "cases.json"), encoding="utf-8") as fh:
        cases = json.load(fh)["cases"]
    failed = 0
    for case in cases:
        problems = run_case(case)
        print(("PASS " if not problems else "FAIL ") + " ".join(case["args"]))
        for p in problems:
            print("    " + p)
        failed += bool(problems)
    print(f"{len(cases) - failed}/{len(cases)} cases passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
