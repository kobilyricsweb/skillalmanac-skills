# Test plan: does json-records-to-csv improve our agent's JSON-to-CSV work?

I read the lie-detector method (`.tools/skill-lie-detector/SKILL.md`, `references/formats.md`, `references/grader_prompt.md`, `scripts/verdict.py`) and the skill under test (`json-records-to-csv/SKILL.md`). I have not run anything. I did not open the example run folder, `VERIFICATION.md`, `blind.py`, or `run_fixtures.py`. Read `blind.py` before step 4, and treat the example folder as unvetted if you use it for comparison.

## What the test can and cannot show

- It runs each task with the skill and without it, in fresh contexts, and grades the outputs blind against pre-written pass/fail checks.
- It measures what the skill does **when the agent is told to read it**. It does not test whether the agent loads the skill on its own. That needs a separate trigger test (step 7).
- The skill is mostly a procedure around a script. The with-arm may run `json_to_csv.py`, which is deterministic. So the test really asks whether the skill makes the agent's *output* better, not whether the script is correct.

## Setup (before any run)

1. **Model:** use the model your team's agent runs in production, the same for both arms.
2. **Workspaces:**
   - With-arm: a folder containing `json-records-to-csv/`. Confirm `python -I scripts/json_to_csv.py` works there, since a missing Python makes the skill look worse for the wrong reason.
   - Baseline: a folder with no copy of the skill. Also check that no globally installed copy loads, and void any baseline run whose transcript shows the skill being read.
3. **Output paths:** `json_to_csv.py` refuses an existing output file (`output_exists`). Each run must write to a fresh file name, and both arms must get the same output name in the task text.
4. **Answer format:** the grader only sees the reply text, not the CSV file. Put this in every task text: "Put the complete CSV in a fenced code block in your final reply." Keep inputs small enough to paste (about 5 to 30 records), except the size-limit task.

## Tasks (8, with 2 runs per arm = 32 runs)

Take real conversions from your team's history if you have them. `json-records-to-csv/fixtures/sample_records.json` is a starting point. If you have none, write these 8, which target the decision table and the refusal rules:

| Task | What it stresses |
|---|---|
| t1 flat orders | Control; expect ties |
| t2 nested address | Dot-named columns, `{}` for an empty object |
| t3 leading zeros and decimals | `"007"` and ZIP codes stay text; `9.50` handling (see note) |
| t4 ragged keys | Column union in first-seen order, blanks for missing keys |
| t5 array join with `"; "` inside items | Separator collision; the skill says to use `--separator " / "` |
| t6 row mode with two arrays | Pairs by position, not a cartesian product |
| t7 null, missing and booleans | `null` and missing both empty; `true`/`false` as text |
| t8 top-level object | Should ask which array to convert, not unwrap it and convert |

**Note on t3:** the skill's rule (`9.50` becomes `9.5`) is its convention, not necessarily what your team wants. Write the check from your data requirements. If you copy the skill's rule, you are measuring imitation.

**Why the task count matters:** a task both arms pass fully contributes zero. Among 8 tasks, LIFT needs at least 5 non-tied tasks, all in the same direction, for the sign-flip test to reach p ≤ 0.05. So choose tasks where the plain model plausibly slips on at least 2 or 3 of them. Easy tasks mostly add ties.

## Checks

Write 3 to 5 per task before the first run. Commit `tasks.json` to git first, so the timestamp is on record.

- Make checks decidable from the reply alone, and check values, not wording. Examples:
  - t2: "The header contains `address.city` and `address.zip`"
  - t5: "The tags cell for row 2 is `red / blue`, not `red; blue`"
  - t8: "Does not output a CSV, and asks which array to convert"
- Where possible, add a second, scripted check outside the lie-detector: parse the CSV block in each reply with Python's `csv` module and compare it to a hand-built expected file. This removes the grader model's blind spots on exact values. It is my suggestion, not part of the skill's method.

## Run and grade

1. **Run** each arm twice per task in fresh sessions (`reps: 2`). Save only the final reply to `lie-detector/runs/<task>/with_<n>.md` and `without_<n>.md`. Keep transcripts elsewhere so you can audit the baseline.
2. **Blind:** `python scripts/blind.py lie-detector`. Read `possible_arm_leaks`. Expect leaks: the with-arm will probably mention `json_to_csv`, `skipped_records`, `status: findings`, or the skill's name. Rerun with `--redact` for those phrases. Do not open `key.json` yet.
3. **Grade:** one fresh grader per task folder, using `references/grader_prompt.md`. Save the merged answers to `grades.json`.
4. **Spot-check:** verify at least 2 grades per task by hand, and every with-arm pass on a numeric check. `verdict.py` only checks that quotes exist in the text, not that they are correct.
5. **Compute:** `python scripts/verdict.py lie-detector`. Read `problems` and `reason`. Do not compute the numbers yourself.

## Trigger test (separate, needed for real-world value)

A skill that never loads is dead weight, even if it lifts results when loaded. Use 6 prompts that do not name the skill, such as "turn this export into a spreadsheet-ready CSV". Run them in the with-skill workspace as your agent normally runs. Record whether it reads `SKILL.md`. Include 2 that should not trigger (a CSV-to-JSON request, an `.xlsx` request). The lie-detector references `skill-authoring-and-evals` for this, but that skill is not in this folder, so you will need it or a simpler equivalent.

## Decision rule

Set these before the run.

| Result | Action |
|---|---|
| **LIFT** and the trigger test passes on at least 5 of 6 | Keep. Also check that the mean difference is at least about 10 points. A small but significant lift may not justify the context cost. |
| **LIFT_UNCONFIRMED** | Add 4 tasks and rerun before deciding. |
| **NO_LIFT** on 8 or more tasks | Remove it, or keep it only if the trigger test shows it is needed. Say "no measurable lift on these tasks," not "useless," because 8 tasks cannot rule out a small effect. |
| **HARMED** | Remove it, or restrict it to the tasks where it hurt. |
| **INCONCLUSIVE** | Fix the test (missing grades, too few tasks, leaked arms) and rerun. Do not interpret it. |

Report the verdict, the difference with its interval, the wins, ties and losses, the output length in each arm, the trigger rate, and any voided tasks or redactions.
