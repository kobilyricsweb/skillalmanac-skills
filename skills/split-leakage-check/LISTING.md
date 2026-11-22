# Listing page content: split-leakage-check

**One line:** Checks train, validation and test files for duplicates, shared groups, time and label leakage; prints JSON.

## What it does

The agent confirms the split order and the key, group, date and label columns, then runs `scripts/check_leakage.py` on the split files. The script normalises key text and finds exact overlaps by hashing, near duplicates by 3-word shingle Jaccard similarity, groups present in more than one split, later-split rows dated before an earlier split's newest row, columns that predict the label, and class-share drift. Output is strict JSON with a verdict and a proposed re-split plan. A decision table maps each finding to an action. Data files are never modified.

## Capabilities

- Exact and near-duplicate rows across splits (user-set threshold, default 0.8)
- Group or entity overlap by an id column
- Time-order violations by a date column
- Target-leakage suspects: perfect, near-perfect and threshold-separable columns
- Class balance per split, with no drift claim below 100 labelled rows
- Optional `--out` report file that refuses to overwrite any input

## When to use

You have train, validation and test files and ask: is my test set contaminated, why is validation too good, do train and test overlap, is there leakage.

## When not to use

Deduplicating one table (a duplicate-record tool does that), profiling columns, building LLM eval sets, splitting a file into train/test, judging model quality, or changing the data. This skill checks between splits only. It does not find paraphrases or preprocessing leakage.

## Requirements

Python 3.9 or newer, standard library only. No network. Without Python the agent follows the manual procedure in `references/leakage-types.md` (near duplicates not covered).

## Install

To be generated at publication: one pinned command per tool. The package installs to `.agents/skills/` and `.claude/skills/`.

## Examples

Real output from `python scripts/check_leakage.py --split train=evals/fixtures/bad_train.csv --split test=evals/fixtures/bad_test.csv --id-col id --text-cols text --group-col user --date-col ts --label-col label` (exit code 1, trimmed):

```
exact_overlaps.count: 1   (train t1 = test s1 after lower-casing and dropping punctuation)
near_duplicates.pairs[0]: train t3 / test s2, similarity 0.8571
group_overlaps: 1 of 6 groups shared (u1)
time_violations: 2 test rows (66.67 percent) dated before the newest train row
verdict.status: fail
```

Second example, `evals/files/t3-patient-visits` with `--group-col patient --date-col visit_date --label-col outcome --text-cols note`: 2 of 5 patients (p1, p2) appear in two splits, no exact or time problems, verdict fail, action "re-split by patient".

No saved agent session exists yet; these are script runs on the saved fixtures.

## Limits

- Finds copies, not paraphrases, translations or images.
- Near-duplicate recall falls with heavy shared boilerplate.
- A threshold-separable numeric column may be a legitimate feature or a counter; a human decides.
- Preprocessing fitted on the whole dataset is not visible in split files.
- ISO or epoch dates only; UTF-8 only; whole files in memory.

## Evidence

See `VERIFICATION.md`: lint 0 FAIL / 0 WARN, 10 of 10 script fixture cases pass (outputs derived by hand). Not tested: efficacy against a baseline, triggering in any tool, cross-tool installs, large files, human review.

## Demo script (60 to 90 seconds)

To be recorded from a real run once one exists. Planned beats:

1. User: "my test accuracy is 99%, check my train and test CSVs for leakage". Agent confirms split order and columns.
2. Run the script: verdict fail with four reasons.
3. Agent shows the two example row pairs and the shared group.
4. Agent gives the plan (group-aware, time-ordered re-split) and the Not checked line.
5. After the user re-splits, a second run shows verdict pass.

## FAQ seeds

- Does it change my files? No. A re-split is a plan for you to run.
- Does it need network access? No.
- How is it different from a duplicate-removal skill? It compares splits with each other and also checks groups, dates and label leakage.
- Does it catch paraphrased copies? No, only text that matches after normalising (exact) or shares most 3-word phrases (near).
- What similarity counts as a near duplicate? 0.8 by default; `--threshold` changes it.
- Can I trust a pass? It means none of the listed checks fired, not that the set is proven clean.
- Which file formats? CSV and JSONL in UTF-8.
- How do I uninstall it? Delete the folder from `.agents/skills/` or `.claude/skills/`.

## Changelog

- 0.1.0 (2026-11-21): first version; lint and script fixtures run on this version; no other evidence.

## License and authorship

Apache-2.0, copyright 2026 Global Media Holdings (skillalmanac.com). Drafted by an AI model (claude-sonnet-5-5). No human editor has reviewed it yet.

## How it differs from nearby skills

`duplicate-record-triage` works inside one table; this checks contamination between splits. `llm-eval-test-sets` builds evaluation prompts; this audits existing tabular or text splits. `dataset-field-profiler` profiles columns; this does not.
