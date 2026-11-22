#!/usr/bin/env python3
"""Run the handoff_note_check fixtures and compare with the recorded expected output.

    python evals/run_fixtures.py

Calls the checker in-process on each case, captures its JSON and compares it
with evals/fixtures/expected_<case>.json plus the expected exit code. Prints one
line per case and exits 0 when every case matches, 1 otherwise. Writes nothing.
"""
import contextlib
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "scripts"))
import handoff_note_check  # noqa: E402

FIX = os.path.join(HERE, "fixtures")
REPO = os.path.join(FIX, "repo")
# case name -> (argv for the checker, expected exit code)
CASES = {
    "good": ([os.path.join(FIX, "good_note.md"), "--root", REPO], 0),
    "bad": ([os.path.join(FIX, "bad_note.md"), "--root", REPO], 1),
    "cred_lowercase": ([os.path.join(FIX, "cred_note.md"), "--root", REPO], 1),
    "missing_file": ([os.path.join(FIX, "does_not_exist.md")], 2),
}


def run(argv):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        code = handoff_note_check.main(argv)
    return code, json.loads(buf.getvalue())


def main():
    failed = 0
    for name, (argv, want_code) in CASES.items():
        code, got = run(argv)
        with open(os.path.join(FIX, "expected_%s.json" % name), encoding="utf-8") as fh:
            want = json.load(fh)
        ok = code == want_code and got == want
        print("%s %s (exit %d, expected %d, %d findings)" % ("PASS" if ok else "FAIL", name, code, want_code, len(got["findings"])))
        failed += 0 if ok else 1
    print("RESULT: %s" % ("PASS" if failed == 0 else "FAIL"))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
