# rfp-response-outline

## One line

Turns pasted RFP requirements and the company's own fact sheet into a requirement matrix, a deadline and form list, and a gap list.

## What it does

The skill reads the requirement sentences in an RFP excerpt and numbers them in source order. Each requirement gets a class from its wording: shall, must and required rows are must; should and preferred rows are should; may and optional rows are may. Every row is mapped to one of six response sections of a typical proposal, with an owner role such as Solutions lead or Contracts lead, so the work can be split before anyone writes text.

Each row is then checked against the facts the user supplied. A fact counts as support only when it names the same capability and meets every number, date, and standard in the requirement. A row with full support is COMPLIANT. A row where the fact covers the capability but misses a stated number, date, or condition is PARTIAL. A row with no supporting fact is GAP. The skill never fills a missing certification, price, reference, or headcount, so the gap list shows exactly what the user still has to supply.

The output also pulls out the submission deadline, counts the days left from a run date you give, and lists any mandatory forms, affidavits, or signatures. A totals line checks that the status counts add up to the requirement count before the matrix is returned.

## When to use

Use it when a bid team has an RFP excerpt in hand and needs a first pass at which requirements the company can answer, which it can answer only in part, and which need a decision. It suits a section-by-section review before the proposal narrative starts, and a quick check of whether a must-level gap exists.

## When not to use

Do not use it to draft the proposal narrative, to set or calculate prices, to certify compliance to the buyer, or to read contract terms for legal risk. It does not read attachments or portal pages, so the user must paste the requirement text. It does not decide bid or no-bid; it only flags that a must row is a GAP.

## Requirements

Type B: no script, no network, no files beyond the pasted text. The agent needs plain text capability. The user supplies the RFP requirement text, a fact sheet of stated company facts with IDs, the submission deadline with time zone and method, and a run date. A missing RFP text or fact sheet stops the run, and a missing deadline or run date produces a partial run with questions.

## Example

```
RUN_STATUS: complete
RUN_DATE: 2026-11-21

### 1. Intake

| Input | Present | Value |
|---|---|---|
| RFP text | yes | Section 3.1 to 3.8, 8 requirements |
| Fact sheet | yes | F01 to F07 |
| Submission deadline | yes | 2026-12-18, 17:00, County local time as printed, County procurement portal |
| Run date | yes | 2026-11-21 |

### 2. Deadlines

| Item | Date and time | Days from run date | Flag |
|---|---|---|---|
| Proposal due | 2026-12-18, 17:00 (County local time as printed) | 27 | NORMAL |

### 3. Mandatory forms

| ID | Form | Signer role | Supplied | Status |
|---|---|---|---|---|
| R08 | Form C-2, Non-Collusion Affidavit | Authorized company signer | no | GAP |

### 4. Requirement matrix

| ID | Class | Requirement (short) | Response section | Owner role | Fact IDs | Status |
|---|---|---|---|---|---|---|
| R01 | must | [3.1] Hosted scheduling for up to 120 vehicles | 4 Technical approach | Solutions lead | F01 | COMPLIANT |
| R02 | must | [3.2] 24/7 support, 30-minute priority-1 response | 6 Service levels | Service delivery lead | F02 | COMPLIANT |
| R03 | must | [3.3] Passenger data stored in United States data centers | 5 Security and compliance | Security and compliance lead | F03 | COMPLIANT |
| R04 | must | [3.4] Current SOC 2 Type II report, copy with proposal | 5 Security and compliance | Security and compliance lead | F04 | PARTIAL |
| R05 | should | [3.5] Driver mobile app on iOS and Android | 4 Technical approach | Solutions lead | F05 | PARTIAL |
| R06 | must | [3.6] Migrate five years of trip records at no additional cost | 4 Technical approach | Solutions lead | F06 | PARTIAL |
| R07 | may | [3.7] Optional real-time passenger notification module | 4 Technical approach | Solutions lead | F07 | GAP |
| R08 | must | [3.8] Signed Form C-2 Non-Collusion Affidavit | 8 Required forms | Contracts lead | none | GAP |

### 5. Gap list

| ID | Class | Gap | Needed from you | Owner role |
|---|---|---|---|---|
| R08 | must | No supplied fact supports a signed Form C-2 | Signed Form C-2 from an authorized signer, or confirmation that one can be obtained before 2026-12-18 | Contracts lead |
| R04 | must | SOC 2 Type I issued 2026-03-10; Type II required and not yet issued | Expected Type II issue date, or confirmation that no Type II report will exist by the due date | Security and compliance lead |
| R06 | must | Migration capability stated; the no-additional-cost condition is not | Whether migration is offered at no additional cost, stated as a fact | Solutions lead |
| R05 | should | Android driver app in development; no release date supplied | Android release date, or confirmation that iOS only will be offered | Solutions lead |
| R07 | may | Company does not offer a notification module | Confirmation that no response is planned for this optional item | Solutions lead |

### 6. Totals

Requirements: 8; COMPLIANT: 3; PARTIAL: 3; GAP: 2; must rows: 6; must GAP: 1; MUST_GAP flag: yes; reconciled: yes

### 7. Questions for you

None.
```

## Limits

- Matches only the wording the user pastes. Requirements in attachments, portal pages, or referenced documents are missed unless pasted.
- Class comes from keywords. A requirement with mixed signals is marked must with a CLASS-CHECK note, and the user must confirm it.
- The deadline flags (CRITICAL at 0 to 3 days, URGENT at 4 to 7) are working values, not a published rule.
- Support is judged from the fact sheet only. A true fact the user leaves out shows as GAP.
- Limit of 60 requirements per run. Longer RFPs must be split by section.
- Owner roles are placeholders for the user to replace with names.

## Status

Provisional. Lint-clean, one smoke run. Not independently verified.
