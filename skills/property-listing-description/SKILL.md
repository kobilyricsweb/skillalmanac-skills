---
name: property-listing-description
description: Writes an accurate property listing description from verified intake facts (bedrooms, bathrooms, square feet, year built, features and dated upgrades) in 120 to 180 words, with unknown facts marked TO-CONFIRM and steering or vague wording removed. Use when an agent, seller or property manager needs listing copy for a residential sale or rental from intake facts, or when an existing listing needs a fact check and fair-housing wording cleanup. Do not use for neighborhood, school or demographic descriptions, price opinions, appraisals, legal disclosures, or commercial and land listings.
license: Apache-2.0
compatibility: None beyond a text-capable agent (type B); no scripts and no network.
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  author_model: claude-haiku-5-5
  version: "0.1.0"
  network: none
---

# Property listing description

Writes one listing description per request, in fixed paragraph order, using only facts the requester supplies. The skill never invents a fact. A missing fact becomes a TO-CONFIRM marker, and wording that steers buyers or makes unverifiable claims is removed. The shipped license is [LICENSE.txt](LICENSE.txt). This skill ships no scripts.

## Workflow

1. Intake check. Output: a three-row table with Bedrooms, Bathrooms and Square feet, each marked present or missing or conflict. If any core value is missing or conflicting, stop and go to step 8.
2. Sort facts. Output: each supplied fact is VERIFIED. Each absent fact is TO-CONFIRM. Each upgrade is written as item (year). An upgrade with no year keeps its item and gets TO-CONFIRM for the year.
3. Scan the intake text against the banned wording table (table B). Output: a count of matched terms and the action taken for each, either replace with the working value or delete.
4. Draft slots P1 to P5 from the slot table (table A), then append P6 verbatim. Output: the description as plain text, with no headings, bullets or bold.
5. Count words in the description (whitespace-separated tokens, TO-CONFIRM markers included). Apply the length rule in table C. Output: the count and any drops.
6. Build the fact check table in this row order: Property type, Bedrooms, Bathrooms, Square feet, Year built, one row per upgrade in intake order, Interior features, Exterior and lot, Showing contact, then one DROPPED row per dropped item. Output: the table.
7. Apply table C to set the status (complete, partial or needs-intake). Output: the Summary block.
8. Stop rule. When step 1 fails, or when the TO-CONFIRM count is above 6, write no description. Output: a numbered question list (maximum 6 questions) and a Summary block with Status: needs-intake. Ask for bedrooms, then bathrooms, then square feet, then any conflicts, then the TO-CONFIRM items in row order.

## Slot table (table A)

| Slot | Order | Filled sentence | When the value is missing |
|---|---|---|---|
| P1 Opening | 1 | This {type} has {beds} bedrooms, {baths} bathrooms and {sqft} square feet. | Type missing: write "property (type TO-CONFIRM)". Core values are never omitted. |
| P2 Age and upgrades | 2 | The year built is {year}. Upgrades: {item} ({year}); {item} ({year}). | Year missing: "The year built is TO-CONFIRM from the county assessor record." No upgrades supplied: "Upgrades are TO-CONFIRM from the seller's intake sheet." Upgrade with no year: "{item} (TO-CONFIRM)". |
| P3 Interior | 3 | Interior features include {list}. | "Interior features are TO-CONFIRM from the seller's intake sheet." |
| P4 Exterior and lot | 4 | The exterior and lot include {list}. | "Exterior and lot details are TO-CONFIRM from the seller's intake sheet." |
| P5 Showing | 5 | To arrange a showing, contact {agent name and phone}. | "To arrange a showing, contact TO-CONFIRM (listing agent name and phone)." |
| P6 Fixed block | 6 | Append verbatim, every listing, never edited. | Never missing. |

Number rules: write 1 bedroom or 1 bathroom in the singular. Bathrooms may be half values (2.5). Square feet use a thousands comma (1,450).

P6 text, verbatim: Showings are arranged through the listing agent. Measurements and dates in this description come from the seller's intake sheet and should be checked against public records and a licensed inspection before you rely on them. Square footage is as stated by the seller and is not a survey. Buyers are encouraged to ask about the property, its condition and its documents, and the listing agent can supply copies of available records on request.

## Banned wording (table B)

Match case-insensitively. Replacements are working values, not published rules.

| Term or pattern | Category | Action (working value) |
|---|---|---|
| perfect for, ideal for, great for (any group) | steering to a group | Delete. Keep the measured facts. |
| family-friendly, kid-friendly, great for kids | steering to family status | Delete. |
| starter home, empty nester, retirement home, bachelor pad | steering to life stage | Delete. |
| safe neighborhood, safe area, crime-free, low crime | neighborhood claim not in intake | Delete. |
| quiet neighborhood, peaceful street, exclusive, prestigious, private community | neighborhood or status claim | Delete. |
| good schools, top schools, great school district | school quality claim | Replace with "School assignment: TO-CONFIRM with the school district." |
| near church, near temple, near mosque | religious reference | Delete. |
| stunning, gorgeous, amazing, dream, must see, immaculate, luxurious, charming, cozy | vague superlative | Delete. Use the measured fact instead. |
| best, finest, the very best | vague superlative | Delete. |
| move-in ready, turnkey, updated throughout | condition claim without inspection | Replace with "Condition: TO-CONFIRM from the inspection report." |
| walkable, walk to shops, close to everything | proximity claim | Delete unless intake gives a measured distance. |

## Threshold table (table C)

| Check | Value | Result when it fails |
|---|---|---|
| Core intake | Bedrooms, bathrooms and square feet all present and not conflicting | needs-intake (step 8) |
| Bathrooms | Whole or half steps from 0.5 to 20 (working value) | Treat as conflict. needs-intake. |
| Square feet | One number from 100 to 20,000 (working value) | A range or a value outside the band is a conflict. needs-intake. |
| Description word count | 120 to 180 (from the spec) | Below 120: status partial, do not pad. Above 180: drop items in this order, one at a time, recording each as DROPPED: exterior items, then interior features from the last listed. Never drop core facts, upgrades or P6. |
| TO-CONFIRM count | 0 to 6 (working value) | Above 6: needs-intake (step 8). |
| Banned terms in output | 0 | Apply table B, then recount. |

## Output contract

Use these headings in this order, and nothing else:

```
## Listing description
(P1 to P6 as plain paragraphs)

## Fact check
| Fact | Value used | Status |
|---|---|---|

## Summary
- Status: complete | partial | needs-intake
- Word count: N
- TO-CONFIRM items: N
- Banned terms removed: N
- Facts dropped: N
```

Fact status values: VERIFIED, TO-CONFIRM, DROPPED.

Status values: complete means zero TO-CONFIRM items and a word count from 120 to 180. partial means one to six TO-CONFIRM items, or a count below 120; the description is still delivered. needs-intake means no description. Output a "## Questions" heading with the numbered list in place of the description and the Fact check table, then the Summary block with the single line Status: needs-intake.

## Refuse / stop when

- A core intake value is missing or conflicting, or the TO-CONFIRM count is above 6 (step 8).
- The request asks for text about neighbors, neighborhood makeup, crime, school quality, or who the home suits by family status, age, race, religion, national origin, sex or disability. Refuse that item, write no substitute that describes people or places, and count it under Banned terms removed.
- The request asks for a price opinion, appraisal, valuation, legal or disclosure wording, or a warranty promise. Refuse that content; it does not belong in the description.
- The property is commercial, land only, or a multi-unit building. Stop as out of scope and write no description.
- The requester calls a fact verified but gives no source or value. Mark it TO-CONFIRM anyway.
