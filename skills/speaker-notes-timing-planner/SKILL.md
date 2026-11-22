---
name: speaker-notes-timing-planner
description: Estimates speaking time for each slide from its speaker notes and checks whether the whole talk fits its time slot, then lists the words to cut when it does not. Use when a talk or presentation must fit a fixed slot, speaker notes need a per-slide time budget, or a deck runs over and needs specific cuts. Do not use for writing or rewriting the slide content itself, for timing a live rehearsal, or for measuring audio or video length.
license: Apache-2.0
compatibility: Python 3.9+ stdlib only, no network (type A).
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  author_model: claude-haiku-5-5
  version: "0.1.0"
  network: none
---

# Speaker notes timing planner

This skill turns a plain text or Markdown file of speaker notes into a timing report. The report estimates speaking seconds per slide, adds a fixed transition allowance per slide, compares the total with the talk slot, and lists exact word cuts when the talk runs over. The arithmetic is done by the bundled script, so the numbers are repeatable. Your job is to run it, read the result, and write the plan.

The pace default of 130 words per minute is a working value chosen for this skill. It is not an industry standard. A speaker who is slower or faster should pass the measured pace with `--wpm`, and the report states the pace it used.

## Package files

- [scripts/talk_timing.py](scripts/talk_timing.py): the timing script. Stdlib only, read-only, writes only to stdout.
- [fixtures/sample_talk_8_slides.md](fixtures/sample_talk_8_slides.md): an eight-slide sample talk for a dry run.
- [LICENSE.txt](LICENSE.txt): Apache License 2.0.

## Inputs you need before running

1. Notes file path. Slides are separated by lines that are exactly three hyphens (a line with only the separator text). A file with no separator line is treated as one slide.
2. Slot length in minutes, greater than 0 and at most 600.
3. Pace in words per minute, only if the user gave a measured value. Allowed range is 60 to 220. Default is 130.
4. Transition seconds per slide, only if the user gave one. Allowed range is 0 to 60. Default is 5.

## Workflow

1. Confirm the inputs above. Required output: the file path, the slot in minutes, and the pace and transition values that will be used, each marked "default" or "user value".
2. Run the script with the exact command line in the next section. Required output: the raw JSON and the exit code.
3. If the exit code is 2, stop and report the one-line JSON error text verbatim. Do not guess at a fix for the file.
4. Read the JSON and classify the result with the decision table below. Required output: one row of the table that applies, with its numbers.
5. Build the plan from the cuts list, if there is one. For each cut, name the slide number, the words to remove, and the seconds saved. Do not invent cuts the script did not list.
6. Write the report in the output contract below. Required output: all four headings present, even when a section is empty.

## Decision table

| Condition in the JSON | Action |
|---|---|
| fits is true | Report the talk length and the spare seconds (minus over_seconds). No cuts. |
| fits is false and over_seconds is 60 or less | Apply the cuts list. Each cut is a word removal from one slide. |
| fits is false and over_seconds is more than 60 | Apply the cuts list, then state that the cuts are large and ask the owner whether to drop a slide or extend the slot. |
| any slide has flagged true | Name that slide and say it holds more than 25 percent of the talk. Suggest splitting it into two slides. |
| unfixed_words is greater than 0 | The cuts cannot close the gap without removing more than half of the listed slides. Report the unfixed words and recommend dropping a whole slide or extending the slot. |
| pace is not the default 130 | Repeat the pace in the report, since every number depends on it. |

The script caps the cut on any single slide at half of that slide's words, rounded down. A slide with one word is never cut.

## Command line

Run from the skill folder:

python -I "scripts/talk_timing.py" "<notes-file>" --minutes 10 [--wpm 130] [--transition-seconds 5]

The sample dry run is:

python -I "scripts/talk_timing.py" "fixtures/sample_talk_8_slides.md" --minutes 10

## Script contract

Arguments:
- first positional argument: path to the notes file
- `--minutes` (required): talk slot, greater than 0 and at most 600
- `--wpm` (optional, integer, default 130): pace, 60 to 220
- `--transition-seconds` (optional, default 5): seconds per slide, 0 to 60

Output on stdout is one JSON object with these keys:
- `source`, `assumptions` (object with `wpm`, `transition_seconds`, `flag_share_percent`, `cut_cap_percent_of_slide`)
- `slot_minutes`, `talk_seconds`, `talk_minutes`, `over_seconds`, `fits`
- `slides`: list of objects with `slide`, `words`, `speaking_seconds`, `slide_seconds`, `share_percent`, `flagged`
- `cuts`: list of objects with `slide`, `cut_words`, `seconds_saved`
- `unfixed_words`

Exit codes:
- 0: the talk fits the slot
- 1: the talk overruns the slot (a finding; the JSON is still complete)
- 2: usage or input error; one-line JSON `{"error": "..."}` on stderr and nothing on stdout

The script never writes files. To keep the report, redirect stdout yourself.

## Output contract

Use these four headings in this order.

1. `## Timing summary`: a table with the columns `Slide | Words | Speaking s | Slide s | Share % | Flag`, one row per slide, then a line with talk minutes, slot minutes, and fits yes or no.
2. `## Cuts`: a bulleted list, one item per cut, in the form `slide N: remove W words (saves S s)`. Write `None` if the cuts list is empty.
3. `## Decision`: one sentence naming the decision-table row that applied, followed by the unfixed words if any.
4. `## Assumptions`: pace, transition seconds, and whether each came from the default or the user.

## Refuse / stop when

- The input path does not exist or cannot be read (exit 2).
- The file is not valid UTF-8, is larger than 2 MB, or has more than 500 slides (exit 2).
- The file has no words in any slide (exit 2, "no words found" error).
- The slot is 0 or below, above 600 minutes, or the pace or transition is outside its range (exit 2).
- The user asks you to rewrite, shorten in wording, or improve the slide content. Report the cuts only, and say the rewrite is outside this skill.
- The user asks for audio or video length, or for timing from a recording. This skill has no access to either.
- The user asks for a timing figure they say comes from an industry study. Say the 130 pace is a working value and do not cite a source.

## Notes for the agent

A word is a whitespace-separated token with at least one letter or digit, so bullet markers and lone punctuation do not count. Whitespace-only chunks between separators are dropped and do not count as slides. Each kept slide gets the transition allowance, so the transition total equals the slide count times the transition seconds.
