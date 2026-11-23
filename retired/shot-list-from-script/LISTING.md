# shot-list-from-script

## One line

Turns a finished narration or video script into a numbered shot table with per-shot timing at 150 words per minute, a visual class, on-screen text, asset sourcing and transitions.

## What it does

The skill gives an agent a fixed procedure for the step between a written script and the shoot. Each script sentence becomes one shot. Sentences of 1 to 4 words are merged with a neighbour, and sentences over 25 words are split at a comma or a conjunction. The duration of a shot is its word count times 0.4 seconds, so the duration column adds up to the narration length exactly, with one decimal place and no rounding error to hide.

Every shot receives one of four classes: B-ROLL for something a camera can record, TEXT CARD for a fact or instruction that needs no image, SCREEN REC for software or code on a screen, and TO-SOURCE when none of those fits. Anything the script does not describe is marked TO-SOURCE rather than invented, so the asset list is the plain shopping list for the shoot. The output is a markdown table with a fixed column order, an asset list, and a check block that states whether the sums match and which working values were used.

## When to use

Use it when a finished script exists and no shot plan has been written yet. Typical cases are a short explainer built in code-driven tooling, a voice-over that must fit a target length, or a planner who needs to know how many assets to capture before a shoot day.

## When not to use

Do not use it to write the script, to cut or render a video, to draw storyboards, or to choose stock footage. It does not handle non-English narration, because the 150 words-per-minute rate is an English working value. Scripts over 3,000 words should be split into parts first.

## Requirements

A text-capable agent. The package contains no scripts, installs nothing, and makes no network calls.

## Example

Excerpt from a 120-word smoke run on a kettle descaling script (full table in VERIFICATION.md):

| Shot | Script line | Duration (s) | Class | Visual | On-screen text | Asset | Transition |
|---|---|---|---|---|---|---|---|
| 1 | Hard water leaves chalky scale inside your kettle. | 3.2 | B-ROLL | Close-up of chalky scale inside the kettle. | Hard water leaves chalky scale | TO-SOURCE: close-up of scaled kettle interior | Fade in 1.0 s |
| 2 | Over time it slows the heating and can taste bitter. | 4.0 | TEXT CARD | Text card on a plain background. | Scale slows heating, can taste bitter | none (generated) | Cut |
| 3 | Descaling takes about twenty minutes and needs only two household items. | 4.4 | TEXT CARD | Text card listing the time and the two items. | About twenty minutes, two household items | none (generated) | Cut |

## Limits

- The 150 words-per-minute rate, the 2-second minimum and the 10-second maximum are working values, not published standards.
- The visual class is a judgement made from the line text. A writer should confirm the class of any line that could be either B-ROLL or TEXT CARD.
- Timing is planned from word counts. The skill does not measure recorded audio, and a slow or fast reading will shift the real length.
- The procedure assumes one sentence per shot before merging and splitting, and it does not handle speaker labels or music cues.

## Status

Provisional. Lint-clean, one smoke run. Not independently verified.
