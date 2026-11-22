#!/usr/bin/env python3
"""Run the fixture cases in fixtures/cases.json against scripts/prep_voiceover.py.

    python evals/run_fixtures.py

Reads fixtures and writes output files only into a temporary directory that is
removed afterwards. Exit 0 if every case matches, 1 otherwise.
"""
import contextlib
import io
import json
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "scripts"))
import prep_voiceover  # noqa: E402

FIXTURES = os.path.join(HERE, "fixtures")
OUTPUT_FILES = ("spoken.txt", "spoken.ssml", "chunks.jsonl")


def view(rep):
    return {
        "verdict": rep["verdict"], "blockers": rep["blockers"], "advisories": rep["advisories"],
        "words": rep["totals"]["words"], "est_seconds": rep["totals"]["est_seconds"],
        "est_seconds_at_140_wpm": rep["totals"]["est_seconds_at_140_wpm"],
        "est_seconds_at_170_wpm": rep["totals"]["est_seconds_at_170_wpm"],
        "chunks": rep["totals"]["chunks"], "unexpanded": rep["unexpanded"],
        "unexpanded_tokens": sorted({u["token"] for u in rep["unexpanded"]}),
        "tongue_twister_lines": [t["line"] for t in rep["tongue_twisters"]],
        "long_url_lines": [u["line"] for u in rep["long_urls"]],
        "mid_sentence_breaks": rep["mid_sentence_breaks"],
        "long_sentence_words": [s["words"] for s in rep["long_sentences"]],
    }


def run_case(case):
    args = list(case["args"])
    args[0] = os.path.join(FIXTURES, args[0])
    if "--lexicon" in args:
        i = args.index("--lexicon") + 1
        args[i] = os.path.join(FIXTURES, args[i])
    problems = []
    with tempfile.TemporaryDirectory() as tmp:
        if case.get("expected_dir"):
            args += ["--out-dir", tmp]
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            try:
                code = prep_voiceover.main(args)
            except SystemExit as exc:
                code = exc.code
        if code != case["exit"]:
            problems.append("exit %r, wanted %r" % (code, case["exit"]))
        if code in (0, 1):
            rep = json.loads(out.getvalue())
            got = view(rep)
            for key, want in case["expect"].items():
                if got.get(key) != want:
                    problems.append("%s: got %r, wanted %r" % (key, got.get(key), want))
            if case.get("expected_dir"):
                for name in OUTPUT_FILES:
                    exp_path = os.path.join(FIXTURES, "expected", case["expected_dir"], name)
                    with open(exp_path, encoding="utf-8", newline="") as f:
                        want_text = f.read()
                    with open(os.path.join(tmp, name), encoding="utf-8", newline="") as f:
                        got_text = f.read()
                    if want_text != got_text:
                        problems.append("%s differs from expected/%s/%s" % (name, case["expected_dir"], name))
        elif not err.getvalue().strip():
            problems.append("exit 2 without a message on stderr")
    return problems


def main():
    with open(os.path.join(FIXTURES, "cases.json"), encoding="utf-8") as f:
        cases = json.load(f)["cases"]
    failed = 0
    for case in cases:
        problems = run_case(case)
        print(("PASS " if not problems else "FAIL ") + case["name"])
        for p in problems:
            print("    " + p)
        failed += bool(problems)
    print("%d/%d cases passed" % (len(cases) - failed, len(cases)))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
