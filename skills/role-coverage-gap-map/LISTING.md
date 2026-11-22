# role-coverage-gap-map

Unpublished original; editorial tier: paid-candidate. No public score or release approval.

## What and when

Use when a supplied process schedule must be checked for role coverage across required windows, assignments, backups, overlaps, and uncovered intervals. Do not use for mapping approval authority, inferring availability, substituting similar job titles, or deciding who should be authorized.

## Task boundary

schedule-conflict-check detects overlaps, rest breaches, capacity issues, and unassigned slots in booking or roster data. role-coverage-gap-map instead partitions required process windows and requires interval-specific coincidence of assignment, permission, and availability, without inferring substitutes or assigning staff.

## Try the independent synthetic example

Build a coverage map using UTC and start-inclusive, end-exclusive intervals. Responsibility: watch the support inbox from 09:00 to 11:00. Assignment: Support Agent A for the whole window. A is available 09:00–10:30. Backup B is assigned 10:00–11:00 and available 10:00–11:00. Rule R1 permits Support Agents A and B to watch the inbox. Partition at every boundary, show coverage and overlap or gap status, and list any decision needing authorized review. Do not alter assignments.

Observed inline supplied-skill output (tools unavailable; not native discovery), job `aggregate_isolated_683de4b018b0d5aa`:

```text
{"time_zone":"UTC","intervals":[{"responsibility":"watch the support inbox","required_window":"09:00–11:00 (start-inclusive, end-exclusive)","interval":"09:00–10:00","assigned_role":"Support Agent A","availability":"Support Agent A available 09:00–10:30","backup":null,"coverage_status":"covered","overlap_or_gap":null,"supporting_rule":"R1 permits Support Agent A to watch the inbox; A is assigned for the whole required window and available during this interval.","unresolved_issue":null},{"responsibility":"watch the support inbox","required_window":"09:00–11:00 (start-inclusive, end-exclusive)","interval":"10:00–10:30","assigned_role":"Support Agent A","availability":"Support Agent A available 09:00–10:30; Backup B available 10:00–11:00","backup":"Backup B assigned 10:00–11:00","coverage_status":"overlap","overlap_or_gap":"A and B both have applicable assignment, permission, and availability during 10:00–10:30.","supporting_rule":"R1 permits Support Agents A and B to watch the inbox.","unresolved_issue":null},{"responsibility":"watch the support inbox","required_window":"09:00–11:00 (start-inclusive, end-exclusive)","interval":"10:30–11:00","assigned_role":"Support Agent A","availability":"Backup B available 10:00–11:00; no availability for A applies after 10:30","backup":"Backup B assigned 10:00–11:00","coverage_status":"covered","overlap_or_gap":"A lacks applicable availability, but qualifying Backup B covers the interval.","supporting_rule":"R1 permits Backup B to watch the inbox; B is assigned and available during this interval.","unresolved_issue":null}],"gap_conflict_register":["No uncovered interval exists within 09:00–11:00.","Qualifying coverage overlaps during 10:00–10:30 because both A and B apply."],"review_decisions":["An authorized reviewer must decide whether the 10:00–10:30 overlap requires coordination or clarification; no assignment is altered."]}
```

## Verify locally

Run `python evals/run_fixtures.py` from this package directory. See [verification](VERIFICATION.md) for actual results and outstanding gates.
