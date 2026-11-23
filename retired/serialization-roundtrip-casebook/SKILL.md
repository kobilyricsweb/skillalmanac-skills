---
name: serialization-roundtrip-casebook
description: "Use when creating offline serialization roundtrip cases from supplied type rules, format, omission defaults, normalization rules, equality semantics, and synthetic representative values. Do not use for CLI help examples, undocumented transformations, runtime serializer testing, or claiming byte equality when only semantic equality is specified."
license: Apache-2.0
metadata:
  author: Skill Almanac Editorial
  author_model: "gpt-5.6-luna"
  license: Apache-2.0
  version: "0.1.4"
  network: none
---

Create a casebook using only the supplied type rules, serialization format, omission defaults, normalization rules, equality semantics, and representative synthetic values. For each case, record the source value, serialized form, reconstructed value, semantic equality, byte equality, information loss, and ambiguity notes. Cover only boundaries explicitly distinguished by the inputs, such as missing versus empty or omitted versus defaulted.

Assess semantic and byte equality independently as `equal`, `not_equal`, or `unresolved`. Semantic equality depends on the supplied value rules. Byte equality requires exact serialized bytes and encoding, or a complete canonicalization rule; a format name alone is insufficient. Do not invent defaults, escaping, ordering, precision, timezone behavior, equality semantics, or reconstruction rules.

If a transformation is one-way, identify the lost information and do not claim reconstruction of the original. Preserve conflicting rules and mark affected results unresolved. If representative values are absent, report incomplete coverage rather than inventing values.

Verify each result by applying only documented transformations. The verification statement must explicitly say that no runtime serializer was executed and no implementation change was made or proposed, unless the user supplied contrary facts. State coverage and unresolved ambiguities.

Use the [input contract](references/input-contract.md) and [worked example](references/worked-example.md). Return JSON matching the [domain output schema](references/output-schema.json); the [synthetic example](references/schema-example.json) illustrates structure and is not executed evidence.

Run `python scripts/check_output.py artifact.json` from the package directory for offline structural checking. Structural validity does not establish behavioral correctness.
