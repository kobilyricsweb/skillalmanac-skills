#!/usr/bin/env python3
"""Run the cases in fixtures/cases.json against scripts/pseudo_localize.py.

    python evals/run_fixtures.py

Reads fixtures and writes only inside a temporary directory it deletes afterwards.
Exit 0 if every case matches, 1 otherwise.
"""
import contextlib
import hashlib
import io
import json
import os
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
FX = os.path.join(HERE, "fixtures")
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "scripts"))
import pseudo_localize  # noqa: E402


def sha(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def derive(rep):
    return {
        "strings_total": rep.get("strings_total"), "transformed": rep.get("transformed"),
        "placeholders_checked": rep.get("placeholders_checked"),
        "placeholder_mismatches": rep.get("placeholder_mismatches"),
        "round_trip_ok": rep.get("round_trip_ok"), "ok": rep.get("ok"), "written": rep.get("written"),
        "output_file": rep.get("output_file"), "expansion": rep.get("expansion"),
        "no_letters": rep.get("no_letters"), "warnings": rep.get("warnings"),
        "fragment_keys": [f["key"] for f in rep.get("fragments", [])],
        "html_keys": [h["key"] for h in rep.get("html_inside", [])],
        "unnamed_keys": [u["key"] for u in rep.get("repeated_unnamed", [])],
        "baked": [[b["key"], b["kind"]] for b in rep.get("baked_values", [])],
        "overflow": [[o["key"], o["class"], o["headroom_pct"]] for o in rep.get("overflow_risk", [])],
        "hardcoded_lines": [h["line"] for h in (rep.get("hardcoded_candidates") or [])],
        "hardcoded_matches": [h["matches_key"] for h in (rep.get("hardcoded_candidates") or [])],
    }


def run_once(args):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        try:
            code = pseudo_localize.main(args)
        except SystemExit as exc:
            code = exc.code
    return code, out.getvalue()


def run_case(case, tmp):
    sub = lambda s: s.replace("{fx}", FX).replace("{tmp}", tmp)
    args = [sub(a) for a in case["args"]]
    before = {n: sha(os.path.join(FX, n)) for n in case.get("unchanged", [])}
    if case.get("twice"):
        run_once(args)
    code, out = run_once(args)
    problems = []
    if code != case["exit"]:
        problems.append("exit %r, wanted %r" % (code, case["exit"]))
    if code in (0, 1) and case.get("expect"):
        got = derive(json.loads(out))
        for key, want in case["expect"].items():
            have = got.get(key)
            if key == "output_file" and want is not None:
                have = os.path.basename(have or "")
            if have != want:
                problems.append("%s: got %r, wanted %r" % (key, have, want))
    for produced, expected in case.get("expect_output", {}).items():
        p = sub(produced)
        if not os.path.exists(p):
            problems.append("missing output " + p)
        elif open(p, "rb").read() != open(os.path.join(FX, expected), "rb").read():
            problems.append("output differs from fixtures/" + expected)
    for n, digest in before.items():
        if sha(os.path.join(FX, n)) != digest:
            problems.append("input changed: " + n)
    for path in case.get("absent", []):
        if os.path.exists(sub(path)):
            problems.append("should not exist: " + sub(path))
    return problems


def main():
    cases = json.load(open(os.path.join(FX, "cases.json"), encoding="utf-8"))["cases"]
    failed = 0
    for case in cases:
        tmp = tempfile.mkdtemp(prefix="pseudo_fx_")
        try:
            problems = run_case(case, tmp)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
        print(("PASS " if not problems else "FAIL ") + case["name"])
        for p in problems:
            print("    " + p)
        failed += bool(problems)
    print("%d/%d cases passed" % (len(cases) - failed, len(cases)))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
