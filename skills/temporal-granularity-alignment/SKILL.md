---
name: temporal-granularity-alignment
description: "Use when supplied sources report observations at different time grains and a comparison or join needs explicit temporal alignment. Do not use for inventing finer-period values, choosing unstated calendars or time zones, or auditing weighted-rate calculations."
license: Apache-2.0
metadata:
  author: Skill Almanac Editorial
  author_model: "gpt-5.6-luna"
  license: Apache-2.0
  version: "0.1.4"
  network: none
---

Create an alignment plan from the supplied timestamp fields, time zones, calendar definitions, aggregation rules, gaps, coverage windows, and intended comparison grain. For every source, state its native grain, coverage period, boundary convention, timezone, permitted transformation, and whether the transformation preserves or changes meaning.

Permit aggregation only when an aggregation rule is supplied. An aggregate may be represented as a complete target-period observation only when source coverage matches that target period. An approved aggregation over partial coverage is permitted when the artifact retains the exact covered window, labels the result as partial, reports it separately from full-period observations, and does not treat it as fully comparable. Retain coarse observations at native grain unless an explicit allocation rule is provided.

Never expand a coarse observation into finer records by copying, averaging, interpolation, or allocation without an explicit rule. Do not assume calendar boundaries, fiscal periods, timezone conversions, inclusive or exclusive endpoints, or equivalent coverage from matching labels. Flag partial-period coverage, missing zones, conflicting calendars, incomplete periods, duplicate coverage, and gaps affecting comparison. Distinguish a permitted alignment from an actual completed join.

Produce a plan with source grains, coverage, transformations, forbidden transformations, boundary decisions, comparability status, gaps, and unresolved inputs. See the [input contract](references/input-contract.md) and [worked example](references/worked-example.md).

## Machine-checkable artifact contract

Return the artifact as JSON matching [references/output-schema.json](references/output-schema.json). The schema and synthetic example define the artifact shape; examples are not executed evidence.

Run `python scripts/check_output.py artifact.json` from the package directory to check JSON structure against the bundled schema. The checker is offline and checks structure only; behavioral quality is assessed separately.
