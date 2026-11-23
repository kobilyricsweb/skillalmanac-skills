# service-package-description

## One line

Turns a freelancer's intake facts into a fixed-scope package sheet with quantified deliverables, exclusions, a working-day timeline and acceptance criteria.

## What it does

The skill takes the facts a seller already knows about a package: each deliverable with its quantity and file format, the working days for each phase, and the number of revision rounds. From those it writes ten sections in a fixed order: package name, outcome, included deliverables with a file count, exclusions, client responsibilities, timeline, revisions, acceptance criteria, price, and open questions. Quantities and totals are recomputed rather than copied, so a file count or a timeline total that does not add up is caught in the self-check. Prices are copied exactly as supplied and never converted or discounted.

If a required fact is missing, the skill stops and returns a numbered list of at most five questions instead of guessing. If the request asks for a guaranteed result or unlimited revisions, it refuses only that clause, writes replacement wording in its place and returns a partial package with the refused clause listed under open questions. A request that is only for a legal contract, trademark clearance or regulated advice gets a refusal.

## When to use

Use it when a design package, such as a logo set with raster or vector files, has been described in a vague sentence such as "unlimited concepts and a few revisions", and the seller needs the terms written so the client knows exactly what arrives and when.

## When not to use

Do not use it to set a price, decide a discount, or write a statement of work for a regulated service. It does not draft contracts and does not give legal or professional advice. It also does not write marketing copy that promises sales or rankings.

## Requirements

A text-capable agent. No network access, no file tools and no scripts are needed. The seller supplies the intake facts in the conversation.

## Example

Intake used for this example: three concept sketches as 1500 px PNG files; one final logo set in SVG, PDF and PNG (3000 px, transparent background), in a color and a one-color version; phase days of 3 for concepts, 2 for client selection, 2 per revision round and 2 for final files; two revision rounds; price of $350 flat fee.

Status: complete

## 1. Package name

Logo Starter

## 2. Outcome

The client receives one selected logo in SVG, PDF and PNG formats, in a color and a one-color version, after up to two revision rounds.

## 3. Included deliverables

| Item | Quantity | Format | Files |
|------|----------|--------|-------|
| Concept sketch | 3 | PNG, 1500 px long edge | 3 |
| Final logo, color | 1 | SVG, PDF, PNG at 3000 px long edge, transparent PNG background | 3 |
| Final logo, one-color | 1 | SVG, PDF, PNG at 3000 px long edge, transparent PNG background | 3 |
| Total files | | | 9 |

## 4. Exclusions

- Trademark search or registration
- Print production and physical proofs
- Animation or motion versions
- Stationery or brand guidelines
- Purchased font or stock image licenses

## 5. Client responsibilities

- Send one consolidated feedback list per round, within 2 working days of delivery
- Supply brand or reference files before the first phase starts
- Confirm the selected concept in writing before the final phase starts

## 6. Timeline

| Phase | Working days | Cumulative |
|-------|--------------|------------|
| Concept sketches | 3 | 3 |
| Client selects concept | 2 | 5 |
| Revision round 1 | 2 | 7 |
| Revision round 2 | 2 | 9 |
| Final files | 2 | 11 |
| Total | 11 | 11 |

## 7. Revisions

Two revision rounds are included. Each round starts when the client sends one consolidated feedback list and takes 2 working days to redeliver.

## 8. Acceptance criteria

| Deliverable | Criterion |
|-------------|-----------|
| Concept sketch (3 files) | Three distinct concepts, one per PNG file, long edge 1500 px or more |
| Final logo, color (3 files) | SVG and PDF open without error in a vector editor and a PDF viewer; PNG long edge 3000 px or more with a transparent background |
| Final logo, one-color (3 files) | SVG and PDF open without error in a vector editor and a PDF viewer; PNG long edge 3000 px or more with a transparent background |
| All items | Delivered count equals the quantity in section 3 (9 files) |

## 9. Price

$350 flat fee, as supplied.

## 10. Open questions

None.

## Limits

The working values in the skill (1500 px and 3000 px sizes, the 2-day feedback window, the 20-day milestone threshold and the default exclusion list for logo work) are not published standards. A seller who uses other values must change the tables in the skill before relying on the output. The skill does not check whether a logo is legally clear, whether a font license allows commercial use, or whether the seller can deliver on the stated days. It also cannot tell whether a client's brief is complete beyond the three required facts.

## Status

Provisional. Lint-clean, one smoke run. Not independently verified.
