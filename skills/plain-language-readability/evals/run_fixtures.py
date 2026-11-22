#!/usr/bin/env python3
"""Run the fixture cases in fixtures/cases.json against scripts/readability.py.

    python evals/run_fixtures.py

Reads fixtures; writes only inside a temporary directory it removes afterwards.
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
FIX = os.path.join(HERE, "fixtures")
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "scripts"))
import readability  # noqa: E402


def digest(path):
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def dig(obj, dotted):
    for part in dotted.split("."):
        obj = obj[int(part)] if isinstance(obj, list) else obj[part]
    return obj


def expand(arg, tmp):
    arg = arg.replace("{tmp}", tmp)
    if not arg.startswith("-") and os.path.exists(os.path.join(FIX, arg)):
        return os.path.join(FIX, arg)
    return arg


def run_case(case, tmp):
    for path, content in case.get("precreate", {}).items():
        with open(path.replace("{tmp}", tmp), "w", encoding="utf-8") as fh:
            fh.write(content)
    # A name that does not exist yet (missing-file case) is still resolved under fixtures.
    args = [expand(a, tmp) for a in case["args"]]
    if case["args"] and not case["args"][0].startswith("-") and not os.path.isabs(args[0]) and not os.path.exists(args[0]):
        args[0] = os.path.join(FIX, case["args"][0])
    before = {f: digest(os.path.join(FIX, f)) for f in case.get("unchanged", [])}
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        try:
            code = readability.main(args)
        except SystemExit as exc:
            code = exc.code
    problems = []
    if code != case["exit"]:
        problems.append("exit %r, wanted %r" % (code, case["exit"]))
    if case["exit"] in (0, 1):
        try:
            rep = json.loads(out.getvalue())
        except ValueError:
            problems.append("stdout is not strict JSON")
            rep = {}
        for key, want in case["expect"].items():
            try:
                got = dig(rep, key)
            except (KeyError, IndexError, TypeError, ValueError):
                got = "<missing>"
            if got != want:
                problems.append("%s: got %r, wanted %r" % (key, got, want))
    elif out.getvalue().strip():
        problems.append("printed a report on an error exit")
    for f, h in before.items():
        if digest(os.path.join(FIX, f)) != h:
            problems.append("input file was modified: " + f)
    if "out_json" in case:
        try:
            with open(case["out_json"].replace("{tmp}", tmp), encoding="utf-8") as fh:
                json.load(fh)
        except (OSError, ValueError):
            problems.append("--out file missing or not valid JSON")
    for path, content in case.get("content_equals", {}).items():
        with open(path.replace("{tmp}", tmp), encoding="utf-8") as fh:
            if fh.read() != content:
                problems.append("existing --out file was overwritten")
    return problems


def main():
    spec = json.load(open(os.path.join(FIX, "cases.json"), encoding="utf-8"))
    tmp = tempfile.mkdtemp(prefix="readability_fixtures_")
    failed = total = 0
    try:
        for case in spec["cases"]:
            problems = run_case(case, tmp)
            total += 1
            print(("PASS " if not problems else "FAIL ") + case["name"])
            for p in problems:
                print("    " + p)
            failed += bool(problems)
        wrong = {w: (readability.count_syllables(w), n) for w, n in spec["syllables"]["words"].items()
                 if readability.count_syllables(w) != n}
        total += 1
        print(("PASS " if not wrong else "FAIL ") + "syllable counts on %d hand-counted words" % len(spec["syllables"]["words"]))
        for w, (got, want) in wrong.items():
            print("    %s: got %d, wanted %d" % (w, got, want))
        failed += bool(wrong)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print("%d/%d cases passed" % (total - failed, total))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
