---
name: job-search-and-interview-prep
description: Runs a structured job search with a tracker, weekly plan, honest outreach, STAR story bank, interview prep and debrief. Use when the user says job search plan, track my applications, prep me for an interview, STAR stories, follow-up email after applying, or debrief my interview. A script validates the tracker (stale applications, missing next actions, duplicate companies, incomplete STAR stories) and prints a weekly plan as JSON; target roles are scored against written criteria and question banks cover each interview type. Do not use for writing or tailoring the CV or resume, salary or contract legal advice, or inventing experience or contacts.
license: Apache-2.0
compatibility: The optional script needs Python 3.9 or newer, standard library only. No network access is used. Without Python, apply the checks in step 3 by hand using the contract tables below.
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  author_model: claude-sonnet-5-5
  version: "0.1.0"
  network: none
---

# Job search and interview prep

Run the search as a pipeline with a tracker as the single source of truth. The CV is out of scope: if the user needs a tailored resume, say so and use a resume skill.

## Truth rule

Everything about the user's history comes from the user. Never invent an employer, title, metric, project, referral, mutual contact or "I saw you at an event". If a story or message needs a fact you do not have, ask for it or leave a bracketed gap. Never send, post or apply on the user's behalf without an explicit yes for that specific message.

## Workflow

```
- [ ] 1 Criteria: write and score target roles
- [ ] 2 Tracker: create or load it in the contract format
- [ ] 3 Validate: run the script, fix errors, read the weekly plan
- [ ] 4 Outreach: draft messages under the outreach rules
- [ ] 5 Stories: build the STAR bank from real experience
- [ ] 6 Prep: pick the question bank for the interview type
- [ ] 7 Debrief: within 2 hours of each interview
```

1. **Criteria.** Read [references/role-criteria.md](references/role-criteria.md) and produce the scored criteria sheet. Roles that fail a deal-breaker are not tracked.
2. **Tracker.** Use the columns below. If the user has a spreadsheet, map it to these names; do not change their data.
3. **Validate.** Run `python scripts/tracker_check.py <tracker> [--stories <file>] --today YYYY-MM-DD`. Run it; do not edit it to make a check pass. Fix every `error`, decide every `warn` with the user, and present `weekly_plan` in rank order. Re-run after the fixes. Add `--stale-days N` and `--new-apps N` when the user states different values.
4. **Outreach.** Draft only under [references/outreach-rules.md](references/outreach-rules.md).
5. **Stories.** Follow [references/star-story-bank.md](references/star-story-bank.md): collect raw experiences by asking, then shape them into STAR records the script can check.
6. **Prep.** Open [references/question-banks.md](references/question-banks.md) at the section for this interview type only. Map 3 or 4 stories to the role's top requirements; do not rehearse all of them.
7. **Debrief.** Fill the template in [references/debrief-template.md](references/debrief-template.md), update the tracker row (status, last_contact_date, next_action with date) and re-run step 3.

## Tracker contract

CSV (one row per application, case-insensitive header) or JSON (a list, or `{"applications": [...], "stories": [...]}`).

| Field | Rule |
|---|---|
| `company`, `role`, `status` | Required. |
| `status` | One of `wishlist preparing applied screening interviewing offer accepted rejected withdrawn closed`. |
| `applied_date`, `last_contact_date`, `next_action_date`, `interview_date` | Optional, `YYYY-MM-DD`. Applied and contact dates cannot be in the future. |
| `next_action` | One concrete step. Required for every status except the four terminal ones (`accepted rejected withdrawn closed`). |
| `source`, `contact`, `notes` | Optional. |

Stories: `id`, `title`, `situation`, `task`, `action`, `result`, `source` (the real job, project and period).

## What the script checks

| Issue code | Severity | Fires when |
|---|---|---|
| `stale_application` | warn | Active status (`applied screening interviewing offer`), more than N days (default 10) since `last_contact_date` or else `applied_date`, and no dated future `next_action`. |
| `missing_next_action` | warn | Non-terminal row with empty `next_action`. |
| `overdue_next_action` | warn | `next_action_date` is before today on a non-terminal row. |
| `duplicate_company` | warn | Same company after normalisation (case, punctuation, Inc, LLC, Ltd and similar suffixes) in different roles. |
| `duplicate_application` | error | Same company and same role twice. |
| `bad_status`, `bad_date`, `future_date`, `missing_field` | error | Invalid value, as named. |
| `missing_date` | warn | Active row with neither applied nor contact date. |
| `story_missing_component` | error | Situation, task, action or result empty or a placeholder such as TBD. |
| `story_thin_component` | warn | A component under 3 words. |
| `story_missing_source`, `duplicate_story_id` | warn, error | No source; repeated id. |
| `story_result_not_quantified`, `story_bank_thin` | info | Result has no digit; fewer than 6 complete stories while a screening or interview is open. |

## Output contract

The script prints one strict JSON object. Keys: `schema_version` (1), `command`, `ok` (true when there is no warn or error), `today`, `params`, `summary` (`applications`, `by_status`, `stories`, `complete_stories`, `issues` counts), `issues` (each with `code`, `severity`, `subject`, `detail`, `fix`) and `weekly_plan`. Each plan item has `rank`, `kind`, `company`, `role`, `action`, `reason`. Plan order is fixed: `interview_prep` (interviews within 7 days), `follow_up` (stale, oldest first), `overdue_action`, `due_this_week`, `set_next_action`, `submit_application` (up to the weekly target, `preparing` before `wishlist`), `fix_stories`, `build_story_bank`. Exit 0 when `ok`, 1 on any warn or error, 2 on unusable input (an object with `error` is printed).

Do not treat `info` issues as failures. Without Python: read each row against the table above and write the plan in the same order by hand.

## Final report format

```
Pipeline: <counts by status>
Fixed: <errors resolved>
Decisions needed: <warns the user must decide>
This week: <plan items in rank order, max 8>
Not checked: <e.g. job posts not opened, facts in stories not verified, dates the user did not confirm>
```

## Limits

- The script checks structure and dates, not truth: it cannot tell whether a story really happened or whether a job exists.
- The 10-day stale window, the weekly target of 5 and the 6-story bank size are working values, not measured optima; the user can override the first two.
- A follow-up that is scheduled but never done is only caught once its date passes.
- Company matching is by normalised name, so a rebrand or a typo is not recognised as the same company.
- Interview question banks reflect common formats; a specific employer's process can differ, so ask the user what the recruiter said.
- This is not legal, immigration, tax or salary-negotiation advice, and it does not guarantee interviews or offers.
