# temporal-granularity-alignment

Unpublished original; editorial tier: free. No public score or release approval.

## What and when

Use when supplied sources report observations at different time grains and a comparison or join needs explicit temporal alignment. Do not use for inventing finer-period values, choosing unstated calendars or time zones, or auditing weighted-rate calculations.

## Task boundary

Nearest is weighted-rate-audit; this aligns temporal grains rather than checking weighted calculations.

## Try the independent synthetic example

Create a temporal alignment plan, not an executed join. Source A contains daily unit counts in UTC for 2026-01-01 value 2 and 2026-01-02 value 3. Its periods are Gregorian calendar days with inclusive starts and exclusive ends. Source B contains one full Gregorian calendar-month unit count for January 2026 in UTC, value 5, covering 2026-01-01 through 2026-02-01 with an inclusive start and exclusive end. The target grain is a UTC Gregorian calendar month with the same January boundary. Approved rule: sum Source A daily counts only within their supplied coverage; retain Source B at monthly grain. Source A's supplied comparison window is explicitly limited to 2026-01-01 through 2026-01-03 exclusive, with no gaps inside that two-day window; no observations or completion rule are supplied for the rest of January. State permitted transformations, forbidden expansions, boundary handling, comparability, and actions outside scope.

Observed inline supplied-skill output (tools unavailable; not native discovery), job `factory100_execute_a2068c39e77d`:

```text
{"target_grain":"UTC Gregorian calendar month","sources":[{"source_id":"A","native_grain":"day","coverage_period":"2026-01-01 inclusive to 2026-01-03 exclusive","boundary_convention":"inclusive start, exclusive end","timezone":"UTC","calendar":"Gregorian","permitted_transformation":"Sum supplied daily counts: 2+3=5 for the covered two-day window; retain that result as partial coverage, not a complete January month.","forbidden_transformations":["Fill or infer the remainder of January","Treat the partial sum as a complete monthly value","Expand monthly observations into daily values"],"meaning_effect":"changed","comparability_status":"conditionally_comparable"},{"source_id":"B","native_grain":"month","coverage_period":"2026-01-01 inclusive to 2026-02-01 exclusive","boundary_convention":"inclusive start, exclusive end","timezone":"UTC","calendar":"Gregorian","permitted_transformation":"Retain the value 5 at monthly grain.","forbidden_transformations":["Expand the monthly value into daily values","Treat it as equivalent to A's partial-coverage sum"],"meaning_effect":"preserved","comparability_status":"conditionally_comparable"}],"boundary_decisions":["Use January 2026 as 2026-01-01 inclusive through 2026-02-01 exclusive.","A's supplied window ends at 2026-01-03 exclusive and is not extended."],"gaps":["A has no supplied observations or completion rule for the rest of January."],"unresolved_inputs":["Complete January daily coverage or an approved rule is needed for full-month comparability."],"execution_status":"plan_only"}
```

## Verify locally

Run `python evals/run_fixtures.py` from this package directory. See [verification](VERIFICATION.md) for actual results and outstanding gates.
