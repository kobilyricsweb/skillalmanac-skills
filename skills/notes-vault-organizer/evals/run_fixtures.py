#!/usr/bin/env python3
"""Run the fixture cases in fixtures/cases.json against scripts/vault_scan.py.

    python evals/run_fixtures.py

Reads fixtures. It writes one temporary plan file for the scan-then-validate
case and deletes it afterwards; nothing in the repository changes. Cases marked
"readonly" also prove the scan left the vault byte-identical, using a hash
routine that shares no code with the script. Exit 0 if every case passes.
"""
import contextlib
import hashlib
import io
import json
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
FIX = os.path.join(HERE, "fixtures")
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "scripts"))
import vault_scan  # noqa: E402


def tree_hash(folder):
    h = hashlib.sha256()
    for root, dirs, files in os.walk(folder):
        dirs.sort()
        for name in sorted(files):
            p = os.path.join(root, name)
            h.update(os.path.relpath(p, folder).encode("utf-8"))
            with open(p, "rb") as fh:
                h.update(fh.read())
    return h.hexdigest()


def run(args):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = vault_scan.main(args)
    return code, out.getvalue()


def lookup(doc, path):
    """Dotted path; '*' spreads over a list, '#' is the length of a list."""
    cur, spread = [doc], False
    for part in path.split("."):
        nxt = []
        for node in cur:
            if part == "#":
                nxt.append(len(node))
            elif part == "*":
                nxt.extend(node)
                spread = True
            else:
                nxt.append(node.get(part) if isinstance(node, dict) else None)
        cur = nxt
    return cur if spread else cur[0]


def reject_constant(name):
    raise ValueError("non-strict JSON constant " + name)


def check(case, args):
    problems = []
    vault = os.path.join(FIX, case["readonly"]) if case.get("readonly") else None
    before = tree_hash(vault) if vault else None
    code, text = run(args)
    if code != case["exit"]:
        problems.append("exit %s, wanted %s" % (code, case["exit"]))
    if vault and tree_hash(vault) != before:
        problems.append("vault files changed during the scan")
    if code in (0, 1) and text.strip():
        doc = json.loads(text, parse_constant=reject_constant)
        for path, want in case["expect"].items():
            got = lookup(doc, path)
            if got != want:
                problems.append("%s: got %r, wanted %r" % (path, got, want))
    return problems


def main():
    with open(os.path.join(FIX, "cases.json"), encoding="utf-8") as fh:
        cases = json.load(fh)["cases"]
    failed = 0
    for case in cases:
        tmp = None
        if "scan_then_validate" in case:
            vault = os.path.join(FIX, case["scan_then_validate"])
            _, scan_text = run(["scan", vault])
            fd, tmp = tempfile.mkstemp(suffix=".json")
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                fh.write(scan_text)
            args = ["validate-plan", vault, tmp]
        else:
            args = [case["args"][0]] + [os.path.join(FIX, a) if i == 0 or a.endswith(".json") else a
                                        for i, a in enumerate(case["args"][1:])]
        problems = check(case, args)
        if tmp:
            os.remove(tmp)
        print(("PASS " if not problems else "FAIL ") + case["name"])
        for p in problems:
            print("    " + p)
        failed += bool(problems)
    print("%d/%d cases passed" % (len(cases) - failed, len(cases)))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
