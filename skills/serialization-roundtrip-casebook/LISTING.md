# serialization-roundtrip-casebook

Unpublished original; editorial tier: paid-candidate. No public score or release approval.

## What and when

Use when creating offline serialization roundtrip cases from supplied type rules, format, omission defaults, normalization rules, equality semantics, and synthetic representative values. Do not use for CLI help examples, undocumented transformations, runtime serializer testing, or claiming byte equality when only semantic equality is specified.

## Task boundary

Nearest is cli-help-example-designer; this creates data roundtrip cases rather than command-line usage examples.

## Try the independent synthetic example

Create an offline roundtrip casebook from these rules. Type: a record with required string id and optional string note. Format: JSON text encoded as UTF-8. Fields serialize in the order id, then note. An absent note is omitted; an empty note is serialized as "note":"". Reconstruction leaves an omitted note absent. Semantic equality compares field presence and string values. Byte equality may be assessed only against the exact serialized text supplied here. Cases: A source {id:"r1", note absent} has serialized text {"id":"r1"}; B source {id:"r2", note:""} has serialized text {"id":"r2","note":""}. Produce the casebook, information-loss assessment, ambiguity notes, coverage, and verification statement. Do not run a serializer or propose implementation changes.

Observed inline supplied-skill output (tools unavailable; not native discovery), job `factory100_execute_a791ca95332f`:

```text
{"cases":[{"case_id":"A","source_value":{"id":"r1"},"serialized_form":"{\"id\":\"r1\"}","reconstructed_value":{"id":"r1"},"semantic_equality":"equal","byte_equality":"equal","information_loss":"none","ambiguity_notes":[]},{"case_id":"B","source_value":{"id":"r2","note":""},"serialized_form":"{\"id\":\"r2\",\"note\":\"\"}","reconstructed_value":{"id":"r2","note":""},"semantic_equality":"equal","byte_equality":"equal","information_loss":"none","ambiguity_notes":[]}],"coverage":"Covers omitted optional note versus explicitly empty note, supplied field order, UTF-8 encoding, and exact serialized texts.","unresolved_ambiguities":[],"verification_statement":"Applying only the supplied omission, preservation, ordering, reconstruction, equality, exact-text, and UTF-8 rules yields these results. No runtime serializer was executed, and no implementation change was made or proposed."}
```

## Verify locally

Run `python evals/run_fixtures.py` from this package directory. See [verification](VERIFICATION.md) for actual results and outstanding gates.
