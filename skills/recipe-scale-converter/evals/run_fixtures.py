#!/usr/bin/env python3
"""Run the fixture cases in fixtures/cases.json against scripts/scale_recipe.py.

    python evals/run_fixtures.py

Also runs the write-safety checks: the script must refuse an --out path that is the
recipe or the density file (even with --force), refuse to replace an existing file
without --force, and write a valid JSON file to a fresh path. Those checks work on
copies in a temporary directory. Reads fixtures; writes only inside that temporary
directory. Exit 0 if everything passes, 1 otherwise.
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
import scale_recipe  # noqa: E402


def run(args):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        try:
            code = scale_recipe.main(args)
        except SystemExit as exc:  # argparse usage errors
            code = exc.code
    return code, out.getvalue(), err.getvalue()


def sha(path):
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def check_case(case):
    args = [os.path.join(FIX, a) if a.endswith((".txt", ".csv")) else a for a in case["args"]]
    code, out, _ = run(args)
    problems = []
    if code != case["exit"]:
        problems.append("exit %r, wanted %r" % (code, case["exit"]))
    exp = case["expect"]
    if exp and code in (0, 1):
        rep = json.loads(out)
        got = {
            "factor": rep["factor"]["value"],
            "scaled_list": rep["scaled_list"],
            "warning_codes": [w["code"] for w in rep["warnings"]],
            "flags": [l["flags"] for l in rep["lines"]],
            "confidence": [l["confidence"] for l in rep["lines"]],
            "unparsed_count": len(rep["unparsed"]),
            "unparsed_reasons": [u["reason"] for u in rep["unparsed"]],
        }
        for key, want in exp.items():
            if got[key] != want:
                problems.append("%s: got %r, wanted %r" % (key, got[key], want))
    return problems


def check_write_safety():
    results = []
    tmp = tempfile.mkdtemp(prefix="recipe_fixture_")
    try:
        recipe = os.path.join(tmp, "recipe.txt")
        dens = os.path.join(tmp, "dens.csv")
        shutil.copy(os.path.join(FIX, "cake.txt"), recipe)
        shutil.copy(os.path.join(FIX, "density_user.csv"), dens)
        before_r, before_d = sha(recipe), sha(dens)

        code, _, _ = run([recipe, "--factor", "2", "--out", recipe, "--force"])
        results.append(("refuse --out equal to the recipe, even with --force", code == 2 and sha(recipe) == before_r))
        code, _, _ = run([recipe, "--factor", "2", "--density", dens, "--out", dens, "--force"])
        results.append(("refuse --out equal to the density file, even with --force", code == 2 and sha(dens) == before_d))

        link_ok = True
        link = os.path.join(tmp, "link.txt")
        try:
            os.link(recipe, link)  # a hard link resolves to the same file
        except (OSError, NotImplementedError, AttributeError):
            link_ok = None
        if link_ok:
            code, _, _ = run([recipe, "--factor", "2", "--out", link, "--force"])
            results.append(("refuse --out that is a hard link to the recipe", code == 2 and sha(recipe) == before_r))

        target = os.path.join(tmp, "result.json")
        code, _, _ = run([recipe, "--factor", "2", "--out", target])
        wrote = code == 0 and os.path.exists(target)
        valid = False
        if wrote:
            with open(target, encoding="utf-8") as fh:
                valid = json.load(fh)["factor"]["value"] == 2.0
        results.append(("write a valid JSON report to a fresh path", wrote and valid and sha(recipe) == before_r))
        code, _, _ = run([recipe, "--factor", "3", "--out", target])
        results.append(("refuse to replace an existing output without --force", code == 2))
        code, _, _ = run([recipe, "--factor", "3", "--out", target, "--force"])
        results.append(("replace an existing output with --force", code == 0))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return results


def main():
    cases = json.load(open(os.path.join(FIX, "cases.json"), encoding="utf-8"))["cases"]
    failed = 0
    total = 0
    for case in cases:
        problems = check_case(case)
        total += 1
        print(("PASS " if not problems else "FAIL ") + case["id"])
        for p in problems:
            print("    " + p)
        failed += bool(problems)
    for label, ok in check_write_safety():
        total += 1
        print(("PASS " if ok else "FAIL ") + "write-safety: " + label)
        failed += not ok
    print("%d/%d checks passed" % (total - failed, total))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
