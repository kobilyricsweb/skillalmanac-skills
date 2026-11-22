# PRD: Bulk invoice export

Status: Draft. Source: notes collected by Ines (PM), with input from Tobias (engineering), Carla (sales), Yael (security) and Ravi (support). Author: not stated in the notes.

## Decisions needed
1. Who may export: admins only (Tobias's assumption) or any accountant role (Ines)? Decider: Ines with Tobias; Yael should confirm the security side.
2. How long does a download link live: 24 hours (Tobias) or 7 days (Yael)? Decider: not named in the notes; Yael and Tobias must agree, escalate to the product owner if they do not.
3. Do exports include voided invoices? Nobody knows what customers expect. Decider: Ines, after asking the six requesting customers.
4. What is the delivery commitment? Carla told Hollis & Wren Accounting "Q1"; Tobias estimates 8 weeks of work after design is done, design has not started, and nobody checked the promise with him. Decider: Ines with Carla and Tobias.

## Problem
Accounting firms must export invoices one at a time. Ravi (support) timed 500 invoices at 14 minutes of clicking. 6 customers asked for a bulk export in the last quarter (list in the CRM), all accounting firms. Two of the six said they would move to a competitor without it; sales did not say which two, so that claim is not verified against the CRM list.

## Users
- Accounting firms that export invoices for their own clients. These are the 6 customers who asked.
- Who may use it inside a customer account is not decided (see Open questions).
- Not for this version: any other customer segment, because the notes show no requests from them.

## Success metrics
- Time for a user to get 500 invoices out of the product: baseline 14 minutes of clicking (Ravi), target [needs data], measured by repeating Ravi's test on the finished feature.
- Requesting customers using bulk export: baseline 0 of 6 [assumption: the feature does not exist yet], target [needs data], measured from usage logs.
- Retention of the customers (two of the six) who said they would leave: [needs data] (sales has not named them).

## Non-goals
- Scheduled monthly export by email: only 1 customer asked for it, so it is Could, not part of the first release.
- Formats other than CSV and ZIP of PDFs: none were requested.
- Date commitments to customers: this PRD gives none (see Open questions).

## Requirements
- **R1 (Must)** A user can pick a date range and a client and export every matching invoice in one action. Accept: choose a range and a client with known invoices, start the export; the result contains exactly the invoices that match.
- **R2 (Must)** The export can produce a CSV of the invoice data. Accept: export a client with 3 invoices as CSV; the file has one row per invoice with the data fields shown in the product.
- **R3 (Must)** The export can produce a ZIP of the invoice PDFs. Accept: export 3 invoices as ZIP; the archive holds 3 PDFs that open and match the invoices.
- **R4 (Must)** Large exports run in the background, and the user gets an email with a download link when the export is ready. The size that counts as large is [needs data]. Accept: start a ZIP export of 500 invoices; the screen confirms the export is running without blocking, and an email with a working download link arrives.
- **R5 (Must)** Download links expire. The expiry period is not decided (24 hours or 7 days, see Open questions). Accept: see Open questions; once decided, open a link after the period and see an expired message instead of the file.
- **R6 (Must)** Only permitted roles can start an export. Which roles is not decided (see Open questions). Accept: see Open questions; once decided, a user without the role cannot start an export.
- **R7 (Could)** A customer can schedule an export to run monthly and be emailed automatically. Accept: set a monthly schedule; at the next scheduled time an email with the export arrives.

## Risks and assumptions
- Risk: a "Q1" promise to Hollis & Wren Accounting exists against an estimate of 8 weeks of work after design, and design has not started. The notes give no start date, so whether Q1 is feasible cannot be judged here.
- Risk: two of six requesting customers may leave if the feature is late; the customers are unnamed.
- Risk: ZIP of PDFs is the heavy part (Tobias); without background processing, large exports could fail or time out.
- Risk: voided invoices included or excluded wrongly could give accountants wrong books.
- [assumption] The 8-week estimate covers all Must requirements; the notes do not say what scope it was given for.

## Open questions
- Link expiry: 24 hours or 7 days? Positions: 24 hours (Tobias) / 7 days, customers will complain about 24 hours (Yael). Decider: not named in the notes.
- Who may export? Positions: admins only (Tobias, an assumption) / any accountant role (Ines). Decider: Ines with Tobias and Yael.
- Do exports include voided invoices? Positions: none; nobody knows what customers expect. Decider: Ines.
- Which delivery date can be promised? Positions: Q1 (Carla, told to Hollis & Wren Accounting, not checked with engineering) / 8 weeks after design is done, design not started (Tobias). Decider: Ines with Carla and Tobias.
- Which two customers said they would leave? Decider: Carla (sales).
- What size makes an export large enough to run in the background? Decider: Tobias.
- Is the monthly scheduled export wanted in version one given only 1 customer asked? Decider: Ines.
