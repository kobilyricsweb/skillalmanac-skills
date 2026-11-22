#!/usr/bin/env python3
"""Run the fixture cases in fixtures/cases.json against scripts/repair_ocr.py.

    python evals/run_fixtures.py

Reads the fixtures and expected files; writes only inside a temporary folder
that is removed at the end. Exit 0 if every case matches, 1 otherwise.
"""
import contextlib
import io
import json
import os
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "scripts"))
import repair_ocr  # noqa: E402

FF_MARK = "[[FF]]\n"


def load(path, form_feed=False):
    with open(path, encoding="utf-8", newline="") as fh:
        text = fh.read()
    return text.replace(FF_MARK, "\f") if form_feed else text


def run_main(args):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        try:
            code = repair_ocr.main(args)
        except SystemExit as exc:
            code = exc.code
    return code, out.getvalue()


def read_bytes(path):
    with open(path, "rb") as fh:
        return fh.read()


def run_case(case, tmp):
    problems = []
    folder = tempfile.mkdtemp(dir=tmp)
    in_path = os.path.join(folder, "input.txt")
    out_path = os.path.join(folder, "output.txt")
    if case.get("input"):
        text = load(os.path.join(HERE, "fixtures", case["input"]), case.get("form_feed", False))
        with open(in_path, "w", encoding="utf-8", newline="") as fh:
            fh.write(text)
    elif "input_text" in case:
        with open(in_path, "w", encoding="utf-8", newline="") as fh:
            fh.write(case["input_text"])
    if case.get("preexisting_out"):
        with open(out_path, "w", encoding="utf-8") as fh:
            fh.write("old")
    args = [in_path] + [a.replace("{in}", in_path).replace("{out}", out_path) for a in case["args"]]
    if "--out" not in args and "--dry-run" not in args and case.get("expected_output"):
        args += ["--out", out_path]
    before = read_bytes(in_path) if os.path.exists(in_path) else None
    code, stdout = run_main(args)
    if code != case["exit"]:
        problems.append(f"exit {code}, wanted {case['exit']}")
    if before is not None and read_bytes(in_path) != before:
        problems.append("input file was modified")
    if case.get("preexisting_out") and read_bytes(out_path) != b"old":
        problems.append("existing output was overwritten without --force")
    if case.get("no_write") and os.path.exists(os.path.join(folder, "input.repaired.txt")):
        problems.append("dry run wrote a file")
    if code in (0, 1) and stdout.strip():
        rep = json.loads(stdout)
        for key, want in case.get("stats", {}).items():
            got = rep["stats"].get(key)
            if got != want:
                problems.append(f"stats.{key}: got {got!r}, wanted {want!r}")
        if "suspicious_kinds" in case:
            got = sorted(h["kind"] for h in rep["suspicious"])
            if got != sorted(case["suspicious_kinds"]):
                problems.append(f"suspicious kinds: got {got!r}")
        for c in rep["changes"]:
            if sorted(c) != ["after", "before", "class", "line", "line_end", "reason"]:
                problems.append("change entry has unexpected keys")
                break
    want_out = case.get("expected_output")
    if want_out and code == 0:
        want = load(in_path) if want_out == "same_as_input" else load(os.path.join(HERE, "expected", want_out), case.get("form_feed", False))
        got = load(out_path) if os.path.exists(out_path) else None
        if got != want:
            problems.append("repaired output differs from expected file")
        if case.get("idempotent") and got is not None:
            again = os.path.join(folder, "again.txt")
            code2, out2 = run_main([out_path, "--out", again])
            rep2 = json.loads(out2) if out2.strip() else {"stats": {}}
            if code2 != 0 or rep2["stats"].get("changes_total") != 0 or load(again) != got:
                problems.append("second pass over the repaired file is not a no-op")
    return problems


def main():
    cases = json.load(open(os.path.join(HERE, "fixtures", "cases.json"), encoding="utf-8"))["cases"]
    tmp = tempfile.mkdtemp(prefix="ocr_fixture_")
    failed = 0
    try:
        for case in cases:
            problems = run_case(case, tmp)
            print(("PASS " if not problems else "FAIL ") + case["name"])
            for p in problems:
                print("    " + p)
            failed += bool(problems)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print(f"{len(cases) - failed}/{len(cases)} cases passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
