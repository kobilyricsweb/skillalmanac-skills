# missingness-pattern-brief

Unpublished original; editorial tier: free. No public score or release approval.

## What and when

Use when a supplied table needs an evidence-bounded summary of blank values by field, subgroup, or co-occurrence pattern. Do not use for profiling field types, explaining why values are absent, imputing data, or treating blanks, zeros, and unknowns as equivalent.

## Task boundary

Nearest is dataset-field-profiler; this examines missingness patterns rather than inventorying observed field types.

## Try the independent synthetic example

Prepare a missingness brief for all three records and only fields x and y. Records: r1 {team:A, x:null, y:0}; r2 {team:A, x:"", y:2}; r3 {team:B, x:5, y:null}. Missing markers are null and blank text "". Zero is known, not missing. Use team as subgroup and check pairwise co-missingness of x and y. Report field counts and denominators, subgroup summaries, supported co-missingness, exclusions, and interpretation limits.

Observed inline supplied-skill output (tools unavailable; not native discovery), job `factory100_execute_11b1501fc455`:

```text
{"status":"complete","scope":"Rows r1-r3; fields x and y; subgroup team; pairwise co-missingness x/y.","missing_markers":[null,""],"field_summaries":[{"field":"x","total_records":3,"missing_count":2,"missing_proportion":0.6667},{"field":"y","total_records":3,"missing_count":1,"missing_proportion":0.3333}],"subgroup_summaries":[{"subgroup":"A","size":2,"field":"x","missing_count":2,"missing_proportion":1},{"subgroup":"A","size":2,"field":"y","missing_count":0,"missing_proportion":0},{"subgroup":"B","size":1,"field":"x","missing_count":0,"missing_proportion":0},{"subgroup":"B","size":1,"field":"y","missing_count":1,"missing_proportion":1}],"co_missing_patterns":[{"fields":["x","y"],"record_ids":[],"count":0}],"excluded_or_unresolved":["No records or in-scope fields excluded."],"interpretation_limits":["Zero in r1.y is known and not missing.","Counts describe only these three records and fields; they do not explain causes or generalize beyond scope."]}
```

## Verify locally

Run `python evals/run_fixtures.py` from this package directory. See [verification](VERIFICATION.md) for actual results and outstanding gates.
