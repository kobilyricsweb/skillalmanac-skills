# Input contract

Provide:

- `offers`: two or more named offers.
- For each offer: `audience`, `promise`, `included_assets`, `proof_items`, `friction`, and `constraints`.
- For each proof item, provide its supplied source, owner, date, or say `not supplied`.
- `comparison_questions`: the internal distinctions the team wants examined.
- `known_unknowns`: facts explicitly unavailable or awaiting confirmation.

Decision rules:

- Compare only supplied offer details.
- supported: supplied proof covers the complete promise; partial: it directly covers an identified subclaim; not supplied: no proof item is supplied; unsupported by supplied record: available items do not address the promise; unresolved: conflicting or ambiguous provenance/scope prevents classification. None means the promise is false.
- Preserve audience and eligibility restrictions exactly.
- Treat absent information as unknown, not negative evidence.
- Conflicts remain visible until an owner resolves them.

Boundary:

This contract supports internal offer comparison. It does not authorize competitor research, market or demand claims, pricing recommendations, campaign planning, copywriting, experiment results, or invented proof.
