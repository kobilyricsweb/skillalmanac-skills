# speaker-notes-timing-planner

## One line

Estimates speaking time for each slide from a notes file, checks the talk against its slot, and lists exact word cuts when it runs long.

## What it does

The skill reads a plain text or Markdown file in which slides are separated by lines containing only three hyphens. For each slide it counts words, converts the count to seconds at a stated pace (130 words per minute by default), and adds a fixed transition allowance per slide (5 seconds by default). It totals the result against the slot length you give and reports whether the talk fits. When the talk runs over, it proposes word cuts from the longest slides first, capping any single slide at half of its words, and reports any words it could not place.

The arithmetic runs in a bundled Python script that uses only the standard library. The script never touches the network and writes nothing to disk; its output is one JSON object. The agent reads that object and writes a short report with a timing table, a cuts list, the decision that applied, and the assumptions used.

## When to use

Use it when a talk must fit a fixed slot, when a speaker wants a per-slide time budget written against their own notes, or when a deck already runs over and needs specific, named cuts rather than general advice to "tighten up". It is also useful for comparing two drafts of the same talk, since the script gives the same numbers for the same input and pace.

## When not to use

Do not use it to rewrite or improve the wording of slides. The skill reports cuts by word count and does not choose which sentences to keep. It cannot time a live rehearsal, because pauses, questions, and applause are not in the notes. It cannot measure audio or video, and it has no view of the slides themselves, only the speaker notes.

## Requirements

Python 3.9 or later. No third-party packages and no network access. The notes file must be UTF-8 text and no larger than 2 MB, with no more than 500 slides.

## Example

Run against the bundled eight-slide fixture with a 10-minute slot, default pace and transition. The output below is pasted verbatim from the smoke run; the exit code was 1 because the talk overruns the slot.

```
{
  "source": "fixtures/sample_talk_8_slides.md",
  "assumptions": {
    "wpm": 130,
    "transition_seconds": 5.0,
    "flag_share_percent": 25.0,
    "cut_cap_percent_of_slide": 50
  },
  "slot_minutes": 10.0,
  "talk_seconds": 721.7,
  "talk_minutes": 12.03,
  "over_seconds": 121.7,
  "fits": false,
  "slides": [
    {
      "slide": 1,
      "words": 320,
      "speaking_seconds": 147.7,
      "slide_seconds": 152.7,
      "share_percent": 21.2,
      "flagged": false
    },
    {
      "slide": 2,
      "words": 282,
      "speaking_seconds": 130.2,
      "slide_seconds": 135.2,
      "share_percent": 18.7,
      "flagged": false
    },
    {
      "slide": 3,
      "words": 201,
      "speaking_seconds": 92.8,
      "slide_seconds": 97.8,
      "share_percent": 13.5,
      "flagged": false
    },
    {
      "slide": 4,
      "words": 141,
      "speaking_seconds": 65.1,
      "slide_seconds": 70.1,
      "share_percent": 9.7,
      "flagged": false
    },
    {
      "slide": 5,
      "words": 147,
      "speaking_seconds": 67.8,
      "slide_seconds": 72.8,
      "share_percent": 10.1,
      "flagged": false
    },
    {
      "slide": 6,
      "words": 130,
      "speaking_seconds": 60.0,
      "slide_seconds": 65.0,
      "share_percent": 9.0,
      "flagged": false
    },
    {
      "slide": 7,
      "words": 111,
      "speaking_seconds": 51.2,
      "slide_seconds": 56.2,
      "share_percent": 7.8,
      "flagged": false
    },
    {
      "slide": 8,
      "words": 145,
      "speaking_seconds": 66.9,
      "slide_seconds": 71.9,
      "share_percent": 10.0,
      "flagged": false
    }
  ],
  "cuts": [
    {
      "slide": 1,
      "cut_words": 160,
      "seconds_saved": 73.8
    },
    {
      "slide": 2,
      "cut_words": 104,
      "seconds_saved": 48.0
    }
  ],
  "unfixed_words": 0
}
```

Reading the output: the talk is 12.03 minutes against a 10-minute slot, so 121.7 seconds must go. The two cuts together remove 264 words, which covers the 260 words needed at 130 words per minute. Neither slide is flagged, because no slide holds more than 25 percent of the talk.

## Limits

The pace is a working value, not a measured speaker rate. A person who speaks faster or slower gets a different result unless they pass their own pace. The model of time is words only: it does not count pauses, slide transitions beyond the flat allowance, demonstrations, or questions from the audience. Word counts treat every whitespace-separated token with a letter or digit as one word, so numbers, abbreviations, and code snippets are counted the same way as prose. The flag for a slide holding more than 25 percent of the talk is advisory and does not change the exit code.

## Status

Provisional. Lint-clean, one smoke run. Not independently verified.
