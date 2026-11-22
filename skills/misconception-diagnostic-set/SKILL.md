---
name: misconception-diagnostic-set
description: "Use when an instructor needs short probes that discriminate among explicitly supplied misconceptions and ordinary mistakes under a supplied governing rule. Do not use for general quiz generation, diagnosing a learner from one response, or resolving conflicting authoritative rules without stated precedence."
license: Apache-2.0
metadata:
  author: Skill Almanac Editorial
  author_model: "gpt-5.6-luna"
  license: Apache-2.0
  version: "0.1.9"
  network: none
---

# Misconception Diagnostic Set

Construct a compact diagnostic set from the supplied learning objective, named misconceptions, governing correct rule, response format, and desired item count. Use only supplied misconceptions.

Validate all five inputs before writing items. The desired count must be a nonnegative integer. If any required input is missing or incompatible, withhold every item that cannot be scoped, targeted, keyed, formatted, or counted from supplied inputs; list the problem in `missing_inputs`. For an absent or non-integer count, set `requested_count` to `null` rather than rounding or inventing a value.

A misconception’s disagreement with the governing rule is the relationship to probe, not a conflict. Record a conflict only when authoritative governing inputs prescribe incompatible keys or have unclear precedence. Preserve conflicting rules, produce no dependent item, key, or distractor interpretation, and request clarification of authority or precedence.

For each supported item:

1. Write the complete learner-facing prompt in the requested format.
2. Key it using the supplied governing rule.
3. Name the targeted misconception and describe distractor reasoning cautiously.
4. List plausible alternative explanations, what the response cannot distinguish, and a follow-up probe when ambiguity remains.

When the requested count can cover all supplied misconceptions, distribute probes so each misconception is tested unless a source-grounded reason prevents it. Additional items may revisit a misconception only through a materially distinct supported decision. Declare a shortfall only when another item would duplicate a decision, invent content, or exceed supplied scope; report requested and delivered counts and the specific reason.

Set `status` to `conflicted` for unresolved governing-rule conflicts. Otherwise use `incomplete` when a required input is missing or incompatible. Use `complete` when all required inputs are compatible and all supportable items are delivered, including a documented source-grounded shortfall.

Treat responses as evidence to investigate, never as diagnosis. Always state this in `interpretation_limits`.

Return exactly one JSON document matching [the output schema](references/output-schema.json). Consult the [input contract](references/input-contract.md), [worked example](references/worked-example.md), and [synthetic example](references/schema-example.json).

Run `python -B scripts/check_output.py artifact.json` for structure only; it does not establish source truth or classification coherence.
