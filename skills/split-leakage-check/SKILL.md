---
name: split-leakage-check
description: Checks train, validation and test files (CSV or JSONL) for contamination between splits, with a script that finds exact and near-duplicate rows, shared group or entity ids, test rows dated before train, columns that give away the label, and class-share drift, then prints strict JSON with a verdict and a re-split plan. Use when the user asks whether the test set is contaminated, why the validation score is too good, whether train and test overlap, or for a data leakage or split hygiene check before training or an eval. Do not use for deduplicating a single table, evaluating LLM prompts, checking model quality, or modifying the data.
license: Apache-2.0
compatibility: The script needs Python 3.9 or newer, standard library only. No network access is used. Without Python, follow the manual procedure in the last section of references/leakage-types.md.
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  author_model: claude-sonnet-5-5
  version: "0.1.0"
  network: none
---

# Split leakage check

Find out whether the evaluation split can still be trusted. The job is a report and a plan. The data files are never changed by this skill.

## What to collect first

Ask only for what is missing:

| Need | Why | If unknown |
|---|---|---|
| Split files in time order (train, validation, test) | pairs are compared across files only | stop; nothing to check |
| Columns that identify a record (`--text-cols`) | exact and near-duplicate keys | default: every column not named below |
| Id column (`--id-col`) | row ids in the report | line numbers are used |
| Group key (`--group-col`): user, patient, device, session, document source | same entity in two splits | group check is skipped and the report says so |
| Date column (`--date-col`) | time order | time check skipped |
| Label column (`--label-col`) | class balance and target leakage | both skipped |

Splits must be listed oldest first. If the user does not know the intended order, ask before running; a wrong order creates false time violations.

## Workflow

```
- [ ] 1 Confirm split order, key columns, group, date and label columns
- [ ] 2 Run the script
- [ ] 3 Read verdict.reasons, then each section
- [ ] 4 Classify every finding with the table below
- [ ] 5 Write the plan and the report
```

1. Confirm the inputs above. Check that the files are different splits, not the same file twice.
2. Run (all options except `--split` are optional):

```bash
python scripts/check_leakage.py --split train=train.csv --split valid=valid.csv --split test=test.csv \
  --id-col id --text-cols title,body --group-col user_id --date-col created_at --label-col label
```

   Add `--threshold 0.9` for stricter near-duplicate matching (default 0.8) and `--out report.json` to save the JSON. The script refuses `--out` pointing at any input, even with `--force`. Do not edit the script to make a check pass.
3. The verdict has `status` pass, warn or fail, plus `reasons` and `proposed_actions`. Exit code: 0 pass, 1 warn or fail, 2 usage error (message on stderr; fix the arguments, usually a misspelled column).
4. Decide per finding with this table. Details and examples are in [references/leakage-types.md](references/leakage-types.md); read the section for a type only when that type appears.

| Finding | Severity | Action |
|---|---|---|
| Exact overlap (same normalised key in two splits) | fail | Remove from the evaluation side. If `label_conflict` is true, the label is noisy: send the rows to the data owner |
| Near duplicate, similarity from threshold up to 0.9 | warn | Read the pairs. Template text and shared boilerplate are often legitimate; paraphrases are not |
| Near duplicate, similarity 0.9 and above | treat as exact | Same action as exact overlap |
| Group in two splits | fail | Group-aware re-split: every group in exactly one split |
| Later split has rows older than an earlier split's newest row | fail | Time-ordered re-split; add a gap if labels arrive late |
| Column predicts label (kind `perfect`, `near_perfect`, `threshold_separable`) | fail | Ask whether the value exists at prediction time. If not, drop the column from the features |
| Class share differs by 10 points or more (only for splits with at least 100 labelled rows) | warn | Stratified re-split |
| Class with zero rows in a split | warn | Re-split, or merge rare classes |

5. Write the plan as steps for the user to run. Never rewrite or delete rows yourself. After the user re-splits, run the script again on the new files and report the second verdict.

## Report format

```
Verdict: <pass|warn|fail> (threshold <t>, splits in order: <names>)
Findings: <one line per reason with counts and 2 example row ids>
Plan: <ordered re-split or cleaning steps; who runs them>
Not checked: <skipped sections and why; paraphrase or translated copies; leakage through features built from the whole dataset>
```

## Output fields (strict JSON on stdout)

`splits[]` (name, path, rows, empty_key_rows, duplicate_rows_within_split, unparseable_dates), `text_columns`, `threshold`, `exact_overlaps` (count, examples with hash, rows, labels), `near_duplicates` (count, skipped_common_shingles, pairs with split, row ids, similarity), `group_overlaps` (null when no group column), `time_violations` (null when no date column; ranges per split and violations), `class_balance` (null without label; per_split shares, drift, missing_classes, rare_classes), `target_leakage` (null without label; suspects), `verdict`.

Lists are capped at 50 entries; the counts are complete.

## Method and thresholds

- Keys: Unicode NFKC, lower case, punctuation turned into spaces, whitespace collapsed. Two rows are an exact overlap when the keys are equal.
- Near duplicates: Jaccard similarity of 3-word shingles, across splits only, never within one. A shingle found in more than 500 rows of a split is treated as boilerplate and skipped (counted in `skipped_common_shingles`).
- Class drift is claimed only when both splits have at least 100 labelled rows. Below that the shares are reported without a claim. No p-values are produced.
- Target leakage needs at least 30 pooled labelled rows. A column is flagged when its value gives the label at least 99 percent of the time (columns with more distinct values than half the rows are treated as id-like and skipped here), or, for two-class labels, when one numeric cut-off separates the classes perfectly.

## Limits

- Detects copies, not meaning. Paraphrases, translations and images of the same item pass unseen.
- Near-duplicate recall drops when many rows share long boilerplate (see `skipped_common_shingles`).
- A threshold-separable numeric column may be a legitimate strong feature or a row counter; the script cannot tell. A human decides.
- Leakage from preprocessing fitted on the whole dataset (scaling, imputing, target encoding, feature selection before the split) is not visible in split files.
- Dates must be ISO-style text or epoch numbers; other formats are counted under `unparseable_dates` and ignored.
- Both CSV and JSONL must be UTF-8. Whole files are loaded into memory.
