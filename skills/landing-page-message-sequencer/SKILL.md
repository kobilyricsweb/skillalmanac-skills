---
name: landing-page-message-sequencer
description: "Use when ordering approved page messages by visitor question, supplied evidence and permitted call to action. Do not use for interface code, campaign planning, conversion predictions, or CTA details that are not supplied or authorized."
license: Apache-2.0
metadata:
  author: Skill Almanac Editorial
  author_model: "gpt-5.6-luna"
  license: Apache-2.0
  version: "0.1.1"
  network: none
---

# Landing Page Message Sequencer

## Purpose
Turn an approved set of messages into a focused, section-by-section landing-page content sequence. The artifact explains what question each section answers, which approved claim it uses, what supplied evidence supports it, and which authorized call to action follows. It does not design the page or forecast performance.

## Required inputs
Provide one audience, the page objective, approved messages, evidence assets with exact descriptions or locations, CTA authority and destination, explicit restrictions, and any claims that are provisional or prohibited. Include the intended visitor questions if known. See [input contract](references/input-contract.md).

## Decision workflow
1. Normalize every message into a stable identifier without rewriting its factual meaning.
2. Classify each message as audience context, problem, approved promise, mechanism, evidence, objection response, qualification, CTA, or unresolved.
3. Order sections by the visitor’s supplied decision questions: orientation, relevance, understanding, confidence, qualification, and action. Use only the stages supported by the input.
4. Attach each claim to the exact supplied evidence asset, or mark the evidence gap. Do not treat an asset as stronger than its description.
5. Check that the CTA wording, destination, audience, authority status, and prerequisites are authorized for the audience and objective. If any required detail is missing or conflicting, preserve the supplied details and mark the CTA unresolved.
6. Reject or quarantine claims that exceed supplied evidence; preserve their wording in a gap note rather than converting them into safer-sounding facts.
7. Record dependencies, such as a qualification section required before the CTA, without adding copy or layout instructions.

## Output
Return an ordered table with section number, visitor question, message IDs, approved claim, evidence asset and location, a structured CTA record containing wording, destination, audience, authority status, and prerequisites where supplied, CTA status, restrictions, and unresolved gaps. Add a brief sequence rationale based only on supplied visitor questions and constraints. Include a rejection log for unsupported or unauthorized items.

## Missing or conflicting inputs
Use “not supplied” for absent evidence, audience, authority, or destination. If approved messages conflict, show both IDs and pause their placement as unresolved. Do not select a preferred claim or invent CTA details silently.

## Limits and verification
No HTML, UI specification, SEO advice, conversion prediction, campaign plan, new claims, invented proof, or CTA invention. Verify every placed claim has an approved ID, every evidence reference matches the supplied description, and every CTA field preserves supplied authority and destination information. See the [synthetic worked example](references/worked-example.md).

## Machine-checkable artifact contract

Return the artifact as JSON matching the [domain output schema](references/output-schema.json). It specifies the required fields and uncertainty representations; a [synthetic JSON example](references/schema-example.json) shows the shape. Human-readable example tables illustrate equivalent content, not a different contract. Do not treat the example as executed evidence.

Run `python scripts/check_output.py artifact.json` from the package directory to check JSON structure against the bundled schema (Python 3 standard library; offline). Exit0 means structural validity,1 contract violations,2 invalid input or unsupported contract. This bounded schema-profile checker reads at most2MiB/50000 nodes/depth100, rejects duplicate keys/nonfinite or oversized numbers, and checks no facts or task judgment. Replay synthetic structural cases with `python evals/run_fixtures.py`; behavioral quality is assessed separately.
