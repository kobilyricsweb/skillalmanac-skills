---
name: slide-speaker-notes-writer
description: Writes short speaker notes for each slide in a deck, restating only the text printed on that slide. Use when slides arrive without notes and the presenter needs 2 to 4 sentence notes per slide, a check that every number in the notes matches a slide figure, and a list of title or image slides that still need content from the author. Do not use for writing new slide text, adding statistics, quotes or sources, drafting a full talk script, or rewriting an existing set of notes.
license: Apache-2.0
compatibility: None beyond a text-capable agent (type B).
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  author_model: claude-haiku-5-5
  version: "0.1.0"
  network: none
---

# Slide speaker notes writer

Turns the printed text of each slide into speaker notes. Every sentence in a note must match a line of slide text. Numbers are checked one by one against the slide they came from.

## Inputs

Required: the text of every slide, in deck order, one block per slide. Each block holds the slide title line and any body lines. Slides with no title may be numbered by position.

Optional: the audience. If it is missing, write neutral notes and do not ask for it.

## Workflow

1. Intake. Number the slides from 1 in the order given. Count the slides with any text. Output: the slide count, and a note of any renumbering for Open questions.
2. Classify each slide with Table 1. Output: a Type value for each slide.
3. Record the slide point (the title, verbatim) and every number on the slide (Table 2). Output: the Slide point and Numbers on slide columns.
4. Draft notes. Content slides get a full note under Table 3. Title and image slides get a draft of 1 or 2 sentences that restates the title only. Output: one note per slide.
5. Test each note against Table 3. Count sentences and words. Delete any sentence that has no matching slide line, then recount. Output: a Words and Sentences line under each note.
6. Run the number check (Table 4). Output: one row per number on a slide, and one row per number found in a note that is not on that slide.
7. Build the TO-ADD list for every title or image slide. Output: one row per slide.
8. Set the Status (Table 5) and list Open questions. Output: the Status line and a numbered question list, or None.

### Table 1: Slide type (working values)

| Type | Rule | Handling |
|---|---|---|
| image | Body is empty except a single line "[image]" | Draft 1 or 2 sentences, add to TO-ADD |
| title | No body text at all, title line only | Draft 1 or 2 sentences, add to TO-ADD |
| content | Any other slide with body text | Full note under Table 3 |

Test image first, then title, then content.

### Table 2: Number rules (working values)

| Item | Rule |
|---|---|
| Number | A whitespace-separated token made only of digits, with optional comma thousands separators, a decimal point or a trailing percent sign. Examples: 4, 1,200, 2.5, 18% |
| Not a number | A digit run attached to letters, such as Q2 or 3D. These are labels, so they are not checked |
| Number word | one through twelve, dozen, hundred, thousand, million, half. A number word in a note counts as a number |

### Table 3: Note rules (working values, content slides only)

| Check | Value | If breached |
|---|---|---|
| Sentences | 2 to 4 | Merge or split sentences |
| Words | 60 maximum, counted as whitespace-separated tokens | Cut words |
| Opening sentence | Names the slide title in the first sentence | Rewrite the opening |
| Transition | Last sentence names the title of the next slide. The final slide ends with a closing sentence and no transition | Rewrite the last sentence |
| New numbers | No number or number word that is absent from that slide | Delete the figure |
| New claims | Every other sentence restates a line of slide text | Delete the sentence |

### Table 4: Number check result codes

| Result | Meaning | Action |
|---|---|---|
| PASS | Number on the slide appears in that slide's note | None |
| MISSING-NUMBER | Number on the slide does not appear in that slide's note | Add it to the note |
| NEW-NUMBER | Number or number word in a note is not on that slide | Delete it from the note |

### Table 5: Status values

| Status | When |
|---|---|
| complete | Every slide has a note, every number check is PASS, and every title or image slide is in TO-ADD |
| partial | Some slides had no text, or one clause of the request was refused. Everything else is delivered |
| stopped | No slide has any text. Return only the numbered question list |

## Output contract

Return these sections in this order, using these exact headings:

1. `## Status`: one line, one value from Table 5.
2. `## Slide inventory`: table with columns Slide | Type | Slide point | Numbers on slide. One row per slide. Use None when a slide has no number.
3. `## Speaker notes`: one block per slide, headed `### Slide <n>`, then the note text, then a line `Words: <n> | Sentences: <n>`.
4. `## Number check`: table with columns Slide | Number | In notes | Result. Result is one of the codes in Table 4. Write `No numbers on slides or in notes.` when the table would be empty.
5. `## TO-ADD`: table with columns Slide | Type | What the author adds. One row per title or image slide. Write None when there are none.
6. `## Open questions`: numbered list. Write None when there are none.

When the status is stopped, return only `## Status` and `## Open questions`.

## Refuse / stop when

- No slide has any text. Set Status to stopped and ask numbered questions: what each slide shows, and whether the deck has any text at all.
- The request asks for a statistic, a quote, a source, a name or a date that is not printed on the slide. Refuse that clause only. Keep the rest of the notes, set Status to partial, and list the refused item under Open questions.
- A note sentence cannot be matched to a slide line. Delete the sentence. Do not keep it to reach the sentence minimum.
- A title or image slide would need invented content to reach 2 sentences. Keep the draft at the length the title allows and put the gap in TO-ADD.
- Slides are numbered out of order or a number is missing. Renumber by position and record the change under Open questions.

## Files

- [SKILL.md](SKILL.md): this procedure and its output contract.
- [LICENSE.txt](LICENSE.txt): Apache License 2.0 text for this skill.
