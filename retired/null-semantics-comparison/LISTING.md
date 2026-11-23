# null-semantics-comparison

Unpublished original; editorial tier: paid-candidate. No public score or release approval.

## What and when

Use when multiple supplied sources represent unknown, absent, empty, zero, sentinel, or invalid values differently and an integration needs a declared semantics matrix. Do not use for generic field profiling, undocumented normalization, or deciding equivalence without an explicit source rule.

## Task boundary

Nearest is dataset-field-profiler; this compares declared missing-value semantics rather than observed JSON types.

## Try the independent synthetic example

Compare semantics for field seats, defined as the known count of available seats. Source A: null=unknown, absent=not collected, empty string=invalid, 0=known none, sentinel "N/A"=not applicable, negative=invalid. Source B: "UNK"=unknown sentinel, absent=not provided, empty string=invalid, 0=known none, negative=invalid. Rule: for seats only, A null maps to B "UNK" in one direction; reject empty strings and negative values. Samples: A {seats:null}, A {}, A {seats:"N/A"}, B {seats:0}. Return the matrix, allowed mapping, preserved distinctions, invalid handling, downstream treatment, and unresolved conflicts.

Observed inline supplied-skill output (tools unavailable; not native discovery), job `factory100_execute_249a02b13374`:

```text
{"status":"partial","semantics_matrix":[{"source":"A","field":"seats","representation":"null","meaning":"unknown","scope":"seats only","certainty":"declared"},{"source":"A","field":"seats","representation":"absent","meaning":"not collected","scope":"seats only","certainty":"declared"},{"source":"A","field":"seats","representation":"empty string","meaning":"invalid","scope":"seats only","certainty":"declared"},{"source":"A","field":"seats","representation":"0","meaning":"known none","scope":"seats only","certainty":"declared"},{"source":"A","field":"seats","representation":"N/A","meaning":"not applicable","scope":"seats only","certainty":"declared"},{"source":"A","field":"seats","representation":"negative","meaning":"invalid","scope":"seats only","certainty":"declared"},{"source":"B","field":"seats","representation":"UNK","meaning":"unknown sentinel","scope":"seats only","certainty":"declared"},{"source":"B","field":"seats","representation":"absent","meaning":"not provided","scope":"seats only","certainty":"declared"},{"source":"B","field":"seats","representation":"empty string","meaning":"invalid","scope":"seats only","certainty":"declared"},{"source":"B","field":"seats","representation":"0","meaning":"known none","scope":"seats only","certainty":"declared"},{"source":"B","field":"seats","representation":"negative","meaning":"invalid","scope":"seats only","certainty":"declared"},{"source":"B","field":"seats","representation":"N/A","meaning":"not declared","scope":"seats only","certainty":"unknown"}],"allowed_mappings":[{"from_source":"A","from_representation":"null","to_source":"B","to_representation":"UNK","field_scope":"seats only","direction":"one-way","rule_kind":"transformation","rule_basis":"Supplied rule allows A null to B UNK for seats only."}],"preserved_distinctions":["A absent/not collected remains distinct from B absent/not provided and from unknown.","A N/A remains not applicable and is not mapped to unknown.","0 remains known none."],"invalid_value_handling":["Reject empty strings and negative values; do not reinterpret them as unknown."],"downstream_treatment":["Apply only the declared A-to-B seats transformation.","Treat B 0 as a known zero count.","Do not infer treatment for B literal null or N/A."],"unresolved_conflicts":["A and B assign different meanings to absence.","B has no declared meaning for literal null or N/A.","No reverse mapping is authorized."]}
```

## Verify locally

Run `python evals/run_fixtures.py` from this package directory. See [verification](VERIFICATION.md) for actual results and outstanding gates.
