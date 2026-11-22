# Worked Example

Synthetic example only. Input fields: customer_id,status,closed_at. Sources: S1 says customer_id
is the account identifier; S2 says status is active or closed; S3 says closed_at is empty for
active accounts; S4 says empty may also mean not recorded. Sample: customer_id=1042,status=active,
closed_at="". No meaning of a non-empty closed_at or exhaustive type policy is supplied.

|Field|Source wording|Normalized definition|Expected type|Allowed values|Null semantics|Blank/empty semantics|Observation|Open question|Provenance|
|---|---|---|---|---|---|---|---|---|---|
|customer_id|account identifier|Identifier for an account|not supplied|not supplied|not supplied|not supplied|sample numeric-looking|Numeric or string?|S1 definition; sample observation separate|
|status|active or closed|Status described as active or closed|not supplied|active/closed listed, exhaustiveness unknown|not supplied|not supplied|sample active|Are these exhaustive?|S2 wording; sample observation separate|
|closed_at|empty for active; may mean not recorded|not supplied|not supplied|not supplied|not supplied|S3: active implies empty; S4: empty may mean not recorded; converse not supplied|sample blank|Does empty imply active, can conditions overlap, and what else produces emptiness or non-empty values?|S3/S4; no name-derived timestamp inference|

Missing definitions remain not supplied; supplied ambiguity remains unresolved. No profiling or
business definition is inferred from the field name or sample.
