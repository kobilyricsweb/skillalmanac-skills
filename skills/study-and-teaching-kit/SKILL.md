---
name: study-and-teaching-kit
description: Builds flashcards, spaced-repetition schedules, study plans and lesson outlines from notes, chapters or transcripts a student or teacher supplies. Use when asked for flashcards, Anki cards, a study schedule, spaced repetition dates, retrieval practice, a lesson outline or exit tickets. A script validates a deck (answer leaks, long cards, duplicate fronts, missing tags) and prints the review schedule as JSON. Do not use for multiple-choice quizzes with answer keys, grading, summaries, tutoring a topic, curriculum policy, or teaching to learning styles.
license: Apache-2.0
compatibility: The script needs Python 3.9 or newer, standard library only. No network access is used. Without Python, follow the manual checks in step 4 and compute dates from the interval table in step 5.
metadata:
  license: Apache-2.0
  author: Skill Almanac Editorial
  author_model: claude-sonnet-5-5
  version: "0.1.0"
  network: none
---

# Study and teaching kit

Builds learning material from a source the user supplies. Every fact on a card or in a lesson comes from that source; the skill adds structure (cards, dates, a lesson shape), never new facts.

## Choose the output

| The user is | Deliver |
|---|---|
| A learner with a date (exam, test) | Cards + exam-mode schedule + a one-paragraph routine |
| A learner with no date | Cards + standard schedule |
| A teacher | Lesson outline + checks + exit-ticket items scheduled to return; cards only if asked |
| Holding a deck already | Run the validator, fix, report each change |

If the user wants an assessment with an answer key, stop and say that is a different job.

## Evidence rules (sources and strength notes in [references/evidence.md](references/evidence.md))

| Rule | Apply it as |
|---|---|
| Retrieval practice | Cards are answered from memory before flipping; lessons open and close with recall, not rereading. Rereading and highlighting are not the plan. |
| Spacing | Use the interval table below. Same-day repetition does not count as a review. |
| Interleaving | In a session, shuffle topics and problem types once each topic has been introduced; block the first exposure. Most useful for telling similar ideas apart. |
| Small steps, checked | In lessons, one idea per chunk, then a check; proceed at about 80 percent correct. |
| Learning styles | Make no claim and no per-style assignment. Choose a format by what the content needs (diagram for spatial ideas). If asked, say the matching idea lacks supported effect on learning and cite S9. |

State the source when you explain a rule to the user (author, year). Strength notes and limits are in the reference; the intervals are working values, not measured optima.

## Spacing table

Days after the first study session (day 0). Review sessions only; a missed review is done as soon as possible and the rest keep their dates.

| Profile | Review days |
|---|---|
| standard (default) | 1, 3, 7, 14, 30, 60, 120 |
| dense (material the learner keeps missing) | 1, 2, 4, 8, 16, 32, 64 |

Exam mode: keep only reviews that land before the exam eve, and add one review on the eve when it falls at least 2 days after the last kept review. Fewer than 7 days to go: tell the user only the early intervals fit.

Per-card result after a review:

| Result | Next step for that card |
|---|---|
| Missed | Back to the day-1 step |
| Hard (recalled with effort) | Repeat the same step |
| Good | Next step |
| Easy | Skip one step |

## Workflow

```
- [ ] 1 Intake
- [ ] 2 Objectives
- [ ] 3 Cards
- [ ] 4 Validate
- [ ] 5 Schedule
- [ ] 6 Lesson outline (teachers)
- [ ] 7 Report
```

1. **Intake.** Ask only for what is missing: the source, the test or lesson date, minutes per day, and what "knowing it" means (recall a fact, explain, apply). Default: 20 minutes a day and 20 new cards a day.
2. **Objectives.** List 5 to 12 objectives, each a verb plus an object that the source supports. Every card and check traces to one.
3. **Cards.** One fact per card. Front 30 words or fewer, back 40 or fewer, at most 4 lines. Tags: at least one `topic:<name>`, and `type:<recall|explain|apply|contrast>`. For 15 or more cards, at least one fifth are `apply` or `explain`. Card forms per sentence shape, the lesson template and check techniques are in [references/card-and-lesson-patterns.md](references/card-and-lesson-patterns.md); read it when writing cards or a lesson outline. Copy numbers and terms from the source exactly.
4. **Validate.** Save the deck as JSON or CSV and run it (below). Fix every finding, re-run until exit 0. Without Python, check each card by hand against the five checks named in the Script section.
5. **Schedule.** Run the schedule command with the start date, the exam date if any, and the card count with new cards per day. Present the dates in a short table and the busiest day. If the script reports a peak over 100 reviews, cut cards or lower new cards per day and re-run.
6. **Lesson outline.** Use the 50-minute template in the patterns file: opening retrieval, goal, two chunks each followed by a check, mixed guided practice, exit ticket. Each check states the misconception it targets, the proceed threshold and the fallback. Name when each exit-ticket item returns (standard profile counted in lessons).
7. **Report** in this shape:

```
Made: <n cards, n objectives, outline length>
Validated: <validator result, findings fixed>
Schedule: <profile, first and last review dates, peak day>
Rules applied: <retrieval, spacing, interleaving, with the sources named>
Not checked: <e.g. facts against the source beyond the cards listed; learner's real capacity>
```

## Script

Run it; do not edit it to make a check pass. Prints one JSON object; stdout is strict JSON.

```bash
python scripts/deck_check.py validate deck.json
python scripts/deck_check.py schedule --start 2026-12-01 --exam 2027-01-18 --cards 60 --new-per-day 20
```

- `validate` accepts `.json` (a list, or `{"cards": [...]}`) or `.csv` (header `front,back,tags`, optional `id`; tags separated by `;`). Checks: `missing_field`, `bad_card`, `missing_tags`, `answer_leak` (at least 60 percent of the answer's content words, or the whole answer, already in the prompt), `too_long` (limits in step 3), `duplicate_front` (same prompt after lowercasing and removing punctuation). Output keys: `ok`, `cards`, `counts_by_check`, `findings` (each with `card` number, `check`, `detail`, and `id` when given). Exit 0 clean, 1 findings.
- `schedule` options: `--start` (required), `--exam`, `--profile standard|dense`, `--cards` with `--new-per-day`. Output keys: `profile`, `start`, `exam`, `offsets`, `final_review_added`, `sessions` (session, kind, date, weekday, day_offset, gap_days), and with cards: `batches`, `daily_load`, `peak_reviews`, `peak_date`, `notes`. Each batch of new cards gets its own review dates.
- Both exit 2 with a plain message on a missing file, wrong header, bad date or infeasible plan.

## Boundaries

- Not an assessment tool: no graded tests, no answer keys, no scoring of student work. For a source-based multiple-choice quiz with a key, use a quiz-building skill.
- Do not tell a learner their memory will reach a given level; the evidence supports tendencies, not guarantees.
- Pasted student data stays in the conversation; do not ask for names or ID numbers.

## Limits

- The leak check is word-overlap. It misses paraphrased leaks and flags some honest cards where the answer repeats a prompt term; read each finding.
- The length limits, the 60 percent overlap ratio and the 100 reviews per day ceiling are working values.
- The schedule is calendar arithmetic; it does not know weekends, holidays or the learner's missed days.
- Card accuracy depends on the source; the validator does not check facts.
- English-oriented stopword list; other languages get length, duplicate and tag checks but weaker leak detection.
- The evidence is for human learning in published studies, mostly fact and maths tasks; no study of this skill's output exists.
