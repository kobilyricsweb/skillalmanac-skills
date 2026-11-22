#!/usr/bin/env python3
"""Run the fixture cases in fixtures/cases.json against scripts/wiki_audit.py.

    python evals/run_fixtures.py

Reads the fixture wikis; writes only inside a temporary folder it creates and
removes itself. It also proves the audit is read-only by hashing every fixture
file before and after the runs. Exit 0 if every check passes, 1 otherwise.
"""
import contextlib
import datetime
import hashlib
import io
import json
import os
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "scripts"))
import wiki_audit  # noqa: E402

FIXTURES = os.path.join(HERE, "fixtures")


def strict_loads(text):
    def refuse(name):
        raise ValueError("non-strict JSON constant " + name)
    return json.loads(text, parse_constant=refuse)


def run(args):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        try:
            code = wiki_audit.main(args)
        except SystemExit as exc:
            code = exc.code
    return code, out.getvalue()


def project(rep):
    return {
        "summary": rep["summary"],
        "ownerless_paths": [o["path"] for o in rep["ownerless"]],
        "stale_paths": [s["path"] for s in rep["stale"]],
        "undated": rep["undated"],
        "orphans": rep["orphans"],
        "entry_points": rep["entry_points"],
        "broken": [[b["source"], b["line"], b["reason"]] for b in rep["broken_links"]],
        "dup": [[d["a"], d["b"], d["relation"]] for d in rep["duplicate_titles"]],
        "identical_content": rep["identical_content"],
        "deep_pages": rep["deep_pages"],
        "plan": [[p["path"], p["action"], p["confidence"]] for p in rep["plan"]],
        "merge_into": {p["path"]: p["merge_into"] for p in rep["plan"] if "merge_into" in p},
    }


def fixture_case(case):
    args = [os.path.join(FIXTURES, case["args"][0])] + case["args"][1:]
    if not os.path.isdir(args[0]):
        args[0] = case["args"][0]
    code, out = run(args)
    problems = []
    if code != case["exit"]:
        problems.append("exit %r, wanted %r" % (code, case["exit"]))
    if case["expect"] and code in (0, 1):
        got = project(strict_loads(out))
        for key, want in case["expect"].items():
            if got.get(key) != want:
                problems.append("%s: got %r, wanted %r" % (key, got.get(key), want))
    return problems


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)


def mtime_checks():
    """Pages with no date inside them are dated by file modified time, and a collapse is reported."""
    problems = []
    tmp = tempfile.mkdtemp(prefix="wiki_audit_fx_")
    try:
        old = datetime.datetime(2020, 1, 1, tzinfo=datetime.timezone.utc).timestamp()
        for i in range(5):
            p = os.path.join(tmp, "page%d.md" % i)
            write(p, "# Page %d\n\nOwner: Ana\n\nBody text.\n" % i)
            os.utime(p, (old, old))
        code, out = run([tmp, "--today", "2026-11-21"])
        rep = strict_loads(out)
        if code != 0 or rep["summary"]["stale"] != 5 or any(s["date_source"] != "mtime" for s in rep["stale"]):
            problems.append("mtime: expected 5 stale pages dated by mtime, got %r" % rep["summary"])
        if not any(n.startswith("mtime_unreliable") for n in rep["notes"]):
            problems.append("mtime: expected the mtime_unreliable note")
        code, out = run([tmp, "--today", "2026-11-21", "--mtime-fallback", "ignore"])
        rep = strict_loads(out)
        if rep["summary"]["stale"] != 0 or rep["summary"]["undated"] != 5:
            problems.append("mtime ignore: expected 0 stale and 5 undated, got %r" % rep["summary"])
        shutil.rmtree(tmp)
        os.makedirs(tmp)
        code, out = run([tmp])
        rep = strict_loads(out)
        if code != 0 or rep["summary"]["pages"] != 0:
            problems.append("empty folder: expected exit 0 and 0 pages")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return problems


def unparsed_date_checks():
    """A date field that cannot be read makes the page undated with a warning, never an mtime date."""
    problems = []
    tmp = tempfile.mkdtemp(prefix="wiki_audit_fx_")
    try:
        write(os.path.join(tmp, "amb.md"), "---\ntitle: Ambiguous\nowner: Ana\nupdated: 03/04/2026\n---\n\nBody text.\n")
        code, out = run([tmp, "--today", "2026-11-21"])
        rep = strict_loads(out)
        if rep["undated"] != ["amb.md"] or rep["summary"]["stale"] != 0:
            problems.append("unparsed: expected amb.md undated and not stale, got %r" % rep["summary"])
        if not any(n.startswith("WARNING unparsed_date") for n in rep["notes"]):
            problems.append("unparsed: expected the unparsed_date warning, got %r" % rep["notes"])
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return problems


def notion_style_checks():
    """Percent-encoded links to files with a 32-hex id resolve; the id is dropped from titles."""
    problems = []
    tmp = tempfile.mkdtemp(prefix="wiki_audit_fx_")
    pid = "0123456789abcdef0123456789abcdef"
    cid = "fedcba9876543210fedcba9876543210"
    try:
        write(os.path.join(tmp, "Team Home %s.md" % pid),
              "Owner: Ana\nLast edited time: March 3, 2026 10:00 AM\n\n[Kid](Team%%20Home/Kid%%20Page%%20%s.md)\n[Bad](Team%%20Home/Nope%%20Page.md)\n" % cid)
        write(os.path.join(tmp, "Team Home", "Kid Page %s.md" % cid), "Owner: Bo\nLast edited time: April 9, 2026\n\nChild body.\n")
        code, out = run([tmp, "--today", "2026-11-21", "--mtime-fallback", "ignore", "--include-pages"])
        rep = strict_loads(out)
        titles = sorted(p["title"] for p in rep["pages"])
        if titles != ["Kid Page", "Team Home"]:
            problems.append("notion titles: got %r" % titles)
        if [b["target"] for b in rep["broken_links"]] != ["Team%20Home/Nope%20Page.md"]:
            problems.append("notion links: got %r" % rep["broken_links"])
        if rep["summary"]["ownerless"] != 0 or rep["summary"]["undated"] != 0:
            problems.append("notion owner/date lines not read: %r" % rep["summary"])
        if rep["orphans"] != ["Team Home %s.md" % pid]:  # the child is linked, the parent is not
            problems.append("notion orphans: got %r" % rep["orphans"])
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return problems


def tree_hash(root):
    h = hashlib.sha256()
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames.sort()
        for fn in sorted(filenames):
            full = os.path.join(dirpath, fn)
            h.update(os.path.relpath(full, root).encode("utf-8"))
            with open(full, "rb") as fh:
                h.update(fh.read())
    return h.hexdigest()


def main():
    before = tree_hash(FIXTURES)
    with open(os.path.join(FIXTURES, "cases.json"), encoding="utf-8") as fh:
        cases = json.load(fh)["cases"]
    failed = 0
    for case in cases:
        problems = fixture_case(case)
        print(("PASS " if not problems else "FAIL ") + case["name"])
        for p in problems:
            print("    " + p)
        failed += bool(problems)
    problems = mtime_checks()
    print(("PASS " if not problems else "FAIL ") + "mtime fallback, mtime collapse note, empty folder")
    for p in problems:
        print("    " + p)
    failed += bool(problems)
    problems = notion_style_checks()
    print(("PASS " if not problems else "FAIL ") + "notion-style encoded links, ids in names, owner and date lines")
    for p in problems:
        print("    " + p)
    failed += bool(problems)
    problems = unparsed_date_checks()
    print(("PASS " if not problems else "FAIL ") + "unparsed date field -> undated with warning, no mtime fallback")
    for p in problems:
        print("    " + p)
    failed += bool(problems)
    unchanged = tree_hash(FIXTURES) == before
    print(("PASS " if unchanged else "FAIL ") + "fixture files unchanged after all runs (read-only)")
    failed += not unchanged
    total = len(cases) + 4
    print("%d/%d checks passed" % (total - failed, total))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
