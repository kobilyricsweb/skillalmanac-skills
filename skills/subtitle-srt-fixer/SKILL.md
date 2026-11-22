---
name: subtitle-srt-fixer
description: Checks SRT subtitle files for out-of-order or overlapping cues, cues shorter than 1 s or longer than 7 s, reading speed above 20 characters per second, lines over 42 characters and more than two lines, and writes a repaired copy to a new path on request. Use when a subtitle file has overlapping timings, cues that flash by too fast, or must pass a layout check before import into a video editor or a Remotion project. Do not use for translating subtitles, writing caption text, burning captions into video, or converting between VTT, ASS and SRT.
license: Apache-2.0
compatibility: Python 3.9+ stdlib only, no network (type A)
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  author_model: claude-haiku-5-5
  version: "0.1.0"
  network: none
---

# SRT subtitle fixer

Use `scripts/srt_check.py` to test one `.srt` file against fixed timing and layout limits, then, if asked, write a repaired copy. The script never writes the input file. It only sorts cues, trims overlaps and renumbers in the repaired copy. It does not rewrite caption text and does not retime cues beyond trimming an overlapping end.

## Workflow

1. Confirm the input. Required output: the input path, the file exists, is under 2 MB and decodes as UTF-8. If any of these fails, stop and report the error code from the script (see Output contract).
2. Run the check without `--fix`. Required output: the `issue_count` value and the full `issues` list, copied as returned.
3. Classify each issue by code using the threshold table. Required output: a count per code, and the cue numbers involved.
4. Decide on repair. Run with `--fix` only when the user asked for a repaired copy, or when `out_of_order` or `overlap` codes appear. Choose a new output path next to the input, for example `INPUT.fixed.srt`, unless the user gives one. Required output: the `fix` block.
5. Read `fix.remaining_issues`. These are the problems the repair cannot fix on its own. Required output: the remaining count and the list, with cue numbers in the repaired file's numbering.
6. Write the final report in the format under Output contract. Mention that repaired cue numbers differ from the input numbers when cues were reordered.

## Thresholds (working values)

These limits are working values chosen for this skill. They are not published industry standards. Report them as "working values" if asked for a source.

| Check | Code | Limit | Repaired by --fix |
|---|---|---|---|
| Start time earlier than an earlier cue | `out_of_order` | start < previous cue start | Yes, cues sorted by start |
| Start before an earlier cue ends | `overlap` | start < latest end of earlier cues | Yes, end trimmed to next start |
| End not after start | `non_positive_duration` | end <= start | No, reported only |
| Duration too short | `too_short` | under 1.000 s | No, reported only |
| Duration too long | `too_long` | over 7.000 s | No, reported only |
| Reading speed | `too_fast` | over 20.0 characters per second | No, reported only |
| Line length | `line_too_long` | any line over 42 characters | No, reported only |
| Line count | `too_many_lines` | more than 2 lines | No, reported only |
| Block without a timing line | `unparseable_block` | no `HH:MM:SS,mmm --> HH:MM:SS,mmm` line, or minutes or seconds of 60 or more | Blocks `--fix` (exit 2) |

Reading speed counts every character in the cue text, spaces included, and excludes line breaks. Duration exactly 1.000 s or 7.000 s passes.

## Repair rules (only when --fix is given)

1. Sort cues by start time. Equal starts keep file order.
2. For each cue in sorted order, set its end to the smaller of its own end and the next cue's start.
3. Renumber cues 1 to N in the new order. Timestamps are written as `HH:MM:SS,mmm`.
4. Write UTF-8 without a BOM and with LF line endings.

Not repaired: text edits, deleted cues, duration changes other than step 2, line breaks inside text, and any cue flagged for duration or speed.

## Output contract

Check result, printed as JSON on stdout (exit 0 or 1):

- `input` (string), `block_count`, `cue_count`, `issue_count` (integers)
- `issues`: list of objects with keys `cue`, `code`, `detail`. `cue` is the 1-based block number in the input file.
- `fix`: null without `--fix`. With `--fix`, an object with keys `output`, `cue_count`, `reordered` (boolean), `overlaps_trimmed` (integer), `renumbered` (true), `remaining_issue_count`, `remaining_issues` (same shape as `issues`, numbered in the output file).

Error result, one line on stdout (exit 2): `{"error": CODE, "detail": TEXT}`. Codes: `file_not_found`, `not_a_file`, `input_too_large`, `invalid_utf8`, `no_cues`, `options_need_fix`, `output_equals_input`, `output_is_directory`, `output_dir_missing`, `output_exists`, `fix_refused_unparseable`, `io_error`.

Final report to the user, in this order:

1. Summary: one sentence with the file name, `cue_count` and `issue_count`.
2. Issues table: columns `Cue`, `Code`, `Detail`, one row per issue, in the order returned.
3. Repair (only if run): output path, `overlaps_trimmed`, `remaining_issue_count`.
4. Not checked: the script does not check text content, spelling, speaker names or sync against audio.

## Script contract

File: `scripts/srt_check.py`. Stdlib only, reads one file, no network, no subprocess.

Arguments:

- `INPUT`: positional path to the `.srt` file.
- `--fix`: write a repaired copy.
- `--out PATH`: new output path for `--fix`. Default is `INPUT.fixed.srt` beside the input. Requires `--fix`.
- `--force`: allow replacing an existing output file. Never allows writing over the input. Requires `--fix`.

Exit codes: 0 no issues found. 1 issues found, including when `--fix` ran. 2 usage or input error, with the JSON error line.

Command lines:

```
python -I scripts/srt_check.py INPUT.srt
python -I scripts/srt_check.py INPUT.srt --fix --out OUTPUT.srt
python -I scripts/srt_check.py INPUT.srt --fix --out OUTPUT.srt --force
```

Use `--force` only when the user has said the existing output may be replaced.

## Refuse / stop when

- The output path resolves to the input path, with or without `--force`. Report `output_equals_input` and do not retry with another flag.
- The input is over 2 MB, is not UTF-8, or is a folder. Stop with the error code.
- The file has an unparseable block and the user asked for `--fix`. Stop and report the block numbers from the check run. Do not drop blocks to make the repair work.
- The file has no cue with a timing line. Report `no_cues`.
- The file is VTT, ASS or another format. The script reads only SRT. Do not convert.
- The user asks to translate, rewrite, shorten or correct caption text. Decline, since this skill only checks timing and layout.

## Files

- `scripts/srt_check.py`: the checker and repair script described above.
- `fixtures/six_cues.txt`: a six-cue SRT sample with one overlap, one fast cue, one short cue and one long cue. It is saved with a `.txt` extension so the package passes the text allow-list; pass it to the script unchanged. Use it to confirm the script runs.
- `LICENSE.txt`: Apache License 2.0 text for this package.
