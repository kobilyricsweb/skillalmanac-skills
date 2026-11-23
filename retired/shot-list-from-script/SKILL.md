---
name: shot-list-from-script
description: Turns a finished narration or video script into a numbered shot list with timing at 150 words per minute, visual type, on-screen text, asset sourcing and transitions. Use when a video or code-driven video project has a script but no shot plan, when shot durations must add up to the narration length, or when each shot needs a B-roll, text card or screen recording choice marked TO-SOURCE. Do not use for writing the script, editing video files, storyboard art, or sourcing or generating footage.
license: Apache-2.0
compatibility: None beyond a text-capable agent (type B).
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  author_model: claude-haiku-5-5
  version: "0.1.0"
  network: none
---

# Shot list from script

This procedure turns a finished script into a shot table whose durations add up to the narration length. It is planning output only. It never creates, finds, or describes footage that the script does not mention.

## Constants (working values)

| Name | Value | Note |
|---|---|---|
| Narration rate | 150 words per minute | Working value for English narration. One word = 60 / 150 = 0.4 s. |
| Minimum shot | 2.0 s (5 words) | Working value. Shorter sentences are merged. |
| Maximum shot | 10.0 s (25 words) | Working value. Longer sentences are split. |
| On-screen text | 7 words at most | Working value. |
| Dissolve | 0.5 s | Entry transition for shots that open a new step. |
| Fade | 1.0 s | Fade in on shot 1; fade to black after the last shot. |

None of these values is an industry standard. Use another value only when the writer states one, and print the stated value in the Check block.

Worked check: a 120-word script = 120 x 0.4 = 48.0 s.

## Workflow

Step 1. Validate the input against "Refuse or stop when". Output: the word count of the script.

Step 2. Count words per sentence. Split sentences on period, exclamation mark and question mark. A word is a run of characters between spaces; a hyphenated word and a number each count as one word. Output: a list of sentences with word counts, the total, and the narration length in seconds (total x 0.4, one decimal).

Step 3. Form shots with the segmentation table below. Keep script order. Every sentence appears in exactly one shot, unchanged. Output: shots with their word counts.

Step 4. Assign one class per shot with the decision table below. Output: class column.

Step 5. Write the visual as one sentence naming the object, hand action, or screen shown. Add no object, person, place, or brand that the script does not name. Output: visual column.

Step 6. Write the on-screen text as a phrase of 7 words or fewer, drawn from the script words, or the word "none". Output: on-screen text column.

Step 7. Set the asset. B-ROLL and SCREEN REC: "TO-SOURCE: <what to capture>". TEXT CARD: "none (generated)". TO-SOURCE class: "TO-SOURCE: writer to decide". Output: asset column and the Assets to source list.

Step 8. Set the transition column with this order of rules: shot 1 is "Fade in 1.0 s". A shot whose sentence starts with Start, Next or Finally is "Dissolve 0.5 s". The last shot is "Cut, then fade to black 1.0 s". Every other shot is "Cut". Output: transition column.

Step 9. Run the Check block. Each check is PASS or FAIL. A FAIL is fixed before output; if it cannot be fixed, report it under Flags. Output: Check block.

Step 10. Emit the output contract below. Nothing else goes in the reply.

## Segmentation table

| Sentence length (words) | Action |
|---|---|
| 1 to 4 | Merge with the next sentence. If it is the last sentence, merge with the previous one. Re-check the merged shot against this table. |
| 5 to 25 | One shot. |
| 26 or more | Split once at the first comma, or at the first "and", "but", "so" or "then", that leaves 5 or more words on each side. Split a part again if it is still over 25 words. If no split point exists, stop. |

Merging and splitting move words between shots without changing their total, so the duration sum stays equal to the narration length.

## Visual class decision table

| Line content | Class | Asset cell |
|---|---|---|
| A physical object, place, or hand action a camera can record | B-ROLL | TO-SOURCE: footage to capture |
| A fact, number, time, warning or instruction that needs no image | TEXT CARD | none (generated) |
| Software, a web page, a settings screen, or code shown on a screen | SCREEN REC | TO-SOURCE: screen capture |
| An abstract idea with no visible form | TEXT CARD | none; visual cell reads "text card only" |
| None of the above | TO-SOURCE | TO-SOURCE: writer to decide |

Tie rule: when a line fits both B-ROLL and TEXT CARD, choose B-ROLL only if a viewer must see the object or action to understand the line. Otherwise choose TEXT CARD.

## Output contract

The reply has exactly these parts, in this order.

```
# Shot list: <short title>

Narration: <N> words at 150 wpm = <S> s

## Shot table
| Shot | Script line | Duration (s) | Class | Visual | On-screen text | Asset | Transition |
|---|---|---|---|---|---|---|---|
| 1 | <exact sentence> | <words x 0.4, one decimal> | <class> | <visual> | <text or none> | <asset cell> | <transition> |
| Total | | <S> | | | | | |

## Assets to source
- Shot <n>: <what to capture>

## Check
- Duration sum = narration length: PASS or FAIL
- Shots under 2.0 s: <count, must be 0>
- Shots over 10.0 s: <count, must be 0>
- On-screen text over 7 words: <count, must be 0>
- Every sentence used once, in order: PASS or FAIL
- Working values used: <list, or "defaults">
- Flags: <list, or "none">
```

Rules for the table: a script line containing a pipe character gets the pipe replaced by a slash. Duration has one decimal place. The Total row sums the duration column. The Assets to source list has one line per B-ROLL, SCREEN REC or TO-SOURCE shot, in shot order.

## Refuse or stop when

- No script is supplied, or the script has fewer than 10 words. Ask for the script.
- The script is not English. The 150 words-per-minute rate is for English narration. Stop and ask the writer for the rate to use.
- The script has more than 3,000 words. Ask for it in parts; each part gets its own shot table.
- A sentence has 26 or more words and no split point exists. Ask the writer to add punctuation.
- The request asks for footage, screenshots, testimonials, a recreation of a real event, or the appearance of a named real person that the script does not describe. Do not invent it. Write "TO-SOURCE: do not fabricate" in the asset cell and list the request under Flags.
- The request asks to present a recreation, a stock clip or a generated image as real footage of an event. Refuse that framing and offer TO-SOURCE rows instead.

## Files in this package

- SKILL.md: this procedure.
- LICENSE.txt: Apache License 2.0 text.

This package contains no scripts and makes no network calls.
