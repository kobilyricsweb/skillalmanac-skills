Synthetic input:
- E1: “Contract signed on March 3.” Source A.
- E2: “Deployment occurred after E1.” Source A.
- E3: “Review happened before E2.” Source B.
- E3: “Review happened after E2.” Source C.
- Uncertainty rule: preserve conflicts.

Concrete artifact:

1. E1 — March 3, exact date. No unresolved placement.
2. E2 — after E1, relative timing. Ordered after E1; exact date unknown.
3. E3 — relative placement conflicted. Source B places it before E2; Source C places it after E2.

Conflict report: E3 cannot be placed uniquely. The scaffold fixes E1 before E2, preserves both E3 relations, and does not infer a date or causal explanation. All three supplied events appear once.
