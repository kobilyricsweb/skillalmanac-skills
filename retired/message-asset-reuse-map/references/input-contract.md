# Input contract

Provide:

- `messages`: IDs, exact approved wording, audience, context, restrictions, and authorized uses.
- `assets`: IDs, exact summaries, locations, format, audience, context, permissions, and limitations.
- `reuse_contexts`: requested channels, placements, or situations.
- `reuse_rules`: explicit inclusion, exclusion, attribution, or permission rules.
- `known_gaps`: missing locations, owners, permissions, or source details.

Decision rules:

- Preserve exact message wording and restrictions.
- Match by supplied audience and context, not by asset format alone.
- Record exact asset locations for every allowed or conditional placement.
- Mark missing authority or incompatible context as unresolved or blocked.
- Adaptation requests may ask for missing source material but may not create new claims.

Boundary:

This is a reuse map. It does not determine claim truth, write campaign plans or variants, validate promotions, or invent evidence.
