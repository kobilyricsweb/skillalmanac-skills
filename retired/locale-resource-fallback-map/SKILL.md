---
name: locale-resource-fallback-map
description: "Use when supplied locale inventories and explicit fallback chains must be mapped to determine how resource keys resolve. Do not use for changing application resources, inventing fallback edges, or general localization writing without inventories and declared rules."
license: Apache-2.0
metadata:
  author: "Skill Almanac Editorial"
  version: "0.1.0"
  network: "none"
  license: "Apache-2.0"
  author_model: "gpt-5.6-luna"
---

Treat locale inventories, fallback edges, and terminal missing-key policy as the complete evidence set. For each requested locale and key, first check the locale’s supplied value, then follow only the declared fallback edge in the declared order. Record the locale that supplies the resolved value, the path taken, and any missing steps. If no fallback chain is supplied, keep the key unresolved; do not substitute arbitrary English text or a culturally inferred default.

Produce a per-locale key resolution map with requested locale, key, resolution status, source locale, fallback path, and notes. Use statuses such as local, inherited, missing, ambiguous, cyclic, or unresolved. Detect cycles and conflicting fallback declarations as questions requiring correction. A terminal missing-key policy may describe what the application should do, but it does not create a resource value unless the input explicitly supplies one.

If inventories, chains, or the terminal policy are incomplete, report the missing input and provide a partial map. Preserve exact key spelling and distinguish an empty supplied value from an absent key when the documents do. Do not edit files, select locales by preference, or claim runtime behavior. See the [input contract](references/input-contract.md) and [worked example](references/worked-example.md).

## Machine-checkable artifact contract

Return the artifact as JSON matching the [domain output schema](references/output-schema.json). It specifies the required fields and uncertainty representations; a [synthetic JSON example](references/schema-example.json) shows the shape. Human-readable example tables illustrate equivalent content, not a different contract. Do not treat the example as executed evidence.

Run `python scripts/check_output.py artifact.json` from the package directory to check JSON structure against the bundled schema (Python 3 standard library; offline). Exit0 means structural validity,1 contract violations,2 invalid input or unsupported contract. This bounded schema-profile checker reads at most2MiB/50000 nodes/depth100, rejects duplicate keys/nonfinite or oversized numbers, and checks no facts or task judgment. Replay synthetic structural cases with `python evals/run_fixtures.py`; behavioral quality is assessed separately.
