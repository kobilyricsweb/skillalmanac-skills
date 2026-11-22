# cohort-membership-rule-table

Unpublished original; editorial tier: paid-candidate. No public score or release approval.

## What and when

Use when an analyst needs deterministic assignment of supplied records to one or more cohorts using inclusion, exclusion, precedence, date, and missing-value rules, including unresolved overlaps. Do not use for defining metric populations or denominators, profiling fields, estimating cohort sizes, or inferring membership from undocumented assumptions.

## Task boundary

Nearest is metric-definition-card; this operationalizes cohort membership rather than documenting a metric population and denominator.

## Try the independent synthetic example

Create a cohort rule table and classify the supplied records. Cohort RecentActive includes a record when status is "active" and event_date is from 2026-11-01 through 2026-11-30 inclusive in Asia/Jerusalem. Exclude records with test_flag=true. Required fields are status, event_date, and test_flag. Missing or invalid required values yield indeterminate. Only one cohort exists; multiple membership is therefore irrelevant. Records: R1 active, 2026-11-01, false; R2 active, 2026-11-15, true; R3 inactive, 2026-11-30, false.

Observed inline supplied-skill output (tools unavailable; not native discovery), job `factory100_execute_c17bc6310f12`:

```text
{"operational_rules":[{"cohort":"RecentActive","inclusion_conditions":["status equals active","event_date is from 2026-11-01 through 2026-11-30 inclusive in Asia/Jerusalem"],"exclusion_conditions":["test_flag equals true"],"boundary_convention":"Inclusive date range in Asia/Jerusalem.","evaluation_order":["Check status, event_date, and test_flag.","Apply test_flag exclusion.","Apply status and date inclusion conditions."],"missing_value_behavior":"Missing or invalid required values yield indeterminate."}],"required_input_notes":["Required fields are status, event_date, and test_flag."],"classifications":[{"record_id":"R1","cohort_evaluations":[{"cohort":"RecentActive","status":"eligible","rule_path":["status is active.","event_date is 2026-11-01, within the inclusive range.","test_flag is false; exclusion does not apply."]}],"candidate_cohorts":["RecentActive"],"assigned_cohorts":["RecentActive"],"assigned_cohort":"RecentActive","status":"included","rule_path":["RecentActive is eligible and is the only cohort.","Assign RecentActive."],"uncertainty":null},{"record_id":"R2","cohort_evaluations":[{"cohort":"RecentActive","status":"excluded","rule_path":["test_flag is true.","The exclusion applies."]}],"candidate_cohorts":[],"assigned_cohorts":[],"assigned_cohort":null,"status":"excluded","rule_path":["RecentActive is excluded.","No cohort remains eligible."],"uncertainty":null},{"record_id":"R3","cohort_evaluations":[{"cohort":"RecentActive","status":"ineligible","rule_path":["status is inactive.","The active-status inclusion condition fails."]}],"candidate_cohorts":[],"assigned_cohorts":[],"assigned_cohort":null,"status":"excluded","rule_path":["RecentActive is ineligible.","No cohort remains eligible."],"uncertainty":null}],"unresolved_conflicts":[]}
```

## Verify locally

Run `python evals/run_fixtures.py` from this package directory. See [verification](VERIFICATION.md) for actual results and outstanding gates.
