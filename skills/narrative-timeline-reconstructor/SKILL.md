---
name: narrative-timeline-reconstructor
description: "Use when unordered notes must become a chronological narrative while preserving exact dates, ranges, relative order, dependencies, overlap, and uncertainty. Do not use for authorization decisions, evidence-status classification, causal inference, or assigning dates and sequence that the notes do not establish."
license: Apache-2.0
metadata:
  author: Skill Almanac Editorial
  author_model: "gpt-5.6-luna"
  license: Apache-2.0
  version: "0.1.1"
  network: none
---

Extract every supplied event into one record with an ID, description, source label, stated time expression, precision, dependencies, conflicts, and placement. Keep exact dates, ranges, approximate periods, relative phrases, and unknown timing distinct. “After E1” establishes only a one-way ordering relation; it supplies neither an interval nor an exact date.

Construct a partial order before writing the narrative scaffold. Add a sequence edge only when an exact non-overlapping time relation or an explicit supplied ordering rule supports it. Overlapping ranges do not establish order. When a range overlaps an exact date, or two events otherwise remain incomparable, group them in the same scaffold segment or explicitly state there that their order is unresolved; paragraph or list position must not imply a sequence the event table denies.

Preserve conflicting notes side by side unless the input supplies a priority rule. Never infer causation from chronology. If IDs, sources, timing, or rules are missing, retain the affected events with provisional or unknown fields and return a partial scaffold.

Before returning, verify that every supplied event appears once, each ordering claim traces to input, scaffold wording and ordering agree with unresolved placements, and no precision was increased. See the [input contract](references/input-contract.md) and [worked example](references/worked-example.md).

Return JSON matching the [domain output schema](references/output-schema.json). The [synthetic JSON example](references/schema-example.json) shows structure only.

Run `python scripts/check_output.py artifact.json` from the package directory for bounded structural validation only. Exit 0 means structural validity, 1 contract violations, and 2 invalid input or unsupported contract; it checks no facts or task judgment. Replay synthetic structural cases with `python evals/run_fixtures.py`; behavioral quality is assessed separately.
