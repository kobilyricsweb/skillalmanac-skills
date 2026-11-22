# property-listing-description

## One line

Writes a 120 to 180 word residential listing description from the facts a seller or agent supplies, marks anything unknown as TO-CONFIRM, and strips steering and vague superlative wording.

## What it does

The skill takes a short intake of facts for one home: bedroom count, bathroom count, square feet, property type, year built, dated upgrades, interior features, exterior and lot details, and a showing contact. It checks the three core values first. If bedrooms, bathrooms or square feet are missing or inconsistent, it writes no description and returns a numbered list of up to six questions. If the core values are present, it fills five fixed slots in a fixed order and then appends a sixth paragraph that is the same on every listing. Each supplied fact is marked VERIFIED in a fact check table and each absent fact is marked TO-CONFIRM. A banned wording table removes phrases that describe who would like a home, judge a neighborhood, refer to religion, or call a home stunning without any measured fact behind it.

The output is three headings: the description, a fact check table, and a summary with a status of complete, partial or needs-intake. The status rules are fixed, so a reader can tell from the summary alone whether the copy can be published or still needs seller input.

## When to use

Use it when a real estate agent, seller or property manager has intake facts for a single residential sale or rental and needs listing copy that matches those facts. It also fits a review pass on an existing listing: paste the current text as the intake and the skill will sort each claim into VERIFIED or TO-CONFIRM and remove steering wording. Use it when the same house needs a consistent structure across many listings, because the paragraph order and the fixed closing paragraph do not change between listings.

## When not to use

Do not use it to describe neighbors, neighborhood makeup, crime, school quality, or who a home suits by family status, age, race, religion, national origin, sex or disability. It will not write a price opinion, an appraisal, a valuation, a legal disclosure, or a warranty promise. It is not for commercial property, land-only sales, or multi-unit buildings. It does not verify facts against public records or inspections; it only marks what it was given.

## Requirements

Any text-capable agent. No scripts, no network access, and no files beyond the skill folder. The intake is typed or pasted into the conversation.

## Example

Intake for this run: 3 bedrooms, 2 bathrooms, 1,450 square feet, new roof in 2022. No property type, year built, interior features, exterior details or showing contact were supplied.

```
## Listing description
This property (type TO-CONFIRM) has 3 bedrooms, 2 bathrooms and 1,450 square feet. The year built is TO-CONFIRM from the county assessor record. Upgrades: new roof (2022). Interior features are TO-CONFIRM from the seller's intake sheet. Exterior and lot details are TO-CONFIRM from the seller's intake sheet. To arrange a showing, contact TO-CONFIRM (listing agent name and phone). Showings are arranged through the listing agent. Measurements and dates in this description come from the seller's intake sheet and should be checked against public records and a licensed inspection before you rely on them. Square footage is as stated by the seller and is not a survey. Buyers are encouraged to ask about the property, its condition and its documents, and the listing agent can supply copies of available records on request.

## Fact check
| Fact | Value used | Status |
|---|---|---|
| Property type | TO-CONFIRM | TO-CONFIRM |
| Bedrooms | 3 | VERIFIED |
| Bathrooms | 2 | VERIFIED |
| Square feet | 1,450 | VERIFIED |
| Year built | TO-CONFIRM | TO-CONFIRM |
| Upgrade: new roof | 2022 | VERIFIED |
| Interior features | TO-CONFIRM | TO-CONFIRM |
| Exterior and lot | TO-CONFIRM | TO-CONFIRM |
| Showing contact | TO-CONFIRM | TO-CONFIRM |

## Summary
- Status: partial
- Word count: 131
- TO-CONFIRM items: 5
- Banned terms removed: 0
- Facts dropped: 0
```

## Limits

The word range of 120 to 180 comes from the skill spec. The sq ft band, the bathroom step size, the six-item TO-CONFIRM ceiling and the removal order are working values and have not been tested against real listings. Banned wording covers English phrasing only, and it matches terms as written, so a steering phrase spelled differently will pass the scan. The fixed sixth paragraph states that measurements come from the seller's intake sheet; a publisher who has verified every figure may choose to edit that paragraph outside the skill. The skill does not know local fair-housing rules beyond the categories in its table.

## Status

Provisional. Lint-clean, one smoke run. Not independently verified.
