# Input contract

Provide:

- `artifact`: item or decision requiring approval.
- `starting_state`: state at intake.
- `roles`: named roles and supplied descriptions.
- `authority_rules`: who may review, approve, reject, return, or escalate.
- `entry_criteria`: conditions for each stage.
- `branches`: explicit conditional approvals or exclusions.
- `evidence`: required records at each handoff.
- `escalations`: supplied triggers, recipients, and limits.
- `constraints`: ordering or timing rules, if any.

Decision rules:

- Treat only explicit authority rules as decision rights.
- Treat a prerequisite as binding only when supplied.
- Keep conditional paths separate until their conditions converge.
- Mark absent, contradictory, cyclic, unreachable, or undeclared logic as unresolved.
- A branch may name an actor absent from `roles`; show the conditional stage but flag the role-definition gap and infer no additional authority.
- Report evidence requirements without claiming that evidence exists.

Boundaries: do not assign new approvers, infer authorization, approve the artifact, schedule reviews, contact participants, or execute any workflow.
