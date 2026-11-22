## Contents

- Deliverability checklist
- Measurement plan
- Guardrail numbers
- Sources

## Deliverability checklist

Ask the user for each answer; mark unknown ones OPEN in the plan note.

| Item | What good looks like |
|---|---|
| Sending domain | Mail goes from a domain the business controls, not a free webmail address |
| SPF and DKIM | Both set up for the sending domain through the sending tool; messages pass |
| DMARC | A published policy (at least monitoring) with the From domain aligned to SPF or DKIM |
| One-click unsubscribe | `List-Unsubscribe` and `List-Unsubscribe-Post` headers set by the platform |
| Reverse path and reply | A real, monitored reply address; replies are read |
| List hygiene | Hard bounces removed at once; addresses that never engage suppressed (see sunset rule); typo-trap at signup |
| Warm-up | A new domain or a long-dormant list starts with the most engaged recipients and low volume, growing over weeks |
| Volume and consistency | Sudden jumps in volume are avoided; a sequence adds mail on top of newsletters, so count total weekly sends per recipient |
| Content | Plain subject, one CTA, working links on your own domain, a text part alongside HTML, no image-only emails, no URL shorteners |
| Seed test | Send to a few real inboxes at the major providers before launch and look in spam and promotions tabs |

Mailbox providers publish rules for bulk senders (about 5,000 or more messages a day to their users): authentication, one-click unsubscribe, honouring unsubscribes within about 2 days and a low spam-complaint rate. Verify current numbers on the provider pages in Sources; they change.

## Measurement plan

Write all of this in the plan note before launch.

1. **Primary metric**: the goal event from the sequence contract, counted within its window ("first order within 14 days" per recipient who entered the sequence). Report as a rate of entrants.
2. **Supporting metrics**: click-through per email (unique clickers divided by delivered), replies, step-to-step drop-off, time from trigger to goal.
3. **Do not use open rate as a result.** Mail privacy features at some providers pre-load images and register opens that never happened, so opens are inflated and unreliable. Use opens only to compare two sends to the same audience on the same day, if at all.
4. **Guardrails** (stop or fix when crossed; see numbers below): unsubscribe rate, spam-complaint rate, hard-bounce rate.
5. **Holdout**: keep a random 10% of eligible entrants out of the sequence for the first run. Compare goal rate of the sequence group with the holdout; without this, you cannot tell whether the sequence caused anything or the customers would have bought anyway. A smaller business with few entrants can run for longer instead of using a holdout, but must then say the result is not causal.
6. **Changes**: change one thing at a time (a subject, a CTA, a send gap). Do not declare a winner on fewer than about 100 goal events per arm or on less than one full cycle of the goal window (working values).
7. **Review dates**: a first look at day 7 for guardrails only, a result review when the last entrant's goal window has closed, and a quarterly review of sunset and exit rules.
8. **Data kept**: which fields record consent evidence and unsubscribe events, and who owns them.

## Guardrail numbers

Working values for a small sender; adjust to the platform's own guidance.

| Metric | Investigate at | Stop and fix at |
|---|---|---|
| Spam complaints per delivered | 0.10% or higher | 0.30% or higher |
| Unsubscribes per delivered, per email | 0.5% | 2% |
| Hard bounces per sent | 1% | 2% or higher |

The two complaint thresholds follow the bulk sender guidance published by Google; the other four numbers are working values from the skill's author, not provider rules.

## Sources

- Google email sender guidelines and the FAQ: https://support.google.com/a/answer/81126 and https://support.google.com/a/answer/14229414
- Yahoo sender requirements: https://senders.yahooinc.com/best-practices/
- RFC 8058 (one-click unsubscribe): https://www.rfc-editor.org/rfc/rfc8058
- Apple Mail Privacy Protection overview: https://support.apple.com/en-us/102420
