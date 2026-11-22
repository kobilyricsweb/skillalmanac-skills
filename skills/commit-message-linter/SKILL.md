---
name: commit-message-linter
description: Checks commit messages saved in a text file against Conventional Commits rules and reports each failure as JSON and as a table. Use when a team wants a pass or fail check on commit titles and bodies before a release, when a pull request needs its commit list validated, or when a changelog step needs well-formed input. Do not use for reviewing code changes, rewriting messages, reading a git repository, or any task that needs git itself to run.
license: Apache-2.0
compatibility: Python 3.9+ stdlib only, no network (type A).
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  author_model: claude-haiku-5-5
  version: "0.1.0"
  network: none
---

# Commit Message Linter

This skill checks a file of commit messages against a fixed set of layout rules. It runs one script, `scripts/lint_commits.py`, and turns its JSON into a report. The script never runs git, never writes files and never changes the input.

## Files in this package

- `scripts/lint_commits.py` - the linter (type A, stdlib only).
- `fixtures/sample_commits.txt` - six-message smoke input: messages 1 to 3 pass, 4 to 6 fail.
- `LICENSE.txt` - Apache-2.0 license text.
- `evals/trigger_queries.json` - six prompts with expected trigger yes or no.
- `evals/evals.json` - three task checks: the smoke command, a git refusal and a bad-encoding case.

## Input the user must supply

The input is one UTF-8 text file. Each commit message is separated from the next by a line that contains only three hyphens (`---`). The agent does not run git. The user produces the file, for example by running a git log command that prints the full message body followed by a separator line, and saves the output. A line of three hyphens inside a message body counts as a separator.

## Workflow

1. **Confirm the input.** Check that the path names a regular file. Required output: the file name and the number of separator lines (the message count is the separator count plus one, minus a trailing empty chunk).
2. **Fix the type list.** Use the default list unless the user's project publishes its own list. Default: `feat,fix,docs,style,refactor,perf,test,build,ci,chore,revert`. Required output: the list used, written out in full.
3. **Fix the limits.** Use 72 for `--max-subject` and 72 for `--max-body`. Allowed range for each is 10 to 200. Required output: the two values used.
4. **Run the script.** Use the command in the next section, with the relative path from the skill folder. Required output: the exact command line and the exit code.
5. **Read the JSON.** Take `messages_checked`, `messages_with_errors`, `error_count` and each result whose `ok` is false. Required output: the three counts.
6. **Interpret codes.** Use the rule table below. For each E005 error, check by hand whether the first word is a real past tense or gerund; report it as a candidate, not a confirmed error. Required output: one line per error.
7. **Write the report.** Use the output contract below. Do not propose new wording for bodies. For E001, E002, E004 and E005 you may suggest a corrected subject line, marked as a suggestion.

## Command

    python -I scripts/lint_commits.py fixtures/sample_commits.txt

With options:

    python -I scripts/lint_commits.py INPUT --types feat,fix,docs,ci --max-subject 72 --max-body 72

Replace `INPUT` with the user's file path. Pass `--types` only when the project uses a different list.

## Script contract

Arguments:

- `INPUT` (required): path to the UTF-8 text file.
- `--types LIST` (default `feat,fix,docs,style,refactor,perf,test,build,ci,chore,revert`): 1 to 50 comma-separated lowercase words, no duplicates.
- `--max-subject N` (default 72): subject length limit, 10 to 200.
- `--max-body N` (default 72): body line length limit, 10 to 200.

Standard output on success or findings, a JSON object with these keys: `tool`, `version`, `input` (base name only), `types`, `limits` (`max_subject`, `max_body`), `messages_checked`, `messages_with_errors`, `error_count`, `results`. Each entry of `results` has `index` (1-based), `subject` (first line, cut to 200 characters), `ok` (boolean) and `errors` (list of objects with `code`, `rule`, `detail`).

Exit codes:

- `0`: every message passes.
- `1`: at least one error was found. The JSON is still written to standard output.
- `2`: usage or input error. Nothing is written to standard output. Standard error holds one line of JSON, for example `{"error": "input is not valid UTF-8"}`.

Input limits: 2 MB file size, 1000 messages, 4000 characters per line. A leading byte order mark is removed. Any other invalid UTF-8 is exit 2.

## Rule table

Working values chosen for this skill. They are not published thresholds.

| Code | Rule | Check | Working value |
|---|---|---|---|
| E001 | header-format | Subject matches `type(scope)!: description`. Type is lowercase letters. Scope is letters, digits, dot, underscore, slash or hyphen. Exactly one space after the colon. | regex |
| E002 | unknown-type | Type is in the `--types` list. Runs only when E001 did not fire. | 11 default types |
| E003 | subject-too-long | Subject length in characters. | 72 |
| E004 | subject-trailing-period | Subject ends with a period. | none |
| E005 | subject-not-imperative | First word of the description ends in `ed` or `ing` after lower-casing. Runs only when E001 did not fire. Known false positives: `need`, `feed`, `bring`. | suffix rule |
| E006 | missing-blank-line-before-body | Line 2 has text while the message has more text after it. | none |
| E007 | body-line-too-long | A body line is longer than the limit, trailing spaces removed. | 72 |
| E008 | breaking-change-footer-missing | `!` is in the header but no line starts with `BREAKING CHANGE: ` or `BREAKING-CHANGE: `. | none |
| E009 | empty-message | A message has no non-blank line. | none |

## Decision table for the exit code

| Exit code | Meaning | What the agent does |
|---|---|---|
| 0 | All messages pass | Report "all N messages pass" with the limits used. Stop. |
| 1 | One or more errors | Build the failing-message table. Apply step 6 to each error. |
| 2 | Input or usage error | Quote the error text from standard error. Do not guess a report. Ask the user for a fix. |

## Output contract

The report has exactly these three sections, in this order.

    # Commit lint report

    ## Summary

    | Field | Value |
    |---|---|
    | Input file | (base name) |
    | Types | (comma list) |
    | Limits | max subject N, max body N |
    | Messages checked | N |
    | Messages with errors | N |
    | Error count | N |
    | Exit code | 0, 1 or 2 |

    ## Failing messages

    | Index | Subject | Code | Rule | Detail |
    |---|---|---|---|---|

    One row per error. Subject is cut to 60 characters with `...` added when cut. If there are no failing messages, write "None." in place of the table.

    ## Not checked

    - Git history, authors, dates and diffs.
    - Whether a scope matches a project's component list.
    - Whether the subject describes the change accurately.

## Refuse / stop when

- The path is a directory, a git repository, or does not exist. Stop and ask for the file.
- The user asks the agent to run git, read a repository, or amend, rebase or rewrite commits.
- The user asks the script to write its output to the input path. The script has no output file option; say so and offer the report in chat.
- The input is larger than 2 MB, has more than 1000 messages, or has a line over 4000 characters (exit 2). Ask the user to split the file.
- The input is not valid UTF-8 (exit 2). Ask the user to save it again as UTF-8.
- The input contains what looks like a password, token or key. Stop, do not repeat the value in the report, and ask the user to remove it and run again.
- The user asks for a judgement on code quality or on what a change does.
- The user asks you to fix messages in the input file. Offer the corrected subjects in the report, but do not edit the file.
