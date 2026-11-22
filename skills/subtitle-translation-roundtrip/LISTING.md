# Subtitle translation roundtrip

## One line

Extracts the text of an SRT subtitle file for translation, then rebuilds the SRT on its original timings and refuses to write it when the translated cues break the cue count, numbering, or layout limits.

## What it does

The skill ships one Python script with two commands. The extract command reads an SRT file, drops the timing lines, and writes a numbered JSON file that holds only the cue text. The agent translates the text values in that JSON, keeping every cue number and the cue order. The rebuild command reads the original SRT and the translated JSON together. It checks that the cue count matches, that each cue carries the right number, that no cue is empty, that no text contains a blank line, that no cue has more than two lines or a line longer than 42 characters, and that the reading speed stays at or below 21 characters per second. The 42, 2 and 21 limits are working values, not a published standard. If any check fails, the script prints each finding with its cue number and writes nothing. If every check passes, it writes a new SRT with the original timing lines and the translated text. The script never overwrites a file and never writes over an input.

## When to use

Use it when a user wants subtitles, captions, or an SRT file translated into another language and needs every cue and its timing kept. The input file must be under the 2 MB cap and must be UTF-8 text.

## When not to use

Do not use it for burned-in text inside video frames, for transcribing speech, for changing cue timings, or for VTT and ASS files. It does not judge whether a translation is accurate, natural, or in the right dialect, and it does not check whether the subtitle matches what is said on screen.

## Requirements

Python 3.9 or later, standard library only. No network access and no subprocess calls. A text-capable agent is needed to write the translation between the two commands.

## Example

Rebuild the shipped sample with a translation that has one 54-character line in cue 4. Run from the skill folder. The output path was not created, so nothing was written:

```
python -I scripts/srt_translate.py rebuild fixtures/source.txt fixtures/translated_planted.json out_planted.srt
```

```
{
  "status": "findings",
  "cue_count_original": 6,
  "cue_count_translated": 6,
  "findings": [
    {
      "cue": 4,
      "code": "LINE_TOO_LONG",
      "detail": "line 1 has 54 characters, limit 42"
    }
  ]
}
```

## Limits

The script does not verify meaning, grammar, names, tone, dialect, or sync with speech. Reading speed counts characters rather than words or syllables, and line length counts characters rather than rendered width. It does not know the target language, does not render video, and does not play the subtitles against the picture. A clean rebuild means the file is structurally sound, not that the translation is good.

## Status

Provisional. Lint-clean, one smoke run. Not independently verified.
