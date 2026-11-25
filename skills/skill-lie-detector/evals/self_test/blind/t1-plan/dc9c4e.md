I read the 's SKILL.md, its format and grader references, both scripts, the skill under test, and the example run the skill's author published. I ran nothing. The plan below is built on those files.

## What to know before you start

- **The example run is not your answer.** The author's run on 4 tasks gave NO_LIFT, with a mean of -18.8 points, an interval of -56.2 to 0.0, and a sign-flip p of 0.5. The interval touches zero, so it is borderline. It is a starting point, not evidence about your work.
- **The one loss came from a rule in the skill.** On a wrapped input (a top-level object holding a `results` array), the with-arm stopped and asked which array to convert, because SKILL.md says "do not unwrap an object on your own." The without-arm converted it and scored 3 of 4. Whether that rule is a defect depends on how often your real inputs are wrapped. Test it on your data.
- **Four tasks cannot confirm a result.**  needs at least 6 graded tasks for LIFT or HARMED. Plan for 8 tasks, with 2 runs per arm.
- **The grader sees only the reply.** The skill's normal behavior is to write a file. For each task, ask the run to save the CSV to a file and also paste the full CSV in its reply. Grade the reply, and check that the file matches it.

## Step 0: what you need from the team (before next week)

- 8 to 10 real JSON inputs from recent requests, anonymized, each under 2 MB. The pool of example inputs in the skill's example folder is only a backup.
- The skill version to test: the exact `json-records-to-csv` folder you install, with its git hash recorded.
- An executor model that matches what your agent runs in production, and a grader model that is different from the executor if you can manage it.

## Step 1: the task set (8 tasks, one per kind of input)

| Task kind | What it checks | Why it's here |
|---|---|---|
| Flat, clean records | Basic conversion | Control. Both arms should tie. |
| Nested objects | Dot-named columns | Plain model may already do this |
| Tag arrays | Joined cell, separator | Default mode |
| Array of objects, one row per item | Row mode, `items.name` style columns | Plain model often gets this wrong |
| Two parallel arrays in one record | Position pairing, blanks | Hard case |
| Ragged keys | Union of columns, empty cells | Common in real data |
| Wrapped object (`results` array) | Whether it converts or stops | Tests the rule behind the example loss |
| Mixed array with non-object items | Still delivers, reports skipped indices | Tests the reporting promise |
| Id with leading zeros, output file already exists | Keeps `00731`; does not overwrite | Safety and fidelity |

Put at least three of these where you expect the plain model to slip.

## Step 2: checks (write them all before any run)

- Use 4 checks per task. Make them decidable from the reply text: row counts, exact values, column names, quoted cells, a stated skipped index, a sentence saying the file was not overwritten.
- Avoid checks that every competent answer passes ("valid CSV") and checks that copy the skill's wording.
- For each task, also keep a golden CSV made without the skill, for example from a short Python reference you write yourself. Use it as a script cross-check on the grader (my addition, outside the 's method). Each task's inputs and golden files stay in a folder the runs cannot read.
- If a check turns out broken after runs, set `"void": true`. Do not rewrite it.

## Step 3: run both arms

- Same model, same task text, same input files, same tools (Bash and Python in both arms). The only difference is the skill.
- **With:** a fresh session in a folder containing `./json-records-to-csv`. Prompt: `Read ./json-records-to-csv/SKILL.md and the files it points to, then follow it for this task.` followed by the task text.
- **Without:** a fresh session in a folder without the skill. Task text only, with no mention of skills.
- Each run gets a fresh folder with its own copy of the inputs. The output path must not exist, except in the "file already exists" task, where it must.
- 8 tasks × 2 arms × 2 reps = 32 runs. Save each final reply as `/runs/<task>/with_<n>.md` or `without_<n>.md`.
- Keep the full transcripts in a separate folder that is not blinded. For each with-run, record whether the script actually ran. If the with-arm never ran the script in more than a few runs, you are measuring a trigger problem, not the skill's content. Report that separately.

## Step 4: blind and grade

- `python   --redact="json_to_csv|SKILL\.md"`
- Read every `possible_arm_leaks` line before grading. Do not open `key.json` until grading is done.
- Copy each task's blinded folder somewhere outside `/`. Start one fresh grader per task with ``, the task, its checks and its blinded files only.
- Spot-check at least two grades per task against the quotes, with extra attention to checks where the two arms differ.

## Step 5: score and decide

Run `python  ` and take its numbers as they are. Decide before you see them:

| Verdict | Action |
|---|---|
| LIFT | Keep. Note which task kinds drove it. |
| LIFT_UNCONFIRMED | Add 4 to 8 tasks and re-run. Do not decide on 4. |
| NO_LIFT | Dead weight on this task mix, provided the with-arm ran the script and the set includes your hard cases. Remove it, or keep it out of the task kinds where it did not help. |
| HARMED | Fix the rule that caused the harm, then test again on a fresh set of tasks you did not use to fix it. |
| INCONCLUSIVE | Fix the missing grades or the void tasks and re-run. |

My suggested rule, which is judgment rather than something the scripts enforce: keep only if the mean is at least +10 points with 12 or more tasks. Also note the length numbers (with-arm replies were longer in the example run). The method does not score length, but it changes how much context the skill adds to each reply.

If every task ties because the plain model gets them all right, the honest reading is that the skill adds nothing for work at that level of difficulty. Make the set harder before you conclude the skill is useless.

## Schedule

- **Monday:** inputs, task set, checks, golden files.
- **Tuesday:** one pilot task in both arms, only to confirm the harness works. Do not tune checks from pilot outputs.
- **Wednesday:** all 32 runs.
- **Thursday:** blind, grade, verdict.
- **Friday:** decide, and write down the decision and the verdict.json.

## What this will not tell you

- Whether the skill triggers on its own. That needs the trigger tests in the skill-authoring-and-evals skill.
- Whether results hold for other agents or for skills that write only files. The  reads replies only.
- Whether two different graders would agree. Grader agreement is untested, so it is worth a second grader on two tasks if the verdict is close.
