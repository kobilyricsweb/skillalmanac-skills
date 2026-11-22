# Voice Profile Extractor

## One line
Builds a ten-line voice profile from three or more of your own writing samples, using hand-counted style markers and fixed bands.

## What it does
Takes the user's own samples (at least three, and at least 600 words in total after cleaning), removes quoted and pasted material, and counts sentences, paragraphs, contractions, first and second person, questions, exclamations and favorite connectors. The counts become rates per 100 words or per 100 sentences, and each rate receives a band such as short, medium or long. A stability check compares the samples with each other and flags any rate whose spread is too wide to trust. The output is ten profile lines: four measured facts, then six do and avoid rules tied to the measured numbers. A before and after pair follows, and the after text is measured against the same bands it was written to meet. If the samples do not share one voice (more than three rates flagged unstable, or fewer than three usable metrics), the output stops at the four measured lines, marks the unstable rates, and asks whether the samples share one voice. Every table lists the raw counts, so the user can check any figure and correct it.

## When to use
Use it when the user wants drafts that sound like them and can supply three or more pieces they wrote themselves. It also suits an editor who needs a short, measured record of how one writer builds sentences and paragraphs before a handover to a new contributor.

## When not to use
Do not use it to imitate a named author, a living writer or any third party. Do not use it to grade writing quality, to decide whether text was written by a machine, or to draft anything when no samples exist. Pasted or quoted material is not the user's voice, so the skill removes it and flags the removal.

## Requirements
A text-capable agent. There are no scripts, no network calls and no extra files beyond the skill text and the license. The user pastes the samples in chat, in any order, and confirms that they wrote each one. The skill labels them S1, S2 and S3 in the order received.

## Example
```text
## Status
partial

## Intake
| Sample | Words | Sentences | Paragraphs |
|--------|-------|-----------|------------|
| S1 | 222 | 26 | 6 |
| S2 | 215 | 22 | 6 |
| S3 | 226 | 25 | 5 |

## Measurements
| Metric | S1 | S2 | S3 | Combined |
|--------|----|----|----|----------|
| Words per sentence | 8.5 | 9.8 | 9.0 | 9.1 |
| Sentences per paragraph | 4.3 | 3.7 | 5.0 | 4.3 |
| Contractions per 100 words | 2.7 | 0.0 | 0.4 | 1.1 |
| First person per 100 words | 8.6 | 8.8 | 8.0 | 8.4 |
| Second person per 100 words | 1.8 | 0.5 | 0.9 | 1.1 |
| Questions per 100 sentences | 4 | 0 | 4 | 3 |
| Exclamations per 100 sentences | 4 | 0 | 0 | 1 |

### Connectors
| Connector | S1 | S2 | S3 | Total |
|-----------|----|----|----|-------|
| and | 8 | 6 | 7 | 21 |
| so | 2 | 2 | 1 | 5 |
| but | 1 | 2 | 1 | 4 |
| still | 2 | 1 | 1 | 4 |
| also | 0 | 1 | 1 | 2 |

## Voice profile
1. Sentence length: short (9.1 words per sentence).
2. Paragraph length: medium (4.3 sentences per paragraph).
3. Contractions: mixed (1.1 per 100 words) [UNSTABLE]; first person high (8.4 per 100 words); second person medium (1.1 per 100 words) [UNSTABLE].
4. Questions: rare (3 per 100 sentences) [UNSTABLE]; exclamations: rare (1 per 100 sentences) [UNSTABLE]; top connectors: and, so, but.

## Flags
UNSTABLE: contractions per 100 words; second person per 100 words; questions per 100 sentences; exclamations per 100 sentences.

Do these samples share one voice?
```

## Limits
Counts are done by hand, so each one may be off by one. The output lists every count so the user can correct a figure and redo the bands. All bands and the 0.50 spread value are working values, not published specifications. Short samples produce unstable rates, as the example shows, and the flags are there to stop the profile from overstating a number. The profile describes the style of the samples given. It does not represent the user's full range, and it does not judge whether the writing is good.

## Status
Provisional. Lint-clean, one smoke run. Not independently verified.
