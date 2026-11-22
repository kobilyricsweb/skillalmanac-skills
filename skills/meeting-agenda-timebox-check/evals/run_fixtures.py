#!/usr/bin/env python3
"""Run the fixture cases in fixtures/cases.json against scripts/check_agenda.py.

    python evals/run_fixtures.py

Reads the fixtures. The only files written are the report files named with
{TMP} in cases.json, inside a temporary directory that is deleted afterwards.
Exit 0 if every case matches, 1 otherwise.
"""
import contextlib
import io
import json
import os
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
FIXTURES = os.path.join(HERE, "fixtures")
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "scripts"))
import check_agenda  # noqa: E402


def resolve(arg, tmp):
    arg = arg.replace("{TMP}", tmp)
    candidate = os.path.join(FIXTURES, arg)
    return candidate if os.path.isfile(candidate) else arg


def summarise(rep):
    return {
        "verdict": rep["verdict"], "total_min": rep["total_min"], "buffer_min": rep["buffer_min"],
        "item_flags": [it["flags"] for it in rep["items"]],
        "item_clock": [[it["start"], it["end"]] for it in rep["items"]],
        "finding_codes": sorted({f["code"] for f in rep["findings"]}),
        "cuts": [[c["item"], c["action"], c["save_min"]] for c in rep["suggested_cuts"]],
        "attendee_hours": rep["attendee_hours"],
    }


def run_case(case, tmp):
    args = [resolve(a, tmp) for a in case["args"]]
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = check_agenda.main(args)
    problems = []
    if code != case["exit"]:
        problems.append(f"exit {code}, wanted {case['exit']}")
    wanted = case.get("stderr_contains")
    if wanted and wanted not in err.getvalue():
        problems.append(f"stderr {err.getvalue().strip()!r} lacks {wanted!r}")
    expect = case.get("expect") or {}
    if code in (0, 1) and expect:
        report = json.loads(out.getvalue())
        got = summarise(report)
        got["schema_version"] = report["schema_version"]
        for key, want in expect.items():
            if key == "out_written":
                path = want.replace("{TMP}", tmp)
                try:
                    saved = json.load(open(path, encoding="utf-8"))
                except (OSError, ValueError) as exc:
                    problems.append(f"report not written: {exc}")
                else:
                    if saved != report:
                        problems.append("written report differs from stdout")
            elif got.get(key) != want:
                problems.append(f"{key}: got {got.get(key)!r}, wanted {want!r}")
    return problems


def main():
    cases = json.load(open(os.path.join(FIXTURES, "cases.json"), encoding="utf-8"))["cases"]
    tmp = tempfile.mkdtemp(prefix="agenda_fixtures_")
    failed = 0
    try:
        for case in cases:
            problems = run_case(case, tmp)
            label = " ".join(a.replace("{TMP}", "<tmp>") for a in case["args"])
            print(("PASS " if not problems else "FAIL ") + label)
            for p in problems:
                print("    " + p)
            failed += bool(problems)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print(f"{len(cases) - failed}/{len(cases)} cases passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
