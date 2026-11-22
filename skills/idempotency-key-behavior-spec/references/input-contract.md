Required inputs:

- Idempotency-key scope and operation.
- Retention duration and expiry definition.
- Rule for replaying the original response.
- Payload comparison rule, including fields or equality basis.
- Documented outcomes for mismatches, duplicates, conflicts, and expiry.

If a required rule is missing, mark affected matrix cells as unspecified and list the missing decision. Each unspecified cell must also appear as an explicit unspecified question. If rules conflict, preserve both and identify the conflict. Do not infer behavior from common API conventions.

Output fields: scope, global and cell-specific comparison basis, timing, scenario matrix, supplied outcomes, unspecified questions, conflicts, and verification statement. The matrix describes a contract from supplied documentation; it does not establish that an implementation is safe, idempotent, available, or compliant.
