#!/usr/bin/env python3
"""Run the fixture cases in fixtures/cases.json against scripts/release_notes.py.

    python evals/run_fixtures.py

Reads fixtures. The only writes are inside a temporary directory (the markdown-out test),
which is deleted afterwards. Exit 0 if every case matches, 1 otherwise.
"""
import contextlib
import io
import json
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "scripts"))
import release_notes  # noqa: E402


def run_main(args):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        try:
            code = release_notes.main(args)
        except SystemExit as exc:
            code = exc.code
    return code, out.getvalue()


def resolve(args):
    return [os.path.join(HERE, "fixtures", a) if a.endswith((".txt", ".md")) else a for a in args]


def run_case(case):
    code, text = run_main(resolve(case["args"]))
    problems = []
    if code != case["exit"]:
        problems.append("exit %r, wanted %r" % (code, case["exit"]))
    try:
        rep = json.loads(text)
    except ValueError:
        return problems + ["stdout is not valid JSON"]
    for key, want in case["expect"].items():
        if key == "error_contains":
            got = rep.get("error", "")
            if want not in got:
                problems.append("error %r does not contain %r" % (got, want))
            continue
        getters = {
            "warning_codes": [w["code"] for w in rep.get("warnings", [])],
            "breaking_refs": [b["ref"] for b in rep.get("breaking", [])],
            "unsorted_refs": [u["ref"] for u in rep.get("unsorted", [])],
            "dropped_reasons": [d["reason"] for d in rep.get("dropped", [])],
            "omitted": rep.get("counts", {}).get("omitted_from_notes"),
        }
        got = getters[key] if key in getters else rep.get(key)
        if got != want:
            problems.append("%s: got %r, wanted %r" % (key, got, want))
    return problems


def run_write_case():
    """Write the skeleton into a temp dir: first write ok, second refused, forced write ok."""
    problems = []
    source = os.path.join(HERE, "fixtures", "log_good.txt")
    with tempfile.TemporaryDirectory() as tmp:
        target = os.path.join(tmp, "notes.md")
        base = [source, "--current-version", "1.4.2", "--markdown-out", target]
        code, text = run_main(base)
        if code != 0 or not os.path.isfile(target):
            return ["first write: exit %r, file exists %r" % (code, os.path.isfile(target))]
        with open(target, encoding="utf-8") as handle:
            written = handle.read()
        if written != json.loads(text)["skeleton"]:
            problems.append("file content differs from the skeleton in the JSON")
        code, _ = run_main(base)
        if code != 2:
            problems.append("second write without --force: exit %r, wanted 2" % code)
        code, _ = run_main(base + ["--force"])
        if code != 0:
            problems.append("second write with --force: exit %r, wanted 0" % code)
    return problems


def main():
    path = os.path.join(HERE, "fixtures", "cases.json")
    with open(path, encoding="utf-8") as handle:
        cases = json.load(handle)["cases"]
    failed = 0
    for case in cases:
        problems = run_case(case)
        print(("PASS " if not problems else "FAIL ") + " ".join(case["args"]))
        for problem in problems:
            print("    " + problem)
        failed += bool(problems)
    problems = run_write_case()
    print(("PASS " if not problems else "FAIL ") + "markdown-out write, refuse overwrite, force")
    for problem in problems:
        print("    " + problem)
    failed += bool(problems)
    total = len(cases) + 1
    print("%d/%d cases passed" % (total - failed, total))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
