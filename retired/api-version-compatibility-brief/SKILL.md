---
name: api-version-compatibility-brief
description: "Use when two supplied API specifications must be compared for documented contract changes across paths, methods, fields, status codes, and behavior. Do not use for live endpoint testing, implementation, migration certification, or producing illustrative errors without a version comparison."
license: Apache-2.0
metadata:
  author: Skill Almanac Editorial
  author_model: "gpt-5.6-luna"
  license: Apache-2.0
  version: "0.1.1"
  network: none
---

Compare two supplied version specifications element by element. Inventory paths, methods, request fields, response fields, types, requiredness, status codes, and explicit behavior notes before drawing conclusions. Classify each difference as unchanged, added, removed, renamed, changed, or behaviorally uncertain. Treat names as compatible only when documented types, requiredness, and semantics also match. A similar-looking field is not a rename unless the specifications explicitly say so or provide an unambiguous rename statement.

Produce a compatibility brief organized by contract area, with version-one evidence, version-two evidence, classification, and impact-oriented explanation limited to what the documents support. Separate documented changes from unknown intent. If a path or field appears only once, label it added or removed only relative to the supplied inventories, not as a runtime fact. Preserve status-code changes exactly and do not infer retry, caching, or error semantics absent from the notes.

When inputs conflict internally, report the conflict before comparing versions. When a required section is missing, provide a partial comparison and identify the gap. Do not call endpoints, inspect deployments, generate client code, or claim migration success. See the [input contract](references/input-contract.md) and [worked example](references/worked-example.md).

## Machine-checkable artifact contract

Return the artifact as JSON matching the [domain output schema](references/output-schema.json). It specifies the required fields and uncertainty representations; a [synthetic JSON example](references/schema-example.json) shows the shape. Human-readable example tables illustrate equivalent content, not a different contract. Do not treat the example as executed evidence.

Run `python scripts/check_output.py artifact.json` from the package directory to check JSON structure against the bundled schema (Python 3 standard library; offline). Exit0 means structural validity,1 contract violations,2 invalid input or unsupported contract. This bounded schema-profile checker reads at most2MiB/50000 nodes/depth100, rejects duplicate keys/nonfinite or oversized numbers, and checks no facts or task judgment. Replay synthetic structural cases with `python evals/run_fixtures.py`; behavioral quality is assessed separately.
