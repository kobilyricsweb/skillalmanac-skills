# Listing page content: gradebook-weight-check

**One line:** Recomputes weighted final grades from a CSV and a stated scheme, and shows where policy choices change the result.

## What it does

The agent collects the teacher's scheme exactly as stated (category weights, drop-lowest counts, maxima, rounding, cut-offs), writes it as a small JSON file and asks the teacher to choose how blank scores are treated. A script then recomputes every student's category averages and weighted final, lists what the final would be if blanks were excluded and if they were zeroed, marks finals within 0.5 of a letter cut-off, and compares the result with the recorded final column. A what-if option finds the smallest score on one blank item that lifts a student's recorded final to a target. Students appear by id only.

## Capabilities

- `scripts/gradebook_check.py`: strict JSON with `scheme_ok`, per-student `final`, `by_category`, `policy_effect`, `flags`, plus `boundary_cases` and `mismatches_with_expected`
- Scheme checks: weights not totalling 100, empty categories, drop-lowest that removes everything, an item in two categories, unsupported keys such as late penalties
- Data checks: scores above the maximum, negatives, text in score cells, duplicate or blank ids, categories with no scores
- Explains a mismatch when the recorded grade matches the other missing-score choice
- Refuses to write a report over the scores or scheme file, even with `--force`

## When to use

A teacher, tutor or course administrator says: check my grades, verify the weighting, why does the final differ from the gradebook, what does she need on the final exam, what if missing work counts as zero.

## When not to use

Deciding grades or grading policy, writing quizzes (see `classroom-quiz-builder`) or rubrics, writing feedback, grading essays, study planning (see `study-and-teaching-kit`), or weighted averages in business data. This skill does arithmetic on the teacher's own scheme only.

## Requirements

Python 3.9 or newer, standard library only. No network. Without Python the agent recomputes a few students by hand with the rules in the reference file.

## Install

To be generated at publication: one pinned command per tool. The package installs to `.agents/skills/` and `.claude/skills/`.

## Examples

No with-skill run exists yet, so there is no saved agent reply. These are real script runs on the saved fixtures.

1. `python scripts/gradebook_check.py evals/fixtures/scores_good.csv evals/fixtures/scheme_good.json --missing exclude`: finals S01 89.0, S02 90.4, S03 76.5, S04 88.6, S05 90.0; boundary cases S02 (0.4 above the A cut-off) and S05 (89.95 unrounded, rounds up to 90.0); S04 is B if the empty final exam is left out and D (62.0) if counted as zero; exit 0.
2. `python scripts/gradebook_check.py evals/fixtures/scores_mismatch.csv evals/fixtures/scheme_good.json --missing exclude`: three recorded finals disagree (S02, S03, S05); S03's recorded 75.0 is explained by counting the blank as zero; exit 1.
3. `python scripts/gradebook_check.py evals/fixtures/scores_good.csv evals/fixtures/scheme_good.json --missing exclude --what-if Final --target 80`: S04 needs at least 59.84 on the final exam.

## Limits

- Arithmetic and consistency only; no judgement about fairness or school rules.
- Extra credit, curves, per-item weights and late penalties are not computed.
- The what-if answer assumes one blank item and the chosen missing policy for the rest.
- A boundary list is for human review; the script never moves a grade.

## Evidence

See `VERIFICATION.md`. In short: static lint 0 FAIL / 0 WARN and 14 script fixture cases pass, with expected values worked out by hand. Not tested: efficacy against a no-skill baseline, trigger behaviour in any tool, native discovery, cross-tool installs, human review.

## Demo script (60 to 90 seconds)

To be recorded from a real run once one exists. Planned beats:

1. A teacher pastes a scheme and a CSV; the agent writes `scheme.json` and finds the weights total 95, so it stops and asks.
2. After the fix, the agent asks how to treat blank work and explains the three choices.
3. Run with `--missing exclude --expected-column Recorded`: three mismatches, one explained by the zero choice.
4. Show the boundary list and the what-if for the final exam; the report ends with what was not checked.

## FAQ seeds

- Does it decide my students' grades? No. It recomputes what your scheme gives and shows where your choices matter.
- Does it need network access? No.
- Are student names sent anywhere or printed? The script never reads the name column and prints ids only; nothing leaves your machine from the script.
- Can it handle late penalties? Not directly; apply the penalty in the scores first.
- How is it different from the quiz or study kits? Those build assessments and study material; this checks gradebook arithmetic.
- Why does it re-weight when a category is empty? That is what excluding means; the report flags it so you can choose zero instead.
- How do I uninstall it? Delete the folder from `.agents/skills/` or `.claude/skills/`.

## Changelog

- 0.1.0 (2026-11-21): first version; static lint and script fixtures run on this version; no other evidence.

## License and authorship

Apache-2.0, copyright 2026 Global Media Holdings (skillalmanac.com). Drafted by an AI model (claude-sonnet-5-5). No human editor has reviewed it yet.
