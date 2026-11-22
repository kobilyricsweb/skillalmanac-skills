---
name: nurture-sequence-logic-map
description: "Use when approved messages, audience states, permitted transitions, timing constraints, exclusions, and terminal conditions must be organized into an auditable logic map. Do not use for defining an entire campaign, predicting engagement, sending messages, or inventing entry rules, destinations, or transitions absent from the supplied design."
license: Apache-2.0
metadata:
  author: Skill Almanac Editorial
  author_model: "gpt-5.6-luna"
  license: Apache-2.0
  version: "0.1.8"
  network: none
---

Build a sequence logic map from the supplied entry rule, audience states, approved messages, transition rules, timing constraints, exclusions, and terminal conditions. The input must identify an initial state or explicit entry rule. A state with no incoming transition is not an established start unless the input says so.

For every transition-bearing row, record the source and destination states, path-entry condition, message purpose, prerequisite, transition-rule ID, operative transition condition, timing, and any gap. Keep the rule ID and condition separate from endpoints and path entry. Order steps only when a supplied transition supports that order; never infer a reverse transition, engagement, readiness, intent, or likely response.

Record every supplied exclusion in the exclusions collection with its supplied scope, condition, and effect. An exclusion may also have a terminal row only when the input separately defines it as terminal; do not promote an exclusion into a stop condition.

Represent every supplied terminal condition as an explicit terminal path row. Record its originating state or stated scope, trigger, and stop behavior. Terminal rows have no destination unless one is explicitly supplied, and they prevent later steps on the affected path.

If initial entry is missing, list it as missing and keep affected entry unresolved. A supplied outgoing transition may still be documented without making its source the start. Mark unsupported states as unreachable or requiring design input, messages without a valid transition as unplaced, missing transitions as gaps, and conflicting rules as unresolved.

Verify that every transition row preserves both endpoints, rule ID, and operative condition; every message is placed or explained; every supplied exclusion is recorded; every path has a supplied or unresolved entry; and every terminal condition has a terminal row.

Use the [input contract](references/input-contract.md), [worked example](references/worked-example.md), and [domain output schema](references/output-schema.json). The [synthetic JSON example](references/schema-example.json) illustrates shape only.

Run `python -B scripts/check_output.py artifact.json` for JSON structure only; not source truth or classification coherence.
