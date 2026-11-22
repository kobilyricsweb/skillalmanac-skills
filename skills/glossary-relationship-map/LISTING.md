# glossary-relationship-map

Unpublished original; editorial tier: free. No public score or release approval.

## What and when

Use when supplied glossary definitions and approved relationship statements must be modeled as broader, narrower, related, or explicitly distinct concepts. Do not use for terminology replacement in prose, linguistic-similarity matching, or factual ontology design without approved relationship evidence.

## Task boundary

Nearest is terminology-consistency-editor; this models conceptual relationships rather than replacing nonpreferred terms in prose.

## Try the independent synthetic example

Build a glossary relationship map. Entries: T1 “Container: an object that can hold items”; T2 “Box: a container with rigid sides”; T3 “Label: a marker attached to an item.” Approved statements: T1 is broader than T2; T2 is related to T3. Hierarchy rules: allowed relations are broader-than, narrower-than, related-to, and distinct-from; broader-than mechanically permits the inverse narrower-than; related-to is symmetric; transitive inference is not allowed. Prohibited equivalence: T2 must not be equivalent to T3. Return the relationship map, prohibited equivalences, unresolved links, and verification report.

Observed inline supplied-skill output (tools unavailable; not native discovery), job `factory100_execute_abba688f7a4c`:

```text
{"relationship_map":[{"source_term":"T1","target_term":"T2","relation_type":"broader-than","direction":"directed","support":"Approved: T1 is broader than T2.","status":"supported"},{"source_term":"T2","target_term":"T1","relation_type":"narrower-than","direction":"directed","support":"Inverse permitted by the broader-than rule.","status":"supported"},{"source_term":"T2","target_term":"T3","relation_type":"related-to","direction":"symmetric","support":"Approved: T2 is related to T3.","status":"supported"},{"source_term":"T3","target_term":"T2","relation_type":"related-to","direction":"symmetric","support":"Symmetry permitted for related-to.","status":"supported"}],"prohibited_equivalences":[{"terms":["T2","T3"],"support":"Supplied prohibition: T2 must not be equivalent to T3.","status":"prohibited"}],"unresolved_links":[{"terms":["T1","T3"],"issue":"Multi-edge path T1 broader-than T2 related-to T3 has no authorized transitive inference.","needed_input":"A direct T1-T3 statement or an authorizing inference rule."}],"verification_report":{"all_edges_supported":true,"all_prohibitions_preserved":true,"inverse_handling":"Only the declared broader-than inverse and related-to symmetry were added; no transitive edge was added.","unlinked_terms":[],"issues":[]}}
```

## Verify locally

Run `python evals/run_fixtures.py` from this package directory. See [verification](VERIFICATION.md) for actual results and outstanding gates.
