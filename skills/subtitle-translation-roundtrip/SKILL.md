---
name: subtitle-translation-roundtrip
description: Prepares SRT subtitle files for translation and rebuilds them on the original timings, checking cue count, cue numbering, empty cues, line count, line length and reading speed. Use when the user asks to translate subtitles, captions or an SRT file into another language and must keep every cue and its timing. Do not use for burned-in video text, speech transcription, retiming cues, or VTT and ASS files.
license: Apache-2.0
compatibility: Python 3.9+ stdlib only, no network (type A).
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  author_model: claude-haiku-5-5
  version: "0.1.0"
  network: none
---

# Subtitle translation roundtrip

The script extracts the cue text of an SRT file for translation, then rebuilds a new SRT on the original timings. It never translates. The agent translates between the two commands, and the SRT is written only after the translated cues pass every check in this file.

## Workflow

1. Extract the cues. Run:
   `python -I "<skill-folder>/scripts/srt_translate.py" extract "<input-srt>" "<work-dir>/cues.json"`
   Required output: exit code 0 and the stdout key `cue_count`. Record that count as N. On exit 2, stop (see "Refuse / stop when").

2. Make the translation file. Copy `<work-dir>/cues.json` to `<work-dir>/translated.json` and translate only the `text` values into the target language. Keep `format`, every `cue` number and the cue order. Do not add, merge, split or drop cues. Write a line break as a single `\n` inside a text value. Do not write an empty line inside a text value. Required output: exactly N entries in `cues`.

3. Check and rebuild. Run:
   `python -I "<skill-folder>/scripts/srt_translate.py" rebuild "<input-srt>" "<work-dir>/translated.json" "<output-srt>"`
   - Exit 0: the SRT is written to `<output-srt>`. Go to step 4.
   - Exit 1: nothing is written. Fix only the cues named in `findings[].cue` inside `translated.json`, then run step 3 again with the same `<output-srt>` path. Stop after 3 rebuild attempts (working value) and report status partial.
   - Exit 2: read the one-line JSON `error` on stderr, fix the named input, and run step 3 again.

4. Report. Write the final report in the output contract below. Do not claim the translation is correct: the checks cover structure and layout only.

## Check thresholds

| Code | What is checked | Limit | Action |
|---|---|---|---|
| COUNT_MISMATCH | Translated cue count equals original cue count | Exact match | Restore the missing or extra cues. No per-cue checks run while this finding stands. |
| INDEX_MISMATCH | Cue at position N carries cue number N | Exact match | Restore the original cue number. |
| EMPTY_CUE | Text is not blank | At least one visible character | Translate the cue. |
| BLANK_LINE | No empty line inside a text value | None allowed | Delete the empty line. |
| TOO_MANY_LINES | Lines per cue | 2 lines (working value) | Merge lines. |
| LINE_TOO_LONG | Characters per line, counted with Python len() | 42 characters (working value) | Shorten or rewrap the line. |
| READING_SPEED | Characters per second over the original cue duration, newlines not counted | 21.0 characters per second (working value) | Shorten the text. The timings cannot change. |

Fix order for a cue that has several findings:

1. Restore the cue number (INDEX_MISMATCH) and the text (EMPTY_CUE, BLANK_LINE) first, because the other checks depend on them.
2. For LINE_TOO_LONG, rewrap into two lines only when the cue has one line and the new lines are each 42 characters or fewer. Otherwise shorten the wording.
3. Re-check READING_SPEED after step 2. Shorten the text until the count is 21.0 or less. Do not drop meaning to pass; note the cue under Open questions if the meaning cannot fit.
4. Never change a cue number to make a count match. A count mismatch means a cue was lost or added, so restore it from `cues.json`.

## Script contract (type A)

Command lines:
- `python -I "<skill-folder>/scripts/srt_translate.py" extract <input-srt> <output-json>`
- `python -I "<skill-folder>/scripts/srt_translate.py" rebuild <original-srt> <translated-json> <output-srt>`

Exit codes: 0 ok (rebuild wrote the SRT). 1 findings (rebuild wrote nothing). 2 usage or input error. Argument errors from the parser also exit 2.

Stdout keys:
- extract: `status` ("ok"), `cue_count`.
- rebuild: `status` ("ok" or "findings"), `cue_count_original`, `cue_count_translated`, `findings` (a list of objects with `cue`, `code`, `detail`). `cue` is null only for COUNT_MISMATCH.

Stderr on exit 2: one JSON line with the key `error`.

Input rules: each file is at most 2 MB. Text must be UTF-8; a BOM is accepted. Each SRT cue needs a line containing `HH:MM:SS,mmm --> HH:MM:SS,mmm` with an end later than its start. The translated file needs a `cues` list whose items each hold an integer `cue` and a string `text`.

Output rules: the output file is created in exclusive mode. The script exits 2 if the path exists or equals an input path, and never overwrites. The SRT is UTF-8 without BOM with LF line endings.

Shipped files: [scripts/srt_translate.py](scripts/srt_translate.py), [fixtures/source.txt](fixtures/source.txt) (an SRT file with 6 cues), [fixtures/translated_planted.json](fixtures/translated_planted.json) (one line of 54 characters in cue 4, which triggers LINE_TOO_LONG), [fixtures/translated_fixed.json](fixtures/translated_fixed.json) (the same cue 4 rewrapped into two lines, which passes), and [LICENSE.txt](LICENSE.txt).

## Output contract (final report)

Use these headings in this order.

- `## Status`: one of `complete` (rebuild exit 0), `findings open` (last rebuild exit 1 and no further attempt), or `partial` (3 attempts used, or a request clause was refused).
- `## Cues`: a line `Original: N`, a line `Translated: M`.
- `## Findings`: a table with columns `Cue`, `Code`, `Detail` from the last rebuild run. Write `none` when the list is empty.
- `## Output`: the full path of the written SRT, or `not written`.
- `## Open questions`: a numbered list of refused or unresolved items, or `none`.

## Refuse / stop when

- The input file is missing, over 2 MB, not UTF-8, or has no cues. Exit 2: stop and report the error.
- A cue has no timing line, or its end is not later than its start. Exit 2: stop, because the source file needs repair by its owner.
- The output path exists or equals an input path. Exit 2: choose a new path. Never delete an existing file to make room.
- The source is VTT, ASS or another format that is not SRT: stop and say so.
- The request asks to change cue timings, merge cues or split cues: refuse that part only. Finish the translation of the existing cues, set status `partial`, and list the refused item under Open questions.
- Rebuild still returns findings after 3 attempts (working value): stop with status `partial` and list the open cue numbers.
- A cue cannot fit its limits without content from another cue (for example a sentence split across two cues): do not move text between cues. Shorten it and note it under Open questions.

## Limits

The checks cover structure and layout only. They do not verify meaning, grammar, names, dialect, tone, or sync with speech. Reading speed counts characters, not words or syllables. Line length counts characters, not rendered pixel width. The script does not know the target language and does not render or play video.
