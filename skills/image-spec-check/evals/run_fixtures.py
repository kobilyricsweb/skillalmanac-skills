#!/usr/bin/env python3
"""Run the cases in fixtures/cases.json against scripts/image_spec_check.py.

    python evals/run_fixtures.py

Sample images are generated into a temporary folder (evals/make_samples.py), so
nothing is written inside the skill folder. Exit 0 if every case matches, 1
otherwise.
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
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "scripts"))
import image_spec_check  # noqa: E402
import make_samples  # noqa: E402


def digest(path):
    with open(path, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()


def dig(obj, dotted):
    for part in dotted.split("."):
        if not isinstance(obj, dict) or part not in obj:
            return "<absent>"
        obj = obj[part]
    return obj


def run_case(case, work):
    group_dir = os.path.join(work, "images")
    make_samples.write_group(group_dir, case["group"])
    specs_copy = os.path.join(work, "specs_copy.csv")
    shutil.copyfile(os.path.join(HERE, "fixtures", "specs.csv"), specs_copy)
    subs = {"{dir}": group_dir, "{specs}": os.path.join(HERE, "fixtures", "specs.csv"), "{specs_copy}": specs_copy,
            "{badspecs}": os.path.join(HERE, "fixtures", "specs_bad_column.csv"), "{tmp}": work}

    def sub(text):
        for key, value in subs.items():
            text = text.replace(key, value)
        return text

    args = [sub(a) for a in case["args"]]
    before = {p: digest(sub(p)) for p in case.get("unchanged", [])}
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = image_spec_check.main(args)
    problems = []
    if code != case["exit"]:
        problems.append("exit %s, wanted %s" % (code, case["exit"]))
    for path, old in before.items():
        if digest(sub(path)) != old:
            problems.append("input was modified: %s" % path)
    report = json.loads(out.getvalue())
    if case["exit"] == 2 and report.get("ok") is not False:
        problems.append("error exit without an ok:false JSON body")
    if "out_matches_stdout" in case:
        with open(sub(case["out_matches_stdout"]), encoding="utf-8") as handle:
            if json.load(handle) != report:
                problems.append("--out file differs from stdout")
    exp = case["expect"]
    if exp and code in (0, 1):
        if report["ok"] != exp["ok"]:
            problems.append("ok: got %r" % report["ok"])
        for key, want in exp["by_status"].items():
            if report["summary"]["by_status"].get(key) != want:
                problems.append("by_status[%s]: got %r, wanted %r" % (key, report["summary"]["by_status"].get(key), want))
        files = {f["name"]: f for f in report["files"]}
        if sorted(files) != sorted(exp["statuses"]):
            problems.append("files: got %s" % sorted(files))
        for name, specs in exp["statuses"].items():
            for spec, (status, issues) in specs.items():
                res = files.get(name, {}).get("results", {}).get(spec)
                got = [res["status"], res["issues"]] if res else None
                if got != [status, issues]:
                    problems.append("%s/%s: got %r, wanted %r" % (name, spec, got, [status, issues]))
        for ex in exp["extras"]:
            entry = files.get(ex["file"], {})
            target = entry if ex["spec"] is None else entry.get("results", {}).get(ex["spec"], {})
            got = dig(target, ex["path"])
            if got != ex["value"]:
                problems.append("%s %s %s: got %r, wanted %r" % (ex["file"], ex["spec"], ex["path"], got, ex["value"]))
    return problems


def main():
    with open(os.path.join(HERE, "fixtures", "cases.json"), encoding="utf-8") as handle:
        cases = json.load(handle)["cases"]
    failed = 0
    for case in cases:
        work = tempfile.mkdtemp(prefix="isc_fixture_")
        try:
            problems = run_case(case, work)
        finally:
            shutil.rmtree(work, ignore_errors=True)
        print(("PASS " if not problems else "FAIL ") + case["id"])
        for problem in problems:
            print("     " + problem)
        failed += bool(problems)
    print("%d/%d cases passed" % (len(cases) - failed, len(cases)))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
