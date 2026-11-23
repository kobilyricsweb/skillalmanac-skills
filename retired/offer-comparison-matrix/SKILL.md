---
name: offer-comparison-matrix
description: "Use when comparing supplied internal offers by aligned audience, promise, assets, friction, evidence, and unresolved distinctions. Do not use for competitor research, market or demand estimation, pricing optimization, copywriting, or selecting an unsupported winner."
license: Apache-2.0
metadata:
  author: Skill Almanac Editorial
  author_model: "gpt-5.6-luna"
  license: Apache-2.0
  version: "0.1.1"
  network: none
---

# Offer Comparison Matrix

Create an internal comparison of supplied offers without importing competitor facts, market demand, pricing assumptions, or unsupported performance expectations.

Collect each offer's audience, promise, included assets, proof items and provenance, friction, constraints, comparison questions, and known unknowns.

1. Normalize every offer into the same fields without strengthening or reinterpreting its promise.
2. Align comparison questions and populations before comparing. Preserve audience and eligibility restrictions exactly.
3. Separate assets, promises, friction, evidence, constraints, assumptions, and unknowns.
4. Classify proof as supported only when supplied evidence covers the complete promise; partial when it covers an identified subclaim; not supplied when no proof is supplied; unsupported by supplied record when supplied items do not address the promise; unresolved when provenance or scope conflicts. None means the promise is false.
5. Distinguish observed differences from unknown outcomes. Equal supplied attributes remain indistinguishable on those attributes.
6. Record only explicitly supplied friction and constraints. Identify testable distinctions without predicting results, assigning weights, declaring dominance, or choosing a winner.
7. Keep conflicts, missing authority, and ambiguous scope visible.

Return the JSON artifact required by the output schema: one row per offer, a cross-offer summary of supplied contrasts, evidence gaps, and conflicts, plus outside-scope items. Keep missing values as "not supplied" and make every cell traceable to supplied input or an open question.

Do not add competitors, market data, demand claims, pricing conclusions, ratings, sales claims, legal conclusions, or invented proof. See the input contract and synthetic worked example.

Return JSON matching the [domain output contract](references/output-schema.json); the [synthetic shape example](references/schema-example.json) is an illustration, not executed evidence.

Run `python scripts/check_output.py artifact.json` from the package directory to check JSON structure against the bundled schema (Python 3 standard library; offline). Exit0 means structural validity,1 contract violations,2 invalid input or unsupported contract. This bounded schema-profile checker reads at most2MiB/50000 nodes/depth100, rejects duplicate keys/nonfinite or oversized numbers, and checks no facts or task judgment. Replay synthetic structural cases with `python evals/run_fixtures.py`; behavioral quality is assessed separately.

Resources: [input contract](references/input-contract.md), [worked example](references/worked-example.md).
