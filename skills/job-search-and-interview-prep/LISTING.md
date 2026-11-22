# Listing page content: job-search-and-interview-prep

**One line:** Runs a structured job search: a validated tracker, weekly plan, honest outreach, STAR stories and interview prep.

## What it does

The skill gives an agent a seven-step pipeline: score roles against a written criteria sheet, keep a tracker in a fixed column contract, validate it with a script, draft outreach under explicit no-fabrication rules, build a STAR story bank by asking the user for real experiences, prepare from a question bank matched to the interview type, and debrief within two hours. The script reads a CSV or JSON tracker (and an optional stories file) and prints strict JSON: issues with severity and a fix, and a ranked weekly plan. Nothing about the user's history is invented; missing facts are asked for or left as placeholders.

## Capabilities

- `scripts/tracker_check.py`: flags stale applications (default 10 days, no dated follow-up), missing or overdue next actions, duplicate companies and duplicate applications, bad statuses and dates, and STAR stories with a missing or thin situation, task, action or result
- A weekly plan in fixed order: interview prep, follow-ups, overdue actions, actions due this week, rows needing a next action, applications to submit, story fixes
- A scored target-role criteria sheet with decision thresholds
- Outreach rules (length limits, cadence, no fabricated connections) and message structures
- A STAR story-bank procedure, question banks by interview type, and a debrief template

## Difference from `resume-tailoring`

`resume-tailoring` (batch 01) rewrites the CV for a job. This skill never touches the CV; it covers everything around it: choosing roles, tracking, outreach, interview preparation and debriefs. Use both together if the user needs both.

## When to use

You say job search plan, track my applications, which applications have gone cold, prep me for an interview, STAR stories, follow-up email after applying, or debrief my interview.

## When not to use

Writing or tailoring a resume or cover letter, salary or contract legal advice, inventing experience or contacts, scraping contact data, applying to jobs automatically, or running interviews as the employer (for user research interviews see `jobs-to-be-done-interview`).

## Requirements

Python 3.9 or newer, standard library only, for the script. No network. Without Python the agent applies the tables in `SKILL.md` by hand.

## Install

Not yet published; the install command is added at release.

## Examples

**Example 1 (real fixture run).** Prompt: "Here is my job-search tracker. Today is 2026-11-21. Tell me what is wrong with it and give me my plan for the week." Input: `evals/files/t1-tracker-audit/tracker.csv`. Script output (summary): 1 error and 4 warnings.

```
error  duplicate_application  company Fabrikam / Fabrikam LLC: rows 4, 5 are the same company and the same role
warn   duplicate_company       company Contoso / Contoso Inc.: rows 2, 3 are different roles at the same company
warn   missing_next_action     row 1: Northwind Labs, Data Analyst
warn   overdue_next_action     row 2: Contoso Inc., Product Analyst (2 days past)
warn   stale_application       row 1: Northwind Labs, Data Analyst (19 days, no follow-up scheduled)
Weekly plan: 1 interview_prep (Contoso, 2026-11-24), 2 follow_up (Northwind Labs), 3 overdue_action,
4-6 due_this_week, 7 set_next_action, 8-9 submit_application, 10 build_story_bank
```

**Example 2 (real fixture run).** Input: `evals/fixtures/tracker_bad.csv` with `evals/fixtures/stories_bad.json`. The script reports a story with an empty result and another with a TBD situation as errors, a two-word task as a thin-component warning, a repeated story id, a status of "ghosted" as invalid and an application dated 2026-11-30 as a future date; it exits 1.

## Limits

- The script checks structure and dates, not truth; it cannot tell whether a story really happened.
- The 10-day stale window, the weekly target of 5 and the 6-story bank size are working values, not measured optima.
- Company matching is by normalised name; a rebrand or typo is not recognised.
- Question banks reflect common formats; a specific employer's process can differ.
- Not legal, immigration, tax or salary-negotiation advice; no guarantee of interviews or offers.

## Evidence

Static lint 0 FAIL, 0 WARN. Script fixtures 6 of 6 pass (Python 3.11, Windows 11, 2026-11-21). No efficacy eval, trigger test, cross-tool run or human review has taken place. See `VERIFICATION.md`.

## Demo script (60 to 90 seconds)

1. Prompt: "Here is my tracker. Today is 2026-11-21. What is wrong and what is my week?" with the 6-row CSV attached.
2. The agent runs `tracker_check.py` and reads the JSON.
3. It reports the duplicate Fabrikam application, the 19-day-old Northwind application and the overdue thank-you note.
4. It presents the ranked plan: prepare for the 2026-11-24 interview first, follow-up second, new applications after.
5. The user fixes the rows; re-run shows `ok` true for the repaired issues.

## FAQ seeds

- Does it need network access? No.
- Does it work with a spreadsheet? Export it as CSV and keep the column names in the contract.
- Will it write my interview answers for me? No; it shapes stories from experiences you supply and asks for missing details.
- Will it message recruiters for me? No; it drafts, you send.
- How is it different from a resume skill? It does not touch the CV.
- Can I change the 10-day stale window? Yes, with `--stale-days`.
- How do I uninstall? Delete the skill folder.

## Changelog

0.1.0, 2026-11-21: first draft; static and fixture checks only.

## License and authorship

Apache-2.0, copyright Global Media Holdings (skillalmanac.com). Drafted by an AI model (claude-sonnet-5-5); accountable editor: Global Media Holdings. No human review of the package has been recorded yet.
