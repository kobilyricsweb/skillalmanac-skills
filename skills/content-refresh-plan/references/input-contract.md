# Input contract

## Required

- `existing_page`: supplied page content.
- `new_evidence`: supplied evidence IDs, content, and available locations.
- Optional `user_impact_criteria`.

## Handling gaps

If the page is absent, no section mapping is possible. If stable anchors are absent, use clearly marked reviewer-created local anchors only when sections remain distinguishable; otherwise mark mapping blocked. Use `retain` when no factual revalidation or content change is requested. Use `verification_gap` when a proposed change or explicitly required verification lacks adequate evidence. Without evidence and without a requested change, do not convert the section to a verification gap merely because evidence is absent. Removal requires supplied invalidating evidence or an explicit removal request. Use `remove_pending_confirmation` while required confirmation remains unresolved; use `remove_confirmed` only when the supplied record resolves that confirmation. Without stated impact criteria, priority is `unknown`.

## Deliverable

Return JSON matching `references/output-schema.json`. Each section or proposal preserves change ID, location, location type, current summary, action, evidence references, impact, priority, readiness (`proposed` or `blocked`), verification gap, and notes. Include open questions and exclusions.
