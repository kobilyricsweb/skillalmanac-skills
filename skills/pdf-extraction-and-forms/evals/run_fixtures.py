#!/usr/bin/env python3
"""Run the fixture cases in fixtures/cases.json against the three scripts.

    python evals/run_fixtures.py

Reads fixtures, writes only to a temporary directory it removes afterwards.
Each case names a tool, its arguments (paths relative to evals/fixtures/, or
"@name" for the saved inspect report of fixtures/name.pdf, generated on the
fly), the expected exit code and expected values at dotted JSON paths.
Exit 0 if every case matches, 1 otherwise.
"""
import contextlib
import io
import json
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
FIX = os.path.join(HERE, "fixtures")
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "scripts"))
import form_verify  # noqa: E402
import pdf_inspect  # noqa: E402
import table_check  # noqa: E402

TOOLS = {"pdf_inspect": pdf_inspect, "table_check": table_check, "form_verify": form_verify}


def call(mod, args):
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        code = mod.main(args)
    return code, out.getvalue()


def dig(obj, path):
    for part in path.split("."):
        if isinstance(obj, list):
            obj = obj[int(part)]
        else:
            obj = obj[part]
    return obj


def main():
    cases = json.load(open(os.path.join(FIX, "cases.json"), encoding="utf-8"))["cases"]
    failed = 0
    with tempfile.TemporaryDirectory() as tmp:
        for case in cases:
            args = []
            for a in case["args"]:
                if a.startswith("@"):
                    code, text = call(pdf_inspect, [os.path.join(FIX, a[1:] + ".pdf")])
                    target = os.path.join(tmp, a[1:] + ".json")
                    with open(target, "w", encoding="utf-8") as fh:
                        fh.write(text)
                    args.append(target)
                elif os.path.exists(os.path.join(FIX, a)):
                    args.append(os.path.join(FIX, a))
                else:
                    args.append(a)
            code, text = call(TOOLS[case["tool"]], args)
            problems = []
            if code != case["exit"]:
                problems.append("exit %s, wanted %s" % (code, case["exit"]))
            try:
                rep = json.loads(text)
            except ValueError:
                rep = None
                problems.append("stdout is not valid JSON")
            if rep is not None:
                for path, want in case["expect"].items():
                    try:
                        got = dig(rep, path)
                    except (KeyError, IndexError, ValueError):
                        got = "<missing>"
                    if got != want:
                        problems.append("%s: got %r, wanted %r" % (path, got, want))
            print(("PASS " if not problems else "FAIL ") + case["tool"] + " " + " ".join(case["args"]))
            for p in problems:
                print("    " + p)
            failed += bool(problems)
    print("%d/%d cases passed" % (len(cases) - failed, len(cases)))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
