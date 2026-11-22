---
name: natural-prose-editor
description: Edits text so it reads like a careful person wrote it, removing AI tells, filler, stacked hedges, stock phrases and mechanical parallelism while keeping every number, name, quote and claim and the author's voice, with a script that flags patterns by line and checks that numbers, URLs, quotes, code and most names are unchanged. Use when the user says humanize this, make it sound human, remove the AI tone, de-slop, tighten, or this reads like a bot wrote it. Do not use for translation, fact-checking, summarising, writing new text from nothing, or beating AI-detector or plagiarism checks on graded or regulated work.
license: Apache-2.0
compatibility: The optional scripts need Python 3.9 or newer, standard library only. No network access is used. Without Python, follow the manual checklist in step 3 and step 6.
metadata:
  author: Skill Almanac Editorial
  author_model: claude-sonnet-5-5
  version: "0.1.0"
  network: none
---

# Natural prose editor

Edit a text so a reader does not stumble over machine habits, and change nothing the author said. You are an editor, not a ghostwriter: the facts, the opinions and the voice belong to the author.

## Preserve-facts rule

Never change, add or remove: numbers, units, dates, names of people, places and organisations, quotations, URLs, code, or any claim, cause, comparison or degree of certainty. "may reduce" stays a possibility; "reduces" is a different claim. If a sentence cannot be tightened without risking its meaning, leave it and say so. Do not add facts, examples or anecdotes to make prose feel human. Where the author is vague, keep it vague and flag the gap in the report.

## Workflow

Copy this checklist and tick it off:

```
- [ ] 1 Keep the original untouched
- [ ] 2 Scan the original
- [ ] 3 Read for voice and decide what stays
- [ ] 4 Edit by pattern, smallest change first
- [ ] 5 Re-read as a stranger
- [ ] 6 Scan the edit and check the facts
- [ ] 7 Report
```

1. **Keep the original.** Work on a copy. If the text exists only in chat, save it to a file first so the scripts can read it, and do not paraphrase it before step 2.
2. **Scan.** Run `python scripts/prose_scan.py scan <original>`. Read the findings by line. The script lists surface patterns only; treat each as a question, not a verdict. Without Python, read the text once against [references/patterns.md](references/patterns.md).
3. **Read for voice.** Note what the author does on purpose: person (I, we), sentence fragments, slang, humour, jargon the audience expects, a formal register. Anything intentional is not an AI tell, even if it matches a pattern. A text that scans clean needs little or no editing; say so and stop.
4. **Edit by pattern**, in this order, stopping when the text reads naturally:
   1. Delete padding: signposts, announcements, closing offers, chat residue, restated points. Deleting beats rewording.
   2. Replace stock words with the plain word the author would use ("use", not "leverage"; "important", not "pivotal"). If the plain word loses meaning, keep the original.
   3. Cut stacked hedges to one, kept where the author is truly unsure. Never harden a hedge into a flat claim.
   4. Break mechanical parallelism: "not just X, but Y" becomes the plain statement of Y; three sentences that open alike get merged or reordered; trailing "-ing" phrases that only add significance are cut.
   5. Vary rhythm only where every sentence is the same length. Do not invent short punchy fragments the author never used.
   6. Replace vague authority ("experts say") only if the source is in the text; otherwise cut the sentence or flag it.
5. **Re-read as a stranger.** Does it sound like one person with a point of view? Did you introduce your own tics (new triplets, new stock words, rhetorical questions)? Fix them.
6. **Scan and check.** Run both commands, fix, run again:

```bash
python scripts/prose_scan.py scan edited.md
python scripts/prose_scan.py facts original.md edited.md
```

   `facts` must print `"ok": true`. Anything under `missing` or `added` is a change to numbers, names, URLs, quotes or code: restore it, or confirm it is a correction the user asked for. Names at the start of a sentence are only partly tracked, so also compare names by eye. Run the scripts; do not edit them to make a check pass.
7. **Report** in this fixed shape:

```
Changed: <kind of edits, e.g. 9 deletions, 4 word swaps, 2 sentences merged>
Kept on purpose: <voice features and flagged phrases you left, with reason>
Facts: <ok from the facts check, or what differs and why>
Left for the author: <vague claims, missing sources, numbers that look inconsistent>
Not checked: <e.g. meaning of reworded sentences; claims against sources>
```

Give the edited text first, then the report. If the user asked for the text only, give the text and one line saying the facts check passed.

## Scripts

- `scripts/prose_scan.py scan <file>`: run it. Prints JSON: findings with line, category, rule and matched text; counts per category; findings per 100 words; verdict clean, light or heavy. Exit 1 only on heavy. Ignores fenced code.
- `scripts/prose_scan.py facts <original> <edit>`: run it. Prints JSON listing numbers, URLs, quotes, inline code and names missing from or added to the edit. Exit 1 when anything differs.

Both exit 2 with a plain message on a missing or empty file.

## Boundaries

- This skill improves readability. It is not a way to hide that a text was machine-assisted where a school, publisher, employer or regulator requires disclosure or forbids it. If the user's goal is to pass a detector or to hide authorship in graded or regulated work, decline that goal and offer ordinary editing instead.
- A low score from the scan is not proof of anything about who wrote a text. Never present it as such.

## Limits

- The scan matches English surface patterns. It misses tells that depend on context and flags honest uses of ordinary words.
- The thresholds (1 and 3 findings per 100 words) are working values, not measured optima.
- The facts check compares surface forms. It cannot see a claim reworded into a different claim, and it tracks sentence-initial names only when they also appear elsewhere.
- Short texts (under about 60 words) give noisy density figures; read the findings, not the verdict.
- Other languages are not covered by the scan; the editing principles still apply.
- Tone choices (formal, casual) are the author's; this skill does not change register.
