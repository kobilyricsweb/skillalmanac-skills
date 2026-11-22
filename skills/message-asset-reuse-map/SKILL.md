---
name: message-asset-reuse-map
description: "Use when mapping approved messages to exact locations in supplied assets with audience and reuse restrictions. Do not use for general factual verification, campaign plans or promotional-variant validation."
license: Apache-2.0
metadata:
  author: "Skill Almanac Editorial"
  version: "0.1.0"
  network: "none"
  license: "Apache-2.0"
  author_model: "gpt-5.6-luna"
---

# Message-Asset Reuse Map

## Purpose
Show where approved messages can be reused across existing assets without inventing proof, changing audience restrictions, or implying that an asset validates a claim beyond its supplied description. The artifact helps teams identify usable placements, blocked placements, and concrete adaptation requests.

## Required inputs
Provide approved message IDs with exact wording, intended audience, context, restrictions, and authorized use; asset IDs with exact summaries, locations, formats, audiences, and contexts; and any explicit reuse rules. Include known gaps, permissions, owners, and requested channels when supplied. See [input contract](references/input-contract.md).

## Decision workflow
1. Normalize message and asset IDs while preserving exact wording and restrictions.
2. Extract each message’s audience, context, claim type, required support, and prohibited use.
3. Extract each asset’s supplied content, location, audience, context, format, stated evidence, and limitations.
4. Match a message to an asset only when audience and context are compatible and the asset’s description permits the proposed use. Record the exact location.
5. Distinguish direct reuse, conditional reuse, adaptation request, and unsupported placement. Conditional reuse must name the missing confirmation or restriction.
6. Keep an approved message with no suitable asset visible as an unpaired message. Keep an asset with no compatible message visible as unused or restricted.
7. Write adaptation requests as specific source or permission needs—for example, request a crop, transcript, audience confirmation, or missing date—without drafting a new claim.

## Output
Return a matrix with message ID, exact message, audience, context, matched asset ID, exact location, reuse status, allowed placement, restriction, and adaptation request. Add separate lists for unpaired messages, unused assets, blocked placements, and unresolved authority. Preserve one-to-many and many-to-one relationships explicitly.

## Missing or conflicting inputs
Use “not supplied” for absent location, audience, permission, or context. If a message or asset has conflicting restrictions, show the conflict and block the placement until resolved. Do not infer compatibility from format alone.

## Limits and verification
Do not assess the ultimate truth of claims, invent proof, create campaign plans, write variants, predict results, or validate promotions. Verify every placement cites an exact supplied asset location and preserves the message’s audience and context. See the [synthetic worked example](references/worked-example.md).

## Machine-checkable artifact contract

Return the artifact as JSON matching the [domain output schema](references/output-schema.json). It specifies the required fields and uncertainty representations; a [synthetic JSON example](references/schema-example.json) shows the shape. Human-readable example tables illustrate equivalent content, not a different contract. Do not treat the example as executed evidence.

Run `python scripts/check_output.py artifact.json` from the package directory to check JSON structure against the bundled schema (Python 3 standard library; offline). Exit0 means structural validity,1 contract violations,2 invalid input or unsupported contract. This bounded schema-profile checker reads at most2MiB/50000 nodes/depth100, rejects duplicate keys/nonfinite or oversized numbers, and checks no facts or task judgment. Replay synthetic structural cases with `python evals/run_fixtures.py`; behavioral quality is assessed separately.
