---
name: action-title-rewriter
description: Rewrites topic-style slide titles such as Q3 Results into full-sentence claim titles that the slide body supports, and flags slides whose body states no single claim. Use when a deck has generic titles, when slide titles do not state their takeaway, or when a presenter needs one support status per slide. Do not use for designing slide layouts, writing speaker notes, adding new facts to slides, or rewriting titles that already state a claim.
license: Apache-2.0
compatibility: None beyond a text-capable agent (type B).
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  author_model: claude-haiku-5-5
  version: "0.1.0"
  network: none
---

# Action Title Rewriter

## Scope

Input is the text of a slide deck. Each slide has one title line and zero or more body lines (bullets or sentences). Output is one table row per slide, a list of flagged slides, and one counts line. The old title is only a label; the body is the only evidence for the new title.

## Workflow

**Step 1. Parse the deck.**
- A new slide starts at a line beginning with "Slide" followed by a number, or at a title line that is followed by body lines.
- Number slides 1, 2, 3 in input order. Number body lines of each slide B1, B2, B3.
- Output: slide number, old title copied verbatim, body lines copied verbatim with their B-numbers.
- A slide with no body lines is kept. Its body is empty.
- Stop if no slide titles are found (see Refuse / stop when).

**Step 2. Extract the claim.**
- Read the body lines only. Ignore the old title for this step.
- Write one claim: a finished sentence with a subject and a finite verb, at most 25 words, true of the body lines.
- A claim may cite at most 2 body lines. Record the cited line numbers (for example B1, B2).
- If the body has no lines, or no body line contains a finite verb, set the claim to NONE.
- Output: claim text (or NONE) and cited lines.

**Step 3. Draft the action title from the claim.**
- Shorten the claim to a title. Use sentence case. No final period.
- Rule a: 15 words or fewer. Count space-separated tokens. A hyphenated word counts as one.
- Rule b: at least one finite verb, present or past tense, or a form of "be".
- Rule c: every number in the title appears in the cited body lines, character for character. If the body says "4.2M", the title says "4.2M", not "4.2 million".
- Rule d: a number in the old title that the cited lines do not contain is removed from the new title.
- Rule e: none of these words may appear (working list): significant, strong, robust, dramatic, unprecedented, game-changing, leading, massive.
- Output: candidate title and whether rules a to e pass.

**Step 4. Set the support status.** Apply the first row that matches.

| Condition | Support status | New title column | Note code |
|---|---|---|---|
| Claim is NONE | UNSUPPORTED | old title, unchanged | NO_CLAIM |
| Claim exists but no title passes rules a to e after one shortening try | UNSUPPORTED | old title, unchanged | NO_SINGLE_CLAIM |
| Old title already passes rules a to e and its wording matches the cited lines | KEPT | old title, unchanged | (blank) |
| Title written, rules a to e pass, old title had a number the cited lines lack | SUPPORTED | new title | N_REMOVED |
| Title written, rules a to e pass, no other issue | SUPPORTED | new title | (blank) |

**Step 5. Check each row before output.** All must be yes:
- Word count of the new title is 15 or fewer.
- A finite verb is present.
- Every number in the new title is found in the cited body lines.
- No word from the rule e list appears.
- The status matches the decision table in Step 4.

If a check fails, correct the title once. If it still fails, apply the table again from the first row that matches.

**Step 6. Write the output contract** (see the next section). Nothing else goes in the reply.

## Thresholds (working values, not industry standards)

| Item | Value |
|---|---|
| Maximum slides per request | 60 |
| Maximum words in a new title | 15 |
| Maximum words in a claim | 25 |
| Maximum body lines cited per claim | 2 |
| Maximum body lines processed per slide | 12 (extra lines are listed as not used) |

## Output contract

Section 1 is a Markdown table with exactly these columns, in this order:

`| Slide | Old title | New title | Support status | Body lines used | Note |`

- One row per slide, in slide order.
- Old title and new title are copied as text. A pipe character inside a title is written as a backslash followed by a pipe.
- Support status is one of: SUPPORTED, KEPT, UNSUPPORTED.
- Note is one of: blank, N_REMOVED, NO_CLAIM, NO_SINGLE_CLAIM.
- Body lines used is B1, or B1, B2, or a dash when none are cited.

Section 2 is a heading `## Flagged slides`, followed by one bullet per UNSUPPORTED row in the form `- Slide N: NOTE_CODE - one sentence naming the body line that was checked.` If there are no UNSUPPORTED rows, write `- None`.

Section 3 is one line: `Counts: total T, SUPPORTED S, KEPT K, UNSUPPORTED U.`

## Example row

Input slide 1: title "Q3 Results"; body B1 "Revenue reached $4.2M"; B2 "Up 18% from Q2".

| Slide | Old title | New title | Support status | Body lines used | Note |
|---|---|---|---|---|---|
| 1 | Q3 Results | Q3 revenue reached $4.2M, up 18% from Q2 | SUPPORTED | B1, B2 | (blank) |

## Refuse / stop when

- No slide titles are found: stop and output only `No slide titles found.`
- The deck has more than 60 slides: stop and output only `Split the deck into parts of 60 slides or fewer.`
- The user asks for a figure, date, name, or source that is not in the body: do not add it. Write the title without it and set the note to N_REMOVED.
- The user asks you to invent facts, quotes, or evidence to fill an empty body: refuse that part. The affected slide is UNSUPPORTED with note NO_CLAIM.
- The user asks for slide layout, speaker notes, or design changes: out of scope. Say so in one line and stop.
- A body line contains only a topic label (for example "Next year" or "Customer feedback"): it does not state a claim. Treat it as no verb in that line.
