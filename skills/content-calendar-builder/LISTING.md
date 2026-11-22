# Content Calendar Builder

## One line

Turns a plain list of topics into a dated posting calendar CSV, with holidays skipped and no channel repeated back to back.

## What it does

The script reads a text file with one topic per line. A line written as `channel|topic` is tagged to a channel; any other line goes to a channel called `general`. You give it a start date, the weekdays to post on, an optional weekly cap, and optional holiday dates. It walks forward from the start date, marks each open post slot, and fills the slots in date order.

For each slot it picks the channel with the most topics still waiting, skipping the channel used in the previous slot. Ties go to the channel that appears first in the file. Topics that cannot fit are listed by line number with a reason code, so nothing disappears silently. The output is a new CSV with four columns: date, weekday, channel, and topic. The script refuses to overwrite an existing file.

## When to use

Use it when a marketing lead has a backlog of topics already written and needs them placed on specific weekdays, with holidays left empty and channels rotated. It is useful when the same person has to check the calendar by hand and wants a first pass that can be re-run with a different start date or holiday list.

## When not to use

Do not use it to generate topic ideas, to decide which channels matter, or to post anything to a platform. It writes one CSV and does nothing else. It does not weigh audience data, time zones, or campaign priorities.

## Requirements

Python 3.9 or later, standard library only. No network access and no subprocess calls. The input file must be UTF-8 text and no larger than 2 MB.

## Example

Command, run from the skill folder on the shipped fixture:

```
python -I scripts/content_calendar.py fixtures/topics_9.txt --start 2027-01-04 --weekdays Mon,Wed,Fri --holidays 2027-01-18 --out <output-file>
```

Stdout, exit code 0:

```
{"scheduled": 9, "unscheduled": 0, "first_date": "2027-01-04", "last_date": "2027-01-25", "unscheduled_items": []}
```

Calendar written to `<output-file>`:

```
date,weekday,channel,topic
2027-01-04,Mon,blog,How to plan a month of posts in one afternoon
2027-01-06,Wed,newsletter,Five prompts that turn raw notes into a draft
2027-01-08,Fri,social,Behind the scenes of our editorial calendar
2027-01-11,Mon,blog,Choosing a posting cadence for a small team
2027-01-13,Wed,newsletter,What to do when a topic goes stale
2027-01-15,Fri,social,Quick tip: batch your captions on Fridays
2027-01-20,Wed,blog,Measuring what a content calendar actually earns
2027-01-22,Fri,newsletter,Reader questions answered this month
2027-01-25,Mon,social,Poll: which format should we run next
```

The 2027-01-18 holiday is skipped, so the Monday after the 15th is not used and the calendar moves to Wednesday the 20th.

## Limits

- Scheduling horizon is 730 days from the start date (working value).
- Input is capped at 2 MB and a channel name at 30 characters (working values).
- A file that has only one channel can place only one topic, because no channel may fill two consecutive slots.
- The script does not read the calendar back or check it against an existing calendar.
- Dates use the Gregorian calendar and the weekday names are English abbreviations only.

## Status

Provisional. Lint-clean, one smoke run. Not independently verified.
