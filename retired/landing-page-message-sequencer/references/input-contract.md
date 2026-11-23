# Input contract

Provide:

- `audience`: one defined visitor group.
- `objective`: the page action or decision, as approved.
- `messages`: IDs, exact approved wording, type, and restrictions.
- `evidence_assets`: IDs, exact supplied descriptions, and locations.
- `cta`: authorized wording, destination, audience, and any prerequisites.
- `visitor_questions`: known questions in the intended decision journey.
- `prohibited_or_provisional`: claims or uses that must not be treated as approved.

Decision rules:

- Place only approved messages.
- Link a claim to an asset only when the supplied description directly supports the claim.
- Preserve wording restrictions and audience qualifications.
- Preserve CTA wording, destination, audience, authority, and prerequisites; mark missing or conflicting details unresolved.
- Mark unsupported or conflicting items as gaps; do not rewrite them into claims.
- Keep CTA authority and destination visible.

Boundary:

This produces content order and traceability only. It does not produce HTML, UI, SEO strategy, campaign planning, copy variants, or performance forecasts.
