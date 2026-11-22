# recurring-task-boundary-checker

Unpublished original; editorial tier: free. No public score or release approval.

## What and when

Use when drafting a proposed recurrence contract from supplied scope, action-specific authorization, completion evidence, exceptions, and stopping requirements. Do not use to schedule or execute automation, infer permission, alter records, perform cleanup, or send messages.

## Task boundary

escalation-trigger-catalog maps exception triggers and workflow-automation-builder implements workflows; this drafts a bounded recurrence contract with stop conditions and supplied permissions. sop-decision-point-extractor extracts branches from an existing procedure.

## Try the independent synthetic example

Draft a proposed recurrence contract for human review. Objective: review the shared intake queue each weekday at 09:00. Owner: Support lead. Input: queue records updated by 08:55. Authorized action: label records whose supplied category is Billing or Access. Exclusion: do not edit record text or contact submitters. Evidence: append record ID, applied label, and review timestamp to the audit log. Escalation: conflicting categories go to the Support lead for a category decision. Stop condition: skip the run when the queue export is unavailable; terminate after 2026-12-31. Constraint: at most 20 records per run. Do not schedule or execute anything.

Observed inline supplied-skill output (tools unavailable; not native discovery), job `factory100_execute_0c09cbaf959c`:

```text
{"objective":"Review the shared intake queue","trigger":"Each weekday at 09:00","owner":"Support lead","inputs":["Queue records updated by 08:55"],"action_boundaries":[{"action":"Label records whose supplied category is Billing or Access","status":"authorized","basis":"Explicitly authorized for those supplied categories"},{"action":"Edit record text","status":"prohibited","basis":"Explicit exclusion"},{"action":"Contact submitters","status":"prohibited","basis":"Explicit exclusion"}],"exclusions":["Edit record text","Contact submitters"],"completion_evidence":["Append record ID, applied label, and review timestamp to the audit log"],"escalations":[{"trigger":"Conflicting categories","recipient":"Support lead","decision_needed":"Choose the category"}],"stop_conditions":["Skip when the queue export is unavailable","Terminate after 2026-12-31"],"constraints":["At most 20 records per run","Proposed contract only; do not schedule or execute"],"unresolved_authorization":[],"verification_report":[{"field":"objective","support_status":"supplied"},{"field":"trigger","support_status":"supplied"},{"field":"owner","support_status":"supplied"},{"field":"completion evidence","support_status":"supplied"},{"field":"stop conditions","support_status":"supplied"}]} 
```

## Verify locally

Run `python evals/run_fixtures.py` from this package directory. See [verification](VERIFICATION.md) for actual results and outstanding gates.
