# Builds one blind grading prompt per task, runs a fresh Sonnet session for each, merges JSON into grades.json.
import json, os, re, shutil, subprocess, sys, tempfile, concurrent.futures as cf

CLAUDE = shutil.which("claude")
W = sys.argv[1]
SKILL = sys.argv[2]
MODEL = sys.argv[3] if len(sys.argv) > 3 else "claude-sonnet-5-5"
OUT = sys.argv[4] if len(sys.argv) > 4 else "grades.json"
tasks = json.load(open(os.path.join(W, "tasks.json"), encoding="utf-8"))["tasks"]
grader = open(os.path.join(SKILL, "references", "grader_prompt.md"), encoding="utf-8").read()
env = {k: v for k, v in os.environ.items() if k != "ANTHROPIC_API_KEY"}
NL = "\n"


def grade(t):
    d = os.path.join(W, "blind", t["id"])
    parts = [grader, NL + "Task id: " + t["id"] + NL + "Task given to the answerer:" + NL + t["prompt"] + NL + NL + "Checks, in order:"]
    parts += [str(i + 1) + ". " + c for i, c in enumerate(t["checks"])]
    for f in sorted(os.listdir(d)):
        body = open(os.path.join(d, f), encoding="utf-8", errors="replace").read()
        parts.append(NL + "===== answer file " + f[:-3] + " =====" + NL + body)
    iso = tempfile.mkdtemp(prefix="grade_")
    shutil.copytree(d, os.path.join(iso, "answers"))
    p = subprocess.run([CLAUDE, "-p", "--model", MODEL, "--safe-mode", "--disallowedTools", "*"], input=NL.join(parts),
                       capture_output=True, text=True, encoding="utf-8", env=env, cwd=os.path.join(iso, "answers"))
    m = re.search(r"\[\s*\{.*\}\s*\]", p.stdout, re.S)
    if not m:
        raise SystemExit("no JSON from grader for " + t["id"] + ": " + p.stdout[:300] + " " + p.stderr[:300])
    rows = json.loads(m.group(0))
    for r in rows:
        r["task"] = t["id"]
    return rows


with cf.ThreadPoolExecutor(4) as ex:
    out = [r for rows in ex.map(grade, tasks) for r in rows]
json.dump(out, open(os.path.join(W, OUT), "w", encoding="utf-8"), indent=1)
print("graded", len(out))
