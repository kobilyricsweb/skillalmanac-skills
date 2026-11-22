# Input Contract

Fields:

- `content`: required passage or bounded passages with locations.
- `glossary`: preferred term, concept, and permitted variants; required for authoritative replacement.
- `protected_text`: optional quotations, code blocks, identifiers, URLs, or names to preserve.
- `rules`: optional scope, case, inflection, or output requirements.

Decision rules:

- Replace only when the preferred term and local meaning match.
- Keep variants separate when they denote different states, roles, objects, or actions.
- A conflicting or incomplete glossary produces an unresolved item, not a guess.
- Every replacement names its location and preservation rationale.

Boundaries:

- Do not change protected text without explicit authorization.
- Do not reconcile factual conflicts between documents; that belongs to document consistency work.
- Do not infer terminology policy from popularity or external sources.
