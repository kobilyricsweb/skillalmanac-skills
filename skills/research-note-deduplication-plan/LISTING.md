# research-note-deduplication-plan

Unpublished original; editorial tier: free. No public score or release approval.

## What and when

Use when labeled research notes must be clustered by exact wording, proposition-level equivalence, provenance, relatedness, or contradiction while preserving independent evidence. Do not use for operational-record matching, topic-only collapsing, deciding which conflicting observation is true, or deleting notes.

## Task boundary

user-research-synthesis synthesizes research into insights and cited-deep-research develops sourced research; this clusters supplied notes by exact repetition, paraphrase, shared source and contradiction without synthesizing findings or deleting notes.

## Try the independent synthetic example

Create a deduplication plan for these notes. N1: "The indicator was red," source A, 2026-02-01, quotation. N2: "The indicator showed red," source A, 2026-02-01, paraphrase. N3: "The indicator was green," source B, 2026-02-02, quotation. Rules: identical wording is an exact duplicate; the same proposition in different wording is a paraphrase; same-source paraphrases form shared-source repetition; incompatible color values are contradictions and remain separate; topical similarity alone never permits merging. Preserve all provenance. Deleting notes or deciding which color is true is outside scope.

Observed inline supplied-skill output (tools unavailable; not native discovery), job `factory100_execute_3d2db961425b`:

```text
{"provenance_inventory":[{"note_id":"N1","source_id":"A","date":"2026-02-01","form":"quotation","original_text":"The indicator was red"},{"note_id":"N2","source_id":"A","date":"2026-02-01","form":"paraphrase","original_text":"The indicator showed red"},{"note_id":"N3","source_id":"B","date":"2026-02-02","form":"quotation","original_text":"The indicator was green"}],"clusters":[{"cluster_id":"C1","note_ids":["N1","N2"],"relationship":"paraphrase","evidence_basis":"shared_source_repetition","rationale":"N1 and N2 state the same red-indicator proposition in different wording from source A.","preserved_provenance":[{"note_id":"N1","source_id":"A","date":"2026-02-01","form":"quotation","original_text":"The indicator was red"},{"note_id":"N2","source_id":"A","date":"2026-02-01","form":"paraphrase","original_text":"The indicator showed red"}]},{"cluster_id":"C2","note_ids":["N1","N3"],"relationship":"contradiction","evidence_basis":"conflicting_propositions","rationale":"The notes assign incompatible colors to the same indicator; both remain visible.","preserved_provenance":[{"note_id":"N1","source_id":"A","date":"2026-02-01","form":"quotation","original_text":"The indicator was red"},{"note_id":"N3","source_id":"B","date":"2026-02-02","form":"quotation","original_text":"The indicator was green"}]}],"pair_decisions":[{"note_ids":["N1","N2"],"classification":"paraphrase","rationale":"Same proposition, different wording, same source.","provenance_treatment":"Retain both; shared-source repetition, not independent evidence."},{"note_ids":["N1","N3"],"classification":"contradiction","rationale":"Red and green are incompatible values for the same indicator.","provenance_treatment":"Keep both notes and provenance; do not decide which is true."},{"note_ids":["N2","N3"],"classification":"contradiction","rationale":"The red and green propositions conflict.","provenance_treatment":"Keep both notes and provenance; do not decide which is true."}],"unresolved_comparisons":[],"verification_report":{"all_note_ids_accounted_for":true,"topical_only_merges":[],"provenance_loss_found":false,"contradictions_remain_visible":true,"notes_left_unclustered":[],"issues":[]}}
```

## Verify locally

Run `python evals/run_fixtures.py` from this package directory. See [verification](VERIFICATION.md) for actual results and outstanding gates.
