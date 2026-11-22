# section-heading-coverage-check

Unpublished original; editorial tier: free. No public score or release approval.

## What and when

Use when auditing whether each heading’s promise and each required topic are supported by directly assigned document content, while tracking descendant coverage separately. Do not use for drafting missing evidence, planning updates, requirements traceability, or constructing an outline from source notes.

## Task boundary

technical-docs-writer creates and audits documentation for structural and operational quality. section-heading-coverage-check narrowly tests whether each heading's semantic promise and each required topic are supported by directly assigned body content, keeping descendant support separate and proposing only bounded repairs.

## Try the independent synthetic example

Audit this complete synthetic document in heading order. Hierarchy: H1 is level 1; H1.1 is level 2. H1 heading: “Setup and Storage,” not protected. H1 content: “Connect the cable before use.” H1.1 heading: “Storage Temperature,” protected. H1.1 content: “Store the unit between 10°C and 20°C.” Required topic: storage temperature. For each heading, state its promise, supporting content, coverage status, missing elements, overbreadth, protection, and bounded repair options. Preserve the protected heading exactly.

Observed inline supplied-skill output (tools unavailable; not native discovery), job `aggregate_isolated_a0d0c4ef61bf9b9a`:

```text
{"sections":[{"row_locator":"heading-1","section_id":"H1","heading":"Setup and Storage,","hierarchy_level":1,"protected":false,"promise":["setup","storage"],"element_assessments":[{"promised_element":"setup","status":"covered","direct_supporting_content":["‘Connect the cable before use.’ directly supports setup."],"missing_or_conflicting_evidence":[]},{"promised_element":"storage","status":"absent","direct_supporting_content":[],"missing_or_conflicting_evidence":["The complete content directly assigned to H1 supplies no storage information."]}],"supporting_content":["‘Connect the cable before use.’ directly supports setup."],"coverage_status":"partial","missing_elements":["storage"],"overbreadth":"The heading promises storage, but H1’s directly assigned content covers only setup.","descendant_notes":["heading-2 (H1.1) supplies storage-temperature information, but descendant content is not direct support for H1."],"repair_options":["Narrow the unprotected heading to ‘Setup.’","Reposition the supplied storage-temperature content into H1 if that placement matches the intended structure.","Propose adding storage content directly beneath H1 once supported content is supplied."]},{"row_locator":"heading-2","section_id":"H1.1","heading":"Storage Temperature,","hierarchy_level":2,"protected":true,"promise":["storage temperature"],"element_assessments":[{"promised_element":"storage temperature","status":"covered","direct_supporting_content":["‘Store the unit between 10°C and 20°C.’ directly states the storage-temperature range."],"missing_or_conflicting_evidence":[]}],"supporting_content":["‘Store the unit between 10°C and 20°C.’ directly states the storage-temperature range."],"coverage_status":"covered","missing_elements":[],"overbreadth":null,"descendant_notes":[],"repair_options":[]}],"required_topic_assessments":[{"required_topic":"storage temperature","status":"covered","supporting_row_locators":["heading-2"],"supporting_section_ids":["H1.1"],"direct_supporting_content":["‘Store the unit between 10°C and 20°C.’ directly states the storage-temperature range."],"appropriate_heading_status":"yes","missing_or_conflicting_evidence":[]}],"input_limitations":[],"unresolved_ambiguities":[]}
```

## Verify locally

Run `python evals/run_fixtures.py` from this package directory. See [verification](VERIFICATION.md) for actual results and outstanding gates.
