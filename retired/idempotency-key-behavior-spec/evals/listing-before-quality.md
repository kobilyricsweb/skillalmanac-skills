Problem: idempotency documentation may omit duplicate, mismatch, expiry, and concurrency semantics. Artifact: a behavior matrix covering first requests, replays, mismatches, concurrent duplicates, and expired keys. Audience: API designers and reviewers. Limits: supplied contract rules only; no request execution, retry-budget audit, safety claim, or operational authorization.

Unpublished editorial tier: paid-candidate. No score or release approval.

Scope distinction: Nearest is retry-budget-audit; this specifies duplicate-request semantics rather than evaluating retry limits.
