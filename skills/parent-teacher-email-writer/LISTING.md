# Parent-Teacher Email Writer

## One line

Drafts a short, factual email from a teacher to a parent about one dated student situation, with a fixed structure and a body of up to 180 words (120 is an advisory floor, never padded to reach).

## What it does

The skill takes a teacher's account of one event and turns it into a brief email. It first sorts the event into one of five situation classes: praise, attendance, missed work, behavior concern, or schedule change. Each class has one extra fact the teacher must supply, such as the assignment names and due dates for missed work, or the old and new times for a schedule change. If a required fact is missing, the skill does not guess. It returns a numbered question list instead.

When the facts are present, the skill writes four body paragraphs in a fixed order: purpose in the first sentence, the dated facts, the next step with a date, and a contact line. It then checks the draft against a short decision table. The table sets the word range, the subject length, the minimum number of dates, a list of blame and label words to avoid, and a rule against naming other students. Each check has a fix, and the skill reruns the check once after a fix. The output is a fixed set of headings, so a teacher or a school office can scan the result quickly.

The skill also stops on requests it should not fill. It refuses to give medical, diagnostic, or special-education conclusions, comparisons between students, or speculation about a child's home. It also refuses to send or submit the email, because it has no sending tool and the teacher remains the sender.

## When to use

Use it when a teacher has one specific, dated event to report, such as three homework assignments not turned in with a Friday deadline, or a late arrival that happened twice in one week. Use it when the teacher can state the facts in plain words and wants a neutral first draft to edit before sending.

## When not to use

Do not use it for a parent conference plan, a letter about a formal discipline record, an individualized education plan meeting, a message to a student, or a message to a colleague. Do not use it for an email that compares a child with classmates or that needs a clinical opinion. Do not use it to decide whether a grade or a placement is correct.

## Requirements

No scripts, no network, and no files. The agent needs only text input from the teacher and the ability to count words. The skill is type B, so a text-capable agent with the SKILL.md file in context is enough.

## Example

Input facts from the teacher: teacher name Ms. Lopez; student first name Jordan; class Period 3 English; three homework assignments not submitted (Chapter 4 reading questions, assigned November 9; Vocabulary worksheet 3, assigned November 12; Week 11 response paragraph, assigned November 16); the class site shows all three as not submitted; the teacher gave a Friday deadline of December 4 to submit all three through the class site; contact: reply to this email or through the main office during school hours.

### Status

complete

### Subject

Three missing homework assignments due Friday, December 4

### Email

Dear Parent or Guardian,

I am writing to let you know that Jordan has three homework assignments that are not yet submitted in Period 3 English.

The missing assignments are the Chapter 4 reading questions, assigned November 9; the Vocabulary worksheet 3, assigned November 12; and the Week 11 response paragraph, assigned November 16. All three assignments are still missing from the class site. I have given Jordan a deadline of Friday, December 4 to submit all three.

Please talk with Jordan about the three assignments. Jordan can submit them through the class site by Friday, December 4.

You can reach me by replying to this email or through the main office during school hours. Thank you for your support.

Sincerely,
Ms. Lopez
Period 3 English

### Checks

| Check | Result |
|---|---|
| Situation class | missed_work |
| Body word count | 116 (SHORT: under 120, not padded) |
| Dated facts | 4 (November 9, November 12, November 16, December 4) |
| Banned words found | none |
| Other students named | none |
| Subject length | 57 characters |

## Limits

The skill does not verify facts. It trusts the teacher's account and only checks structure, length, and wording. Word counts follow the body-paragraph rule in SKILL.md, so the greeting, sign-off, and subject line are not counted. The banned-word list and the 60-character subject limit are working values, not published standards. The skill does not know school policy, grading rules, or local notice requirements, so a teacher should check those before sending. It produces text in US English only.

## Status

Provisional. Lint-clean, one smoke run. Not independently verified.
