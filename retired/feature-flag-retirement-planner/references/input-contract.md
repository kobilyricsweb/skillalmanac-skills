# Input Contract

Provide:

- `flag`: identifier, owner, current state, and known targeting or rollout status.
- `references`: application, configuration, test, documentation, and dashboard references supplied by the user.
- `policy`: retirement, approval, ownership, or change-control rules.
- `dependencies`: supplied relationships between references or cleanup tasks.
- `rollback`: supplied rollback method, boundary, and evidence.
- `format_preferences`: optional checklist or table preference.

Decision rules:

- Preserve every supplied reference and classify its evidence status.
- Treat missing state, policy, dependency, or rollback information as unknown.
- Mark ordering as supplied or proposed.
- Do not infer dead code, safe deletion, rollout safety, or ownership.
- Phrase outputs as planning and verification tasks, never completed actions.

Boundary: offline planning only. No repository edits, live inspection, flag removal, configuration change, deployment, or universal safe-deletion conclusion.
