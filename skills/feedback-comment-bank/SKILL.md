---
name: feedback-comment-bank
description: "Use when evaluators need concise formative comments tied to supplied rubric criteria and observable response patterns. Do not use for customer-service replies, grading absent work, trait judgments, or feedback based on evidence not provided."
license: Apache-2.0
metadata:
  author: Skill Almanac Editorial
  author_model: "gpt-5.6-luna"
  license: Apache-2.0
  version: "0.1.5"
  network: none
---

Create a comment bank from the supplied rubric, observable response patterns, tone guidance, revision opportunities, and length limits. Organize entries by criterion and evidence pattern.

For each entry:

1. Record only what is visibly present in the supplied work.
2. Identify the comparison or judgment required by the rubric.
3. Determine whether the benchmark needed for that judgment was supplied.
4. Give one supported action only when revision is available.
5. Write a `prohibited_overclaim` that explicitly rejects every material overreach relevant to the entry.

The prohibited-overclaim field must be specific, not a generic warning. When applicable, name unsupported grading, trait or ability judgments, causal inferences, and scope reversals such as claiming all evidence is missing when some evidence is supplied.

When a judgment depends on an unstated benchmark—such as the intended logical order—list it in `missing_inputs`. Preserve the observable pattern, but do not invent the benchmark or declare the work incorrect. If revision is explicitly unavailable, set `next_action` to null; that is known information, not a missing input or conflict. Reserve `conflicts` for supplied statements that cannot both hold.

Do not assign a grade unless explicitly requested and supported. Distinguish “not shown in the supplied work” from “missing.” If inputs conflict, preserve the conflict and mark the affected entry provisional.

Return JSON matching the [output schema](references/output-schema.json), using the [input contract](references/input-contract.md) and [worked example](references/worked-example.md). The [synthetic JSON example](references/schema-example.json) illustrates structure only.

Run `python -B scripts/check_output.py artifact.json` for JSON structure only; not source truth or classification coherence.
