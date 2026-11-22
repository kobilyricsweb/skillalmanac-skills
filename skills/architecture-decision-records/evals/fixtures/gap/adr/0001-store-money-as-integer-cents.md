# 0001. Store money as integer cents

Status: accepted
Date: 2025-04-11

## Context

Three services round prices differently and invoices have drifted by up to 2 cents. All currencies we sell in have at most two decimal places today.

## Options considered

- Floating point numbers: simplest to write, but binary rounding gives the drift we already see.
- Decimal column type: exact, but each service library handles it differently and one of them silently converts to float.
- Integer cents plus a currency code: exact everywhere, but needs conversion at the edges and cannot represent three-decimal currencies without a change.

## Decision

We will store money as integer minor units plus an ISO currency code, because every language we use handles integers exactly.

## Consequences

- Positive: no rounding drift; comparisons are plain integer comparisons.
- Negative: display code must divide by the currency exponent, and adding a three-decimal currency such as KWD needs a schema review.
- Follow-up: a one-off migration of the 1.2 million existing price rows.
