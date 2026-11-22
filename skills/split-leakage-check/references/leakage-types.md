## Contents

1. Exact and near duplicates
2. Group or entity leakage
3. Time leakage
4. Target leakage
5. Class balance
6. Manual procedure when Python is unavailable

## 1. Exact and near duplicates

- Cause: scraped sources with reposts, data augmentation done before splitting, the same item under two ids.
- Check the `labels` field on an exact overlap. If `label_conflict` is true, the same input carries two labels: the task is ambiguous or the labelling is noisy, which caps any achievable score.
- Near duplicates at 0.8 to 0.9 are frequently harmless templates ("Your order 123 has shipped"). If most pairs differ only in a number or a name, say so and recommend masking those tokens before comparing, then re-run.
- Fix: remove from the evaluation split, not from train, unless the evaluation split would fall below a usable size. Re-run after the fix, because removing rows can shift class shares.

## 2. Group or entity leakage

- Cause: several rows per user, patient, device, store, document or conversation, split at random by row. The model learns the entity and scores well on the same entity in test.
- Typical groups: user id, patient id, customer, session, thread, document id for chunks, speaker, camera.
- Fix: group-aware split. Assign whole groups to a split. Sizes then differ from the target ratios; report the achieved row counts. If groups are very unequal in size, one giant group can dominate a split; list it.
- A single shared group that is a generic placeholder (for example `unknown`, `0`, empty) is not an entity. Check the group names in `examples` before acting.

## 3. Time leakage

- Applies when the model will be used on the future: forecasting, fraud, churn, ranking, anything with a date column.
- A violation means some rows of a later split are dated before the newest row of an earlier split, so the model has seen the future relative to those rows.
- Fix: cut by date (train before validation before test). Where the label is only known after a delay (chargebacks, 30-day churn), leave a gap at least as long as the delay between the splits.
- If the data has no real time order (shuffled benchmark), ignore this section and say why.

## 4. Target leakage

- Suspects are columns whose value was created by, or after, the outcome: refund status for a churn label, discharge code for a diagnosis label, resolution time for a ticket priority label, a copy of the label with a different name.
- `perfect` or `near_perfect`: each value of the column almost always has one label. `threshold_separable`: one cut-off on a numeric column splits two classes without error. A numeric counter that grows with row position in a file sorted by label also produces this; check the column name and meaning.
- Test: would this value exist at the moment a prediction is made? If no, remove it. If yes, keep it, but note it is a very strong feature.
- Not flagged: columns with many distinct values (id-like), combinations of columns, and leakage that needs a model to see.

## 5. Class balance

- Drift of 10 points or more in a class share between two splits with at least 100 labelled rows each is reported. For small splits only the shares are given.
- A class with fewer than 5 rows in a split is listed as rare; metrics on it will swing with one row.
- A class missing from a split makes macro metrics undefined for that class.
- Fix: stratified split on the label (and on the group if groups exist: stratified group split).

## 6. Manual procedure when Python is unavailable

1. Take the key columns, lower-case them, remove punctuation, collapse spaces, and sort the lines of each split.
2. Compare sorted lists of the train and test keys for equal lines (a spreadsheet COUNTIF or a database join works). Any match is an exact overlap.
3. List distinct group values per split and intersect them.
4. Compare the earliest date of each later split with the latest date of each earlier split.
5. For each non-label column, count distinct values, then count how many have more than one label. Zero such values is a leakage suspect.
6. Compute class shares per split.
Say in the report that near duplicates were not checked.
