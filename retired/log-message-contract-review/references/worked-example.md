Synthetic input:

Event definition: payment_rejected requires order_id and reason_code; severity guidance says warning. Redaction policy forbids card_number. Proposed template payment_rejected contains order_id and card_number, but no severity is supplied.

Concrete artifact:

| Template | Missing required | Prohibited present | Severity | Assessment | Repair note |
|---|---|---|---|---|---|
| payment_rejected | reason_code | card_number | absent | undetermined | Add reason_code, remove card_number, and add the policy-required warning severity |

The guidance establishes warning as the required value, but does not establish that the template currently supplies it. Unresolved: the template's actual severity is absent. Verification: the template was compared with the declared required list, prohibition, and severity guidance. This review confirms only the static contract assessment; it does not show what the application emits at runtime.
