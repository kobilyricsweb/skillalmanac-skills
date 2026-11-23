# provenance-labeling-scheme

Unpublished original; editorial tier: free. No public score or release approval.

## What and when

Use when a knowledge collection needs consistent labels for quotation, paraphrase, observation, assumption, or synthesis, including explicit handling of mixed-content segments and provenance metadata. Do not use for classifying decision records, judging truth or credibility, or collapsing mixed provenance into one unsupported label.

## Task boundary

Nearest is decision-evidence-ledger; this standardizes provenance labels across knowledge notes rather than classifying decision records.

## Try the independent synthetic example

Design a provenance scheme from these rules. Allowed labels: quotation, paraphrase, observation, assumption, synthesis. Metadata: quotation requires source_id and location; paraphrase requires source_id; observation requires observer and date; assumption requires analyst and date; synthesis requires component_note_ids. note_id is optional for all labels. Mixed-content rule: split a note into atomic segments. Edge case: a faithful restatement with a source is paraphrase even if the analyst agrees with it. Use tiny synthetic examples, define every allowed label, and verify coverage. Labels describe provenance form, not truth.

Observed inline supplied-skill output (tools unavailable; not native discovery), job `factory100_execute_03fe0d916dda`:

```text
{"label_definitions":[{"label":"quotation","definition":"Wording copied directly from an identified source."},{"label":"paraphrase","definition":"A faithful restatement attributed to an identified source."},{"label":"observation","definition":"A statement recorded as directly observed by a named observer."},{"label":"assumption","definition":"An analyst-supplied premise or inference."},{"label":"synthesis","definition":"Content combined from identified component notes."}],"decision_rules":[{"condition":"Copied wording","label_result":["quotation"],"uncertainty":"resolved","segmentation_action":"not_applicable","handling":"Classify as quotation and check source_id and location."},{"condition":"Faithful source restatement","label_result":["paraphrase"],"uncertainty":"resolved","segmentation_action":"not_applicable","handling":"Classify as paraphrase even if the analyst agrees; check source_id."},{"condition":"Direct observation","label_result":["observation"],"uncertainty":"resolved","segmentation_action":"not_applicable","handling":"Check observer and date."},{"condition":"Analyst premise or inference","label_result":["assumption"],"uncertainty":"resolved","segmentation_action":"not_applicable","handling":"Check analyst and date."},{"condition":"Combination of notes","label_result":["synthesis"],"uncertainty":"resolved","segmentation_action":"not_applicable","handling":"Check component_note_ids."},{"condition":"Mixed provenance note","label_result":[],"uncertainty":"resolved","segmentation_action":"split_atomic_segments","handling":"Split into atomic segments and classify each independently with metadata status."}],"metadata_requirements":[{"label":"quotation","required_fields":["source_id","location"],"optional_fields":["note_id"],"unknown_fields":[]},{"label":"paraphrase","required_fields":["source_id"],"optional_fields":["note_id"],"unknown_fields":[]},{"label":"observation","required_fields":["observer","date"],"optional_fields":["note_id"],"unknown_fields":[]},{"label":"assumption","required_fields":["analyst","date"],"optional_fields":["note_id"],"unknown_fields":[]},{"label":"synthesis","required_fields":["component_note_ids"],"optional_fields":["note_id"],"unknown_fields":[]}],"edge_case_handling":[],"synthetic_examples":[{"content":"The source says ‘Rain began.’","labels":["quotation"],"metadata":{"source_id":"S1","location":"line 1"},"status":"complete"},{"content":"The report restates the result.","labels":["paraphrase"],"metadata":{"source_id":"S1"},"status":"complete"}],"verification_report":{"covered_labels":["quotation","paraphrase","observation","assumption","synthesis"],"missing_definitions":[],"rule_conflicts":[],"metadata_gaps":[],"truth_assessment_performed":false}}
```

## Verify locally

Run `python evals/run_fixtures.py` from this package directory. See [verification](VERIFICATION.md) for actual results and outstanding gates.
