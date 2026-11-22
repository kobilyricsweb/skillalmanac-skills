---
name: llm-eval-test-sets
description: Builds and validates an eval dataset (test set) for any LLM feature, prompt or agent, using a case format with a grader per case, hallucination probes, and a script that checks the JSONL for duplicate and near-duplicate prompts, missing expected outputs or graders, tag and label imbalance, train/test leakage and prompt-length spread. Use when the user asks for an eval set, golden set, benchmark, test cases for a prompt, how many test cases they need, or how to measure hallucination before changing a prompt or model. Do not use for testing whether a skill triggers, unit tests for code, or running the model and scoring outputs.
license: Apache-2.0
compatibility: The script needs Python 3.9 or newer, standard library only. No network access is used and no model is called. Without Python, follow the manual checks in step 5.
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  author_model: claude-sonnet-5-5
  version: "0.1.0"
  network: none
---

# LLM eval test sets

Build a set of cases that can tell the user whether a change to a prompt, model or agent made the feature better or worse, then check the set before anyone trusts a score from it. Running the model and scoring its outputs happens outside this skill, in the user's own harness.

## Case format (JSONL, one object per line)

| Field | Rule |
|---|---|
| `id` | Required, unique. |
| `prompt` | Required. The exact input the system receives. |
| `grader` | Required. One of the scorers in the table below. |
| `expected` | Per grader (table). Absent for `abstain` and `judge`. |
| `tolerance` | Required for `numeric`: absolute, number 0 or more. |
| `markers` | For `abstain`: phrases that count as declining to answer. |
| `rubric` | Required for `judge`: one or two sentences saying what a pass looks like. |
| `tag` | `typical`, `edge`, `adversarial` or `unanswerable`. |
| `label` | Class label, only for classification sets. |
| `split` | Optional: `train`, `dev`, `test`. |

## Choosing the grader

Use the first row that fits. Prefer the cheapest scorer that cannot be fooled; reach for `judge` last because it costs a model call and adds its own error.

| The right answer is | Grader | `expected` |
|---|---|---|
| One fixed word, label, or code | `exact` (compare after trimming and lowercasing) | string or number |
| A fact that may sit inside a longer reply | `contains` (all listed strings must appear) | string or list of strings |
| A shape (date, id, JSON key, status code) | `regex` | pattern string |
| A number, where rounding or units may vary | `numeric` | number, plus `tolerance` |
| A list in any order | `set` (compare as sets, ignore order and case) | non-empty list |
| Nothing: the system should say it cannot know | `abstain` | none; give `markers` |
| Open prose such as a summary, tone, or refusal quality | `judge` | none; give `rubric` |

## Workflow

```
- [ ] 1 Name the decision the set will support
- [ ] 2 Write 30 to 100 cases across four tags
- [ ] 3 Assign a grader to every case
- [ ] 4 Add unanswerable probes
- [ ] 5 Validate; fix; re-validate
- [ ] 6 Freeze the test split
- [ ] 7 Report
```

1. **Decision.** Write one sentence: "We will switch to prompt B if it fixes more cases than it breaks." A set with no decision behind it grows without end and measures nothing.
2. **Write cases.** Take real inputs (logs, tickets, user messages) wherever they exist and scrub personal data; invented cases are the fallback. Target mix: 40 to 50 percent `typical`, 20 to 30 percent `edge` (empty, very long, wrong language, ambiguous, formatting traps), 15 to 20 percent `adversarial` (prompt injection, false premises, pressure to break a rule), 10 to 15 percent `unanswerable`. Use 30 cases as the floor and 100 as the target for a go or no-go decision; see [references/sizing-and-comparison.md](references/sizing-and-comparison.md) for how wide the uncertainty is at each size.
3. **Graders.** Use the table. Write each `expected` yourself or from a source the user can show; never take it from the model under test. Have a second reader check a sample of 10 expected answers.
4. **Unanswerable probes.** At least 10 percent of the set, graded by `abstain` or `judge`. Valid kinds: private context the model cannot see, events past its knowledge limit, false-premise questions, questions about a document that was not supplied. Read the reference section on hallucination metrics before choosing them.
5. **Validate.** Run the script (below). Fix every FAIL. Read every WARN and either fix it or write down why it is fine (templated sets legitimately trigger near-duplicate warnings). Run again until the FAIL count is 0. Without Python, check by hand: ids unique, every case has a grader and what that grader needs, no prompt appears twice, no tag above 70 percent, no test prompt also in training or few-shot examples.
6. **Freeze.** Put test cases in a separate file or mark `split: test`, record the file's SHA-256, and never put test prompts into few-shot examples, prompt text or fine-tuning data. If the set is edited after scores were seen, call it version 2 and do not compare its scores with version 1.
7. **Report** in this fixed shape:

```
Set: <file>, <n> cases, tags <counts>, graders <counts>
Validator: <ok true/false>; FAIL <n>, WARN <n>; warnings kept and why
Hallucination probes: <n> (<share>%), graders used
Decision the set supports: <one sentence, or "not stated">
Needs your decision: <expected answers or graders I supplied, and gaps I left open>
Not checked: <e.g. expected answers not verified against a source or a second reader; no model run; judge rubrics not calibrated>
```

`Not checked` is always the last line of the reply.

## Repairing an existing set

When the user hands over a set to fix, the workflow above is a checklist, not a to-do list to grow the file. Fix only what is wrong: unparseable lines, duplicate ids, missing graders or fields, contradictory duplicates, answers leaked in prompts. Delete or merge a case only when it is a true duplicate. Do not add new cases to reach 30, the tag mix or the 10 percent probe share; report those gaps under "Needs your decision" and offer to write them. Where a repair needs an expected answer, tolerance, marker or rubric the file does not contain, write the smallest plausible value, mark it in the report as supplied by you, and say it needs a source or the owner's confirmation. Keep a list of removed ids.

## Script

`scripts/validate_evalset.py` is run, not edited, and never changed to make a check pass.

```bash
python scripts/validate_evalset.py cases.jsonl
python scripts/validate_evalset.py test.jsonl --against train.jsonl
```

It reads the files, writes nothing and prints one strict JSON document: `ok` (true when there is no FAIL), `counts` (FAIL, WARN, INFO), `stats` (cases, by_tag, by_grader, by_label, unanswerable, splits, prompt_chars and prompt_words with min, median, p90, max) and `findings` (each with `severity`, `check`, `message`, and `case_ids` capped at 20 with a `more` count). Exit 0 when `ok`, 1 on any FAIL, 2 on a missing file or bad arguments.

| Severity | Checks |
|---|---|
| FAIL | unparseable line; missing or duplicate id; missing prompt; missing, unknown or incomplete grader (no expected, bad regex, no tolerance, no rubric); identical prompts with different expected answers; identical or near-identical prompts across splits |
| WARN | identical or near-duplicate prompts (2-shingle overlap 0.80 or more, or character similarity 0.92 or more); under 30 cases; one tag above 70 percent or no tags; one label above 80 percent; unanswerable share under 10 percent; abstain case without markers; expected answer inside its own prompt or another split's prompt; prompt under 5 or over 8000 characters; p90 length over 5 times the median; all prompts within 1.3 times of each other |
| INFO | leakage check skipped because only one split exists |

Splits come from the `split` field or from `--against` (the extra file is `train`, the main file is `test`).

## Limits

- The script checks the structure and statistics of the set. It cannot tell whether an expected answer is true, whether a case is realistic, or whether a probe is truly unanswerable; a human reads those.
- Near-duplicate and leakage checks compare wording only. Two prompts that ask the same thing in different words pass.
- A `judge` grader is only as reliable as its rubric; calibrate it on 20 cases with a human before trusting it.
- Thresholds are working values. They are listed in the script with the reason for each.
- Comparison and interval tables assume independent cases; many questions about one document are not independent.
- This skill does not run models, compute pass rates from predictions, or test whether a skill activates (use a skill-authoring skill for that).
