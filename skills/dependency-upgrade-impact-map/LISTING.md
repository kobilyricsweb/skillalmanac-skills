# dependency-upgrade-impact-map

Unpublished original; editorial tier: paid-candidate. No public score or release approval.

## What and when

Use when translating supplied old and new dependency notes plus named usage references into a bounded, offline upgrade impact map. Do not use for executing upgrades, proving breakage or safety, claiming complete repository coverage, or planning feature-flag retirement.

## Task boundary

Nearest is feature-flag-retirement-planner; this assesses supplied dependency changes rather than retiring conditional behavior.

## Try the independent synthetic example

Build an offline upgrade impact map. Old notes for library L 1.0: function openBox(path) is supported. New notes for L 2.0: openBox(path) is renamed to loadBox(path); migration guidance says replace the old name. Usage references: U1 at app/start.js calls openBox("a"); U2 at app/view.js calls renderBox(data). Supported environment: Runtime 8. Project assumption: production uses Runtime 8. New notes state L 2.0 supports Runtime 8. Classify exposure and limit coverage to these references.

Observed inline supplied-skill output (tools unavailable; not native discovery), job `factory100_execute_e9b2f9a02834`:

```text
{"documented_changes":[{"dependency_item":"openBox(path)","change_type":"renamed","old_behavior":"Supported in L 1.0.","new_behavior":"Renamed to loadBox(path) in L 2.0; migration guidance says replace the old name.","evidence":"Supplied old and new library notes."}],"matched_usage_sites":[{"usage_reference":"U1 at app/start.js calls openBox(\"a\").","dependency_item":"openBox(path)","exposure":"directly exposed","required_review":"Review and migrate this call from openBox to loadBox; no execution or breakage conclusion is established.","uncertainty":"material"},{"usage_reference":"U2 at app/view.js calls renderBox(data).","dependency_item":"openBox(path)","exposure":"not matched in supplied references","required_review":"No review for this rename is indicated by this reference.","uncertainty":"low"}],"environment_considerations":[{"environment":"Runtime 8","status":"supported_by_supplied_notes","basis":"New L 2.0 notes explicitly state support for Runtime 8, matching the project assumption."}],"conflicts":[],"unverified_exposure":["Textual matching does not establish runtime reachability, actual breakage, or safety."],"coverage_limitation":"Coverage is limited to U1 and U2; absence of another match does not establish absence elsewhere in the project."}
```

## Verify locally

Run `python evals/run_fixtures.py` from this package directory. See [verification](VERIFICATION.md) for actual results and outstanding gates.
