# Ledger: checkout emails sent twice

## Reproduction
- command: python scripts/place_order.py --user demo
- reproduced: yes

## Hypotheses
### H1
- statement: The retry decorator re-sends the email when the SMTP call times out
- prediction: With the SMTP timeout set to 30 s the duplicate disappears
- status: confirmed

### H2
- statement: The order-created event is published twice
- prediction: The subscriber log shows two deliveries per order
- status: open

### H3
- statement: The email template renders two recipients
- status: open

## Experiments
### E1
- hypothesis: H1
- changed: SMTP timeout 10 s to 30 s; retry count 3 to 1
- result: one email received
- outcome: confirmed

## Root cause
The retry decorator is probably resending.

## Fix
- description: Set retry count to 1 in mailer.py
