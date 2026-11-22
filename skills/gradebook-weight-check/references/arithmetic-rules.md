# Arithmetic rules and flag codes

## Contents

1. Order of operations
2. Why the two category methods differ
3. Drop-lowest rules
4. Missing-score effects
5. Rounding
6. Flag and problem codes
7. Hand check for one student

## 1. Order of operations

The script follows this order for every student. Use it for a hand recomputation.

1. Classify each score cell: number, missing, excused, or text (text becomes missing and is flagged).
2. Apply the missing choice: `zero` turns missing into 0 out of the item maximum; `exclude` and `flag` remove it; excused is always removed.
3. Drop the lowest scored items in each category (section 3).
4. Compute the category percentage (section 2).
5. Multiply each category percentage by its weight, add, and divide by the weights of the categories that have scores. With all categories present that divisor is 100.
6. Round once, at the end, unless the scheme says `per_category`: true (then each category percentage is rounded first).
7. Look up the letter from the rounded final.

## 2. Why the two category methods differ

`points` divides total earned by total possible, so a 20-point quiz counts twice a 10-point quiz. `mean_of_percents` gives every item the same say. Example: 18 of 20 and 5 of 10. Points: 23 of 30 = 76.67. Mean of percents: (90 + 50) / 2 = 70.00. If the teacher's recorded grades match one method and not the other, that is the quickest explanation for a systematic gap.

## 3. Drop-lowest rules

- The lowest items are chosen by percentage of their own maximum, not by raw points. Ties drop the earlier column.
- The drop happens after the missing choice. Under `zero` a blank is a 0 and is normally the item dropped; under `exclude` the blank is not there, so a real low score is dropped instead. The same student can land on a different category average for that reason alone.
- At least one item always stays. If fewer scored items than drops exist, fewer are dropped and `drop_lowest_reduced` is flagged. A scheme that drops as many items as the category has is invalid (`drop_leaves_zero`).

## 4. Missing-score effects

| Situation | exclude / flag | zero |
|---|---|---|
| One blank among four equal items, no drop | average of three | average of four with a 0 |
| One blank, drop 1 | blank ignored, a real low score dropped | blank dropped; the others count in full |
| Whole category blank | category removed, remaining weights scaled to 100 | category counts as 0 |
| Excused (EX) | removed | removed |

A student whose whole final-exam category is blank is the usual large swing: with a 30 percent final, `exclude` re-scales the rest and can look 25 points higher than `zero`. The script lists both under `policy_effect`.

## 5. Rounding

- `half_up`: 89.95 becomes 90.0 at one decimal. `half_even`: ties go to the even last digit (89.95 becomes 90.0, 89.85 becomes 89.8).
- Rounding the final once keeps the arithmetic exact; rounding each category first can move a final by up to the rounding unit times the weight share. `rounding_order_changes_letter` is raised when the other order would give a different letter.
- `rounding_changes_letter`: the unrounded final is under a cut-off and the rounded one reaches it (or the reverse). It is the case where a teacher who rounds up "just 89.9" and one who does not disagree.
- Boundary list: within 0.5 of the nearest cut-off above 0, by the unrounded final. 0.5 is a review margin, not a rule.

## 6. Flag and problem codes

Scheme problems (any one makes `scheme_ok` false and no grades are produced): `weights_not_100`, `empty_category`, `drop_leaves_zero`, `bad_weight`, `bad_max`, `bad_method`, `bad_drop_lowest`, `bad_rounding`, `bad_letters`, `item_in_two_categories`, `item_column_missing`, `unsupported_key`, `no_categories`, `category_not_object`, `scheme_not_object`, `bad_expected_column`.

Student flags: `missing_score`, `non_numeric_score`, `score_above_max`, `negative_score`, `category_absent`, `drop_lowest_reduced`, `rounding_changes_letter`, `rounding_order_changes_letter`, `letter_depends_on_missing_policy`, `expected_not_numeric`.

Top-level: `duplicate_ids` (first row graded, later rows listed with their CSV line numbers, line 2 being the first student row), `blank_id_rows`, `unmapped_columns` (header names only).

## 7. Hand check for one student

Homework 30 percent, drop 1, items 10, 9, 8, 7 out of 10 each; quizzes 20 percent, 18 of 20 and 9 of 10 as mean of percents; midterm 85 at 20 percent; final 90 at 30 percent.

Homework: drop 7, 27 of 30 = 90. Quizzes: (90 + 90) / 2 = 90. Final grade: 0.30 x 90 + 0.20 x 90 + 0.20 x 85 + 0.30 x 90 = 27 + 18 + 17 + 27 = 89.0, a B under a 90 cut-off, and one point from the line, so not a boundary case.
