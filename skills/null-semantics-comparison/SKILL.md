---
name: null-semantics-comparison
description: "Use when multiple supplied sources represent unknown, absent, empty, zero, sentinel, or invalid values differently and an integration needs a declared semantics matrix. Do not use for generic field profiling, undocumented normalization, or deciding equivalence without an explicit source rule."
license: Apache-2.0
metadata:
  author: Skill Almanac Editorial
  author_model: "gpt-5.6-luna"
  license: Apache-2.0
  version: "0.1.6"
  network: none
---

Create a semantics matrix comparing supplied representations of null, absent fields, empty values, zero, sentinels, invalid values, and documented downstream treatment. For every source and field, separate representation from meaning. A token such as `-1` or `null` has only the meaning declared by the input.

Inventory each required category for each source and field. Include declared invalid representations in the matrix as well as in invalid-value handling. Record every undeclared required convention as unresolved; a source having an unknown sentinel does not establish its literal-null semantics.

For each allowed mapping, record the supplied rule as its basis and classify that basis as:

- `transformation`: permits only the stated direction and scope; it does not establish semantic equivalence or a reverse mapping.
- `equivalence`: supports a two-way mapping only where the supplied rule explicitly declares equivalence.

Preserve distinctions the rules do not authorize collapsing. If a value is invalid, report rejection or unresolved handling; do not reinterpret it as unknown. If sources disagree about one representation, show the conflict by source and field. Zero remains known when stated, and absent is not automatically equal to null.

Use synthetic records only to illustrate declared cases. Do not invent a canonical encoding, infer business meaning, or perform conversion.

Return JSON matching the [domain output schema](references/output-schema.json), using the [input contract](references/input-contract.md) and [worked example](references/worked-example.md). The [synthetic JSON example](references/schema-example.json) is illustrative, not executed evidence.

Run `python -B scripts/check_output.py artifact.json` for JSON structure only; not source truth or classification coherence.
