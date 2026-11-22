# slide-speaker-notes-writer

## One line

Writes 2 to 4 sentence speaker notes for each slide, using only the text printed on that slide, and checks every number in the notes against its slide.

## What it does

The skill takes the text of a deck, slide by slide, and produces a note for each slide. Each sentence in a content note must restate a line that is printed on that slide. The opening sentence names the slide title, and the last sentence hands off to the next slide. The final slide closes instead of handing off.

Each note is held to a word count and a sentence count. Any sentence with no matching slide line is removed rather than kept. A number check then compares every figure on a slide with the note for that slide. A figure missing from the note is flagged MISSING-NUMBER. A figure or number word that the slide does not contain is flagged NEW-NUMBER.

Title-only and image-only slides cannot support a full note, so the skill drafts one or two sentences from the title alone and lists those slides under TO-ADD. The author supplies the context those slides lack.

## When to use

Use it when a presenter has a slide deck with no notes and wants a first draft that stays faithful to the slides. It suits internal reviews, status decks and short talks, where the speaker needs a reminder of each point and a check that the figures read the same aloud as on screen.

## When not to use

Do not use it to write new slide content, to add statistics, quotes or sources that the slides do not show, or to produce a full talk script with stories and examples. It does not rewrite notes the presenter already wrote, and it does not judge whether the slides are accurate.

## Requirements

A text-capable agent and the slide text pasted into the conversation, one block per slide in deck order. No files, tools or network access are needed. The audience is optional.

## Example

Input: a six-slide deck, pasted as plain text in this form:

```text
Slide 1, title: Q3 Support Review. No body.
Slide 2, title: What we measured. Body: Ticket volume / Reply time / Customer ratings
Slide 3, title: Ticket volume fell. Body: Tickets dropped 18% from Q2 to Q3.
Slide 4, title: Our support team. Body: [image]
Slide 5, title: Reply time. Body: Median first reply: 4 hours
Slide 6, title: Next steps. Body: Staff the weekend queue / Publish a refund policy
```

Slide 1 is a title only. Slide 4 is an image. Slides 3 and 5 each carry one number. The output below was revised to follow SKILL.md on that input, and every count in it was recounted by hand.

```markdown
## Status

complete

## Slide inventory

| Slide | Type | Slide point | Numbers on slide |
|---|---|---|---|
| 1 | title | Q3 Support Review | None |
| 2 | content | What we measured | None |
| 3 | content | Ticket volume fell | 18% |
| 4 | image | Our support team | None |
| 5 | content | Reply time | 4 |
| 6 | content | Next steps | None |

## Speaker notes

### Slide 1

This is the Q3 Support Review.

Words: 6 | Sentences: 1

### Slide 2

This slide covers what we measured: ticket volume, reply time, and customer ratings. Next up: Ticket volume fell.

Words: 18 | Sentences: 2

### Slide 3

This slide shows that ticket volume fell. Tickets dropped 18% from Q2 to Q3. Next up: Our support team.

Words: 19 | Sentences: 3

### Slide 4

This slide introduces our support team.

Words: 6 | Sentences: 1

### Slide 5

This slide reports reply time. The median first reply takes 4 hours. Next up: Next steps.

Words: 16 | Sentences: 3

### Slide 6

This slide lists our next steps. Our next steps are to staff the weekend queue and publish a refund policy.

Words: 20 | Sentences: 2

## Number check

| Slide | Number | In notes | Result |
|---|---|---|---|
| 3 | 18% | 18% | PASS |
| 5 | 4 | 4 | PASS |

No NEW-NUMBER rows. No number words appear in any note.

## TO-ADD

| Slide | Type | What the author adds |
|---|---|---|
| 1 | title | Why this review is happening and who it is for |
| 4 | image | What the photo shows and who appears in it |

## Open questions

None
```

## Limits

The skill checks only what it can match mechanically: sentence count, word count, number tokens and whether a note opens with the slide title. It cannot confirm that a restated claim is true, that the wording suits the speaker's voice, or that the speaking time fits the slot. Number matching covers digit tokens and a short list of number words. It does not match figures written as words in other forms, dates, or units inside labels such as Q2. The rules are working values chosen for this skill, not a published standard.

## Status

Provisional. Lint-clean, one smoke run. Not independently verified.
