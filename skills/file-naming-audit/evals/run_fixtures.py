#!/usr/bin/env python3
"""Run the fixture cases in fixtures/cases.json against scripts/naming_audit.py.

    python evals/run_fixtures.py

Reads fixtures. Writes only inside a temporary folder it creates and removes (the
output-safety checks need somewhere to write). Also checks that running the audit
leaves the fixture tree byte-for-byte unchanged. Exit 0 if every check passes, 1 otherwise.
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
import naming_audit  # noqa: E402


def run(args):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        try:
            code = naming_audit.main(args)
        except SystemExit as exc:
            code = exc.code
    return code, out.getvalue(), err.getvalue()


def view(rep):
    return {
        "pattern": rep["convention"]["pattern"],
        "source": rep["convention"]["source"],
        "files_total": rep["files_total"],
        "dirs_total": rep["dirs_total"],
        "ignored": rep["ignored"],
        "violations_by_code": rep["violations_by_code"],
        "fix_by_path": {v["path"]: v["fix"] for v in rep["violations"]},
        "rename_plan": [[r["old"], r["new"]] for r in rep["rename_plan"]],
        "dir_renames": [[r["old"], r["new"]] for r in rep["dir_renames"]],
        "held_back": [h["path"] for h in rep["held_back"]],
        "collisions": [c["paths"] for c in rep["collisions"]],
        "needs_decision": {n["path"]: n["remaining"] for n in rep["needs_decision"]},
        "version_series": [{k: s[k] for k in ("series", "versions", "latest_by_number", "latest_by_mtime",
                                              "latest_ambiguous", "mtime_disagrees", "duplicate_numbers", "gaps")}
                           for s in rep["version_series"]],
        "plan_is_collision_free": rep["plan_is_collision_free"],
    }


def run_case(case):
    args = [os.path.join(FIX, a[1:]) if a.startswith("@") else a for a in case["args"]]
    code, out, err = run(args)
    problems = []
    if code != case["exit"]:
        problems.append("exit %r, wanted %r" % (code, case["exit"]))
    if code in (0, 1):
        got = view(json.loads(out))
        for key, want in case["expect"].items():
            if got.get(key) != want:
                problems.append("%s: got %r, wanted %r" % (key, got.get(key), want))
    return problems


def tree_digest(path):
    h = hashlib.sha256()
    for cur, dirs, files in os.walk(path):
        dirs.sort()
        for f in sorted(files):
            full = os.path.join(cur, f)
            h.update(os.path.relpath(full, path).encode("utf-8"))
            with open(full, "rb") as fh:
                h.update(fh.read())
    return h.hexdigest()


def special_checks():
    results = []
    tmp = tempfile.mkdtemp(prefix="naming_audit_fixture_")
    try:
        def check(label, ok, detail=""):
            results.append((label, ok, detail))

        tree = os.path.join(FIX, "tree_basic")
        before = tree_digest(tree)
        conv = "{date}_{name}_v{nn}"
        code, out, err = run([tree, "--convention", conv, "--plan", os.path.join(tmp, "plan.csv")])
        check("walk leaves the audited tree unchanged", tree_digest(tree) == before)
        plan_text = open(os.path.join(tmp, "plan.csv"), encoding="utf-8", newline="").read()
        want = "old,new\nClient Files/2026-03-01_brief_v1.txt,Client-Files/2026-03-01_brief_v01.txt\nClient Files/Meeting Notes.txt,Client-Files/Meeting Notes.txt\n"
        check("plan CSV content", plan_text == want, repr(plan_text))

        listing = os.path.join(tmp, "listing.txt")
        shutil.copy(os.path.join(FIX, "listing_messy.txt"), listing)
        code, out, err = run(["--listing", listing, "--convention", conv, "--plan", listing, "--force"])
        check("plan equal to the listing is refused even with --force", code == 2 and "is an input" in err, "%r %r" % (code, err))
        code, out, err = run([tree, "--plan", os.path.join(tree, "readme.txt"), "--force"])
        check("plan equal to a scanned file is refused even with --force", code == 2 and "is an input" in err, "%r %r" % (code, err))
        check("scanned file still unchanged", tree_digest(tree) == before)
        code, out, err = run([tree, "--report", os.path.join(tree, "report.json")])
        check("report inside the audited folder is refused", code == 2 and "inside the audited folder" in err, "%r %r" % (code, err))
        check("nothing was created in the audited folder", tree_digest(tree) == before)
        existing = os.path.join(tmp, "exists.csv")
        with open(existing, "w", encoding="utf-8") as fh:
            fh.write("keep me\n")
        code, out, err = run(["--listing", listing, "--convention", conv, "--plan", existing])
        check("existing plan file needs --force", code == 2 and open(existing, encoding="utf-8").read() == "keep me\n", "%r %r" % (code, err))
        code, out, err = run(["--listing", listing, "--convention", conv, "--plan", existing, "--force"])
        check("--force replaces an existing non-input plan file", code == 1 and open(existing, encoding="utf-8").read().startswith("old,new\n"), "%r %r" % (code, err))
        both = os.path.join(tmp, "both.json")
        code, out, err = run(["--listing", listing, "--convention", conv, "--plan", both, "--report", both])
        check("plan and report must differ", code == 2 and "different files" in err, "%r %r" % (code, err))
        code, out, err = run(["--listing", listing, "--convention", "{date}_{name}_{nn}"])
        check("convention with {nn} but no v literal is a usage error", code == 2 and "ending in v" in err, "%r %r" % (code, err))
        code, out, err = run([os.path.join(tmp, "no_such_folder")])
        check("missing folder exits 2", code == 2, "%r %r" % (code, err))
        code, out, err = run([])
        check("no root and no listing exits 2", code == 2, "%r %r" % (code, err))
        code, out, err = run(["--listing", os.path.join(tmp, "no_such_listing.txt")])
        check("missing listing exits 2", code == 2, "%r %r" % (code, err))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return results


def main():
    cases = json.load(open(os.path.join(FIX, "cases.json"), encoding="utf-8"))["cases"]
    failed = 0
    for case in cases:
        problems = run_case(case)
        print(("PASS " if not problems else "FAIL ") + case["name"])
        for p in problems:
            print("    " + p)
        failed += bool(problems)
    total = len(cases)
    for label, ok, detail in special_checks():
        print(("PASS " if ok else "FAIL ") + label)
        if not ok:
            print("    " + detail)
        failed += not ok
        total += 1
    print("%d/%d checks passed" % (total - failed, total))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
