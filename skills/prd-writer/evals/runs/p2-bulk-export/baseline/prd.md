# PRD: Bulk Invoice Export

Status: Draft v1 (not ready for build sign-off; see Open decisions) | Date: 2026-11-20 | From notes by Ines (PM)

## 1. Problem
Invoices can only be exported one at a time. Ravi (support) timed 500 invoices at 14 minutes of clicking. Six customers, all accounting firms, asked for a bulk option last quarter (list in CRM). Two of them said they would move to a competitor without it; sales has not said which two.

## 2. Goal
Let a user export many invoices at once by date range and client.

Success metrics: **not defined in the notes.** Suggested to decide: time to export 500 invoices (baseline 14 min), and retention of the six requesting accounts. No targets set.

## 3. Requirements
### Must (v1)
- Filter by date range and client.
- Output formats: CSV of invoice data, and a ZIP of the invoice PDFs.
- Large exports run in the background and the user receives an emailed download link when ready (eng: the ZIP is the heavy part). Where "large" starts is not defined; eng to specify.
- Download links expire (duration undecided, see open decisions).

### Not in v1 / unconfirmed
- Scheduled monthly export emailed automatically. Only one of six customers asked. Proposed as a follow-up, not v1; Ines to confirm.

## 4. Open decisions
| # | Question | Positions | Needed from |
|---|---|---|---|
| 1 | Who may export? | Tobias: admins only. Ines: any accountant role | PM + Security |
| 2 | Link expiry | Tobias: 24h. Yael (Security): 7 days is fine; customers will complain about 24h | Security + Eng |
| 3 | Include voided invoices? | Nobody knows what customers expect | Ask the six customers |
| 4 | Success metric and targets | None set | PM |

## 5. Timeline and commitments (needs attention)
- Eng estimate: 8 weeks of work **after design is complete**. Design has not started, so there is no ship date, and design duration is unknown.
- Sales (Carla) told Hollis & Wren Accounting it would ship in Q1. Tobias was not consulted. Today is 2026-11-20 and Q1 ends 2027-03-31, about 19 weeks away, so 8 weeks of build requires design to finish in roughly 11 weeks or less with no slack. This arithmetic is mine from the notes; eng should confirm. Recommend validating the commitment with Tobias and managing the customer's expectation now.

## 6. Risks
- Unvalidated Q1 promise to a named customer.
- Churn risk from two unnamed customers; ask Sales to identify them so the roadmap can be prioritized and communicated.
- A link emailed to a user is a data-exposure vector, so decisions 1 and 2 should be settled together with Security.
