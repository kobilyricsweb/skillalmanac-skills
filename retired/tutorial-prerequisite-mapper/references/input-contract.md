# Input Contract

Fields:

- `steps`: required ordered steps with IDs and text.
- `environment`: optional stated platform, tools, starting state, or access conditions.
- `inputs_artifacts`: optional supplied files, data, credentials state, or expected outputs.
- `learner_assumptions`: optional prior knowledge and permissions.
- `verification`: optional checks stated by the tutorial.

Decision rules:

- Map a dependency at the earliest step where it is consumed.
- Mark missing facts unknown; do not infer platform, credentials, versions, or permissions.
- Every produced artifact gets an origin and later consumers, or an explicit none.
- A verification cue is adequate only when it observes the stated step output.

Boundaries:

- Do not execute steps, install packages, fetch credentials, or access external systems.
- Do not invent setup details or convert the map into a handover or runbook.
- Report circular, late, or unverifiable dependencies explicitly.
