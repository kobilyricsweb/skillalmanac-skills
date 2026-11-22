# Candidate Scorecard Builder

## One line

Turns written interview notes for two or more candidates into one weighted scorecard, so every candidate is judged on the same criteria with cited evidence.

## What it does

The skill walks an agent through a fixed procedure. It takes the role title, the candidates' notes, and four to six criteria. Each criterion receives a weight, and the weights must total 100. Each criterion gets a short anchor that describes what a top score looks like in observable terms, such as a project, a tested skill, or a measured result.

Each candidate is then scored from 1 to 4 on every criterion. A score is only valid when it cites a note. A score of 1 means the notes contradict the criterion. A criterion with no matching evidence is not scored: it is marked MISSING with 0.00 points, the status becomes partial, and the affected total is labeled provisional. Points are calculated as score times weight divided by four, so the maximum total is 100.00. The output lists the criteria, every score with its evidence, the totals, the ranks, and a tie note. The final line states that the scorecard supports a human decision and does not make it.

The skill also includes refusal rules. It will not use protected traits as criteria, and it will not use stand-ins for them such as graduation year, first name, or home neighborhood. It stops when the role title, the notes, or the criteria are missing, and it returns a numbered question list instead of guessing.

## When to use

Use it when a recruiter or hiring manager has notes from several interviews and wants a side-by-side comparison on the same criteria. It is useful before a debrief meeting, when interviewers disagree about who did best, or when a team wants a written record of why scores were given.

## When not to use

Do not use it to choose a hire, write rejection messages, or rank people who have no written notes. It is not a substitute for a structured interview plan, and it does not check whether the notes are accurate. It should not be used for criteria that are not tied to the job.

## Requirements

No software, network access, or files are needed. The agent needs to read text and produce tables. The user provides the role title, one block of notes per candidate, and the criteria or permission to propose them.

## Example

Input: role of data analyst, three candidates labeled A, B, and C, five criteria, notes written by the interviewer.

```
# Candidate scorecard: Data analyst

Status: partial

## Criteria
| # | Criterion | Weight | 4-anchor |
|---|---|---|---|
| 1 | SQL and data modeling | 25 | Builds a multi-table data model and solves a window-function test unaided, with a measured result. |
| 2 | Statistical analysis and experiment design | 20 | Designs and reads an A/B test or regression, reports effect size with uncertainty, and states its limits. |
| 3 | Communication to non-technical readers | 20 | Presents findings to a non-technical audience at least monthly, with a stated decision that followed. |
| 4 | Python or R analysis tooling | 15 | Uses Python or R for cleaning and analysis in two or more projects. |
| 5 | Media or retail analytics experience | 20 | Works in media or retail analytics for one year or more, with a described project. |
| | Total weight | 100 | |

## Scores
| Criterion | Candidate | Score (1-4) | Points (of weight/4 max) | Evidence |
|---|---|---|---|---|
| 1 SQL and data modeling | A | 3 | 18.75 | Multi-table joins; a report query cut from 40 to 6 minutes by adding indexes. |
| 1 SQL and data modeling | B | 4 | 25.00 | Star schema built for ad inventory; window-function test solved in 12 minutes. |
| 1 SQL and data modeling | C | 2 | 12.50 | Basic joins and GROUP BY; window functions not tested. |
| 2 Statistical analysis and experiment design | A | 3 | 15.00 | Email subject-line A/B test; lift reported with a confidence interval. |
| 2 Statistical analysis and experiment design | B | MISSING | 0.00 | No matching evidence in notes. |
| 2 Statistical analysis and experiment design | C | 2 | 10.00 | Regression on churn; no experiment design described. |
| 3 Communication to non-technical readers | A | 3 | 15.00 | Presents findings to marketing leads monthly. |
| 3 Communication to non-technical readers | B | 2 | 10.00 | R dashboards built; audience and outcome not described. |
| 3 Communication to non-technical readers | C | 3 | 15.00 | Explained a churn regression to a VP in plain language; one-page summary. |
| 4 Python or R analysis tooling | A | 4 | 15.00 | Pandas used for cleaning in two projects. |
| 4 Python or R analysis tooling | B | 2 | 7.50 | R used for dashboards. |
| 4 Python or R analysis tooling | C | 2 | 7.50 | Python scripts for one year. |
| 5 Media or retail analytics experience | A | 4 | 20.00 | Two years in media analytics; email test described. |
| 5 Media or retail analytics experience | B | MISSING | 0.00 | No matching evidence in notes. |
| 5 Media or retail analytics experience | C | 3 | 15.00 | Eight-month retail analytics internship. |

## Totals
| Rank | Candidate | Total (of 100.00) | Note |
|---|---|---|---|
| 1 | A | 83.75 | No tie |
| 2 | C | 60.00 | No tie |
| 3 | B | 42.50 | Provisional: MISSING on criteria 2 and 5 |

## Tie note
None

## Decision note
This scorecard supports a human hiring decision. It does not make the decision.
```

## Limits

The weights, the 10-to-40 weight range, and the tie rule are working values chosen for this skill. They are not a published standard, and an organization may need different ones. The skill checks arithmetic and format, but it cannot judge whether an interviewer's notes are fair or complete. Scores depend on the quality of the notes. The skill does not handle more than six criteria, and it does not compare candidates across different roles in one scorecard.

## Status

Provisional. Lint-clean, one smoke run. Not independently verified.
