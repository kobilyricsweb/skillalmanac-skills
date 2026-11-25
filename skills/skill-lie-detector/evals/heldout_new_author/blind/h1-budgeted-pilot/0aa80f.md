# Pilot plan: support-reply skill on six saved scenarios

Nothing has been run. This plan uses 12 executor calls and about 14 grader calls, and it has no spare executor calls.

## What the pilot can and cannot show

With six scenarios and one sample per cell, the pilot can catch gross failures and regressions. It cannot estimate an error rate or detect small differences. The release rule below is built around that limit: it treats any wrong refund decision or invented promise as blocking, and it does not ask for statistical significance.

## Budget allocation

| Cell | Scenarios | Executor calls |
|---|---|---|
| Skill on (same model, same policy) | S1–S6 | 6 |
| Baseline, skill off | S1–S6 | 6 |
| **Total** | | **12** |

- Run the pairs interleaved (S1-skill, S1-base, S2-skill, …). If the budget or a call fails partway through, you still have matched pairs for the scenarios that finished.
- There are no retries. A failed or truncated call is logged as a failed output, and that cell counts as a gate failure. Retrying would need budget you do not have.

## Grader budget (proposed, since it was not specified)

- **0 grader calls** for refund decisions. The executor's task prompt requires a final line `DECISION: eligible | not eligible | needs human review`, and you compare it to gold with string matching. Use the same wording in both conditions, outside the skill, so the comparison stays fair.
- **0 grader calls** for invented promises. Run a regex screen (`guarantee`, `always`, `within \d+ (hours|days)`, `full refund`, `we will`, `certainly`, `lifetime`, and so on). Then a human reads every reply and checks each hit against the policy text.
- **2 calibration calls.** Grade two hand-written replies first, one good and one with a planted invented promise, to confirm the grader rubric works.
- **12 answer-relevance calls**, one per reply, blinded.
- **Reserve 4** for re-grading disagreements between the grader and the human reviewer.

Total: at most 18 grader calls, if your separate grader budget allows it.

## Pre-run steps (no executor calls)

1. **Freeze the inputs.** Copy the six tickets, the policy snapshot, and the skill file into the run folder. Record SHA-256 hashes and the git commit of the skill.
2. **Set gold labels before running.** A person who did not write the skill labels each scenario's refund decision from the policy snapshot. Scenarios should cover a mix: about two eligible, two ineligible, one edge case (for example, just outside the window with a possible exception), and one that should be escalated. Write the labels into `manifest.json` before any run.
3. **Write the rubric and the prompt.** Relevance is scored 0–2:
   - 2: answers every question the customer asked.
   - 1: partial, or answers a neighboring question.
   - 0: does not address the question, or is wrong.
4. **Static diff of the two prompts.** Confirm that the only difference between skill-on and baseline is the skill text. Do this by reading the files, not by making a test call.

## Execution

5. Run the 12 executor calls in the interleaved order above, with the same model ID (`claude-haiku-5-5`), the same ticket text, and the same temperature settings in both conditions. Keep a visible counter: 12 calls total, stop at 12.

## Scoring

6. Run the regex screen on all 12 replies.
7. Strip the condition labels. Assign each reply a random ID (R01–R12) and shuffle the order.
8. A human reviewer checks, for each reply: refund decision vs. gold, every promise hit, and the answer to "did it answer what was asked?"
9. Run the 12 relevance grades, blinded, after the 2 calibration calls. Compare with the human scores and resolve disagreements.

## What to save, and where

Save these under a durable folder in the repo, for example `pilot/support-reply-skill/run-2026-11-25/`. Do not rely on the scratchpad, since it can be cleared.

- `manifest.json`: scenario IDs, gold labels, policy hash, skill hash and commit, model ID, prompt template hash, and the executor call count.
- `runs.jsonl`: one line per executor call with scenario ID, condition, full raw output, stop reason, and failure flag.
- `grader_log.jsonl`: the grader inputs and raw outputs, including calibration.
- `scores.csv`: one row per reply with decision, gold, match, regex hits, human promise verdict, both relevance scores, and notes.
- `decision.md`: the gate results and the release decision, written before anyone looks at the skill's conclusion.

The scenarios and replies probably contain customer data. Redact personal details before committing anything to git, or keep the folder out of version control.

## Release decision rule

Pre-register these rules in `decision.md` before scoring.

**Gate A: all must pass.**
1. **Refund decisions:** the skill matches gold on all six scenarios, and it is not wrong on any scenario where the baseline was right.
2. **Invented promises:** zero promises in the skill's replies that the policy does not support, as judged by a human.
3. **Answer relevance:** the skill's mean relevance score is at least the baseline's, and no skill reply scores 0.

**Gate B: informational.** Report where the skill is better or worse than baseline, but do not use it to pass or fail the pilot.

**Outcomes:**
- **All Gate A pass:** release to a controlled rollout, for example with a human sending every reply, and monitor. Do not describe this as proven better. The pilot shows no gross failures on six scenarios.
- **Any Gate A fail:** do not release. Record which scenario failed and why. These six scenarios are now a development set, so they cannot be used again as a clean test after the skill is changed. A fix needs a new budget and a fresh holdout set.
- **Any skill cell incomplete:** count it as a Gate A failure for that cell. Do not retry.
