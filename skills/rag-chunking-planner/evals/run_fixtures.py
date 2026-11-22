#!/usr/bin/env python3
"""Run the fixture cases in fixtures/cases.json against scripts/plan_chunks.py.

    python evals/run_fixtures.py

Reads the fixtures; writes only to a temporary folder it deletes afterwards.
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
FIX = os.path.join(HERE, "fixtures")
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "scripts"))
import plan_chunks  # noqa: E402


def call(args):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        try:
            code = plan_chunks.main(args)
        except SystemExit as exc:
            code = exc.code
    return code, out.getvalue(), err.getvalue()


def lookup(report, dotted):
    if dotted == "defect_counts":
        return dict((d["type"], d["count"]) for d in report.get("defects", []))
    cur = report
    for part in dotted.split("."):
        cur = cur[int(part)] if isinstance(cur, list) else cur.get(part)
    return cur


def run_case(case):
    args = [os.path.join(FIX, a[1:]) if a.startswith("@") else a for a in case["args"]]
    code, out, _err = call(args)
    problems = []
    if code != case["exit"]:
        problems.append("exit %r, wanted %r" % (code, case["exit"]))
    if case["expect"] and code in (0, 1):
        report = json.loads(out, parse_constant=lambda c: (_ for _ in ()).throw(ValueError(c)))
        for key, want in case["expect"].items():
            got = lookup(report, key)
            if got != want:
                problems.append("%s: got %r, wanted %r" % (key, got, want))
    return problems


def extra_checks(tmp):
    """Output file, overwrite guard and malformed questions file."""
    problems = []
    out_path = os.path.join(tmp, "chunks.jsonl")
    faq = os.path.join(FIX, "corpus", "faq.txt")
    base = ["plan", faq, "--strategy", "paragraph", "--size", "70", "--overlap", "35", "--out", out_path]
    code, _o, _e = call(base)
    rows = [json.loads(line) for line in open(out_path, encoding="utf-8")]
    if code != 0 or len(rows) != 3:
        problems.append("--out: exit %r with %d rows, wanted exit 0 with 3" % (code, len(rows)))
    elif sorted(rows[0]) != ["end", "heading_path", "id", "position", "source", "start", "text", "tokens"]:
        problems.append("--out: unexpected row keys %r" % sorted(rows[0]))
    code, _o, _e = call(base)
    if code != 2:
        problems.append("--out over an existing file without --force: exit %r, wanted 2" % code)
    corp = os.path.join(tmp, "corpus")
    os.makedirs(corp)
    mine = os.path.join(corp, "a.md")
    with open(mine, "w", encoding="utf-8") as fh:
        fh.write("# A\n\nSome original text that must survive.\n")
    for target in (mine, os.path.join(corp, "chunks.jsonl")):
        code, _o, _e = call(["plan", corp, "--out", target, "--force"])
        if code != 2:
            problems.append("--out %s inside the corpus with --force: exit %r, wanted 2" % (os.path.basename(target), code))
    code, _o, _e = call(["plan", mine, "--out", mine, "--force"])
    if code != 2:
        problems.append("--out equal to the input file with --force: exit %r, wanted 2" % code)
    if open(mine, encoding="utf-8").read() != "# A\n\nSome original text that must survive.\n" or os.path.exists(os.path.join(corp, "chunks.jsonl")):
        problems.append("a refused --out still changed or created a file in the corpus")
    bad = os.path.join(tmp, "bad_questions.json")
    with open(bad, "w", encoding="utf-8") as fh:
        fh.write('[{"question": "no passage here"}]')
    code, _o, _e = call(["plan", faq, "--questions", bad])
    if code != 2:
        problems.append("malformed questions file: exit %r, wanted 2" % code)
    return problems


def main():
    cases = json.load(open(os.path.join(FIX, "cases.json"), encoding="utf-8"))["cases"]
    failed = 0
    for case in cases:
        problems = run_case(case)
        print(("PASS " if not problems else "FAIL ") + case["name"])
        for p in problems:
            print("    " + p)
        failed += bool(problems)
    tmp = tempfile.mkdtemp(prefix="chunkfix_")
    try:
        problems = extra_checks(tmp)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print(("PASS " if not problems else "FAIL ") + "output file, overwrite guard, malformed questions")
    for p in problems:
        print("    " + p)
    failed += bool(problems)
    total = len(cases) + 1
    print("%d/%d cases passed" % (total - failed, total))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
