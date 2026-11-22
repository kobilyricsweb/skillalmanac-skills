---
name: podcast-episode-outline
description: Outlines a podcast episode before recording. Use when a host needs a timed structure for a solo or guest episode, when episodes keep running past their planned length, or when show notes must be prepared. Writes the intake, cold open, segments, timing budget that sums to the episode length, interview question ladder, clip-worthy markers and a show-notes template. Do not use for word-for-word scripts, ad copy, audio editing, or inventing guest credentials or quotes.
license: Apache-2.0
compatibility: None beyond a text-capable agent (type B), with no scripts, no network and no files beyond the written outline.
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  author_model: claude-haiku-5-5
  version: "0.1.0"
  network: none
---

# Podcast episode outline

Produce one outline for one episode. The outline is a plan the host reads aloud from or follows loosely. It is not a transcript.

## Workflow

1. Intake. Collect these fields and write them into the `## Intake` block of the output. Required: topic (one sentence), format (`solo` or `guest`), length in whole minutes, audience (one phrase). Optional: guest name and role (only as the user typed it), recording date.
   - If length is missing, ask once and stop until it is given.
   - If length is above 90, stop and suggest splitting the episode into two parts. Do not build a 90+ minute outline.
   - If format is `guest` and no guest role is given, write `guest role: [MISSING]` and continue.
2. Choose the segment count from the length. Use the table below. Do not choose a count by feel.

| Length (minutes) | Format | Segments | Structure |
|---|---|---|---|
| 5 to 15 | solo or guest | 2 | cold open, intro, 2 segments, close |
| 16 to 45 | solo or guest | 3 | cold open, intro, 3 segments, close |
| 46 to 90 | solo or guest | 4 | cold open, intro, 4 segments, close |
| 91 and above | any | none | refuse, see Refuse / stop when |

3. Build the timing budget. Fixed blocks: cold open 2 minutes, intro 2 minutes, close 2 minutes (for lengths 5 to 15, use cold open 1, intro 1, close 1). Segments share the rest: segment minutes = (length minus the fixed blocks) divided by the segment count, rounded down. Any remainder goes to the last segment. The minutes must sum to the length exactly.

   Worked values for the 30-minute solo case: fixed blocks 2 + 2 + 2 = 6, remaining 24, three segments of 8 each.

| Block | Start (minute) | End (minute) | Minutes |
|---|---|---|---|
| Cold open | 0 | 2 | 2 |
| Intro | 2 | 4 | 2 |
| Segment 1 | 4 | 12 | 8 |
| Segment 2 | 12 | 20 | 8 |
| Segment 3 | 20 | 28 | 8 |
| Close | 28 | 30 | 2 |

   Check: the last End equals the length and the Minutes column sums to the length. If not, fix the table before writing anything else.

4. Write the cold open. One paragraph, spoken length 30 to 60 seconds (working value), with the rest of the cold open block used for a tease of segment 1. It states the episode's single most surprising fact or claim from the topic. Do not invent a fact. If the host has not supplied one, write `[HOST TO SUPPLY FACT]`.
5. Write each segment. For each segment, write:
   - title (4 words or fewer)
   - purpose (one sentence that starts with the word "Answer" or "Show")
   - 2 to 4 beats, each a short phrase, not a full sentence
   - one clip marker reference, if the segment has a clip moment (see step 8)
6. For `guest` format only, write the question ladder. Use the stage counts below. Total questions: 7 to 8 (2 warm-up + 3 or 4 depth + 1 surprise + 1 close).

| Stage | Count | Rule |
|---|---|---|
| Warm-up | 2 | Factual and easy, about the guest's path to the topic |
| Depth | 3 to 4 | Open "how" or "why" questions, one per segment |
| Surprise | 1 | A question that asks for a counterexample or a mistake |
| Close | 1 | "What should listeners do or check next" |

   Every question must be open-ended. Do not write any question that presumes a fact about the guest that the host has not supplied.

7. Write the close: one line for the thank-you, one line for the call to action the host has supplied. If none is supplied, write `[HOST TO SUPPLY CTA]`.
8. Mark clip-worthy moments. A moment qualifies when it is a concrete claim, a number, or a clear opinion that can be stated in 30 seconds or less. Target one clip per 10 minutes of length (working value), so 3 clips for a 30-minute episode. Each marker gives the minute, the segment, the beat it comes from, and a clip length in seconds between 15 and 60.
9. Write the show-notes template. Timestamps stay as `[fill after recording]` in the outline. Never estimate a real timestamp before the episode is recorded. The template has one line per segment and one line per clip marker, each with a `HH:MM:SS` placeholder.
10. Read the outline back once against the checks in the Output contract section. Fix any failing check before returning it.

## Output contract

Return exactly these headings in this order, with nothing before the first heading except the title line.

```
# Episode outline: [title]

## Intake
- topic:
- format:
- length minutes:
- audience:
- guest name and role: (guest only, otherwise omit)
- recording date: (optional)

## Timing budget
| Block | Start (minute) | End (minute) | Minutes |

## Cold open
(one paragraph)

## Segments
### 1. [title]
- purpose:
- beats:
- clip: (marker id or none)

(repeat for each segment)

## Question ladder (guest only)
| Stage | Question |

## Close
- thank-you:
- call to action:

## Clip markers
| Id | Minute | Segment | Beat | Clip length (seconds) |

## Show notes template
- [HH:MM:SS] segment title, one line per segment
- [HH:MM:SS] clip id, one line per clip marker

Total: [length] minutes
```

Checks before returning:
- The Timing budget minutes sum to the Intake length.
- Segment count equals the count in the step 2 table.
- Clip count equals length divided by 10, rounded to the nearest whole number (a value ending in .5 rounds up, so 15 minutes gives 2 clips), with a minimum of 1 and a maximum of 6. A 30-minute episode has 3 clips.
- No placeholder other than `[MISSING]`, `[HOST TO SUPPLY FACT]`, `[HOST TO SUPPLY CTA]`, `[fill after recording]` or `HH:MM:SS` appears.

## Refuse / stop when

- The length is missing (ask once, then stop until given), or above 90 minutes (suggest a split).
- The user asks for a word-for-word script. Return the outline and say that narration is out of scope.
- The user asks for a guest quote, credential, title, or statistic that the user did not supply. Write `[HOST TO SUPPLY ...]` in its place and do not guess. Never invent a guest's credentials or quotes.
- The user asks for real timestamps before recording. Return the placeholders only.
- The topic would need a claim about a named private person. Stop and ask the host to supply the claim with its source.

## Limits

- The timing values are working values for planning, not measured speaking rates.
- Clip marker counts are working values. A host may change them, but the change must be written in the outline.
- The skill does not transcribe, edit or time recorded audio.
