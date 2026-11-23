---
name: assessment-accommodation-translation
description: "Use when an exact approved accommodation statement must become concrete assessment logistics while preserving supplied construct, item content, response demand, scoring, format, and constraints, including partial analysis when baselines are missing. Do not use for eligibility decisions, diagnosis, legal judgments, private profiling, or unapproved assessment changes."
license: Apache-2.0
metadata:
  author: Skill Almanac Editorial
  author_model: "gpt-5.6-luna"
  license: Apache-2.0
  version: "0.1.7"
  network: none
---

# Assessment Accommodation Translation

Translate only exact approved accommodations into assessment logistics.

1. Inventory the supplied baseline separately: construct, format, item content, response demand, scoring target, standard timing, materials, instructions, room, staffing, equipment, and session constraints. Use null for an unknown baseline field and list every missing element separately; one missing element must not conceal another.
2. Map only properties established by each approval. Availability does not prove that a room is quiet, low-distraction, accessible, or private. If an approved property is unconfirmed, mark implementation `unresolved` and name the required confirmation. If supplied equipment, staffing, or session constraints directly prevent the approved change, mark it `conflicting` and identify the compatible authorized setup or decision required.
3. Expose conflicts without substituting another accommodation or silently weakening the approval.
4. Calculate timing from supplied values and show the arithmetic. A missing construct does not prevent a supported timing calculation.
5. Keep two judgments distinct:
   - `unchanged-form comparison`: identify only supplied format, materials, items, response demand, and scoring conditions that can remain unchanged;
   - `construct fidelity`: mark unverified until the construct and every baseline needed to evaluate fidelity are supplied. A scoring target does not by itself establish the assessed construct.
6. Preserve known item content, response demand, scoring target, and format unless the exact approval authorizes a change. Flag any proposal that could alter what is assessed for authorization.

Never claim an unspecified element is preserved. Do not infer diagnosis, eligibility, entitlement, privacy facts, legal compliance, or performance effects.

Return JSON matching the [output schema](references/output-schema.json). Follow the [input contract](references/input-contract.md); the [worked example](references/worked-example.md) and [synthetic example](references/schema-example.json) are illustrative.

Run `python scripts/check_output.py artifact.json` for structural checking only. It does not verify facts or judgment; `python evals/run_fixtures.py` replays synthetic structural cases.
