# approval-path-mapper

Unpublished original; editorial tier: free. No public score or release approval.

## What and when

Use when mapping supplied roles, authority rules, states, evidence, branches, cycles, and reachability into an approval path. Do not use to grant authority, choose missing decision rights, approve an artifact, schedule reviews, or produce generic meeting actions.

## Task boundary

escalation-trigger-catalog defines triggers, service-request-routing-table routes requests, permission-matrix-spec specifies permissions and role-coverage-gap-map checks role coverage; this maps supplied approval authority and state reachability. workflow-automation-builder implements workflows; this produces an offline map.

## Try the independent synthetic example

Map the approval path for artifact “release note,” starting state drafted. Roles: Writer, Reviewer, Publisher. Rules: Writer may send drafted to reviewed only after attaching a change list. Reviewer may return reviewed to drafted or send it to ready. Publisher may approve ready. Branch: if the note mentions pricing, Finance must approve pricing before Reviewer sends it to ready; otherwise Finance is excluded. Publisher handoff requires the change list and Reviewer decision. No escalation or deadlines are supplied. Show both branches, evidence status, unresolved items, and actions outside scope.

Observed inline supplied-skill output (tools unavailable; not native discovery), job `factory100_execute_1f94f628e63f`:

```text
{"scope":"Offline approval map for release note; not an approval decision or executed workflow.","assumptions":["No approval has been granted.","Pricing status is the sole branch condition supplied."],"artifact":"release note","starting_state":"drafted","path":[{"from_state":"drafted","actor":"Writer","action":"send to reviewed","prerequisite":"Change list attached","next_state":"reviewed","support":"Supplied Writer rule."},{"from_state":"reviewed","actor":"Reviewer","action":"return to drafted","prerequisite":"Reviewer decision","next_state":"drafted","support":"Supplied Reviewer rule."},{"from_state":"reviewed","actor":"Reviewer","action":"send to ready","prerequisite":"Reviewer decision; Finance pricing approval if pricing is mentioned","next_state":"ready","support":"Supplied Reviewer and conditional Finance rules."},{"from_state":"ready","actor":"Publisher","action":"approve","prerequisite":"Change list and Reviewer decision handed off","next_state":"approved","support":"Supplied Publisher rule and handoff constraint."}],"branches":[{"condition":"Note mentions pricing","outcome":"Finance approval is required before Reviewer sends it to ready; Finance is not otherwise defined as a role","status":"unresolved"},{"condition":"Note does not mention pricing","outcome":"Finance is excluded; Reviewer may send reviewed to ready under the stated prerequisites","status":"supported"}],"handoffs":[{"recipient":"Reviewer","evidence":["Change list"],"existence":"required-not-confirmed"},{"recipient":"Publisher","evidence":["Change list","Reviewer decision"],"existence":"required-not-confirmed"},{"recipient":"Finance","evidence":["Pricing approval when applicable"],"existence":"required-not-confirmed"}],"escalations":[],"unresolved":["Finance is required conditionally but is absent from the named roles.","No escalation, deadline, or final publication transition is supplied."],"reachability_findings":["Reviewed is reachable from drafted only after the change list is attached.","Ready and approved are reachable only through the stated transitions and prerequisites.","Finance is excluded on the non-pricing branch."],"cycle_findings":["Reviewer may return reviewed to drafted, creating a reviewed-to-drafted loop if the Writer resubmits."],"verification":["Each supported transition cites a supplied rule; evidence existence is not confirmed.","Actions outside scope: approve, publish, schedule, escalate, or contact participants."]}
```

## Verify locally

Run `python evals/run_fixtures.py` from this package directory. See [verification](VERIFICATION.md) for actual results and outstanding gates.
