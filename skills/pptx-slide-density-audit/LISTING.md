# pptx-slide-density-audit

## One line

Runs a read-only check on a .pptx deck and lists each slide's word count, bullet-paragraph count, title status and speaker-notes status.

## What it does

The skill gives an agent one stdlib Python script, `scripts/pptx_density.py`, and a fixed report format. The script opens the .pptx as a zip archive, parses each slide's XML and the notes page linked from that slide, and prints one JSON document. For every slide it reports the total word count of its text runs, the number of bullet-candidate paragraphs, whether a title placeholder has text, and whether the notes body has text.

Three flags can fire on a slide: `dense_text` when the word count is above 60, `too_many_bullets` when the bullet count is above 7, and `missing_title` when no title placeholder has text. Those limits are working values chosen for a first pass, and both can be changed on the command line. Missing speaker notes are reported as a count and a column, not as a flag, so they do not change the exit code.

Before parsing, the script refuses inputs that look unsafe or oversized: files above 2 MB, archives with too many entries or an unusually high compression ratio, and any XML that declares a DTD or entities. The script writes no files.

## When to use

Use it when a deck with long slides has to be checked before a talk, a webinar or a client review, and the reviewer wants a per-slide table rather than a general opinion. It also fits a quick pass over a batch of decks where the only question is which slides need trimming, which slides lack a title, and which slides have no notes.

## When not to use

Do not use it to rewrite slide text, to fix formatting, or to judge the quality of an argument. It does not read images, charts, tables or colours, and it does not evaluate layout. It does not handle .ppt, .key or .odp files, and it refuses decks above 2 MB.

## Requirements

Python 3.9 or newer, with the standard library only. No network access, no third-party packages and no Office installation are needed. The input must be a .pptx file that has a `ppt/presentation.xml` entry.

## Example

Smoke run on a three-slide deck built for testing. Slide 1 has a title, three bullets and notes. Slide 2 has no title, nine bullet paragraphs, about 190 words and no notes. Slide 3 has a title and two bullets, with an empty notes body. The command was `python -I scripts/pptx_density.py smoke_deck.pptx`, and the exit code was 1.

```
{
  "tool": "pptx_density",
  "input": "smoke_deck.pptx",
  "thresholds": {
    "max_words": 60,
    "max_bullets": 7
  },
  "slide_count": 3,
  "slides": [
    {
      "slide": 1,
      "words": 14,
      "bullets": 3,
      "title_present": true,
      "notes_present": true,
      "flags": []
    },
    {
      "slide": 2,
      "words": 190,
      "bullets": 10,
      "title_present": false,
      "notes_present": false,
      "flags": [
        "dense_text",
        "too_many_bullets",
        "missing_title"
      ]
    },
    {
      "slide": 3,
      "words": 8,
      "bullets": 2,
      "title_present": true,
      "notes_present": false,
      "flags": []
    }
  ],
  "findings_count": 3,
  "summary": {
    "slides_flagged": 1,
    "slides_without_notes": 2
  }
}
```

## Limits

- Slide numbers follow the file names inside the archive, not the order shown in PowerPoint.
- A bullet is a counting rule: any non-blank paragraph outside the title that is not marked as having no bullet. Plain text-box paragraphs are counted too.
- Word counts split on whitespace, so unspaced scripts are undercounted.
- Tables, charts, images and field text (slide numbers, dates) are not counted.
- The 2 MB, 300-entry and 200-slide caps are working values, not format limits.
- Speaker notes are checked through the notes placeholder only.

## Status

Provisional. Lint-clean, one smoke run. Not independently verified.
