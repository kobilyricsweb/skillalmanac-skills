---
name: event-promotion-asset-plan
description: "Use when turning confirmed event facts, channels, permissions, and milestones into a bounded promotional asset plan. Do not use for overall campaign strategy, invented event details, publishing assets, or registration assumptions unsupported by the supplied event process."
license: Apache-2.0
metadata:
  author: Skill Almanac Editorial
  author_model: "gpt-5.6-luna"
  license: Apache-2.0
  version: "0.1.1"
  network: none
---

Use only the supplied event facts, approved audience, confirmed schedule, speaker permissions, channel list, and production milestones. Create an asset plan with one row per proposed artifact. Include artifact name, purpose, audience, required facts, dependency, deadline relation, permitted speaker or event references, and content boundary. Tie every date, speaker, benefit, and call to action to a confirmed input. Mark unconfirmed details as placeholders or open questions; never convert them into promotional promises. Apply speaker permissions separately by channel and do not generalize web permission to email, print, or paid media. Express deadlines relative to supplied milestones when no exact production date is provided. If the requested asset set exceeds the supplied facts or channels, identify the gap and propose a bounded placeholder rather than filling it. If inputs conflict, show the conflict and keep both statements visible until resolved. Treat registration facts and milestones as applicable only when the supplied event process or proposed artifact depends on registration; if registration is explicitly not applicable, record that, and otherwise ask whether it applies without automatically blocking unrelated assets. Report a short dependency summary and a list of assets blocked by missing confirmation. Distinguish a content plan from authorization to produce, approve, distribute, or publish. Do not invent schedule, speakers, benefits, registration terms, audience traits, performance targets, or channel availability.

See the [input contract](references/input-contract.md) and [worked example](references/worked-example.md).

## Machine-checkable artifact contract

Return the artifact as JSON matching the [domain output schema](references/output-schema.json). It specifies the required fields and uncertainty representations; a [synthetic JSON example](references/schema-example.json) shows the shape. Human-readable example tables illustrate equivalent content, not a different contract. Do not treat the example as executed evidence.

Run `python scripts/check_output.py artifact.json` from the package directory to check JSON structure against the bundled schema (Python 3 standard library; offline). Exit0 means structural validity,1 contract violations,2 invalid input or unsupported contract. This bounded schema-profile checker reads at most2MiB/50000 nodes/depth100, rejects duplicate keys/nonfinite or oversized numbers, and checks no facts or task judgment. Replay synthetic structural cases with `python evals/run_fixtures.py`; behavioral quality is assessed separately.
