# subtitle-srt-fixer

## One line

Checks an SRT subtitle file for timing and layout problems and, on request, writes a repaired copy with sorted, trimmed and renumbered cues.

## What it does

The skill runs a single Python script, `scripts/srt_check.py`, against one SRT file. The script reads the file as UTF-8 with an optional byte order mark, accepts CRLF or LF line endings, and splits it into cue blocks. Each cue is then tested against eight working limits: start times out of order, a cue that starts before an earlier cue ends, zero or negative duration, a duration under 1 second or over 7 seconds, reading speed above 20 characters per second, a line over 42 characters, and more than two lines per cue. The result is a JSON report with one entry per problem, keyed by cue number.

With the fix option, the script writes a second file to a new path. It sorts cues by start time, trims any cue whose end runs past the next cue's start, and renumbers the cues from 1. It does not change caption text and does not fix speed, length or duration problems. Those are listed as remaining issues so a person can decide what to do with them.

## When to use

Use it when a subtitle file has overlapping cues, when cues in a Remotion or video-editor project flash by too quickly, or when a file must pass a fixed layout check before import. It also suits a quick audit of several SRT files, since the report is structured and the exit code tells a script whether any issue was found.

## When not to use

Do not use it to translate captions, rewrite wording, shorten text for reading speed, burn subtitles into video, or convert between VTT, ASS and SRT. It checks timing and layout only. It cannot tell whether a caption matches the audio.

## Requirements

Python 3.9 or newer. No third-party packages. No network access. The script is run with the isolated flag, for example `python -I scripts/srt_check.py INPUT.srt`. Input must be under 2 MB and valid UTF-8.

## Example

Smoke run on the bundled six-cue sample, with the check only:

```
{
  "input": "fixtures\\six_cues.txt",
  "block_count": 6,
  "cue_count": 6,
  "issue_count": 4,
  "issues": [
    {
      "cue": 2,
      "code": "overlap",
      "detail": "starts 00:00:03,500, before cue 1 ends 00:00:04,000"
    },
    {
      "cue": 3,
      "code": "too_fast",
      "detail": "30.0 characters per second, maximum 20.0"
    },
    {
      "cue": 5,
      "code": "too_short",
      "detail": "0.500 s, minimum 1.000 s"
    },
    {
      "cue": 6,
      "code": "too_long",
      "detail": "8.500 s, maximum 7.000 s"
    }
  ],
  "fix": null
}
```

## Limits

The thresholds are working values set for this skill and are not published standards. The script only reads SRT. It does not handle VTT or ASS, styling tags, positioning codes or cues that use formatting markup. A block with no timing line stops the repair step, so a damaged file must be corrected by hand first. The repair trims overlaps but does not reflow text, so a trimmed cue can end up too short or too fast, and the report will say so.

## Status

Provisional. Lint-clean, one smoke run. Not independently verified.
