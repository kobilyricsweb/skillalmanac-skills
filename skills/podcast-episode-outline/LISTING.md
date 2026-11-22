# podcast-episode-outline

## One line

Turns a planned podcast episode into a timed outline with fixed blocks, segments, clip markers and a show-notes template.

## What it does

The skill takes a short intake (topic, solo or guest format, length in minutes, audience) and returns one outline. The timing budget is built from a fixed rule: cold open, intro and close take two minutes each for episodes longer than 15 minutes, and the remaining minutes are split evenly across the segments. The segment count comes from a length table, so a 30-minute episode gets three segments and a 50-minute episode gets four. The outline checks its own arithmetic before returning, so the minutes in the budget add up to the stated length.

For guest episodes the skill adds a question ladder with fixed stage counts: two warm-up questions, three or four depth questions, one surprise question and one closing question. Clip-worthy moments are marked with a minute, a segment, a beat and a clip length, and the show-notes template leaves every timestamp as a placeholder until the episode has been recorded.

## When to use

Use it before recording when the episode needs a fixed length, when earlier episodes have run long, or when a host wants the show notes prepared alongside the outline. It fits solo episodes on a single subject and guest episodes where the host has the guest's role and the main talking points.

## When not to use

Do not use it for a word-for-word script, for ad copy, for editing recorded audio, or for any episode longer than 90 minutes, which the skill asks to split. It does not supply facts, quotes or credentials. Where the host has not provided one, the outline holds a visible placeholder.

## Requirements

A text-capable agent. No scripts, no network access and no files other than the outline itself.

## Example

Excerpt from the smoke run (30-minute solo episode on composting), produced by following this skill's own SKILL.md:

```
## Timing budget
| Block | Start (minute) | End (minute) | Minutes |
|---|---|---|---|
| Cold open | 0 | 2 | 2 |
| Intro | 2 | 4 | 2 |
| Segment 1 | 4 | 12 | 8 |
| Segment 2 | 12 | 20 | 8 |
| Segment 3 | 20 | 28 | 8 |
| Close | 28 | 30 | 2 |
```

## Limits

- The timing values are working values for planning. They are not measured speaking rates, and a fast or slow speaker will need to adjust segment minutes by hand.
- Clip counts follow a one-per-ten-minutes rule that the host can change, but the change must be written into the outline.
- The skill does not transcribe, time or edit recorded audio, and it cannot check whether a fact the host supplies is correct.
- Only one smoke run has been made.

## Status

Provisional. Lint-clean, one smoke run. Not independently verified.
