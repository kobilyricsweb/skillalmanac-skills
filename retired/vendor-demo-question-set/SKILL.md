---
name: vendor-demo-question-set
description: "Use when turning supplied requirements, participants, evidence needs, and time limits into a proposed vendor demonstration script with explicit timing uncertainty. Do not use for vendor rankings, market research, procurement scoring, contacting vendors, or claims that any capability was observed or validated."
license: Apache-2.0
metadata:
  author: Skill Almanac Editorial
  author_model: "gpt-5.6-luna"
  license: Apache-2.0
  version: "0.1.3"
  network: none
---

# Vendor Demo Question Set

Create a proposed demonstration agenda from supplied requirements. It is a request-and-capture script, not product evaluation or observed proof.

1. Preserve requirement IDs and meaning.
2. Prioritize only from supplied priority; if absent, state the neutral order or gap.
3. For each requirement, specify a live action, observable result, evidence request, and follow-up question.
4. Keep supplied segment times binding. Label planning allocations provisional and separate from observed timing.
5. Mark requirements non-demonstrable when a required action, participant, data, or condition is unavailable. A missing necessary participant is non-demonstrable for this session; future scheduling is separate.
6. Keep mandatory segments and supplied times. If requested segments exceed the cap, provide a feasible in-cap agenda where possible plus explicit deferred or overflow items. If mandatory segments alone exceed the cap, state that no feasible agenda exists.
7. When any requested duration is unknown, leave affected duration totals and feasibility conclusions null and identify the missing timing input; do not invent allocations. Use provisional allocations only when supplied or explicitly requested, label them provisional, and calculate only from those allocations.
8. Distinguish in-cap planned minutes, total requested minutes, arithmetic overflow, deferred minutes, and whether full scope and the selected agenda fit.

Return JSON matching the [domain output contract](references/output-schema.json), including objective, assumptions, timed script, traceability, evidence requests, follow-up questions, non-demonstrable items, overflow arithmetic, and verification. The [synthetic shape example](references/schema-example.json) is illustrative, not executed evidence.

Resources: [input contract](references/input-contract.md), [worked example](references/worked-example.md).

Do not research, rank, score, contact vendors, validate claims, or claim demonstration results.

Run `python scripts/check_output.py artifact.json` from the package directory to check JSON structure against the bundled schema (Python 3 standard library; offline). Exit0 means structural validity,1 contract violations,2 invalid input or unsupported contract. This bounded schema-profile checker reads at most2MiB/50000 nodes/depth100, rejects duplicate keys/nonfinite or oversized numbers, and checks no facts or task judgment. Replay synthetic structural cases with `python evals/run_fixtures.py`; behavioral quality is assessed separately.
