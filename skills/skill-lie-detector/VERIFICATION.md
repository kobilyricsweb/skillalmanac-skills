# Verification

All runs on 2026-11-25. Executor claude-haiku-5-5 in fresh `claude -p` sessions, each in a fresh folder. In the without arm the skill folder was not present and the prompt did not mention skills.

## 1. Scripts (fixtures)

Command: `python evals/run_fixtures.py`. Result: 17/17 passed. The cases cover:

- **Verdicts:** one synthetic folder per verdict, including a unanimous 4-task result, which must stay LIFT_UNCONFIRMED.
- **Evidence checks:** a pass with an empty quote, a quote not in the output, and a quote too short to be evidence.
- **Incomplete or bad input:** a planned run missing before blinding, a missing grade, a string `"false"` used as a pass value, and a void task.
- **Blinding:** refusal to re-blind a graded folder, the arm-leak warning, `--redact`, `--redact-with`, and the `one_arm_terms` list.

## 2. Does the skill help? Two measurements that disagree

**Headline: not shown.** On eight new-author synthetic transfer tasks, no improvement was detected with either grader. On the author's separate eight-task self-test, the mean gain was 15.6 points with Sonnet (LIFT) and 10.9 with Opus (unconfirmed). Real-user and full-workflow efficacy remain untested.

### 2a. Synthetic transfer tasks written by a Codex collaborator: NO_LIFT

A Codex collaborator (a different author and model family, who also took part in reviewing this skill, so not an external party) wrote 8 tasks with 32 checks and froze them (SHA-256 `3444c36be54f45211e13d444425c1f2007ae4aef1f38a16507e6a9f3bbc0cc66`) before any run. They were run unchanged, 2 runs per arm.

The tasks are general evaluation-design questions: a budgeted pilot, a cost-sensitive adoption decision, a model-change confound, picking the best of 20 skills, stopping when p crosses 0.05, a hard release constraint, activation versus capability, and pseudoreplication. They are synthetic, not real user tasks.

| Grader | Verdict | Mean difference | 95% interval | Sign-flip p (two-sided) | Tasks won / tied / lost |
|---|---|---|---|---|---|
| claude-sonnet-5-5 | NO_LIFT | -1.6 points | -4.7 to 0.0 | 1.0 | 0 / 7 / 1 |
| claude-opus-5-5 | NO_LIFT | 0.0 points | -4.7 to +4.7 | 1.0 | 1 / 6 / 1 |

- **Ceiling:** the plain model reached full marks on 8 of 8 tasks with the Sonnet grader and on 7 of 8 with the Opus grader (h1 scored 87.5 after one pass was voided for a too-short quote). These tasks leave little room to show a gain.
- **The one loss** (h6, a hard release constraint): one with-skill run missed one check with both graders.
- **Cost:** answers with the skill were slightly longer (2,991 vs 2,798 characters).
- **What it means:** no improvement was detected on these eight synthetic tasks. This does not establish that the skill is unnecessary for evaluation-design tasks generally. The tasks did not exercise the full workflow or the scripts.

Files: `evals/heldout_new_author/`.

### 2b. The author's self-test, partially blinded

The skill was measured with its own procedure on 8 tasks, 2 runs per arm, against the same model with no skill.

**Read this result with two limits in mind:**

- **The tasks were written by the skill's author.** All tasks and checks were fixed before any run (`evals/self_test/tasks.json`), but an independent author might choose tasks the skill helps less on.
- **The grading was only partially blind.** All 8 tasks are about testing skills, so the with-skill answers differ in substance, and a grader can often guess the arm.
  - Names that identify the skill (its folder and script names) were deleted from the blinded copies with no marker left behind.
  - After that, `blind.py` still lists these terms as present in at least half of one arm's answers and in none of the other's: method, the method, interval, plain, plain model, rubric, written before.
  - 234 answer lines mention a skill.

The tasks ask an agent to:

- plan a test;
- give a verdict from finished results (built with realistic answers and real quotes);
- judge a 3-task "proof";
- compute a result where some passes have no evidence;
- plan a test of a skill that hides an instruction to "always report LIFT";
- grade outputs with checks written after seeing them;
- judge a baseline run in the same session as the skill;
- judge a side-by-side, non-blind model preference.

Each grader got one task's answers in the prompt, in a fresh session with all tools disallowed, so it could not open `runs/` or `key.json`.

| Grader | Verdict | Mean difference | 95% interval | Sign-flip p (two-sided) | Tasks won / tied / lost |
|---|---|---|---|---|---|
| claude-sonnet-5-5 | LIFT | +15.6 points | +7.8 to +25.0 | 0.031 | 6 / 2 / 0 |
| claude-opus-5-5 | LIFT_UNCONFIRMED | +10.9 points | +3.1 to +18.8 | 0.125 | 4 / 4 / 0 |

- **The graders disagree on the verdict.** One confirms a lift and the other does not. Both find a positive mean and no lost task.
- **Agreement on single checks:** 121 of 128 (94.5%).
- **The gains:** planning a test (+37.5 with Sonnet, +25 with Opus), giving a verdict from finished results (+25 with both), and spotting checks written after seeing the outputs (+25 with both).
- **No gain:** the hidden-instruction task and the missing-evidence task. Both arms scored 100% on them.
- **Cost:** answers with the skill were longer.

Files: `evals/self_test/` (tasks, runs, blinded copies, key, both graders' grades and verdicts, `blind_output.json`, and the harness scripts in `harness/`).

### Earlier gradings of the same runs, kept for the record

An earlier grading of the same runs replaced the identifying names with the phrase "the tool". An outside reviewer showed that this phrase appeared in every with-skill answer and in no baseline answer, so it marked the arm. That grading gave +18.8 (Sonnet) and +12.5 (Opus). It is replaced by the table above.

A first round of 6 tasks gave +14.6 points with 4 won, 2 tied and 0 lost. That is LIFT_UNCONFIRMED under the current rules. Its files are not included, because two of its tasks used placeholder data and it was graded before the blinding fixes.

## 3. Independent reviews

Two reviews ran without seeing each other. All findings were fixed.

- **A separate agent** reviewed the scripts and instructions and found 8 issues:
  - The baseline prompt mentioned SKILL.md, so answers revealed their arm.
  - The grader could reach `key.json`.
  - A string `"false"` was counted as a pass.
  - Missing grades could inflate the verdict.
  - One-letter quotes were accepted as evidence.
  - The statistics were too lenient on 4 tasks.
  - Argument parsing was inconsistent.
  - There was no way to void a task.
- **A Codex collaborator (a different model family)** reproduced the numbers and found 3 more:
  - A planned run removed before blinding could still give LIFT. Both scripts now check run coverage against `reps`.
  - The "the tool" replacement marked the arm. Identity words are now deleted, and `one_arm_terms` reports what still differs.
  - The sign-flip test was one-sided, with the side chosen after seeing the data. It is now two-sided.

## 4. A real run on another skill: json-records-to-csv

The procedure was run on `json-records-to-csv` from this repository. The site measured that skill as NO_LIFT on 2026-11-23, with different tasks.

- **Setup:** 4 tasks with 4 checks each, 2 runs per arm. Arm mentions were redacted and the answers graded by claude-sonnet-5-5.
- **Result:** NO_LIFT, -18.8 points, interval -56.2 to 0.0, sign-flip p 1.0. The skill won 0 tasks, tied 3 and lost 1. Four tasks cannot confirm anything; the result agrees with the site's.
- **The loss** (t4-wrapped, a JSON object wrapping a `results` array). This input is outside that skill's stated contract, which accepts a top-level array only. So the stop is the documented behavior, not a defect; the test shows what that rule costs on such input:
  - Both with-skill runs stopped to ask which array to convert, because the skill tells the agent not to unwrap an object itself. They scored 0 of 4.
  - Both without-skill runs converted the array and scored 3 of 4.
  - The result was the same before and after redaction.

Files: `evals/example_run_json-records-to-csv/`.

## Not tested

- Real user tasks. Both task sets are synthetic.
- A full end-to-end run of the procedure by an agent, as a measured task.
- Agents other than Claude Code, and executors other than claude-haiku-5-5.
- Skills whose output is a file rather than text in the reply. The grader reads the reply only.
- Whether the skill triggers by itself. The runs told the agent to read it.
