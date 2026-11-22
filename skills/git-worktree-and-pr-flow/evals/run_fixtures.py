#!/usr/bin/env python3
"""Run the cases in fixtures/cases.json against scripts/repo_branch_audit.py.

    python evals/run_fixtures.py

The fake repositories are described in fixtures/repos.json (a .git folder cannot
be committed inside another repository). They are written to a fresh temporary
directory, audited with a fixed clock, then deleted. Nothing else is written.
Exit 0 if every case matches, 1 otherwise.
"""
import contextlib
import io
import json
import os
import re
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "scripts"))
import repo_branch_audit  # noqa: E402


def materialize(spec, root):
    now = spec["now"]
    for rel, content in spec["files"].items():
        content = content.replace("{ROOT}", root.replace(os.sep, "/"))
        content = re.sub(r"\{NOW-(\d+)\}", lambda m: str(now - int(m.group(1))), content)
        path = os.path.join(root, *rel.split("/"))
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8", newline="") as handle:
            handle.write(content)
        age = spec["age_seconds"].get(rel, spec["default_age_seconds"])
        os.utime(path, (now - age, now - age))


def run_case(case, root, now):
    args = [os.path.join(root, *case["repo"].split("/"))] + case.get("args", []) + ["--now", str(now)]
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        try:
            code = repo_branch_audit.main(args)
        except SystemExit as exc:
            code = exc.code
    problems = []
    if code != case["exit"]:
        problems.append(f"exit {code}, wanted {case['exit']}")
    if code in (0, 1):
        rep = json.loads(out.getvalue())
        exp = case["expect"]
        got = {
            "ok": rep["ok"], "counts": rep["counts"],
            "findings": [[f["severity"], f["code"], f["subject"]] for f in rep["findings"]],
            "worktrees": [[w["id"], w["exists"]] for w in rep["worktrees"]],
            "branches": [b["name"] for b in rep["branches"]],
        }
        for key, want in exp.items():
            if key == "details":
                details = {f"{f['code']}|{f['subject']}": f["detail"] for f in rep["findings"]}
                for k, frag in want.items():
                    if frag not in details.get(k, ""):
                        problems.append(f"detail {k}: {details.get(k)!r} lacks {frag!r}")
            elif got.get(key) != want:
                problems.append(f"{key}: got {got.get(key)!r}, wanted {want!r}")
    return problems


def main():
    spec = json.load(open(os.path.join(HERE, "fixtures", "repos.json"), encoding="utf-8"))
    cases = json.load(open(os.path.join(HERE, "fixtures", "cases.json"), encoding="utf-8"))["cases"]
    root = tempfile.mkdtemp(prefix="repo_audit_fixtures_")
    failed = 0
    try:
        materialize(spec, root)
        for case in cases:
            problems = run_case(case, root, spec["now"])
            print(("PASS " if not problems else "FAIL ") + case["name"])
            for p in problems:
                print("    " + p)
            failed += bool(problems)
    finally:
        shutil.rmtree(root, ignore_errors=True)
    print(f"{len(cases) - failed}/{len(cases)} cases passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
