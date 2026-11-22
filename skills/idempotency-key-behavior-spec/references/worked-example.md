Synthetic input:

Keys are scoped per account for 24 hours. An exact replay returns the original response. A changed payload returns 409. No rule is supplied for concurrent duplicates or requests after 24 hours.

Concrete artifact:

| Scenario | Comparison basis | Outcome | Status |
|---|---|---|---|
| first request | unspecified | not specified by supplied input | unspecified |
| exact replay within 24 hours | supplied payload rule | original response returned | specified |
| changed payload within 24 hours | supplied payload rule | 409 | specified |
| concurrent duplicate | unspecified | undocumented | unspecified |
| request after 24 hours | unspecified | undocumented | unspecified |

Scope: per account. Verification checks each required scenario against the supplied rules. Every unspecified cell is also listed as an explicit question. The matrix does not claim retries are safe or infer behavior for missing cases.
