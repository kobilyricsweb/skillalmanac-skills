# evidence-expiry-review-queue

Unpublished original; editorial tier: paid-candidate. No public score or release approval.

## What and when

Use when supplied evidence records have review periods or supersession rules and a collection needs an orderly attention queue. Do not use to declare evidence false, refresh one page’s content, or invent review dates, priority rules, labels, or supersession conclusions.

## Task boundary

Nearest is content-refresh-plan; this queues evidence review across a collection rather than planning updates to one page.

## Try the independent synthetic example

Create an evidence review queue as of 2026-11-21; do not edit claims or create reminders. Records: E1 dated 2026-11-01 supports C1 and C2; E2 dated 2026-11-10 supports C3. Rule: review each record 14 calendar days after its record date. Priority policy: earlier trigger date first; ties use more dependent claims first. Allowed interim label: “review due” when the trigger date is on or before the as-of date, otherwise “scheduled.” No supersession notes exist.

Observed inline supplied-skill output (tools unavailable; not native discovery), job `factory100_execute_75178eb4c9c6`:

```text
{"queue":[{"evidence_item":"E1","supplied_rule":"Review 14 calendar days after the record date.","trigger_date":"2026-11-15","date_calculation":"2026-11-01 + 14 calendar days = 2026-11-15","dependent_claims":["C1","C2"],"priority_basis":"Earlier trigger date; two dependent claims.","interim_label":"review due","supersession_status":"not_stated"},{"evidence_item":"E2","supplied_rule":"Review 14 calendar days after the record date.","trigger_date":"2026-11-24","date_calculation":"2026-11-10 + 14 calendar days = 2026-11-24","dependent_claims":["C3"],"priority_basis":"Later trigger date; one dependent claim.","interim_label":"scheduled","supersession_status":"not_stated"}],"unscheduled":[],"open_questions":["Are any supersession statuses applicable despite no notes being supplied?"],"verification_report":["Both records are covered.","E1 is due as of 2026-11-21; E2 is scheduled.","Ordering follows trigger date, with dependent-claim count supporting the ordering."],"outside_scope":["Editing claims","Declaring evidence false or superseded","Creating reminders"]}
```

## Verify locally

Run `python evals/run_fixtures.py` from this package directory. See [verification](VERIFICATION.md) for actual results and outstanding gates.
