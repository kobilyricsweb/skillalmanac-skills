# Subtitle Format Converter

## One line

Converts WebVTT and SRT caption files to WebVTT, SRT, or a plain-text transcript, and flags any cue whose end time falls before its start time.

## What it does

The script reads one caption file and writes one new file. It detects WebVTT from a leading WEBVTT line and treats everything else as SRT. WebVTT NOTE, STYLE, and REGION blocks are dropped and counted. Cue numbers, cue identifiers, and cue settings such as position and alignment are not carried into the output. In SRT and WebVTT output, only bold, italic, and underline tags survive; every other tag, including voice and class tags, is removed. Plain-text output removes all tags and writes one line per cue. With the rolling-merge flag, a cue that opens with the line the previous cue closed with has that repeated line removed, which suits auto-generated captions that scroll.

Every run prints one JSON line with the cue counts, the number of blocks dropped, and any findings. A cue that ends before it starts is reported and still written, so the source timing can be reviewed rather than silently changed.

## When to use

Use it when a player, upload form, or editor accepts only one of the two caption formats and the file you hold is in the other. Use it when a readable transcript is needed from an existing caption file. Run it once per file, with a new output name each time, and read the findings before the output is published.

## When not to use

Do not use it to translate captions, to move or stretch cue timing, to burn subtitles into video, or to check captions against the audio. It does not read ASS, SSA, TTML, or SBV files. It is not a caption-quality checker.

## Requirements

Python 3.9 or later. The script uses only the standard library and makes no network calls. The input must be UTF-8 text of 2,097,152 bytes or less. The output path must not exist.

## Example

Run from the skill folder, with the smoke fixtures:

```
python -I scripts/sub_convert.py --input fixtures/sample_captions.txt --to srt --output smoke_out.srt
```

Output (exit 0):

```
{"input_format": "vtt", "output_format": "srt", "cues_read": 5, "cues_written": 5, "blocks_dropped": 2, "output": "smoke_out.srt", "findings": []}
```

```
python -I scripts/sub_convert.py --input smoke_out.srt --to txt --output smoke_out.txt --merge-rolling
```

Output (exit 0), followed by the content of `smoke_out.txt`:

```
{"input_format": "srt", "output_format": "txt", "cues_read": 5, "cues_written": 5, "blocks_dropped": 0, "output": "smoke_out.txt", "findings": []}
Welcome back to the show.
Today we test conversions. And the captions roll.
Next we check the timing.
Later italic text &amp; more.
Final cue.
```

```
python -I scripts/sub_convert.py --input fixtures/end_before_start_captions.txt --to vtt --output smoke_bad.vtt
```

Output (exit 1, file still written):

```
{"input_format": "srt", "output_format": "vtt", "cues_read": 3, "cues_written": 3, "blocks_dropped": 0, "output": "smoke_bad.vtt", "findings": [{"code": "END_BEFORE_START", "cue": 2, "start": "00:00:04.000", "end": "00:00:03.500"}]}
```

## Limits

- Cue positions, line settings, and alignment are dropped in every output. Text that depends on them can read differently.
- HTML entities such as `&amp;` are copied as written and are not decoded.
- Any text between a bare `<` and a later `>` is read as a tag and removed in every output format, so `5 < 6 > 3` loses `< 6 >` in WebVTT, SRT, and plain-text output alike.
- Rolling merge matches lines exactly after tag removal and whitespace trimming. Near-duplicate lines are kept.
- The only timing check is end before start. Overlapping cues, reading speed, and gaps are not reported.
- The script does not check that captions match the audio, that text is accurate, or that a platform will accept the file.
- Visual rendering of the captions in a player is not tested.

## Status

Provisional. Lint-clean, one smoke run. Not independently verified.
