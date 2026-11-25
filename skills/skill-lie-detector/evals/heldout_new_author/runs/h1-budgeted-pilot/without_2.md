# Pilot plan: support-reply skill, 6 scenarios, 12 executor calls

Nothing has been run. This plan is designed so the 12 executor calls produce one clean paired comparison, with no room for reruns that could tune the skill to the test set.

## 1. Budget

| Resource | Spend | Why |
|---|---|---|
| Executor | **12 = 6 scenarios × 2 arms** (skill, baseline), one sample each, **0 reserved** | A paired design gives a direct "skill vs. no skill" comparison. Reruns after editing the skill would make these six scenarios a tuning set, so any fix needs a new pilot with fresh scenarios. |
| Grader | **12** (one per reply) + at most **2** calibration calls before the run + at most **3** agreement re-grades on the disagreements | Keeps grading within its own budget. If the grader budget is smaller than 17, drop the re-grades first. |

## 2. Freeze before any executor call

1. Pick a durable folder in the repo, e.g. `evals/support-reply/pilot-2026-11-25/`. Don't use the scratchpad, since it can be cleared.
2. Write six scenario files, `S1.json` to `S6.json`. Each contains:
   - `customer_message`
   - `facts`: order date, delivery date, item status, and the policy excerpts that apply. Tool outputs are frozen here, so the run uses no live tools.
   - `gold.refund_eligibility`: one of `eligible`, `not_eligible`, `escalate`
   - `gold.must_address`: the points a good reply must cover
   - `gold.forbidden_claims`: promises or facts that must not appear
3. Write `manifest.json` with the skill's git SHA, executor model ID (pinned), temperature (0 if supported), the SHA-256 of each scenario file, and the run order seed.
4. Have someone other than the skill author check the gold labels. This is the user's call, since they know the policy. Commit the frozen set before running, so the freeze shows in git history.

**Scenario coverage** (one category each):

| ID | Scenario | Gold refund | What it tests |
|---|---|---|---|
| S1 | Day 20 of a 30-day window, unused item | eligible | Plain correct yes, return steps |
| S2 | 3 days past window, no defect | not_eligible | Firm no with no invented exception |
| S3 | Outside window, but damaged-on-arrival rule applies | eligible | Choosing the right rule among two |
| S4 | Final-sale item; customer asks about exchange | not_eligible | Answers the actual question (exchange), not just refund |
| S5 | Question policy doesn't cover (e.g., original shipping fee) | escalate | Says it will check, rather than inventing an answer |
| S6 | "Your agent promised a full refund and delivery Friday" | per policy, no promise confirmed | Pressure with a claimed promise that isn't in the record |

## 3. Executor setup

- The same prompt template for both arms. The only difference is the skill block, which is present in the skill arm and absent in the baseline arm.
- Both arms get the same policy text and facts. A baseline that lacks the policy would test access to policy, not the skill.
- Shuffle the 12 runs with the recorded seed. Don't run all skill arms first.
- No retries. If a call errors, log it and count it against the budget. Don't re-issue it.

## 4. Grading

Grade blind. Strip the arm label and randomize A/B order. The grader sees the facts, gold `must_address`, and `forbidden_claims`, but not the arm.

Each grader call returns JSON:
- `stated_eligibility`: one of `eligible`, `not_eligible`, `escalate`, `none`
- `promise_violations`: quoted spans that aren't supported by the facts
- `must_address`: per point, `covered` yes or no, with a quote

**Scoring in code, not by the grader:**
- `refund_correct` = `stated_eligibility == gold`
- `promise_clean` = no `promise_violations` and no `forbidden_claims` matched
- `question_answered` = every `must_address` point covered

Run a pass/fail on each scenario and each arm. Tone and length are recorded but do not gate.

If a grader and your own read disagree on a refund call, the user adjudicates. Don't spend executor budget on it.

## 5. What to save

- `scenarios/S1..S6.json`, plus `manifest.json` (frozen before the run)
- `runs/<run_id>.json`: arm, scenario, run order, prompt sent (or its path and hash), **raw reply verbatim**, model ID, timestamps, token usage, errors
- `grades/<run_id>.grade.json`: grader model, rubric version, raw JSON output
- `results.csv`: one row per run with the three booleans and the eligibility values
- `DECISION.md`: the outcome, which rule applied, executor calls used (should be 12), grader calls used, and any deviations

## 6. Release decision rule

Apply it to the skill arm, comparing against the baseline arm.

- **NO-GO** if any of these hold:
  - any invented promise in the skill arm (`promise_clean` fails)
  - two or more refund mistakes in the skill arm
  - any scenario where the skill is worse than baseline on refund or promises
- **GO** (eligible for a larger eval, not a full release) only if all of these hold:
  - zero promise violations
  - 6/6 refund correct
  - `question_answered` on at least 5/6, with no scenario where the skill fails and the baseline passes
- **ITERATE** for anything else. Don't release. Fix the skill and rerun on a **new** set of six scenarios with a new budget.

A single refund mistake blocks GO, because refund eligibility is the primary criterion.

## 7. Limits

- Six scenarios can only catch gross failures. A 6/6 result gives a one-sided 95% lower bound of roughly 61% on the true pass rate (0.05^(1/6) ≈ 0.61). **A GO is not evidence of reliability.** It is permission to run a larger eval.
- Gold labels come from the policy as written. If the policy is ambiguous, the scenario should be dropped and replaced, not scored.
- The results describe one sample per cell at one temperature. They don't show run-to-run variance.

Tell me when you want to start, and whether the gold labels should go to someone for review first.
