---
name: username-candidate-screen
description: Screens a list of username candidates for length, allowed characters, edge separators, digit runs, confusable characters, repeated characters and near-duplicate pairs, then ranks them by number of findings. Use when a user has several handle options and wants the weak ones flagged before choosing one. Do not use for checking whether a username is available, taken or safe to register, for legal or trademark review, or for generating new names.
license: Apache-2.0
compatibility: Python 3.9+ standard library only, no network (type A).
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  author_model: claude-haiku-5-5
  version: "0.1.0"
  network: none
---

# Username candidate screen

Screens a plain-text list of handle candidates with one local script and returns a ranked table of the rule codes each candidate triggers. The script never contacts a platform, so it cannot say whether a name is free.

## Inputs

- One file, UTF-8 text, one candidate per line. Blank lines and lines starting with `#` are skipped.
- Each line is one candidate. A space inside a line is a character outside the allowed set and is flagged.
- Limits: 2 MB file size, 2000 candidates.

Shipped files:

- [scripts/username_screen.py](scripts/username_screen.py): the screening script (type A).
- [fixtures/candidates_smoke.txt](fixtures/candidates_smoke.txt): ten candidates with one planted problem each, for a smoke run.
- LICENSE.txt: Apache-2.0 license text.

## Workflow

1. Confirm the intake. Get the path of the user's file (use `<input-file>` in all commands) and confirm it is a candidate list, not a sentence or a spreadsheet. Output: the path and the number of lines the user expects.
2. Run the script with the exact command below. Output: the raw stdout table and the exit code.
3. Branch on the exit code. `0` means no findings, `1` means findings exist, `2` means the input was rejected; report the one-line JSON error from stderr and stop. Output: one status line such as `Exit 1: 10 candidates, 10 flagged`.
4. Map every code in the table to its rule in the Decision table below. Output: a Findings table with one row per flagged candidate.
5. Write the recommendation: keep the clean candidates, and for each NEAR_DUP or DUPLICATE pair keep one member only. Output: a Keep list and a Fix list.

## Decision table

Thresholds marked "working value" are not a published platform rule; they are this skill's defaults.

| Code | Check (lowercase compare unless stated) | Threshold | Action |
|---|---|---|---|
| LEN_SHORT | length below minimum | 3 characters (working value) | Lengthen |
| LEN_LONG | length above maximum | 20 characters (working value) | Shorten |
| CHARSET | any character outside A-Z, a-z, 0-9, underscore, period, hyphen; includes spaces, `@` and non-ASCII letters | none allowed | Remove or replace the character |
| EDGE_SEP | first or last character is `_`, `.` or `-` | none allowed (working value) | Move the separator inside or delete it |
| DIGIT_RUN | run of digits | 4 or more in a row (working value) | Drop the number or year |
| CONFUSABLE | two different characters from {1, l, I} (case kept); or two different characters from {0, o} (case ignored); or the pair `rn` | 2 distinct characters (working value) | Rewrite with letters that do not look alike |
| REPEAT | same character three times in a row | 3 in a row (working value) | Shorten the run |
| DUPLICATE | equal to another candidate after lowercasing | 1 match | Keep one copy |
| NEAR_DUP | differs from another candidate by exactly one edit (substitution, insertion or deletion) after lowercasing | 1 edit | Keep one of the pair |

Ranking: candidates sort by findings count ascending, then by input line number. A candidate with zero findings ranks first.

## Output contract

The script prints this to stdout, in this order:

1. Version line: `username-candidate-screen 0.1.0 (length 3-20)`.
2. Header: `rank  line  candidate  length  findings  codes`.
3. One row per candidate. `codes` is a comma-separated list in this order: LEN_SHORT, LEN_LONG, CHARSET, EDGE_SEP, DIGIT_RUN, CONFUSABLE, REPEAT, DUPLICATE, NEAR_DUP. A row with no findings shows `none`.
4. Summary line: `candidates=N flagged=F clean=C`.

The agent's reply to the user uses these three headings and no others:

- `## Summary`: exit status, candidates, flagged, clean.
- `## Findings`: a table with columns `rank`, `line`, `candidate`, `codes`, `action`, copied from the script output and the Decision table.
- `## Keep and fix`: two bullet lists, `Keep` and `Fix`.

## Script contract

Command (replace the placeholder with the user's file):

```
python -I scripts/username_screen.py <input-file>
```

- Arguments: exactly one, the path to the input file.
- Reads the file only. Writes nothing to disk.
- Stdout: the table described above.
- Stderr on exit 2: one JSON object on one line with keys `error` (text) and `exit` (value 2).
- Exit 0: every candidate is clean. Exit 1: at least one finding. Exit 2: usage error or rejected input (missing file, file over 2 MB, not UTF-8, no candidates, more than 2000 candidates).
- Output is deterministic: the same file always gives the same rows in the same order.
- Surrounding whitespace is stripped before any check, so a trailing space is never flagged on its own.
- Smoke run on the shipped fixture, which should exit 1 with ten flagged rows: `python -I scripts/username_screen.py fixtures/candidates_smoke.txt`.

## Refuse / stop when

- The user asks whether a username is available, registered or taken on any site or app. The script has no network access and this skill does not check availability.
- The user asks for a legal, trademark or brand-safety conclusion about a name. Report the rule codes only.
- The input is missing, larger than 2 MB, not UTF-8, has no candidates after blank and comment lines are removed, or has more than 2000 candidates. Exit 2, report the JSON error, and ask for a smaller or split file.
- The user asks the skill to write the report to a file or to overwrite the input. The script never writes files; offer the stdout text instead.
- The user asks for a score that is not the findings count, such as a popularity or memorability rating. This skill does not produce one.
- The user asks the skill to invent replacement names for flagged candidates. Report the codes and the action column; the user writes the replacements and reruns the screen on them.
