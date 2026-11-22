# Listing page content: llm-eval-test-sets

**One line:** Builds and validates an eval dataset for any LLM feature, with a checker for duplicates, missing graders, imbalance and leakage.

## What it does

The skill gives an agent a seven-step procedure for writing a test set of 30 to 100 cases across typical, edge, adversarial and unanswerable inputs, with a decision table that assigns each case a grader (exact, contains, regex, numeric within tolerance, set, abstain, judge). A script then checks the JSONL file: parse errors, duplicate ids, missing or incomplete graders, identical and near-identical prompts, tag and label balance, share of hallucination probes, prompt-length spread, and leakage between train and test splits. A reference gives the width of the 95 percent interval at each set size and the sign-test table for comparing two runs. The agent ends with a fixed report that says what was not checked.

## Capabilities

- `scripts/validate_evalset.py`: strict JSON report with `ok`, counts of FAIL, WARN and INFO, statistics and findings by case id; exit 0, 1 or 2
- Case format and grader decision table
- Interval-width and sign-test tables for deciding how many cases are enough and whether run B really beat run A
- Hallucination and over-refusal definitions for unanswerable probes

## When to use

You are about to change a prompt, model or agent and need a test set; you have an eval JSONL and do not trust it; scores look too good and you suspect test prompts leaked into training or few-shot examples; you want to measure how often the system makes things up.

## When not to use

- Testing whether an agent skill triggers on the right requests: use `skill-authoring-and-evals`, which covers skill trigger queries and with/without-skill task evals. This skill is about the behaviour of an application built on a model.
- Writing the prompt itself: use `prompt-writing`.
- Running the model or computing pass rates from predictions: do that in your own harness; this skill does not call a model.
- Unit tests for code.

## Requirements

Python 3.9 or newer, standard library only. No network. Nothing is written to disk.

## Install

```
.agents/skills/llm-eval-test-sets/    (Codex, Gemini, Cursor, Copilot)
.claude/skills/llm-eval-test-sets/    (Claude Code)
```

## Examples

Both outputs below are from a saved fixture run (`python scripts/validate_evalset.py ...`).

1. `python scripts/validate_evalset.py evals/fixtures/good_cases.jsonl`: 30 cases (12 typical, 8 edge, 6 adversarial, 4 unanswerable; 7 numeric, 5 regex, 5 contains, 4 exact, 4 abstain, 3 set, 2 judge), prompt length 19 to 123 characters, median 59. Result: `ok` true, 0 FAIL, 0 WARN, 1 INFO (leakage check skipped because there is one split). Exit 0.
2. `python scripts/validate_evalset.py evals/fixtures/bad_cases.jsonl`: 15 cases, `ok` false, 9 FAIL, 7 WARN. FAIL: line 16 not JSON, case b3 has no grader, b4 grader `fuzzy`, b5 no expected, b6 invalid regex, b7 no tolerance, b8 no rubric, id b1 used twice, prompts b9 and b10 identical with answers 7 and 6. WARN: b12 and b13 near-identical, b11 contains its own answer ("Nile"), b14 has a 2-character prompt, b15 abstain without markers, one tag only, 7 percent unanswerable, 15 cases.
3. `python scripts/validate_evalset.py evals/fixtures/test_leaky.jsonl --against evals/fixtures/train_pool.jsonl`: exit 1; FAIL for an identical prompt in both splits (te1 and tr1) and a near-identical pair (te2 and tr2); WARN because the test answer "Jupiter" is stated inside a training prompt (te3 and tr3).

## Limits

- The script checks structure and statistics; it cannot tell whether an expected answer is true or a probe is really unanswerable.
- Near-duplicate and leakage checks compare wording only.
- A judge grader is only as reliable as its rubric.
- Thresholds are working values, not measured optima.
- Interval and sign-test tables assume independent cases.
- It does not run models or score predictions.

## Evidence

See `VERIFICATION.md`. In short: static lint 0 FAIL and 0 WARN; 5 script fixture cases pass. Not tested: any with/without efficacy comparison, trigger behaviour in any tool, native discovery, cross-tool runs, human review.

## Demo script (60 to 90 seconds)

To be recorded from a real run once one exists. Planned beats:

1. Paste a hand-written set of 15 cases; run the validator: 9 FAIL shown with case ids.
2. The agent fixes ids, graders and the conflicting duplicate, and asks the user which of two answers is right.
3. It adds unanswerable probes until the share passes 10 percent and re-runs: `ok` true.
4. The report names the decision the set supports and what was not checked.

## FAQ seeds

- Does it call a model or need network? No; it only reads your JSONL.
- How many cases do I need? At least 30, ideally 100 for a go or no-go decision; the reference table shows the interval width at each size.
- How is it different from `skill-authoring-and-evals`? That skill tests whether an agent skill activates and helps; this one builds datasets for the behaviour of an LLM application.
- Will it write expected answers for me? Only from sources you can show; it tells the agent never to take them from the model under test.
- Does it score my model's outputs? No. Run your harness; the reference explains how to compare two runs with a sign test.
- Can it check a classification set for class balance? Yes, via the `label` field, or via `expected` values for exact-match cases.
- How do I uninstall it? Delete the folder from `.agents/skills/` or `.claude/skills/`.

## Changelog

- 0.1.0 (2026-11-21): first version; static lint and script fixtures run on this version; no other evidence.

## License and authorship

Apache-2.0, copyright 2026 Global Media Holdings (skillalmanac.com). Drafted by an AI model (claude-sonnet-5-5). No human editor has reviewed it yet.
