# Worked example

Synthetic example only.

Input:

- Artifact: `Release R7 access-change request`.
- Starting state: `draft`.
- Roles: Request Owner; Security Reviewer; Data Owner; Operations Approver.
- Rules: Security Reviewer may reject or pass security review. Data Owner approves only when customer data is affected. Operations Approver gives final approval after required reviews. A rejected request returns to Request Owner.
- Entry criteria: security review starts when the request is complete; data review applies when `customer_data=true`.
- Evidence: completed request, security decision, data decision when applicable.
- Escalation: none supplied.

Expected artifact:

The scope and assumptions state that this is an offline map and not an approval. The path records the completeness transition as unresolved because its provider and transition are not supplied, then shows Security Reviewer, the conditional Data Owner stage, and Operations Approver. The branch table records `customer_data=true` and `customer_data=false`. Handoffs list required evidence as not confirmed. Reachability findings state that the path is not established from `draft`; the rejection return is recorded, and a cycle is asserted only if later rules send corrected work through an already completed stage. Verification cites the supplied rule for each supported segment. Escalation is undefined, not invented.
