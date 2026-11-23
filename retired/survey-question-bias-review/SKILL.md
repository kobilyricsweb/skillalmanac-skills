---
name: survey-question-bias-review
description: Reviews draft survey questions for leading, loaded, double-barrelled, absolute, ambiguous and jargon wording, recall burden, unbalanced scales and missing opt-out options, then proposes rewrites, scale fixes, order checks and a five-respondent pilot. Use when a questionnaire is being drafted or revised and each question needs a wording check before it is fielded. Do not use for judging whether a survey is valid, reliable or representative, for sampling design, or for analysing collected responses.
license: Apache-2.0
compatibility: Requires none beyond a text-capable agent (type B).
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  author_model: claude-haiku-5-5
  version: "0.1.0"
  network: none
---

# Survey question bias review

This is a text procedure. It checks the wording and layout of draft survey questions before they are fielded. It runs no code, contacts no one, and does not analyse responses.

## Workflow

Run the steps in order. Each step names the output it must produce. Write "none" where a step finds nothing; do not drop the step.

1. Intake. Record the number of questions, the target population in one sentence, the mode (online form, phone, in person, paper) and the scale types used. Write "unknown" for anything not given. Output: the Intake block.
2. Number and quote. Assign IDs Q1, Q2 and so on in drafted order. Copy each question and its full option list verbatim, including punctuation. Output: the numbered verbatim list.
3. Run all nine tests in Table 1 on every question. A question can fail several tests. For each fail, copy the exact fragment that triggered it. Output: one finding row per fail.
4. Rewrite every failing question. Keep the construct it measures. Fix one flaw per rewrite where possible and name the flaw code it fixes. Output: the rewrite block with the full option list.
5. Check every closed question against Table 2. Output: one scale verdict row per closed question.
6. Check order effects. Look at each question that follows a question on the same product, topic or attitude. Output: one bullet per risky pair, or the line "no order issue found".
7. Write the pilot block in the fixed form given under Output contract. Output: the Pilot protocol section.
8. Write the Limits section, using the fixed sentence given under Output contract.

## Table 1: question tests

| Code | Test | Fails when | Working threshold |
|---|---|---|---|
| LEAD | Leading | the wording points to an answer through social proof ("most users"), a tag question ("don't you agree"), or a presupposition ("since our tool is faster") | any instance |
| LOAD | Loaded | the stem holds an evaluative word ("excellent", "frustrating", "simply") | any instance in the stem |
| DOUBLE | Double-barrelled | one question asks about two objects or attributes joined by "and", "or", "as well as" or a slash | any instance |
| ABS | Absolute | "always", "never", "every", "all" or "none" appear where the respondent must judge frequency or agreement | any instance, except a true yes or no fact |
| AMB | Ambiguous | a term has two readings, or "this" or "it" has no clear antecedent | any term the target population could read two ways |
| JARGON | Jargon | a term or acronym is undefined and not in everyday use by the target population | any undefined term |
| RECALL | Recall burden | a count or frequency has no time window, or the window is longer than 4 weeks | window over 4 weeks (working value) |
| SCALE | Unbalanced scale | positive and negative options differ in number | difference of 1 or more (working value) |
| OPT | Missing opt-out | the item asks about an experience or a product the respondent may not have, and no "not applicable" or "no view" option is offered | option absent |

The 4-week window and the difference of 1 are working values chosen for this procedure. They are not published standards.

## Table 2: scale design

| Decision | Choose | Trade-off |
|---|---|---|
| Neutral position is possible | 5 or 7 points with a labelled middle option | the middle absorbs undecided answers; some respondents over-pick it |
| Respondents must lean one way | 4 or 6 points with no middle option, plus a separate "no view" option | forces a direction; respondents with no view may pick at random |
| Likelihood or recommendation | 0 to 10, both endpoints labelled | 11 options are hard to hear in phone mode |
| Labels | label every point on scales of 5 or fewer; label endpoints and middle on scales of 7 | full labels take space on small screens |
| Direction | one direction across the whole form, always from most negative to most positive, or always the reverse | a change of direction mid-form causes misreads |
| Balance | equal positive and negative options; intensity words mirrored ("somewhat" against "somewhat") | asymmetric intensity words tilt answers |

These are working values for drafting. Check them against the pilot, not against a standard.

## Severity and rewrite rules

Rank each finding before rewriting, so the most damaging flaws are fixed first.

| Severity | Codes | Why |
|---|---|---|
| Critical | LEAD, LOAD, DOUBLE | the answer depends on the wording, not on the respondent |
| Major | ABS, AMB, OPT, SCALE | answers are interpretable only with a known bias or gap |
| Minor | JARGON, RECALL | answers are usable but noisy; fix if the text is still open |

Rewrite rules, applied in this order:

1. Remove evaluative words and social proof from the stem first. Move any opinion or benefit to a separate question only if the construct needs it.
2. Split a DOUBLE question into one item per attribute. Keep the original order of attributes.
3. Replace ABS words with a frequency band or a graded agreement item.
4. Give every RECALL item a window of 4 weeks or less, and a count band with an upper open band.
5. Add an OPT option at the end of the list, labelled "Not applicable" or "No view", and keep it out of the scale count in Table 2.
6. Define any JARGON term inside the stem in five words or fewer, or swap it for a common word.
7. Do not change the construct. If a rewrite would measure something different, stop and say so instead of rewriting.

## Output contract

Use these headings, in this order, and no other top-level headings.

- `## Intake`: four bullets, labelled Questions, Population, Mode, Scale types.
- `## Findings`: table with columns ID | Test | Quoted fragment | Why it fails.
- `## Rewrites`: one block per failing ID. First line "Qn (was CODE)", then "Rewrite:" with the new question, then "Options:" as a list.
- `## Scale verdicts`: table with columns ID | Balanced | Mid-point | Opt-out | Action. Cell values are yes, no or n/a.
- `## Order effects`: bullets, or the line "no order issue found".
- `## Pilot protocol`: the fixed text: "Five respondents from the target population. Read each question aloud and ask the respondent to restate it in their own words. Record understood yes or no, the option chosen and any comment. Revise any question that two or more of the five misread, then pilot again with five new respondents. Five is a working value for finding misreadings; it estimates nothing."
- `## Limits`: the fixed sentence: "This review checks wording and layout only. It does not establish that the survey is valid, reliable or representative, and it does not test the sample."

## Refuse or stop when

- The user asks you to state that a survey is valid, reliable, unbiased, representative or statistically significant. Refuse, and quote the Limits sentence.
- The user asks for a sample size, sampling frame or weighting scheme. Out of scope.
- The user asks you to analyse collected responses. Out of scope.
- The user wants a question worded to produce a chosen result. Refuse that rewrite and offer a neutral version with the reason.
- The draft is an image or file with no text transcription. Stop and ask for the text.
- No question text is given. Stop and ask for the draft.
