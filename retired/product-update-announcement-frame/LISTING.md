# product-update-announcement-frame

Unpublished original; editorial tier: paid-candidate. No public score or release approval.

## What and when

Use when framing one documented product change with confirmed availability, audience impact, limitations, required action, permitted CTA, and evidence references. Do not use for refreshing existing pages, inventing benefits, authorizing deployment, notifying users, or planning broader campaigns.

## Task boundary

release-notes-writer documents shipped changes; this frames a supplied product update for a specified audience with source-traced claims, explicit unknown release status and permitted announcement actions.

## Try the independent synthetic example

Frame one draft product update from these facts. Approved change CN1: project owners can duplicate an existing checklist within the same project. Affected audience: project owners on the Standard plan. Release status: limited beta for selected workspaces. Limitations: duplication does not copy file attachments; cross-project duplication is unavailable. Required action: none. Evidence E1 supports CN1 and both limitations. Permitted CTA: “Read the beta notes.” Produce headline options, confirmed change, scoped audience impact, limitation, migration note, CTA, unresolved items, fact trace, and actions outside announcement framing.

Observed inline supplied-skill output (tools unavailable; not native discovery), job `factory100_execute_11b1501fc455`:

```text
{"headline_options":["Limited beta: duplicate checklists within a project","Project owners can try checklist duplication in selected Standard workspaces"],"confirmed_change":"Project owners can duplicate an existing checklist within the same project.","audience_impact":"The change is scoped to project owners on the Standard plan in selected workspaces.","release_status":"limited beta for selected workspaces","limitation":"Duplication does not copy file attachments; cross-project duplication is unavailable.","migration_note":"No action is required.","cta":"Read the beta notes.","unresolved_items":[],"fact_trace":[{"statement":"Project owners can duplicate an existing checklist within the same project.","evidence_references":["CN1","E1"],"status":"confirmed"},{"statement":"The beta is limited to selected workspaces and Standard-plan project owners.","evidence_references":["E1"],"status":"confirmed"},{"statement":"Attachments are not copied and cross-project duplication is unavailable.","evidence_references":["E1"],"status":"confirmed"}],"outside_scope":["Product authorization","Deployment","Documentation changes","User notification"]}
```

## Verify locally

Run `python evals/run_fixtures.py` from this package directory. See [verification](VERIFICATION.md) for actual results and outstanding gates.
