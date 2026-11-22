# STAR story bank

A story bank is a set of records about things that really happened to the user, shaped so they can be told in about two minutes.

## Contents

- Collection (ask, never invent)
- The record
- Component rules
- Themes and coverage
- Mapping stories to a role
- Spoken form

## Collection (ask, never invent)

Run this interview, one question at a time, before writing anything:

1. "Name a time you fixed something that was broken." Then: failed, disagreed, led without authority, missed a deadline, learned something fast, worked with a difficult person, made a decision with missing data, improved a process.
2. For each answer, ask the four gap questions only where the answer is silent: when and where (job, project, year); what exactly the user did themselves, as opposed to the team; what changed afterwards; any number (time, money, error rate, people, scale).
3. If the user cannot remember a number, record the result qualitatively. Never estimate a figure for them. If they offer an estimate, mark it `(approx.)` in the record.
4. Anything the user did not say stays out. A thin story is flagged, not padded.

## The record

Fields, one object per story, matching the tracker contract: `id` (short, unique), `title`, `situation`, `task`, `action`, `result`, `source` (job or project and period), and optional `themes` (a list; the script ignores it).

## Component rules

| Component | Rule | Typical length |
|---|---|---|
| Situation | Context only: where, when, what was at stake. No judgement words. | 1 to 2 sentences |
| Task | The user's own responsibility or goal in that situation, not the team's. | 1 sentence |
| Action | First person singular. At least two concrete steps in order, including one decision and why. "We" only for what the team did, said so. | 3 to 5 sentences |
| Result | What changed, with a number if one exists, plus what the user would do differently or learned. | 1 to 3 sentences |

The script treats an empty or placeholder component (TBD, n/a, ...) as an error and one under 3 words as thin.

## Themes and coverage

Tag each story with 2 or 3 themes: conflict, failure, leadership, deadline pressure, ambiguity, influence without authority, customer focus, learning quickly, ethics or integrity, initiative. Target 6 to 8 complete stories in total, each theme covered by at least 2, and no single story carrying more than 3 themes. A story that fits every question is usually too vague.

## Mapping stories to a role

1. Extract the role's top 4 requirements from the job post, in its own words.
2. For each requirement pick the story that proves it best; a story may serve two requirements but not three.
3. Keep one failure story ready: situation, what the user got wrong, what they changed, evidence it stuck. Do not offer a disguised strength.
4. Note the gaps: a requirement with no story is a question to put to the user ("Do you have an example where...?"), not a place to improvise.

## Spoken form

Roughly 250 to 300 spoken words, about two minutes. Order: one sentence of situation, the task, the actions (the longest part), the result, one line of reflection. Test it out loud; if the user says "we" more than "I" in the action, ask what they personally did.
