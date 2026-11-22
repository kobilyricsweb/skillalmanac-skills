# survey-question-bias-review

## One line

Checks draft survey questions for leading, double-barrelled, loaded, absolute, unbalanced and recall-heavy wording, then returns rewrites, scale fixes and a five-respondent pilot plan.

## What it does

The skill takes a numbered draft of survey questions and runs nine fixed tests on each one: leading wording, loaded adjectives, double-barrelled items, absolute words, ambiguous references, undefined jargon, recall windows that are too long, unbalanced option lists, and missing "not applicable" or "no view" options. Each failed test is logged with the exact quoted fragment that triggered it. Failing questions are ranked by severity, so the flaws that change answers are fixed before the flaws that only add noise.

Every failing question gets a rewrite that keeps the construct it measures. The skill then checks each closed question against a scale table covering balance, mid-point choice and direction, reviews adjacent questions for order effects, and writes a fixed pilot protocol in which five people read the questions aloud and restate them. The output follows a strict heading order so the findings can be compared across drafts.

## When to use

Use it when a questionnaire is still being written, when a team is revising an old form that produced results nobody trusts, or when a set of questions needs a wording check before a pilot. It is most useful for short forms of five to thirty items, where a manual read can miss a double-barrelled item or an unbalanced scale.

## When not to use

Do not use it to decide whether a survey is valid, reliable or representative. It does not design samples, does not weight responses, and does not analyse results. If the draft is only available as a scanned image, the text must be transcribed first.

## Requirements

Any text-capable agent can run the procedure. No script, no network access and no installed package is needed. The input is the draft question text with its option lists. Target population and mode are optional; the skill records "unknown" when they are missing and keeps the wording checks in force.

## Example

The smoke run used six draft questions with three planted flaws. The excerpt below is the findings table from that run, copied from the review the skill produced.

| ID | Test | Quoted fragment | Why it fails |
|---|---|---|---|
| Q1 | LEAD | "Most users agree our app saves time." | Social proof presupposes the answer and signals the expected agreement |
| Q2 | DOUBLE | "the speed and the accuracy of the monthly report" | Two attributes in one item; a respondent who finds it fast but inaccurate has no valid answer |
| Q5 | SCALE | "Excellent / Very good / Good / Fair" | Three positive options against one negative option |
| Q5 | OPT | "Excellent / Very good / Good / Fair" | No "not applicable" option for a respondent who has not used the Pro plan |

## Limits

The procedure works on wording and layout only. Its thresholds, such as the 4-week recall window and the difference of 1 between positive and negative options, are working values and not published standards. The review cannot say whether a question measures what it is meant to measure, whether respondents will interpret it as intended in the field, or whether the sample is suitable. Those questions need the pilot and a real sampling plan, which this skill does not provide. The procedure has been run once, on a constructed draft.

## Status

Provisional. Lint-clean, one smoke run. Not independently verified.
