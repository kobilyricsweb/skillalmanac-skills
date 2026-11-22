---
name: subtitle-format-converter
description: Converts caption files between WebVTT and SRT, or strips one to a plain transcript, and reports cue counts and any cue whose end time falls before its start. Use when a video player, platform, or editor needs a specific caption format, such as turning a VTT file into SRT, or when a plain text transcript of existing captions is needed. Do not use for translating captions, burning subtitles into video, retiming cues, or checking captions against the audio.
license: Apache-2.0
compatibility: Python 3.9+ stdlib only, no network (type A).
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  author_model: claude-haiku-5-5
  version: "0.1.0"
  network: none
---

# Subtitle Format Converter

Converts one WebVTT or SRT caption file into WebVTT, SRT, or a plain-text transcript with `scripts/sub_convert.py`. The script does all parsing and writing. The agent collects the inputs, runs the command, branches on the exit code, and reports the result.

## Workflow

1. Collect intake. Required: the input file path (shown as `<input-file>`), the target `srt`, `vtt`, or `txt`, and a new output path that does not exist yet. Optional: `--merge-rolling`, which applies only to `txt`. Output: an intake note with those four values. If the output path is missing, ask for it. Never choose a path that already exists.
2. Check the input size. Output: the byte count. If it is above 2,097,152 bytes, stop under "Refuse / stop when".
3. Run the command in "Script contract". Output: the stdout JSON line on exit 0 or 1, or the stderr JSON line on exit 2, plus the numeric exit code.
4. Branch on the exit code using the decision table. Output: the status value (`complete`, `partial`, or `refused`).
5. On exit 0 or 1, compare `cues_read` with `cues_written`. For `srt` and `vtt`, the difference is the number of cues with no text after tag removal. For `txt` without merge, the difference is 0. For `txt` with merge, the difference is the number of cues whose lines were all removed as rolling repeats. Output: the difference and its reason. If the difference does not match one of these, list it under Open questions.
6. Write the final report in the output contract, in the section order given there.

## Decision table

| Check | Value | Action |
|---|---|---|
| Input size | above 2,097,152 bytes (working value, cap set by the author brief) | exit 2, `FILE_TOO_LARGE`; ask for a shorter export or a split |
| Input format | first non-blank line starts with `WEBVTT` | read as vtt; any other file is read as srt |
| Same format | input format equals `--to` | exit 2, `SAME_FORMAT`; ask for a different target |
| Timestamp | `H:MM:SS.mmm` or `MM:SS.mmm` (vtt); `HH:MM:SS,mmm` (srt); minutes and seconds 00 to 59 | otherwise exit 2, `BAD_TIMING`, with the block number |
| Cue end before start | end time earlier than start time | exit 1, finding `END_BEFORE_START`; output is still written |
| VTT NOTE, STYLE, REGION blocks | first word of the block is NOTE, STYLE, or REGION | dropped and counted in `blocks_dropped` |
| Tags in srt and vtt output | `<b>`, `<i>`, `<u>` kept; every other tag removed | cue identifiers and cue settings are never written |
| Tags in txt output | every tag removed | `&amp;` and other entities are left as written |
| Rolling merge (`--merge-rolling`, txt only) | first cleaned line of a cue equals last cleaned line of the previous cue | drop that first line; working value |

## Output contract

Stdout, on exit 0 or 1, is one JSON line with these keys in this order: `input_format`, `output_format`, `cues_read`, `cues_written`, `blocks_dropped`, `output`, `findings`. Each finding is an object with keys `code`, `cue`, `start`, `end`. `cue` is the 1-based position among all timed cues, and `start` and `end` use `HH:MM:SS.mmm`.

The written file:
- `srt`: cues numbered from 1, `HH:MM:SS,mmm --> HH:MM:SS,mmm`, text lines, one blank line between cues, LF line endings, UTF-8 without BOM, final newline.
- `vtt`: first line `WEBVTT`, a blank line, then cues without numbers using `HH:MM:SS.mmm --> HH:MM:SS.mmm`.
- `txt`: one line per emitted cue, its text lines joined with one space, no timestamps.

Final report to the user, with these headings in this order:
- `## Result`: a table with columns `Field` and `Value`, one row for each of `input_format`, `output_format`, `cues_read`, `cues_written`, `blocks_dropped`, `output`.
- `## Findings`: a table with columns `Cue`, `Start`, `End`, `Code`. Write "No findings." when the list is empty.
- `## Status`: one of `complete` (exit 0), `partial` (exit 1, file written, findings open), or `refused` (exit 2, output not written).
- `## Open questions`: a numbered list, or "None."

## Script contract

Command line:

```
python -I scripts/sub_convert.py --input <input-file> --to {srt,vtt,txt} --output <output-file> [--merge-rolling]
```

Arguments:
- `--input`: an existing UTF-8 file of 2,097,152 bytes or less.
- `--to`: `srt`, `vtt`, or `txt`.
- `--output`: a new file name in an existing folder. The script never overwrites it.
- `--merge-rolling`: optional; valid only with `--to txt`.

Exit codes: 0 ok; 1 findings (output is still written); 2 usage or input error (one JSON line on stderr with keys `error` and `code`, plus `block` or `line` where relevant).

| Code | Exit | Meaning |
|---|---|---|
| `USAGE` | 2 | missing or bad arguments, or `--merge-rolling` without `--to txt` |
| `FILE_NOT_FOUND` | 2 | input path does not exist |
| `NOT_A_FILE` | 2 | input path is a folder or other non-file |
| `READ_ERROR` | 2 | input cannot be read |
| `FILE_TOO_LARGE` | 2 | input above 2,097,152 bytes |
| `NOT_UTF8` | 2 | input bytes are not valid UTF-8 |
| `BAD_BLOCK` | 2 | a caption block has no timing line; `block` gives its number |
| `BAD_TIMING` | 2 | timing line or timestamp malformed; `block` gives its number |
| `NO_CUES` | 2 | no timed cue, or no cue with text to write |
| `SAME_FORMAT` | 2 | input already in the `--to` format |
| `OUTPUT_IS_INPUT` | 2 | output path is the input file |
| `OUTPUT_DIR_MISSING` | 2 | output folder does not exist |
| `OUTPUT_EXISTS` | 2 | output path already exists; nothing is overwritten |
| `WRITE_ERROR` | 2 | output file cannot be written |
| `END_BEFORE_START` | 1 | finding in the `findings` list; cue end earlier than cue start |

## Refuse / stop when

- The input is above 2,097,152 bytes: stop with `FILE_TOO_LARGE`; ask for a shorter export or a split.
- The input is not valid UTF-8: stop with `NOT_UTF8`; ask the user to re-export as UTF-8. Do not guess an encoding.
- The output path already exists: stop with `OUTPUT_EXISTS`; ask for a new name. Never delete or overwrite the existing file.
- The output path is the input file: stop with `OUTPUT_IS_INPUT`.
- The input is ASS, SSA, TTML, SBV, or any format other than WebVTT or SRT: stop; the script reads only WebVTT and SRT.
- The request also asks to translate, retime, correct, or burn in captions: refuse only that clause, keep the conversion, set Status to `partial`, and list the refused clause under Open questions.

## Files shipped

- `scripts/sub_convert.py`: the converter described in the script contract.
- `fixtures/sample_captions.txt`: a five-cue WebVTT file with a NOTE block, a STYLE block, cue settings, voice and class tags, and a rolling caption pair. The format is detected from content, so the `.txt` extension is only for packaging. Used for the smoke run.
- `fixtures/end_before_start_captions.txt`: a three-cue SRT file in which cue 2 ends before it starts. Used for the exit 1 check.
- `LICENSE.txt`: the Apache-2.0 license text.
