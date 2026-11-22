# research-question-refiner

## One line

Turns a broad research topic into three scoped questions, scores them on a ten-item feasibility checklist, and records which design each question can support.

## What it does

The skill takes a topic such as "social media and teenagers" and walks through a fixed procedure. It first restates the topic in one sentence, then fills a five-slot frame: population, exposure, comparison, outcome and time frame. Each slot is labelled as stated by the user, assumed, or unspecified, so an invented value cannot pass as a user fact.

Next, four tests run on the frame: whether the available data can answer it, whether it is falsifiable, whether its scope is too broad, and whether it fits the project length. The skill then drafts exactly three questions, assigns one of four designs to each (descriptive, correlational, causal or qualitative), and scores each question on ten items. Questions are ranked by score, with written tie-breakers. The final output follows a fixed set of headings, so two runs on the same inputs can be compared line by line.

The skill refuses to state a predicted finding, to supply citations, or to write a causal question when no comparison group exists. It downgrades such a question to correlational wording instead.

## When to use

- A student has a topic for a thesis or a seminar paper but no research question yet.
- An analyst has a business or policy topic and needs to know which of the four designs the available data supports.
- A project has a fixed length, and the question must be finished inside it.
- The team wants the same frame and checklist applied to several topics, so the questions can be compared.

## When not to use

- You need a literature review, a gap analysis or citations. The skill does not search or verify sources.
- You need the answer or a forecast of the result. It writes questions, not findings.
- You need the survey items, interview guide or codebook. Those are a separate task.
- The subject is a private person, or the study would collect data from minors with no consent route.

## Requirements

Any text-capable agent. No scripts, no network access, no tools beyond reading and writing text. The user supplies a topic of three or more words and, optionally, the data access, project length and reader type. Without answers, the defaults are a survey, eight weeks and general register.

## Example

Excerpt from the offline smoke run on the topic "social media and teenagers", produced by following SKILL.md with the defaults above. The population, measure and sample assumptions were chosen by the run and are labelled as such in the output.

```
## Ranked questions
| Rank | Question | Design | Score | Failing items |
|---|---|---|---|---|
| 1 | Among 13 to 17-year-olds in one school, what share report using social media for more than three hours on a school day, in a self-report survey run during one 8-week term? | Descriptive | 9 | 8 |
| 2 | Among 13 to 17-year-olds in one school, is self-reported daily social media time associated with self-reported sleep hours on school nights, in the same survey? | Correlational | 9 | 8 |
| 3 | How do 14 to 17-year-olds in one school describe the moments they stop using social media at night, in 8 to 15 semi-structured interviews? | Qualitative | 8 | 6, 8 |
```

## Limits

The skill works from the topic text and the stated inputs only. It does not confirm that a population exists, that a school will grant access, or that a measure has been validated. Its thresholds, including the 30-unit sample for correlational work and the three-week collection window, are working values chosen for planning and are not published standards. Scores come from a human-readable checklist, so two authors may score one item differently; the item wording is meant to narrow that gap but does not remove it. The tie-break rule counts measures in the question wording, which favours short questions and can rank a well-designed two-measure question lower. The skill has had one offline smoke run and no comparison against a baseline prompt.

## Status

Provisional. Lint-clean, one smoke run. Not independently verified.
