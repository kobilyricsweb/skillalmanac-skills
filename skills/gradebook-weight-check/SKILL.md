---
name: gradebook-weight-check
description: Recomputes weighted final grades from a CSV gradebook and the grading scheme the teacher states, checking that category weights add to 100, applying drop-lowest, showing how excluding versus zeroing missing work changes each final, flagging rounding boundaries, and comparing with the recorded finals. Use when a teacher, tutor or course administrator asks to check grades, verify the weighting, find why a final differs from the gradebook, or what score a student needs on the final exam. Do not use to decide grades or policy, write quizzes or rubrics, or give student feedback.
license: Apache-2.0
compatibility: The script needs Python 3.9 or newer, standard library only. No network access is used. Without Python, follow the manual method in step 4.
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  author_model: claude-sonnet-5-5
  version: "0.1.0"
  network: none
---

# Gradebook weight check

Recompute final grades from scores and a stated scheme, and show every place where the arithmetic depends on a choice. The school's grading policy belongs to the teacher. You check consistency; you never decide what a grade should be, and you never pick a missing-work policy for them.

## Privacy rule

Identify students by id only in replies, logs and saved reports. The script reads the id column, the item columns and the recorded-final column, and nothing else, so a name column never reaches the output. Do not paste names from the CSV into your answer.

## Workflow

```
- [ ] 1 Collect the scheme in the teacher's words
- [ ] 2 Write scheme.json and check it
- [ ] 3 Ask for the missing-score choice
- [ ] 4 Run the script
- [ ] 5 Read the results in the fixed order
- [ ] 6 Report
```

1. **Collect the scheme.** Get from the teacher, exactly as they state it: category names, each weight, which score columns belong to each category with their maximum points, drop-lowest counts, the rounding rule, the letter cut-offs, and the column holding the recorded final if there is one. If a late-work penalty exists, it must already be inside the scores; the script does not apply penalties. Never fill a gap from what is common elsewhere; ask.
2. **Write `scheme.json`.** Format below. Weights are in percent and must add to 100 (tolerance 0.05, which absorbs 33.3 + 33.3 + 33.4). If they do not, stop and show the teacher the total; do not rescale silently.
3. **Ask for the missing-score choice** whenever any score is blank. Offer the three choices and say what each does; do not choose.

   | Choice | Effect | Use when |
   |---|---|---|
   | `exclude` | a blank is left out of its category; a category with nothing scored is dropped and the other weights are re-scaled to 100 | the work was not assigned, or the student was excused |
   | `zero` | a blank counts as 0 and can be removed by drop-lowest | the work was due and not handed in |
   | `flag` (default) | calculates like `exclude`, marks the final `provisional`, lists every gap | the teacher has not decided yet |

   A cell of `EX` or `excused` is always left out, whatever the choice. Blank, `NA`, `N/A`, `-`, `missing` count as missing. Any other text is reported as `non_numeric_score` and treated as missing.
4. **Run the script** (do not edit it to make a check pass):

```bash
python scripts/gradebook_check.py scores.csv scheme.json --missing exclude
python scripts/gradebook_check.py scores.csv scheme.json --missing zero --expected-column Recorded
python scripts/gradebook_check.py scores.csv scheme.json --what-if Final --target 80
```

   Options: `--id-column` (default `student_id`), `--expected-column`, `--tolerance` (default 0.05), `--delimiter`, `--out FILE` (add `--force` to replace an existing file; the script refuses any path that resolves to the scores or scheme file). Exit 0 = computed and consistent, 1 = scheme invalid or a recorded final disagrees, 2 = usage or file problem. Without Python, recompute by hand with the rules in [references/arithmetic-rules.md](references/arithmetic-rules.md) for the few students in question and say the full table was not checked.
5. **Read results in this order:** `scheme_ok` and `scheme_problems` first (if false there are no grades); then `mismatches_with_expected` (an entry with `explained_by_missing_policy` means the recorded grade matches the other choice, so the teacher probably used it); then `boundary_cases`; then each student's `flags`; last `policy_effect` for students whose letter changes with the choice.
6. **Report** in this shape:

```
Scheme: <ok or the problems>; weights total <n>
Policy used: <exclude | zero | flag>; rounding <decimals, mode, per-category or at end>
Recorded vs recomputed: <n compared, n differ>; differences listed by id
Needs a human decision: <ids whose letter depends on the missing-score choice or sits within 0.5 of a cut-off>
Data problems: <duplicate ids, scores above max, negatives, text in score cells, absent categories>
Not checked: <e.g. the policy itself, late penalties, whether the maxima are right>
```

## Scheme file

```json
{
  "categories": {
    "Homework": {"weight": 30, "drop_lowest": 1, "items": {"HW1": 10, "HW2": 10, "HW3": 10}},
    "Final": {"weight": 70, "items": {"Final": 100}}
  },
  "letters": [{"letter": "A", "min": 90}, {"letter": "B", "min": 80}, {"letter": "F", "min": 0}],
  "rounding": {"decimals": 1, "mode": "half_up", "per_category": false},
  "expected_column": "Recorded"
}
```

`items` maps a CSV column to its maximum points. `method` is `points` (default: total earned over total possible) or `mean_of_percents` (average of each item's percentage); the two differ whenever maxima differ. `mode` is `half_up` or `half_even`. Only `categories` is required; unknown keys are reported as `unsupported_key`.

## Output contract

Strict JSON on stdout: `scheme_ok`, `scheme_problems[]` (`code`, `detail`), `policy`, `rounding`, `students_total`, `duplicate_ids[]`, `blank_id_rows[]`, `unmapped_columns[]`, `students[]` (`student_id`, `final`, `final_unrounded`, `letter`, `provisional`, `by_category{}` with `percent`, `counted`, `dropped[]`, `missing[]`, `policy_effect` with the final and letter under `exclude` and `zero`, `flags[]`), `boundary_cases[]`, `mismatches_with_expected[]`, `expected_compared`, `what_if`, `flag_counts{}`. Duplicate ids: only the first row is graded; later rows are listed. Flag codes are in [references/arithmetic-rules.md](references/arithmetic-rules.md), which you read only when a code needs explaining or you are recomputing by hand.

## Limits

- It checks arithmetic and consistency. It does not know whether a scheme is fair, allowed, or what the school requires.
- Scores above the maximum and negative scores are used as entered and flagged; extra credit is not modelled beyond that.
- The what-if answer assumes one blank item, scores in steps of 0.01 capped at the item's maximum, and the chosen missing policy for everything else. It reaches the target on the recorded (rounded) final.
- Letters come from the rounded final. A final within 0.5 of a cut-off is only listed for a human; the script never moves a student across a line.
- Curves, per-item weights inside a category, per-student weight overrides and late penalties are not computed. Rounding each category first is supported only when the scheme asks for it, and the other order is always compared.
- Dates, attendance and written comments are out of scope.
