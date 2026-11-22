---
name: research-question-refiner
description: Refines a vague research topic into three scoped, answerable research questions, ranks them, and matches each one to a design the data can support. Use when a student or analyst has a topic but no question, needs population, exposure, comparison, outcome and time frame filled in, or must choose between descriptive, correlational, causal and qualitative methods for a project of fixed length. Do not use for writing a literature review, inventing findings, sourcing citations, or designing survey instruments.
license: Apache-2.0
compatibility: No tools, network or scripts beyond a text-capable agent (type B).
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  author_model: claude-haiku-5-5
  version: "0.1.0"
  network: none
---

# Research Question Refiner

Turns a broad topic into three scoped research questions, scores each one against a fixed checklist, ranks them, and records the design each can support. The output is a set of questions and a feasibility judgement. It is not a findings report, and it does not check the literature.

This is a type B skill: no scripts and no network. Work from the topic text and the inputs in Step 0 only.

## Step 0: Inputs

Ask for missing inputs in one message, once. Accept short answers. Apply the default when the user does not answer.

| Input | Accepted values | Default |
|---|---|---|
| Topic | any text of 3 or more words | none: see the Refuse list |
| Data access | survey, experiment, existing dataset, interviews or text | survey |
| Project length | whole weeks, 1 to 52 | 8 |
| Reader | thesis, brief, general | general |

Reader sets the register of the final text only. It does not change any score.

## Step 1: Topic sentence

Restate the topic in one sentence with no added claims.

Output: one line beginning `Topic sentence:`.

## Step 2: PECOT frame

Fill five slots from the topic and the Step 0 inputs: Population, Exposure, Comparison, Outcome, Time frame.

Each slot gets a source label: `user` (stated by the user), `assumed` (you chose it), or `unspecified` (no value yet).

Rules:
- Do not invent an outcome the topic does not name. Leave it `unspecified`; Step 4 may supply a candidate, labelled `assumed`.
- Descriptive designs write `not applicable` in Comparison.
- Time frame defaults to the project length from Step 0.

Output: a five-row table with columns Slot, Value, Source.

## Step 3: Four tests on the frame

Run the tests in this order. A failed test gets the fix in the table before Step 4.

| Test | Pass when | Fix when it fails |
|---|---|---|
| Answerable | the data access from Step 0 can measure the outcome in the population | pick an outcome the data can measure, or change the data access |
| Falsifiable | you can write one sentence stating a result that would contradict the frame | add a threshold or a direction, for example "more than 3 hours" |
| Scope | Population and Outcome each name at most 2 groups and at most 2 measures | split the topic and keep the narrower frame |
| Time | the work fits the project length (Step 6, item 3) | drop a comparison or a second wave |

## Step 4: Three candidate questions

Write exactly three questions. Each rule below is mandatory.
- One sentence, ending in a question mark.
- Names the population, the outcome measure and the time frame.
- Differs from the other two in at least one of: population, outcome measure, time frame.
- Uses "associated with" for correlational questions. Words "cause", "effect", "impact" and "lead to" appear only in causal questions that pass the Step 5 rule.

Output: a draft list labelled Q1, Q2, Q3.

## Step 5: Assign one design per question

| Design | The question asks | The data must contain | The design cannot claim |
|---|---|---|---|
| Descriptive | how many, how much, how often; no comparison | one measure per unit in one group | cause, effect, or a difference between groups |
| Correlational | whether two measures move together | both measures for each unit, 30 or more units (working value) | that one measure causes the other |
| Causal | whether changing an exposure changes an outcome | assignment by the researcher, or a documented natural experiment with a comparison group | anything the comparison group does not support |
| Qualitative | how or why people experience or describe something | interview, text or observation data from 8 to 30 participants (working values) | population frequencies |

Downgrade rule: a causal question with no assignment and no comparison group becomes correlational. Rewrite its wording with "associated with" before scoring it.

## Step 6: Feasibility checklist

Score each question 0 or 1 on each of the ten items. Record the numbers of the items that score 0.

1. The outcome measure is named, and the Step 0 data access can collect it.
2. The population can be reached with that data access.
3. The time frame fits the project length. Working values: 3 weeks for collection, 2 weeks for analysis.
4. Sample size fits the Step 5 design (30 or more for descriptive and correlational surveys; 8 to 30 for qualitative).
5. The exposure or theme is defined by a rule that two people could apply the same way.
6. The question is falsifiable (Step 3).
7. Population and Outcome each name one group and one measure.
8. Respondents under 18 require a named consent route. Score 0 until the user names one.
9. The design from Step 5 matches the wording of the question.
10. The results can be reported from data the user holds, not from a source the user cannot access.

Score bands (working values):

| Score | Action |
|---|---|
| 8 to 10 | rank the question |
| 5 to 7 | rank the question and list its failing items as conditions |
| 0 to 4 | do not rank it; return to Step 2 with the top failing item as one question to the user |

## Step 7: Rank

Sort by score, highest first. Break ties in this order:
1. A falsifiable question beats one that is not falsifiable.
2. The question with fewer measures in its wording wins.
3. The lower Q number wins.

## Step 8: Output contract

Use these headings, in this order, and no other headings.

```
## Topic sentence
## Frame
| Slot | Value | Source |
## Ranked questions
| Rank | Question | Design | Score | Failing items |
## Conditions
- one line per failing item the user must fix before fieldwork, or "none"
## Assumptions
- one line per value marked assumed or unspecified
```

Questions scored 0 to 4 appear under Conditions as "unranked", with the reason.

## Refuse / stop when

- The topic is missing or has fewer than 3 words. Ask for the topic; do not guess one.
- The user asks for the answer or a predicted finding. Say that this skill writes questions, not findings, and continue from Step 1.
- The user asks for literature, citations, statistics or quotes to support the topic. Supply none, invent none, and say that a literature search is needed.
- The user wants a causal claim but no assignment or comparison group is available. Apply the Step 5 downgrade rule; do not write a causal question.
- The study names a private individual, not a public figure, as its subject. Stop.
- The user asks for personal data from minors with no consent route. Stop that part and score item 8 as 0.

## Limits

The skill does not check whether the population or the measure exists in the real world, does not check the literature for gaps, and does not replace an ethics review. The thresholds marked "working value" are not published standards.
