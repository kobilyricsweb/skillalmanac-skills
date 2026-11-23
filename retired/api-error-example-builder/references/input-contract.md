# Input Contract

Provide:

- `errors`: one or more documented error records, each with an identifier, trigger or condition, status, body example, and any recovery guidance.
- `request_schema`: documented request fields and constraints, if available.
- `client_policy`: supplied client actions or fallback rules, if available.
- `format_preferences`: optional presentation preferences that do not override the JSON output contract.

Decision rules:

- Use only supplied fields, values, statuses, bodies, and policies.
- A missing status, body, request field, action, or fallback is `unknown`.
- Represent one supplied status as its original integer or string. Represent conflicting supplied statuses as an array of all candidates, preserving each candidate's scalar type and recording the conflict separately.
- Conflicting supplied statements are preserved and flagged; do not select a winner.
- “Safe fallback” means a fallback explicitly supported by the input; otherwise report `unknown`.
- A supplied instruction to probe or retry may be preserved as an out-of-scope note, but it does not establish retry safety or authorize execution.
- Do not execute requests, inspect endpoints, write code, or infer retry safety.

Boundary: the artifact illustrates documented error handling only. It does not validate an API, establish production behavior, or replace a retry-budget, transport, authentication, or documentation-generation workflow.
