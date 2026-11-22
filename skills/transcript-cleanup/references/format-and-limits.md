## Contents

- File formats the script reads
- Where the subtitle limits come from
- Choosing a convention
- Sources

## File formats the script reads

SRT: blocks separated by a blank line. Each block is an optional numeric id, a line `hh:mm:ss,mmm --> hh:mm:ss,mmm`, then one or more text lines. The comma before the milliseconds is the SRT habit; the reader also accepts a dot. There is no formal standard for SRT, so files in the wild vary; a block with no timing line is skipped with a warning.

WebVTT: a file that starts with `WEBVTT`, then blocks. A cue may have an identifier line, then `hh:mm:ss.mmm --> hh:mm:ss.mmm` followed by optional settings such as `align:start`; the hours part may be left out in the input. Text may carry tags: `<v Name>` marks the speaker, `<i>` italics. NOTE, STYLE and REGION blocks are not cues; the script drops them and says so.

Plain text: one segment per non-empty line. A line may begin with a timestamp in brackets, in parentheses, or bare (`[00:01:05]`, `(1:05)`, `00:01:05 -`). A timestamp alone on a line (the style some video sites copy out) is attached to the next line. A blank line is treated as a paragraph break, so the lines on either side are never merged. Timestamps are kept as written.

## Where the subtitle limits come from

| Limit | Value used | Reason |
|---|---|---|
| Characters per line | 42 | Common ceiling in broadcast and streaming style guides for Latin scripts; some broadcasters use 37 |
| Lines per cue | 2 | A third line covers too much of the picture |
| Reading speed | 21 characters per second flagged; 17 is the usual target for children's content | Adult guides sit around 17 to 20; the script flags the upper end so only clear problems appear |
| Cue duration | 1.0 s minimum, 7.0 s maximum | Shorter cues flash; longer ones feel stuck. Some guides allow about 0.83 s as the minimum |
| Gap between cues | 80 ms minimum | About two frames at 24 to 25 frames per second |

These are working values taken from public style guides as the author recalls them; they were not re-fetched when this skill was written. If a client names a different guide (a broadcaster, a platform), use their numbers and say so in the report; the script's constants sit at the top of `scripts/clean_transcript.py` for a reader, but do not change them to make a file pass.

The script counts visible characters: spaces count, line breaks and VTT tags do not.

## Choosing a convention

- Captions for a platform upload: use the platform's own limit if it publishes one.
- Subtitles in a non-Latin script: the per-line character limit is often lower; confirm with the client.
- Transcript only (no timing needed): use plain output; none of the limits apply.

## Sources

- Netflix Timed Text Style Guide (English): https://partnerhelp.netflixstudios.com/hc/en-us/articles/217350977-English-Timed-Text-Style-Guide
- W3C WebVTT specification: https://www.w3.org/TR/webvtt1/
- BBC Subtitle Guidelines: https://bbc.github.io/subtitle-guidelines/
