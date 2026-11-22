# document-template-field-map

Unpublished original; editorial tier: paid-candidate. No public score or release approval.

## What and when

Use when supplied template placeholders must be bound to candidate source fields under explicit mapping and transformation policies, with conflicts and unknowns exposed. Do not use for defining a general dataset dictionary, filling or sending documents, or inventing sources, conversions, or defaults.

## Task boundary

dataset-field-dictionary-builder defines fields; this binds fields to template placeholders under explicit mapping rules.

## Try the independent synthetic example

Create a binding map only; do not fill a document. Placeholders: {{client_name}} expects text; {{service_date}} expects YYYY-MM-DD; {{fee_usd}} expects USD with two decimals. Candidate values: customer.full_name="Mira Chen", appointment.start="2026-12-03T09:00:00Z", invoice.fee_cents=1250. Policies: map client_name to customer.full_name; map service_date to appointment.start using the UTC date portion; map fee_usd to invoice.fee_cents by dividing by 100 and formatting as USD with two decimals. Missing values remain unknown. No other mappings or transformations are authorized.

Observed inline supplied-skill output (tools unavailable; not native discovery), job `factory100_execute_e9b2f9a02834`:

```text
{"bindings":[{"placeholder":"{{client_name}}","candidate_sources":["customer.full_name"],"selected_source":"customer.full_name","status":"bound","rationale":"Policy explicitly maps client_name to customer.full_name.","transform":null,"expected_format":"text","conflict_note":null,"missing_value_behavior":"Remain unknown if the source value is missing."},{"placeholder":"{{service_date}}","candidate_sources":["appointment.start"],"selected_source":"appointment.start","status":"bound","rationale":"Policy explicitly maps service_date to appointment.start.","transform":"Use the UTC date portion.","expected_format":"YYYY-MM-DD","conflict_note":null,"missing_value_behavior":"Remain unknown if the source value is missing."},{"placeholder":"{{fee_usd}}","candidate_sources":["invoice.fee_cents"],"selected_source":"invoice.fee_cents","status":"bound","rationale":"Policy explicitly maps fee_usd to invoice.fee_cents.","transform":"Divide by 100 and format as USD with two decimals.","expected_format":"USD with two decimals","conflict_note":null,"missing_value_behavior":"Remain unknown if the source value is missing."}],"unresolved":[],"conflicts":[],"implementation_note":"A later authorized filling step may read the selected sources and apply only the listed transforms; this map does not fill a document."}
```

## Verify locally

Run `python evals/run_fixtures.py` from this package directory. See [verification](VERIFICATION.md) for actual results and outstanding gates.
