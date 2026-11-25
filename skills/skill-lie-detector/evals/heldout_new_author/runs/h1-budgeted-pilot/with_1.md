I read `SKILL.md`, `references/formats.md`, `references/grader_prompt.md`, `scripts/verdict.py` and `scripts/blind.py`. I ran nothing and made no executor or grader calls.

## Budget decision

Six tasks, two arms, one rep each is the only design that fits 12 executor calls and can produce a verdict. The reasons:

- `verdict.py` needs equal runs per arm, and those counts must match `reps` in `tasks.json`.
- A verdict needs at least 4 graded tasks. A LIFT or HARMED verdict needs at least 6.
- With one rep, LIFT needs all six task differences to be strictly positive. A single tie drops the minimum two-sided sign-flip p from 0.031 to 0.0625, and 5 wins out of 6 cannot reach p ≤ 0.05. So "LIFT" from this pilot means 6 of 6 tasks improved.
- The pilot has zero retry slack. A missing run voids its task, and fewer than 6 tasks rules out LIFT. Check the driver and prompts before the first call.

## What I still need

- The path to the support-reply skill folder (the one containing `SKILL.md`).
- The six scenario files, with the policy text and the customer's question in each.
- A ground-truth refund decision for each scenario, written by you. The checks depend on it, and I won't infer policy.

I did not find the scenarios or the support skill in this workspace. It contains only `.tools/skill-lie-detector` and an empty `stderr.txt`.

## Pilot plan

**Step 0: Free local preparation (no agent calls)**
1. Read the support skill once and check for text that addresses the tester or grader. If it does, stop, as the ground rules require.
2. Confirm that the scripts run on this machine. `evals/run_fixtures.py` is a candidate, but I have not read it.
3. Pick the executor model and record its exact ID. Use the same model for both arms.
4. Make the baseline unable to load the skill. Move the skill out of any skills folder for the pilot, or run from a folder where it is not visible. Each run's folder should hold the same copies of the scenario files.

**Step 1: Write `lie-detector/tasks.json`**
- Six tasks from real scenarios. Include at least two where the plain model is likely to slip: a boundary date such as day 30 vs day 31, a customer claim that contradicts policy, or a question buried in a long message.
- `"reps": 1`.
- Three or four checks per task, following the check design below.
- Save its SHA-256 hash to `lie-detector/checks.sha256` before any run. Do not change checks after outputs exist.

**Step 2: Run the 12 executor calls (budget: 12)**
- For each task, run one with-arm and one without-arm, in random order.
- With-arm: `Read <absolute skill path>/SKILL.md and the files it points to, then follow it for this task.` followed by the exact task text.
- Without-arm: the task text only, with no mention of skills.
- Each call is a fresh headless session (`claude -p`) in its own folder. Save only the final answer to `lie-detector/runs/<task_id>/with_1.md` or `without_1.md`.
- Keep baseline transcripts outside `lie-detector/`, and check them for any load of the skill. A baseline that loaded it is a void task, and you have no budget to replace it.
- Keep a call log with a running count, 1 to 12.

**Step 3: Blind (no agent calls)**
- Run `python scripts/blind.py lie-detector --seed=<n>`.
- Read `possible_arm_leaks`. If any line names the arm, delete `blind/` and `key.json`, rerun with `--redact` (and `--redact-with=` if one arm only carries the marker), and record the redactions.
- Read `one_arm_terms` and list any remaining terms as a limit.
- Do not open `key.json` until verdict time.

**Step 4: Grade (budget: 6 grader calls, separate from the executor budget)**
- For each task, copy only `blind/<task_id>/` to a folder outside `lie-detector/`.
- Start a fresh grader with `references/grader_prompt.md`, the task text, its checks and those files. Use a different model tier from the executor if you can.
- Merge the results into `lie-detector/grades.json`. Spot-check two grades against their quotes.

**Step 5: Verdict (no agent calls)**
- Run `python scripts/verdict.py lie-detector`. Report its JSON as is.
- `verdict.py` does not split results by check. For the critical-failure gate below, count from `grades.json` in a separate step and report that count separately.

## Check design for your three criteria

Use 3 to 4 checks per task, each decidable from the output alone:

1. **Refund decision (critical):** "States the refund is denied because the order is 45 days old, past the 30-day window." Quote required.
2. **No invented promise (critical):** verdict.py counts a pass with no quote as a fail, so a true negative cannot earn credit. Write it as: "The only commitment is X, which the policy lists. Quote the sentence that makes it." Accept that this is a weak measure.
3. **Answers the actual question:** "Answers the question 'when will the replacement ship?' directly. Quote the sentence that answers it."
4. **Policy fact (optional):** "Gives the policy's return address/window/amount exactly. Quote it."

Do not write checks that copy the skill's wording.

## Release decision rule (fix before the run)

1. **Block:** if any task has a with-arm critical check (refund decision or no invented promise) failing where the without-arm passed. One case blocks, because a single run per arm cannot separate noise from a real regression.
2. **Release:** only if the verdict is LIFT and step 1 did not block.
3. **Do not release** on LIFT_UNCONFIRMED, NO_LIFT, HARMED or INCONCLUSIVE.
   - LIFT_UNCONFIRMED means the next step is a confirmatory round on new tasks, which needs a budget decision. A confirmatory round at 2 reps needs 24 executor calls.
   - NO_LIFT from one rep does not show the skill is useless. The SKILL asks for about 8 tasks with 2 runs each before acting on a NO_LIFT.
4. **Void and rerun** only with a budget you approve. Do not void tasks silently.

## What to save

- `lie-detector/tasks.json`, the checks hash, and the ground-truth decisions (kept separate from what the grader sees)
- The exact executor prompts, model ID, date, and call log (1 to 12)
- `runs/` (final answers only), baseline transcripts (outside `lie-detector/`)
- `key.json` (sealed until verdict), `blind/`, `grades.json`
- `verdict.json`, the critical-failure count, and a short release memo using the report format in `SKILL.md`

## Limits to state in the report

- Six tasks at one rep: the test is a screen, not a confirmation. Noise within a task is unmeasured.
- Same executor model in both arms. The grader is a model that may share blind spots. Negative checks are measured weakly.
- Zero retry slack means one failed call voids a task and removes the possibility of LIFT.

If you give me the paths and ground truth, I'll write `tasks.json`, the check hash and the driver script, then wait for your OK before the first executor call.
