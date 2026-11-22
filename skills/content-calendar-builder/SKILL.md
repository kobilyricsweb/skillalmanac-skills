---
name: content-calendar-builder
description: Builds a dated content calendar CSV from a topics file, posting weekdays, a weekly cap and holiday dates. Use when a marketing lead must turn a backlog of topics into a posting schedule, skip holidays, avoid the same channel twice in a row and see which topics did not fit. Do not use for writing the topics, choosing channels as a strategy, or publishing posts automatically.
license: Apache-2.0
compatibility: Python 3.9+ stdlib only, no network (type A).
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  author_model: claude-haiku-5-5
  version: "0.1.0"
  network: none
---

# Content Calendar Builder

Runs [scripts/content_calendar.py](scripts/content_calendar.py) on a topics file and writes a new CSV calendar. The script does the scheduling; the agent collects intake, runs the command, and reports the result.

## Workflow

1. **Collect intake.** Required: topics file, start date (`YYYY-MM-DD`), posting weekdays, output path. Optional: posts per week, holiday dates. Output: an intake table with each value confirmed by the user.
2. **Prepare the topics file.** Save as UTF-8 text, one topic per line. A line `channel|topic` splits on the first `|`. A line without `|` goes to channel `general`. Output: `<input-file>` with no empty channel or topic fields.
3. **Choose a new output path.** The path must not exist yet. Output: `<output-file>`, a path the user has not used before.
4. **Run the script** (command below). Output: one JSON line on stdout (exit 0 or 1) or one JSON line on stderr (exit 2).
5. **Read the exit code.** Exit 0: every topic scheduled. Exit 1: the calendar was written, but some topics were not scheduled; list them by line number and reason. Exit 2: report the `error` code and `detail`, fix the cause, and use a new output path.
6. **Hand back the result.** Output: the summary table in the output contract below, then the calendar path and the list of unscheduled lines.

Command, run from the skill folder:

```
python -I scripts/content_calendar.py <input-file> --start <YYYY-MM-DD> --weekdays <Mon,Wed,Fri> --out <output-file>
```

Optional flags: `--per-week <N>` and `--holidays <YYYY-MM-DD,YYYY-MM-DD>`. Example smoke check on the shipped fixture: `python -I scripts/content_calendar.py fixtures/topics_9.txt --start 2027-01-04 --weekdays Mon,Wed,Fri --holidays 2027-01-18 --out <output-file>` should exit 0 with 9 scheduled rows.

## Decision and threshold table

| Rule | Value | Status |
|---|---|---|
| Weekday names | Mon, Tue, Wed, Thu, Fri, Sat, Sun; first three letters, any case | fixed |
| Default posts per ISO week | number of listed weekdays | fixed |
| Allowed `--per-week` | 1 up to the number of weekdays | fixed |
| Scheduling horizon | 730 days from `--start` | working value |
| Input size cap | 2 MB (2,097,152 bytes) | working value |
| Maximum channel length | 30 characters | working value |
| Default channel | `general` | fixed |
| Channel rule | a channel never fills two consecutive slots | fixed |
| Channel choice per slot | among allowed channels, the one with the most topics left; ties go to the channel that appears first in the file | fixed |
| One channel only | at most one topic scheduled | fixed consequence |

Worked cases the agent can check against:

- Holiday: with `--weekdays Mon,Wed,Fri` and `--holidays 2027-01-18`, the Monday of that week is dropped and the next listed weekday after it takes the next topic. The fixture run places topic 7 on `2027-01-20`.
- Weekly cap: with the default cap and Mon,Wed,Fri, each ISO week has at most three slots. With `--per-week 2`, the third weekday of each week stays empty.
- Skewed input: `fixtures/topics_skewed.txt` has four `blog` lines and one `newsletter` line. The run takes line 1 (blog), line 5 (newsletter), then line 2 (blog). Lines 3 and 4 are unscheduled with `channel_run_limit`, and the exit code is 1.

## Output contract

Calendar CSV, header exactly `date,weekday,channel,topic`. `date` is `YYYY-MM-DD`; `weekday` is `Mon` to `Sun`; rows are in date order. The file is UTF-8 with no index column, and a topic containing a comma is quoted by the CSV writer.

Stdout, one JSON line, on exit 0 or 1:

| Key | Type | Meaning |
|---|---|---|
| `scheduled` | integer | rows written |
| `unscheduled` | integer | topics not placed |
| `first_date` | string or null | first scheduled date |
| `last_date` | string or null | last scheduled date |
| `unscheduled_items` | list | objects with `line`, `channel`, `reason` |

Reason codes in `unscheduled_items`: `channel_run_limit` (the only topics left share the previous slot's channel) and `horizon_exhausted` (slots ran out inside the 730-day horizon).

Stderr, one JSON line, on exit 2: keys `error` and `detail`. Error codes: `bad_arguments`, `bad_date`, `bad_weekday`, `input_missing`, `input_too_large`, `input_not_utf8`, `bad_line`, `no_topics`, `output_exists`, `output_is_input`, `output_unwritable`.

Exit codes: 0 all topics scheduled; 1 at least one topic unscheduled, calendar still written; 2 usage or input error, no calendar written.

## Shipped files

- [scripts/content_calendar.py](scripts/content_calendar.py): the scheduler.
- [fixtures/topics_9.txt](fixtures/topics_9.txt): nine topics across three channels, for the smoke check.
- [fixtures/topics_skewed.txt](fixtures/topics_skewed.txt): one channel dominating, to show exit 1 and `channel_run_limit`.
- [LICENSE.txt](LICENSE.txt): Apache License 2.0.

The fixtures are read-only inputs for the smoke check. Copy them before editing, and never point `--out` at a fixture.

## Refuse / stop when

- The output path already exists. Stop and ask for a new path. Never overwrite.
- The output path is the topics file. Refuse.
- The topics file is over 2 MB or is not UTF-8. Stop and ask the user to split or re-save it.
- The start date or weekdays are missing or invalid. Stop and ask a numbered question for each missing value.
- Every topic has the same channel and there is more than one topic. Stop and ask for channel tags; the script can place only one topic.
- The user asks the skill to publish, post or schedule to a platform. Refuse; this skill writes a CSV only.
- The user asks for topic ideas or channel strategy. Stop; this skill schedules topics the user supplies.
