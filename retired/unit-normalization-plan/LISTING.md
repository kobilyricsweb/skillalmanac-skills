# unit-normalization-plan

Unpublished original; editorial tier: free. No public score or release approval.

## What and when

Use when supplied measurements use mixed or potentially ambiguous units and need a controlled conversion specification before transformation. Do not use for inventing conversion factors, guessing unlabeled units, interpreting field meaning, or applying conversions without approved formulas and rounding rules.

## Task boundary

recipe-scale-converter converts recipe quantities and data-analysis-eda explores datasets; this plans a controlled, unexecuted per-field unit conversion under supplied formulas and precision rules, quarantining unlabeled values.

## Try the independent synthetic example

Create a normalization plan from this complete synthetic input. Field: parcel_span. Original value and source label: 3 A. Target unit: B. Approved formula: target = source * 2. Precision rule: whole B units. Intended scope: illustrative planning for parcel_span values explicitly labeled A. Ambiguous examples: none. The input is illustrative, not ready for execution. Preserve the original value and show any reproducible planned output, validation checks, status, quarantines, and scope limits. Do not overwrite data or claim domain validity.

Observed inline supplied-skill output (tools unavailable; not native discovery), job `factory100_execute_3b1bbe1c52ba`:

```text
{"field_specifications":[{"field":"parcel_span","original_value":"3 A","source_unit":"A","target_unit":"B","supplied_formula":"target = source * 2","precision_rule":"whole B units","validation_checks":["Confirm the original value is 3 and the source label is A.","Apply the supplied formula in the source-to-target direction.","Confirm the result is expressed in whole B units.","Retain the original value and unit."],"status":"planned","planned_output":6}],"quarantined_cases":[],"scope_limits":["Applies only to parcel_span values explicitly labeled A.","The planned output 6 B is illustrative and not an executed data change.","The input does not establish domain validity."],"execution_authorized":false}
```

## Verify locally

Run `python evals/run_fixtures.py` from this package directory. See [verification](VERIFICATION.md) for actual results and outstanding gates.
