---
name: sales-call-prep-and-followup
description: Preps a seller's discovery call from supplied notes and writes the follow-up email after it. Use when a founder or sales rep says prep my discovery call, call plan, discovery questions, write the follow-up after my call, or recap email to a prospect. Builds a five-stage question plan (situation, problem, impact, decision process, next step) and a follow-up that only commits to what was said, checked by a script for invented promises, missing next-step owner or date, unanswered fields and plan coverage. Do not use for buyer-side vendor demo questions, cold outreach, web research on a prospect, or CRM data entry.
license: Apache-2.0
compatibility: The optional script needs Python 3.9 or newer, standard library only. No network access is used. Without Python, follow the manual checklist in step 6.
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  author_model: claude-sonnet-5-5
  version: "0.1.0"
  network: none
---

# Sales call prep and follow-up

Seller-side. Three jobs in order: a prep sheet before the call, notes during it, a follow-up email after it. Everything comes from what the user pasted. Do not research the prospect, do not state facts about their company that the user did not give you, and say "unknown, ask" where the notes are silent.

## The five stages

| Stage | The call has answered it when the notes hold | Common miss |
|---|---|---|
| situation | the current process, tools, team size or volume in the prospect's words | recording your assumption instead of their answer |
| problem | one concrete failure, who feels it, how often | a feature wish ("we want dashboards") |
| impact | a number (money, hours, deals, headcount) or the name of who could supply it | "it's painful" with no figure |
| decision process | who decides or approves, a timeline, budget or paperwork, any other option being weighed | only the person on the call |
| next step | action, ONE named owner, a calendar date | "I'll circle back next week" |

An answer under 3 words, or TBD, N/A, "not discussed", is unanswered. Read [the question bank](references/question-bank.md) for wording by stage and the follow-up probe for each weak answer.

## Workflow

Copy and tick:

```
- [ ] 1 Collect: what the user supplied (notes, prior emails, goal of this call)
- [ ] 2 Prep sheet
- [ ] 3 Question plan (one row per stage)
- [ ] 4 Notes file after the call
- [ ] 5 Follow-up draft
- [ ] 6 Run the checker, fix, re-run
- [ ] 7 Report
```

1. Collect. Ask only for what is missing and cannot be inferred: the call goal, what you already know (as pasted), the prospect's role, and the date of the call. Never fill gaps from memory of the company.
2. Prep sheet, exactly these headings: `Goal of the call` (one sentence, an outcome the prospect can agree to), `Known` (only supplied facts, each tagged with where it came from), `Unknown, ask` (the gaps), `Risks` (what could derail: wrong person, no budget signal), `Proposed next step` (action, owner, a date window to offer).
3. Question plan: at least one question per stage, 5 to 8 in all, in the order of the table. Write them in the notes file as `- [ ] stage: question`. Open each stage with an open question; use a probe from the bank only when the answer is thin. Stop planning at 8; a call that tries 15 questions answers none.
4. Notes file, the layout the checker reads (Markdown; a JSON form with `fields`, `question_plan`, `commitments`, `next_step` is also accepted):

```
# Call notes: <account>, <date>
## Question plan
- [x] impact: What does a missed pickup cost you in a month?
## Situation
## Problem
## Impact
## Decision process
## Commitments made
- [us] Send the integration overview
- [them] Priya to share two weeks of load data
## Next step
Action: ...
Owner: Dana Reyes (us)
Date: 2026-11-19
```

   Tick `[x]` only for questions actually asked. Record promises under Commitments made with the party in brackets: us, them, both.
5. Follow-up draft. Read [the follow-up patterns](references/followup-patterns.md) for the structure and the cases (no next step agreed, "we will think about it", silence). Rules that are not negotiable:
   - Commit only to items in Commitments made or Next step. Anything the notes do not record is a question ("Would a Dec 1 start work for you?"), never a promise.
   - No price, discount, percentage, count, date or weekday that is absent from the notes. No "guarantee", "free", "unlimited", roadmap claims, or other customers' names unless the notes contain them.
   - Restate the next step with its date and owner. Name the owner, or use "I'll" for you and "you'll" for them.
   - 80 to 180 words, one ask, subject line naming the account and the next date.
6. Verify: `python scripts/call_check.py notes.md followup.md --pretty` (run it, do not edit it; never change the script to make a check pass). Fix every `error`, re-run until `ok` is true. Treat each `warn` as a question for the user, not noise. Manual fallback without Python: for every sentence with "I'll", "we will", "we can", "you will" find its line in Commitments made; for every number, date or weekday find it in the notes; confirm the next step has owner and calendar date in both files; list which of the five stages have no answer.
7. Report in this order: ok or needs work; coverage score; unanswered fields; each error with the sentence; open warnings; what the checker cannot judge (tone, whether a claim is true, whether the prospect really agreed).

## Checker contract

`call_check.py NOTES [FOLLOWUP] [--min-coverage N] [--pretty]` prints one JSON object. Exit 0 no errors, 1 at least one error, 2 unreadable input (`{"ok": false, "error": "..."}`).

Keys: `ok`, `verdict` (pass or needs_work), `followup_checked`, `coverage_score` (0 to 100), `coverage_by_stage`, `fields`, `unanswered_fields`, `next_step` (action, owner, date), `counts`, `findings`. Each finding has `severity`, `code`, `message`, and sometimes `line`, `text`, `figure`, `field`, `term`.

| Code | Severity | Meaning |
|---|---|---|
| commitment_not_in_notes | error | a promise sentence matches under 50% of the content words of any notes commitment |
| figure_not_in_notes | error | amount, percent, count with unit, date or weekday not in the notes |
| next_step_missing / next_step_no_owner / next_step_no_date / next_step_invalid_date | error | next step incomplete; "next week" or a bare weekday is not a date |
| followup_missing_next_step_date / followup_missing_next_step_owner | error | follow-up does not repeat them |
| followup_empty, coverage_below_min | error | under 15 words; score under `--min-coverage` |
| unanswered_field, impact_not_quantified, decision_process_gap, no_plan_for_stage, plan_line_unrecognized, commitments_section_empty, risky_term_not_in_notes, followup_too_long | warn | see message |

Coverage score: per stage 1 point if a question was planned, 1 if asked, 2 if answered; total of 20 scaled to 100. Weekdays given with an ISO date in the notes are accepted for that date.

## Limits

- It checks consistency with the notes, not truth: wrong notes give a clean pass.
- Promise detection is by wording and word overlap; a promise phrased without "I'll", "we can", "you will" or similar can slip through, and a benign sentence can be flagged. Read the flagged sentence.
- English only. Dates are read as ISO or "Nov 19" / "19 November"; other formats count as missing.
- No web research, no CRM access, no sending. The user sends the email.
- Not legal or contract advice; do not draft terms, pricing or discounts the user did not state.
- For questions a buyer should ask a vendor, use a buyer-side skill instead.
