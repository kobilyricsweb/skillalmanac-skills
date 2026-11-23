---
name: parent-teacher-email-writer
description: Writes a short, factual email from a teacher to a parent about one dated student situation, such as praise, attendance, missed work, a behavior concern, or a schedule change. Use when a teacher has a specific event to report and supplies the date, what happened, and what was done. Use it to draft text only. Do not use for medical, diagnostic, learning-disability, or special-education conclusions, for comparisons between students, for messages to students or staff, or for sending or submitting any message.
license: Apache-2.0
compatibility: none beyond a text-capable agent (type B).
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  author_model: claude-haiku-5-5
  version: "0.1.0"
  network: none
---

# Parent-Teacher Email Writer

Drafts one short, factual email from a teacher to a parent or guardian about one dated student situation. The agent writes text only. The teacher reviews the draft and sends it.

## Workflow

1. **Classify the situation.** Pick exactly one class from the table in step 2. Output: the class name, used in the Checks table. If no class fits, return status partial with one question asking which class applies.
2. **Collect the required facts.** Every class needs the common facts plus its extra fact. Output: a fact list with the teacher's words.

| Class | Use for | Extra required fact |
|---|---|---|
| praise | a specific positive action or result | the action being praised |
| attendance | absences, tardies, or early pickups | the number of days or tardies, and the dates |
| missed_work | assignments not submitted | each assignment name, its due date, and the new deadline |
| behavior_concern | one observed incident in class | the place and time, and what the teacher did in response |
| schedule_change | a change to a class date, time, or event | the old date or time and the new date or time |

Common facts for every class: the student's first name, the date of the event, what happened in observable terms, what was done or will be done, the next step with a date, and the teacher's name and contact method.

Record the fact list with one line per item, in this order, using these labels:

- `Student:` first name only
- `Class:` the class or period name
- `Event date:` month and day, or a list of month and day values
- `What happened:` observable events in the teacher's words
- `What was done:` the action already taken, such as a deadline given
- `Next step:` the action and its due date
- `Contact:` how the parent can reach the teacher
- `Extra fact:` the field from the class table in step 2

A label with no value counts as a missing fact.

Counting rules for step 6: split the body on whitespace, so "November 9" counts as two words and "Period 3" counts as two words. Do not count the greeting, the sign-off, or the subject line. Count the contact line as body text because it is the fourth body paragraph.

3. **Check refusal triggers.** Run every item in "Refuse / stop when". Output: pass, or stop with status refused and a one-sentence reason.
4. **Stop on missing facts.** Compare the fact list with the common facts and the extra fact for the class. If any item is missing, do not draft. Output: status partial and a numbered question list. Never guess a date, a name, a count, or an assignment title.
5. **Draft in the fixed structure.** Greeting "Dear Parent or Guardian," unless the teacher gives a name. Then four body paragraphs in this order: (a) purpose, stated in the first sentence; (b) the dated facts in plain words; (c) the next step with a date; (d) the contact line. Sign-off "Sincerely," then the teacher's name and class. Output: subject line and email text.
6. **Apply the limits.** Run the decision table below against the draft. Fix each failure by the action in the table, then rerun the check once. Output: the Checks table.

| Check | Limit | If it fails |
|---|---|---|
| Body word count | Up to 180 words, counting the four body paragraphs only; 120 is an advisory floor | Under 120: do not pad. Mark the count SHORT in Checks; the draft is still complete if every required fact is present. Over 180: cut background sentences first |
| Subject line | 60 characters or fewer (working value) | Shorten to the situation and the key date |
| Dated facts | at least 2 dates for missed_work and attendance; at least 1 for the other classes (working value) | Return status partial and ask for the dates |
| Banned words | none of: lazy, careless, fault, always, never, refuses, disrespectful, unmotivated, failing, bad (working value) | Rewrite the sentence with an observable fact; if the teacher insists on a label, refuse |
| Other students | 0 named, 0 compared | Delete the sentence |

## Rewrite pattern

Use these replacements when a teacher's draft wording hits the banned list or states a conclusion instead of an event.

| Avoid | Use instead |
|---|---|
| Jordan is lazy about homework. | Jordan has not submitted three homework assignments. |
| Jordan always forgets the materials. | Jordan did not bring the lab materials on Tuesday, November 17. |
| This is Jordan's fault. | Jordan did not complete the lab report by the due date of November 16. |
| Jordan refuses to participate. | Jordan did not take part in the group activity on Thursday, November 19. |

Subject line pattern: the situation in four to six words, then the key date. Example form: "<situation> due <day>, <month> <day>". Do not put the student's full name in the subject line.

Sentence rules for the body: one fact per sentence; each dated fact names the month and day; no sentence starts with "Unfortunately"; the next-step sentence names a day of the week and a month and day.

## Output contract

Return these headings in this order. Leave out a section only where the table says so.

- `## Status`: one word, `complete`, `partial`, or `refused`.
- `## Subject`: one line. Only when status is complete.
- `## Email`: greeting, four body paragraphs, sign-off. Only when status is complete.
- `## Checks`: a table with columns `Check` and `Result`. Rows: `Situation class`, `Body word count`, `Dated facts`, `Banned words found`, `Other students named`, `Subject length`. Only when status is complete.
- `## Questions`: a numbered list, at most 6 items, one per missing fact. Only when status is partial.
- `## Reason`: one sentence naming the refusal trigger. Only when status is refused.

## Refuse / stop when

- The request asks for a diagnosis, or a medical, ADHD, autism, learning-disability, or special-education conclusion. Status refused.
- The request asks for a comparison with another student, a class average, or a ranking. Status refused.
- The request asks you to speculate about the student's home, family, or health. Status refused.
- The email would go to a student, a coworker, or anyone other than the parent or guardian. Status refused.
- The request asks you to send, submit, or schedule the email. Status refused; return the text only.
- No situation class fits. Status partial with one question.
- Any required fact for the class is missing. Status partial with a numbered question list.
- The teacher insists on a banned label after a rewrite. Status refused.

## Files

- [LICENSE.txt](LICENSE.txt): Apache-2.0 license text for this skill. No other files ship with it.
