---
name: punctuation-capitalization-fixer
description: Fixes spacing, punctuation and sentence capitalization in a plain text file and lists every change with its line number. Use when pasted prose has double spaces, a space before a comma or period, a missing space after a comma, a lowercase sentence start, a standalone lowercase i or repeated punctuation, and a corrected copy plus a change list is wanted. Do not use for rewriting wording, grammar, spelling or style, or for Word, PDF or spreadsheet files.
license: Apache-2.0
compatibility: Python 3.9+ stdlib only, no network (type A).
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  author_model: claude-haiku-5-5
  version: "0.1.0"
  network: none
---

# Punctuation and Capitalization Fixer

This skill runs `scripts/punct_fix.py` on a UTF-8 text file. The script writes a new corrected file and reports every change. It never edits the input and never overwrites an existing file. Your job is to run it, check the change list, and report it in the output contract below.

## Workflow

1. **Intake.** Confirm three facts: the input is plain UTF-8 text of at most 2 MB; the output path is a new file name in a folder that exists; the user wants a corrected copy, not rewritten wording. Output: one line, `input: <input-file>, output: <output-file>`. If any fact fails, go to the refuse list and stop.
2. **Run the script** with the exact command line in the script contract. Output: the exit code and the JSON line from stdout (or the JSON error from stderr).
3. **Branch on the exit code** using the table below. Output: the branch taken and the status line.
4. **Review the change list.** For each change, check its rule against the rule table. Put any change that may be wrong in Open questions, with its line number and the reason. Do not edit the output file by hand. Output: the Open questions list, or `None`.
5. **Report** in the output contract. Output: the report only, no extra prose.

Exit code branches:

| Exit code | Meaning | Action |
|---|---|---|
| 0 | No changes. The output file is still written as a copy. | Report `unchanged`, change count 0. |
| 1 | Changes made. The output file is written. | Go to step 4. |
| 2 | Usage or input error. No output file is written. | Report the `error` text from stderr. Stop. |

## Rule table

Each change carries one rule code. Thresholds marked working value are implementation choices, not a published standard.

| Rule code | Changes | Leaves alone |
|---|---|---|
| `space_before_punct` | Deletes spaces before `,` `.` `;` `:` `!` `?` when the character before the spaces is not a digit. | `10 : 30`, `2026 .` (digit before the space). |
| `double_space` | Collapses 2 or more spaces between two non-space characters into 1 space. | Leading indentation and tabs. |
| `repeated_punct` | Collapses `!!`, `??`, `,,`, `;;`, `::` to one character; `..` to `.`; 4 or more dots to `...`. | A single `...`; mixed runs such as `?!`. |
| `missing_space_after` | Inserts a space after `,` `;` `:` when a letter follows and a letter precedes. | Digits on either side (`1,000`, `10:30`). |
| `missing_space_after_terminal` | Inserts a space after `!` or `?` between letters. Inserts a space after `.` only when a lowercase letter precedes it and a capital followed by a lowercase letter follows. | `file.PDF`, `U.S.A`, `node.JS`. |
| `capitalize_sentence` | Capitalizes a whole lowercase word at the start of a line or after `.` `!` `?` and spaces. At line start the word must be followed by a space and a letter, by punctuation, or by the end of the line. | `iPhone` (not all lowercase); the 22 abbreviations in the script set (for example `e.g.`, `etc.`, `vs.`) when a period follows them (working value). |
| `standalone_i` | Changes a standalone lowercase `i` to `I`, including `i'm`. | `i.e.` (letter after the period); `i` inside words, after a letter, or next to `-`, `/`, `@`. |

Protected spans are never changed by any rule: single-line code spans in backticks, web addresses that start with a scheme or `www.`, and email addresses. Context printed with each change is 12 characters on each side (working value).

## Known misses and false positives

Check these in step 4 before reporting a change as correct.

- A lowercase fragment at the start of a line, such as a list item typed without a bullet (`apples, pears`), is capitalized like a sentence. Put it in Open questions.
- A lowercase word after a period in a mixed-case token, such as `file.Txt`, is split into `file. Txt`. Put it in Open questions.
- A sentence that starts with a non-ASCII lowercase letter (for example an accented letter) is not capitalized. Report it as a miss.
- Spaces before punctuation after a digit are kept on purpose, so `2026 .` and `10 : 30` remain as typed. Report them as misses if the user expected a fix.
- Only the 22 abbreviations in the script set stop capitalization. An abbreviation outside that set, such as `Ave.` or `Gen.`, followed by a lowercase word, is treated as a sentence end, so that word is capitalized in error. Put it in Open questions.

## Output contract

The report has four headings, in this order.

- `## Summary`: a table with columns `Field` and `Value`. Rows: `Status` (`changed` or `unchanged`), `Change count`, `Output file`.
- `## Changes`: a table with columns `Line`, `Rule`, `Before`, `After`. One row per entry in the JSON `changes` list, in the same order. Use `None` in the table body if there are no changes.
- `## Open questions`: a bullet list of changes to check, each as `line N, rule: reason`. Write `None` if nothing needs checking.
- `## Output`: the output file path as given by the user.

## Script contract

Command line, run from the skill folder:

`python -I scripts/punct_fix.py <input-file> <output-file>`

- Arguments: exactly two positional paths. There are no flags.
- Input: an existing regular file, UTF-8, at most 2 MB (2,097,152 bytes). Read only.
- Output file: created with exclusive-create mode. An existing path, or the input path itself, is refused.
- Stdout on exit 0 or 1: one JSON line with keys `status` (`changed` or `unchanged`), `change_count` (equal to the length of `changes`), `output` (the path as given), and `changes`. Each entry in `changes` has keys `line` (1-based), `rule` (one of the seven rule codes above), `before`, and `after`.
- Stderr on exit 2: one JSON line `{"error": "<message>"}`. Messages: usage; input file not found; cannot read input file; input exceeds 2 MB limit; input is not valid UTF-8; input contains reserved private-use characters U+E000 or U+E001; output path must differ from input path; output file already exists; output folder does not exist; cannot write output file.
- Exit codes: 0 no changes (output file written), 1 changes made (output file written), 2 usage or input error (no output file written).

## Smoke check

Before running on user text, run the command on [fixtures/slips.txt](fixtures/slips.txt) with a scratch output name. Expected result: `status` is `changed`, `change_count` is 8, with 2 changes on line 1, 3 on line 2, and 1 each on lines 3, 4 and 5. The web address on line 3 is unchanged, and line 6 has no changes. Any other result means the install is damaged; stop and report it.

## Refuse / stop when

- The input is not plain text: a Word, PDF, spreadsheet or image file, bytes that are not UTF-8, or a file over 2 MB. Ask the user to paste the text into a `.txt` file.
- The request is to rewrite wording, fix grammar or spelling, change style, translate or summarize. This skill changes only spacing, punctuation and capitalization.
- The user asks to overwrite an existing file or edit the input in place. Ask for a new output name.
- The text is source code, log output, or data where capitalization carries meaning. Stop and say the tool is for prose.
- Intake (step 1) cannot confirm the facts. Stop with the missing fact named.

## Shipped files

- [scripts/punct_fix.py](scripts/punct_fix.py): the fixer described in the script contract.
- [fixtures/slips.txt](fixtures/slips.txt): six-line smoke input with eight planted slips and one web address that must stay unchanged.
- [LICENSE.txt](LICENSE.txt): Apache-2.0 license text.
