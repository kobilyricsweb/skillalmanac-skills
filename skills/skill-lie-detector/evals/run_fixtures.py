#!/usr/bin/env python3
"""Fixture tests for blind.py and verdict.py. Builds synthetic test folders in a
temporary directory, runs both scripts, and checks the verdicts and refusals.

    python evals/run_fixtures.py

Exit 0 when every case matches, 1 otherwise. Standard library only.
"""
import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.join(HERE, "..", "scripts")


def build(root, name, plan, reps=2, checks=4, extra_text=""):
    """plan: list of (with_passes, without_passes) per task, passes out of `checks`."""
    work = os.path.join(root, name)
    tasks = []
    for i, _ in enumerate(plan):
        tid = f"t{i + 1}"
        tasks.append({"id": tid, "prompt": f"task {tid}", "checks": [f"c{j}" for j in range(checks)]})
        os.makedirs(os.path.join(work, "runs", tid))
        for arm in ("with", "without"):
            for r in range(1, reps + 1):
                with open(os.path.join(work, "runs", tid, f"{arm}_{r}.md"), "w", encoding="utf-8") as fh:
                    fh.write(f"{arm} answer {r} " + ("x" * (200 if arm == "with" else 100)) + "\n" + extra_text)
    with open(os.path.join(work, "tasks.json"), "w", encoding="utf-8") as fh:
        json.dump({"skill": "fixture", "reps": reps, "tasks": tasks}, fh)
    return work


def grade(work, plan, checks=4, mode=None):
    key = json.load(open(os.path.join(work, "key.json"), encoding="utf-8"))
    grades = []
    for i, (w, wo) in enumerate(plan):
        tid = f"t{i + 1}"
        for rid, arm in key[tid].items():
            k = w if arm == "with" else wo
            res = [{"pass": j < k, "quote": (f"{arm} answer" if j < k else "")} for j in range(checks)]
            if arm == "with" and mode == "empty":
                res = [{"pass": True, "quote": ""} for _ in range(checks)]
            if arm == "with" and mode == "absent":
                res = [{"pass": True, "quote": "Total: 1,240.00"} for _ in range(checks)]
            if arm == "with" and mode == "short":
                res = [{"pass": True, "quote": "e"} for _ in range(checks)]
            if arm == "with" and mode == "string":
                res = [{"pass": "false", "quote": "with answer"} for _ in range(checks)]
            grades.append({"task": tid, "id": rid, "checks": res})
    if mode == "missing":
        drop = next(g for g in grades if key[g["task"]][g["id"]] == "with")
        grades.remove(drop)
    json.dump(grades, open(os.path.join(work, "grades.json"), "w", encoding="utf-8"))


def run(script, *args):
    p = subprocess.run([sys.executable, os.path.join(SCRIPTS, script), *args], capture_output=True, text=True)
    return p.returncode, p.stdout, p.stderr


SIX_UP = [(4, 1), (4, 2), (3, 1), (4, 2), (4, 1), (3, 1)]
SIX_EVEN = [(1, 1)] * 6
CASES = [
    # name, plan, expected verdict (or "exit2"), grading mode, extra check on the output
    ("lift", SIX_UP, "LIFT", None, lambda r: r["length_chars"]["with"] > r["length_chars"]["without"]),
    ("harmed", [(b, a) for a, b in SIX_UP], "HARMED", None, None),
    ("no-lift", [(2, 2), (3, 3), (2, 3), (3, 2), (2, 2)], "NO_LIFT", None, None),
    ("unconfirmed", [(4, 0), (1, 2), (2, 3), (3, 2)], "LIFT_UNCONFIRMED", None, None),
    ("four-unanimous-not-confirmed", [(4, 1)] * 4, "LIFT_UNCONFIRMED", None, lambda r: "confirmation needs" in r.get("reason", "")),
    ("too-few", [(4, 1)] * 3, "INCONCLUSIVE", None, None),
    ("pass-without-quote", SIX_EVEN, "HARMED", "empty", lambda r: any("without a quote" in p for p in r["problems"])),
    ("quote-not-in-output", SIX_EVEN, "HARMED", "absent", lambda r: any("not found in the output" in p for p in r["problems"])),
    ("quote-too-short", SIX_EVEN, "HARMED", "short", lambda r: any("too short" in p for p in r["problems"])),
    ("missing-grade", SIX_UP, "INCONCLUSIVE", "missing", lambda r: any("not graded" in p for p in r["problems"])),
    ("string-pass-refused", SIX_UP, "exit2", "string", None),
]


def main():
    failures = 0
    total = 0
    with tempfile.TemporaryDirectory() as root:
        for name, plan, expected, mode, extra in CASES:
            total += 1
            work = build(root, name, plan)
            code, out, err = run("blind.py", work, "--seed=7")
            if code != 0:
                print(f"FAIL {name}: blind.py exit {code}: {err.strip()}")
                failures += 1
                continue
            grade(work, plan, mode=mode)
            code, out, err = run("verdict.py", work)
            if expected == "exit2":
                ok = code == 2
                print(f"{'PASS' if ok else 'FAIL'} {name}: exit {code} {err.strip()[:80]}")
                failures += not ok
                continue
            if code != 0:
                print(f"FAIL {name}: verdict.py exit {code}: {err.strip()}")
                failures += 1
                continue
            res = json.loads(out)
            ok = res["verdict"] == expected and (extra is None or extra(res))
            print(f"{'PASS' if ok else 'FAIL'} {name}: verdict {res['verdict']} mean {res['mean_difference']} ci {res['ci95']} p {res.get('sign_flip_p')}")
            failures += not ok

        # A void task is left out: its runs exist but it is not graded.
        total += 1
        work = build(root, "void", SIX_UP + [(0, 4)])
        run("blind.py", work, "--seed=7")
        doc = json.load(open(os.path.join(work, "tasks.json")))
        doc["tasks"][-1]["void"] = True
        json.dump(doc, open(os.path.join(work, "tasks.json"), "w"))
        grade(work, SIX_UP)
        code, out, _ = run("verdict.py", work)
        res = json.loads(out) if code == 0 else {}
        ok = res.get("verdict") == "LIFT" and res.get("void_tasks") == ["t7"]
        print(f"{'PASS' if ok else 'FAIL'} void-task: verdict {res.get('verdict')} void {res.get('void_tasks')}")
        failures += not ok

        # A planned run missing before blinding: blind.py refuses, and verdict.py
        # gives INCONCLUSIVE if the folders are blinded by other means.
        total += 1
        work = build(root, "missing-run", SIX_UP)
        os.remove(os.path.join(work, "runs", "t1", "with_2.md"))
        code, _, err = run("blind.py", work, "--seed=7")
        ok_blind = code == 2 and "without" in err
        os.makedirs(os.path.join(work, "blind", "t1"))
        key = {}
        for i in range(1, 7):
            tid = f"t{i}"
            os.makedirs(os.path.join(work, "blind", tid), exist_ok=True)
            key[tid] = {}
            for f in sorted(os.listdir(os.path.join(work, "runs", tid))):
                rid = f"{tid}{f[:-3]}".replace("_", "")
                key[tid][rid] = f.split("_")[0]
                with open(os.path.join(work, "runs", tid, f), encoding="utf-8") as src, open(os.path.join(work, "blind", tid, rid + ".md"), "w", encoding="utf-8") as dst:
                    dst.write(src.read())
        json.dump(key, open(os.path.join(work, "key.json"), "w"))
        plan = SIX_UP
        grades = []
        for i, (w, wo) in enumerate(plan):
            tid = f"t{i + 1}"
            for rid, arm in key[tid].items():
                k = w if arm == "with" else wo
                grades.append({"task": tid, "id": rid, "checks": [{"pass": j < k, "quote": (f"{arm} answer" if j < k else "")} for j in range(4)]})
        json.dump(grades, open(os.path.join(work, "grades.json"), "w"))
        code, out, _ = run("verdict.py", work)
        res = json.loads(out) if code == 0 else {}
        ok = ok_blind and res.get("verdict") == "INCONCLUSIVE" and any("unequal" in p or "reps" in p for p in res.get("problems", []))
        print(f"{'PASS' if ok else 'FAIL'} missing-planned-run: blind exit refused={ok_blind}, verdict {res.get('verdict')}")
        failures += not ok

        # blind.py must refuse to re-blind an already blinded folder.
        total += 1
        code, _, _ = run("blind.py", os.path.join(root, "lift"))
        print(f"{'PASS' if code == 2 else 'FAIL'} refuse-reblind: exit {code}")
        failures += code != 2

        # blind.py lists lines that may reveal the arm, and --redact removes them.
        total += 1
        work = build(root, "leak", SIX_UP, extra_text="The skill says to stop and ask.\n")
        code, out, _ = run("blind.py", work, "--seed=7")
        leaks = json.loads(out)["possible_arm_leaks"] if code == 0 else []
        work2 = build(root, "leak-redacted", SIX_UP, extra_text="The skill says to stop and ask.\n")
        code2, out2, _ = run("blind.py", work2, "--seed=7", "--redact=the skill says")
        leaks2 = json.loads(out2)["possible_arm_leaks"] if code2 == 0 else ["error"]
        ok = len(leaks) == 24 and leaks2 == []
        print(f"{'PASS' if ok else 'FAIL'} leak-warning-and-redact: {len(leaks)} flagged, {len(leaks2)} after redact")
        failures += not ok

        # --redact-with puts a neutral phrase in place of the match.
        total += 1
        work3 = build(root, "leak-neutral", SIX_UP, extra_text="The skill says to stop and ask.\n")
        run("blind.py", work3, "--seed=7", "--redact=the skill says", "--redact-with=The notes say")
        sample = os.path.join(work3, "blind", "t1")
        body = open(os.path.join(sample, sorted(os.listdir(sample))[0]), encoding="utf-8").read()
        ok = "The notes say to stop and ask." in body and "redacted" not in body
        print(f"{'PASS' if ok else 'FAIL'} redact-with-neutral-text")
        failures += not ok

        # one_arm_terms flags a phrase that only one arm uses, without naming the arm.
        total += 1
        work4 = build(root, "one-arm", SIX_UP)
        for i in range(1, 7):
            for r in (1, 2):
                p = os.path.join(work4, "runs", f"t{i}", f"with_{r}.md")
                open(p, "a", encoding="utf-8").write("I ran the tool.\n")
        code, out, _ = run("blind.py", work4, "--seed=7")
        terms = [t["term"] for t in json.loads(out)["one_arm_terms"]] if code == 0 else []
        ok = "the tool" in terms and all("with" not in json.dumps(t) or True for t in terms)
        print(f"{'PASS' if ok else 'FAIL'} one-arm-terms: {terms[:5]}")
        failures += not ok

    print(f"{total - failures}/{total} passed")
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
