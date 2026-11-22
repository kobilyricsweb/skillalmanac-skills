---
name: dataset-field-dictionary-builder
description: "Use when building a field dictionary from supplied schemas, definitions, constraints, notes, and labeled samples while separating source meaning from observations. Do not use for dataset profiling, record validation, inferred business semantics, web research, schema remediation, or backfill design."
license: Apache-2.0
metadata:
  author: Skill Almanac Editorial
  author_model: "gpt-5.6-luna"
  license: Apache-2.0
  version: "0.1.2"
  network: none
---

# Dataset Field Dictionary Builder

Build a field dictionary only from supplied field lists, schemas, definitions, constraints, notes, and labeled samples. Preserve every field name and supplied allowed value exactly.

For each field, record source wording before writing a faithful normalized definition. Record an expected type only when stated or directly constrained; a sample alone does not establish business type or meaning.

Keep these distinctions explicit:

- allowed values versus whether that list is exhaustive;
- null meaning versus blank, zero, unknown, not applicable, or omission;
- definitions and constraints versus sample observations;
- supported statements versus missing or conflicting source material.

Allowed values may be strings, numbers, booleans, or null and must retain their supplied JSON scalar types. Use a null `allowed_values` field only when no allowed-value list was supplied; an array containing null means null was explicitly supplied as an allowed value. Mark exhaustiveness true or false only when stated, otherwise use null.

Represent absent semantic material with null and status `not_supplied`, then add an unresolved question where clarification matters. Preserve conflicts as `unresolved_conflict` without choosing a winner. A one-way condition never establishes its converse.

Do not calculate distributions, validate records, infer definitions from names or samples, or propose remediation.

Return JSON matching the [domain output contract](references/output-schema.json), with every supplied field exactly once and provenance for each entry. The [synthetic shape example](references/schema-example.json) illustrates structure, not executed evidence.

Resources: [input contract](references/input-contract.md) and [worked example](references/worked-example.md).

Run `python scripts/check_output.py artifact.json` from the package directory to check JSON structure against the bundled schema (Python 3 standard library; offline). Exit0 means structural validity,1 contract violations,2 invalid input or unsupported contract. This bounded schema-profile checker reads at most2MiB/50000 nodes/depth100, rejects duplicate keys/nonfinite or oversized numbers, and checks no facts or task judgment. Replay synthetic structural cases with `python evals/run_fixtures.py`; behavioral quality is assessed separately.
