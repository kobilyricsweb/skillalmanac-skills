# Input contract

## Required

- `draft_text`: the designated draft.
- `sources`: zero or more supplied records with source IDs, content, and any available location markers.

## Handling gaps

If the draft is absent, report missing input and extract nothing. With no sources, factual claims are unsupported. Preserve conflicting matches without choosing a winner. For a source passage lacking a location marker, use `location_unavailable`; do not fabricate an anchor. Mixed statements may be split where meaning is preserved. A factual attribution that a person or group made a recommendation is assessable separately from the recommendation's merits, which may be `not assessable`.

## Deliverable

Return JSON matching `references/output-schema.json`. Preserve claim ID, statement, type, status, matches, reason, and open questions. A match preserves source ID, tagged location, minimized supplied wording or anchor, and evidence relation.

Example: Draft: “Managers recommend extending the pilot.” S3, with no location marker, says the same. Record the attribution as a factual claim supported by S3 with `location_unavailable`; assess the recommendation's merits separately only if they are stated as a claim.
