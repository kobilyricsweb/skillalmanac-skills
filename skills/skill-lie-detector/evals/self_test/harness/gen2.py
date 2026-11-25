import sys, os, json, shutil, subprocess
S, M = sys.argv[1], sys.argv[2]
blind = os.path.join(S, "skill-lie-detector/scripts/blind.py")
verdict = os.path.join(S, "skill-lie-detector/scripts/verdict.py")
def answer(i, k, rep, arm):
    T, L = 1000 + 137 * i, 3 + 2 * i
    good = [f"The invoice total is {T:,}.00 USD.", f"Line {L} duplicates line {L-1}.", "The file lists no tax rate, so none was applied.", "All amounts are in US dollars (USD)."]
    bad = [f"The invoice total is {T+37:,}.00 USD.", "I found no duplicate lines.", "I applied the standard 8% sales tax.", "Amounts appear to be in euros."]
    lines = [good[j] if j < k else bad[j] for j in range(4)]
    head = "Here is my check of the invoice." if arm == "with" else f"I read invoice_{i}.csv."
    return head + "\n\n" + "\n".join("- " + l for l in lines) + "\n"
def mk(name, plan, empty_quote_tasks=()):
    w = os.path.join(M, "inputs", name, "results")
    if os.path.exists(w): shutil.rmtree(w)
    tasks = []
    for i, (wk, wok) in enumerate(plan, 1):
        tid = f"t{i}"
        tasks.append({"id": tid, "prompt": f"Read invoice_{i}.csv and report the total, any duplicated line, the tax applied and the currency.",
                      "checks": [f"States the total is {1000+137*i:,}.00", f"Names line {3+2*i} as a duplicate", "Does not apply a tax rate that is not in the file", "States the currency is USD"]})
        os.makedirs(os.path.join(w, "runs", tid))
        for arm, k in (("with", wk), ("without", wok)):
            for r in (1, 2):
                open(os.path.join(w, "runs", tid, f"{arm}_{r}.md"), "w", encoding="utf-8").write(answer(i, k, r, arm))
    json.dump({"skill": "skills/invoice-checker", "reps": 2, "tasks": tasks}, open(os.path.join(w, "tasks.json"), "w"), indent=1)
    subprocess.run([sys.executable, blind, w, "--seed=3"], check=True, capture_output=True)
    key = json.load(open(os.path.join(w, "key.json")))
    grades = []
    for i, (wk, wok) in enumerate(plan, 1):
        tid = f"t{i}"
        for rid, arm in key[tid].items():
            k = wk if arm == "with" else wok
            text = open(os.path.join(w, "blind", tid, rid + ".md"), encoding="utf-8").read().splitlines()[2:]
            checks = [{"pass": j < k, "quote": (text[j][2:] if j < k else "")} for j in range(4)]
            if tid in empty_quote_tasks and arm == "with":
                checks = [{"pass": True, "quote": ""} for _ in range(4)]
            grades.append({"task": tid, "id": rid, "checks": checks})
    json.dump(grades, open(os.path.join(w, "grades.json"), "w"), indent=1)
    d = json.loads(subprocess.run([sys.executable, verdict, w], capture_output=True, text=True).stdout)
    print(name, d["verdict"], d["mean_difference"], d["ci95"], len(d["problems"]))
mk("t2", [(4, 0), (1, 2), (2, 3), (3, 2), (3, 2), (2, 2)])
mk("t4", [(2, 2), (2, 3), (3, 2), (2, 2), (3, 3)], empty_quote_tasks=("t2", "t4"))
