---
name: refund-handling
description: Rules for writing, changing, reviewing or debugging refund code in the payments service (full and partial refunds, account credit, disputed charges, idempotency keys, ledger_adjustments, reconcile_refund). Use whenever a task touches src/refunds/ or anything that issues or records a refund.
---

# Refund handling

Refunds are the most common source of money bugs in this service. Four incidents between January and June, three of them double refunds. Finance reconciles the ledger nightly and any mismatch pages the on-call engineer. Read this whole file before touching refund code.

## Step 1: classify the request

| Situation | Action | Ledger entry |
|---|---|---|
| Full refund, charge 90 days old or newer | call processor refund API | `refund_full` |
| Partial refund, sum of refunds at or below captured amount | call processor refund API with amount | `refund_partial` |
| Partial refund that would exceed captured amount | reject with error `REFUND_EXCEEDS_CAPTURE` | none |
| Charge older than 90 days | issue account credit, no processor call | `credit_issued` |
| Chargeback open on the charge | reject with error `CHARGE_DISPUTED` | none |

- A full refund returns the whole captured amount.
- Several partial refunds may exist for one charge, but their sum can never exceed the captured amount.
- Charges older than 90 days cannot go back through the card network, so they get account credit.
- Never refund a disputed charge: the dispute process returns the money, and refunding too pays the customer twice.

## Step 2: call the processor safely

- Every processor refund call carries the idempotency key `refund:<charge_id>:<request_id>`.
- Never generate a random key. Never reuse the key of the original charge.
- Retrying with the same key is safe. Retrying with a new key is how double refunds happen.

## Step 3: record it

- Every refund writes a row to `ledger_adjustments` in the same database transaction as its row in `refunds`.
- If the processor call succeeds but the transaction fails, do not retry the processor call. Enqueue a `reconcile_refund` job with the processor's refund id.
- Amounts are integer minor units (cents). Never use floats.
- Currency must equal the currency of the original charge.

## Done checklist

Do not report a refund change as done until all of these hold:

- [ ] test for double submit (same request twice returns the same refund)
- [ ] test for a partial refund that would exceed the captured amount
- [ ] test for a charge older than 90 days
- [ ] test for a disputed charge
- [ ] test asserting the idempotency key format
- [ ] ledger row and refund row are written in one transaction

## Verify on a local database

Find refunds that have no ledger row:

```sql
SELECT r.id FROM refunds r
LEFT JOIN ledger_adjustments l ON l.refund_id = r.id
WHERE l.id IS NULL;
```

If this returns rows after your change, the change is wrong.
