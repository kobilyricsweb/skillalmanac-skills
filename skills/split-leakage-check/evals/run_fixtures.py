#!/usr/bin/env python3
"""Run the fixture cases against scripts/check_leakage.py.

    python evals/run_fixtures.py

Reads the fixtures in evals/fixtures and evals/files. Writes only inside a
temporary directory (generated data for the class-drift, target-leakage and
write-refusal cases), removed at the end. Exit 0 if every case matches.
Expected values were worked out by hand, see VERIFICATION.md.
"""
import contextlib
import hashlib
import io
import json
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "scripts"))
import check_leakage  # noqa: E402

FX = os.path.join(HERE, "fixtures")
T3 = os.path.join(HERE, "files", "t3-patient-visits")


def run(args):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = check_leakage.main(args)
    rep = json.loads(out.getvalue()) if out.getvalue().strip() else None
    return code, rep, err.getvalue()


def dig(obj, path):
    for part in path.split("."):
        obj = obj[int(part)] if isinstance(obj, list) else obj[part]
    return obj


def write(path, lines):
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(lines) + "\n")


def sha(path):
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def make_generated(tmp):
    # 80 rows; label pos when i is even. status copies the label; score is
    # separable by one threshold; noise (i mod 7) has both labels in each value.
    rows = ["text,status,score,noise,label"]
    for i in range(1, 81):
        pos = i % 2 == 0
        rows.append("item %d,%s,%d,%d,%s" % (i, "refunded" if pos else "active", i + 100 if pos else i, i % 7, "pos" if pos else "neg"))
    write(os.path.join(tmp, "g_train.csv"), rows[:41])
    write(os.path.join(tmp, "g_test.csv"), [rows[0]] + rows[41:])
    # Drift: train 60/60, test 96 pos / 24 neg, valid 20 pos only.
    head = "text,label"
    write(os.path.join(tmp, "d_train.csv"), [head] + ["alpha %d,%s" % (i, "pos" if i < 60 else "neg") for i in range(120)])
    write(os.path.join(tmp, "d_test.csv"), [head] + ["beta %d,%s" % (i, "pos" if i < 96 else "neg") for i in range(120)])
    write(os.path.join(tmp, "d_valid.csv"), [head] + ["gamma %d,pos" % i for i in range(20)])


def cases(tmp):
    bad = ["--split", "train=" + FX + "/bad_train.csv", "--split", "test=" + FX + "/bad_test.csv",
           "--id-col", "id", "--text-cols", "text", "--group-col", "user", "--date-col", "ts", "--label-col", "label"]
    clean = ["--split", "train=" + FX + "/clean_train.csv", "--split", "test=" + FX + "/clean_test.csv",
             "--id-col", "id", "--text-cols", "text", "--group-col", "user", "--date-col", "ts", "--label-col", "label"]
    t3 = ["--split", "train=" + T3 + "/train.csv", "--split", "valid=" + T3 + "/valid.csv", "--split", "test=" + T3 + "/test.csv",
          "--group-col", "patient", "--date-col", "visit_date", "--label-col", "outcome", "--text-cols", "note"]
    gen = ["--split", "train=" + tmp + "/g_train.csv", "--split", "test=" + tmp + "/g_test.csv", "--text-cols", "text", "--label-col", "label"]
    drift = ["--split", "train=" + tmp + "/d_train.csv", "--split", "test=" + tmp + "/d_test.csv", "--split", "valid=" + tmp + "/d_valid.csv",
             "--text-cols", "text", "--label-col", "label"]
    return [
        ("bad: exact, near, group, time", bad, 1, {
            "verdict.status": "fail", "exact_overlaps.count": 1, "exact_overlaps.examples.0.labels": ["spam"],
            "exact_overlaps.examples.0.splits": ["train", "test"],
            "near_duplicates.count": 1, "near_duplicates.pairs.0.row_id_a": "t3", "near_duplicates.pairs.0.row_id_b": "s2",
            "near_duplicates.pairs.0.similarity": 0.8571,
            "group_overlaps.groups_total": 6, "group_overlaps.groups_shared": 1,
            "time_violations.violations.0.later_rows_before_that": 2, "time_violations.violations.0.share_of_later_split": 0.6667,
            "class_balance.drift": [], "target_leakage.claim_made": False}),
        ("bad: threshold above the pair similarity drops the near pair", bad + ["--threshold", "0.9"], 1, {
            "near_duplicates.count": 0, "verdict.status": "fail"}),
        ("clean: no signal", clean, 0, {
            "verdict.status": "pass", "exact_overlaps.count": 0, "near_duplicates.count": 0, "group_overlaps.groups_shared": 0,
            "time_violations.violations": []}),
        ("group leakage across three splits", t3, 1, {
            "verdict.status": "fail", "group_overlaps.groups_total": 5, "group_overlaps.groups_shared": 2,
            "group_overlaps.per_split.0.share": 0.6667, "exact_overlaps.count": 0, "time_violations.violations": []}),
        ("jsonl, no id column: line numbers are row ids", ["--split", "a=" + FX + "/jsonl_a.jsonl", "--split", "b=" + FX + "/jsonl_b.jsonl"], 1, {
            "exact_overlaps.count": 1, "exact_overlaps.examples.0.rows.0.row_id": "1", "exact_overlaps.examples.0.rows.1.row_id": "1"}),
        ("target leakage: copy column and threshold-separable column", gen, 1, {
            "verdict.status": "fail", "target_leakage.claim_made": True, "target_leakage.columns_checked": 4,
            "target_leakage.suspects.0.column": "status", "target_leakage.suspects.0.kind": "perfect",
            "target_leakage.suspects.1.column": "score", "target_leakage.suspects.1.kind": "threshold_separable",
            "target_leakage.suspects.2": KeyError}),
        ("class drift and small-split floor", drift, 1, {
            "verdict.status": "warn", "class_balance.drift.0.class": "neg", "class_balance.drift.0.difference": 0.3,
            "class_balance.drift.1.class": "pos", "class_balance.per_split.2.enough_for_drift_claim": False,
            "class_balance.missing_classes": [{"class": "neg", "split": "valid"}]}),
        ("missing column exits 2", ["--split", "a=" + FX + "/clean_train.csv", "--split", "b=" + FX + "/clean_test.csv", "--group-col", "nope"], 2, {}),
        ("fewer than two splits exits 2", ["--split", "a=" + FX + "/clean_train.csv"], 2, {}),
    ]


def main():
    failed = 0
    total = 0
    with tempfile.TemporaryDirectory() as tmp:
        make_generated(tmp)
        for label, args, want_exit, expect in cases(tmp):
            total += 1
            code, rep, _err = run(args)
            problems = []
            if code != want_exit:
                problems.append("exit %r, wanted %r" % (code, want_exit))
            if expect and rep is not None:
                for path, want in expect.items():
                    try:
                        got = dig(rep, path)
                    except (KeyError, IndexError):
                        got = KeyError
                    if got != want:
                        problems.append("%s: got %r, wanted %r" % (path, got, want))
            print(("PASS " if not problems else "FAIL ") + label)
            for p in problems:
                print("    " + p)
            failed += bool(problems)

        # Write-safety: --out must never land on an input, even with --force.
        total += 1
        victim = os.path.join(tmp, "victim.csv")
        write(victim, ["text", "a b c d", "e f g h"])
        before = sha(victim)
        other = os.path.join(tmp, "other.csv")
        write(other, ["text", "x y z w"])
        problems = []
        for extra in (["--out", victim], ["--out", victim, "--force"]):
            code, _rep, _err = run(["--split", "a=" + victim, "--split", "b=" + other] + extra)
            if code != 2:
                problems.append("writing over an input with %s exited %r, wanted 2" % (" ".join(extra), code))
        if sha(victim) != before:
            problems.append("input file changed")
        report_path = os.path.join(tmp, "report.json")
        code, _rep, _err = run(["--split", "a=" + victim, "--split", "b=" + other, "--out", report_path])
        if code not in (0, 1) or not os.path.isfile(report_path):
            problems.append("fresh --out was not written (exit %r)" % code)
        code, _rep, _err = run(["--split", "a=" + victim, "--split", "b=" + other, "--out", report_path])
        if code != 2:
            problems.append("existing --out without --force exited %r, wanted 2" % code)
        code, _rep, _err = run(["--split", "a=" + victim, "--split", "b=" + other, "--out", report_path, "--force"])
        if code not in (0, 1):
            problems.append("--force on a non-input report exited %r" % code)
        print(("PASS " if not problems else "FAIL ") + "write-safety: report never overwrites an input")
        for p in problems:
            print("    " + p)
        failed += bool(problems)
    print("%d/%d cases passed" % (total - failed, total))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
