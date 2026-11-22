# terminology-consistency-editor

Unpublished original; editorial tier: free. No public score or release approval.

## What and when

Use when applying a supplied preferred glossary to editable prose with location-specific term changes. Do not use for factual reconciliation across documents or modifying quotations and code identifiers.

## Task boundary

natural-prose-editor edits style, document-consistency-check compares facts and abbreviation-disambiguation-guide distinguishes expansions; this proposes location-specific term replacements under a supplied glossary.

## Try the independent synthetic example

Apply the supplied glossary to this bounded prose. P1: “The client portal shows invoices. Open the customer portal to download one.” P2: “A customer is a person who buys a service.” Glossary: concept account website—preferred “client portal”, no permitted variants; concept purchasing person—preferred “customer”, permitted variant “buyer”. Rule: replace only when local meaning matches the glossary concept. No text is protected.

Observed inline supplied-skill output (tools unavailable; not native discovery), job `factory100_execute_d688a11ec810`:

```text
{"scope":{"locations":["P1","P2"],"protected_text":[],"rules":["Replace only where local meaning matches the glossary concept."]},"candidate_terms":[{"location":"P1 sentence 1","term":"client portal","concept":"account website","status":"preferred"},{"location":"P1 sentence 2","term":"customer portal","concept":"account website","status":"replaceable_variant"},{"location":"P2","term":"customer","concept":"purchasing person","status":"preferred"}],"preferred_terms":[{"concept":"account website","preferred_term":"client portal","permitted_variants":[],"basis":"Supplied glossary."},{"concept":"purchasing person","preferred_term":"customer","permitted_variants":["buyer"],"basis":"Supplied glossary."}],"replacements":[{"location":"P1 sentence 2","current_text":"customer portal","proposed_text":"client portal","status":"proposed","preservation_note":"Same account-website meaning; unprotected prose."}],"unresolved_distinctions":[],"verification":{"ordinary_replacements_glossary_supported":true,"protected_text_changed":false,"code_changes_executed":false,"unknowns":[]}}
```

## Verify locally

Run `python evals/run_fixtures.py` from this package directory. See [verification](VERIFICATION.md) for actual results and outstanding gates.
