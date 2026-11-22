## תקציר

- תוכן עמוד ה-skill: בונה מבחן אמריקאי עם מפתח תשובות מטקסט שהמורה מספק.
- שואל רק על מה שכתוב בטקסט; לכל תשובה מצורף ציטוט מדויק מהמקור.
- מפזר את התשובות הנכונות בין A ל-D ומפיק עותק תלמיד בלי תשובות.
- כולל script שבודק את המבחן. בלי רשת. המורה קורא את המפתח לפני השימוש.
- טיוטה: לא לפרסום לפני סקירה אנושית.

---

# Listing page content: classroom-quiz-builder

**One line:** Make a multiple-choice quiz from your own reading or briefing, with a key where every answer points to the exact line that proves it.

## What it does

You give it the text and the number of questions. It first lists the points worth testing with the exact words from the text, decides where the correct answers will sit so there is no pattern, then writes each question with three wrong options that look as plausible as the right one. Every answer carries a quotation from your text and a one-line reason. A script checks the format, that each quotation really is in the text, and that the answer letters are spread out; it also prints a clean student copy.

## Capabilities

- A teacher copy with answers, source quotations and a reason for each.
- A student copy with no answers.
- Questions tagged recall, understand or apply, with at least three in ten above recall.
- `quiz_check.py`: four options, one answer, quotation found in the text, answer-letter spread, banned options, repeated questions.
- A note of which parts of the text no question covers.

## When to use

You have a chapter, handout, article or safety briefing and need a quick check that people read and understood it; you want a quiz that cannot be answered from general knowledge alone.

## When not to use

Grading, essays, lesson plans, flashcards, live one-question-at-a-time quizzing, quizzes on a topic with no text supplied, high-stakes exams without a teacher's review.

## Before and after (from saved test runs)

**Without the skill.** For a warehouse safety briefing the plain assistant wrote ten correct questions, but in seven of them the right option was the longest (one was 103 characters against 46, 43 and 61), and the answer key sat at the bottom of the same file the trainees would get.

**With the skill.** With the skill the options are evenly weighted, five of ten questions describe a situation and ask what to do, answers are spread A=3 B=2 C=2 D=3, and there is a separate student copy.

## Requirements

Python 3.9 or newer for the script (standard library only). No network access. English wording is assumed by the script.

## Install

To be generated at publication: one pinned command per tool.

## Examples (from saved test runs)

1. Prompt: "I need a 10 question knowledge check for new hires based on this briefing." Result: `evals/runs/q3-forklift-briefing/with_skill/quiz.md`. 7 of 7 assertions; blind score 8 against 7.
2. Prompt: "Make a 10 question multiple choice quiz from this reading for my 7th graders, with an answer key." Result: `evals/runs/q1-herring-trade/with_skill/quiz.md`. 6 of 7; failed the option-length assertion, as did the baseline.

## Limits

- The correct option was still the longest by a small margin in 7 of 10 and 5 of 8 questions in two tests; the script only flags a clear length gap, so it reported PASS.
- The script proves each quotation exists, not that it supports the answer. Read the key once.
- Multiple choice with four options only.
- An error in your text becomes an error in the key.
- It used about 22% more tokens than the plain assistant, the highest overhead in this batch.

## Evidence

See `VERIFICATION.md`. In short: 3 tasks, one run each way, one model, Claude Code only, 2026-11-20. Blind grader: with skill preferred in 3 of 3. Static check: 0 fails. Token overhead about +22%. Not tested: other tools, real triggering, repeated runs, human review.

## Demo script (60 to 90 seconds)

1. Show the reading and the request for ten questions.
2. Plain assistant: scroll the quiz and read only the longest option each time; most are correct.
3. With the skill: one question block with Answer, Source and Why; then `quiz_check.py`: answer letters A=3 B=2 C=2 D=3, RESULT PASS.
4. Run `--student` and show the clean copy.

## FAQ seeds

- Will the answers be right? In our three tests every keyed answer was correct for both the skill and the plain assistant. Still read the key.
- Can students find the answers in the file? The student copy has no answers.
- Can it use facts beyond my text? No; that is the point.
- Can it make true/false or short-answer questions? No.
- Does it need internet access? No.
- Does it work for workplace training? One of three tests was a warehouse briefing.

## Changelog

- 0.1.0 (2026-11-20): first version, batch 01.

## License and authorship

Apache-2.0 (proposed; owner decision pending). Drafted and tested by an AI agent on 2026-11-20. No human editor has reviewed it yet.
