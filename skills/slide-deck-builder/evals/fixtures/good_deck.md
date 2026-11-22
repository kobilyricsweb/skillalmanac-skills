---
marp: true
theme: default
---

# The new checkout cut abandonment by a third

Q3 review for the product board

Notes: Open with the result, then say what we ask the board to approve today. The redesign shipped in June, and every number in this deck comes from the live checkout between July and September.

---

# Abandonment fell from 31% to 21% after the redesign

Chart: Bar chart, cart abandonment rate before (31%) and after (21%) the June release
Source: Internal analytics, checkout funnel, Jan-Sep 2026

Notes: This is the one number to remember. Abandonment dropped ten points on identical traffic mix. If someone asks about seasonality, the same months last year were flat at 30 to 32 percent.

---

# One change explains most of the gain: guest checkout

- Guest checkout removed the account wall
- 70% of the lift came from first-time buyers
- Payment-step errors did not change

Notes: Walk the three points in order. Stress that returning customers barely moved, which is why we think the account wall was the problem. The payment-step line is there to rule out a fix we did not make.

---

# Approve two more markets for guest checkout in Q4

- Canada and Germany: same stack, no legal blocker
- Cost: two engineer-weeks each
- Expected lift: 5 to 8 points, based on the US result

Notes: This is the ask. Pause after the first line and let the board react. If they push on cost, point to the appendix slide with the effort estimate and the risks we considered.

---

# Appendix: effort estimate and risks

- Canada: 2 engineer-weeks, French copy review needed
- Germany: 2 engineer-weeks, payment methods differ
- Risk: guest orders raise fraud review volume
- Risk: lower account creation at checkout
- Mitigation: prompt account creation on the confirmation page
