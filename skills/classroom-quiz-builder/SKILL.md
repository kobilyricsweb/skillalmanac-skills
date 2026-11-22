---
name: classroom-quiz-builder
description: Builds a multiple-choice quiz with an answer key from a text the teacher or trainer supplies (reading, chapter, lesson notes, handbook, briefing), testing only what that text says. Every answer is tied to an exact quotation, correct answers are spread across A to D, and a bundled script validates the quiz and prints a student copy. Use when the user asks for a quiz, test, knowledge check, comprehension or practice questions from material they provide. Do not use for grading student work, essays or open-ended assessments, lesson plans, flashcards, or quizzes with no source text.
license: Apache-2.0
compatibility: The check script needs Python 3.9 or newer (standard library only). No network access is used. Without Python, check the key by hand as described in the Verify step.
metadata:
  author: Skill Almanac Editorial
  version: "0.1.0"
  network: none
---

# Classroom quiz builder

Write a quiz a teacher can hand out after one read of the key. The usual defects of a generated quiz are: a keyed answer that the material does not actually support, questions answerable from general knowledge instead of the lesson, correct answers that sit mostly at B or C, and a correct option that is visibly longer than the others.

## Ground rules

1. **Only the supplied material.** Every question can be answered from the text alone, and the correct answer is provable by a line in it. Outside facts, however true, are not tested and not used in options as the correct answer.
2. **One defensible answer.** Exactly one option is correct according to the text. If a careful student could argue for two, rewrite.
3. **Quote the proof.** Each question carries a `Source:` line with words copied exactly from the material.
4. **Wrong options are real alternatives.** Same kind of thing as the answer (a date among dates, a cause among causes), similar length and grammar, drawn from the material or from typical misunderstandings. No joke options, no "all of the above", no "none of the above".
5. **The key has no pattern.** Decide the answer positions before writing options, spread evenly across A to D, no letter three times in a row.
6. **Mix the thinking.** At least three in ten questions ask the student to explain, compare or apply to a new case, not to recall a word.
7. **Fit the audience.** Vocabulary in questions is no harder than the material's.

## Workflow

### 1. Fix the request

Save the material as `source.md`. Settle: number of questions (default 10), audience (grade or role), and anything to leave out. If the material is too short for the count (fewer distinct testable points than questions), say so and propose a smaller number instead of padding.

### 2. List the testable points

Before writing questions, list more points than needed (count + 3), each with its exact quotation and a level tag:

```
point | exact words from the material | recall / understand / apply
```

Spread the points across the whole text, not just the opening paragraphs. Prefer points the material stresses.

### 3. Plan the key

Write the answer letters for all questions first, for example for ten: `B D A C A D B C D A`. Each letter two or three times, no run of three.

### 4. Write the questions

Use exactly this format; the script reads it. Rules and worked examples for question stems and wrong options are in [references/question-writing.md](references/question-writing.md); read it before the first quiz in a session.

```markdown
# <Quiz title>

## Q1 [recall]
<Question text?>
A. <option>
B. <option>
C. <option>
D. <option>
Answer: B
Source: "<exact words from the material>"
Why: <one line: why B is right, and why the most tempting wrong option is wrong>
```

Place the correct option at the planned letter, then write three wrong options to match its length and form. An `apply` question sets a short new situation; its answer must still follow from a quoted line.

Save as `quiz.md`. This is the teacher's copy with the key.

### 5. Verify

```bash
python scripts/quiz_check.py quiz.md --source source.md --count 10
```

- `FAIL source quote is not in the material`: copy the words exactly, or change the question to one the text supports.
- `FAIL answer X is correct in N of M` / `correct option is the longest`: move answers or even out the options.
- `FAIL` on format: fix the block.
- `WARN` items: fix unless there is a reason.
- Re-run until PASS. Do not edit the script or the material to make the check pass.

Then do the check the script cannot: for each question read the quoted line and confirm it proves the keyed answer and rules out the other three.

If the script cannot run, check each `Source:` quotation against the material by search, count the answer letters, and say the check was manual.

### 6. Make the student copy and deliver

```bash
python scripts/quiz_check.py quiz.md --student
```

Save the printed text as `student.md`. Deliver both files, then:

```
Questions: <count>; levels: <recall / understand / apply counts>; key spread: <A= B= C= D=>
Parts of the material not covered: <sections with no question, or "none">
Review before use: <any question where the proof needs a teacher's eye, or "none">
Check: <PASS, or "manual">
```

## Limits

- Multiple choice with four options only. No open questions, matching or true/false.
- The script proves each quotation exists in the material. It cannot prove the quotation supports the answer; the teacher reads the key once before use.
- An error in the material becomes an error in the key. The skill does not fact-check the material.
- Not for high-stakes exams without review by a subject teacher. It does not grade or score student answers.
