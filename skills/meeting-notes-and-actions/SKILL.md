---
name: meeting-notes-and-actions
description: Turns a meeting transcript or rough call notes into minutes that separate decisions from discussion, with an action table of owners and due dates where nothing is guessed; later statements override earlier ones and unowned tasks are marked Unassigned. A bundled script traces owners, dates and numbers back to the transcript. Use when the user shares a transcript, call captions or raw notes and asks for meeting notes, minutes, a summary, a recap email, action items or who owes what. Do not use for transcribing audio, writing an agenda, or summarising documents that are not meetings.
license: Apache-2.0
compatibility: The check script needs Python 3.9 or newer (standard library only). No network access is used. Without Python, trace each action row to the transcript by hand.
metadata:
  author: Skill Almanac Editorial
  version: "0.1.0"
  network: none
---

# Meeting notes and actions

Produce notes that someone who missed the meeting can act on, and that someone who attended will not dispute. The two ways notes go wrong are recording a thing as decided when it was only floated, and naming an owner or a date that nobody said.

## Ground rules

1. **The last word wins.** A meeting changes its mind. Record the final position, and when it replaced an earlier one say so in a short clause ("moved from 1 Dec"). The same goes for a corrected number: only the corrected figure is the fact.
2. **Decided, or not.** A decision needs agreement from the person who can make it, or no objection after a clear proposal. "Let's think about it", "park it", "I'll check and come back" are not decisions.
3. **Owners are never guessed.** A person owns an action when they accepted it, or were asked by name and did not refuse. A reassignment replaces the first owner. "Someone should" has no owner: write `Unassigned`.
4. **Dates as spoken.** Write an exact date only if it was said. Convert a relative date ("by Friday") only when the meeting date is known, and keep the spoken phrase beside it. No date said: `No date set`.
5. **Nothing from outside.** No number, name, reason or background that the transcript does not contain. Do not tidy a figure or complete a half-said plan.
6. **Neutral.** No judgement of people or of how the meeting went. Leave out small talk.

## Workflow

### 1. Fix the inputs

Save the transcript as `transcript.txt`. Find the meeting date in the file or the request. If it is unknown, relative dates stay relative.

### 2. Build the ledger before writing

Read the whole transcript in order, once, and keep a working list with one line per topic:

```
topic | proposals in order | final status: decided / reversed to X / parked / left open | who closed it | where (time or speaker turn)
```

Add a second list of every "I will", "can you", "we need to", "someone should". For each: who accepted, whether it was handed to someone else later, the due phrase, whether it was cancelled by a later decision.

Do not write the notes from a first-impression skim. Reversals and corrections usually sit far from the original statement.

### 3. Write the notes

Use the layout in [references/notes-template.md](references/notes-template.md); read it once per session. Sections, in this order:

1. **Summary**: at most three lines; the outcomes, not the story.
2. **Decisions**: one line each, with who made it and the source.
3. **Action items**: a table with the columns `Owner | Action | Due | Source`. The action starts with a verb and can be understood without the rest of the notes.
4. **Open questions**: questions raised and not answered, and requests that got "I'll check" instead of a yes or no.
5. **Discussed, not decided**: ideas that were floated or parked, so nobody reads them as agreed.

Write `None` under a heading that has nothing.

Save as `notes.md`.

### 4. Verify

```bash
python scripts/notes_check.py transcript.txt notes.md
```

- `FAIL ... owner does not appear`: the name is wrong or invented. Fix it or write `Unassigned`.
- `FAIL ... due cannot be traced`: use the date as said, or a computed date followed by the spoken phrase in double quotes, for example `2026-11-20 ("by Friday")`.
- `FAIL NEW NUMBER`: a figure in the notes is not in the transcript. Remove it or copy the figure as spoken.
- `FAIL quotation`: make the quotation word for word, or drop the quotation marks and paraphrase.
- `WARN capitalised word`: check that it is not a misspelt or invented name.
- Re-run until the result is PASS. Do not edit the script or the transcript to make the check pass.

Then run the two checks the script cannot do: for each decision, find the line where it was agreed and confirm nothing later reversed it; scan the ledger for commitments that did not reach the table.

If the script cannot run, do the tracing by hand for every row of the action table and say so in the delivery note.

### 5. Deliver

Give the notes first. Then:

```
Needs confirming: <Unassigned actions, actions with no date, decisions that depended on someone absent; or "nothing">
Changed during the meeting: <reversals and corrected figures, one line each; or "nothing">
Check: <PASS, or "traced by hand">
```

If the user asked for a recap email, write it from the finished notes: decisions first, then each person's actions under their name.

## Limits

- Works from text. It does not transcribe audio, and a wrong speaker label in the transcript becomes a wrong owner in the notes.
- The script proves that names, dates, numbers and quotations exist in the transcript. It cannot prove that a decision was really agreed or that no action was missed.
- Number words ("fifteen thousand") in a transcript do not match digits in the notes; copy the form the transcript uses, or expect a flag to review by eye.
- Tone, sarcasm and silent agreement are not visible in text. When agreement is unclear, the item belongs under Open questions.
