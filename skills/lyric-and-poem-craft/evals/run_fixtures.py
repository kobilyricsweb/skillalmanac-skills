#!/usr/bin/env python3
"""Run the fixture cases in fixtures/cases.json against scripts/audit_lyrics.py.

    python evals/run_fixtures.py

Reads fixtures; writes nothing. For each case it runs audit_lyrics.main with the listed
arguments (paths ending in .txt or .json are resolved inside evals/fixtures) and compares
the exit code and selected JSON values. A value path is dotted: "sections.0.rhyme_scheme".
The pseudo path "flag_codes" is the sorted list of distinct flag codes.
Also checks the word-level syllable and rhyme tables in cases.json.
Exit 0 if every check matches, 1 otherwise.
"""
import contextlib
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "scripts"))
import audit_lyrics  # noqa: E402


def dig(obj, path):
    if path == "flag_codes":
        return sorted({f["code"] for f in obj["flags"]})
    cur = obj
    for part in path.split("."):
        if isinstance(cur, list):
            cur = cur[int(part)]
        else:
            cur = cur[part]
    return cur


def run_case(case):
    args = [os.path.join(HERE, "fixtures", a) if a.endswith((".txt", ".json")) else a
            for a in case["args"]]
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        try:
            code = audit_lyrics.main(args)
        except SystemExit as exc:
            code = 2 if isinstance(exc.code, str) else exc.code
    problems = []
    if code != case["exit"]:
        problems.append("exit %r, wanted %r" % (code, case["exit"]))
    if code == 0:
        text = out.getvalue()
        try:
            rep = json.loads(text, parse_constant=lambda c: (_ for _ in ()).throw(ValueError(c)))
        except ValueError as exc:
            return problems + ["output is not strict JSON: %s" % exc]
        for path, want in case["expect"].items():
            try:
                got = dig(rep, path)
            except (KeyError, IndexError, ValueError, TypeError):
                got = "<missing>"
            if got != want:
                problems.append("%s: got %r, wanted %r" % (path, got, want))
    return problems


def run_words(table):
    problems = []
    for word, want in table["syllables"].items():
        got = audit_lyrics.count_core(word)
        if got != want:
            problems.append("syllables(%s): got %d, wanted %d" % (word, got, want))
    for word, want in table["known_misses"].items():
        got = audit_lyrics.count_core(word)
        if got != want["heuristic"]:
            problems.append("known miss %s: heuristic gave %d, recorded %d" % (word, got, want["heuristic"]))
    for a, b, want in table["rhyme_pairs"]:
        ka, kb = audit_lyrics.rhyme_key(a, {}), audit_lyrics.rhyme_key(b, {})
        got = audit_lyrics.classify_pair(a, b, ka, kb)
        if got != want:
            problems.append("rhyme(%s,%s): got %s, wanted %s" % (a, b, got, want))
    return problems


def main():
    data = json.load(open(os.path.join(HERE, "fixtures", "cases.json"), encoding="utf-8"))
    failed = 0
    for case in data["cases"]:
        problems = run_case(case)
        print(("PASS " if not problems else "FAIL ") + case["name"])
        for p in problems:
            print("    " + p)
        failed += bool(problems)
    problems = run_words(data["word_tables"])
    print(("PASS " if not problems else "FAIL ") + "word tables (syllables, known misses, rhyme pairs)")
    for p in problems:
        print("    " + p)
    failed += bool(problems)
    total = len(data["cases"]) + 1
    print("%d/%d checks passed" % (total - failed, total))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
