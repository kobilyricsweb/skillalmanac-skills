# cross-reference-ambiguity-map

Unpublished original; editorial tier: free. No public score or release approval.

## What and when

Use when bounded document excerpts contain references such as above, this section, or duplicate headings and the possible target locations must be mapped explicitly. Do not use for judging factual consistency, rewriting prose, modifying navigation, or selecting a target merely because it appears nearest.

## Task boundary

document-consistency-check compares factual statements; this resolves textual navigation references without judging facts.

## Try the independent synthetic example

Map the references using only this inventory. Document D1 sections: S1 heading “Setup,” S2 heading “Checks,” S3 heading “Cleanup.” Excerpt E1 is in D1/S3: “After storage, repeat the checks in section S2.” Occurrence R1 is the phrase “section S2” at D1/S3. Excerpt E2 is in D1/S2: “Record results in the Setup section.” Occurrence R2 is “Setup section” at D1/S2. Select targets only when the supplied ID or unique heading supports them, then verify target existence.

Observed inline supplied-skill output (tools unavailable; not native discovery), job `factory100_execute_102d6cfc38c3`:

```text
{"reference_map":[{"occurrence_id":"R1","source_location":"D1/S3","reference_text":"section S2","candidate_targets":["D1/S2"],"selected_target":"D1/S2","status":"resolved","basis":"The occurrence supplies section ID S2, which uniquely identifies the inventoried section in D1."},{"occurrence_id":"R2","source_location":"D1/S2","reference_text":"Setup section","candidate_targets":["D1/S1"],"selected_target":"D1/S1","status":"resolved","basis":"The supplied heading Setup uniquely identifies D1/S1."}],"ambiguity_report":[],"verification_report":{"all_occurrences_have_status":true,"selected_targets_exist":true,"findings":["Both occurrences have exactly one status.","Selected targets D1/S2 and D1/S1 exist in the inventory.","The map does not judge whether referenced content is true or consistent.","The map does not modify, rewrite, or repair navigation or document text."]}}
```

## Verify locally

Run `python evals/run_fixtures.py` from this package directory. See [verification](VERIFICATION.md) for actual results and outstanding gates.
