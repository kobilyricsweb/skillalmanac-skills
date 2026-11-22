---
name: refund-handling
description: Implements and changes refund logic in the payments service (full and partial refunds, account credit for old charges, disputed charges, idempotency keys, ledger rows) and checks it before it is called done. Use when the user asks to add, fix, review or test a refund, double refund, chargeback, refund API call or ledger mismatch. Do not use for charges, payouts or other payment flows.
metadata:
  source: payments/.cursor/rules/refund-handling.mdc
---

# Refund handling

Refunds are the most common source of money bugs here; double refunds are the worst, and any ledger mismatch with the nightly finance reconciliation pages the on-call engineer.

## Workflow

1. Classify the request. Full refund = whole captured amount. Partial refund = part of it; several may exist per charge but their sum can never exceed the captured amount.
2. Pick the action from this table (the first matching row; a disputed charge always wins):

   | Situation | Action | Ledger entry |
   |---|---|---|
   | Full refund, charge 90 days old or newer | call processor refund API | `refund_full` |
   | Partial refund, sum of refunds at or below captured amount | call processor refund API with amount | `refund_partial` |
   | Partial refund that would exceed captured amount | reject with error `REFUND_EXCEEDS_CAPTURE` | none |
   | Charge older than 90 days | issue account credit, no processor call | `credit_issued` |
   | Chargeback open on the charge | reject with error `CHARGE_DISPUTED` | none |

   A charge older than 90 days cannot go back through the card network, hence account credit. A disputed charge must not be refunded: the dispute process returns the money and a refund would pay the customer twice.
3. Call the processor refund API with idempotency key `refund:<charge_id>:<request_id>`. Never generate a random key and never reuse the original charge's key. Retrying with the same key is safe; retrying with a new key is how double refunds happen.
4. Write the `ledger_adjustments` row in the same database transaction as the `refunds` row.
5. If the processor call succeeded but the transaction failed, do not retry the processor call. Enqueue a `reconcile_refund` job with the processor's refund id.

## Rules that always hold

- Amounts are integer minor units (cents), never floats.
- Currency must equal the currency of the original charge.

## Check before finishing

- [ ] Test: double submit (same request twice returns the same refund)
- [ ] Test: partial refund that would exceed the captured amount
- [ ] Test: charge older than 90 days
- [ ] Test: disputed charge
- [ ] Test asserts the idempotency key format
- [ ] Ledger row and refund row are written in one transaction
- [ ] On a local database this query returns no rows (if it returns rows, the change is wrong):

```sql
SELECT r.id FROM refunds r
LEFT JOIN ledger_adjustments l ON l.refund_id = r.id
WHERE l.id IS NULL;
```
