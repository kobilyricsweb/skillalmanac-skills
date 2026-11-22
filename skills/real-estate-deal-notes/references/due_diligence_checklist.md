## Contents

1. Item format
2. Core items (all property types)
3. Add for rentals and multi-unit
4. Add for condominiums and associations
5. Add when there is a loan
6. Add when renovating
7. Who normally owns what

## 1. Item format

Each item in `deal.json` under `due_diligence`: `{"item", "owner", "due", "status"}`. Owner is a named person or a role (buyer, agent, attorney, lender, inspector, title company). Due is a calendar date. Status is `open`, `done`, `blocked` or `na`. When closing an item, write one line in `deal_notes.md`: result, document name, date received, and whether it was seen or only reported by someone.

Dates: if the user gave a contract deadline (for example an inspection or financing period), work backwards from it and write the deadline source in the notes. Do not invent contract deadlines; ask for them.

## 2. Core items (all property types)

- Ownership and title search, with liens and easements listed
- Survey or plat, boundaries and access
- Property tax bills for the last periods available, and any pending reassessment notice
- Insurance quote for the actual property (not the seller's policy)
- Physical inspection report; roof, structure, plumbing, electrical, heating and cooling
- Environmental or hazard disclosures required locally (ask the agent or attorney which apply)
- Zoning and permitted use confirmed in writing with the local authority
- Open permits and code violations
- Seller disclosure forms
- Occupancy: who lives there, on what terms, and what transfers with the sale

## 3. Add for rentals and multi-unit

- Rent roll with unit, tenant, rent, deposit, lease start and end
- Copies of leases and any side agreements
- Estoppel or tenant confirmation where customary
- 12-month income and expense statement, plus bank deposits or tax returns that support it
- Utility bills by unit and who pays each
- Rental registration, licence or rent-regulation status
- Management contract, if any, with fees

## 4. Add for condominiums and associations

- Governing documents, rules and rental restrictions
- Budget, reserve study and current dues
- Special assessments, planned or pending
- Litigation involving the association
- Association-approved occupancy or lease limits

## 5. Add when there is a loan

- Loan estimate or term sheet, rate, term, fees, prepayment terms
- Lender's appraisal and its date
- Lender's required reserves and DSCR definition
- Rate lock date and expiry

## 6. Add when renovating

- Written contractor bids, at least two for large scopes, with scope and exclusions
- Permit requirements and who pulls them
- Licence and insurance proof for each contractor
- Timeline and the rent or income lost during works

## 7. Who normally owns what

| Item type | Usual owner |
|---|---|
| Title, liens, contract terms | Attorney or title company |
| Condition, systems | Licensed inspector |
| Value | Appraiser or agent comparables |
| Loan terms | Lender |
| Rent roll, leases, statements | Seller or seller's agent, checked by the buyer |
| Tax and structure questions | Tax adviser or attorney |

A role in the table is a typical pattern, not a rule for any jurisdiction. If the owner of an item is unknown, record it as `open` with the owner "to be assigned by user" and ask; do not guess.
