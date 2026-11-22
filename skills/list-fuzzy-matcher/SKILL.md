---
name: list-fuzzy-matcher
description: Matches each item in a left CSV list to its closest item in a right CSV list and flags weak, tied, and unmatched pairs. Use when two lists of names, labels, or titles do not match exactly because of case, spacing, punctuation, or typos, and you need a reviewable match file with scores. Do not use for exact-key joins, database merges, live lookups on websites, or deciding record merges without human review.
license: Apache-2.0
compatibility: Python 3.9+ stdlib only, no network (type A).
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  author_model: claude-haiku-5-5
  version: "0.1.0"
  network: none
---

# List Fuzzy Matcher

Matches each item of a left CSV list to its closest item in a right CSV list, scores the pair, and writes a new CSV that marks every pair a person should check. The script reports statuses and scores only. The agent turns them into decisions, and the report states every decision.

## Workflow

1. Check the intake. Both files must be CSV, UTF-8 with an optional byte-order mark, have a header row, be 2 MB or smaller, and have 1000 data rows or fewer each. Pick the item column per file by header name or 0-based index; the default is column 0. Required output: an intake note with, for each side, the role (left or right), the file's column used, and its data row count.
2. Pick an output path that does not exist yet. Required output: the output path, shown as `<output-file>` in the report.
3. Run the script with the command in the Script contract section. Required output: the exit code and the one-line JSON summary, copied verbatim.
4. Read the summary and classify every row with the threshold table. Required output: the status counts and the Flagged rows table (every row with status weak, tie, or unmatched).
5. Decide every flagged row using the decision rules in the table. Use only the text and scores in the output file; never invent a match. Required output: the Decisions table.
6. Write the report in the Output contract format. Required output: the four headings in order, with the Summary table filled in.

## Normalization and scoring

Each item is casefolded, every character that is not a letter or digit becomes a space, and runs of spaces collapse to one. The score is the difflib SequenceMatcher ratio of the normalized left item against each distinct normalized right item. Word order is not normalized, so "Corp Acme" scores lower against "Acme Corp" than an exact spelling would. Duplicate right items with the same normalized text count once, so a repeated name never creates a false tie. Blank items are skipped and counted in skipped_blank.

## Threshold and decision table

Scores are rounded to 4 decimal places before any comparison. The thresholds 0.85 and 0.60 are working values, not a published standard. Check in this order: unmatched, then tie, then weak, then ok.

| Status | Rule on best_score (rounded) | Meaning | Decision rule |
|---|---|---|---|
| ok | best_score is 0.8500 or higher, and no tie | Strong match | accept. Spot-check 10 percent of ok rows, at least 5 rows or all of them if fewer, and report the count as ok_spot_checked. |
| weak | best_score is 0.6000 or higher and below 0.8500 | Plausible but uncertain | accept only when the two visible texts differ just by case, spacing, punctuation, or one or two character edits. Otherwise no_match. |
| tie | two distinct right items share the best score | Ambiguous | needs_source_check. Never choose by file order. |
| unmatched | best_score below 0.6000 | No candidate | no_match. Do not use runner_up_match. |

Decision codes: accept, no_match, needs_source_check. Each flagged row gets exactly one code.

## Output contract

Output CSV, written by the script. Header: `left_item,status,best_match,best_score,runner_up_match,runner_up_score`. One row per non-blank left item, in input order. Scores have 4 decimal places. The runner-up columns are empty when the right list has only one distinct item.

Report, in this order:

- `## Summary`: a two-column table with keys status (complete or partial), left_items, right_items, skipped_blank_left, skipped_blank_right, ok, weak, tie, unmatched, ok_spot_checked, exit, and output (the placeholder `<output-file>`).
- `## Flagged rows`: a table with columns left_item, status, best_match, best_score, runner_up_match, runner_up_score. List every weak, tie, and unmatched row.
- `## Decisions`: a table with columns left_item, decision, chosen_match, basis. chosen_match is filled only for accept. basis is a short phrase naming the visible text difference, such as "case only" or "two candidates tie at 0.8333". Cover every flagged row.
- `## Open questions`: a numbered list, or the single word None.

## Script contract (type A)

Run from the skill folder:

`python -I scripts/fuzzy_match.py --left <left-file> --right <right-file> --output <output-file> [--left-column <name-or-index>] [--right-column <name-or-index>] [--flag-below <value>] [--no-match-below <value>]`

| Argument | Default | Meaning |
|---|---|---|
| --left, --right | none | CSV file with a header row. |
| --output | none | New file path. The script exits 2 if the path exists. |
| --left-column, --right-column | 0 | Header name or 0-based index of the item column. |
| --flag-below | 0.85 | Working value. Scores below this are weak. |
| --no-match-below | 0.60 | Working value. Scores below this are unmatched. Must satisfy 0 < no-match-below < flag-below <= 1. |

Exit codes:

| Exit | Meaning |
|---|---|
| 0 | Every left item is ok. |
| 1 | At least one item is weak, tie, or unmatched. The output file is written. |
| 2 | Usage or input error. Stderr holds one JSON line with keys ok (false) and error. No output file is written. |

Stdout on exit 0 or 1: one JSON line with keys exit, left_items, right_items, skipped_blank (left, right), and status_counts (ok, weak, tie, unmatched).

## Refuse or stop when

- Either file is larger than 2 MB or has more than 1000 data rows. Stop and ask the user to split or narrow the list.
- Either file is not UTF-8, has no header row, or names a column that is not in the header. Report the exit 2 error text and stop.
- The output path already exists. Stop and ask for a new name. Never delete, rename, or overwrite.
- The output path is one of the input files. Stop.
- The inputs are free text such as paragraphs rather than names or labels. Stop; similarity scores on prose are not meaningful at these thresholds.
- The user asks to look items up online, call a service, or query a database. Refuse that clause only. Keep the match file, set status to partial, and list the refused item under Open questions.
- The user asks to merge or overwrite source records from scores alone. Refuse that clause only, keep the match file, set status to partial, and list it under Open questions.

## Shipped files

- [scripts/fuzzy_match.py](scripts/fuzzy_match.py): the matcher.
- [fixtures/left.csv](fixtures/left.csv) and [fixtures/right.csv](fixtures/right.csv): eight-item smoke inputs with typos, one tie, and two unmatched items.
- [LICENSE.txt](LICENSE.txt): Apache License 2.0.
