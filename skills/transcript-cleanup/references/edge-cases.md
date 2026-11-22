## Contents

- Speakers
- Merging
- Lost or empty cues
- Fillers
- Integrity warning

## Speakers

- A line such as "Note: call back" or "Time: 5 pm" is not a speaker. The script skips a fixed list of such words (note, warning, tip, summary, time, date, url, action, decision, question, answer and a few more). If a real speaker has one of these names, the label is left in the text; tell the user.
- A speaker label must start with a capital letter (or be word plus number, such as "guest 1") and have at most four words. "Reminder to self: x" is not a label.
- Titles (Dr, Mr, Mrs, Ms, Miss, Prof, Professor, Sir, Mx) are ignored when comparing labels, so "Dr. Lee" and "Lee" are one speaker; the longest form with the most words wins, then the more frequent, then the mixed-case one.
- A one-word label joins a full name only when exactly one full name contains it as first or last word. With "Sarah Lee" and "Tom Lee" present, "Lee" stays as it is and is listed under `speakers.ambiguous`.
- All-caps or all-lowercase labels longer than two letters are title-cased when they stand alone.
- Interview labels "Q" and "A" are accepted as speakers and are not merged with anything.
- Output labels are always `Name: text`. A leading `>>` and VTT voice tags in plain output are not reproduced; in VTT output the voice tag is kept.

## Merging

- If a merge you disagree with happened, rerun with `--no-merge` and compare; each merge is in `edits` with `source_cue_ids`.
- A cue ending in a comma, semicolon or colon merges with a capitalised next cue; a cue ending without punctuation merges only when the next starts lowercase. Proper nouns that start a continuation line are therefore not merged; this is deliberate.
- Merging never crosses a speaker change, a blank line in plain text, an overlap, or a silence above `--merge-gap`.

## Lost or empty cues

A cue that contained only fillers is removed, so the file has a longer gap there. If the user needs the original cue count (for example to match another language track), run with `--policy verbatim`.

## Fillers

- Capitalised ASR tokens "Um" and "Uh" at the start of a cue count as sentence starts; lowercase ones do not, so a cue that begins "uh, how small teams ship" becomes "how small teams ship" and can still merge into the cue before it.
- "I mean" is removed only when a comma follows it and it opens a sentence or follows a comma. "I mean it" is untouched.
- A repeated word that is intentional emphasis ("the the" in a quoted title) cannot be told apart from a stutter: use `verbatim` for quoted material.

## Integrity warning

The script compares word tokens (lowercased letters and digits) of input and output, allowing only the tokens of glossary replacements. A non-empty `words.added` means a defect in the script or a glossary entry used as a free rewrite; do not deliver the file, report it.
