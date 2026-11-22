Required fields:

- approved_change_notes: exact documented change.
- affected_audiences: named users, roles, plans, or workspaces affected.
- release_status: supplied availability or rollout label.
- limitations: known limits, exclusions, or capacity constraints.
- required_action: supplied action, or explicit statement that none is required.
- permitted_cta: supplied CTA text, or explicit statement that no CTA is permitted or supplied.
- evidence_references: supplied references supporting claims.

If a field is missing, produce a partial frame and list the unresolved field. Output must include headline options, confirmed change, audience impact, limitation, migration note, CTA, unresolved items, and fact trace. Use permitted_cta exactly when supplied. If it is absent, CTA must be null and the missing CTA must be unresolved; do not invent one. Keep release status and audience scope exact. Do not infer benefits, availability, rollout completion, compatibility, or performance. Treat a frame as draft communication guidance, not product or publication authorization. Conflicts remain visible and conservative wording is required.
