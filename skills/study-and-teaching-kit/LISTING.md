# Listing page content: study-and-teaching-kit

**One line:** Turns your notes into validated flashcards, a spaced review calendar and a lesson outline with live checks.

## What it does

The skill gives an agent a seven-step procedure for turning source material into learning material: set objectives, write one-fact cards with typed tags, validate the deck, compute review dates from a start date (and an exam date if there is one), and, for teachers, build a 50-minute lesson outline with checks for understanding that each carry a proceed threshold and a fallback. The rules (retrieval practice, spacing, interleaving, small steps with checks) are stated with their sources and strength notes in a reference file; the interval table is a stated working schedule, not a claimed optimum. A script validates a JSON or CSV deck and prints the review schedule as strict JSON, including the daily load when you give a card count.

## Capabilities

- `scripts/deck_check.py validate`: JSON report on a deck file: answer leaks, over-long fronts and backs, duplicate fronts, missing tags, missing fields
- `scripts/deck_check.py schedule`: review dates and weekdays from a start date; exam mode; two interval profiles; batches of new cards with a per-day load and the peak day
- A card-writing guide (sentence shape to card form), a lesson template with minutes, and checks for understanding that need no quiz
- A source list with strength notes and a plain statement on learning styles

## When to use

A student says make flashcards from these notes and tell me when to review them. A teacher says give me a lesson outline with checks for understanding and exit tickets from this reading. Someone has an Anki or CSV deck and wants it checked before import.

## When not to use

Multiple-choice quizzes with answer keys, grading or scoring student work, summarising a text, tutoring a topic, district-level curriculum or policy, or assigning activities by learning style.

**How it differs from `classroom-quiz-builder`:** that skill builds a multiple-choice quiz with a key, each answer tied to a quotation, as an assessment instrument for a teacher. This skill builds the practice side: cards the learner answers from memory, a review calendar, and live checks inside a lesson. It produces no answer key and no graded assessment, and its script validates card decks and dates rather than quiz keys. A user who needs both runs both.

## Requirements

Python 3.9 or newer for the script (standard library only). No network. Without Python the agent checks cards by hand against the five named checks and counts dates from the interval table.

## Install

To be generated at publication: one pinned command per tool. The package installs to `.agents/skills/` and `.claude/skills/`.

## Examples

No with-skill agent run exists yet, so there is no saved agent answer to show. The script on the saved fixtures (real output):

1. `python scripts/deck_check.py validate evals/fixtures/deck_bad.json`: exit 1, 10 cards, 8 findings: card 2 `answer_leak` ("prompt already contains answer words: mitochondrion"), cards 3, 4 and 8 `too_long` (35-word front, 56-word back, 5-line back), card 5 `missing_tags`, card 7 `duplicate_front` ("same front as card 6 with a different back"), card 9 `missing_field`, card 10 `bad_card`.
2. `python scripts/deck_check.py schedule --start 2026-12-01 --exam 2026-12-11`: offsets 1, 3, 7, 9; review dates Wednesday 2026-12-02, Friday 12-04, Tuesday 12-08, and a `final_review` on Thursday 12-10.
3. `python scripts/deck_check.py schedule --start 2026-12-01 --exam 2026-12-11 --cards 50 --new-per-day 20`: three batches (20, 20, 10 cards), peak of 30 reviews on 2026-12-04.

## Limits

- The leak check is word overlap; paraphrased leaks pass and some honest cards are flagged.
- Length limits, the 60 percent overlap ratio, the 100 reviews per day ceiling and the interval table are working values, not measured optima.
- The schedule is calendar arithmetic and ignores weekends, holidays and missed days.
- The validator does not check facts; card accuracy depends on the source.
- The evidence is from published studies of human learning, mostly facts and maths; none measures this skill.

## Evidence

See `VERIFICATION.md`. In short: static lint 0 FAIL / 0 WARN, 15 script fixture cases pass, literature references checked against Crossref records. Not tested: any with/without efficacy comparison, trigger behaviour in any tool, native discovery, any cross-tool install, human review.

## Demo script (60 to 90 seconds)

To be recorded from a real run once one exists. Planned beats:

1. Paste a page of notes and an exam date; the agent lists objectives.
2. The agent writes a JSON deck; `validate` reports a leaking card and a missing tag; the agent fixes them; exit 0.
3. `schedule` prints the dates and the peak day; the agent shows a short table.
4. Switch to a teacher prompt: a 50-minute outline with three checks, each with a threshold and fallback, and exit-ticket items placed on later dates.

## FAQ seeds

- Does it need network access? No.
- Will it make my cards from the internet? No. Cards come only from the source you give; unsupported facts are flagged, not filled in.
- Does it support learning styles? No. It says why not and cites a source.
- Can I import the deck into Anki? The JSON and CSV are plain card tables; import mapping depends on your Anki setup and has not been tested.
- How is it different from classroom-quiz-builder? See above: practice cards and schedules versus a graded multiple-choice quiz with a key.
- Are the intervals proven optimal? No. They follow the published shape (gaps widen with the retention goal) and are labelled as working values.
- How do I uninstall it? Delete the folder from `.agents/skills/` or `.claude/skills/`.

## Changelog

- 0.1.0 (2026-11-21): first version; static lint and script fixtures run on this version; no other evidence.

## License and authorship

Apache-2.0, copyright 2026 Global Media Holdings (skillalmanac.com). Drafted by an AI model (claude-sonnet-5-5). No human editor has reviewed it yet.
