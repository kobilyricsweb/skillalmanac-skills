# sampling-frame-coverage-note

Unpublished original; editorial tier: paid-candidate. No public score or release approval.

## What and when

Use when a supplied sampling frame needs a bounded description of included and excluded populations, duplicate risks, time limits, and unknown coverage. Do not use for taxonomy assignment coverage, representativeness claims, bias estimation, or statistical sampling design beyond the supplied rules.

## Task boundary

Nearest is taxonomy-gap-finder; this assesses population-frame coverage rather than taxonomy assignment coverage.

## Try the independent synthetic example

Write a bounded coverage note from this synthetic frame. Target population: all current members of Garden Club North during May. Frame form: snapshot exported 31 May. Inclusion rule: members with an email account in the club portal. Exclusion rule: paper-only members. Duplicate risk: a member can have both a personal and work portal account. Known unknown: whether all current members use the portal. Include a compact coverage account, time bound, duplicate mechanism and consequence, unknowns, conflicts, verification findings, and actions outside scope.

Observed inline supplied-skill output (tools unavailable; not native discovery), job `factory100_execute_1b97612002cf`:

```text
{"target_definition":"All current members of Garden Club North during May.","frame_form":"snapshot","time_bounds":"Snapshot exported 31 May; relation to all current May members is not established beyond that date.","coverage_entries":[{"unit_or_channel":"Members with an email account in the club portal","status":"included","supporting_rule":"Inclusion rule: members with an email account in the club portal.","limitation":"Inclusion does not establish coverage of all current members."},{"unit_or_channel":"Paper-only members","status":"excluded","supporting_rule":"Exclusion rule: paper-only members.","limitation":"The number of excluded members is unknown."},{"unit_or_channel":"All current May members without a portal account","status":"unknown","supporting_rule":null,"limitation":"Whether all current members use the portal is unknown."}],"duplicate_risks":[{"mechanism":"A member can have both a personal and work portal account.","consequence":"One member may appear through more than one account; counts of occurrences may exceed counts of members.","occurrence_status":"possible"}],"unknown_coverage":["Whether all current May members use the portal.","The number of paper-only members and duplicate occurrences."],"conflicts":[],"verification_findings":["The frame is bounded to the 31 May snapshot.","No representativeness, bias magnitude, population size, or duplicate count is established.","Actions outside scope: sampling, weighting, deduplication, and external contact."]}
```

## Verify locally

Run `python evals/run_fixtures.py` from this package directory. See [verification](VERIFICATION.md) for actual results and outstanding gates.
