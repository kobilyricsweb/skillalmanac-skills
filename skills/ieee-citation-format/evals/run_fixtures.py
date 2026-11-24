#!/usr/bin/env python3
"""Run the cases in fixtures/cases.json against scripts/ieee_format.py, plus hostile inputs.

    python evals/run_fixtures.py

Reads the fixtures; writes only to a temporary directory it creates and removes.
Exit 0 if every case matches, 1 otherwise.
"""
import contextlib
import hashlib
import io
import json
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
FIXTURES = os.path.join(HERE, "fixtures")
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "scripts"))
import ieee_format  # noqa: E402


def digest(path):
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def call(args):
    out = io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(io.StringIO()):
        try:
            code = ieee_format.main(args)
        except SystemExit as exc:
            code = exc.code
    return code, out.getvalue()


def codes(issues):
    return sorted("%s:%s" % (i["severity"], i["code"]) for i in issues)


def run_case(case, tmp):
    args = []
    for a in case["args"]:
        if a.startswith("@TMP/"):
            args.append(os.path.join(tmp, a[5:]))
        elif a.endswith((".json", ".txt")) and not a.startswith("--"):
            args.append(os.path.join(FIXTURES, a))
        else:
            args.append(a)
    before = {n: digest(os.path.join(FIXTURES, n)) for n in os.listdir(FIXTURES)}
    code, out = call(args)
    problems = []
    if code != case["exit"]:
        problems.append("exit %r, wanted %r" % (code, case["exit"]))
    for n, h in before.items():
        if digest(os.path.join(FIXTURES, n)) != h:
            problems.append("fixture %s was modified" % n)
    for n in case.get("writes", []):
        if not os.path.exists(os.path.join(tmp, n)):
            problems.append("missing output %s" % n)
    if code in (0, 1):
        doc = json.loads(out, parse_constant=lambda c: (_ for _ in ()).throw(ValueError(c)))
        if "in_text" in case:
            got = [i["text"] for i in doc["in_text"]]
            if got != case["in_text"]:
                problems.append("in_text: got %r" % got)
        if "refs" in case:
            got = [r["text"] for r in doc["references"]]
            if got != case["refs"]:
                for i, (g, w) in enumerate(zip(got, case["refs"]), 1):
                    if g != w:
                        problems.append("ref %d: got %r wanted %r" % (i, g, w))
                if len(got) != len(case["refs"]):
                    problems.append("ref count %d" % len(got))
        for num, start in case.get("ref_starts", {}).items():
            if doc["references"][int(num) - 1]["text"] != start:
                problems.append("ref %s: got %r" % (num, doc["references"][int(num) - 1]["text"]))
        if "issue_codes" in case and codes(doc["issues"]) != sorted(case["issue_codes"]):
            problems.append("issues: got %r" % codes(doc["issues"]))
        for c in case.get("issue_codes_include", []):
            if c not in codes(doc["issues"]):
                problems.append("missing issue %s" % c)
        for k, v in case.get("summary", {}).items():
            if doc["summary"].get(k) != v:
                problems.append("summary %s: %r" % (k, doc["summary"].get(k)))
    return problems


def hostile(tmp):
    """Each of these must exit 2 with a one-line JSON error and no traceback."""
    files = {
        "huge_float.json": b'{"entries":[{"id":"a","year":1e400}],"citations":[["a"]]}',
        "nan.json": b'{"entries":NaN,"citations":[]}',
        "bigint.json": b'{"entries":[{"id":"a","year":' + b"9" * 5000 + b'}],"citations":[["a"]]}',
        "empty.json": b"",
        "badutf8.json": b'{"entries":"\xff\xfe"}',
        "deep.json": b"[" * 3000 + b"]" * 3000,
        "notobj.json": b"[1,2]",
        "empty_list.txt": b"   \n",
    }
    results = []
    for name, data in files.items():
        path = os.path.join(tmp, name)
        with open(path, "wb") as fh:
            fh.write(data)
        sub = "verify" if name.endswith(".txt") else "format"
        code, out = call([sub, path])
        ok = code == 2 and out.count("\n") == 1 and "error" in json.loads(out)
        results.append(("hostile " + name, ["exit %r, out %r" % (code, out[:80])] if not ok else []))
    code, out = call(["format", os.path.join(tmp, "absent.json")])
    results.append(("hostile missing path", [] if code == 2 else ["exit %r" % code]))
    return results


def main():
    with open(os.path.join(FIXTURES, "cases.json"), encoding="utf-8") as fh:
        cases = json.load(fh)["cases"]
    failed = total = 0
    with tempfile.TemporaryDirectory() as tmp:
        for case in cases:
            problems = run_case(case, tmp)
            print(("PASS " if not problems else "FAIL ") + case["name"])
            for p in problems:
                print("    " + p)
            failed += bool(problems)
            total += 1
        for name, problems in hostile(tmp):
            print(("PASS " if not problems else "FAIL ") + name)
            for p in problems:
                print("    " + p)
            failed += bool(problems)
            total += 1
    print("%d/%d cases passed" % (total - failed, total))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
