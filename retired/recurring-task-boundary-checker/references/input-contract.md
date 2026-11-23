# Input contract

Provide:

- `objective`: recurring outcome requested.
- `trigger`: cadence or event starting each run.
- `owner`: supplied accountable role.
- `inputs`: sources and minimum inputs.
- `actions`: requested and permitted actions.
- `exclusions`: actions or records outside scope.
- `evidence`: completion record or observable result.
- `escalations`: triggers, recipients, and decisions.
- `stop_conditions`: pause, skip, termination, and exception rules.
- `constraints`: safety, timing, or volume limits.

Decision rules:

- Separate requested, authorized, prohibited, and unresolved actions.
- Treat missing cadence, owner, evidence, or stop conditions as contract gaps.
- Do not infer authorization from a recurring request.
- Preserve destructive or externally visible actions for explicit review.
- A proposed contract is not a schedule or execution permission.

Boundaries: do not schedule automation, run the task, alter records, contact people, or claim completion evidence exists.

A description of a future action or a numerical scope limit is not an authorization record. Preserve expressly supplied action-specific permission; otherwise distinguish requested scope from authorized execution. An incomplete permission record does not prevent drafting the partial contract.
