---
name: flashcard-set-builder
description: Builds a deduplicated flashcard CSV from term and definition lines and flags cards that need editing. Use when a student or teacher has study notes written one card per line as term, double colon, definition, and wants exact and near-duplicate cards removed, long fronts or backs marked, and a front,back CSV ready for a flashcard app. Do not use for writing new study content, generating quiz questions, scheduling reviews, or converting PDFs and slides into notes.
license: Apache-2.0
compatibility: Python 3.9+ stdlib only, no network (type A).
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  author_model: claude-haiku-5-5
  version: "0.1.0"
  network: none
---

# Flashcard Set Builder

This skill runs a script that reads one card per line, drops duplicates, marks cards that
break the length or wording rules, and writes a new CSV. The script never rewrites card text.
Your job is to run it, report what it found, and hand the edits back to the user.

## Workflow

1. **Confirm intake.** Get two paths: the input notes file (`<input-file>`) and a new output
   CSV path (`<output-csv>`) that does not exist yet. Output: both paths, stated back to the user.
2. **Check the input format.** Every non-blank line must contain exactly one `::`, with text
   on both sides and at least one letter or digit on each side. Blank lines are skipped and
   counted. Output: the count of lines you expect to read. If you cannot tell whether a line
   is valid, do not guess; run the script and let it report the first bad line.
3. **Run the script** with the command in the Script contract section. Output: the raw stdout
   lines and the exit code, copied exactly.
4. **Review drops.** Each `DROP` line names the input line it duplicates (`duplicate_of_line`).
   Output: a table of dropped lines, one row per `DROP` line. Do not restore a dropped card
   unless the user asks; if they do, the card is the user's decision to keep, and the output
   CSV must be regenerated under a new name.
5. **Review flags.** Each `FLAG` line gets one action from the flag table below. Output: a
   table of flagged lines with the code and the action. Do not change card text yourself
   unless the user supplies the replacement wording.
6. **Report the result** in the Output contract format, with the exit code and the path of
   the CSV that was written.

## Thresholds and decision table

Values marked "working value" are editorial choices, not a published standard.

| Check | Code | Rule | Value |
|---|---|---|---|
| Exact duplicate | DUP_EXACT | Normalized front and back both equal an earlier kept card. Card is dropped. | none |
| Near duplicate | DUP_NEAR | Jaccard similarity of normalized front token sets is greater than the threshold against an earlier kept card. Card is dropped. | 0.8 (working value) |
| Long front | FRONT_LONG | Front has more than this many whitespace-separated words. Card is kept and flagged. | 12 (working value) |
| Long back | BACK_LONG | Back has more than this many whitespace-separated words. Card is kept and flagged. | 30 (working value) |
| Term in definition | DEF_CONTAINS_TERM | Normalized front appears as a whole-word sequence inside the normalized back. Card is kept and flagged. | none |
| Input size | (error input_too_large) | Input file size limit. | 2097152 bytes (2 MB) |
| Card count | (error too_many_cards) | Maximum cards read from one file. | 5000 (working value) |

Normalization: Unicode NFKC, casefold, then split on runs of non-word characters. Duplicates
are judged in input order: the first card is kept and later matches are dropped.

| Code | Action for the author | Re-run needed |
|---|---|---|
| DUP_EXACT | Keep the earlier line; delete the later one from the notes. | Yes, after the notes change |
| DUP_NEAR | Compare the two cards; keep the clearer one and delete the other. | Yes, after the notes change |
| FRONT_LONG | Shorten the front to 12 words or fewer, or split the card in two. | Yes |
| BACK_LONG | Shorten the back to 30 words or fewer, or move detail to a second card. | Yes |
| DEF_CONTAINS_TERM | Reword the definition so it does not repeat the term. | Yes |

## Script contract (type A)

Command, run from the skill folder:

```
python -I "scripts/flashcards.py" "<input-file>" "<output-csv>"
```

- Arguments: exactly two positional paths, input then output. The script reads
  [scripts/flashcards.py](scripts/flashcards.py) only; the input file is never modified.
- Input: UTF-8 text (a leading byte order mark is accepted), at most 2 MB, at most 5000 cards.
  The shipped sample is [fixtures/sample_notes.txt](fixtures/sample_notes.txt).
- Output CSV: created new with header `front,back`; rows are kept cards in input order.
  Flagged cards stay in the CSV. Dropped cards do not appear.
- Stdout layout: line 1 `lines= blank= cards=`; line 2 `kept= dropped= flags=`; then one
  `DROP line= code= duplicate_of_line=` line per drop, one `FLAG line= code=` line per flag,
  then `written=` and `result=` (`clean` or `findings`). `lines` counts every line read,
  `blank` counts skipped blank lines, `cards` counts non-blank lines. Card text is never printed.
- Exit 0: no drops and no flags. Exit 1: at least one drop or flag; the CSV is still written.
  Exit 2: usage or input error; nothing is written; stderr holds one line of JSON with an
  `error` key.

| Error code | Meaning |
|---|---|
| usage | Wrong number of arguments |
| input_missing | Input path is not a file |
| input_unreadable | Input cannot be read |
| input_too_large | Input is over 2 MB |
| invalid_utf8 | Input is not UTF-8 |
| malformed_line | A non-blank line lacks exactly one `::` or has an empty or wordless side; JSON gives the line number |
| no_cards | No non-blank lines |
| too_many_cards | More than 5000 cards |
| output_equals_input | Output path resolves to the input file |
| output_exists | Output path already exists; nothing is overwritten |
| output_dir_missing | Parent folder of the output path does not exist |
| output_unwritable | Output cannot be created or written |

## Output contract

Your reply to the user uses these headings, in this order:

- `## Summary`: a table with columns `input lines | blank | cards | kept | dropped | flags | exit code`.
- `## Dropped cards`: a table with columns `line | code | duplicate_of_line`. Write "none" if empty.
- `## Flagged cards`: a table with columns `line | code | action`. Write "none" if empty.
- `## Output`: the `written=` path and the `result=` value.

## Refuse or stop when

- Any line fails the format check (exit 2, `malformed_line`). Stop, give the line number and
  the reason, and ask the user to fix that line. Do not guess how to split it.
- The output path already exists (`output_exists`). Never overwrite it. Ask for a new name.
- The output path is the input file (`output_equals_input`). Refuse and ask for a new name.
- The input is over 2 MB or has more than 5000 cards. Stop. Suggest splitting the notes by
  topic and running each part to its own CSV. Do not merge the outputs yourself, because
  duplicates across parts are not caught.
- The input is not UTF-8 (`invalid_utf8`). Ask the user to save the file as UTF-8 and retry.
- The user asks you to write, rewrite or invent card content. That is outside this skill.
  You may describe what a flag asks for, and the user writes the new wording.
