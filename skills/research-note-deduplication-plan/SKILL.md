---
name: research-note-deduplication-plan
description: "Use when labeled research notes must be clustered by exact wording, proposition-level equivalence, provenance, relatedness, or contradiction while preserving independent evidence. Do not use for operational-record matching, topic-only collapsing, deciding which conflicting observation is true, or deleting notes."
license: Apache-2.0
metadata:
  author: Skill Almanac Editorial
  author_model: "gpt-5.6-luna"
  license: Apache-2.0
  version: "0.1.5"
  network: none
---

Create a deduplication plan from labeled notes, source IDs, dates, quotation or paraphrase markers, and explicit comparison rules. First inventory every note with its complete provenance. Then identify exact duplicates, paraphrases supported by the same source, related notes that share a topic without asserting the same proposition, and contradictions where propositions or values conflict. Never merge notes solely because they discuss the same subject.

Preserve every note ID, source ID, supplied date, form marker, and original wording in the provenance inventory whether the note is clustered, unclustered, or part of an unresolved comparison. Treat multiple notes from one source as shared-source repetition rather than independent corroboration. Keep notes from different sources separate unless supplied rules explicitly permit consolidation, and retain contradictory wording even when one note appears more recent. Dates are optional unless the supplied rules make them material. If metadata, proposition boundaries, or comparison rules required for a particular decision are missing, leave that comparison unresolved; irrelevant missing metadata does not block a decision.

A relationship cluster must contain at least two unique notes. Do not create a singleton cluster; list an otherwise unclustered note in the verification report instead.

Return the provenance inventory, clusters, pair decisions, unresolved comparisons, and verification report. Verify that every note is inventoried, every cluster has a rationale, no provenance is lost, and contradiction labels are not used for mere topical difference. Do not delete notes or decide which conflicting proposition is true.

See the [input contract](references/input-contract.md) and [worked example](references/worked-example.md).

## Machine-checkable artifact contract

Return JSON matching the [domain output schema](references/output-schema.json). The [synthetic JSON example](references/schema-example.json) illustrates the required shape only; neither resource verifies factual accuracy or task judgment.


Run `python -B scripts/check_output.py artifact.json` for JSON structure only; not source truth or classification coherence.
