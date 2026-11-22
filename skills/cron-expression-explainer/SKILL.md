---
name: cron-expression-explainer
description: Explains a five-field cron expression in plain English and lists its next run times in UTC, using a stdlib-only Python script. Use when a user pastes a cron string such as '*/15 9-17 * * 1-5' and asks what it means, needs the next N run times after a start time, or is checking whether a day-of-month and day-of-week pair fires on the days they expect. Do not use for crontab installation, systemd timers, cloud scheduler syntax with seconds or years, or time zones other than UTC.
license: Apache-2.0
compatibility: Python 3.9+ stdlib only, no network (type A).
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  author_model: claude-haiku-5-5
  version: "0.1.0"
  network: none
---

# Cron Expression Explainer

Type A skill. One script reads a JSON request file and prints JSON to stdout.
It makes no network calls and writes no files.

## Inputs

- A cron expression with exactly five whitespace-separated fields, in this order: minute, hour, day of month, month, day of week.
- A start time in UTC, written as `YYYY-MM-DDTHH:MM`. Seconds (`:SS`) and a trailing `Z` or `+00:00` are optional.
- An optional `count` from 1 to 50. The default is 5.

## Workflow

1. Count the fields in the expression. Output: the field count. If it is not 5, stop (see "Refuse / stop when").
2. Write the request to `cron_request.json` in the working folder. Use one JSON object for one expression, or a JSON list of up to 50 objects. Each object has the keys `expression`, `start` and `count`. Output: the file path and the number of requests written.
3. Run the command line in "Command line" below. Output: the exit code (0, 1 or 2) and the JSON on stdout.
4. Branch on the exit code. Exit 0: every request returned its full run count. Exit 1: at least one result has a finding (fewer runs than requested); report it as a finding. Exit 2: an input error; read the `error` text, correct the request once, and rerun. Output: the final exit code and, for exit 2, the error text.
5. Write the answer in the format given in "Output contract". Output: the Markdown answer with its four headings.

Do not guess the run times yourself. Copy them from `runs_utc`.

## Field rules

| Field | Position | Allowed values | Names accepted | Note |
|---|---|---|---|---|
| minute | 1 | 0-59 | none | |
| hour | 2 | 0-23 | none | 24-hour clock |
| day of month | 3 | 1-31 | none | |
| month | 4 | 1-12 | JAN to DEC, any case | |
| day of week | 5 | 0-7 | SUN to SAT, any case | 0 and 7 both mean Sunday |

Syntax forms (each item can be combined with commas into a list):

| Form | Meaning | Example | Values produced |
|---|---|---|---|
| `*` | whole range | `*` | every value in the field |
| `a` | one value | `9` | 9 |
| `a-b` | inclusive range | `9-17` | 9 through 17 |
| `*/s` | whole range, every s-th value | `*/15` | 0, 15, 30, 45 for minute |
| `a/s` | from a up to the field maximum, every s-th | `5/20` | 5, 25, 45 for minute |
| `a-b/s` | range, every s-th value | `MON-FRI/2` | 1, 3, 5 |

The script refuses a step of 0, a reversed range such as `5-1`, a value outside its field, and empty list items.

## Day rule (decision table)

A day field whose text starts with an asterisk counts as unrestricted. This is the classic Vixie behaviour.

| Day of month text | Day of week text | Rule the script applies | A day matches when |
|---|---|---|---|
| starts with `*` | starts with `*` | AND | both fields match |
| starts with `*` | restricted (any other text) | AND | both fields match |
| restricted | starts with `*` | AND | both fields match |
| restricted | restricted | OR | either field matches |

The `day_rule` key in the JSON is `or` only for the last row. Other cron implementations may differ, so say so when the user runs the expression elsewhere.

## Thresholds (working values chosen for this script, not industry standards)

| Limit | Value |
|---|---|
| Input file size | 2 MB (2,097,152 bytes) |
| Expression length | 200 characters |
| Requests per input file | 1 to 50 |
| `count` per request | 1 to 50, default 5 |
| Nesting depth of input JSON | 8 levels |
| Search horizon after the start time | 2928 days (8 x 366) |
| Smallest run considered | the next whole minute after start, so a run exactly at start is not listed |

## Output contract

The final answer is Markdown with these four headings, in this order:

1. `## Meaning` lists the five lines of the `explanation` array for each request, as bullets. Copy the text unchanged.
2. `## Next runs (UTC)` lists each value of `runs_utc` as a bullet. If the list is empty, write: No runs found within the search horizon.
3. `## Findings` lists each entry of `findings`. If there are none, write: None.
4. `## Request` lists the `expression`, `start_utc` and `count_requested` for each request.

The script's JSON has these keys. The top level holds `items` (an integer) and `results` (a list). Each result holds `index`, `expression`, `start_utc`, `count_requested`, `fields` (an object with keys `minute`, `hour`, `day_of_month`, `month` and `day_of_week`, each a comma-separated list of normalized values), `day_rule` (`or` or `and`), `explanation` (a list of strings), `runs_utc` (a list of strings) and `findings` (a list of strings).

## Refuse / stop when

- The expression does not have exactly five fields. Macros such as `@daily` or `@reboot` and six-field forms with seconds are refused. Ask the user for a five-field expression.
- The expression uses syntax outside the table above, such as `L`, `W`, `#` or `?`. The script exits 2 on these. Ask the user what schedule they want.
- The start time has an offset other than `Z` or `+00:00`. Do not convert time zones silently. Ask the user for the time in UTC.
- The user asks you to install, edit or create a scheduled job on any system. This skill only explains expressions and lists times.
- The input exceeds a limit in the thresholds table. Split the request into smaller files.
- The script exits 2 twice for the same request. Stop and report the error text.

## Script contract

Script: `scripts/cron_explain.py`. Python 3.9+ standard library only.

- Argument: `--input PATH` (required). The file must be UTF-8 JSON, at most 2 MB.
- Reads only the input file. Writes JSON to stdout. Writes no files.
- Exit 0: every request returned its requested number of runs.
- Exit 1: at least one request returned fewer runs. This is a finding, not a crash.
- Exit 2: usage or input error. Stdout holds one line of JSON with an `error` key.

## Command line

```
python -I scripts/cron_explain.py --input cron_request.json
```

Smoke test input: `fixtures/smoke.json` (expression `*/15 9-17 * * 1-5`, start `2026-01-05T08:00Z`, count 5). Expected first run: `2026-01-05T09:00:00Z`.

## Package files

`SKILL.md`, `LICENSE.txt`, `scripts/cron_explain.py`, `fixtures/smoke.json`, `fixtures/batch.json`, `fixtures/bad_field.json`.
