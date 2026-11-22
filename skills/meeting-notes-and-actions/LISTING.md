## תקציר

- תוכן עמוד ה-skill: הופך תמליל פגישה לסיכום שמפריד בין מה שהוחלט למה שרק נדון.
- טבלת משימות עם אחראי, תאריך ומקור; משימה בלי אחראי מסומנת Unassigned ולא מנוחשת.
- כולל script שמוודא שכל שם, תאריך, מספר וציטוט מופיעים בתמליל. בלי רשת.
- אינו מתמלל אודיו.
- טיוטה: לא לפרסום לפני סקירה אנושית.

---

# Listing page content: meeting-notes-and-actions

**One line:** Turn a meeting transcript into notes nobody will dispute: what was decided, who owes what by when, and what is still open.

## What it does

You paste a transcript or rough notes. Before writing, the skill walks the whole conversation in order and tracks each topic to its final state, because meetings change their minds: a launch date moves, a figure is corrected, a task is handed to someone else. The notes separate decisions from things that were only discussed, and the action table never names an owner or a date that nobody said. A script then checks that every owner, date, number and quotation in the notes exists in the transcript.

## Capabilities

- Notes with fixed sections: Summary, Decisions, Action items, Open questions, Discussed not decided.
- An action table: owner, action, due, source line. Unowned tasks are marked Unassigned.
- Relative dates ("by Friday") converted only when the meeting date is known, with the spoken phrase kept beside them.
- `notes_check.py`: traces owners, dates, numbers and quotations back to the transcript.
- A closing note of what needs confirming and what changed during the meeting.

## When to use

After a call you have the transcript or captions and need minutes, action items or a recap email; you missed a meeting and need to know what was decided.

## When not to use

Transcribing audio, writing an agenda, summarising reports or email threads, scheduling.

## Before and after (from saved test runs)

**Without the skill.** In a marketing sync the launch was agreed for December 1st, then moved to December 8th after legal joined. The plain assistant got the date right but wrote "Monday 8 December 2026" (it is a Tuesday), said the legal review was "not started" when the transcript says "isn't finished", and added an action built from a remark about the cancelled date.

**With the skill.** With the skill: "Winter campaign launch is December 8th. Replaces: December 1st." The budget is 18,500 with the misread 15,000 noted as replaced, the landing-page update is listed as Unassigned, and the newsletter vendor switch sits under "Discussed, not decided".

## Requirements

Python 3.9 or newer for the script (standard library only). No network access. English wording is assumed by the script.

## Install

To be generated at publication: one pinned command per tool.

## Examples (from saved test runs)

1. Prompt: "Here's the transcript from today's sync. Can you write up the meeting notes with action items?" Result: `evals/runs/m1-marketing-sync/with_skill/notes.md`. 7 of 7 assertions; blind score 9 against 7.
2. Prompt: "minutes for this retro pls, need to send to the team" Result: `evals/runs/m3-retro/with_skill/notes.md`. 7 of 7; no invented date. The baseline wrote "By 30 Nov" for an undated "by the 30th".

## Limits

- On a client call the plain assistant's notes were judged more useful: grouped by company, with the SLA figures kept. The skill's fixed layout dropped context.
- The script proves that items exist in the transcript, not that a decision was really agreed. It cannot catch an outdated figure that was later corrected, because the old figure is in the transcript too.
- Works from text only; a wrong speaker label becomes a wrong owner.
- Number words ("fifteen thousand") do not match digits.

## Evidence

See `VERIFICATION.md`. In short: 3 tasks, one run each way, one model, Claude Code only, 2026-11-20. Blind grader: with skill preferred in 2 of 3, baseline preferred in 1. Static check: 0 fails. Token overhead about +2%. Not tested: other tools, real triggering, repeated runs, human review.

## Demo script (60 to 90 seconds)

1. Show the transcript; highlight "December 1st it is" at 00:01:55 and "launch is December 8th" at 00:07:05.
2. Plain assistant's notes: point at "Monday 8 December" and the extra action.
3. With the skill: the Decisions line with "Replaces: December 1st", the Unassigned row, then `notes_check.py`: RESULT PASS.
4. End on "Needs confirming": landing page has no owner; photo approval is open.

## FAQ seeds

- Does it record or transcribe the meeting? No. It needs text.
- What if nobody agreed to do a task? It is listed as Unassigned so someone can pick it up.
- Does it guess due dates? No. It uses the date as said, or "No date set".
- Does it need internet access? No.
- Can it write the follow-up email? Yes, from the finished notes. That path was not tested.
- Does it work with captions that have no timestamps? Yes; the source column then uses the speaker and a few words. One test task was of this kind.

## Changelog

- 0.1.0 (2026-11-20): first version, batch 01.

## License and authorship

Apache-2.0 (proposed; owner decision pending). Drafted and tested by an AI agent on 2026-11-20. No human editor has reviewed it yet.
